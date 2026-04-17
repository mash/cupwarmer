---
name: kicad-text-collision-fix
description: Detect and fix overlapping text, values, references, and global-label frames in KiCad schematic files by exporting SVG, building bbox collisions, searching nearby candidates, applying kiutils edits, and validating with roundtrip/ERC.
---

# KiCad Text Collision Fix

Use this when a user points out that KiCad schematic text is hard to read because:

- a `Value` overlaps a wire, component, or another text
- a `Reference` overlaps nearby geometry
- a `global_label` overlaps another text
- the visible KiCad label frame overlaps a `Value` or another label

This skill is for **text/layout cleanup** in `.kicad_sch`. Use `kicad-schematic-edit` for general schematic editing and `kicad-validate` for full validation.

## Core workflow

1. Export the edited sheet to SVG.
2. Run the collision detector on the schematic and SVG.
3. If needed, build a small candidate list around the target text and run the candidate searcher.
4. Apply the chosen position with `kiutils`.
5. Re-export SVG and rerun collision detection.
6. Validate with roundtrip and ERC.

## Important rule

For `global_label`, do **not** rely only on glyph bbox. KiCad draws a visible label frame; the detector in this skill reads that `SVG path` and uses the frame bbox for collisions.

For `Reference` and `Value`, treat overlap with the **same component body** as a real collision. Do not suppress owner-component hits: if text sits on top of its own symbol body, the detector should report that component.

## Scripts

- `scripts/kicad_sch_bbox_collisions.py`
  SVG-based collision detector for:
  - text vs text
  - text vs wire
  - text vs component bbox
  - text vs own component bbox
  - global-label frame vs text/wire/component

- `scripts/search_text_candidates.py`
  Generic candidate searcher for one `property` or one `global_label`.

- `scripts/text_collision_core.py`
  Shared bbox logic.

## Typical commands

Export SVG:

```bash
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
"$KICAD_CLI" sch export svg \
  --output tmp/rx-power-post-svg \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch
```

Detect collisions:

```bash
python3 skills/kicad-text-collision-fix/scripts/kicad_sch_bbox_collisions.py \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  tmp/rx-power-post-svg/rx-power.svg
```

Search candidates for a property:

```bash
python3 skills/kicad-text-collision-fix/scripts/search_text_candidates.py \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --target-kind property \
  --ref C5 \
  --key Value \
  --text 47nF \
  --candidates tmp/c5-value-candidates.json \
  --anchor-x 78.74 \
  --anchor-y 68.58
```

Search candidates for a global label:

```bash
python3 skills/kicad-text-collision-fix/scripts/search_text_candidates.py \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --target-kind global_label \
  --text RX_NTC \
  --match-x 81.28 \
  --match-y 66.04 \
  --candidates tmp/rx-ntc-candidates.json
```

## Candidate file format

JSON array of positions:

```json
[
  {"x": 72.39, "y": 71.12, "angle": 90},
  {"x": 73.66, "y": 69.85, "angle": 0}
]
```

## Candidate search rules

- Prefer the nearest collision-free candidate to the intended anchor.
- For duplicate texts, identify the target by `owner_ref + owner_key` for properties, or by `text + original position` for labels.
- When a nearby open area is visually obvious, make sure the candidate list actually covers it before concluding there is no valid placement.
- If one text cannot be moved closer without collisions, search moving the neighboring text too, but do that as a second pass.

## Validation

Run after edits:

```bash
python3 tmp/roundtrip_sch.py hardware/kicad/cupwarmer-hw/<edited-file>.kicad_sch
```

```bash
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
"$KICAD_CLI" sch erc \
  --exit-code-violations \
  --output tmp/cupwarmer-erc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

Expected:

- roundtrip `100.0%`
- ERC count does not increase
- exported SVG matches the intended cleanup
