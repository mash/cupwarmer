"""Query, filter, and formatting helpers for the JLCPCB SQLite DB."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from typing import Any, Iterable, Optional


# --- LCSC normalisation ----------------------------------------------------

_LCSC_RE = re.compile(r"^[Cc]?(\d+)$")


def normalize_lcsc(s) -> Optional[int]:
    """Accept 'C2040' or '2040' or 2040 (int); return the integer or None."""
    if s is None:
        return None
    s = str(s).strip()
    m = _LCSC_RE.match(s)
    if not m:
        return None
    return int(m.group(1))


def fmt_lcsc(n: int) -> str:
    return f"C{n}"


# --- SI suffix parsing for numeric --attr filters --------------------------

_SI = {
    "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6,
    "m": 1e-3, "": 1.0, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9,
}

# Trailing units we strip after parsing the SI prefix (e.g. "0.1uF" -> u + F).
_UNIT_TAIL_RE = re.compile(
    r"^\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*"
    r"([fpnuµμmkKMG]?)\s*"
    r"([a-zA-ZΩ%/]*)\s*$"
)


def parse_si_number(s) -> Optional[tuple[float, str]]:
    """Parse a number with optional SI prefix and unit.

    Returns (value, unit_lower) or None. ``unit_lower`` is the lowercased
    unit suffix (e.g. "f" for farads, "ohm", "%", "v", "/c"); empty string if
    no unit suffix was present.

    A parsed result is considered "numeric for comparison" only when either
    the unit suffix is non-empty, or the SI prefix group is also empty
    (i.e. a bare digit-only number). A lone single-letter SI prefix with no
    trailing unit is not numeric.
    """
    if s is None:
        return None
    m = _UNIT_TAIL_RE.match(str(s))
    if not m:
        return None
    num_str, prefix, unit = m.groups()
    try:
        v = float(num_str)
    except Exception:
        return None
    mult = _SI.get(prefix, None)
    if mult is None:
        return None
    return (v * mult, (unit or "").casefold())


def _is_numeric(parsed: Optional[tuple[float, str]], raw: str) -> bool:
    """True when parsed result should be compared numerically.

    Per spec: numeric iff the parsed unit-suffix is non-empty, OR the input
    consumed no SI-prefix character (purely digits/decimal w/ optional sign).
    """
    if parsed is None:
        return False
    _v, unit = parsed
    if unit:
        return True
    # No unit suffix: only numeric when no prefix character was consumed.
    m = _UNIT_TAIL_RE.match(str(raw))
    if not m:
        return False
    prefix = m.group(2)
    return prefix == ""


# --- Price JSON helpers ----------------------------------------------------

def parse_price(price_text: Optional[str]) -> list[dict]:
    if not price_text:
        return []
    try:
        v = json.loads(price_text)
        if isinstance(v, list):
            return v
    except Exception:
        pass
    return []


def price_for_qty(tiers: list[dict], qty: int) -> Optional[float]:
    """Find the price/unit for the tier covering qty."""
    best: Optional[float] = None
    for t in tiers:
        try:
            q_from = int(t.get("qFrom", 1))
            q_to_raw = t.get("qTo")
            q_to = int(q_to_raw) if q_to_raw not in (None, "") else 10**12
            p = float(t.get("price"))
        except Exception:
            continue
        if q_from <= qty <= q_to:
            return p
        # also remember the highest tier <= qty as fallback
        if q_from <= qty and (best is None):
            best = p
    return best


def price_first_tier(tiers: list[dict]) -> Optional[float]:
    if not tiers:
        return None
    try:
        return float(tiers[0].get("price"))
    except Exception:
        return None


# --- Type ranking ---------------------------------------------------------

def part_type(basic: int, preferred: int) -> str:
    if basic:
        return "basic"
    if preferred:
        return "pref"
    return "ext"


def type_rank(t: str) -> int:
    return {"basic": 0, "pref": 1, "ext": 2}.get(t, 3)


# --- --attr parsing -------------------------------------------------------

# Operators recognised in --attr expressions. Order here is not significant;
# parse_attr_expr does leftmost-longest matching.
ATTR_OPS = ["~", ">=", "<=", "=", ">", "<"]


def parse_attr_expr(expr: str) -> tuple[str, str, str]:
    """Split 'Key OP Value' into (key, op, value).

    Uses leftmost-longest matching so "K>=V" splits at >= not >, and a stray
    '=' inside Value (e.g. "X=Y=Z") splits at the first '='.
    """
    # Sort longest-first so 2-char ops are tried before their 1-char prefixes.
    ops_sorted = sorted(ATTR_OPS, key=len, reverse=True)
    n = len(expr)
    for i in range(n):
        for op in ops_sorted:
            if i + len(op) <= n and expr[i:i + len(op)] == op:
                if i == 0:
                    # No key — fall through to error.
                    continue
                key = expr[:i].strip()
                val = expr[i + len(op):].strip()
                if not key:
                    continue
                return key, op, val
    raise ValueError(
        f"Could not parse --attr {expr!r}; expected Key OP Value with OP in "
        f"{ATTR_OPS}"
    )


def attr_match(stored: Any, op: str, query: str) -> bool:
    """Compare stored value (from JSON extra) against query under op."""
    if stored is None:
        return False
    s_str = str(stored)
    q_str = str(query)

    sn = parse_si_number(s_str)
    qn = parse_si_number(q_str)
    s_numeric = _is_numeric(sn, s_str)
    q_numeric = _is_numeric(qn, q_str)

    def _units_compatible() -> bool:
        # Both are numeric here. Compatible iff units casefold-equal each
        # other OR one side is empty.
        su = sn[1] if sn else ""
        qu = qn[1] if qn else ""
        if not su or not qu:
            return True
        return su == qu

    if op == "=":
        if s_str == q_str:
            return True
        if s_numeric and q_numeric:
            if not _units_compatible():
                return False
            sv = sn[0]
            qv = qn[0]
            return abs(sv - qv) <= max(abs(sv), abs(qv)) * 1e-6
        return s_str.casefold() == q_str.casefold()

    if op == "~":
        return q_str.casefold() in s_str.casefold()

    # numeric ops: require both sides numeric and units compatible.
    if not (s_numeric and q_numeric):
        return False
    if not _units_compatible():
        return False
    sv = sn[0]
    qv = qn[0]
    if op == ">=": return sv >= qv
    if op == "<=": return sv <= qv
    if op == ">":  return sv > qv
    if op == "<":  return sv < qv
    return False


# --- DB connection --------------------------------------------------------

def open_db(path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file://{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# --- Search ---------------------------------------------------------------

class SearchOpts:
    def __init__(self) -> None:
        self.query: Optional[str] = None
        self.category: Optional[str] = None
        self.package: Optional[str] = None
        self.manufacturer: Optional[str] = None
        self.min_stock: Optional[int] = None
        self.basic_only: bool = False
        self.preferred_only: bool = False
        self.attrs: list[tuple[str, str, str]] = []
        self.limit: int = 20


def _like_escape(s: str) -> str:
    """Escape LIKE wildcards. Pair with ESCAPE '\\' in the SQL clause."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def run_search(conn: sqlite3.Connection, opts: SearchOpts) -> list[sqlite3.Row]:
    where: list[str] = []
    params: list[Any] = []

    base = "FROM v_components c"

    if opts.query:
        # LIKE on mfr/description; no FTS index.
        terms = [t.strip() for t in opts.query.split() if t.strip()]
        for t in terms:
            where.append("(c.mfr LIKE ? ESCAPE '\\' OR c.description LIKE ? ESCAPE '\\')")
            pat = f"%{_like_escape(t)}%"
            params.extend([pat, pat])

    if opts.category:
        where.append("c.category = ?")
        params.append(opts.category)
    if opts.package:
        where.append("c.package = ?")
        params.append(opts.package)
    if opts.manufacturer:
        where.append("c.manufacturer LIKE ? ESCAPE '\\'")
        params.append(f"%{_like_escape(opts.manufacturer)}%")
    if opts.min_stock is not None:
        where.append("c.stock >= ?")
        params.append(opts.min_stock)
    if opts.basic_only:
        where.append("c.basic = 1")
    if opts.preferred_only:
        where.append("c.preferred = 1")

    sql = (
        "SELECT c.lcsc, c.mfr, c.manufacturer, c.package, c.description, c.datasheet, "
        "c.basic, c.preferred, c.stock, c.price, c.category, c.subcategory, "
        "c.extra "
        f"{base}"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    # SQL pre-pass orders by the macro-criteria so the overscan returns the
    # right candidate set; price-based tiebreak still happens in Python after
    # attr filtering.
    sql += " ORDER BY c.basic DESC, c.preferred DESC, c.stock DESC, c.lcsc ASC"
    sql += " LIMIT ?"
    overscan = max(opts.limit * 50, 2000)
    params.append(overscan)

    cur = conn.execute(sql, params)
    rows = cur.fetchall()

    if opts.attrs:
        rows = [r for r in rows if _row_passes_attrs(r, opts.attrs)]

    rows.sort(key=lambda r: _sort_key(r))
    return rows[: opts.limit]


def _row_passes_attrs(row: sqlite3.Row, attrs: list[tuple[str, str, str]]) -> bool:
    extra_text = row["extra"]
    try:
        extra = json.loads(extra_text) if extra_text else {}
    except Exception:
        extra = {}
    if not isinstance(extra, dict):
        return False
    for key, op, val in attrs:
        # Be tolerant about key matching — some categories use slightly
        # different capitalisation between rows.
        candidates = [k for k in extra.keys() if k == key]
        if not candidates:
            candidates = [k for k in extra.keys() if k.casefold() == key.casefold()]
        if not candidates:
            return False
        if not any(attr_match(extra[k], op, val) for k in candidates):
            return False
    return True


def _sort_key(row: sqlite3.Row):
    t = part_type(row["basic"] or 0, row["preferred"] or 0)
    tiers = parse_price(row["price"])
    p1 = price_first_tier(tiers)
    p1_key = p1 if p1 is not None else 1e12
    stock = row["stock"] or 0
    # type asc, stock desc (negate), price asc
    return (type_rank(t), -stock, p1_key)


# --- Show -----------------------------------------------------------------

def run_show(conn: sqlite3.Connection, lcsc: int) -> Optional[sqlite3.Row]:
    cur = conn.execute(
        "SELECT lcsc, mfr, manufacturer, package, description, datasheet, basic, preferred, "
        "stock, price, category, subcategory, extra "
        "FROM v_components WHERE lcsc = ?",
        (lcsc,),
    )
    return cur.fetchone()


# --- Schema ---------------------------------------------------------------

def list_categories(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    cur = conn.execute(
        "SELECT category, COUNT(*) AS n FROM v_components "
        "WHERE category IS NOT NULL AND category != '' "
        "GROUP BY category ORDER BY category"
    )
    return [(r["category"], r["n"]) for r in cur.fetchall()]


def category_attr_summary(
    conn: sqlite3.Connection, category: str, sample_limit: int = 8
) -> dict[str, list[str]]:
    cur = conn.execute(
        "SELECT extra FROM v_components WHERE category = ? "
        "AND extra IS NOT NULL AND extra != '' LIMIT 5000",
        (category,),
    )
    keys: dict[str, list[str]] = {}
    for r in cur.fetchall():
        try:
            d = json.loads(r["extra"])
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if v is None:
                continue
            sv = str(v)
            seen = keys.setdefault(k, [])
            if sv not in seen and len(seen) < sample_limit:
                seen.append(sv)
    return keys


# --- Formatting -----------------------------------------------------------

def _display_width(s: str) -> int:
    """Display width treating East-Asian Wide/Fullwidth chars as 2 columns."""
    if s is None:
        return 0
    w = 0
    for c in s:
        if unicodedata.east_asian_width(c) in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


def _truncate(s: str, n: int) -> str:
    """Truncate ``s`` so its display width is at most ``n``."""
    if s is None:
        return ""
    if _display_width(s) <= n:
        return s
    if n <= 1:
        # Best-effort: peel chars until within budget.
        out_chars: list[str] = []
        used = 0
        for c in s:
            cw = 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1
            if used + cw > n:
                break
            out_chars.append(c)
            used += cw
        return "".join(out_chars)
    # Reserve 1 column for the ellipsis.
    budget = n - 1
    out_chars: list[str] = []
    used = 0
    for c in s:
        cw = 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1
        if used + cw > budget:
            break
        out_chars.append(c)
        used += cw
    return "".join(out_chars) + "…"


def format_search_table(rows: Iterable[sqlite3.Row]) -> str:
    rows = list(rows)
    if not rows:
        return "(no matches)"

    header = ["LCSC", "MPN", "Pkg", "Type", "Stock", "$1", "$100", "Mfr"]
    body: list[list[str]] = []
    for r in rows:
        tiers = parse_price(r["price"])
        p1 = price_first_tier(tiers)
        p100 = price_for_qty(tiers, 100)
        body.append([
            fmt_lcsc(r["lcsc"]),
            _truncate(r["mfr"] or "", 28),
            _truncate(r["package"] or "", 14),
            part_type(r["basic"] or 0, r["preferred"] or 0),
            str(r["stock"] or 0),
            f"{p1:.4f}" if p1 is not None else "-",
            f"{p100:.4f}" if p100 is not None else "-",
            _truncate(r["description"] or "", 36),
        ])
    # The trailing column is description (more useful than repeating mfr/MPN).
    header[-1] = "Description"

    cols = list(zip(header, *body))
    widths = [max(_display_width(str(c)) for c in col) for col in cols]

    def _pad(cell: str, w: int) -> str:
        pad = w - _display_width(str(cell))
        if pad < 0:
            pad = 0
        return str(cell) + (" " * pad)

    def _fmt_row(cells: list[str]) -> str:
        return "  ".join(_pad(c, w) for c, w in zip(cells, widths))

    lines = [_fmt_row(header)]
    lines.append(_fmt_row(["-" * w for w in widths]))
    for r in body:
        lines.append(_fmt_row(r))
    out = "\n".join(lines)
    return out


def format_show(row: sqlite3.Row) -> str:
    lines: list[str] = []
    lcsc_n = row["lcsc"]
    lines.append(f"lcsc: {fmt_lcsc(lcsc_n)}")
    lines.append(f"mpn: {row['mfr'] or ''}")
    lines.append(f"description: {row['description'] or ''}")
    lines.append(f"package: {row['package'] or ''}")
    lines.append(f"category: {row['category'] or ''}")
    lines.append(f"subcategory: {row['subcategory'] or ''}")
    lines.append(f"type: {part_type(row['basic'] or 0, row['preferred'] or 0)}")
    lines.append(f"stock: {row['stock'] or 0}")

    tiers = parse_price(row["price"])
    if tiers:
        lines.append("price tiers:")
        for t in tiers:
            q_from = t.get("qFrom", "?")
            q_to = t.get("qTo", "")
            p = t.get("price", "")
            lines.append(f"  {q_from}-{q_to}: ${p}")
    else:
        lines.append("price tiers: (none)")

    extra_text = row["extra"]
    if extra_text:
        try:
            extra = json.loads(extra_text)
        except Exception:
            extra = None
        if isinstance(extra, dict) and extra:
            lines.append("attributes:")
            for k in sorted(extra.keys()):
                lines.append(f"  {k}: {extra[k]}")

    if row["datasheet"]:
        lines.append(f"datasheet: {row['datasheet']}")
    lines.append(f"jlcpcb_url: https://jlcpcb.com/partdetail/{lcsc_n}")
    return "\n".join(lines)


def format_schema_categories(cats: list[tuple[str, int]]) -> str:
    if not cats:
        return "(no categories)"
    return "\n".join(f"{name}  ({n} parts)" for name, n in cats)


def format_schema_category(keys: dict[str, list[str]]) -> str:
    if not keys:
        return "(no attributes found)"
    lines = []
    for k in sorted(keys.keys()):
        samples = ", ".join(keys[k])
        lines.append(f"{k}: {samples}")
    return "\n".join(lines)
