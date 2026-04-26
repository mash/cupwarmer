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

- `scripts/score_schematic.py`: main entry point — exports SVG via `kicad-cli`, computes collisions and corners, prints JSON score.
- `scripts/kicad_sch_bbox_collisions.py`: standalone collision helper — run against an already-exported SVG for focused debugging.
- `scripts/text_collision_core.py`: shared `Rect`/padding/intersection helpers.

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

- `score.total`: total penalty (lower is better).
- `collision_count` / `wire_hits` / `component_hits` / `text_hits`: text/label collision records, broken down by what they hit (wires / symbol bodies & pin stubs / other text).
- `symbol_wire_conflict_count`: symbol body directly overlapped by a wire.
- `symbol_wire_clearance_count`: wire visually too close to a symbol body.
- `wire_corner_count`: two-segment bend points + wire endpoints T-junctioning into a perpendicular segment.

Report the score and the highest-impact collision records. If `collision_count` is low, also list the dominant numeric penalty contributors (e.g. `wire_corner_penalty`, `symbol_wire_clearance_count`). If the user asks for fixes, switch to `kicad-hardware-editing`.
