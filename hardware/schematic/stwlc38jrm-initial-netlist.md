# STWLC38JRM 初回ネットリスト案

## Power

| Net | Source | Sink | Notes |
|---|---|---|---|
| `COIL_P` | `L1` | `U1` resonant input | exact pin `TBD` |
| `COIL_N` | `L1` | `U1` resonant input | exact pin `TBD` |
| `RECT_IN` | `U1` | local decoupling | internal rectified rail |
| `VOUT_12V` | `U1` | heater stage / bulk caps | target programmable output |
| `RX_VDD` | `U1` local logic rail | `I2C` pullups / service reference / NTC dividers | service/monitor reference rail |
| `PGND` | power return | heater / U1 | keep separate from quiet analog return until star point |

## Heater Path

| Ref | From | To | Notes |
|---|---|---|---|
| `F1` | `VOUT_12V` | `HEATER_PROTECTED` | hard cutoff placeholder |
| `H1` | `HEATER_PROTECTED` | `HEATER_SW` | flexible heater |
| `Q1` | `HEATER_SW` | `PGND` | low-side N-MOSFET |
| `R_SENSE` | `Q1 source` or low side | `PGND` | optional current sense placeholder |

## Sensing / Control

| Signal | From | To | Notes |
|---|---|---|---|
| `NTC_TOP` | `NTC_A` | evaluation pads or future monitor | top plate thermal placeholder |
| `NTC_PCB` | `NTC_B` | evaluation pads or future monitor | board thermal placeholder |
| `RX_INTB` | `U1` | status monitor header | optional interrupt/status observe point |
| `I2C_SCL` | service header | `U1` | bring-up / configuration |
| `I2C_SDA` | service header | `U1` | bring-up / configuration |
| `HEATER_CTRL` | `TBD` | `Q1 gate network` | gate drive source still open |
| `I_HEATER_MON` | heater shunt | service measurement or future monitor | optional current monitor |

## Open Items

- `U1` pin map from official package / data brief
- whether `STWLC38JRM` stand-alone mode is sufficient for first spin
- final decision on heater high-side vs low-side switching
