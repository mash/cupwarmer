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

## Argument conventions

- `<schematic>` is always the first positional.
- Required args are positional, in table order. Coordinates are a single `X,Y` (bbox: `X1,Y1,X2,Y2`); rotation is `--rotation R`.
- `--flag` only for optional knobs, mutex selectors (e.g. `--uuid` vs `--at` for `wire delete`), and the universal `--dry-run` (edits) / `--json` (all).

## Commands

| Command | Purpose | Key flags |
|---|---|---|
| `sch render-svg <sheet>` | Export one sheet to SVG | `--out <dir>` |
| `sch inspect <sheet>` | Score + collisions (re-renders SVG internally) | `--json`, `--only-text <regex>` (Python regex; score stays global), `--margin` |
| `sch erc <top>` | ERC, hierarchical | `--report <path>` |
| `sch netlist <top>` | Netlist export | `--out <path>` |
| `sch validate <top>` | erc + netlist + render-svg(`--sheet`) + inspect(`--sheet`) in one call | `--sheet <edited>`, `--json` |
| `pcb drc <board>` | PCB DRC | `--report <path>`, `--schematic-parity` |

### Query

Read-only inspection of a sheet. All take a positional `<schematic.kicad_sch>` and accept `--json`.

| Command | Purpose |
|---|---|
| `sch query symbol <sch> <REF>` | Symbol details (position, properties, pin map) by reference |
| `sch query pin <sch> <REF.PIN> [--netlist PATH]` | One pin's coordinates, orientation, and (with netlist) net |
| `sch query net <sch> <NAME_OR_REF.PIN> --netlist PATH` | Members and labels of a net (REF.PIN dispatched by `.`) |
| `sch query region <sch> <X1,Y1,X2,Y2>` | All elements inside a bounding box |
| `sch query wire <sch> (--uuid U \| --at X,Y \| --through X,Y)` | Locate a wire by uuid, endpoint, or any point on the segment |
| `sch query label <sch> (--name N \| --uuid U)` | Locate labels by name or uuid |
| `sch query lib-symbol <sch> <LIB_ID>` | Library symbol definition (pins, units) |
| `sch query list <sch> <KIND> [--netlist PATH]` | Enumerate elements of one kind (KIND ∈ symbols/labels/wires/junctions/nets; `nets` requires `--netlist`) |

### Edit

Structural mutations. All take a positional `<schematic.kicad_sch>`, accept `--json`, and support `--dry-run`.

| Command | Purpose |
|---|---|
| `sch edit symbol move <sch> <REF> <X,Y> [--rotation R]` | Move/rotate a symbol |
| `sch edit symbol add-pin <sch> <LIB_ID> <NUMBER> <NAME> <X,Y> --length L --type T [--rotation R] [--shape S] [--lib-file PATH]` | Add a pin to a symbol (updates embedded lib_symbols + standalone .kicad_sym) |
| `sch edit wire add <sch> <X1,Y1> <X2,Y2> [--type solid\|default]` | Add a wire segment |
| `sch edit wire delete <sch> (--uuid U \| --from X,Y --to X,Y)` | Delete a wire |
| `sch edit label add <sch> <KIND> <NAME> <X,Y> [--rotation R] [--justify J]` | Add a label (KIND ∈ global/hier/local) |
| `sch edit label move <sch> <UUID> <X,Y> [--rotation R]` | Move a label |
| `sch edit label delete <sch> <UUID>` | Delete a label |
| `sch edit junction add <sch> <X,Y>` | Add a junction |
| `sch edit junction delete <sch> (--uuid U \| --at X,Y)` | Delete a junction |

### Validate (with baseline)

| Command | Purpose |
|---|---|
| `sch validate <top> --save-baseline DIR` | Save current ERC + netlist as the baseline |
| `sch validate <top> --baseline DIR` | Re-run validation and diff against the saved baseline |

### Decision rules

- "I want to know X" → `sch query`. Pick the element by what you have a name/coord for: a `REF` → `symbol`; `REF.PIN` → `pin`; a net name → `net`; coords → `region` or `wire`/`junction`/`label` by `--at`.
- "I want to change something structural" → `sch edit <element> <action>`. The action is `add` / `move` / `delete`.
- "I want to know if my edit broke connectivity" → `sch validate --baseline DIR`.
- "I want to render or score" → existing `render-svg` / `inspect`.

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
- `wire_length` — independent non-score metric with total wire length, segment count, and longest segment.
- `collisions` — text/label/property/wire/symbol records.
- `symbol_wire_conflicts` — body overlaps + clearance violations.
- `filters` — applied `only_text`, `margin`.

## Scripts

- `scripts/kicad_tool.py` — only executable entrypoint.
- `scripts/score_schematic.py`, `scripts/kicad_sch_bbox_collisions.py`, `scripts/text_collision_core.py` — import-only helpers; do not invoke directly.
