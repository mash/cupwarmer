---
name: kicad-validate
description: Validate KiCad hardware files after edits. Dispatched as a subagent by kicad-hardware-editing. Runs roundtrip coverage, kicad-cli ERC, netlist diff, and text-level checks.
---

# KiCad Validate

## Run Order

Execute these checks in order. Stop and report on first failure.

### 1. Roundtrip coverage

```bash
python3 tmp/roundtrip_sch.py hardware/kicad/cupwarmer-hw/<edited-file>.kicad_sch
```

OVERALL COVERAGE must be 100%. Any drop means the edit introduced tokens kiutils cannot roundtrip.

### 2. ERC (electrical rules check)

```bash
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

"$KICAD_CLI" sch erc \
  --exit-code-violations \
  --output tmp/cupwarmer-erc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

### 3. Netlist export and diff

```bash
"$KICAD_CLI" sch export netlist \
  --output tmp/cupwarmer-post.net \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

If a pre-edit netlist exists at `tmp/cupwarmer-pre.net`, diff them. Only the file path line should differ.

### 4. SVG export (visual check)

```bash
"$KICAD_CLI" sch export svg \
  --output tmp/cupwarmer-sch-svg \
  hardware/kicad/cupwarmer-hw/<edited-file>.kicad_sch
```

### 5. Board checks (if board was edited)

```bash
"$KICAD_CLI" pcb drc \
  --schematic-parity \
  --output tmp/cupwarmer-drc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb
```

### 6. Text-level checks

- `git diff` — review the actual changes
- Confirm `Sheetfile` references point to existing files
- Confirm net names and symbol references are consistent

### 7. Full validation script

For comprehensive before/after comparison:

```bash
python3 tmp/kicad_cli_validate.py
```

Expected: ERC exit codes match, netlists identical except file path.

## Interpreting Results

- syntax errors → fail fast
- hierarchy mistakes → may still export successfully
- successful CLI output → necessary but not sufficient
- **roundtrip 100% + identical netlist = high confidence**

## Report Format

Report results as:

```
Roundtrip: 100% (no LOST, no CHANGED)
ERC: exit=5 (same as before edit)
Netlist: identical (path-only diff)
SVG: exported OK
```

Or on failure:

```
FAIL: Roundtrip dropped to 95.3%
  LOST: kicad_sch > symbol > new_token (3 occurrences)
```
