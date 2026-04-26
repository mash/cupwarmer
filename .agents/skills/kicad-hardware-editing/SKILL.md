---
name: kicad-hardware-editing
description: Workflow for editing KiCad hardware design files in this repository under `hardware/kicad/cupwarmer-hw`. Use `kicad-tool` for all KiCad CLI operations, validation, and schematic layout inspection.
---

# KiCad Hardware Editing

Primary hardware-editing workflow for the Cup Warmer KiCad project.

## Scope

KiCad project: `hardware/kicad/cupwarmer-hw`

| File type | Approach |
|---|---|
| `.kicad_sch` | Minimal S-expression text edit; preserve KiCad 10 formatting and UUIDs |
| `.kicad_pcb` | Manual S-expression edit (minimal, local changes only) |
| `.kicad_pro` | JSON edit (minimal) |
| `.kicad_prl` | Do not edit unless explicitly asked |
| `.kicad_sym` | Keep in sync with embedded `lib_symbols` when changing custom symbols |

Current schematic hierarchy:

- `cupwarmer-hw.kicad_sch` top sheet
- `rx-power.kicad_sch`
- `heater-control.kicad_sch`
- `sensors-logic.kicad_sch`

Read `hardware/kicad/cupwarmer-hw/README.md` before editing.

## Key Rules

- Prefer the least invasive S-expression text edit that preserves KiCad 10 structure. Validate with KiCad CLI after every edit.
- Adding pins: update both the `.kicad_sch` embedded `lib_symbols` and `cupwarmer.kicad_sym`.
- Pin coordinate transform: `y_schematic = symbol_center_y - pin_symbol_y` (Y negated). `round(value, 2)` before writing.
- Wires need `(stroke (width 0) (type solid))`; generate a fresh UUID. Labels: clone an existing block — never synthesize `(justify ...)` from scratch.
- Run `kicad-tool` before/after visual cleanup edits:
  `python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch inspect <sheet> --json`.

## Workflow

### 1. Pre-edit: capture baseline

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch erc \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch \
  --report tmp/cupwarmer-pre-erc.rpt
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch netlist \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch \
  --out tmp/cupwarmer-pre.net
```

### 2. Edit

Make the smallest schematic, board, project, or symbol-library change that satisfies the request.

If adding pins to symbols: update the embedded `lib_symbols` entry in the affected schematic and the matching symbol in `cupwarmer.kicad_sym`.

#### Minimal worked example: add a global label

Most schematic edits are this shape — clone an existing block, change name/coords/UUID, do not touch surrounding indentation or trailing parens.

1. `grep -n '(global_label "<sibling>"' hardware/kicad/cupwarmer-hw/<sheet>.kicad_sch` to find an existing label to clone.
2. Read ±25 lines around the match to capture the full block (label + `effects` + `Intersheetrefs` property + `uuid`).
3. Generate a fresh UUID: `python3 -c 'import uuid; print(uuid.uuid4())'`.
4. Insert with `Edit` immediately after the sibling. Keep the exact tab indentation.
5. Adjust only: label text, `(at x y rotation)` (sheet space — no Y negation), and `uuid`.
6. **Do not** synthesize `(justify ...)` from scratch — copy from the sibling. **Do not** add `(stroke ...)` to a label.

### 3. Validate

Use `kicad-validate`:
- ERC: no new violations
- Netlist: expected changes only
- SVG export for edited schematic sheets
- `sch inspect` if the change affects schematic readability

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch \
  --sheet hardware/kicad/cupwarmer-hw/<edited-file>.kicad_sch \
  --json
```

### 4. Review

- New ERC violations: check coordinates, stroke type, and lib_symbols integrity (intentional-violation exception is handled in `kicad-validate`)
- Netlist mismatch: investigate unintended connectivity changes
- Worse schematic score: inspect collision records and wire-corner count before accepting the layout

## Board Editing Rules

Keep stable: `layers`, `setup`, `setup.stackup`, `Edge.Cuts`, title block.

High-risk: `net`, `footprint`, `segment`, `via`, `zone`.

4-layer stackup unless explicitly changed. RX, heater power, control stay separated.

## Project Settings

Treat `.kicad_pro` as JSON. Minimal edits only.
