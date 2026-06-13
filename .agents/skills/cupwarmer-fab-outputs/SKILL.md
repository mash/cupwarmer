---
name: cupwarmer-fab-outputs
description: Regenerate the JLCPCB BOM and CPL (component placement list) for the cupwarmer-hw control PCB from its KiCad sources, writing them to their canonical locations. Use after editing the cupwarmer-hw schematic or PCB, or when the user asks to refresh/export the BOM, CPL, pick-and-place, or fab outputs. The flexible heater has no assembled SMT parts and is intentionally out of scope.
---

# cupwarmer fab outputs (BOM + CPL)

Regenerate JLCPCB assembly files for the **cupwarmer-hw control PCB** straight
from KiCad, deterministically and headless. Wraps `kicad-cli` plus a small
transform so the output matches this repo's JLCPCB conventions.

## Run

```bash
python3 .agents/skills/cupwarmer-fab-outputs/scripts/gen_fab.py --repo .
```

From the repo root `--repo .` is the default and can be omitted. The script
finds `kicad-cli` on `PATH` or at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.

## Outputs (overwritten in place — canonical locations)

| File | Format | Source |
|---|---|---|
| `hardware/bom/jlcpcb-bom.csv` | `Comment, Designator, Footprint, LCSC Part #` | `cupwarmer-hw.kicad_sch` (`sch export bom`) |
| `hardware/fab/cupwarmer-hw/cupwarmer-hw-cpl-jlcpcb.csv` | `Designator, Mid X, Mid Y, Layer, Rotation` (CRLF) | `cupwarmer-hw.kicad_pcb` (`pcb export pos`) |

The master `hardware/bom/bom.csv` and `seeed-fusion-bom.csv` are hand-maintained
and are **not** touched. Gerbers are not regenerated here.

## What counts as a part

- **CPL** = `pcb export pos --smd-only --exclude-dnp`, minus fiducials, with
  `top/bottom` → `Top/Bottom`. This set defines exactly what JLC pick-and-places.
- **BOM** = the CPL part set, restricted to parts carrying an `LCSC` #. The CPL
  is generated first and the BOM is constrained to it, so **BOM ⊆ CPL**: THT
  parts (e.g. `J1`), hand-mounted parts, and externals never enter either file.
  JLCPCB matches by LCSC Part #; the `Footprint` column is an informational
  hint, rule-simplified for new parts but **preserved from the existing BOM by
  LCSC #** so hand-curated strings (`WLCSP-40_2.5x2.5mm_P0.4mm`, `SMB(DO-214AA)`,
  `SOD-123FL`) survive regeneration.

## Read the warnings — nothing is silently dropped

The script prints, to stderr:

- **WARNING — placed (CPL) parts with no LCSC #**: a part JLC would place but
  can't source. If it must be assembled, add `MPN`/`LCSC` in the schematic and
  rerun; otherwise it stays in the CPL but is absent from the BOM. (A regression
  where `D1`/`D2` indicator LEDs lost their part numbers was caught this way and
  restored — `XL-1608SURC-04`/`C965798`, `XL-1608UGC-04`/`C965804`.)
- **note — not placed by JLC, excluded from BOM**: intentionally off both files
  because they are not pick-and-placed — `F1` (on the heater assembly), `J1`
  (THT I2C service header, hand-soldered), `L1` (coil, hand-mounted), `J2`/`J3`
  (heater harness solder pads), `R_HTR1`/`TH2` (heater element + external NTC).
  Sourced/mounted separately; see `docs/design-notes.md` 発熱体・熱設計 and the
  Off-board 手配チェックリスト.

## Heater is out of scope

`hardware/kicad/heater/` is a flexible heater: the element is routed by JLCPCB
and the NTC is embedded, so it has no SMT BOM/CPL. It ships as a gerber package
(`hardware/fab/heater/heater-jlcpcb-flex-heater.zip`) ordered via the JLCPCB
flex-heater form — see `docs/design-notes.md`.

## Source of truth

KiCad (`.kicad_sch` / `.kicad_pcb`) is authoritative for nets, footprints, and
placement. These CSVs are generated artifacts — never hand-edit them; fix the
schematic/PCB and rerun. Verify the schematic/PCB are saved and ERC/DRC-clean
(via the `kicad-tool` / `kicad-workflow` skills) before regenerating.
