# STWLC38JRM 初回 PCB 方針

## 目的

初回 PCB で、`WLCSP40` 実装、Qi 受電、ヒーター電力経路、温度センサを破綻なく共存させるための配置方針をまとめる。

## スタックアップ前提

- 初回は `4-layer` を第一候補
- 理由:
  - `WLCSP40` breakout の余裕
  - 受電部と電力段の return を整理しやすい
  - `I2C` / sense / PWM の静かな層を取りやすい

### 層構成 (v1)

1. Top (`F.Cu`): `U1`, small passives, AC1/AC2, VOUT_12V 出口, U1 escape
2. Inner 1 (`In1.Cu`): solid `SYS_GND` plane（連続）
3. Inner 2 (`In2.Cu`): solid `SYS_GND` plane（連続）
4. Bottom (`B.Cu`): heater 高電流 return, `J1/J2/J3`, debug, optional MCU

VOUT_12V は単一 rail・`0.8A` のため内層 power plane を持たず、L1/L4 の
太いポリゴン + `Z3 / C2/C23 / Q1.D` 近傍の via cluster で配電する。AC1/AC2
と WLCSP40 escape の return 整合を最優先し、L2/L3 を両方 solid GND にする
（詳細: `docs/plans/20260505-4layer-stackup-inner-layers.md`）。

## 機能ブロック配置

### 受電部

- `L1` とフェライトは機械中心に合わせる
- `U1` はコイル給電経路を最短にできる位置
- 共振コンデンサは `U1` とコイルの間を最短・対称に置く

### 電力段

- ヒーター MOSFET と保護部品は `VOUT` 出口近傍
- 大電流ループを小さく保つ
- 温度センサ `NTC_B` はこの領域の hottest area 近傍
- `Z3` は `C2/C3` と同じ VOUT 出口グループに置き、heater-control sheet へ渡る前に clamp する
- `Z3` の GND return は短く太くし、U1 近傍の power return 領域へ戻す
- F1/H1 の wire pad は `0.8A` 連続、手はんだ、引張緩和を前提に大きめにする

### 制御部

- optional MCU は電力段から少し離し、`I2C` と NTC 読み出しを短く保つ
- debug header は board edge に逃がす
- `J1` は `RX_VAA` 2.5V VREF 追従 adapter 専用。3.3V 固定 pull-up / 3.3V push-pull 出力を想定した配置やラベルにしない

## Return path / GND 制約

- 回路図ネット名は `SYS_GND` 一本のまま扱う
- `In1.Cu` は solid GND plane を維持する
- v1 では split plane、net-tie、離れた一点合流は使わない
- `VSSP`、`CRECT/COUT`、`Z3`、heater return は power return 領域として短く太く U1 近傍へ戻す
- `VSSA`、`VAA/VDD` decoupling、`RX_NTC`、I2C/service reference は quiet 領域として扱う
- heater return を `VSSA`、`RX_NTC`、I2C/service reference の下や並走近傍に通さない
- `VSSP/VSSA/VSSD` の実質合流点は U1 直近の GND via cluster とする

## Placement checklist before routing

- `U1` 周辺に `VAA/VDD/VRECT/VOUT` decoupling を最短配置したか
- `C2/C3/Z3` が VOUT 出口として一群になっているか
- `Z3` から GND plane への return が短く太いか
- heater current loop が quiet analog / service 領域を横切らないか
- `RX_NTC` と `NTC_TOP` の配線が high-current node と並走していないか
- coil / ferrite / top plate fastening metal の keepout が機構側と一致しているか
- H1/F1 wire pads に手はんだ作業余裕と引張緩和余裕があるか

## STWLC38JRM 実装方針

- `0.4 mm pitch WLCSP40`
- 初回は ST 提供 footprint を起点にする
- 発注前に外注先へ以下を確認してから pad を確定する
  - `NSMD` / `SMD`
  - `via-in-pad`
  - filled / capped via
  - stencil
  - aperture reduction

## 配置で避けること

- `U1` 直下やコイル直近に不要な大きな銅面
- heater 大電流 return を quiet analog path と共有すること
- top plate fastening metal をコイル中心に近付けること
- `NTC_TOP` の長配線を high-current switching node に並走させること

## 初回で入れる基板要素

- `U1` footprint
- coil interface footprint
- ferrite keepout notes
- heater output pads
- top-plate NTC connector or solder pads
- board-temperature NTC footprint
- optional MCU footprint and passives
- `I2C` / debug header

## V1 floorplan

標準マグの比較的小さい底径を狙い、KiCad board file に `76mm` 円形外形と `Dwgs.User` / `Cmts.User` の配置ガイドとして v1 floorplan を入れた。詳細は `floorplan-v1.md` を参照。

概要:

- `76mm` diameter circular placeholder outline
- 中心 `(100,100)` を coil / ferrite / enclosure axis とする
- 右上を `U1` + resonant / rectifier cluster
- 右側を `VOUT/Z3` + heater switch + `H1/F1` wire pads
- 左下を `J1` service / I2C
- 左側を `NTC_TOP` / `RX_NTC` quiet sense region

## Open Items

- exact board diameter
- exact coil footprint
- ~~final stackup~~ → 4-layer `SIG / GND / GND / SIG`（L2/L3 とも solid `SYS_GND`）。詳細: `docs/plans/20260505-4layer-stackup-inner-layers.md`。fab 確定の層厚・誘電体寸法は発注前に追記
- board house design rules
- H1/F1 wire pad geometry
- U1 breakout DFM confirmation
