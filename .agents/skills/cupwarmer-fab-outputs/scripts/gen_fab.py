#!/usr/bin/env python3
"""Regenerate JLCPCB BOM and CPL for the cupwarmer-hw board from KiCad.

Outputs (canonical locations, overwritten in place):
  hardware/bom/jlcpcb-bom.csv                          (Comment, Designator, Footprint, LCSC Part #)
  hardware/fab/cupwarmer-hw/cupwarmer-hw-cpl-jlcpcb.csv (Designator, Mid X, Mid Y, Layer, Rotation)

LCSC Part # is the authoritative match key for JLCPCB assembly. The BOM
"Footprint" column is an informational hint only: rule-simplified for new
parts, but preserved from the existing BOM (keyed by LCSC #) so hand-curated
package strings (WLCSP-40_..., SMB(DO-214AA), SOD-123FL) survive regeneration.

The heater board has no assembled SMT parts (flex heater routed by JLCPCB,
NTC embedded), so it has no BOM/CPL and is intentionally not handled here.

Run from the repo root, or pass --repo. No external deps; stdlib only.
"""
import argparse
import csv
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCH = "hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch"
PCB = "hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_pcb"
BOM_OUT = "hardware/bom/jlcpcb-bom.csv"
CPL_OUT = "hardware/fab/cupwarmer-hw/cupwarmer-hw-cpl-jlcpcb.csv"

KICAD_CLI_CANDIDATES = [
    "kicad-cli",
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
]


def find_kicad_cli() -> str:
    for c in KICAD_CLI_CANDIDATES:
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        elif shutil.which(c):
            return c
    sys.exit("kicad-cli not found. Install KiCad or add kicad-cli to PATH.")


def natural_key(ref: str):
    m = re.match(r"^([A-Za-z]+)(\d+)$", ref)
    if m:
        return (m.group(1), int(m.group(2)))
    return (ref, 0)


def sort_refs(refs_field: str) -> str:
    refs = [r.strip() for r in refs_field.split(",") if r.strip()]
    refs.sort(key=natural_key)
    return ",".join(refs)


def simplify_footprint(fp: str) -> str:
    """Best-effort package hint for a *new* part (no existing value to keep)."""
    name = fp.split(":", 1)[-1]  # strip library prefix
    m = re.match(r"^(LED_)?[CRL]?D?_?(\d{4})_\d+Metric$", name)
    if m:
        return (m.group(1) or "") + m.group(2)
    m = re.match(r"^[CRL]_(\d{4})_\d+Metric$", name)
    if m:
        return m.group(1)
    return name


def run_cli(cli: str, args: list[str]) -> str:
    res = subprocess.run([cli, *args], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"kicad-cli failed: {' '.join(args)}\n{res.stderr}")
    return res.stdout


def gen_bom(cli: str, repo: Path, placed_refs: set):
    out = Path("/tmp/cupwarmer-bom-raw.csv")
    run_cli(cli, [
        "sch", "export", "bom",
        "--fields", "MPN,${Reference},Footprint,LCSC",
        "--labels", "Comment,Designator,Footprint,LCSC Part #",
        "--group-by", "MPN,Footprint,LCSC",
        "--exclude-dnp",
        "-o", str(out),
        str(repo / SCH),
    ])
    rows = list(csv.DictReader(out.read_text().splitlines()))

    # Preserve hand-curated footprint strings keyed by LCSC #.
    bom_path = repo / BOM_OUT
    prev_fp: dict[str, str] = {}
    if bom_path.exists():
        for r in csv.DictReader(bom_path.read_text().splitlines()):
            if r.get("LCSC Part #"):
                prev_fp[r["LCSC Part #"]] = r["Footprint"]

    # The JLCPCB BOM must cover exactly the parts JLC pick-and-places, i.e. the
    # CPL set (SMD, not DNP, not fiducial). A part is assembled only if at least
    # one of its designators is in the CPL *and* it carries an LCSC #. THT and
    # hand-mounted parts never enter the CPL, so they drop out of the BOM too.
    assembled, no_lcsc_placed, excluded = [], [], []
    for r in rows:
        r["Designator"] = sort_refs(r["Designator"])
        placed = [x for x in r["Designator"].split(",") if x in placed_refs]
        if not placed:
            excluded.append(r)          # not placed by JLC (THT/hand-mount/no-fp)
        elif r["LCSC Part #"]:
            assembled.append(r)         # placed + sourceable
        else:
            no_lcsc_placed.append(r)    # placed SMD but no LCSC -> JLC can't match

    for r in assembled:
        lcsc = r["LCSC Part #"]
        r["Footprint"] = prev_fp.get(lcsc) or simplify_footprint(r["Footprint"])
    assembled.sort(key=lambda r: natural_key(r["Designator"].split(",")[0]))
    rows = assembled

    if no_lcsc_placed:
        print("WARNING: placed (CPL) parts WITHOUT an LCSC # (not in JLCPCB BOM "
              "— add MPN/LCSC in the schematic if they must be assembled):",
              file=sys.stderr)
        for r in no_lcsc_placed:
            print(f"  {r['Designator']}  {r['Comment'] or r.get('Value','')}  "
                  f"{r['Footprint']}", file=sys.stderr)
    if excluded:
        print("note: not placed by JLC, excluded from BOM (THT/hand-mount/"
              "external/no-footprint): "
              + ", ".join(r["Designator"] for r in excluded), file=sys.stderr)

    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for r in rows:
        w.writerow([r["Comment"], r["Designator"], r["Footprint"], r["LCSC Part #"]])
    bom_path.write_text(buf.getvalue())
    print(f"wrote {BOM_OUT} ({len(rows)} lines)")


def gen_cpl(cli: str, repo: Path):
    out = Path("/tmp/cupwarmer-pos-raw.csv")
    run_cli(cli, [
        "pcb", "export", "pos",
        "--format", "csv", "--units", "mm",
        "--side", "both", "--smd-only", "--exclude-dnp",
        "-o", str(out),
        str(repo / PCB),
    ])
    rows = list(csv.DictReader(out.read_text().splitlines()))

    buf = io.StringIO()
    # JLCPCB CPL convention in this repo uses CRLF line endings.
    w = csv.writer(buf, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    placed = set()
    for r in rows:
        # Drop fiducials (no pick-and-place part).
        if r["Val"] == "Fiducial" or r["Package"].startswith("Fiducial"):
            continue
        layer = "Top" if r["Side"] == "top" else "Bottom"
        w.writerow([r["Ref"], r["PosX"], r["PosY"], layer, r["Rot"]])
        placed.add(r["Ref"])
    (repo / CPL_OUT).write_text(buf.getvalue())
    print(f"wrote {CPL_OUT} ({len(placed)} placements)")
    return placed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".", help="repo root (default: cwd)")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / SCH).exists():
        sys.exit(f"can't find {SCH} under {repo}. Pass --repo <repo-root>.")
    cli = find_kicad_cli()
    placed_refs = gen_cpl(cli, repo)   # CPL defines the placed-part set
    gen_bom(cli, repo, placed_refs)    # BOM is constrained to that set


if __name__ == "__main__":
    main()
