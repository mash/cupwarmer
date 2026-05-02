# V1 PCB floorplan

## Scope

これは配線済みレイアウトではなく、物理配置の floorplan。現在の KiCad board は標準マグの比較的小さい底径を狙い、`76mm` 円形の placeholder outline と `Dwgs.User` / `Cmts.User` の配置ガイドを持つ。

## 座標系

- Board outline: center `(100,100)`, radius `38mm`, diameter `76mm`
- Mechanical center: `(100,100)`
- Coil / ferrite axis: board center
- 単位は millimeters

## 配置ゾーン

| Zone | Coordinate guide | 意図 |
| --- | --- | --- |
| Coil envelope | center `(100,100)`, ref `56mm` diameter | receiver coil と筐体中心を一致させる |
| Ferrite / mechanical envelope | center `(100,100)`, ref `68mm` diameter | ferrite、coil bonding、bottom stack tolerance の予約領域 |
| No large metal over coil core | center `50mm` diameter guide | 結合が強い中心領域から large copper、fastener、top-plate metal feature を離す |
| `U1` + resonant / rectifier cluster | `(109,75)` to `(127,94)` | STWLC38JRM、resonant capacitors、`CRECT/COUT` を近接配置 |
| `VOUT/Z3` + heater switch | `(110,99)` to `(130,122)` | VOUT clamp から heater switching までの high-current path を短くする |
| `H1/F1` wire pads | `(124,105)` to `(132,119)` | board edge 近傍に大型 hand-solder pads と strain relief 方向を確保 |
| `J1` service / I2C | `(76,116)` to `(92,128)` | edge access 可能な service connector。`RX_VAA` 2.5V adapter 前提 |
| Quiet sense | `(67,84)` to `(89,112)` | `NTC_TOP`、`RX_NTC`、low-current reference を heater return から離す |

## Routing intent

- `In1.Cu` は連続した `SYS_GND` plane のままにする。
- `VSSP`、`CRECT/COUT`、`Z3`、heater return は `U1` power return via cluster 近傍で閉じる。
- `VSSA`、`VAA/VDD` decoupling、`RX_NTC`、`NTC_TOP`、service reference は左側の quiet region に置く。
- Heater current は quiet sense/service region の下を横切らず、近傍で並走させない。
- `Z3` は heater-control section へ渡る前の VOUT exit で `C2/C3` と同じ物理グループに置く。

## 次の board work

1. `U1`、coil interface、resonant capacitors、`C2/C3/Z3`、heater switch、`H1/F1`、thermistors、`J1` の footprint を割り当てる。
2. placeholder の coil/ferrite guide を実部品 geometry へ置き換える。
3. `76mm` 円形外形を、実 coil/ferrite と enclosure clearance に合わせて lock する。
4. `U1`、local decoupling/resonant、VOUT clamp/heater switch、low-current connectors の順で placement する。
5. footprint placement 後に schematic parity 付き PCB DRC を実行する。
