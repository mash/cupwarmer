---
name: kicad-validate
description: Workflow for validating KiCad hardware files after edits. Use `kicad-tool` to run ERC, netlist export/diff, SVG export, schematic layout inspection, and PCB DRC.
---

# KiCad Validate

All commands go through the `kicad-tool` skill. See its command table for flag reference.

## One-shot validate

For most schematic edits this is the only command needed:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch \
  --sheet hardware/kicad/cupwarmer-hw/<edited>.kicad_sch \
  --json
```

This runs ERC + netlist + SVG export + `sch inspect` in order, stopping on the first failure.

## Baseline-diff workflow

For any non-trivial structural edit, snapshot a baseline first (cheap) so you can confirm connectivity is preserved — not just "ERC still passes":

```bash
# Before edit:
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch --save-baseline tmp/baseline

# After edit:
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch --baseline tmp/baseline
```

`--save-baseline DIR` writes `erc.rpt`, `netlist.net`, `inspect.json` to `DIR`. `--baseline DIR` reruns the stages and emits a JSON diff (`added_nets` / `removed_nets` / `changed_nets` / `new_erc_errors`); exits non-zero on regression (new ERC errors, removed nets, or removed nodes from existing nets).

## Target rules (when running stages individually)

- **ERC**: always against the **top-level** `cupwarmer-hw.kicad_sch` (hierarchical ERC propagates into children). Never on a child sheet directly.
- **Netlist**: always from the top-level.
- **SVG export**: each edited sheet.
- **Inspect**: each edited sheet (run for any edit that moves labels/text/symbols/wires).
- **PCB DRC**: only when the board was edited; pass `--schematic-parity`.

## Baseline filename convention

| Stage | Pre-edit | Post-edit |
|---|---|---|
| ERC report | `tmp/cupwarmer-pre-erc.rpt` | `tmp/cupwarmer-post-erc.rpt` |
| Netlist | `tmp/cupwarmer-pre.net` | `tmp/cupwarmer-post.net` |
| Inspect score | `tmp/score-pre.json` | `tmp/score-post.json` |

If no pre-edit baseline exists, write the post file and note "no baseline" in the report.

## Schematic sheets

`cupwarmer-hw.kicad_sch` (top), `rx-power.kicad_sch`, `heater-control.kicad_sch`, `sensors-logic.kicad_sch`.

## Interpreting results

- Existing ERC violations are not failures; **new** ones are. Intentional new violations (e.g. deliberately-dangling test label) are acceptable — call them out.
- Netlist diff: visual-only edits should differ only in path/header metadata. Electrical edits: summarize intended changes.
- Successful CLI exit ≠ correctness. **ERC parity + expected netlist diff + SVG export + score check (when relevant)** = high confidence.
- Also `git diff` review; confirm `Sheetfile` references, net names, and that custom symbol changes appear in both embedded `lib_symbols` and `cupwarmer.kicad_sym`.

## Report format

```
ERC: exit=5 (same as before edit)
Netlist: identical (path-only diff)
SVG: exported OK
Inspect: total 3170.808 (wire_corner_count 41)
```

On failure:

```
FAIL: New ERC violation
  See tmp/cupwarmer-erc.rpt
```
