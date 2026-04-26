---
name: kicad-hardware-editing
description: Stage 1 (functional) workflow for editing KiCad hardware design files in this repository under `hardware/kicad/cupwarmer-hw`. Covers connectivity, nets, symbols, pins, ERC, and netlist correctness. Use `kicad-tool` for all KiCad CLI operations and validation. Score / layout tightening (stage 2) is delegated to `kicad-sch-cleanup-loop`.
---

# KiCad Hardware Editing

Primary editing workflow for the Cup Warmer KiCad project at `hardware/kicad/cupwarmer-hw`.

Read `hardware/kicad/cupwarmer-hw/README.md` before editing.

For any KiCad CLI invocation (render, inspect, ERC, netlist, validate, DRC), **read the `kicad-tool` skill via the Skill tool first** to get exact subcommands and flags.

## File types

| File | Approach |
|---|---|
| `.kicad_sch` | Prefer `sch edit ...` subcommands; fall back to minimal S-expression text edit for cases not yet automated. Preserve KiCad 10 formatting and UUIDs |
| `.kicad_pcb` | Manual S-expression edit (minimal, local only) |
| `.kicad_pro` | JSON edit (minimal) |
| `.kicad_prl` | Do not edit unless explicitly asked |
| `.kicad_sym` | Keep in sync with embedded `lib_symbols` when changing custom symbols |

Sheets: `cupwarmer-hw.kicad_sch` (top), `rx-power.kicad_sch`, `heater-control.kicad_sch`, `sensors-logic.kicad_sch`.

## Key rules

- For automated cases (move/add/delete symbol, wire, label, junction), use `sch edit ...` — see `kicad-tool`. Always pass `--dry-run` first, then re-run without it. Validate via `kicad-tool` after every edit.
- For cases not yet automated (e.g. adding pins to symbols), make the smallest S-expression text edit that preserves KiCad 10 structure.
- Adding pins to symbols (manual): update both the affected schematic's embedded `lib_symbols` **and** `cupwarmer.kicad_sym`. Pin coordinate transform: `y_schematic = symbol_center_y - pin_symbol_y` (Y negated). `round(value, 2)` before writing.

### Automated `sch edit` subcommands

```
sch edit symbol move --ref REF --to X,Y [--rotation R]
sch edit wire add --from X,Y --to X,Y
sch edit wire delete --uuid U | --from X,Y --to X,Y
sch edit label add --kind global|hier|local --name N --at X,Y [--rotation R] [--justify J]
sch edit label move --uuid U --to X,Y [--rotation R]
sch edit label delete --uuid U
sch edit junction add --at X,Y
sch edit junction delete --uuid U | --at X,Y
```

All accept `--dry-run` and `--json`.

### Use `sch query` to gather coordinates

Read-only inspection — prefer it over grepping `.kicad_sch`:

- `sch query symbol --ref REF` for symbol position/rotation.
- `sch query pin --ref REF [--number N]` for absolute pin coordinates.
- `sch query region --bbox X1,Y1,X2,Y2` to list everything in an area.
- Other read-only forms: `sch query net|wire|label|lib-symbol|list`.

## Workflow

This skill is **stage 1: functional editing**. Visual/score cleanup is stage 2 and lives in `kicad-sch-cleanup-loop` — finish the functional edit and validate it here, then hand off if score improvement is wanted.

### 1. Pre-edit baseline

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch --json \
  > tmp/validate-pre.json
```

(Or run `sch erc` and `sch netlist` individually if you need separate `tmp/cupwarmer-pre-erc.rpt` / `tmp/cupwarmer-pre.net` artifacts — see `kicad-validate`.)

### 2. Edit (functional)

Smallest change satisfying the request. Pin additions: keep embedded `lib_symbols` and `cupwarmer.kicad_sym` in sync.

Scope of stage 1: connectivity, nets, symbols, pins, values, hierarchy, ERC correctness. Do **not** chase `sch inspect` score, collisions, `wire_corner_count`, `diagonal_wire_penalty`, or label/value tightening here — that is stage 2.

If the new edit happens to introduce obvious local mess (overlapping label, crossing wire) that would block reading the diff, fix only that local mess. Anything broader belongs to the cleanup loop.

#### Minimal worked example: add a global label

```
sch edit label add --kind global --name <NAME> --at X,Y [--rotation R] [--justify J] --dry-run
```

Re-run without `--dry-run` to apply. Use `sch query` (above) to find coordinates first.

### 3. Validate

Use `kicad-validate` (one-shot `sch validate --sheet <edited>`).

### 4. Review

- New ERC violations → check coordinates, stroke type, `lib_symbols` integrity (intentional-violation handling lives in `kicad-validate`).
- Netlist mismatch → investigate unintended connectivity.
- A worse `sch inspect` score is acceptable in stage 1 if connectivity is correct; do not chase it here.

### 5. Hand off to stage 2 (visual cleanup)

Stage 1 ends once ERC and netlist are correct. If the user wants score/layout tightening on the edited sheet, hand off to `kicad-sch-cleanup-loop` with the sheet path. Do not perform score-driven layout work in this skill.

## Board editing

Keep stable: `layers`, `setup`, `setup.stackup`, `Edge.Cuts`, title block. High-risk: `net`, `footprint`, `segment`, `via`, `zone`. 4-layer stackup unless explicitly changed; RX, heater power, control stay separated.

## Project settings

`.kicad_pro` is JSON. Minimal edits only.
