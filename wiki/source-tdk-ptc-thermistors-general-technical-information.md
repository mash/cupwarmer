---
title: TDK PTC Thermistors 要約
type: source-summary
tags: [ptc, thermistor, protection, overtemperature]
sources: [tdk-ptc-thermistors-general-technical-information.md]
created: 2026-04-11
updated: 2026-04-11
---

[TDK PTC Thermistors 原文](raw/tdk-ptc-thermistors-general-technical-information.md) は、`PTC` を「ある温度を超えると抵抗が急増する部品」として説明している。温度依存特性の中心にはキュリー温度があり、この近傍から急激な抵抗上昇が起きる。

文書は、`PTC` をモーター保護、短絡保護、過電流保護、自己調温ヒーターなどに使えると整理している。つまり `PTC` は計測用というより、しきい値を境に振る舞いを変える保護・制御寄りの部品である。

Cup Warmer では、制御回路が取りこぼした異常をハード側で抑える発想に対応し、[PTC Thermistor](ptc-thermistor.md) の基礎ソースになる。
