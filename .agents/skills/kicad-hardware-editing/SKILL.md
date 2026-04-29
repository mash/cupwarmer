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
| `.kicad_sch` | Use `sch edit ...` subcommands. Preserve KiCad 10 formatting and UUIDs |
| `.kicad_pcb` | Manual S-expression edit (minimal, local only) |
| `.kicad_pro` | JSON edit (minimal) |
| `.kicad_prl` | Do not edit unless explicitly asked |
| `.kicad_sym` | Keep in sync with embedded `lib_symbols` when changing custom symbols |

Sheets: `cupwarmer-hw.kicad_sch` (top), `rx-power.kicad_sch`, `heater-control.kicad_sch`, `sensors-logic.kicad_sch`.

## Key rules

- For automated cases (move/add/delete symbol, wire, label, junction; add-pin), use `sch edit ...` — see `kicad-tool`. Always pass `--dry-run` first, then re-run without it. Validate via `kicad-tool` after every edit.
- Adding pins to symbols: use `sch edit symbol add-pin ...` — it updates both the schematic's embedded `lib_symbols` and `cupwarmer.kicad_sym` together. Coordinates are symbol-local (no Y negation here).

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

Read-only inspection. Do not `Read`/`cat`/`grep` `.kicad_sch` — raw S-expression files are huge and burn the context window; `sch query` returns scoped JSON.

- `sch query symbol --ref REF` — symbol position/rotation.
- `sch query pin REF.PIN` — absolute pin coordinates (+ net with `--netlist`).
- `sch query region --bbox X1,Y1,X2,Y2` — everything in an area.
- `sch query net|wire|label|lib-symbol|list` — other read-only forms.

If a needed query is missing, extend `kicad-tool` rather than fall back to raw reads.

## Workflow

This skill is **stage 1: functional editing**. Visual/score cleanup is stage 2 and lives in `kicad-sch-cleanup-loop` — finish the functional edit and validate it here, then hand off if score improvement is wanted.

### 0. Plan and get approval (mandatory)

Before any `sch edit`, state and wait for approval:

1. **Goal** — what the design should do (design terms, not "add wires").
2. **Problem** — what's missing/wrong, citing specific symbols/nets/pins (via `sch query`).
3. **Approach** — proposed change + alternatives considered + why this one. Smallest unit that meets the goal.
4. **Placement** — for each new/moved symbol, which existing symbol or net it should sit *near* and why (decoupling next to its IC's VDD pin, pull-ups next to their label, function-grouped — no parking in empty corners).
5. **Layout sketch (ASCII art) — required** — show **both** the *current* local layout and the *proposed* layout side-by-side (or before/after) as small ASCII diagrams. Include anchor symbols/pins, the new/moved parts, and the connecting wires/labels. Coordinates (X,Y numbers) are *supplementary* to the sketch, not a substitute — the sketch is the primary artifact for the user to spot orientation/topology issues before any edit runs. Approximate proportions are fine; what matters is relative position and connectivity. Example:

   ```
   Current:                Proposed:
        VCC                     VCC
         │                       │
         ●── U2.VCC               ●── U2.VCC
                                  │
                                 ─┴─ C99 100nF
                                  │
                                  ●── GND
   ```

Skip only if: (a) the user gave an exact single action ("move R5 to 100,50"), or (b) running under an autonomous-iteration context the user invoked — notably `/kicad-sch-cleanup-loop` (bounded edits, auto-revert on regression) or another explicit pre-approval. Auto Mode alone is **not** pre-approval — still plan and wait. When in doubt, plan and wait.

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
