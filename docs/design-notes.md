# 設計ノート

## 現在の前提

- 受電 IC は `STWLC38JRM`
- 目標は `15W` 級 Qi cup warmer
- `WLCSP40` 実装は外注前提
- 初回は KiCad バイナリより先に、テキストで設計判断を固定する

## 現時点の主要判断

### 1. 受電 IC

`STWLC38JRM` を採用する。理由は、現行 `15W` 候補としての妥当性と、`4-12V` 可変出力、`I2C`、`FOD`、熱保護を持つ点。

### 2. 電圧方針

初回は `12V` 出力を第一候補にする。  
理由は `15W` を低電流で扱えるためで、ヒーター、MOSFET、配線損失の面で有利。

### 3. ヒーター方針

初回ヒーター目標:

- `12V`
- `10Ω` 前後
- `14.4W` 前後

最終値は熱試験で再調整する。

### 4. 制御方針

初版では外部 `MCU` は載せない。  
`STWLC38JRM` の autonomous 動作、`I2C` service header、独立ハード保護で成立させる。

- 初版は固定 `VOUT_12V` 前提
- ヒーター段の gate 制御源は `TBD`
- 製品固有の温調ロジックは初版のスコープ外
- `ENB` は未使用時 `GND` 固定を基本にする
- `NTC` は専用 `RX_NTC` として露出し、未使用時は `VAA` へ `10k` pull-up とする
- `INTB` は optional な bring-up / service 観測線として扱う
- `IEXT` は `RCL + TVS` の clamp path を前提にする

### 5. 保護方針

- `NTC_A`: top plate
- `NTC_B`: power board hotspot
- `F1`: independent hardware cutoff
- `FOD`: Qi 側の停止系として扱う

## 初回 PCB の考え方

- `4-layer`
- `X-ray` 前提
- `via-in-pad` などは設計前に外注 DFM で確定
- top plate と coil の距離は最小化しつつ、金属干渉は後で実測する

## Open Items

- ST 推奨の完全な最小回路
- exact coil / ferrite part
- heater final resistance and footprint
- heater gate drive source
- top plate material
- hard cutoff implementation choice
