---
title: AO3400 MOSFET 要約
type: source-summary
tags: [mosfet, n-channel, load-switch, sot-23, ao3400]
sources: [ao3400-mosfet-datasheet-hottech.md, ao3400-mosfet-datasheet-hottech.pdf]
created: 2026-04-29
updated: 2026-04-29
---

[AO3400 原文](raw/ao3400-mosfet-datasheet-hottech.md) は Shenzhen Hottech 版のセカンドソース データシート。`AO3400` は元々 Alpha & Omega Semiconductor (AOS) の N-channel MOSFET 品番で、SOT-23 の汎用ロジックレベル MOSFET として広く流通している。

## 主要パラメータ

- 構造: N-channel エンハンスメント MOSFET
- パッケージ: `SOT-23`
- VDS 最大: `30 V`
- VGS 最大: `±12 V`
- ID 連続: `5.8 A` (TA=25°C), `4.9 A` (TA=70°C)
- ID パルス: `30 A`
- RDS(ON): typ `18 mΩ` / max `28 mΩ` @ VGS=10V
- RDS(ON): typ `19 mΩ` / max `33 mΩ` @ VGS=4.5V — **ロジックレベルで十分低い**
- RDS(ON): typ `24 mΩ` / max `52 mΩ` @ VGS=2.5V
- VGS(th): `0.65–1.45 V` (typ 1.05 V) — **3.3V/5V ロジック直接駆動可能**
- Qg total: typ `6 nC` @ VGS=4.5V
- Ciss: `630 pF`
- RθJA: `125 °C/W` (SOT-23 単体)
- PD: `1.40 W` (TA=25°C)

## 位置づけ

- ロジックレベル N-MOSFET の最も普及した汎用品の一つ。MCU の GPIO（3.3V）から直接駆動でき、RDS(ON) が低く、SOT-23 で安価。
- ボディダイオードは普通 (VSD~0.7V, trr~8.5ns)。逆電圧保護用途には別途 Schottky を入れる前提で考える。
- VDS=30V なので、5V/12V 系のローサイドスイッチや PWM 用途に適合。Cup Warmer のヒーター制御や `LED` ドライブ、補助回路のロードスイッチに使える候補。

## Cup Warmer 文脈での含意

- ヒーター（数 W〜十数 W）のローサイドスイッチには、電流次第で AO3400 (5.8A) 単体で足りる場合とそうでない場合がある。`PD=1.4W @ TA=25°C` と `RθJA=125°C/W` から、SOT-23 単体での連続電力は限定的なので、本格的なヒーター駆動は専用パワーパッケージ（DFN/PowerPAK 等）の方が安心。
- 補助系（FAN、`LED`、信号スイッチング、PWM 制御の小信号段）の load switch やレベル変換用途には十分な余裕がある。
- セカンドソースが多数あり供給性は良好だが、Hottech 版データシートのみを正としない方が良い — 設計値は AOS 公式版とクロスチェックする。
