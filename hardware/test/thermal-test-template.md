# Thermal Test Template

Use this template for v1 heater, F1, cup contact layer, and Qi/FOD evaluation. Keep one copy per test run.

## Test ID

- Date:
- Operator:
- Ambient temperature:
- Prototype revision:
- Schematic commit:
- PCB revision:
- Test location:

## Stack

- Top plate material:
- Top plate thickness:
- Cup contact layer material:
- Cup contact layer thickness:
- Heater type:
- Heater resistance measured cold:
- F1 part:
- F1 mounting method:
- Heater NTC / TH2 mounting method:
- Heater NTC target: coil / ferrite / top plate / heater hotspot, not PCB ambient
- Insulation layer:
- Coil:
- Ferrite:
- Qi pad:

## Instrumentation

- Heater NTC / TH2 channel:
- F1 body probe:
- Coil / ferrite edge probe:
- Top surface probe:
- Heater current measurement:
- VOUT measurement:
- RX_NTC voltage / STWLC38 NTC OTP event:
- IR camera / image path:
- Logging interval:

## DUT Configuration

- Power mode: wired bench supply / EPP 15W / BPP 5W
- Input voltage or pad model:
- Current limit:
- Cup material:
- Cup bottom diameter:
- Fill liquid:
- Fill volume:
- Initial liquid temperature:
- Cup offset from center:

## Test Matrix

| Case | Condition | Input | Duration | Pass / Fail | Notes |
| --- | --- | --- | --- | --- | --- |
| A1 | Cup present, centered | 12V / 15 ohm equivalent | 30 min | | |
| A2 | Cup absent | 12V / 15 ohm equivalent | Until F1 open or 30 min | | |
| A3 | Metal mug, centered | EPP 15W pad | 30 min | | |
| A4 | Cup present, offset +5mm | EPP 15W pad | 15 min | | |
| A5 | Cup present, offset +10mm | EPP 15W pad | 15 min | | |
| A6 | Cup present, centered | BPP 5W pad | 30 min | | |

## Time Series Log

| Time | VOUT | Heater current | Top surface | Heater NTC / TH2 | F1 body | Coil / ferrite edge | RX_NTC / OTP | Qi status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00:00 | | | | | | | | | |
| 01:00 | | | | | | | | | |
| 02:00 | | | | | | | | | |
| 05:00 | | | | | | | | | |
| 10:00 | | | | | | | | | |
| 20:00 | | | | | | | | | |
| 30:00 | | | | | | | | | |

## F1 Event Log

| Event | Time | Top surface | Heater NTC / TH2 | F1 body | RX_NTC / OTP | VOUT | Heater current | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 open | | | | | | | | |
| F1 reset | | | | | | | | |
| STWLC38 NTC OTP | | | | | | | | |

## Observations

- Surface hot spots:
- Heater NTC vs F1 open/reset delta:
- STWLC38 NTC OTP relative to F1 open/reset:
- Odor, discoloration, adhesive movement:
- F1 or wire movement:
- Qi pad stop / restart behavior:
- VOUT droop or oscillation:
- FOD events:

## Result

- Summary:
- Pass / fail:
- Required design change:
- Next test:
