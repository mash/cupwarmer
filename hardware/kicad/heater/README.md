# Cup Warmer Flexible Heater

This directory contains a KiCad-generated Gerber package for the external flexible heater.

- Board outline: 55 mm diameter, sized to the thermal stack (aluminum spreader Ø54.5 mm, heater seat Ø50.7/Ø57.2 mm) — **not** the Ø50 mm control PCB. The heater covers the spreader, seats on the bottom-tray heater-seat step, and stays under the Ø56.5 mm cup contact pad.
- Heating element routing: intentionally not drawn; ask JLCPCB to route it during engineering review
- Bottom lead-out pads: four pads labelled `H+`, `NTC`, `NTC_GND`, and `H-`
- Center NTC placement marker: `NTC` near the board center
- Target electrical spec: 12 V, about 12 W, nominal 12 ohm
- Preferred routed element material: FeCrAl 0.05 mm, adjusted by JLCPCB to hit nominal 12 ohm

JLCPCB flexible-heater order notes:

- Upload `gerber/heater-jlcpcb-flex-heater.zip`.
- Select a flexible heater service, not a normal FR-4 PCB service.
- Ask JLCPCB to route the heater pattern. The uploaded Gerber only defines the 55 mm circular shape, bottom lead-out pad locations, and requested center NTC location.
- Ask JLCPCB to manufacture the heating element as FeCrAl 0.05 mm, or adjust routing/material during engineering review to hit 12 ohm.
- Ask for an embedded 100k NTC, B25/85 approximately 4260 K, placed at the center `NTC` marker if available.
- Cable exit should be from the bottom lead-pad area. The cupwarmer PCB harness expects `H+`, `H-`, `NTC`, and `NTC_GND` as separate wires.
- The Gerber dimensions should auto-detect as 55 mm x 55 mm on JLCPCB.
