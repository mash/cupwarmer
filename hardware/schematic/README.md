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
- `C_RES_*`: 共振ネットワーク用コンデンサ, value `TBD`
- `SHIELD1`: フレキシブルフェライト, exact part `TBD`

### 出力電圧方針

- 初回は `12V` 近傍を第一候補にする
- 理由: `15W` を `5V` で扱うより電流が低く、配線・FET・ヒーター設計が楽
- 目標ヒーター条件:
  - `12V`
  - `10Ω` 前後
  - `14.4W` 前後

### ヒーター電力段

- ヒーター直結ではなく、スイッチング制御を入れる
- 初回方針:
  - `Q1`: logic-level N-MOSFET による low-side switched stage
  - `R_GATE`, `R_GS`: ゲート安定化
  - `F1`: 独立ハード遮断 `TBD`
  - `R_SENSE`: optional current-monitor placeholder

### 温度保護

- `NTC_A`: トッププレート裏面
- `NTC_B`: 受電基板の hottest area 近傍
- `F1`: ヒーター系に独立遮断を入れる
- 初版は on-board reader を持たず、評価用 thermal placeholder として残す

### 制御部

- 初回回路図では外部 `MCU` は載せない
- 最低条件:
  - `I2C` service access
  - `STWLC38JRM` stand-alone 受電
  - heater gate drive source は `TBD`

## 推奨ネット名

- `RECT_IN`
- `VOUT_12V`
- `HEATER_CTRL`
- `HEATER_SW`
- `HEATER_RT`
- `NTC_TOP`
- `NTC_PCB`
- `I2C_SCL`
- `I2C_SDA`
- `I_HEATER_MON`

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
- heater gate drive source

## 直近の次作業

1. `STWLC38JRM` の推奨外付け回路を確認
2. `U1` 周辺の最小回路を回路図へ起こす
3. ヒーター電力段の方式を low-side PWM で確定するか再判断する
