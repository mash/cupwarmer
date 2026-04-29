# STWLC38JRM 初回回路方針

## 目的

`STWLC38JRM` ベースの `15W` Qi Cup Warmer に対して、初回回路図で固定する機能ブロックと接続方針をまとめる。

## 回路ブロック

```
Qi TX Pad
  ->
RX Coil
  ->
Resonant Network
  ->
STWLC38JRM
  ->
Programmable VOUT (target: 12V nominal)
  ->
Power Path Protection
  ->
Heater Power Stage
  ->
Flexible Heater

Sensors:
- NTC_A: top plate temperature
- NTC_B: power board temperature

Control:
- `STWLC38JRM` stand-alone operation
- Optional `I2C` service access during bring-up
```

## 初回アーキテクチャ

### 受電部

- `U1`: `STWLC38JRM`
- `L1`: `15W` 対応 Qi receiver coil, exact part `TBD`
- `AC1`, `AC2`: receiver coil / resonant network local nets
- `C_RES_*`: 共振ネットワーク用コンデンサ, value `TBD`
- `SHIELD1`: フレキシブルフェライト, exact part `TBD`

### 出力電圧方針

- 初回は `12V` 近傍を第一候補にする
- 理由: `15W` を `5V` で扱うより電流が低く、配線・FET・ヒーター設計が楽
- 目標ヒーター条件:
  - `12V`
  - `15Ω` 前後
  - `9.6W` 前後

### ヒーター電力段

- ヒーター直結ではなく、スイッチング制御を入れる
- 初回方針:
  - `Q1`: logic-level N-MOSFET による low-side switched stage
  - `R_GATE`, `R_GS`: ゲート安定化
  - `F1`: `KSD9700-70/5JSB/080C` 独立ハード遮断
  - `H1`: 外部 heater/F1 series assembly を受ける大型 solder pads / wire pads
  - `R_SENSE`: optional current-monitor placeholder

### 温度保護

- `NTC_A`: トッププレート裏面
- `NTC_B`: 受電基板の hottest area 近傍
- `F1`: ヒーター系に独立遮断を入れる
- 初版は on-board reader を持たず、評価用 thermal placeholder として残す
- v1 では flexible heater と F1 は手実装ワイヤで接続する。board-to-wire connector や FPC/FFC connector は採用しない

### 制御部

- 初回回路図では外部 `MCU` は載せない
- 最低条件:
  - `I2C` service access
  - `STWLC38JRM` stand-alone 受電
  - heater gate は初版では `VOUT_12V` から常時 ON 駆動
  - `RX_INTB` は bring-up / status monitor として露出
- `I2C` service header は `RX_VAA` 2.5V VREF 追従アダプタ専用。3.3V 固定 pull-up の直結は禁止

## 現在のネット名

KiCad 回路図ではシート間接続に以下の global label を使う。

- `VOUT_12V`
- `SYS_GND`
- `RX_VAA`
- `RX_VDD`
- `RX_NTC`
- `RX_INTB`
- `I2C_SCL`
- `I2C_SDA`
- `NTC_TOP`
- `NTC_PCB`
- `I_HEATER_MON`

`rx-power` シート内の STWLC38 周辺では以下を local label として使う。

- `AC1`
- `AC2`
- `GPIO0`

以下は過去の仮名または実装詳細で、現在の global label としては使わない。

- `RECT_IN` -> STWLC38 の `VRECT` pin group / local rectified rail
- `HEATER_CTRL` -> 初版では `VOUT_12V` から gate network を常時 ON 駆動
- `HEATER_SW` -> heater-control シート内の MOSFET switched node
- `HEATER_RT` -> 現在は未使用

## 主要ネットの役割

| Net | 用途 |
| --- | --- |
| `VOUT_12V` | STWLC38 programmable output, heater stage input, indicator LED supply |
| `SYS_GND` | system ground shared by RX, heater, and monitor circuits |
| `RX_VAA` | STWLC38 analog/service reference rail, I2C/NTC pull-up rail |
| `RX_VDD` | STWLC38 local digital rail |
| `RX_NTC` | STWLC38 NTC input / default pull-up node |
| `GPIO0` | local STWLC38 GPIO net for LED2 active-low sink indicator |
| `RX_INTB` | STWLC38 interrupt/status monitor |
| `NTC_TOP` | top plate thermal monitor node |
| `NTC_PCB` | receiver board thermal monitor node |
| `I2C_SCL` | STWLC38 service I2C clock |
| `I2C_SDA` | STWLC38 service I2C data |
| `I_HEATER_MON` | heater current monitor placeholder/export node |

## 初回で入れるべき部品

- `U1` receiver IC
- `L1` receiver coil
- 共振コンデンサ
- 出力バルク / デカップリング
- NTC 2 系統
- ヒーター MOSFET
- ハード遮断部品
- I2C / service header

## 初回では未確定の点

- ST 推奨の完全な外付け定数
- 受電コイルと共振値
- ヒーターの最終抵抗値
- ハード遮断を `PPTC` にするか thermostat にするか
- heater gate drive の v2 以降の制御方式

## 直近の次作業

1. `STWLC38JRM` の推奨外付け回路を確認
2. `U1` 周辺の最小回路を回路図へ起こす
3. ヒーター電力段の方式を low-side PWM で確定するか再判断する
