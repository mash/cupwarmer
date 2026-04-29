---
name: kicad-sch-cleanup-loop
description: Iteratively improve a KiCad schematic sheet's `sch inspect` score, then tighten label/value placement. Main loop plans from a render of the user-targeted area plus a small surrounding margin, then dispatches a subagent per problem cluster in planned order. Use when the user asks to clean up, tidy, or improve the score of a sheet.
---

# KiCad Schematic Visual Cleanup Loop

Main loop plans + scores; subagents edit one cluster at a time. Edit conventions: `kicad-hardware-editing`. CLI: `kicad-tool`. Connectivity-parity: `kicad-validate`.

Inputs: `<sheet>` (child) and `<top>` = `hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch`.

## CLI-only

Never `Read`/`cat`/`grep` the `.kicad_sch` (thousands of S-expr lines blow context). Use `sch query` (`region`/`symbol`/`pin`/`wire`/`label`/`net`/`list`) and mutate via `sch edit`. Missing query/edit → extend `kicad-tool`.

## Baseline

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  <top> --sheet <sheet> --save-baseline tmp/cleanup-baseline > tmp/cleanup-baseline.json
```

Repo-root-relative paths. No `2>&1` (stderr breaks JSON). Record `score.total`, `collisions`, `symbol_wire_conflicts`.

## Phase 0 — area plan (mandatory before any edit)

Greedy "fix highest-priority first" produces myopic rewires that later moves invalidate. Plan the target area with surrounding context first.

1. **Target bbox** = user instruction + latest validate JSON, expanded ~one local block.
2. **Render** to `tmp/cleanup-overview.png` via `sch render-region`. Read alongside JSON.
3. **Cluster issues** (≤6) by spatial locality + topological coupling (shared symbol/net/pin field).
4. **Order clusters** by:
   - **Anchors first** (MCU / multi-pin connector / MOSFET orientation) — late anchor moves waste earlier rewires.
   - **Topology before cosmetics** — `symbol_wire_conflicts`/`collisions` before `wire_corner_count`/`diagonal`/`wire_length`.
   - **Independence** — non-coupled clusters: pick whichever unblocks more.
   - **Defer label/value placement to Phase 2** (Phase 1 component moves invalidate it).
5. **Per-cluster**: name, bbox, issues, fix preference (rewire → rotate/flip label → rotate/flip small comp → move label → move comp → reshape), dependencies on earlier clusters.
   - **Wire relocate/delete tap audit (mandatory).** Enumerate every connection on the original wire — wire endpoints, junctions, pin endpoints, labels — via `sch query region` over the wire's bbox (+~0.01 mm). Endpoint stubs orphan mid-span taps. Pass tap list to subagent.
6. **Write `tmp/cleanup-plan.md`** — clusters in order, one block each. Update as work progresses.

## Phase 1 — execute, validate per cluster

Score is a **long-horizon** target: an anchor rotation may temporarily lengthen neighbor wires, paying off only after 1–2 more clusters. Use checkpoints, not per-edit gating, for score.

### Two gates per dispatch

- **Hard gate (immediate revert).** Baseline-diff exit must be 0 (no new ERC, no removed nets, no removed nodes). Connectivity damage → `git checkout -- <sheet>`, record `(cluster, approach)`. Never tolerate.
- **Soft gate (deferred).** Score regression alone does **not** revert. Enter exploratory state with a checkpoint cap.

### Checkpoint loop

**Last-good checkpoint** = most recent state with `score.total ≤` baseline checkpoint. Materialized by `tmp/cleanup-baseline/` (only refreshed on accept) + working tree. Rollback = `git checkout -- <sheet>` (no stash/branch). Accepting mid-streak resets the streak counter to 0 — there is no "streak with accepted edits in the middle".

For each cluster in planned order:

1. **Re-render cluster** to `tmp/cleanup-area.png`, re-query bbox issues. Skip if already resolved upstream.
2. **Dispatch one subagent** with: cluster name, bbox, `tmp/cleanup-area.png`, issue records, symbols/labels/wires inside, pre-edit `score.total`, planned approach + rationale, fix preference, and a note that short-term score regression is allowed if it sets up the next cluster (prefer non-regressing fixes when equivalent).
3. **Validate**: `sch validate <top> --sheet <sheet> --baseline tmp/cleanup-baseline > tmp/cleanup-latest.json`
   - **Hard-gate fail** → revert, record, next cluster.
   - **Hard-gate pass, score ≤ last-good** → accept as new last-good. Refresh baseline (`--save-baseline tmp/cleanup-baseline`). Clear streak.
   - **Hard-gate pass, score worse** → keep edits, mark exploratory, **do not refresh baseline**, increment streak.
4. **After every exploratory dispatch**: re-render `tmp/cleanup-overview.png`, read it, compare against the plan's predicted *intermediate* topology. Diverges → planning miss: roll streak back, record divergence, update `tmp/cleanup-plan.md`.
5. **Checkpoint cap.** Roll back the entire exploratory streak when any of: streak == 3 without recovering ≤ last-good, single-step jump >~20% above last-good (runaway), or overview diverges from plan.
6. **Re-plan** when topology shifts around downstream clusters.

Stop Phase 1 when:
- all clusters processed (end on last-good — if exploratory, roll back first),
- a cluster exhausts every approach without progress and plan has no fallback,
- two consecutive cap rollbacks (plan itself is wrong — stop and re-plan with user). Track the cap-rollback count in `tmp/cleanup-plan.md` alongside the cluster log.

## Phase 2 — label/value tightening

After Phase 1 stabilizes positions. Cosmetic only — long-horizon argument does **not** apply. Per-cluster strict gate: accept only if ERC parity, `score.total` not worse, no new collisions; else revert immediately. Group components into local clusters; subagent places `Value`/`Reference` adjacent to symbol body and tightens labels onto wire endpoints — no symbol moves unless trivial. Stop after one full pass with zero accepts.

## Report

```
Sheet: <sheet>
Baseline: total=<n0> ERC=<e0>
Plan: <k> clusters
Phase 1: total=<n1> Δ=<n1-n0> checkpoints=<a1> hard-reverts=<r1> exploratory-rollbacks=<x1> skipped=<s1>
Phase 2: accepted=<a2> passes=<p2>
Final ERC: <parity | listed intentional>
```

Show `git diff --stat <sheet>`. Do not commit unless asked.

## Hard rules

- No edit before `tmp/cleanup-plan.md` exists.
- One dispatch = one cluster = one validate. Subagents never validate; main loop always does. Subagents always get the rendered PNG path, not just bbox JSON.
- **Connectivity regression ⇒ immediate revert.** Never tolerated.
- **Score regression ≠ immediate revert.** Exploratory; render overview; judge vs plan. Roll streak back only on (a) streak == 3 no recovery, (b) >~20% jump, or (c) overview divergence. Final state must be last-good.
- **Wire relocate ⇒ enumerate every tap**, not just endpoints. ERC count parity misses orphaned taps; baseline-diff `removed_nodes` catches it.
- Reuse stable `tmp/` filenames: `cleanup-baseline.json`, `cleanup-latest.json`, `cleanup-overview.png`, `cleanup-area.png`, `cleanup-plan.md`.
