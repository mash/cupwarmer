#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SCHEMATIC_EDIT_DIR = SKILLS_DIR / "kicad-schematic-edit" / "scripts"

if str(SCHEMATIC_EDIT_DIR) not in sys.path:
    sys.path.insert(0, str(SCHEMATIC_EDIT_DIR))

from layout_helpers import LayoutEditor


def reroute_symbol_move(
    editor: LayoutEditor,
    ref: str,
    x: float,
    y: float,
    angle: int | None = None,
    tolerance: float = 0.1,
    move_properties: bool = True,
) -> None:
    editor.move_symbol_with_attached_wires(
        ref,
        x,
        y,
        angle=angle,
        tolerance=tolerance,
        move_properties=move_properties,
    )
