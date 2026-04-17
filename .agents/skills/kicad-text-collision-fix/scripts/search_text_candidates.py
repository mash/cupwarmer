#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
LAYOUT_HELPERS = ROOT / "skills/kicad-schematic-edit/scripts"

if str(LAYOUT_HELPERS) not in sys.path:
    sys.path.insert(0, str(LAYOUT_HELPERS))

from layout_helpers import LayoutEditor

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
DETECTOR = SCRIPT_DIR / "kicad_sch_bbox_collisions.py"


def load_candidates(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("candidate file must be a JSON array")
    out = []
    for item in data:
        out.append({"x": float(item["x"]), "y": float(item["y"]), "angle": int(item.get("angle", 0))})
    return out


def apply_target(schematic: Path, target: dict, cand: dict) -> None:
    ed = LayoutEditor(str(schematic))
    if target["target_kind"] == "property":
        for sym in ed.sch.schematicSymbols:
            ref = next((p.value for p in sym.properties if p.key == "Reference"), None)
            if ref != target["ref"]:
                continue
            for prop in sym.properties:
                if prop.key == target["key"] and prop.value == target["text"]:
                    prop.position.X = cand["x"]
                    prop.position.Y = cand["y"]
                    prop.position.angle = cand["angle"]
    else:
        found = False
        for gl in ed.sch.globalLabels:
            if gl.text != target["text"]:
                continue
            if abs(round(gl.position.X, 2) - target["match_x"]) > 0.01:
                continue
            if abs(round(gl.position.Y, 2) - target["match_y"]) > 0.01:
                continue
            gl.position.X = cand["x"]
            gl.position.Y = cand["y"]
            gl.position.angle = cand["angle"]
            found = True
        if not found:
            raise ValueError("target global_label not found")
    ed.save(str(schematic))


def target_match(collision: dict, target: dict, cand: dict) -> bool:
    if target["target_kind"] == "property":
        return (
            collision["kind"] == "property"
            and collision["owner_ref"] == target["ref"]
            and collision["owner_key"] == target["key"]
            and collision["text"] == target["text"]
        )
    return (
        collision["kind"] == "global_label"
        and collision["text"] == target["text"]
        and collision.get("matched_x") is not None
        and collision.get("matched_y") is not None
        and abs(collision["matched_x"] - cand["x"]) < 0.02
        and abs(collision["matched_y"] - cand["y"]) < 0.02
    )


def score(cand: dict, anchor_x: float | None, anchor_y: float | None) -> float:
    if anchor_x is None or anchor_y is None:
        return 0.0
    return math.hypot(cand["x"] - anchor_x, cand["y"] - anchor_y) + (0.75 if cand["angle"] != 0 else 0.0)


def export_svg(schematic: Path, outdir: Path) -> Path:
    subprocess.run(
        [KICAD_CLI, "sch", "export", "svg", "-o", str(outdir), str(schematic)],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    svgs = sorted(outdir.glob("*.svg"))
    if not svgs:
        raise FileNotFoundError(f"no SVG exported into {outdir}")
    return svgs[0]


def detect_payload(schematic: Path, svg: Path) -> dict:
    proc = subprocess.run(
        ["python3", str(DETECTOR), str(schematic), str(svg), "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def collision_signatures(payload: dict) -> set[tuple]:
    sigs: set[tuple] = set()
    for collision in payload["collisions"]:
        ident = (
            collision["kind"],
            collision["owner_ref"],
            collision["owner_key"],
            collision["text"],
        )
        for hit in collision["wire_hits"]:
            sigs.add(("wire", *ident, hit["uuid"]))
        for hit in collision["component_hits"]:
            sigs.add(("component", *ident, hit["ref"]))
        for hit in collision["text_hits"]:
            sigs.add(("text", *ident, hit["owner_ref"], hit["owner_key"], hit["text"]))
    return sigs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("schematic", type=Path)
    ap.add_argument("--target-kind", required=True, choices=["property", "global_label"])
    ap.add_argument("--text", required=True)
    ap.add_argument("--ref")
    ap.add_argument("--key")
    ap.add_argument("--match-x", type=float)
    ap.add_argument("--match-y", type=float)
    ap.add_argument("--candidates", type=Path, required=True)
    ap.add_argument("--anchor-x", type=float)
    ap.add_argument("--anchor-y", type=float)
    args = ap.parse_args()

    target = {
        "target_kind": args.target_kind,
        "text": args.text,
        "ref": args.ref,
        "key": args.key,
        "match_x": args.match_x,
        "match_y": args.match_y,
    }
    if args.target_kind == "property" and (not args.ref or not args.key):
        raise ValueError("--ref and --key are required for property targets")
    if args.target_kind == "global_label" and (args.match_x is None or args.match_y is None):
        raise ValueError("--match-x and --match-y are required for global_label targets")

    results = []
    candidates = load_candidates(args.candidates)
    with tempfile.TemporaryDirectory(prefix="kicad-text-candidate-") as tmpdir:
        tmpdir = Path(tmpdir)
        baseline_svg_dir = tmpdir / "baseline-svg"
        baseline_svg = export_svg(args.schematic, baseline_svg_dir)
        baseline_payload = detect_payload(args.schematic, baseline_svg)
        baseline_signatures = collision_signatures(baseline_payload)
        for cand in candidates:
            sch = tmpdir / "candidate.kicad_sch"
            outdir = tmpdir / "svg"
            if outdir.exists():
                shutil.rmtree(outdir)
            shutil.copyfile(args.schematic, sch)
            apply_target(sch, target, cand)
            svg = export_svg(sch, outdir)
            payload = detect_payload(sch, svg)
            hit = next((c for c in payload["collisions"] if target_match(c, target, cand)), None)
            introduced = sorted(collision_signatures(payload) - baseline_signatures)
            results.append(
                {
                    "candidate": cand,
                    "score": score(cand, args.anchor_x, args.anchor_y),
                    "collision": hit,
                    "introduced_collisions": introduced,
                }
            )

    results.sort(key=lambda r: (r["collision"] is not None, len(r["introduced_collisions"]), r["score"]))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
