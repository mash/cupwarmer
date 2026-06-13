#!/usr/bin/env python3
"""Generate the cupwarmer flexible-heater KiCad board."""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "heater.kicad_pcb"
PROJECT = ROOT / "heater.kicad_pro"
README = ROOT / "README.md"

CENTER_X = 100.0
CENTER_Y = 100.0
OUTLINE_RADIUS = 27.5


def uid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"cupwarmer-heater:{name}"))


def fmt(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def line(layer: str, x1: float, y1: float, x2: float, y2: float, width: float, name: str) -> str:
    return (
        f'\t(gr_line (start {fmt(x1)} {fmt(y1)}) (end {fmt(x2)} {fmt(y2)})\n'
        f'\t\t(stroke (width {fmt(width)}) (type solid)) (layer "{layer}") (uuid "{uid(name)}"))'
    )


def text(
    layer: str,
    value: str,
    x: float,
    y: float,
    size: float,
    name: str,
    justify: str = "left bottom",
) -> str:
    escaped = value.replace('"', '\\"')
    return (
        f'\t(gr_text "{escaped}" (at {fmt(x)} {fmt(y)} 0) (layer "{layer}") (uuid "{uid(name)}")\n'
        f'\t\t(effects (font (size {fmt(size)} {fmt(size)}) (thickness {fmt(size / 10)})) '
        f'(justify {justify})))'
    )


def board_text() -> str:
    outline = '\n'.join(
        line(
            "Edge.Cuts",
            CENTER_X + OUTLINE_RADIUS * math.cos(2 * math.pi * i / 96),
            CENTER_Y + OUTLINE_RADIUS * math.sin(2 * math.pi * i / 96),
            CENTER_X + OUTLINE_RADIUS * math.cos(2 * math.pi * (i + 1) / 96),
            CENTER_Y + OUTLINE_RADIUS * math.sin(2 * math.pi * (i + 1) / 96),
            0.10,
            f"edge-{i:02d}",
        )
        for i in range(96)
    )

    return f'''(kicad_pcb
\t(version 20250114)
\t(generator "cupwarmer-heater-generator")
\t(generator_version "1")
\t(general
\t\t(thickness 0.2)
\t)
\t(paper "A4")
\t(title_block
\t\t(title "Cup Warmer Flexible Heater")
\t\t(date "2026-05-09")
\t\t(rev "v1")
\t\t(company "cupwarmer")
\t\t(comment 1 "JLCPCB flexible heater order file")
\t\t(comment 2 "Outline 55 mm diameter, sized to thermal stack (aluminum spreader 54.5 mm, heater seat), not the 50 mm control PCB")
\t\t(comment 3 "No heater routing drawn; JLCPCB to route for 12 ohm at 12 V")
\t)
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(31 "B.Cu" signal)
\t\t(32 "B.Adhes" user "B.Adhesive")
\t\t(33 "F.Adhes" user "F.Adhesive")
\t\t(34 "B.Paste" user)
\t\t(35 "F.Paste" user)
\t\t(36 "B.SilkS" user "B.Silkscreen")
\t\t(37 "F.SilkS" user "F.Silkscreen")
\t\t(38 "B.Mask" user)
\t\t(39 "F.Mask" user)
\t\t(40 "Dwgs.User" user "User.Drawings")
\t\t(41 "Cmts.User" user "User.Comments")
\t\t(44 "Edge.Cuts" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints yes)
\t)
\t(net 0 "")
\t(net 1 "H_PLUS")
\t(net 2 "H_MINUS")
\t(net 3 "NTC")
\t(net 4 "NTC_GND")
\t(footprint "Heater:LeadoutPads"
\t\t(layer "F.Cu")
\t\t(uuid "{uid("leadout-footprint")}")
\t\t(at 100 121.7 0)
\t\t(property "Reference" "J1" (at 0 -4 0) (layer "F.Fab") (uuid "{uid("leadout-ref")}")
\t\t\t(effects (font (size 1 1) (thickness 0.15))))
\t\t(property "Value" "Heater and NTC leads" (at 0 4 0) (layer "F.Fab") (uuid "{uid("leadout-val")}")
\t\t\t(effects (font (size 1 1) (thickness 0.15))))
\t\t(pad "1" smd roundrect (at -10 0 0) (size 4 5) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2)
\t\t\t(net 1 "H_PLUS") (pinfunction "H+") (pintype "passive") (uuid "{uid("pad-h-plus")}"))
\t\t(pad "2" smd roundrect (at -3 0 0) (size 2 3) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2)
\t\t\t(net 3 "NTC") (pinfunction "NTC") (pintype "passive") (uuid "{uid("pad-ntc-lead")}"))
\t\t(pad "3" smd roundrect (at 3 0 0) (size 2 3) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2)
\t\t\t(net 4 "NTC_GND") (pinfunction "NTC_GND") (pintype "passive") (uuid "{uid("pad-ntc-gnd-lead")}"))
\t\t(pad "4" smd roundrect (at 10 0 0) (size 4 5) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2)
\t\t\t(net 2 "H_MINUS") (pinfunction "H-") (pintype "passive") (uuid "{uid("pad-h-minus")}"))
\t)
\t(footprint "Heater:NTCPads"
\t\t(layer "F.Cu")
\t\t(uuid "{uid("ntc-footprint")}")
\t\t(at 100 100 0)
\t\t(property "Reference" "NTC1" (at 0 -3 0) (layer "F.Fab") (uuid "{uid("ntc-ref")}")
\t\t\t(effects (font (size 1 1) (thickness 0.15))))
\t\t(property "Value" "100k NTC 0603" (at 0 3 0) (layer "F.Fab") (uuid "{uid("ntc-val")}")
\t\t\t(effects (font (size 1 1) (thickness 0.15))))
\t\t(pad "1" smd roundrect (at -0.825 0 0) (size 0.9 1.0) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.25)
\t\t\t(net 3 "NTC") (pinfunction "NTC") (pintype "passive") (uuid "{uid("pad-ntc")}"))
\t\t(pad "2" smd roundrect (at 0.825 0 0) (size 0.9 1.0) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.25)
\t\t\t(net 4 "NTC_GND") (pinfunction "NTC_GND") (pintype "passive") (uuid "{uid("pad-ntc-gnd")}"))
\t)
{outline}
{text("Cmts.User", "Order notes: no heater pattern drawn. Please route 12R heater for 12V/12W and place 100k NTC near center.", 68, 66, 1.0, "order-note")}
{text("F.SilkS", "H+", 90, 119.2, 1.0, "h-plus-label", "bottom")}
{text("F.SilkS", "NTC", 97, 119.2, 0.75, "ntc-lead-label", "bottom")}
{text("F.SilkS", "NTC_GND", 103, 119.2, 0.6, "ntc-gnd-lead-label", "bottom")}
{text("F.SilkS", "H-", 110, 119.2, 1.0, "h-minus-label", "bottom")}
{text("F.SilkS", "NTC", 100, 96.5, 1.0, "ntc-label", "bottom")}
)'''


def project_text() -> str:
    project = {
        "board": {"design_settings": {"defaults": {"board_outline_line_width": 0.1}}},
        "meta": {"filename": "heater.kicad_pro", "version": 1},
        "project": {"title": "Cup Warmer Flexible Heater"},
    }
    return json.dumps(project, indent=2) + "\n"


def readme_text() -> str:
    return f"""# Cup Warmer Flexible Heater

This directory contains a KiCad-generated Gerber package for the external flexible heater.

- Board outline: 55 mm diameter, sized to the thermal stack (aluminum spreader Ø54.5 mm, heater seat Ø50.7/Ø57.2 mm) — **not** the Ø50 mm control PCB. The heater covers the spreader, seats on the bottom-tray heater-seat step, and stays under the Ø56.5 mm cup contact pad.
- Heating element routing: intentionally not drawn; ask JLCPCB to route it during engineering review
- Bottom lead-out pads: four pads labelled `H+`, `NTC`, `NTC_GND`, and `H-`
- Center NTC placement marker: `NTC` near the board center
- Target electrical spec: 12 V, about 12 W, nominal 12 ohm
- Preferred routed element material: FeCrAl 0.05 mm, adjusted by JLCPCB to hit nominal 12 ohm

JLCPCB flexible-heater order notes:

- Upload `gerber/heater-jlcpcb-flex-heater.zip`.
- Select a flexible heater service, not a normal FR-4 PCB service.
- Ask JLCPCB to route the heater pattern. The uploaded Gerber only defines the 55 mm circular shape, bottom lead-out pad locations, and requested center NTC location.
- Ask JLCPCB to manufacture the heating element as FeCrAl 0.05 mm, or adjust routing/material during engineering review to hit 12 ohm.
- Ask for an embedded 100k NTC, B25/85 approximately 4260 K, placed at the center `NTC` marker if available.
- Cable exit should be from the bottom lead-pad area. The cupwarmer PCB harness expects `H+`, `H-`, `NTC`, and `NTC_GND` as separate wires.
- The Gerber dimensions should auto-detect as 55 mm x 55 mm on JLCPCB.
"""


def main() -> None:
    BOARD.write_text(board_text() + "\n")
    PROJECT.write_text(project_text())
    README.write_text(readme_text())


if __name__ == "__main__":
    main()
