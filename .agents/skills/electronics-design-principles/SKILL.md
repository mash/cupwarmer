---
name: electronics-design-principles
description: Electrical design invariants, placement/partitioning rules, and forbidden patterns for KiCad hardware work in this repo. Consult before moving/rotating components, planning new circuitry, or reviewing a sheet. Editing + validation mechanics live in the `kicad-workflow` skill (kicad-skills plugin); CLI commands live in `kicad-tool`.
---

# Electronics Design Principles

Design judgement that applies regardless of which skill is doing the editing. When deciding *what* should change electrically — not *how* to encode the change — consult this skill.

## Core idea

- Schematic = logical truth.
- PCB = physical constraint solving.
- Think in nets and constraints, not in wires and shapes.
- Generate → check → refine. No "probably works".
- Prefer simple and robust over clever.

## Flow

`req → arch → schematic → verify → layout → drc → output`

Don't skip stages. A schematic edit that has no clear requirement behind it, or that hasn't been verified, isn't ready for layout.

## Invariants (must hold after any edit)

- No floating nets or pins.
- Every IC has decoupling near its supply pins.
- Continuous ground reference; minimal return-path loop area.
- Low-impedance power paths (bulk + local decouplers on every rail that needs them).
- Manufacturable and testable.

If an edit would violate any of these, stop and surface the conflict.

## Schematic

**Blocks:** power | mcu | io | analog | rf

**Always:**
- Decoupling caps placed near the IC pins they serve (visually and electrically).
- Bulk caps on rails.
- Pull resistors where the bus/pin requires them (I²C, reset, boot-mode straps, etc.).

**Validate (electrical, not just ERC):**
- Polarity (electrolytics, diodes, connectors).
- Pin mapping (correct pin function on correct net).
- Rails actually connected end-to-end.

## Placement / partitioning

**Placement:**
- Mechanical constraints first (connectors, mounting, antennas).
- IC central, peripherals nearby.
- Minimize crossings.

**Partition:**
- Separate analog / digital / power domains.
- Don't route noisy signals through sensitive areas.

### Grouping (schematic) — layout consistency

Electrically equivalent parts should read as a group on the sheet.

**Rules:**
- Parts with the same electrical role — decouplers on the same rail, components of the same divider/filter, pull-ups on the same bus — should share either an X or a Y coordinate.
- Choose the shared axis to follow the flow of signal/power (Y for a rail running horizontally, X for supplies stacked vertically).
- Place Reference/Value properties on the same row/column as the shared axis.

**Decision:**
- Before moving a part, state in one line which existing group it belongs to.
- If it belongs to a group, align it to that group's shared axis.
- If the placement intentionally falls outside any group, state the reason before proceeding.

**On collision:**
- Preserve the group's shared axis first; resolve conflicts by offsetting individual properties.
- Breaking the axis itself is a last resort.

## Routing (PCB)

- Short, direct traces.
- Orthogonal per layer.
- No sharp angles.
- Solid ground plane; continuous return path.
- Length-/impedance-controlled where the signal demands it.

## Debug / observability

Designs should be debuggable on the bench:
- Test points on key nets.
- Debug headers (UART/SWD).
- Power rails observable (probe point or LED where appropriate).

## Constraints to optimize

In rough priority order, but always weighed in context:
- Signal integrity.
- Thermal.
- Manufacturability (DFM).
- Cost.

## Forbidden

- No decoupling on an IC.
- Blind autorouting.
- Mixing noisy and sensitive signals on the same plane / adjacent traces.
- Breaking DFM rules (clearance, antenna structures, unconnected copper).

## When to consult this skill

- Before moving or rotating a component (does the move respect electrical intent?).
- Before adding new circuitry (which block? which rail? what invariants apply?).
- During schematic review (run the invariants checklist).
- When deciding how to partition a new sheet.

For *how* to encode an edit safely and validate after, go to `kicad-workflow` (kicad-skills plugin).
