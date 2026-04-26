#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
DEFAULT_KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import score_schematic as schematic_score


def kicad_cli() -> str:
    return os.environ.get("KICAD_CLI", DEFAULT_KICAD_CLI)


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_result(name: str, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": name,
        "argv": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def run_checked(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def render_svg(schematic: Path, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    run_checked([kicad_cli(), "sch", "export", "svg", "--output", str(outdir), str(schematic)])
    expected = outdir / f"{schematic.stem}.svg"
    if expected.exists():
        return expected
    svgs = sorted(outdir.glob("*.svg"))
    if not svgs:
        raise FileNotFoundError(f"no SVG exported into {outdir}")
    return svgs[0]


def inspect_schematic(schematic: Path, only_text: str | None, margin: float) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="kicad-tool-inspect-") as tmpdir:
        svg = render_svg(schematic, Path(tmpdir))
        payload = schematic_score.score_schematic_from_svg(schematic, svg, margin=margin)

    collisions = payload["collisions"]
    if only_text:
        pattern = re.compile(only_text)
        collisions = [collision for collision in collisions if pattern.search(collision["text"])]

    return {
        "score": payload["score"],
        "wire_length": payload["wire_length"],
        "collisions": collisions,
        "symbol_wire_conflicts": payload["symbol_wire_conflicts"],
        "filters": {
            "only_text": only_text,
            "margin": margin,
        },
    }


def cmd_sch_render_svg(args: argparse.Namespace) -> int:
    try:
        svg = render_svg(args.schematic, args.out)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or "")
        return exc.returncode
    if args.json:
        print_json({"svg": str(svg), "out": str(args.out)})
    else:
        print(svg)
    return 0


def cmd_sch_inspect(args: argparse.Namespace) -> int:
    payload = inspect_schematic(args.schematic, args.only_text, args.margin)
    if args.json:
        print_json(payload)
        return 0

    score = payload["score"]
    print(f"Score: total {score['total']} (collisions {score['collision_count']}, wire corners {score['wire_corner_count']})")
    print(f"Wire length: {payload['wire_length']['total_mm']} mm across {payload['wire_length']['segment_count']} segments")
    print(f"Collisions: {len(payload['collisions'])}")
    for collision in payload["collisions"]:
        owner = collision["kind"]
        if collision["owner_ref"] and collision["owner_key"]:
            owner = f"{collision['owner_ref']}.{collision['owner_key']}"
        print(f"- {collision['text']} [{owner}]")
    print(f"Symbol-wire conflicts: {len(payload['symbol_wire_conflicts'])}")
    return 0


def cmd_sch_erc(args: argparse.Namespace) -> int:
    args.report.parent.mkdir(parents=True, exist_ok=True)
    result = command_result(
        "sch erc",
        [
            kicad_cli(),
            "sch",
            "erc",
            "--exit-code-violations",
            "--output",
            str(args.report),
            str(args.schematic),
        ],
    )
    if args.json:
        print_json({"erc": result, "report": str(args.report)})
    else:
        print(f"ERC: exit={result['returncode']} report={args.report}")
        if result["stderr"]:
            sys.stderr.write(result["stderr"])
    return result["returncode"]


def cmd_sch_netlist(args: argparse.Namespace) -> int:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result = command_result(
        "sch netlist",
        [
            kicad_cli(),
            "sch",
            "export",
            "netlist",
            "--output",
            str(args.out),
            str(args.schematic),
        ],
    )
    if args.json:
        print_json({"netlist": result, "output": str(args.out)})
    else:
        print(f"Netlist: exit={result['returncode']} output={args.out}")
        if result["stderr"]:
            sys.stderr.write(result["stderr"])
    return result["returncode"]


def cmd_sch_validate(args: argparse.Namespace) -> int:
    erc_report = args.erc_report
    netlist_out = args.netlist_out
    svg_out = args.svg_out
    erc_report.parent.mkdir(parents=True, exist_ok=True)
    netlist_out.parent.mkdir(parents=True, exist_ok=True)
    svg_out.mkdir(parents=True, exist_ok=True)

    erc = command_result(
        "sch erc",
        [
            kicad_cli(),
            "sch",
            "erc",
            "--exit-code-violations",
            "--output",
            str(erc_report),
            str(args.schematic),
        ],
    )
    netlist = command_result(
        "sch netlist",
        [
            kicad_cli(),
            "sch",
            "export",
            "netlist",
            "--output",
            str(netlist_out),
            str(args.schematic),
        ],
    )

    render: dict[str, Any]
    try:
        svg = render_svg(args.sheet, svg_out)
        render = {"returncode": 0, "svg": str(svg), "out": str(svg_out)}
    except subprocess.CalledProcessError as exc:
        render = {"returncode": exc.returncode, "stderr": exc.stderr, "out": str(svg_out)}

    inspect: dict[str, Any]
    try:
        inspect = inspect_schematic(args.sheet, args.only_text, args.margin)
        inspect_returncode = 0
    except subprocess.CalledProcessError as exc:
        inspect = {"stderr": exc.stderr}
        inspect_returncode = exc.returncode

    payload = {
        "erc": {**erc, "report": str(erc_report)},
        "netlist": {**netlist, "output": str(netlist_out)},
        "render_svg": render,
        "inspect": inspect,
    }
    if args.json:
        print_json(payload)
    else:
        print(f"ERC: exit={erc['returncode']} report={erc_report}")
        print(f"Netlist: exit={netlist['returncode']} output={netlist_out}")
        print(f"SVG: exit={render['returncode']} out={svg_out}")
        if inspect_returncode == 0:
            score = inspect["score"]
            print(f"Inspect: total {score['total']} (collisions {score['collision_count']}, wire corners {score['wire_corner_count']})")
        else:
            print(f"Inspect: exit={inspect_returncode}")

    return 0 if erc["returncode"] == netlist["returncode"] == render["returncode"] == inspect_returncode == 0 else 1


def cmd_pcb_drc(args: argparse.Namespace) -> int:
    args.report.parent.mkdir(parents=True, exist_ok=True)
    command = [kicad_cli(), "pcb", "drc"]
    if args.schematic_parity:
        command.append("--schematic-parity")
    command.extend(["--output", str(args.report), str(args.board)])
    result = command_result("pcb drc", command)
    if args.json:
        print_json({"drc": result, "report": str(args.report)})
    else:
        print(f"DRC: exit={result['returncode']} report={args.report}")
        if result["stderr"]:
            sys.stderr.write(result["stderr"])
    return result["returncode"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kicad-tool",
        description="Repository-local KiCad inspection and validation helper.",
    )
    subcommands = parser.add_subparsers(dest="domain", required=True)

    sch = subcommands.add_parser("sch", help="schematic commands")
    sch_commands = sch.add_subparsers(dest="sch_command", required=True)

    render_svg_parser = sch_commands.add_parser("render-svg", help="export a schematic sheet to SVG")
    render_svg_parser.add_argument("schematic", type=Path)
    render_svg_parser.add_argument("--out", type=Path, default=Path("tmp/cupwarmer-sch-svg"))
    render_svg_parser.add_argument("--json", action="store_true")
    render_svg_parser.set_defaults(func=cmd_sch_render_svg)

    inspect_parser = sch_commands.add_parser("inspect", help="inspect schematic score and visual collisions")
    inspect_parser.add_argument("schematic", type=Path)
    inspect_parser.add_argument("--only-text")
    inspect_parser.add_argument("--margin", type=float, default=0.0)
    inspect_parser.add_argument("--json", action="store_true")
    inspect_parser.set_defaults(func=cmd_sch_inspect)

    erc_parser = sch_commands.add_parser("erc", help="run schematic ERC")
    erc_parser.add_argument("schematic", type=Path)
    erc_parser.add_argument("--report", type=Path, default=Path("tmp/cupwarmer-erc.rpt"))
    erc_parser.add_argument("--json", action="store_true")
    erc_parser.set_defaults(func=cmd_sch_erc)

    netlist_parser = sch_commands.add_parser("netlist", help="export schematic netlist")
    netlist_parser.add_argument("schematic", type=Path)
    netlist_parser.add_argument("--out", type=Path, default=Path("tmp/cupwarmer-post.net"))
    netlist_parser.add_argument("--json", action="store_true")
    netlist_parser.set_defaults(func=cmd_sch_netlist)

    validate_parser = sch_commands.add_parser("validate", help="run schematic validation checks")
    validate_parser.add_argument("schematic", type=Path)
    validate_parser.add_argument("--sheet", type=Path, required=True)
    validate_parser.add_argument("--erc-report", type=Path, default=Path("tmp/cupwarmer-erc.rpt"))
    validate_parser.add_argument("--netlist-out", type=Path, default=Path("tmp/cupwarmer-post.net"))
    validate_parser.add_argument("--svg-out", type=Path, default=Path("tmp/cupwarmer-sch-svg"))
    validate_parser.add_argument("--only-text")
    validate_parser.add_argument("--margin", type=float, default=0.0)
    validate_parser.add_argument("--json", action="store_true")
    validate_parser.set_defaults(func=cmd_sch_validate)

    pcb = subcommands.add_parser("pcb", help="PCB commands")
    pcb_commands = pcb.add_subparsers(dest="pcb_command", required=True)

    drc_parser = pcb_commands.add_parser("drc", help="run PCB DRC")
    drc_parser.add_argument("board", type=Path)
    drc_parser.add_argument("--report", type=Path, default=Path("tmp/cupwarmer-drc.rpt"))
    drc_parser.add_argument("--schematic-parity", action="store_true")
    drc_parser.add_argument("--json", action="store_true")
    drc_parser.set_defaults(func=cmd_pcb_drc)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or "")
        return exc.returncode
    except Exception as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
