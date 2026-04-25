---
name: kicad-schematic-score
description: Evaluate a KiCad schematic's current visual layout state and assign deterministic penalty points without modifying the schematic. Use when checking label/property collisions, label-to-pin crowding, wire/text overlaps, symbol-wire overlaps, near-symbol wire clearance, wire-corner/T-junction count, or comparing before/after schematic readability scores.
---

# KiCad Schematic Score

Use this skill when the user wants to **evaluate only**. Do not optimize, move symbols, rewrite wires, or edit `.kicad_sch` files as part of this skill.

## What It Scores

The score is a penalty total: lower is better.

- visible text/property/global-label collisions
- global-label frames touching or crowding symbol pin stubs
- text or label frames overlapping wires
- symbol body vs wire overlap
- near-symbol wire clearance for `PASSIVE_2` bodies
- simple wire-corner count, including wire endpoints that T-junction into a perpendicular wire segment

The output includes both a numeric breakdown and the concrete collision records used to assign points.

## Scripts

- `scripts/score_schematic.py`: Main command-line entry point. Exports the schematic to SVG with `kicad-cli`, combines SVG text geometry with KiCad schematic structure, computes collision records, counts wire corners/T-junctions, applies penalty weights, and prints the final JSON score.
- `scripts/kicad_sch_bbox_collisions.py`: Geometry extraction and collision helper. Parses rendered SVG text bounding boxes, matches rendered labels/properties back to KiCad schematic targets, collects wire segments and symbol/pin boxes from `.kicad_sch`, and can be run directly for focused collision debugging against an already exported SVG.
- `scripts/text_collision_core.py`: Shared rectangle math. Defines `Rect`, collision padding rules for global labels and symbol properties, and text/text frame intersection helpers used by the other scripts.

## Command

```bash
python3 .agents/skills/kicad-schematic-score/scripts/score_schematic.py \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch
```

Optional margin:

```bash
python3 .agents/skills/kicad-schematic-score/scripts/score_schematic.py \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --margin 0.05
```

Focused collision debugging after exporting an SVG yourself:

```bash
python3 .agents/skills/kicad-schematic-score/scripts/kicad_sch_bbox_collisions.py \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  tmp/cupwarmer-sch-svg/rx-power.svg \
  --only-text 'SYS_GND|RX_NTC' \
  --json
```

## Interpretation

- `score.total`: total penalty points for the current schematic state.
- `collision_count`: number of visible text/label collision records.
- `wire_hits`: text or label collisions with wires.
- `component_hits`: text or labels colliding with symbol bodies or pin stubs.
- `text_hits`: text-to-text collisions.
- `symbol_wire_conflict_count`: symbol body directly overlapped by a wire.
- `symbol_wire_clearance_count`: wire is visually too close to a symbol body.
- `wire_corner_count`: two-segment bend points plus wire endpoints that T-junction into a perpendicular wire segment.

Report the score and the highest-impact collision records. If the user asks for fixes, switch to `kicad-hardware-editing`.
