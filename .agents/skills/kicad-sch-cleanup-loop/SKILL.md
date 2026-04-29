---
name: kicad-sch-cleanup-loop
description: Iteratively improve a KiCad schematic sheet's `sch inspect` score, then tighten label/value placement. Main loop plans from a render of the user-targeted area plus a small surrounding margin, then dispatches a subagent per problem cluster in planned order. Use when the user asks to clean up, tidy, or improve the score of a sheet.
---

# KiCad Schematic Visual Cleanup Loop

Main loop owns scoring **and planning**; subagents (general-purpose Agent) own edits inside one problem area at a time. Defer to `kicad-hardware-editing` for edit conventions and `kicad-tool` for CLI.

Inputs: `<sheet>` (child) and `<top>` = `hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch`.

## CLI-only inspection

Never `Read`/`cat`/`grep` the `.kicad_sch`. The file is thousands of lines of S-expressions and sequential reads blow the context window. `sch query` returns scoped JSON for exactly the element you ask about — see the `kicad-tool` skill for the full list (`region`, `symbol`, `pin`, `wire`, `label`, `net`, `list`). Mutate only via `sch edit`. If a query/edit you need doesn't exist, extend `kicad-tool` instead of falling back to raw reads.

## Baseline

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  <top> --sheet <sheet> > tmp/cleanup-baseline.json
```

JSON が default。`2>&1` は付けない（stderr 混入で壊れる）。`<top>` `<sheet>` ともに repo root 相対パス。

Record ERC violation identities, `score.total`, and the `collisions` / `symbol_wire_conflicts` arrays. ERC parity = same count and same identities.

## Phase 0 — area-level plan (mandatory, before any edit)

Greedy "fix highest-priority issue first" produces myopic rewires that other planned moves immediately invalidate. Plan the **target area with surrounding context** before any subagent runs. Do not render the whole sheet.

1. **Identify the target area.** Start from the user's instruction (which region/symbols to clean up) and the latest validate JSON. Compute a bbox around it; expand by ~one local block (a few grid steps) so neighboring symbols, wires, and labels that could be affected are visible — but no more.
2. **Render the area with context** to `tmp/cleanup-overview.png` via `sch render-region`. Read this image alongside the JSON.
3. **Identify problem clusters inside the area.** Group issues into a small number (≤6) of named clusters by spatial locality and topological coupling (issues that share a symbol, share a net, or are inside the same pin field belong together).
4. **Order the clusters.** Decide an explicit order with reasons. Default heuristics, in priority:
   - **Anchors first.** A component whose rotation/flip dictates the surrounding routing (MCU, connector with many pins, MOSFET orientation) is fixed before its neighbors. Moving an anchor late wastes earlier rewires.
   - **Topology before cosmetics.** `symbol_wire_conflicts` / `symbol_wire_clearance` / `collisions` (coupled to routing) come before pure `wire_corner_count` / `diagonal` / `wire_length`.
   - **Independence.** Two clusters that don't share symbols or nets can be ordered freely; pick whichever unblocks more downstream area.
   - **Don't touch label/value placement in Phase 1.** That's Phase 2 — doing it now is rework once components move.
5. **Per-cluster plan.** For each cluster record: name, bbox, the issue records inside, the candidate fix in the preference order (rewire → rotate/flip label → rotate/flip small component → move label → move component → reshape), and any **dependencies** on earlier clusters ("after cluster A is rotated, this wire likely resolves on its own — re-check before dispatch").
6. **Write the plan to `tmp/cleanup-plan.md`** — clusters in order, one block each, with bbox and rationale. This is the working plan; update it as clusters complete.

Show the plan to the user only if asked; otherwise proceed.

## Phase 1 — execute the plan, re-validate per cluster

For each cluster **in planned order**:

1. **Re-render the cluster region** to `tmp/cleanup-area.png` (overwrite each iteration) and re-query the latest issues inside its bbox. If the cluster's issues are already gone (resolved by an earlier cluster's edit), skip and note it in the plan.
2. **Dispatch one subagent** with: cluster name, bbox, `tmp/cleanup-area.png` path, all issue records inside, list of symbols/labels/wires inside, pre-edit `score.total`, the planned fix approach + rationale from the plan, and the fix preference order. Subagent may make multiple coordinated edits **inside the bbox**, must not change hierarchy/nets/symbol identity, and must not validate.
3. **Main loop validates.** Run `sch validate <top> --sheet <sheet> > tmp/cleanup-latest.json`. Accept if ERC parity holds and `score.total` decreased **vs the last accepted value** (baseline on first iteration); otherwise `git checkout -- <sheet>` and record `(cluster, approach)` as tried in the plan.
4. **Re-plan if needed.** If the accepted edit visibly changed the topology around a downstream cluster (new collisions appeared, planned dependency triggered), re-render `tmp/cleanup-overview.png` for the target area and update `tmp/cleanup-plan.md` before moving on.

Stop Phase 1 when **any** of:
- all planned clusters are processed (success exit),
- a cluster exhausts every approach in the preference order without improvement and the plan has no fallback,
- three consecutive dispatches are rejected (stop and re-plan with the user).

Bounding box rule: start ~one local block (a few grid steps) around the seed issues and expand to include any neighboring issues that touch them.

## Phase 2 — label/value tightening

Only after Phase 1 has stabilized component positions. Group sheet components into local clusters. For each cluster, dispatch a subagent to place each `Value`/`Reference` adjacent to its symbol body and tighten labels onto wire endpoints — cluster only, no symbol moves unless trivial. Main loop validates: accept if ERC parity, `score.total` not worse, no new collisions in the cluster; otherwise revert. Stop after one full pass with zero accepted edits.

## Report

```
Sheet: <sheet>
Baseline: total=<n0> ERC=<e0>
Plan: <k> clusters
Phase 1: total=<n1> Δ=<n1-n0> accepted=<a1> rejected=<r1> skipped=<s1>
Phase 2: accepted=<a2> passes=<p2>
Final ERC: <parity | listed intentional>
```

Show `git diff --stat <sheet>`. Do not commit unless asked.

## Hard rules

- **No edit before the Phase 0 plan exists.** If `tmp/cleanup-plan.md` is missing, you have not planned yet.
- One subagent dispatch = one cluster = one validate cycle.
- Subagents never validate; main loop always does.
- Subagents always receive the rendered region PNG path, not just the bbox JSON.
- Revert via `git checkout -- <sheet>` on any regression before next dispatch.
- Reuse stable filenames in `tmp/`: `cleanup-baseline.json`, `cleanup-latest.json`, `cleanup-overview.png`, `cleanup-area.png`, `cleanup-plan.md`. Do not mint new suffixed names per iteration.
- All KiCad CLI through `kicad-tool`; all S-expression conventions through `kicad-hardware-editing`.
