---
name: kicad-hardware-editing
description: Edit and inspect KiCad hardware design files for this repository under `hardware/kicad/cupwarmer-hw`. Orchestrates subagents for schematic editing (kicad-schematic-edit) and validation (kicad-validate).
---

# KiCad Hardware Editing

Orchestrator skill. Dispatches subagents for editing and validation.

## Scope

KiCad project: `hardware/kicad/cupwarmer-hw`

| File type | Approach |
|---|---|
| `.kicad_sch` | Subagent: `kicad-schematic-edit` |
| `.kicad_pcb` | Manual S-expression edit (minimal, local changes only) |
| `.kicad_pro` | JSON edit (minimal) |
| `.kicad_prl` | Do not edit unless explicitly asked |

Read before editing:
- `hardware/kicad/cupwarmer-hw/README.md`
- `hardware/schematic/README.md`
- `hardware/pcb/README.md`

## Key Rules

### kiutils

kiutils handles all schematic operations: modifying properties, adding components/wires/labels, moving components, and adding pins to `lib_symbols`.

When adding pins, update both the `.kicad_sch` embedded `lib_symbols` and the standalone `cupwarmer.kicad_sym` file.

### Coordinate system

KiCad 10: `y_schematic = symbol_center_y - pin_symbol_y` (Y negated).

Use `skills/kicad-schematic-edit/scripts/pin_calc.py` for all pin position calculations. Always `round(value, 2)` before writing coordinates.

### Connection requirements

Wires need: `stroke = Stroke(width=0, type="solid")`. UUID is auto-generated.

Labels: clone from existing (never construct Justify from string).

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

Dispatch subagent with `kicad-schematic-edit` skill for the edit.

If adding pins to symbols: use raw text first, then kiutils for the rest.

### 3. Validate

Dispatch subagent with `kicad-validate` skill:
- Roundtrip coverage 100%
- ERC: no new violations
- Netlist: expected changes only

### 4. Review

- Roundtrip < 100%: revert, fix approach
- New ERC violations: check coordinates, stroke type, and lib_symbols integrity
- Netlist mismatch: investigate unintended connectivity changes

## Board Editing Rules

Keep stable: `layers`, `setup`, `setup.stackup`, `Edge.Cuts`, title block.

High-risk: `net`, `footprint`, `segment`, `via`, `zone`.

4-layer stackup unless explicitly changed. RX, heater power, control stay separated.

## Project Settings

Treat `.kicad_pro` as JSON. Minimal edits only.
