# STWLC38JRM 初回 PCB 方針

## 目的

初回 PCB で、`WLCSP40` 実装、Qi 受電、ヒーター電力経路、温度センサを破綻なく共存させるための配置方針をまとめる。

## スタックアップ前提

- 初回は `4-layer` を第一候補
- 理由:
  - `WLCSP40` breakout の余裕
  - 受電部と電力段の return を整理しやすい
  - `I2C` / sense / PWM の静かな層を取りやすい

### 仮の層構成

1. Top: `U1`, small passives, short critical routing
2. Inner 1: solid ground
3. Inner 2: power and secondary routing
4. Bottom: heater stage, connectors, debug, optional MCU

## 機能ブロック配置

### 受電部

- `L1` とフェライトは機械中心に合わせる
- `U1` はコイル給電経路を最短にできる位置
- 共振コンデンサは `U1` とコイルの間を最短・対称に置く

### 電力段

- ヒーター MOSFET と保護部品は `VOUT` 出口近傍
- 大電流ループを小さく保つ
- 温度センサ `NTC_B` はこの領域の hottest area 近傍

### 制御部

- optional MCU は電力段から少し離し、`I2C` と NTC 読み出しを短く保つ
- debug header は board edge に逃がす

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

## Open Items

- exact board diameter
- exact coil footprint
- whether separate daughterboard for heater power stage is useful
- final stackup and board house design rules
