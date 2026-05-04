---
name: jlcpcb-parts
description: Search the JLCPCB / LCSC parts catalogue from the command line. Use when you need to find a JLCPCB-stocked part by MPN, function, package, parametric attributes, or category, or to look up the LCSC number for a KiCad symbol's `LCSC` property. Builds a local SQLite from yaqwsx/jlcparts's published JSON shards (~100MB DL, refreshed every ~6h) behind `.agents/skills/jlcpcb-parts/scripts/jlcpcb_parts.py`.
---

# JLCPCB Parts

Plain-text CLI (no JSON) for the JLCPCB / LCSC catalogue.

```bash
python3 .agents/skills/jlcpcb-parts/scripts/jlcpcb_parts.py <command> ...
```

LCSC numbers display with `C` prefix (`C2040`); inputs accept `C2040` or `2040`.

## Commands

- `update` — force-refresh the cached SQLite (~100MB DL, builds local ~600MB SQLite).
- `search [<query>] [filters...]` — substring search on MPN/description and/or filters (AND-combined). Default limit 20.
- `show <LCSC>` — base fields, attributes, price tiers, datasheet URL, JLC partdetail URL.
- `schema` — categories with part counts.
- `schema <category>` — attribute keys + up to 8 sample values each.

### `search` filters

- `--category <name>` exact (discover via `schema`)
- `--package <name>` exact (`0603`, `SOT-23-5`)
- `--manufacturer <name>` substring, case-insensitive
- `--min-stock <N>`
- `--basic` | `--preferred` (JLC tier, mutex)
- `--attr "Key OP Value"` repeatable. Ops: `=` `>=` `<=` `>` `<` `~`. SI-prefixed numbers parsed (`0.1uF`, `25V`, `1k`).
- `--limit N` — applied **after** ordering (top-N in the order below)
- `--text-fallback` — if `--attr` filters yield 0 hits, retry with the attr **values** substring-matched against MPN/description (rescues parts whose upstream attribute fields are corrupt or use vendor-specific notation)

Output columns: `LCSC  MPN  Pkg  Type  Stock  $1  $100  Description`. Order: basic → pref → ext, then stock desc, unit-price asc.

**Attribute keys are category-specific and not guessable.** Always run `schema <category>` first and copy the exact key (capitalisation matters). Values are SI-formatted (`100nF`, `50V`); `--attr` accepts any SI form (`0.1uF`, `100k`) and the `~` operator does substring match on text values.

## Cache & freshness

- Cache: `$XDG_CACHE_HOME/jlcpcb-parts/components.sqlite3` (else `~/.cache/...`), shared across repos.
- First non-`update` command auto-downloads if missing.
- Every command prints DB age to **stderr**: `# JLCPCB DB: built 2026-05-02 (2d ago)`. The timestamp is the upstream `manifest.json:created` (yaqwsx refreshes every ~6h), not an HTTP `Last-Modified`. Age ≥ 7d adds `⚠ DB is Nd old — run 'update'`.

## Examples

```bash
# MPN lookup
... search "STWLC38JRM"

# Parametric: 0.1uF 0603 25V+ Basic caps
... search --category "Capacitors" --package 0603 \
    --attr "Capacitance=0.1uF" --attr "Voltage Rated>=25V" --basic --limit 10

# Detail
... show C14663

# Discover attributes before querying
... schema "Resistors"
```

## Troubleshooting

Zero results — work the funnel from the most-likely cause:

1. **Wrong attribute key** — re-run `schema <category>` and copy the exact key name. X7R lives under `Dielectric` for some subcategories and `Temperature Coefficient` for others.
2. **Too-strict operator** — swap `=` for `~` (substring) on text-ish attributes (`--attr "Dielectric~X7R"`).
3. **Tier filter too narrow** — drop `--basic` / `--preferred` to include extended parts.
4. **Corrupt or vendor-specific attribute fields** — yaqwsx's parser occasionally mis-routes MPN tokens into wrong attribute keys (e.g. TORCH `CT41G-...-2X1-...-K(N)` puts `2X1` in `Temperature coefficient`; the `(N)` actually denotes NP0). Add `--text-fallback` to retry the search with attr values matched against MPN/description when the structured filter returns 0.
5. **Absent from upstream** — yaqwsx drops parts that have been out of stock for >120 days; truly rare or new parts may not appear.
6. **Stale DB** — if the stderr banner shows `⚠ DB is Nd old`, run `update` and retry.

## Out of scope

- Writing LCSC# back to a KiCad symbol — use `kicad-tool`'s `sch edit set-property`.
- Live stock & price feeds — the local DB is a snapshot refreshed every ~6h upstream; current JLC stock may differ.

## Scripts

`scripts/jlcpcb_parts.py` is the only entry point; `db_cache.py` and `search.py` are imports-only.
