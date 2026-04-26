---
name: kicad-tool
description: Use the repository-local unified KiCad CLI for schematic rendering, visual inspection/scoring, ERC, netlist export, validation, and PCB DRC. This is the single skill that owns `.agents/skills/kicad-tool/scripts/kicad_tool.py` and its helper modules.
---

# KiCad Tool

Use this skill whenever you need to run repository-local KiCad commands. This skill owns the implementation scripts; workflow skills should call this CLI instead of invoking helper modules directly.

## Entrypoint

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py <domain> <command> ...
```

`KICAD_CLI` can override the default KiCad executable. The default is:

```bash
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
```

## Schematic Commands

Export one schematic sheet to SVG:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch render-svg \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --out tmp/cupwarmer-sch-svg
```

Inspect schematic visual quality. This internally exports SVG, then returns score, collision records, symbol-wire conflicts, and filters:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch inspect \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --json
```

Filter returned collision records by label/property text. The score remains global:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch inspect \
  hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --only-text 'SYS_GND|RX_NTC' \
  --json
```

Run ERC against the top-level schematic:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch erc \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch \
  --report tmp/cupwarmer-erc.rpt
```

Export a netlist from the top-level schematic:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch netlist \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch \
  --out tmp/cupwarmer-post.net
```

Run schematic validation stages together:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch \
  --sheet hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --json
```

`sch validate` runs ERC, netlist export, SVG export for the edited sheet, and `sch inspect`.

## PCB Commands

Run PCB DRC:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py pcb drc \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb \
  --report tmp/cupwarmer-drc.rpt \
  --schematic-parity
```

## Inspect JSON

`sch inspect --json` returns:

- `score`: total penalty and breakdown fields.
- `collisions`: text, label, property, wire, and symbol collision records.
- `symbol_wire_conflicts`: direct symbol body overlaps and near-symbol clearance conflicts.
- `filters`: applied options such as `only_text` and `margin`.

Important score fields:

- `total`: lower is better.
- `collision_count`: total unfiltered text/label collision count used by the global score.
- `wire_corner_count`: two-segment bends plus wire endpoints that T-junction into perpendicular segments.
- `symbol_wire_conflict_count`: wires directly crossing symbol bodies.
- `symbol_wire_clearance_count`: wires too close to symbol bodies.

## Scripts

- `scripts/kicad_tool.py`: only executable entrypoint.
- `scripts/score_schematic.py`: import-only scoring helper.
- `scripts/kicad_sch_bbox_collisions.py`: import-only SVG/schematic geometry helper.
- `scripts/text_collision_core.py`: import-only rectangle and collision helper.

Do not run helper modules directly. If another skill needs scoring, rendering, ERC, netlist, validation, or DRC, use `kicad_tool.py`.
