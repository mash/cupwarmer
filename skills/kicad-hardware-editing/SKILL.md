---
name: kicad-hardware-editing
description: Edit and inspect KiCad hardware design files for this repository under `hardware/kicad/cupwarmer-hw`. Use when Codex needs to modify or analyze `.kicad_sch`, `.kicad_pcb`, or related `.kicad_pro` files, preserve hierarchical sheet structure, reason about KiCad S-expression content, or validate hardware-file changes with `kicad-cli`.
---

# Kicad Hardware Editing

## Scope

Work on the KiCad project in `hardware/kicad/cupwarmer-hw`.

Treat file types differently:

- `.kicad_sch`: KiCad schematic S-expression
- `.kicad_pcb`: KiCad board S-expression
- `.kicad_pro`: project JSON
- `.kicad_prl`: local preferences; avoid editing unless the task is explicitly about local view state

Read these files before editing:

- `hardware/kicad/cupwarmer-hw/README.md`
- `hardware/schematic/README.md`
- `hardware/pcb/README.md`
- `docs/kicad-file-format-research.md`
- `https://docs.kicad.org/master/en/cli/cli.html`

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

Preserve the S-expression structure exactly.

Prefer editing existing `property`, `text`, `wire`, and `global_label` blocks over reshuffling large sections.

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

Run `kicad-cli` after manual edits.

Use `command -v kicad-cli` first. If that is empty on this machine, use:

```bash
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
```

Useful checks:

```bash
'/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli' sch export netlist \
  --format kicadsexpr \
  --output /tmp/cupwarmer.net \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch

'/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli' sch erc \
  --exit-code-violations \
  --output /tmp/cupwarmer-erc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch

'/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli' sch export svg \
  --output /tmp/cupwarmer-sch-svg \
  hardware/kicad/cupwarmer-hw/heater-control.kicad_sch

'/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli' pcb export stats \
  --format json \
  --output /tmp/cupwarmer-board-stats.json \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb

'/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli' pcb drc \
  --schematic-parity \
  --output /tmp/cupwarmer-drc.rpt \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb
```

Also verify with text-level checks:

- inspect `git diff`
- use `rg` to confirm `Sheetfile`, net names, and symbol references
- confirm edited child sheets still exist and are referenced correctly

Remember the validation boundary:

- syntax errors usually fail fast
- hierarchy mistakes may still export
- successful CLI output is necessary, not sufficient

If using `sch upgrade`, upgrade child sheets explicitly. The CLI does not recursively upgrade sub-sheets just because the top sheet was targeted.

## Working Style

Read the smallest relevant set of KiCad files first.

Make the narrowest possible edit.

Re-check the corresponding root and child files after each schematic change.

Prefer adding repo-specific rationale in nearby docs rather than stuffing long design commentary into KiCad file text blocks.
