---
name: kicad-hardware-editing
description: Edit and inspect KiCad hardware design files for this repository under `hardware/kicad/cupwarmer-hw`. Use the current KiCad project structure, validate with kicad-validate, and score schematic layout with kicad-schematic-score when visual readability matters.
---

# KiCad Hardware Editing

Primary hardware-editing workflow for the Cup Warmer KiCad project.

## Scope

KiCad project: `hardware/kicad/cupwarmer-hw`

| File type | Approach |
|---|---|
| `.kicad_sch` | Minimal S-expression or kiutils edit; preserve KiCad 10 formatting and UUIDs |
| `.kicad_pcb` | Manual S-expression edit (minimal, local changes only) |
| `.kicad_pro` | JSON edit (minimal) |
| `.kicad_prl` | Do not edit unless explicitly asked |
| `.kicad_sym` | Keep in sync with embedded `lib_symbols` when changing custom symbols |

Current schematic hierarchy:

- `cupwarmer-hw.kicad_sch` top sheet
- `rx-power.kicad_sch`
- `heater-control.kicad_sch`
- `sensors-logic.kicad_sch`

Read before editing:
- `hardware/kicad/cupwarmer-hw/README.md`
- `hardware/schematic/README.md`
- `hardware/pcb/README.md`

## Key Rules

### Schematic edits

Prefer the least invasive edit that preserves KiCad 10 S-expression structure. Use kiutils only when it can round-trip the touched construct safely; otherwise make a tightly scoped text edit and validate with KiCad CLI.

When adding pins, update both the `.kicad_sch` embedded `lib_symbols` and the standalone `cupwarmer.kicad_sym` file.

### Coordinate system

KiCad 10: `y_schematic = symbol_center_y - pin_symbol_y` (Y negated).

Always `round(value, 2)` before writing coordinates.

### Connection requirements

Wires need: `stroke = Stroke(width=0, type="solid")`. UUID is auto-generated.

Labels: clone from existing (never construct Justify from string).

### Layout readability

Use `kicad-schematic-score` before and after visual schematic cleanup. It scores text/label collisions, wire overlaps, symbol-wire conflicts, near-symbol clearance, and wire-corner count including perpendicular T-junction stubs.

## Workflow

### 1. Pre-edit: capture baseline

```bash
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
"$KICAD_CLI" sch erc --exit-code-violations \
  --output tmp/cupwarmer-pre-erc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
"$KICAD_CLI" sch export netlist \
  --output tmp/cupwarmer-pre.net \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

### 2. Edit

Make the smallest schematic, board, project, or symbol-library change that satisfies the request.

If adding pins to symbols: update the embedded `lib_symbols` entry in the affected schematic and the matching symbol in `cupwarmer.kicad_sym`.

### 3. Validate

Use `kicad-validate`:
- ERC: no new violations
- Netlist: expected changes only
- SVG export for edited schematic sheets
- `kicad-schematic-score` if the change affects schematic readability

### 4. Review

- New ERC violations: check coordinates, stroke type, and lib_symbols integrity
- Netlist mismatch: investigate unintended connectivity changes
- Worse schematic score: inspect collision records and wire-corner count before accepting the layout

## Board Editing Rules

Keep stable: `layers`, `setup`, `setup.stackup`, `Edge.Cuts`, title block.

High-risk: `net`, `footprint`, `segment`, `via`, `zone`.

4-layer stackup unless explicitly changed. RX, heater power, control stay separated.

## Project Settings

Treat `.kicad_pro` as JSON. Minimal edits only.
