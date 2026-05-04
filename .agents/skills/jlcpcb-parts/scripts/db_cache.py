"""Download and cache management for the JLCPCB SQLite database.

The DB is built locally from yaqwsx/jlcparts's published JSON manifest +
gzipped JSONL shards (https://yaqwsx.github.io/jlcparts/data/), refreshed
upstream every ~6h. We synthesise a single SQLite file with the column
shape that ``search.py`` already expects (``v_components`` view).

Cache layout:
    $XDG_CACHE_HOME/jlcpcb-parts/components.sqlite3
    $XDG_CACHE_HOME/jlcpcb-parts/meta.json

meta.json fields:
    created:        upstream manifest.json ``created`` ISO 8601 UTC.
    last_modified:  same as ``created`` (kept for staleness compatibility).
    downloaded_at:  ISO 8601 UTC timestamp of when we wrote the file.
    url:            the source base URL.
    total_components, version: from manifest.json.
"""

from __future__ import annotations

import fcntl
import gzip
import io
import json
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

BASE_URL = "https://yaqwsx.github.io/jlcparts/data/"
MANIFEST_URL = BASE_URL + "manifest.json"

try:
    import requests  # type: ignore
    HAVE_REQUESTS = True
except Exception:
    HAVE_REQUESTS = False
    import urllib.request


class SchemaHeaderError(Exception):
    """Raised when a shard's line-1 schema header fails to parse."""
    pass


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    p = Path(base) / "jlcpcb-parts"
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path() -> Path:
    return cache_dir() / "components.sqlite3"


def meta_path() -> Path:
    return cache_dir() / "meta.json"


def read_meta() -> dict:
    p = meta_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def write_meta(meta: dict) -> None:
    target = meta_path()
    partial = target.with_suffix(".json.partial")
    partial.write_text(json.dumps(meta, indent=2, sort_keys=True))
    os.replace(partial, target)


# --- HTTP helpers ----------------------------------------------------------

_session = None


def _get_session():
    global _session
    if not HAVE_REQUESTS:
        return None
    if _session is None:
        s = requests.Session()
        # connection pool sized to our worker pool
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=32, pool_maxsize=32, max_retries=3
        )
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _session = s
    return _session


def _http_get_bytes(url: str, timeout: int = 60) -> bytes:
    if HAVE_REQUESTS:
        r = _get_session().get(url, timeout=timeout)
        r.raise_for_status()
        return r.content
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


# --- LUT decoding ----------------------------------------------------------

# unit_kind → (suffix, allow_si_prefix)
_UNIT_SUFFIX = {
    "resistance": ("Ω", True),
    "capacitance": ("F", True),
    "inductance": ("H", True),
    "voltage": ("V", True),
    "current": ("A", True),
    "power": ("W", True),
    "frequency": ("Hz", True),
    "time": ("s", True),
    "charge": ("C", True),
    "count": ("", False),
    "percent": ("%", False),
    "temperature": ("℃", False),
    "string": ("", False),
}

# SI prefixes from large to small for selection.
_SI_PREFIXES = [
    (1e9, "G"), (1e6, "M"), (1e3, "k"), (1.0, ""),
    (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p"), (1e-15, "f"),
]


def _format_number(n: float, unit_kind: str) -> str:
    suffix_info = _UNIT_SUFFIX.get(unit_kind)
    if suffix_info is None:
        # Unknown unit kind: format compactly without prefix.
        suffix, use_si = "", False
    else:
        suffix, use_si = suffix_info
    if not use_si or n == 0:
        s = f"{n:g}"
        return f"{s}{suffix}"
    a = abs(n)
    chosen_mult, chosen_prefix = 1.0, ""
    for mult, p in _SI_PREFIXES:
        if a >= mult:
            chosen_mult, chosen_prefix = mult, p
            break
    else:
        chosen_mult, chosen_prefix = _SI_PREFIXES[-1]
    scaled = n / chosen_mult
    s = f"{scaled:g}"
    return f"{s}{chosen_prefix}{suffix}"


def _format_value(v) -> str:
    """LUT value entry: [raw_value, unit_kind]. Format for display."""
    try:
        raw, unit_kind = v[0], v[1]
    except Exception:
        return str(v)
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return _format_number(float(raw), str(unit_kind))
    return str(raw)


_FMT_RE = re.compile(r"\$\{([^}]+)\}")


def _decode_attr(lut_entry) -> tuple[str, str]:
    """Return (key, display_string) for a single LUT entry."""
    key, meta = lut_entry
    fmt = meta.get("format") or "${default}"
    primary = meta.get("primary") or "default"
    values = meta.get("values") or {}

    try:
        def _sub(m):
            k = m.group(1)
            v = values.get(k)
            if v is None:
                raise KeyError(k)
            return _format_value(v)
        out = _FMT_RE.sub(_sub, fmt)
        return key, out
    except Exception:
        pass

    v = values.get(primary)
    if v is not None:
        return key, _format_value(v)
    if values:
        return key, _format_value(next(iter(values.values())))
    return key, ""


def _build_lut_index(lut: list) -> tuple[list[tuple[str, str]], int]:
    """Decode the LUT once into a flat list of (key, display) tuples.

    Returns (entries, empty_keys_count).
    """
    out: list[tuple[str, str]] = []
    empty_keys = 0
    for entry in lut:
        try:
            k, v = _decode_attr(entry)
            out.append((k, v))
            if not k:
                empty_keys += 1
        except Exception:
            out.append(("", ""))
            empty_keys += 1
    return out, empty_keys


# --- Schema ----------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE components (
  lcsc INTEGER PRIMARY KEY,
  mfr TEXT,
  manufacturer TEXT,
  package TEXT,
  category TEXT,
  subcategory TEXT,
  description TEXT,
  datasheet TEXT,
  basic INTEGER NOT NULL DEFAULT 0,
  preferred INTEGER NOT NULL DEFAULT 0,
  stock INTEGER NOT NULL DEFAULT 0,
  joints INTEGER,
  image TEXT,
  url_slug TEXT,
  price TEXT,
  extra TEXT
);
CREATE INDEX idx_components_category ON components(category);
CREATE INDEX idx_components_package ON components(package);
CREATE INDEX idx_components_manufacturer ON components(manufacturer);
CREATE INDEX idx_components_stock ON components(stock);
CREATE VIEW v_components AS SELECT * FROM components;
"""


def _normalize_lcsc_str(s: str) -> Optional[int]:
    if not s:
        return None
    s = s.strip()
    if s.startswith(("C", "c")):
        s = s[1:]
    try:
        return int(s)
    except Exception:
        return None


# --- Shard download/parse --------------------------------------------------

def _process_shard(
    shard_url: str,
    cat: str,
    subcat: str,
    lut_idx: list[tuple[str, str]],
) -> tuple[list[tuple], dict]:
    """Download one shard, return (rows, counters).

    counters: {"lut_oor": int, "mfg_missing": int}
    Raises SchemaHeaderError if the line-1 schema header cannot be parsed.
    """
    raw = _http_get_bytes(shard_url, timeout=120)
    rows_out: list[tuple] = []
    counters = {"lut_oor": 0, "mfg_missing": 0}
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
        text = io.TextIOWrapper(gz, encoding="utf-8")
        first = text.readline()
        if not first:
            return rows_out, counters
        try:
            schema = json.loads(first)
            i_lcsc = schema["lcsc"]
            i_mfr = schema["mfr"]
            i_joints = schema["joints"]
            i_desc = schema["description"]
            i_ds = schema["datasheet"]
            i_price = schema["price"]
            i_img = schema["img"]
            i_url = schema["url"]
            i_attrs = schema["attributes"]
            i_stock = schema["stock"]
        except Exception as e:
            raise SchemaHeaderError(f"schema header parse failed: {e}")

        for line in text:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            lcsc_n = _normalize_lcsc_str(row[i_lcsc])
            if lcsc_n is None:
                continue

            attrs_decoded: dict[str, str] = {}
            for idx in row[i_attrs] or []:
                if 0 <= idx < len(lut_idx):
                    k, v = lut_idx[idx]
                    if k:
                        attrs_decoded[k] = v
                else:
                    counters["lut_oor"] += 1

            manufacturer = attrs_decoded.get("Manufacturer") or ""
            if not manufacturer:
                # Case-insensitive fallback scan.
                for k, v in attrs_decoded.items():
                    if k.casefold() == "manufacturer" and v:
                        manufacturer = v
                        break
            if not manufacturer:
                counters["mfg_missing"] += 1
            package = attrs_decoded.get("Package") or ""
            be = attrs_decoded.get("Basic/Extended") or ""
            basic = 1 if be == "Basic" else 0
            preferred = 1 if be == "Preferred" else 0

            price_text = json.dumps(row[i_price]) if row[i_price] is not None else None
            extra_text = json.dumps(attrs_decoded, ensure_ascii=False)

            try:
                joints_val = int(row[i_joints]) if row[i_joints] is not None else None
            except Exception:
                joints_val = None

            rows_out.append((
                lcsc_n,
                row[i_mfr] or "",
                manufacturer,
                package,
                cat,
                subcat,
                row[i_desc] or "",
                row[i_ds] or "",
                basic,
                preferred,
                int(row[i_stock] or 0),
                joints_val,
                row[i_img] or "",
                row[i_url] or "",
                price_text,
                extra_text,
            ))
    return rows_out, counters


# --- Progress --------------------------------------------------------------

class _Progress:
    def __init__(self, total_shards: int, total_parts: int) -> None:
        self.total_shards = total_shards
        self.total_parts = total_parts
        self.shards = 0
        self.parts = 0
        self.last_print = 0.0

    def tick(self, shard_done: int, parts_added: int, force: bool = False) -> None:
        self.shards += shard_done
        self.parts += parts_added
        now = time.time()
        if not force and now - self.last_print < 0.5:
            return
        self.last_print = now
        sys.stderr.write(
            f"\r  shards {self.shards}/{self.total_shards}  "
            f"parts {self.parts:,} / {self.total_parts:,}     "
        )
        sys.stderr.flush()


# --- Main download / build -------------------------------------------------

def _download_impl(url: str, force: bool) -> dict:
    """Build the SQLite DB. Caller holds the build lock."""
    target = db_path()
    tmp = target.with_suffix(".sqlite3.partial")
    if tmp.exists():
        try:
            tmp.unlink()
        except Exception:
            pass

    sys.stderr.write(f"Fetching manifest from {MANIFEST_URL}\n")
    sys.stderr.flush()
    manifest_bytes = _http_get_bytes(MANIFEST_URL, timeout=60)
    manifest = json.loads(manifest_bytes.decode("utf-8"))

    # B15 — manifest short-circuit
    cached_meta = read_meta()
    cached_created = cached_meta.get("created", "")
    new_created = manifest.get("created", "")
    if (
        not force
        and new_created
        and cached_created
        and cached_created == new_created
        and target.exists()
    ):
        sys.stderr.write(
            f"# manifest unchanged (created={new_created}); skipping rebuild\n"
        )
        sys.stderr.flush()
        meta = dict(cached_meta)
        meta["downloaded_at"] = datetime.now(timezone.utc).isoformat()
        write_meta(meta)
        return meta

    lut_url = BASE_URL + manifest.get("attributesLut", "attributes-lut.json.gz")
    sys.stderr.write(f"Fetching LUT from {lut_url}\n")
    sys.stderr.flush()
    lut_bytes = _http_get_bytes(lut_url, timeout=120)
    lut = json.loads(gzip.decompress(lut_bytes).decode("utf-8"))
    sys.stderr.write(f"  decoded {len(lut):,} LUT entries\n")
    sys.stderr.flush()
    lut_idx, lut_empty_keys = _build_lut_index(lut)
    del lut

    cats = manifest.get("categories", [])
    total_parts = int(manifest.get("totalComponents", 0))

    shard_jobs: list[tuple[str, str, str]] = []  # (url, category, subcategory)
    for c in cats:
        cat = c.get("category") or ""
        subcat = c.get("subcategory") or ""
        for shard in c.get("shards", []):
            shard_jobs.append((BASE_URL + shard, cat, subcat))

    sys.stderr.write(
        f"Building SQLite from {len(shard_jobs)} shards "
        f"({total_parts:,} parts expected)\n"
    )
    sys.stderr.flush()

    # Open partial DB
    conn = sqlite3.connect(str(tmp))
    conn.execute("PRAGMA journal_mode=MEMORY")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.executescript(_SCHEMA_SQL)

    insert_sql = (
        "INSERT OR IGNORE INTO components "
        "(lcsc, mfr, manufacturer, package, category, subcategory, "
        "description, datasheet, basic, preferred, stock, joints, "
        "image, url_slug, price, extra) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )

    progress = _Progress(len(shard_jobs), total_parts)
    progress.tick(0, 0, force=True)

    failed_shards = 0
    header_failures = 0
    lut_oor_total = 0
    mfg_missing_total = 0

    # Concurrent download + parse, serial DB insert
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {
            pool.submit(_process_shard, url, cat, subcat, lut_idx): (url, cat, subcat)
            for (url, cat, subcat) in shard_jobs
        }
        for fut in as_completed(futures):
            url, cat, subcat = futures[fut]
            try:
                rows, counters = fut.result()
            except SchemaHeaderError as e:
                sys.stderr.write(f"\nshard schema header failed: {url}: {e}\n")
                header_failures += 1
                failed_shards += 1
                progress.tick(1, 0)
                continue
            except Exception as e:
                sys.stderr.write(f"\nshard failed: {url}: {e}\n")
                failed_shards += 1
                progress.tick(1, 0)
                continue
            lut_oor_total += counters.get("lut_oor", 0)
            mfg_missing_total += counters.get("mfg_missing", 0)
            if rows:
                conn.execute("BEGIN")
                conn.executemany(insert_sql, rows)
                conn.commit()
            progress.tick(1, len(rows))

    progress.tick(0, 0, force=True)
    sys.stderr.write("\n  ANALYZE...\n")
    sys.stderr.flush()
    conn.execute("ANALYZE")
    conn.commit()
    conn.close()

    total_shards = len(shard_jobs)
    threshold = max(5, total_shards // 100)
    if failed_shards > threshold:
        sys.stderr.write(
            f"\nERROR: {failed_shards} of {total_shards} shards failed "
            f"(threshold {threshold}); aborting build.\n"
            f"Partial DB left at: {tmp}\n"
        )
        sys.stderr.flush()
        raise SystemExit(1)

    os.replace(tmp, target)

    # Report decode counters
    sys.stderr.write(
        f"# LUT decode: skipped {lut_oor_total} out-of-range indices, "
        f"{lut_empty_keys} empty keys\n"
    )
    if mfg_missing_total:
        sys.stderr.write(
            f"# manufacturer missing for {mfg_missing_total} parts\n"
        )
    sys.stderr.flush()

    meta = {
        "created": manifest.get("created", ""),
        "last_modified": manifest.get("created", ""),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "url": BASE_URL,
        "total_components": manifest.get("totalComponents"),
        "version": manifest.get("version"),
    }
    if failed_shards > 0:
        meta["failed_shards"] = failed_shards
    if header_failures > 0:
        meta["header_failures"] = header_failures
    write_meta(meta)
    sys.stderr.write(f"Wrote {target} ({target.stat().st_size / (1024*1024):.0f}MB)\n")
    sys.stderr.flush()
    return meta


def download(url: str = BASE_URL, force: bool = False) -> dict:
    """Build the SQLite DB from yaqwsx's manifest + shards.

    Returns the meta dict written. Holds an exclusive flock on
    ``cache_dir()/build.lock`` for the entire build to prevent
    concurrent rebuilds from corrupting the cache.
    """
    lock_path = cache_dir() / "build.lock"
    with open(lock_path, "w") as lock_fp:
        try:
            fcntl.flock(lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("another build is running")
        try:
            return _download_impl(url, force)
        finally:
            try:
                fcntl.flock(lock_fp.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass


# --- Freshness -------------------------------------------------------------

def parse_last_modified(s: str) -> Optional[datetime]:
    """Parse either ISO 8601 (yaqwsx ``created``) or RFC 1123 (legacy)."""
    if not s:
        return None
    # Try ISO first
    try:
        # Python 3.11+ accepts trailing 'Z'; older needs replace
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def staleness_lines() -> list[str]:
    """Return list of stderr lines summarising DB freshness."""
    meta = read_meta()
    lm = parse_last_modified(meta.get("last_modified") or meta.get("created", ""))
    lines: list[str] = []
    if not db_path().exists():
        lines.append("# JLCPCB DB: not downloaded yet")
        return lines
    if lm is None:
        lines.append("# JLCPCB DB: cached (upstream timestamp unknown)")
        return lines
    today = datetime.now(timezone.utc)
    age_days = (today.date() - lm.date()).days
    ago = "today" if age_days == 0 else f"{age_days}d ago"
    lines.append(f"# JLCPCB DB: built {lm.date().isoformat()} ({ago})")
    if age_days >= 7:
        lines.append(
            f"⚠ DB is {age_days}d old — run "
            f"'jlcpcb_parts.py update'"
        )
    return lines


def emit_staleness() -> None:
    for line in staleness_lines():
        sys.stderr.write(line + "\n")
    sys.stderr.flush()


def ensure_db_or_warn(auto_download: bool = True) -> Path:
    """Return path to the DB. If missing, optionally download with a warning."""
    p = db_path()
    if p.exists():
        return p
    if not auto_download:
        raise SystemExit(
            f"JLCPCB DB not found at {p}. Run 'jlcpcb_parts.py update' first."
        )
    sys.stderr.write(
        "JLCPCB DB cache not found. Performing first-time build "
        "(~100MB, ~1300 shards from yaqwsx, takes 1–3 min)...\n"
    )
    sys.stderr.flush()
    download()
    return p
