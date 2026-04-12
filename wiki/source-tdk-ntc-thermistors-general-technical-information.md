---
title: TDK NTC Thermistors 要約
type: source-summary
tags: [ntc, thermistor, sensor, temperature]
sources: [tdk-ntc-thermistors-general-technical-information.md]
created: 2026-04-11
updated: 2026-04-11
---

[TDK NTC Thermistors 原文](raw/tdk-ntc-thermistors-general-technical-information.md) は、`NTC` を温度上昇で抵抗が下がる温度感応抵抗として定義している。ポイントは、抵抗変化が大きく、しかも周囲温度変化と自己発熱の両方に応答する点にある。

この性質により、`NTC` は温度測定、温度補償、温度制御入力に向く。一方で、通電条件によって自己発熱も起こるため、測定系では「どれだけ電流を流すか」が精度に直結する。

Cup Warmer では、天板裏面に取り付けて接触面温度を推定する用途が自然で、[NTC Thermistor](ntc-thermistor.md) の主要ソースとして使える。
