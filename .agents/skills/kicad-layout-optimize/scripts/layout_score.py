#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, "/Users/mash/src/github.com/mvnmgrx/kiutils/src")

from kiutils.schematic import Schematic
from kicad_sch_bbox_collisions import (
    collect_symbol_boxes,
    collect_text_targets,
    collect_wires,
    detect_collisions,
    match_rendered_to_targets,
    parse_svg_rendered_texts,
)

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
WIRE_CORNER_WEIGHT = 25.0
SYMBOL_WIRE_CONFLICT_WEIGHT = 1200.0


@dataclass
class ScoreBreakdown:
    total: float
    collision_count: int
    wire_hits: int
    component_hits: int
    text_hits: int
    collision_area: float
    wire_corner_count: int
    wire_corner_penalty: float
    symbol_wire_conflict_count: int
    symbol_wire_penalty: float


def rect_area(rect: dict | None) -> float:
    if not rect:
        return 0.0
    return max(0.0, rect["x2"] - rect["x1"]) * max(0.0, rect["y2"] - rect["y1"])


def point_key(point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0], 2), round(point[1], 2))


def direction_from(point: tuple[float, float], other: tuple[float, float]) -> tuple[int, int] | None:
    dx = round(other[0] - point[0], 2)
    dy = round(other[1] - point[1], 2)
    if abs(dx) < 0.01 and abs(dy) < 0.01:
        return None
    sx = 0 if abs(dx) < 0.01 else (1 if dx > 0 else -1)
    sy = 0 if abs(dy) < 0.01 else (1 if dy > 0 else -1)
    return (sx, sy)


def is_corner_directions(a: tuple[int, int], b: tuple[int, int]) -> bool:
    if a == b:
        return False
    if a[0] == -b[0] and a[1] == -b[1]:
        return False
    return True


def count_wire_corners(wires: list) -> int:
    incidents: dict[tuple[float, float], list[tuple[int, int]]] = {}
    for wire in wires:
        p1 = point_key(wire.p1)
        p2 = point_key(wire.p2)
        d1 = direction_from(p1, p2)
        d2 = direction_from(p2, p1)
        if d1 is not None:
            incidents.setdefault(p1, []).append(d1)
        if d2 is not None:
            incidents.setdefault(p2, []).append(d2)

    corners = 0
    for directions in incidents.values():
        if len(directions) != 2:
            continue
        if is_corner_directions(directions[0], directions[1]):
            corners += 1
    return corners


def detect_symbol_wire_conflicts(wires: list, symbol_boxes: list, margin: float = 0.0) -> list[dict]:
    conflicts: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for box in symbol_boxes:
        rect = box.bbox.normalized()
        for wire in wires:
            if not rect.intersects_segment(wire.p1, wire.p2, margin=margin):
                continue
            key = (box.ref, wire.uuid)
            if key in seen:
                continue
            seen.add(key)
            conflicts.append(
                {
                    "ref": box.ref,
                    "lib_id": box.lib_id,
                    "bbox": asdict(rect),
                    "wire": {
                        "uuid": wire.uuid,
                        "p1": wire.p1,
                        "p2": wire.p2,
                    },
                }
            )
    return conflicts


def export_svg(schematic: Path, outdir: Path) -> Path:
    subprocess.run(
        [KICAD_CLI, "sch", "export", "svg", "--output", str(outdir), str(schematic)],
        cwd=SKILLS_DIR.parents[1],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    svgs = sorted(outdir.glob("*.svg"))
    if not svgs:
        raise FileNotFoundError(f"no SVG exported into {outdir}")
    return svgs[0]


def collision_payload(schematic: Path, svg: Path, margin: float = 0.0) -> dict:
    sch = Schematic.from_file(str(schematic))
    rendered = parse_svg_rendered_texts(svg)
    targets = collect_text_targets(sch)
    matched = match_rendered_to_targets(rendered, targets)
    wires = collect_wires(sch)
    boxes = collect_symbol_boxes(sch)
    collisions = detect_collisions(matched, wires, boxes, margin=margin)
    symbol_wire_conflicts = detect_symbol_wire_conflicts(wires, boxes, margin=margin)
    return {
        "collisions": collisions,
        "wires": wires,
        "symbol_wire_conflicts": symbol_wire_conflicts,
    }


def score_payload(payload: dict) -> ScoreBreakdown:
    collisions = payload["collisions"]
    wires = payload["wires"]
    symbol_wire_conflicts = payload["symbol_wire_conflicts"]
    wire_hits = sum(len(c["wire_hits"]) for c in collisions)
    component_hits = sum(len(c["component_hits"]) for c in collisions)
    text_hits = sum(len(c["text_hits"]) for c in collisions)
    collision_area = sum(rect_area(c.get("collision_bbox")) for c in collisions)
    wire_corner_count = count_wire_corners(wires)
    wire_corner_penalty = wire_corner_count * WIRE_CORNER_WEIGHT
    symbol_wire_conflict_count = len(symbol_wire_conflicts)
    symbol_wire_penalty = symbol_wire_conflict_count * SYMBOL_WIRE_CONFLICT_WEIGHT
    total = (
        1000.0 * wire_hits
        + 1000.0 * component_hits
        + 800.0 * text_hits
        + 50.0 * len(collisions)
        + collision_area
        + wire_corner_penalty
        + symbol_wire_penalty
    )
    return ScoreBreakdown(
        total=round(total, 3),
        collision_count=len(collisions),
        wire_hits=wire_hits,
        component_hits=component_hits,
        text_hits=text_hits,
        collision_area=round(collision_area, 3),
        wire_corner_count=wire_corner_count,
        wire_corner_penalty=wire_corner_penalty,
        symbol_wire_conflict_count=symbol_wire_conflict_count,
        symbol_wire_penalty=symbol_wire_penalty,
    )


def score_schematic(schematic: Path, margin: float = 0.0) -> dict:
    with tempfile.TemporaryDirectory(prefix="kicad-layout-score-") as tmpdir:
        svg = export_svg(schematic, Path(tmpdir))
        payload = collision_payload(schematic, svg, margin=margin)
    score = score_payload(payload)
    return {
        "score": asdict(score),
        "collisions": payload["collisions"],
        "symbol_wire_conflicts": payload["symbol_wire_conflicts"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("schematic", type=Path)
    ap.add_argument("--margin", type=float, default=0.0)
    args = ap.parse_args()
    print(json.dumps(score_schematic(args.schematic, margin=args.margin), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
