# cupwarmer — project conventions

## Scratch / temporary files

- The temporary working directory is **`./tmp/`** at the repo root.
- All ephemeral artifacts (validation snapshots, ERC reports, netlists, SVG renders, baseline files, multi-line command bodies passed to `git`/`gh`, intermediate Python scripts, etc.) go under `./tmp/`.
- Skills and scripts that emit `tmp/...` paths mean this directory.
- `./tmp/` is git-ignored. Do not commit anything from it.
- Always reference it with the literal `./tmp/` (or `tmp/` from repo root) — do not introduce a different scratch dir.

## Reuse files instead of fanning out

- For a recurring artifact (validation snapshot, ERC report, netlist, score JSON, baseline, command-body file), use **one stable filename per role** and overwrite it on each run.
- Do not create timestamped, suffixed, or otherwise proliferating files (`tmp/foo-1.json`, `tmp/foo-pre-2.json`, `tmp/commit-msg-2.txt`). One file per role; the latest run replaces the previous.
- If you need a before/after pair, two stable files is the cap (e.g. `tmp/score-pre.json`, `tmp/score-post.json`) — not a sequence per iteration.
- Same for one-shot inputs to `git commit -F` / `gh pr create --body-file`: reuse `tmp/commit-msg.txt` / `tmp/pr-body.txt` rather than minting new names.

