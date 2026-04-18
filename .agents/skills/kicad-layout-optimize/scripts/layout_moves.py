#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SCHEMATIC_EDIT_DIR = SKILLS_DIR / "kicad-schematic-edit" / "scripts"

for path in (SCRIPT_DIR, SCHEMATIC_EDIT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from layout_helpers import LayoutEditor
from layout_reroute import reroute_symbol_move
from layout_score import score_schematic


@dataclass(frozen=True)
class LayoutMove:
    kind: str
    text: str | None = None
    ref: str | None = None
    key: str | None = None
    match_x: float | None = None
    match_y: float | None = None
    x: float | None = None
    y: float | None = None
    angle: int | None = None
    dx: float | None = None
    dy: float | None = None
    reason: str | None = None


def generate_candidate_moves(
    payload: dict,
    grid_step: float = 1.27,
    rings: int = 2,
    allow_symbol_moves: bool = False,
) -> list[LayoutMove]:
    collisions = payload["collisions"]
    symbol_wire_conflicts = payload.get("symbol_wire_conflicts", [])
    moves: list[LayoutMove] = []
    seen: set[tuple] = set()
    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ]

    for collision in collisions:
        base_x = collision.get("matched_x", collision["anchor_x"])
        base_y = collision.get("matched_y", collision["anchor_y"])
        angle = 0
        for ring in range(1, rings + 1):
            for sx, sy in directions:
                x = round(base_x + sx * grid_step * ring, 2)
                y = round(base_y + sy * grid_step * ring, 2)
                if collision["kind"] == "property":
                    move = LayoutMove(
                        kind="property",
                        text=collision["text"],
                        ref=collision["owner_ref"],
                        key=collision["owner_key"],
                        x=x,
                        y=y,
                        angle=angle,
                        reason="nudge-property",
                    )
                else:
                    move = LayoutMove(
                        kind="global_label",
                        text=collision["text"],
                        match_x=round(collision["matched_x"], 2) if collision.get("matched_x") is not None else None,
                        match_y=round(collision["matched_y"], 2) if collision.get("matched_y") is not None else None,
                        x=x,
                        y=y,
                        angle=angle,
                        reason="nudge-global-label",
                    )
                key = tuple(asdict(move).items())
                if key not in seen:
                    seen.add(key)
                    moves.append(move)

        if allow_symbol_moves and collision.get("owner_ref"):
            for ring in range(1, rings + 1):
                for sx, sy in directions[:4]:
                    dx = round(sx * grid_step * ring, 2)
                    dy = round(sy * grid_step * ring, 2)
                    move = LayoutMove(
                        kind="symbol",
                        ref=collision["owner_ref"],
                        dx=dx,
                        dy=dy,
                        reason="nudge-owner-symbol",
                    )
                    key = tuple(asdict(move).items())
                    if key not in seen:
                        seen.add(key)
                        moves.append(move)

    if allow_symbol_moves:
        for conflict in symbol_wire_conflicts:
            for ring in range(1, rings + 1):
                for sx, sy in directions[:4]:
                    dx = round(sx * grid_step * ring, 2)
                    dy = round(sy * grid_step * ring, 2)
                    move = LayoutMove(
                        kind="symbol",
                        ref=conflict["ref"],
                        dx=dx,
                        dy=dy,
                        reason="nudge-symbol-wire-conflict",
                    )
                    key = tuple(asdict(move).items())
                    if key not in seen:
                        seen.add(key)
                        moves.append(move)
    return moves


def apply_move(source: Path, move: LayoutMove, target: Path) -> None:
    shutil.copyfile(source, target)
    ed = LayoutEditor(str(target))

    if move.kind == "property":
        if not move.ref or not move.key or move.x is None or move.y is None:
            raise ValueError(f"incomplete property move: {move}")
        sym = ed.symbols[move.ref]["sym"]
        found = False
        for prop in sym.properties:
            if prop.key == move.key and prop.value == move.text:
                prop.position.X = move.x
                prop.position.Y = move.y
                prop.position.angle = move.angle or 0
                found = True
                break
        if not found:
            raise ValueError(f"property target not found: {move}")
    elif move.kind == "global_label":
        found = False
        for gl in ed.sch.globalLabels:
            if gl.text != move.text:
                continue
            if move.match_x is not None and abs(round(gl.position.X, 2) - move.match_x) > 0.01:
                continue
            if move.match_y is not None and abs(round(gl.position.Y, 2) - move.match_y) > 0.01:
                continue
            gl.position.X = move.x
            gl.position.Y = move.y
            gl.position.angle = move.angle or 0
            found = True
            break
        if not found:
            raise ValueError(f"global label target not found: {move}")
    elif move.kind == "symbol":
        if not move.ref or move.dx is None or move.dy is None:
            raise ValueError(f"incomplete symbol move: {move}")
        info = ed.symbols[move.ref]
        reroute_symbol_move(
            ed,
            move.ref,
            round(info["x"] + move.dx, 2),
            round(info["y"] + move.dy, 2),
            angle=int(info["angle"] or 0),
            move_properties=True,
        )
    else:
        raise ValueError(f"unknown move kind: {move.kind}")

    ed.save(str(target))


def evaluate_moves(
    schematic: Path,
    moves: list[LayoutMove],
    margin: float = 0.0,
) -> list[dict]:
    results = []
    with tempfile.TemporaryDirectory(prefix="kicad-layout-moves-") as tmpdir:
        tmpdir = Path(tmpdir)
        for idx, move in enumerate(moves):
            candidate = tmpdir / f"candidate-{idx}.kicad_sch"
            apply_move(schematic, move, candidate)
            scored = score_schematic(candidate, margin=margin)
            results.append(
                {
                    "move": asdict(move),
                    "score": scored["score"],
                    "collision_count": len(scored["collisions"]),
                }
            )
    results.sort(key=lambda item: (item["score"]["total"], item["score"]["collision_count"]))
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("schematic", type=Path)
    ap.add_argument("--score-json", type=Path, required=True)
    ap.add_argument("--grid-step", type=float, default=1.27)
    ap.add_argument("--rings", type=int, default=2)
    ap.add_argument("--allow-symbol-moves", action="store_true")
    ap.add_argument("--margin", type=float, default=0.0)
    args = ap.parse_args()

    payload = json.loads(args.score_json.read_text())
    moves = generate_candidate_moves(
        payload,
        grid_step=args.grid_step,
        rings=args.rings,
        allow_symbol_moves=args.allow_symbol_moves,
    )
    print(json.dumps(evaluate_moves(args.schematic, moves, margin=args.margin), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
