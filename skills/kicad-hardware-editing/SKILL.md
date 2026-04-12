---
name: kicad-hardware-editing
description: Edit and inspect KiCad hardware design files for this repository under `hardware/kicad/cupwarmer-hw`. Use when Codex needs to modify or analyze `.kicad_sch`, `.kicad_pcb`, or related `.kicad_pro` files, preserve hierarchical sheet structure, reason about KiCad S-expression content, or validate hardware-file changes with `kicad-cli`.
---

# Kicad Hardware Editing

## Scope

Work on the KiCad project in `hardware/kicad/cupwarmer-hw`.

Treat file types differently:

- `.kicad_sch`: KiCad schematic S-expression — **edit via kiutils**
- `.kicad_pcb`: KiCad board S-expression
- `.kicad_pro`: project JSON
- `.kicad_prl`: local preferences; avoid editing unless the task is explicitly about local view state

Read these files before editing:

- `hardware/kicad/cupwarmer-hw/README.md`
- `hardware/schematic/README.md`
- `hardware/pcb/README.md`

## kiutils Setup

This project uses a patched version of kiutils (branch `fix/roundtrip-fidelity`) with KiCad v8+ format support. The patched kiutils is at:

```
/Users/mash/src/github.com/mvnmgrx/kiutils/src/kiutils/
```

All Python scripts that use kiutils must add the path before importing:

```python
import sys
sys.path.insert(0, "/Users/mash/src/github.com/mvnmgrx/kiutils/src")
from kiutils.schematic import Schematic
from kiutils.items.schitems import SchematicSymbol, Text, HierarchicalSheet, Connection, GlobalLabel
from kiutils.items.common import Property, Effects, Position
from kiutils.symbol import Symbol
```

The patched kiutils supports these KiCad v8+ tokens that upstream kiutils does not:

- `generator_version`, `embedded_fonts` (Schematic)
- `exclude_from_sim` (SchematicSymbol, Text, HierarchicalSheet, Symbol)
- `in_bom`, `on_board`, `dnp` (HierarchicalSheet)
- `(hide yes/no)` in Effects and pin_numbers
- `show_name` with yes/no values (Property)

## Choose The Target

Identify which file class is being changed before editing.

- Top-level schematic:
  `hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch`
- Child schematics:
  `hardware/kicad/cupwarmer-hw/*.kicad_sch`
- Board:
  `hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb`
- Project settings:
  `hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pro`

When editing a schematic, decide whether the change belongs in the top sheet, a child sheet, or both.

## Edit Schematics

**Use kiutils, not raw text editing, for all .kicad_sch modifications.**

Write a Python script in `tmp/` that:

1. Reads the schematic with `Schematic.from_file()`
2. Modifies the object model (add symbols, properties, wires, etc.)
3. Writes back with `sch.to_file()`

Example — adding a symbol property:

```python
import sys
sys.path.insert(0, "/Users/mash/src/github.com/mvnmgrx/kiutils/src")
from kiutils.schematic import Schematic

sch = Schematic.from_file("hardware/kicad/cupwarmer-hw/heater-control.kicad_sch")

for sym in sch.schematicSymbols:
    if sym.entryName == "PASSIVE_2":
        # Modify properties, position, etc.
        for prop in sym.properties:
            if prop.key == "Value":
                prop.value = "100R"

sch.to_file("hardware/kicad/cupwarmer-hw/heater-control.kicad_sch")
```

### Structural rules

Keep these structures coherent:

- top sheet `sheet`
- top sheet `Sheetname` and `Sheetfile`
- child sheet `sheet_instances`
- placed `symbol`
- `symbol.instances.project.path`
- `global_label` and any matching connectivity assumptions

Treat these fields as high-risk:

- `uuid`
- `sheet_instances`
- `instances`
- pin UUIDs

Do not rename or renumber references casually. If a symbol is already `U1`, `Q1`, `C1`, or `L1`, preserve that identity unless the task explicitly requires refactoring.

Follow the repo's current net naming where possible:

- `VOUT_12V`
- `SYS_GND`
- `I2C_SCL`
- `I2C_SDA`
- `HEATER_PWM`
- `ISENSE`
- `NTC_TOP`
- `NTC_PCB`
- `RX_INT`

When editing the top sheet, confirm that every `Sheetfile` actually exists on disk. A missing child sheet may still allow some CLI exports, so do not treat a successful export as proof that hierarchy is correct.

## Edit The Board

Preserve the existing board skeleton unless the task explicitly changes board setup.

Keep these sections stable:

- `layers`
- `setup`
- `setup.stackup`
- `Edge.Cuts`
- board title block

Treat these sections as high-risk for manual edits:

- `net`
- `footprint`
- `segment`
- `via`
- `zone`

Prefer small, local edits over broad rewrites. `gr_text` and other non-connectivity graphics are relatively safe. Net numbering and footprint internals are not.

Respect the repo's current hardware intent:

- keep the 4-layer assumption unless the task changes stackup intentionally
- keep RX, heater power, and control concerns separated
- avoid introducing board-level changes that conflict with `hardware/pcb/README.md`

## Edit Project Settings

Treat `.kicad_pro` as JSON, not S-expression.

Prefer minimal edits. Avoid rewriting formatting or unrelated settings.

Use `.kicad_pro` for project-wide design settings and rules. Avoid touching `.kicad_prl` unless the task explicitly concerns local UI state.

## Validate Changes

After every schematic edit, run validation in this order:

### 1. Roundtrip coverage test

Verify kiutils can read and write the file without losing tokens:

```bash
python3 tmp/roundtrip_sch.py hardware/kicad/cupwarmer-hw/<edited-file>.kicad_sch
```

Check that OVERALL COVERAGE remains 100%. Any drop means the edit introduced tokens that kiutils cannot roundtrip.

### 2. kicad-cli validation

Use `kicad-cli` to confirm the output is valid KiCad:

```bash
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
```

**ERC (electrical rules check):**

```bash
"$KICAD_CLI" sch erc \
  --exit-code-violations \
  --output tmp/cupwarmer-erc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

**Netlist export (circuit equivalence):**

```bash
"$KICAD_CLI" sch export netlist \
  --output tmp/cupwarmer.net \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

**SVG export (visual check):**

```bash
"$KICAD_CLI" sch export svg \
  --output tmp/cupwarmer-sch-svg \
  hardware/kicad/cupwarmer-hw/heater-control.kicad_sch
```

**Board checks:**

```bash
"$KICAD_CLI" pcb export stats \
  --format json \
  --output tmp/cupwarmer-board-stats.json \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb

"$KICAD_CLI" pcb drc \
  --schematic-parity \
  --output tmp/cupwarmer-drc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb
```

### 3. Full validation script

For comprehensive before/after comparison (roundtrip + ERC + netlist diff):

```bash
python3 tmp/kicad_cli_validate.py
```

This script roundtrips all .kicad_sch files, then compares ERC results and netlists between originals and roundtripped outputs. The expected result is:
- ERC exit codes match
- Netlists identical (except file path)

### 4. Text-level checks

- inspect `git diff`
- use `rg` to confirm `Sheetfile`, net names, and symbol references
- confirm edited child sheets still exist and are referenced correctly

### Validation boundary

- syntax errors usually fail fast
- hierarchy mistakes may still export
- successful CLI output is necessary, not sufficient
- **roundtrip coverage 100% + identical netlist = high confidence**

If using `sch upgrade`, upgrade child sheets explicitly. The CLI does not recursively upgrade sub-sheets just because the top sheet was targeted.

## Working Style

Read the smallest relevant set of KiCad files first.

Make the narrowest possible edit.

Re-check the corresponding root and child files after each schematic change.

Prefer adding repo-specific rationale in nearby docs rather than stuffing long design commentary into KiCad file text blocks.
