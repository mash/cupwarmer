---
source: AO3400.pdf (SHENZHEN HOTTECH ELECTRONICS CO.,LTD)
extracted: 2026-04-29
---

# AO3400 — Low Voltage MOSFET (N-Channel)

Hottech 版データシート（PDF: `ao3400-mosfet-datasheet-hottech.pdf`）からのテキスト抽出。`AO3400` は元々 Alpha & Omega Semiconductor (AOS) の品番だが、本データシートは Shenzhen Hottech 製のセカンドソース版。

## 概要

- N-channel MOSFET, 低電圧, 低 RDS(ON)
- パッケージ: SOT-23
- 用途: PWM, ロードスイッチ
- メーカー連絡先: hkt@heketai.com

## 絶対最大定格 (TA = 25°C)

| Parameter | Symbol | Value | Unit |
|---|---|---|---|
| Drain-source voltage | VDS | 30 | V |
| Gate-source voltage | VGS | ±12 | V |
| Continuous drain current (TA=25°C) | ID | 5.8 | A |
| Continuous drain current (TA=70°C) | ID | 4.9 | A |
| Pulsed drain current | IDM | 30 | A |
| Power dissipation (TA=25°C) | PD | 1.40 | W |
| Power dissipation (TA=70°C) | PD | 0.9 | W |
| Thermal resistance Junction-to-ambient | RθJA | 125 | °C/W |
| Junction temperature | TJ | 150 | °C |
| Storage temperature | TSTG | -55 ~ +150 | °C |

## 主な電気的特性 (TA = 25°C)

| Parameter | Symbol | Min | Typ | Max | Unit | Conditions |
|---|---|---|---|---|---|---|
| Drain-Source breakdown voltage | V(BR)DSS | 30 | | | V | VGS=0V, ID=250µA |
| Zero gate voltage drain current | IDSS | | | 1 | µA | VDS=30V, VGS=0V |
| Gate-body leakage current | IGSS | | | ±100 | nA | VDS=0V, VGS=±12V |
| Gate-threshold voltage | VGS(th) | 0.65 | 1.05 | 1.45 | V | VDS=VGS, ID=250µA |
| Drain-source on-resistance | RDS(ON) | | 18 | 28 | mΩ | VGS=10V, ID=5.8A |
| | | | 19 | 33 | mΩ | VGS=4.5V, ID=5A |
| | | | 24 | 52 | mΩ | VGS=2.5V, ID=4A |
| On-State Drain Current | ID(ON) | 30 | | | A | VDS=5V, VGS=4.5V |
| Forward transconductance | gFS | | 33 | | S | VDS=5V, ID=5.8A |
| Input capacitance | Ciss | | 630 | | pF | VDS=15V, VGS=0V, f=1MHz |
| Output capacitance | Coss | | 75 | | pF | |
| Reverse transfer capacitance | Crss | | 50 | | pF | |
| Turn-on delay time | td(on) | | 3 | | ns | VDS=15V, VGS=10V, RGEN=3Ω, RL=2.6Ω |
| Turn-on rise time | tr | | 2.5 | | ns | |
| Turn-off delay time | td(off) | | 25 | | ns | |
| Turn-off fall time | tf | | 4 | | ns | |
| Total gate charge | Qg | | 6 | 7 | nC | VDS=15V, VGS=4.5V, ID=5.8A |
| Gate-source charge | Qgs | | 1.3 | | nC | |
| Gate-drain charge | Qgd | | 1.8 | | nC | |
| Diode forward voltage | VSD | | 0.7 | 1 | V | IS=1A, VGS=0V |
| Diode forward current | IS | | | 2 | A | |
| Body diode reverse recovery time | trr | | 8.5 | | ns | IF=5.8A, dI/dt=100A/µs |
| Body diode reverse recovery charge | Qrr | | 2.6 | | nC | |

* Pulse test: pulse width ≤300µs, duty cycle ≤0.5%.

## パッケージ (SOT-23)

主要寸法 (mm):
- 全高 A: 0.900–1.150
- ボディ D: 2.800–3.000
- E: 1.200–1.400, E1: 2.250–2.550
- ピッチ e: 0.950 typ
- リード幅 b: 0.300–0.500

テープ&リール: 7" reel, W=8.00mm, P=4.00mm。

## 抽出元

PDF 全 6 ページ。Page 1: 仕様、Page 2-3: 特性グラフ（On-Region、Transfer、RDS(ON)、Body diode、Cap、Gate charge、SOA、過渡熱抵抗）、Page 4: 試験回路、Page 5: パッケージ寸法、Page 6: テープ&リール。
