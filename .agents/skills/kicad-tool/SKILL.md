---
name: kicad-tool
description: Use the repository-local unified KiCad CLI for schematic rendering, visual inspection/scoring, ERC, netlist export, validation, and PCB DRC. This is the single skill that owns `.agents/skills/kicad-tool/scripts/kicad_tool.py` and its helper modules.
---

# KiCad Tool

Single owner of repository-local KiCad commands. Other skills must call this CLI, never the helper modules.

## Entrypoint

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py <domain> <command> ...
```

`KICAD_CLI` overrides the executable. Default: `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.

## Commands

| Command | Purpose | Key flags |
|---|---|---|
| `sch render-svg <sheet>` | Export one sheet to SVG | `--out <dir>` |
| `sch inspect <sheet>` | Score + collisions (re-renders SVG internally) | `--json`, `--only-text <regex>` (Python regex; score stays global), `--margin` |
| `sch erc <top>` | ERC, hierarchical | `--report <path>` |
| `sch netlist <top>` | Netlist export | `--out <path>` |
| `sch validate <top>` | erc + netlist + render-svg(`--sheet`) + inspect(`--sheet`) in one call | `--sheet <edited>`, `--json` |
| `pcb drc <board>` | PCB DRC | `--report <path>`, `--schematic-parity` |

Pass top-level (`cupwarmer-hw.kicad_sch`) to `erc` / `netlist` / `validate`. Pass the edited child sheet to `render-svg` / `inspect` (or via `--sheet` for `validate`).

Example — full validation after editing `rx-power.kicad_sch`:

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch \
  --sheet hardware/kicad/cupwarmer-hw/rx-power.kicad_sch \
  --json
```

## Inspect JSON

`sch inspect --json` returns:

- `score` — `total` (lower better), `collision_count`, `wire_corner_count` (two-segment bends + wire-endpoint T-junctions), `symbol_wire_conflict_count` (wires crossing symbol bodies), `symbol_wire_clearance_count` (wires too close to symbols).
- `collisions` — text/label/property/wire/symbol records.
- `symbol_wire_conflicts` — body overlaps + clearance violations.
- `filters` — applied `only_text`, `margin`.

## Scripts

- `scripts/kicad_tool.py` — only executable entrypoint.
- `scripts/score_schematic.py`, `scripts/kicad_sch_bbox_collisions.py`, `scripts/text_collision_core.py` — import-only helpers; do not invoke directly.
