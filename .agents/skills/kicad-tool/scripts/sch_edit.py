"""Pure S-expression text mutation for KiCad 10 schematic files.

All functions take a path to a `.kicad_sch` file, perform a structural edit on
the raw text (preserving tab indentation and existing formatting), and return a
result dict of the form::

    {
        "action": "<verb_element>",
        "changed": bool,
        "diff": "<unified diff string>",
        "details": {...},
    }

When ``dry_run=True`` no file is written. When ``dry_run=False`` and the edit
changes the text, the file is overwritten with the new content.

Notes
-----
- We deliberately do NOT round-trip via kiutils for writes — kiutils can lose
  formatting / reorder tokens / re-emit UUIDs. kiutils is only used to look up
  anchors (e.g., a symbol's current ``(at)`` position).
- Block extraction is done by paren-balancing on the raw text starting from a
  located opening token. This works for KiCad 10's pretty-printed format where
  every `(symbol ...)`, `(wire ...)`, `(junction ...)`, `(global_label ...)`,
  `(hierarchical_label ...)`, `(label ...)` block sits at depth 1 with leading
  tab.
- Coordinates are rendered with KiCad's usual style: integer if value is an
  integer, else with the minimum number of decimals KiCad would emit. We use
  ``_fmt_coord`` to mimic this.
"""

from __future__ import annotations

import difflib
import math
import re
import sys
import uuid as _uuid
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, "/Users/mash/src/github.com/mvnmgrx/kiutils/src")

from kiutils.schematic import Schematic  # noqa: E402

from kicad_sch_bbox_collisions import local_to_schematic  # noqa: E402


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _fmt_coord(v: float) -> str:
    """Format a coordinate the way KiCad does: drop trailing zeros, no exponent."""
    if isinstance(v, int):
        return str(v)
    # Round to 4 decimals (KiCad uses up to 4 in practice for sch coords).
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _new_uuid() -> str:
    return str(_uuid.uuid4())


def _read(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _diff(old: str, new: str, path: Path) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
            n=3,
        )
    )


def _maybe_write(path: Path, old: str, new: str, dry_run: bool) -> bool:
    """Write file if not dry-run and content changed. Returns True if changed."""
    if old == new:
        return False
    if not dry_run:
        Path(path).write_text(new, encoding="utf-8")
    return True


def _find_block_end(text: str, open_idx: int) -> int:
    """Given index of an `(`, return the index just past the matching `)`.

    Respects double-quoted strings (with `\"` escapes).
    """
    if text[open_idx] != "(":
        raise ValueError(f"expected '(' at {open_idx}, got {text[open_idx]!r}")
    depth = 0
    i = open_idx
    n = len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced parentheses")


def _expand_block_with_indent(text: str, open_idx: int, end_idx: int) -> tuple[int, int]:
    """Expand the block range to include leading tabs/spaces and the trailing newline.

    Returns ``(start, stop)`` where ``text[start:stop]`` is the full block with
    its indentation prefix and trailing ``\\n`` (if any).
    """
    # walk back to start of line
    start = open_idx
    while start > 0 and text[start - 1] in (" ", "\t"):
        start -= 1
    # include trailing newline
    stop = end_idx
    if stop < len(text) and text[stop] == "\n":
        stop += 1
    return start, stop


def _detect_indent_unit(text: str) -> str:
    """Heuristically detect indentation unit: tab if a tab-indented block exists."""
    if re.search(r"^\t\(", text, flags=re.MULTILINE):
        return "\t"
    if re.search(r"^    \(", text, flags=re.MULTILINE):
        return "    "
    return "\t"


# ---------------------------------------------------------------------------
# Block locators
# ---------------------------------------------------------------------------


_TOKEN_AT_DEPTH1_RE = re.compile(r"^\t\(([a-z_]+)\b", re.MULTILINE)


def _iter_top_blocks(text: str, token: str):
    """Yield (open_idx, end_idx) for each ``(token ...)`` block at depth 1 (tab indent)."""
    pat = re.compile(r"^\t\(" + re.escape(token) + r"\b", re.MULTILINE)
    for m in pat.finditer(text):
        open_idx = m.start() + 1  # skip the leading tab
        end_idx = _find_block_end(text, open_idx)
        yield open_idx, end_idx


def _block_field(block: str, field: str) -> str | None:
    """Extract the first ``(field ...)`` inner content from a block string."""
    m = re.search(r"\(" + re.escape(field) + r"\s+([^)]*)\)", block)
    if not m:
        return None
    return m.group(1).strip()


def _block_uuid(block: str) -> str | None:
    m = re.search(r'\(uuid\s+"([^"]+)"\)', block)
    return m.group(1) if m else None


def _block_at(block: str) -> tuple[float, float, float] | None:
    m = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)", block)
    if not m:
        return None
    x, y = float(m.group(1)), float(m.group(2))
    rot = float(m.group(3)) if m.group(3) is not None else 0.0
    return x, y, rot


def _coords_close(a: float, b: float, tol: float = 0.001) -> bool:
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# move_symbol
# ---------------------------------------------------------------------------


def _find_symbol_block_by_ref(text: str, ref: str) -> tuple[int, int, str] | None:
    """Locate a top-level (symbol ...) block whose Reference property == ref.

    Returns (open_idx, end_idx, block_text) or None.
    """
    for open_idx, end_idx in _iter_top_blocks(text, "symbol"):
        block = text[open_idx:end_idx]
        m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        if m and m.group(1) == ref:
            return open_idx, end_idx, block
    return None


def move_symbol(
    sch_path: str | Path,
    ref: str,
    to: tuple[float, float],
    rotation: float | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Move a symbol by reference, cascading all five property ``(at)`` positions.

    Returns ``details`` containing old/new symbol position and absolute pin
    coordinates (computed via lib pin offsets).
    """
    sch_path = Path(sch_path)
    text = _read(sch_path)

    found = _find_symbol_block_by_ref(text, ref)
    if not found:
        raise ValueError(f"symbol with reference {ref!r} not found in {sch_path}")
    open_idx, end_idx, block = found

    sym_at = _block_at(block)
    if sym_at is None:
        raise ValueError(f"symbol {ref!r} has no (at ...) field")
    old_x, old_y, old_rot = sym_at
    new_x, new_y = float(to[0]), float(to[1])
    new_rot = float(rotation) if rotation is not None else old_rot
    dx = new_x - old_x
    dy = new_y - old_y
    drot = new_rot - old_rot

    # Replace the symbol's own (at ...) — must replace ONLY the first one inside the block.
    sym_at_re = re.compile(r"\(at\s+-?[\d.]+\s+-?[\d.]+(?:\s+-?[\d.]+)?\s*\)")
    m_sym_at = sym_at_re.search(block)
    if not m_sym_at:
        raise ValueError("symbol (at ...) not found")
    new_sym_at = f"(at {_fmt_coord(new_x)} {_fmt_coord(new_y)} {_fmt_coord(new_rot)})"
    new_block = block[: m_sym_at.start()] + new_sym_at + block[m_sym_at.end() :]

    # Cascade property (at ...): shift each by (dx, dy) and add drot to its rotation.
    prop_re = re.compile(
        r'(\(property\s+"(?:Reference|Value|Footprint|Datasheet|Description)"\s+"[^"]*"\s*\n\s*)'
        r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)"
    )

    def _shift(m: re.Match) -> str:
        head = m.group(1)
        px = float(m.group(2)) + dx
        py = float(m.group(3)) + dy
        prot = float(m.group(4) or "0") + drot
        return f"{head}(at {_fmt_coord(px)} {_fmt_coord(py)} {_fmt_coord(prot)})"

    new_block = prop_re.sub(_shift, new_block)

    new_text = text[:open_idx] + new_block + text[end_idx:]

    # Compute new absolute pin coordinates using lib symbol pin offsets via kiutils.
    pins_abs: list[dict[str, Any]] = []
    try:
        sch_obj = Schematic.from_file(str(sch_path))
        lib = {s.entryName: s for s in sch_obj.libSymbols}
        sym_obj = next(
            (
                s
                for s in sch_obj.schematicSymbols
                if any(p.key == "Reference" and p.value == ref for p in s.properties)
            ),
            None,
        )
        if sym_obj is not None:
            libsym = lib.get(sym_obj.entryName)
            if libsym is not None:
                for unit in getattr(libsym, "units", []):
                    for pin in getattr(unit, "pins", []):
                        ax, ay = local_to_schematic(
                            new_x, new_y, int(new_rot) % 360, pin.position.X, pin.position.Y
                        )
                        pins_abs.append(
                            {
                                "number": pin.number,
                                "name": pin.name,
                                "x": round(ax, 4),
                                "y": round(ay, 4),
                            }
                        )
    except Exception as exc:  # noqa: BLE001
        pins_abs = [{"error": f"pin computation failed: {exc}"}]

    changed = _maybe_write(sch_path, text, new_text, dry_run)
    return {
        "action": "move_symbol",
        "changed": changed,
        "diff": _diff(text, new_text, sch_path),
        "details": {
            "ref": ref,
            "old": {"x": old_x, "y": old_y, "rotation": old_rot},
            "new": {"x": new_x, "y": new_y, "rotation": new_rot},
            "delta": {"dx": dx, "dy": dy, "drot": drot},
            "pins": pins_abs,
        },
    }


# ---------------------------------------------------------------------------
# add_wire / delete_wire
# ---------------------------------------------------------------------------


def _wire_block(x1: float, y1: float, x2: float, y2: float, wire_type: str, uuid_str: str) -> str:
    return (
        f"\t(wire\n"
        f"\t\t(pts\n"
        f"\t\t\t(xy {_fmt_coord(x1)} {_fmt_coord(y1)}) (xy {_fmt_coord(x2)} {_fmt_coord(y2)})\n"
        f"\t\t)\n"
        f"\t\t(stroke\n"
        f"\t\t\t(width 0)\n"
        f"\t\t\t(type {wire_type})\n"
        f"\t\t)\n"
        f'\t\t(uuid "{uuid_str}")\n'
        f"\t)\n"
    )


def add_wire(
    sch_path: str | Path,
    pt_from: tuple[float, float],
    pt_to: tuple[float, float],
    wire_type: str = "default",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Append a (wire ...) block. Inserts after the last existing wire if any,
    otherwise just before the closing top-level paren.
    """
    sch_path = Path(sch_path)
    text = _read(sch_path)
    if wire_type not in {"default", "solid"}:
        raise ValueError(f"wire_type must be 'default' or 'solid', got {wire_type!r}")

    uuid_str = _new_uuid()
    block = _wire_block(pt_from[0], pt_from[1], pt_to[0], pt_to[1], wire_type, uuid_str)

    # Insert after the last existing top-level wire block, if any.
    last_end: int | None = None
    for open_idx, end_idx in _iter_top_blocks(text, "wire"):
        last_end = end_idx
    if last_end is not None:
        # consume trailing newline
        insert_at = last_end
        if insert_at < len(text) and text[insert_at] == "\n":
            insert_at += 1
        new_text = text[:insert_at] + block + text[insert_at:]
    else:
        # fall back: insert before the final closing paren of the file
        last_paren = text.rstrip().rfind(")")
        if last_paren < 0:
            raise ValueError("could not locate end of schematic")
        new_text = text[:last_paren] + block + text[last_paren:]

    changed = _maybe_write(sch_path, text, new_text, dry_run)
    return {
        "action": "add_wire",
        "changed": changed,
        "diff": _diff(text, new_text, sch_path),
        "details": {
            "uuid": uuid_str,
            "from": list(pt_from),
            "to": list(pt_to),
            "type": wire_type,
        },
    }


def _wire_endpoints(block: str) -> tuple[tuple[float, float], tuple[float, float]] | None:
    m = re.search(
        r"\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)\s+\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)",
        block,
    )
    if not m:
        return None
    return (float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4)))


def delete_wire(
    sch_path: str | Path,
    uuid: str | None = None,
    pt_from: tuple[float, float] | None = None,
    pt_to: tuple[float, float] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Delete a (wire ...) block by uuid or matching endpoints (order-insensitive)."""
    sch_path = Path(sch_path)
    text = _read(sch_path)
    if uuid is None and (pt_from is None or pt_to is None):
        raise ValueError("delete_wire requires either uuid or both pt_from and pt_to")

    target: tuple[int, int] | None = None
    matched_uuid: str | None = None
    matched_pts = None
    for open_idx, end_idx in _iter_top_blocks(text, "wire"):
        block = text[open_idx:end_idx]
        wuuid = _block_uuid(block)
        if uuid is not None and wuuid == uuid:
            target = (open_idx, end_idx)
            matched_uuid = wuuid
            matched_pts = _wire_endpoints(block)
            break
        if uuid is None:
            pts = _wire_endpoints(block)
            if pts is None:
                continue
            (a, b) = pts
            ok = (
                _coords_close(a[0], pt_from[0])
                and _coords_close(a[1], pt_from[1])
                and _coords_close(b[0], pt_to[0])
                and _coords_close(b[1], pt_to[1])
            ) or (
                _coords_close(a[0], pt_to[0])
                and _coords_close(a[1], pt_to[1])
                and _coords_close(b[0], pt_from[0])
                and _coords_close(b[1], pt_from[1])
            )
            if ok:
                target = (open_idx, end_idx)
                matched_uuid = wuuid
                matched_pts = pts
                break

    if target is None:
        raise ValueError("no matching wire found")

    start, stop = _expand_block_with_indent(text, target[0], target[1])
    new_text = text[:start] + text[stop:]
    changed = _maybe_write(sch_path, text, new_text, dry_run)
    return {
        "action": "delete_wire",
        "changed": changed,
        "diff": _diff(text, new_text, sch_path),
        "details": {
            "uuid": matched_uuid,
            "endpoints": matched_pts,
        },
    }


# ---------------------------------------------------------------------------
# Labels: add / move / delete
# ---------------------------------------------------------------------------


_LABEL_TOKENS = {
    "global": "global_label",
    "hier": "hierarchical_label",
    "local": "label",
}


def _find_sibling_label_block(text: str, kind_token: str) -> tuple[int, int, str] | None:
    for open_idx, end_idx in _iter_top_blocks(text, kind_token):
        return open_idx, end_idx, text[open_idx:end_idx]
    return None


def add_label(
    sch_path: str | Path,
    kind: str,
    name: str,
    at: tuple[float, float],
    rotation: float = 0.0,
    justify: str | None = None,  # noqa: ARG001 — kept for API parity; cloned from sibling
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add a label by cloning a sibling block of the same kind.

    Per the kicad-hardware-editing rules, we never synthesize ``(justify ...)``,
    ``(effects ...)``, or related quirks from scratch — we copy from a sibling
    in the same file and only swap text/at/uuid.

    The ``justify`` argument is currently ignored; the cloned sibling's justify
    is preserved. Pass it explicitly only if a future implementation overrides.
    """
    sch_path = Path(sch_path)
    text = _read(sch_path)
    if kind not in _LABEL_TOKENS:
        raise ValueError(f"kind must be one of {sorted(_LABEL_TOKENS)}, got {kind!r}")
    token = _LABEL_TOKENS[kind]

    sib = _find_sibling_label_block(text, token)
    if sib is None:
        raise ValueError(
            f"no existing {token!r} block in {sch_path} to clone from; "
            "add one manually first or pick a different kind"
        )
    _, sib_end, sib_block = sib

    new_uuid = _new_uuid()
    x, y = float(at[0]), float(at[1])
    rot = float(rotation)

    # Replace the head: ({token} "OLDNAME" → ({token} "NEWNAME"
    new_block = re.sub(
        r'^\(' + re.escape(token) + r'\s+"[^"]*"',
        f'({token} "{name}"',
        sib_block,
        count=1,
    )
    # Replace the first (at ...) — that's the label's own position.
    new_block = re.sub(
        r"\(at\s+-?[\d.]+\s+-?[\d.]+(?:\s+-?[\d.]+)?\s*\)",
        f"(at {_fmt_coord(x)} {_fmt_coord(y)} {_fmt_coord(rot)})",
        new_block,
        count=1,
    )
    # Replace label uuid (the first uuid in the block — the label's, before Intersheetrefs).
    new_block = re.sub(
        r'\(uuid\s+"[^"]+"\)',
        f'(uuid "{new_uuid}")',
        new_block,
        count=1,
    )
    # If global label has Intersheetrefs (at ...), align it to label position.
    if token == "global_label":
        new_block = re.sub(
            r'(\(property\s+"Intersheetrefs"[^\n]*\n\s*)\(at\s+-?[\d.]+\s+-?[\d.]+(?:\s+-?[\d.]+)?\s*\)',
            lambda m: f"{m.group(1)}(at {_fmt_coord(x)} {_fmt_coord(y)} {_fmt_coord(rot)})",
            new_block,
            count=1,
        )

    # Insert immediately after the sibling block (preserving its trailing newline).
    insert_at = sib_end
    if insert_at < len(text) and text[insert_at] == "\n":
        insert_at += 1
    # The sibling block we extracted does NOT include the leading tab; we need to
    # prepend the tab before our cloned block since sib_block was extracted from
    # the depth-1 token onward without the leading tab.
    new_block_with_indent = "\t" + new_block + "\n"
    new_text = text[:insert_at] + new_block_with_indent + text[insert_at:]

    changed = _maybe_write(sch_path, text, new_text, dry_run)
    return {
        "action": "add_label",
        "changed": changed,
        "diff": _diff(text, new_text, sch_path),
        "details": {
            "kind": kind,
            "name": name,
            "at": [x, y],
            "rotation": rot,
            "uuid": new_uuid,
        },
    }


def _find_label_block_by_uuid(text: str, uuid: str) -> tuple[str, int, int, str] | None:
    """Search all label kinds for a block whose first uuid matches.

    Returns (token, open_idx, end_idx, block) or None.
    """
    for kind, token in _LABEL_TOKENS.items():  # noqa: B007
        for open_idx, end_idx in _iter_top_blocks(text, token):
            block = text[open_idx:end_idx]
            m = re.search(r'\(uuid\s+"([^"]+)"\)', block)
            if m and m.group(1) == uuid:
                return token, open_idx, end_idx, block
    return None


def move_label(
    sch_path: str | Path,
    uuid: str,
    to: tuple[float, float],
    rotation: float | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Move a label by uuid; updates the label's (at) and any Intersheetrefs (at)."""
    sch_path = Path(sch_path)
    text = _read(sch_path)
    found = _find_label_block_by_uuid(text, uuid)
    if not found:
        raise ValueError(f"label with uuid {uuid!r} not found")
    token, open_idx, end_idx, block = found

    old_at = _block_at(block)
    if old_at is None:
        raise ValueError("label has no (at ...) field")
    old_x, old_y, old_rot = old_at
    new_x, new_y = float(to[0]), float(to[1])
    new_rot = float(rotation) if rotation is not None else old_rot

    # Replace the first (at ...)
    new_block = re.sub(
        r"\(at\s+-?[\d.]+\s+-?[\d.]+(?:\s+-?[\d.]+)?\s*\)",
        f"(at {_fmt_coord(new_x)} {_fmt_coord(new_y)} {_fmt_coord(new_rot)})",
        block,
        count=1,
    )
    if token == "global_label":
        # Update Intersheetrefs (at ...) — typically rot 0.
        new_block = re.sub(
            r'(\(property\s+"Intersheetrefs"[^\n]*\n\s*)\(at\s+-?[\d.]+\s+-?[\d.]+(?:\s+-?[\d.]+)?\s*\)',
            lambda m: f"{m.group(1)}(at {_fmt_coord(new_x)} {_fmt_coord(new_y)} {_fmt_coord(new_rot)})",
            new_block,
            count=1,
        )

    new_text = text[:open_idx] + new_block + text[end_idx:]
    changed = _maybe_write(sch_path, text, new_text, dry_run)
    return {
        "action": "move_label",
        "changed": changed,
        "diff": _diff(text, new_text, sch_path),
        "details": {
            "uuid": uuid,
            "kind": token,
            "old": {"x": old_x, "y": old_y, "rotation": old_rot},
            "new": {"x": new_x, "y": new_y, "rotation": new_rot},
        },
    }


def delete_label(
    sch_path: str | Path,
    uuid: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    sch_path = Path(sch_path)
    text = _read(sch_path)
    found = _find_label_block_by_uuid(text, uuid)
    if not found:
        raise ValueError(f"label with uuid {uuid!r} not found")
    token, open_idx, end_idx, _block = found
    start, stop = _expand_block_with_indent(text, open_idx, end_idx)
    new_text = text[:start] + text[stop:]
    changed = _maybe_write(sch_path, text, new_text, dry_run)
    return {
        "action": "delete_label",
        "changed": changed,
        "diff": _diff(text, new_text, sch_path),
        "details": {"uuid": uuid, "kind": token},
    }


# ---------------------------------------------------------------------------
# Junctions
# ---------------------------------------------------------------------------


def _junction_block(x: float, y: float, uuid_str: str) -> str:
    return (
        f"\t(junction\n"
        f"\t\t(at {_fmt_coord(x)} {_fmt_coord(y)})\n"
        f"\t\t(diameter 0)\n"
        f"\t\t(color 0 0 0 0)\n"
        f'\t\t(uuid "{uuid_str}")\n'
        f"\t)\n"
    )


def add_junction(
    sch_path: str | Path,
    at: tuple[float, float],
    dry_run: bool = False,
) -> dict[str, Any]:
    sch_path = Path(sch_path)
    text = _read(sch_path)
    uuid_str = _new_uuid()
    block = _junction_block(at[0], at[1], uuid_str)

    last_end: int | None = None
    for open_idx, end_idx in _iter_top_blocks(text, "junction"):
        last_end = end_idx
    if last_end is not None:
        insert_at = last_end
        if insert_at < len(text) and text[insert_at] == "\n":
            insert_at += 1
        new_text = text[:insert_at] + block + text[insert_at:]
    else:
        last_paren = text.rstrip().rfind(")")
        if last_paren < 0:
            raise ValueError("could not locate end of schematic")
        new_text = text[:last_paren] + block + text[last_paren:]

    changed = _maybe_write(sch_path, text, new_text, dry_run)
    return {
        "action": "add_junction",
        "changed": changed,
        "diff": _diff(text, new_text, sch_path),
        "details": {"uuid": uuid_str, "at": [float(at[0]), float(at[1])]},
    }


def delete_junction(
    sch_path: str | Path,
    uuid: str | None = None,
    at: tuple[float, float] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    sch_path = Path(sch_path)
    text = _read(sch_path)
    if uuid is None and at is None:
        raise ValueError("delete_junction requires uuid or at")

    target: tuple[int, int] | None = None
    matched_uuid: str | None = None
    matched_at: tuple[float, float, float] | None = None
    for open_idx, end_idx in _iter_top_blocks(text, "junction"):
        block = text[open_idx:end_idx]
        juuid = _block_uuid(block)
        jat = _block_at(block)
        if uuid is not None and juuid == uuid:
            target = (open_idx, end_idx)
            matched_uuid = juuid
            matched_at = jat
            break
        if uuid is None and at is not None and jat is not None:
            if _coords_close(jat[0], at[0]) and _coords_close(jat[1], at[1]):
                target = (open_idx, end_idx)
                matched_uuid = juuid
                matched_at = jat
                break

    if target is None:
        raise ValueError("no matching junction found")
    start, stop = _expand_block_with_indent(text, target[0], target[1])
    new_text = text[:start] + text[stop:]
    changed = _maybe_write(sch_path, text, new_text, dry_run)
    return {
        "action": "delete_junction",
        "changed": changed,
        "diff": _diff(text, new_text, sch_path),
        "details": {
            "uuid": matched_uuid,
            "at": list(matched_at[:2]) if matched_at else None,
        },
    }


__all__ = [
    "move_symbol",
    "add_wire",
    "delete_wire",
    "add_label",
    "move_label",
    "delete_label",
    "add_junction",
    "delete_junction",
]
