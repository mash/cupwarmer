# v1 Heater Incoming Inspection

## Test ID

- Date: 2026-08-16
- Operator: Masakazu Ohtsuka
- Ambient temperature: approximately 22°C
- Prototype revision: v1
- DUT: JLCPCB flexible silicone heater
- JLCPCB batch: W2026061317360571
- JLCPCB order: FH2026061328500004

## Factory Inspection Record

Values transcribed from the outgoing inspection report supplied with the heater:

- Result: PASS
- Finished outer diameter: 55.40mm (nominal 55mm, tolerance ±1.0mm)
- Finished thickness: 1.16mm (tolerance ±0.2mm)
- Lead length: 42.00mm (nominal 40mm, tolerance ±5mm)
- Heater resistance: 11.88Ω (nominal 12.00Ω, tolerance ±5%)
- NTC resistance: 98.4kΩ (nominal 100kΩ)
- Adhesive: 3M 468MP
- Heater wire: 26AWG
- F1 marking visible on received assembly: KSD9700, 70°C, 250V 5A

## Local Unpowered Inspection

- Heater power-pair resistance: 11.9Ω — PASS
- NTC resistance after handling at approximately 22°C ambient: approximately 90kΩ
- NTC resistance after warming with fingers: 79kΩ — PASS; resistance decreased with temperature
- Isolation between heater power pair and NTC pair: open circuit — PASS
- Heater/NTC wire grouping: two outer unmarked leads form one pair; two center red-marked leads form the other pair

## Result

- Overall result: PASS
- The heater power path, embedded NTC response, and isolation between the power and sensor circuits survived shipping.
- Do not treat the approximately 90kΩ reading as an equilibrium 22°C characterization because the assembly had been handled immediately beforehand.
- The reported 1.16mm finished thickness is greater than the 0.5mm silicone-film value used in the initial enclosure assumptions. Verify mechanical clearance using the received assembly before removing the 3M liner or bonding the stack.

## Next Test

- Dry-fit the heater in the printed bottom tray with the adhesive liner left in place.
- Confirm outer-diameter clearance, lead-tab exit, F1 clearance, and that the heater lies flat without compression or buckling.

## STWLC38 Read-Only Bring-Up (2026-08-22)

Test conditions:

- Heater H+ / VOUT lead disconnected and insulated.
- Receiver powered from a Qi transmitter; CP2112 connected through the PCA9306 level translator.
- All accesses below were read-only. No STWLC38 register or NVM writes were performed.

Results:

- CP2112 enumerated as VID `0x10C4`, PID `0xEA90`, serial `00E1E3D6`.
- STWLC38 acknowledged at 7-bit I2C address `0x61`.
- Chip ID: `0x0026`.
- Chip revision: `0x03`.
- ROM ID: `0x0161`.
- NVM patch ID: `0x1299`.
- RAM patch ID: `0x0000`.
- Configuration ID: `0x1026`.
- Production ID: `0x0007`.
- Operation mode: `0x02` (Qi RX mode).
- System/NVM error bytes at `0x002C..0x002F`: `00 00 00 00` (no reported boot, header, or CRC error).
- BPP VOUT setting at `0x00B1..0x00B2`: `00 2D` (5.0V).
- EPP VOUT setting at `0x00B3..0x00B4`: `00 00`; not the required 12V cupwarmer configuration.
- Live monitor snapshot: VRECT `5136mV`, VOUT `4985mV`, IOUT `43mA`, operating frequency `145kHz`, TMEAS raw `0x018A`.

Conclusion:

- The assembled IC is not blank: valid, nonzero patch/configuration IDs load without NVM errors.
- The loaded configuration is not suitable for the 12V heater. Keep the heater power lead disconnected until a cupwarmer-specific configuration, protection actions, and FOD settings are programmed and verified.

## STWLC38 Configuration Staging (2026-08-22)

- Installed chip revision `0x03` maps to STWLC38JRM cut 1.2.
- Selected official starting pair: patch `1656` plus configuration `1078 cut1.2 EPP12V`.
- The unmodified ST configuration and a checksum-pinned fetch helper are staged in `hardware/firmware/stwlc38/`.
- This is a bring-up reference configuration only. Coil/stack-specific FOD calibration and explicit verification of NTC/protection actions remain required before reconnecting the heater.
- DC programming supply connection is `J2 pin 1 (VOUT_12V)` = +5V and `J2 pin 3 (SYS_GND)` = 0V, with the coil off the Qi transmitter and the heater H+ lead disconnected.
