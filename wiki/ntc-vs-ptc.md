---
title: NTC vs PTC
type: comparison
tags: [ntc, ptc, pptc, thermistor, comparison, cup-warmer]
sources: [tdk-ntc-thermistors-general-technical-information.md, tdk-ptc-thermistors-general-technical-information.md, littelfuse-polyswitch-resettable-pptc-devices.md]
created: 2026-04-11
updated: 2026-04-11
---

`NTC` と `PTC` はどちらも温度で抵抗が変わる部品だが、設計上の役割はほぼ逆である。

## 一番短い違い

- `NTC`: 温度が上がると抵抗が下がる。測定と制御入力に向く
- `PTC`: 温度が上がると抵抗が上がる。保護と電流制限に向く

## 実務上の違い

| 観点 | NTC | PTC / PPTC |
|---|---|---|
| 主用途 | 温度監視 | 過電流・過温保護 |
| 反応 | 連続的に抵抗が下がる | しきい値以降で抵抗が大きく上がる |
| 得意なこと | 「何度か」を知る | 「危険だから止める」を実現する |
| 制御依存 | 高い | 低い |
| Cup Warmer での位置づけ | 天板温度センサ | 異常時の独立保護 |

## Cup Warmer への適用

このプロジェクトでは、`NTC` をアルミ天板裏面に置いて接触面温度を監視し、`PTC` はヒーター直列や保護系に置いて制御不全や想定外の熱暴走時のバックストップにするのが自然である。

重要なのは、`NTC` と `PTC` は代替関係ではなく補完関係だという点である。`NTC` だけでは制御依存になり、`PTC` だけでは通常運転温度を細かく扱えない。

## 未確定事項

- 部品表の `PTC ヒューズ 90°C` は、セラミック `PTC` なのか `PPTC` なのかを部品選定段階で明確化する必要がある
- 実際の停止温度やデレート開始温度は、採用する受電・制御系と `NTC` 特性で決まるため、しきい値は回路確定後に別途定義が必要
