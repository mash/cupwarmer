---
name: kicad-hardware-editing
description: Stage 1 (functional) workflow for editing KiCad hardware design files. Covers the editing mechanics — `sch edit` subcommands, dry-run/validate loop, plan-and-approval gate. Design judgement (invariants, partitioning, layout consistency, forbidden patterns) lives in `electronics-design-principles`. KiCad CLI lives in `kicad-tool`. Validation lives in `kicad-validate`. Score/layout tightening (stage 2) lives in `kicad-sch-cleanup-loop`.
---

# KiCad Hardware Editing

Editing **workflow** for KiCad hardware files. This skill owns the _how_; design _what/why_ lives in `electronics-design-principles`.

Project-specific information (board path, sheet inventory, net naming, stackup, partitioning) lives in the repo's hardware docs — `hardware/schematic/README.md`, `hardware/pcb/README.md`, and the project README under `hardware/kicad/<project>/README.md`. Read them before editing.

For any KiCad CLI invocation (render, inspect, ERC, netlist, validate, DRC), **read the `kicad-tool` skill via the Skill tool first** to get exact subcommands and flags.

For any decision about _what_ to change electrically (placement, grouping, decoupling, partitioning, rotation that affects pin meaning), consult **`electronics-design-principles`** before forming the plan.

## File types

| File         | Approach                                                               |
| ------------ | ---------------------------------------------------------------------- |
| `.kicad_sch` | Use `sch edit ...` subcommands. Preserve KiCad 10 formatting and UUIDs |
| `.kicad_pcb` | Manual S-expression edit (minimal, local only)                         |
| `.kicad_pro` | JSON edit (minimal)                                                    |
| `.kicad_prl` | Do not edit unless explicitly asked                                    |
| `.kicad_sym` | Keep in sync with embedded `lib_symbols` when changing custom symbols  |

## Editing rules

- For automated cases (move/add/delete symbol, wire, label, junction; add-pin), use `sch edit ...` — see `kicad-tool`. Always pass `--dry-run` first, then re-run without it. Validate via `kicad-tool` after every edit.
- Adding pins to symbols: use `sch edit symbol add-pin ...` — it updates both the schematic's embedded `lib_symbols` and the project's `.kicad_sym` library together. Coordinates are symbol-local (no Y negation here).
- Do not `Read`/`cat`/`grep` `.kicad_sch` — raw S-expression files are huge and burn the context window. Use `sch query` for scoped JSON.
- If `sch edit` lacks a subcommand for a write operation, **extend kicad-tool first** (`sch_edit.py` + argparse). Raw `Edit`/`Write` on `.kicad_sch` is the last resort and requires explicit user approval.

### Wire delete / replace — audit mid-span taps first

A wire can carry connections **anywhere along its length** (junctions, perpendicular wire endpoints, pin endpoints, label anchors), not just at its two endpoints. Endpoint-only stub replacement orphans the mid-span taps, and ERC misses it (a remaining junction at the orphaned coordinate keeps the count parity-clean).

Before any `sch edit wire delete` / replace: run `sch query region` over the wire's bbox (expand ~0.01 mm) and enumerate every tap; each must be re-attached by the new routing. Validate with `kicad-validate`'s baseline-diff workflow (`--save-baseline` / `--baseline`) — its `removed_nodes` check is what actually catches this.

### Automated `sch edit` subcommands

```
sch edit symbol move <sch> <REF> <X,Y> [--rotation R]
sch edit symbol delete <sch> <REF>
sch edit symbol set-property <sch> <REF> <KEY> <VALUE>
sch edit wire add <sch> <X1,Y1> <X2,Y2>
sch edit wire delete <sch> --uuid U
sch edit label add <sch> <KIND> <NAME> <X,Y> [--rotation R]   # KIND: global|hier|local; for global passive labels, justify follows rotation
sch edit label move <sch> <UUID> <X,Y> [--rotation R]
sch edit label delete <sch> <UUID>
sch edit junction add <sch> <X,Y>
sch edit junction delete <sch> --uuid U
```

All accept `--dry-run` and `--format {json,text}` (default `json`).

### Use `sch query` to gather coordinates

Read-only inspection (returns scoped JSON):

- `sch query symbol <sch> <REF>` — symbol position/rotation.
- `sch query pin <sch> <REF.PIN>` — absolute pin coordinates (+ net with `--netlist`).
- `sch query region <sch> <X1,Y1,X2,Y2>` — everything in an area.
- `sch query net|wire|label|lib-symbol|list` — other read-only forms.

If a needed query is missing, extend `kicad-tool` rather than fall back to raw reads.

## Workflow

This skill is **stage 1: functional editing**. Visual/score cleanup is stage 2 and lives in `kicad-sch-cleanup-loop` — finish the functional edit and validate it here, then hand off if score improvement is wanted.

### 0. Plan and get approval (mandatory)

Before the approval plan, **bird's-eye self-check, three zoom levels** — one sentence each (for you; surface anything load-bearing):

- **Board**: does this change fit the project's critical path now, or should it wait?
- **Sheet**: what function does the region serve, and will the change ripple style-wise into a follow-up pass elsewhere?
- **Local**: what does the *area* look like when done; what alternative framing might the request really mean (different scope/mechanism — "tighten labels" → "shorten Value text"; "add decoupling" → "consolidate an existing rail").

Then state and wait for approval:

1. **Goal** — what the design should do (design terms, not "add wires").
2. **Problem** — what's missing/wrong, citing specific symbols/nets/pins (via `sch query`).
3. **Approach** — proposed change + alternatives considered + why this one. Smallest unit that meets the goal.
4. **Placement** — for each new/moved symbol, which existing symbol or net it should sit _near_ and why. Apply `electronics-design-principles` (grouping, partitioning, decoupling near supply pins, function-grouped — no parking in empty corners).
5. **Layout sketch (ASCII art) — required** — show **both** the _current_ local layout and the _proposed_ layout side-by-side (or before/after) as small ASCII diagrams. Include anchor symbols/pins, the new/moved parts, and the connecting wires/labels. Coordinates (X,Y numbers) are _supplementary_ to the sketch, not a substitute — the sketch is the primary artifact for the user to spot orientation/topology issues before any edit runs. Approximate proportions are fine; what matters is relative position and connectivity. Example:

   ```
   Current:                Proposed:
        VCC                     VCC
         │                       │
         ●── U2.VCC               ●── U2.VCC
                                  │
                                 ─┴─ C99 100nF
                                  │
                                  ●── GND
   ```

Skip only if: (a) the user gave an exact single action ("move R5 to 100,50"), or (b) running under an autonomous-iteration context the user invoked — notably `/kicad-sch-cleanup-loop` (bounded edits, auto-revert on regression) or another explicit pre-approval. Auto Mode alone is **not** pre-approval — still plan and wait. When in doubt, plan and wait.

### 1. Pre-edit baseline

```bash
python3 .agents/skills/kicad-tool/scripts/kicad_tool.py sch validate \
  <path/to/top.kicad_sch> --sheet <path/to/edited-child.kicad_sch> \
  > tmp/validate-pre.json
```

(Or run `sch erc` and `sch netlist` individually if you need separate report/netlist artifacts — see `kicad-validate`.)

### 2. Edit (functional)

Smallest change satisfying the request. Pin additions: keep embedded `lib_symbols` and the project's `.kicad_sym` library in sync.

Scope of stage 1: connectivity, nets, symbols, pins, values, hierarchy, ERC correctness. Do **not** chase `sch inspect` score, collisions, `wire_corner_count`, `diagonal_wire_penalty`, or label/value tightening here — that is stage 2.

If the new edit happens to introduce obvious local mess (overlapping label, crossing wire) that would block reading the diff, fix only that local mess. Anything broader belongs to the cleanup loop.

#### Minimal worked example: add a global label

```
sch edit label add <sch> global <NAME> X,Y [--rotation R] --dry-run
```

Re-run without `--dry-run` to apply. Use `sch query` (above) to find coordinates first.

### 3. Validate

Use `kicad-validate` (one-shot `sch validate --sheet <edited>`).

### 4. Review

- New ERC violations → check coordinates, stroke type, `lib_symbols` integrity (intentional-violation handling lives in `kicad-validate`).
- Netlist mismatch → investigate unintended connectivity. For wire delete/move/replace, use `kicad-validate`'s baseline-diff (`--save-baseline` / `--baseline`); ERC parity alone can hide an orphaned mid-span tap.
- A worse `sch inspect` score is acceptable in stage 1 if connectivity is correct; do not chase it here.

### 5. Hand off to stage 2 (visual cleanup)

Stage 1 ends once ERC and netlist are correct. If the user wants score/layout tightening on the edited sheet, hand off to `kicad-sch-cleanup-loop` with the sheet path. Do not perform score-driven layout work in this skill.

## Board editing

Keep stable: `layers`, `setup`, `setup.stackup`, `Edge.Cuts`, title block. High-risk fields: `net`, `footprint`, `segment`, `via`, `zone`. Project-specific stackup and domain-separation rules live in `hardware/pcb/README.md`.

## Project settings

`.kicad_pro` is JSON. Minimal edits only.
