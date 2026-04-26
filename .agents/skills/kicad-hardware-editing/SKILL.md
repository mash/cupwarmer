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
- A worse `sch inspect` score is acceptable in stage 1 if connectivity is correct; do not chase it here.

### 5. Hand off to stage 2 (visual cleanup)

Stage 1 ends once ERC and netlist are correct. If the user wants score/layout tightening on the edited sheet, hand off to `kicad-sch-cleanup-loop` with the sheet path. Do not perform score-driven layout work in this skill.

## Board editing

Keep stable: `layers`, `setup`, `setup.stackup`, `Edge.Cuts`, title block. High-risk: `net`, `footprint`, `segment`, `via`, `zone`. 4-layer stackup unless explicitly changed; RX, heater power, control stay separated.

## Project settings

`.kicad_pro` is JSON. Minimal edits only.
