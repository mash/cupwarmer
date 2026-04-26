---
name: kicad-hardware-editing
description: Workflow for editing KiCad hardware design files in this repository under `hardware/kicad/cupwarmer-hw`. Use `kicad-tool` for all KiCad CLI operations, validation, and schematic layout inspection.
---

# KiCad Hardware Editing

Primary editing workflow for the Cup Warmer KiCad project at `hardware/kicad/cupwarmer-hw`.

Read `hardware/kicad/cupwarmer-hw/README.md` before editing.

## File types

| File | Approach |
|---|---|
| `.kicad_sch` | Minimal S-expression text edit; preserve KiCad 10 formatting and UUIDs |
| `.kicad_pcb` | Manual S-expression edit (minimal, local only) |
| `.kicad_pro` | JSON edit (minimal) |
| `.kicad_prl` | Do not edit unless explicitly asked |
| `.kicad_sym` | Keep in sync with embedded `lib_symbols` when changing custom symbols |

Sheets: `cupwarmer-hw.kicad_sch` (top), `rx-power.kicad_sch`, `heater-control.kicad_sch`, `sensors-logic.kicad_sch`.

## Key rules

- Smallest S-expression text edit that preserves KiCad 10 structure. Validate via `kicad-tool` after every edit.
- Adding pins to symbols: update both the affected schematic's embedded `lib_symbols` **and** `cupwarmer.kicad_sym`.
- Pin coordinate transform: `y_schematic = symbol_center_y - pin_symbol_y` (Y negated). `round(value, 2)` before writing.
- Wires need `(stroke (width 0) (type solid))` and a fresh UUID. Labels: clone an existing block — never synthesize `(justify ...)` from scratch, never add `(stroke ...)` to a label.

## Workflow

### 1. Pre-edit baseline

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch --json \
  > tmp/validate-pre.json
```

(Or run `sch erc` and `sch netlist` individually if you need separate `tmp/cupwarmer-pre-erc.rpt` / `tmp/cupwarmer-pre.net` artifacts — see `kicad-validate`.)

### 2. Edit

Smallest change satisfying the request. Pin additions: keep embedded `lib_symbols` and `cupwarmer.kicad_sym` in sync.

#### Visual cleanup priority (when improving `sch inspect` score)

Preserve connectivity and functional grouping. Smallest local change first.

1. Rewire locally.
2. Rotate/flip labels and properties.
3. Rotate/flip small components.
4. Move labels and properties.
5. Move small components.
6. Move larger components or reshape the local block.
7. Never change hierarchy, net names, symbol identity, or circuit semantics solely for score.

#### Minimal worked example: add a global label

Most schematic edits follow this shape — clone an existing block, change name/coords/UUID, leave indentation and trailing parens alone.

1. `grep -n '(global_label "<sibling>"' hardware/kicad/cupwarmer-hw/<sheet>.kicad_sch` to locate a sibling.
2. Read ±25 lines to capture the full block (label + `effects` + `Intersheetrefs` property + `uuid`).
3. New UUID: `python3 -c 'import uuid; print(uuid.uuid4())'`.
4. `Edit` immediately after the sibling, preserving exact tab indentation.
5. Adjust **only** label text, `(at x y rotation)` (sheet space — no Y negation), and `uuid`.
6. Copy `(justify ...)` from the sibling. Do not add `(stroke ...)`.

### 3. Validate

Use `kicad-validate` (one-shot `sch validate --sheet <edited>`).

### 4. Review

- New ERC violations → check coordinates, stroke type, `lib_symbols` integrity (intentional-violation handling lives in `kicad-validate`).
- Netlist mismatch → investigate unintended connectivity.
- Worse `sch inspect` score → inspect collision records and `wire_corner_count` before accepting the layout.

## Board editing

Keep stable: `layers`, `setup`, `setup.stackup`, `Edge.Cuts`, title block. High-risk: `net`, `footprint`, `segment`, `via`, `zone`. 4-layer stackup unless explicitly changed; RX, heater power, control stay separated.

## Project settings

`.kicad_pro` is JSON. Minimal edits only.
