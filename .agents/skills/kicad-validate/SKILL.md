---
name: kicad-validate
description: Validate KiCad hardware files after edits. Runs kicad-cli ERC, netlist export/diff, SVG export, optional schematic layout scoring, and text-level checks.
---

# KiCad Validate

## Run Order

Execute these checks in order. Stop and report on first failure.

### 1. KiCad CLI availability

```bash
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
"$KICAD_CLI" version
```

### 2. ERC (electrical rules check)

Always run ERC against the **top-level sheet** (`cupwarmer-hw.kicad_sch`), even when only a child sheet was edited — hierarchical ERC propagates into child sheets. Do not run ERC on a child sheet directly.

```bash
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

"$KICAD_CLI" sch erc \
  --exit-code-violations \
  --output tmp/cupwarmer-erc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

Compare against the pre-edit ERC result when available. Existing violations are not automatically failures; new violations are. New violations that are the intended consequence of the request (e.g. a deliberately-added test-point label that is dangling on purpose) are acceptable; call them out in the report.

### 3. Netlist export and diff

Always export from the **top-level sheet**. Output filename convention: pre-edit baseline is `tmp/cupwarmer-pre.net`, post-edit is `tmp/cupwarmer-post.net`. If no baseline was captured, write `tmp/cupwarmer-post.net` and note "no pre-edit baseline" in the report.

```bash
"$KICAD_CLI" sch export netlist \
  --output tmp/cupwarmer-post.net \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

If a pre-edit netlist exists at `tmp/cupwarmer-pre.net`, diff them. For visual-only edits, only path/header metadata should differ. For electrical edits, summarize the intended netlist changes.

### 4. SVG export (visual check)

Run this for each edited schematic sheet:

```bash
"$KICAD_CLI" sch export svg \
  --output tmp/cupwarmer-sch-svg \
  hardware/kicad/cupwarmer-hw/<edited-file>.kicad_sch
```

Current schematic sheets:

- `cupwarmer-hw.kicad_sch`
- `rx-power.kicad_sch`
- `heater-control.kicad_sch`
- `sensors-logic.kicad_sch`

### 5. Schematic layout score (if schematic readability changed)

Use `kicad-schematic-score` for any edit that moves labels, text, symbols, or wires:

```bash
python3 .agents/skills/kicad-schematic-score/scripts/score_schematic.py \
  hardware/kicad/cupwarmer-hw/<edited-file>.kicad_sch
```

Lower is better. Compare before/after scores when a baseline exists. Report the score inline (stdout summary is enough; no need to redirect to a file).

### 6. Board checks (if board was edited)

```bash
"$KICAD_CLI" pcb drc \
  --schematic-parity \
  --output tmp/cupwarmer-drc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb
```

### 7. Text-level checks

- `git diff` — review the actual changes
- Confirm `Sheetfile` references point to existing files
- Confirm net names and symbol references are consistent
- Confirm custom symbol changes are reflected in both embedded `lib_symbols` and `cupwarmer.kicad_sym`

## Interpreting Results

- syntax errors → fail fast
- hierarchy mistakes → may still export successfully
- successful CLI output → necessary but not sufficient
- **ERC parity + expected netlist diff + SVG export + score check when relevant = high confidence**

## Report Format

Report results as:

```
ERC: exit=5 (same as before edit)
Netlist: identical (path-only diff)
SVG: exported OK
Score: total 3170.808 (wire_corner_count 41)
```

Or on failure:

```
FAIL: New ERC violation
  See tmp/cupwarmer-erc.rpt
```
