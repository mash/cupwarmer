---
name: kicad-layout-optimize
description: Optimize KiCad schematic layout by iteratively scoring visible collisions in exported SVGs, moving labels/properties first, then locally nudging symbols with attached wires when needed.
---

# KiCad Layout Optimize

Use this when a KiCad schematic is readable enough electrically but visually messy:

- `Value` / `Reference` / `global_label` placements look cramped
- moving text alone does not resolve overlaps
- a nearby symbol should move slightly to make space
- the user wants repeated local improvement rather than one-off manual cleanup

This skill is for **local schematic layout optimization**. Use:

- `kicad-schematic-edit` for direct deterministic edits
- `kicad-validate` for full validation after accepted edits

## Core workflow

1. Export the target sheet to SVG.
2. Score the current layout from visible collisions.
3. Generate local candidate moves:
   - property / label nudges first
   - owner symbol nudges second
4. Apply one move to a temp schematic.
5. Re-export, rescore, and keep only improvements.
6. Repeat until no candidate improves the score.
7. Validate accepted output with roundtrip and ERC.

## Editing rules

- Prefer text moves before symbol moves.
- Symbol moves must remain local. Do not perform broad layout reshuffles in one pass.
- When moving a symbol, preserve connectivity by moving wire endpoints that sit on the symbol pins.
- Keep rotations at `0/90/180/270`.
- Treat overlap with the owner symbol body as a real penalty.
- Treat `symbol body vs wire` overlap as a separate penalty and generate symbol moves to clear it.
- The score includes a wire-corner penalty for simple bends (`degree == 2` bend points). Junctions are not penalized in the current MVP.

## Scripts

- `scripts/layout_state.py`
  Extract symbols, properties, labels, wires, and symbol boxes from a sheet.

- `scripts/layout_score.py`
  Export SVG, run collision detection, and compute a comparable score.

- `scripts/layout_moves.py`
  Generate candidate moves and apply one move to a temporary schematic.

- `scripts/kicad_sch_bbox_collisions.py`
  Shared SVG collision detector used by the score path and debugging workflows.

- `scripts/search_text_candidates.py`
  Legacy text-only candidate evaluator kept here as a helper for debugging and narrow fixes.

- `scripts/layout_reroute.py`
  Local wire-follow behavior for small symbol nudges.

- `scripts/layout_optimize.py`
  Hill-climbing CLI that iterates until no improving move remains.

## Typical command

```bash
python3 .agents/skills/kicad-layout-optimize/scripts/layout_optimize.py \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --output tmp/rx-power-optimized.kicad_sch \
  --iterations 8 \
  --grid-step 1.27 \
  --rings 2 \
  --allow-symbol-moves
```

## Validation

Run after accepting output:

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

- score decreases monotonically for accepted moves
- no accepted move introduces worse visible collisions
- roundtrip remains `100.0%`
- ERC count does not increase
