#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from layout_moves import LayoutMove, apply_move, generate_candidate_moves
from layout_score import score_schematic


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("schematic", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--iterations", type=int, default=8)
    ap.add_argument("--grid-step", type=float, default=1.27)
    ap.add_argument("--rings", type=int, default=2)
    ap.add_argument("--allow-symbol-moves", action="store_true")
    ap.add_argument("--margin", type=float, default=0.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    history: list[dict] = []
    best_move: LayoutMove | None = None

    with tempfile.TemporaryDirectory(prefix="kicad-layout-optimize-") as tmpdir:
        tmpdir = Path(tmpdir)
        current = tmpdir / "current.kicad_sch"
        shutil.copyfile(args.schematic, current)

        current_scored = score_schematic(current, margin=args.margin)
        history.append({"iteration": 0, "score": current_scored["score"], "move": None})

        for iteration in range(1, args.iterations + 1):
            candidates = generate_candidate_moves(
                current_scored,
                grid_step=args.grid_step,
                rings=args.rings,
                allow_symbol_moves=args.allow_symbol_moves,
            )
            if not candidates:
                break

            best_candidate_path: Path | None = None
            best_candidate_score: dict | None = None
            best_move = None

            for idx, move in enumerate(candidates):
                candidate_path = tmpdir / f"iter-{iteration}-candidate-{idx}.kicad_sch"
                apply_move(current, move, candidate_path)
                candidate_scored = score_schematic(candidate_path, margin=args.margin)
                if candidate_scored["score"]["total"] >= current_scored["score"]["total"]:
                    continue
                if best_candidate_score is None or candidate_scored["score"]["total"] < best_candidate_score["score"]["total"]:
                    best_candidate_path = candidate_path
                    best_candidate_score = candidate_scored
                    best_move = move

            if best_candidate_path is None or best_candidate_score is None:
                break

            shutil.copyfile(best_candidate_path, current)
            current_scored = best_candidate_score
            history.append(
                {
                    "iteration": iteration,
                    "score": current_scored["score"],
                    "move": None if best_move is None else vars(best_move),
                }
            )

        shutil.copyfile(current, args.output)

    result = {
        "input": str(args.schematic),
        "output": str(args.output),
        "iterations_run": len(history) - 1,
        "final_score": history[-1]["score"],
        "history": history,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"output={result['output']}")
        print(f"iterations={result['iterations_run']}")
        print(f"final_score={result['final_score']['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
