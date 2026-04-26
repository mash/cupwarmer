---
name: kicad-sch-cleanup-loop
description: Iteratively improve a KiCad schematic sheet's `sch inspect` score, then tighten label/value placement. Main loop watches the score and dispatches a subagent per problem area. Use when the user asks to clean up, tidy, or improve the score of a sheet.
---

# KiCad Schematic Visual Cleanup Loop

Main loop owns scoring; subagents (general-purpose Agent) own edits inside one problem area at a time. Defer to `kicad-hardware-editing` for edit conventions and `kicad-tool` for CLI.

Inputs: `<sheet>` (child) and `<top>` = `hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch`.

## Baseline

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  <top> --sheet <sheet> --json > tmp/cleanup-baseline.json
```

Record ERC violation identities, `score.total`, and the `collisions` / `symbol_wire_conflicts` arrays. ERC parity = same count and same identities.

## Phase 1 — score-driven loop

Repeat:

1. From latest inspect JSON, pick the highest-priority issue:
   `symbol_wire_conflicts` → `symbol_wire_clearance` → `collisions` → `wire_corner_count` → `diagonal_wire_penalty` → `wire_length`.
2. Expand to a **problem area**: a small bounding box around it that captures any nearby collisions/conflicts/corners.
3. Dispatch one subagent with: bounding box, all issue records inside it, list of symbols/labels/wires inside it, pre-edit `score.total`, and fix preference order (rewire → rotate/flip label → rotate/flip small component → move label → move component → reshape). Subagent may make multiple coordinated edits **inside the box**, must not change hierarchy/nets/symbol identity, and must not validate.
4. Main loop runs `sch validate --json`. Accept if ERC parity holds and `score.total` decreased **vs the last accepted value** (baseline on first iteration); otherwise `git checkout -- <sheet>` and record `(area_bbox, approach)` as tried.

Stop Phase 1 when **any** of:
- the highest-priority queue is empty (no issue remains across all priority levels) — success exit
- two consecutive top-priority areas exhaust their fixes (every approach in the preference order has been tried and rejected for that area) without improvement
- three consecutive dispatches are rejected

Bounding box: start ~one local block (a few grid steps) around the seed issue and expand to include any neighboring issues that touch it.

## Phase 2 — label/value tightening

Group sheet components into local clusters. For each cluster, dispatch a subagent to place each `Value`/`Reference` adjacent to its symbol body and tighten labels onto wire endpoints — cluster only, no symbol moves unless trivial. Main loop validates: accept if ERC parity, `score.total` not worse, no new collisions in the cluster; otherwise revert. Stop after one full pass with zero accepted edits.

## Report

```
Sheet: <sheet>
Baseline: total=<n0> ERC=<e0>
Phase 1: total=<n1> Δ=<n1-n0> accepted=<a1> rejected=<r1>
Phase 2: accepted=<a2> passes=<p2>
Final ERC: <parity | listed intentional>
```

Show `git diff --stat <sheet>`. Do not commit unless asked.

## Hard rules

- One subagent dispatch = one area = one validate cycle.
- Subagents never validate; main loop always does.
- Revert via `git checkout -- <sheet>` on any regression before next dispatch.
- All KiCad CLI through `kicad-tool`; all S-expression conventions through `kicad-hardware-editing`.
