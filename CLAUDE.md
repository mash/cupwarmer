# cupwarmer — project conventions

## Scratch / temporary files

- Scratch dir is **`./tmp/`** at the repo root (git-ignored). Every ephemeral artifact goes there: ERC/DRC reports, netlists, SVG/PNG renders, baselines, intermediate scripts, and command bodies for `git commit -F` / `gh pr create --body-file`.
- Nothing generated lands at the repo root. Always the literal `./tmp/` — do not introduce another scratch dir.
- `./tmp/` is disposable, not a record. Do not assume a file from an earlier session survives, and do not cite one as evidence. Anything worth keeping belongs in `docs/` or `wiki/`. Deleting stale contents is always safe — clear it out when it gets noisy.

## Reference material (datasheets, PDFs, source data)

- Datasheets, PDFs, and source data live in **`./wiki/`** — search there before fetching from the web or asking.
- Read **`./wiki/README.md`** first for that directory's conventions and index.
