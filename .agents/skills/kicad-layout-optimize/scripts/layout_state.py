#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SCHEMATIC_EDIT_DIR = SKILLS_DIR / "kicad-schematic-edit" / "scripts"

for path in (SCRIPT_DIR, SCHEMATIC_EDIT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
sys.path.insert(0, "/Users/mash/src/github.com/mvnmgrx/kiutils/src")

from kiutils.schematic import Schematic
from layout_helpers import LayoutEditor
from kicad_sch_bbox_collisions import collect_symbol_boxes, collect_wires


@dataclass
class SymbolState:
    ref: str
    entry: str
    x: float
    y: float
    angle: int


@dataclass
class PropertyState:
    ref: str
    key: str
    text: str
    x: float
    y: float
    angle: int
    hidden: bool


@dataclass
class LabelState:
    text: str
    x: float
    y: float
    angle: int


@dataclass
class LayoutState:
    schematic: str
    symbols: list[SymbolState]
    properties: list[PropertyState]
    global_labels: list[LabelState]
    wires: list[dict]
    symbol_boxes: list[dict]
    pin_positions: dict[str, dict[str, tuple[float, float]]]


def build_layout_state(schematic: Path) -> LayoutState:
    ed = LayoutEditor(str(schematic))
    sch = Schematic.from_file(str(schematic))

    symbols = [
        SymbolState(
            ref=ref,
            entry=info["entry"],
            x=round(info["x"], 2),
            y=round(info["y"], 2),
            angle=int(info["angle"] or 0),
        )
        for ref, info in sorted(ed.symbols.items())
    ]

    properties: list[PropertyState] = []
    for ref, info in sorted(ed.symbols.items()):
        sym = info["sym"]
        for prop in sym.properties:
            properties.append(
                PropertyState(
                    ref=ref,
                    key=prop.key,
                    text=prop.value,
                    x=round(prop.position.X, 2),
                    y=round(prop.position.Y, 2),
                    angle=int(prop.position.angle or 0),
                    hidden=bool(getattr(prop.effects, "hide", False)),
                )
            )

    labels = [
        LabelState(
            text=gl.text,
            x=round(gl.position.X, 2),
            y=round(gl.position.Y, 2),
            angle=int(gl.position.angle or 0),
        )
        for gl in sch.globalLabels
    ]

    wires = [
        {"uuid": wire.uuid, "p1": wire.p1, "p2": wire.p2}
        for wire in collect_wires(sch)
    ]
    symbol_boxes = [
        {"ref": box.ref, "lib_id": box.lib_id, "bbox": asdict(box.bbox.normalized())}
        for box in collect_symbol_boxes(sch)
    ]
    pin_positions = {
        ref: {name: (round(pos[0], 2), round(pos[1], 2)) for name, pos in ed.symbol_pin_positions(ref).items()}
        for ref in sorted(ed.symbols)
    }
    return LayoutState(
        schematic=str(schematic),
        symbols=symbols,
        properties=properties,
        global_labels=labels,
        wires=wires,
        symbol_boxes=symbol_boxes,
        pin_positions=pin_positions,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("schematic", type=Path)
    args = ap.parse_args()
    state = build_layout_state(args.schematic)
    print(json.dumps(asdict(state), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
