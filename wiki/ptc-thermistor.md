---
title: PTC Thermistor
type: concept
tags: [ptc, pptc, thermistor, protection, fuse, cup-warmer]
sources: [tdk-ptc-thermistors-general-technical-information.md, littelfuse-polyswitch-resettable-pptc-devices.md]
created: 2026-04-11
updated: 2026-04-11
---

`PTC` は `Positive Temperature Coefficient` の略で、温度上昇に伴って抵抗が上がる系統の部品である。ただし実務では、同じ `PTC` でも用途の違う二系統を分けて考えた方がよい。

## 2つの文脈

### セラミック PTC サーミスタ

[TDK PTC Thermistors 要約](source-tdk-ptc-thermistors-general-technical-information.md) の文脈で、ある温度を超えると抵抗が急増する温度依存部品。温度スイッチ、モーター保護、自己調温ヒーターなどに使われる。

### ポリマー PPTC リセッタブルヒューズ

[Littelfuse PolySwitch PPTC 要約](source-littelfuse-polyswitch-resettable-pptc-devices.md) の文脈で、過電流や自己発熱で高抵抗化し、冷えると自動復帰する保護部品。部品表の `PTC ヒューズ` は通常こちらに近い。

## 何に向くか

- 過電流保護
- 過温時の電流制限
- 異常時の独立したハード保護

## Cup Warmer での意味

Cup Warmer の設計では、`PTC` は温度を精密に測る役ではなく、異常加熱時にヒーター電流を抑える安全部品として使うのが筋である。つまり `NTC` が「監視」、`PTC/PPTC` が「最後の保護」という役割分担になる。

`NTC` との違いは [NTC vs PTC](ntc-vs-ptc.md) に整理した。
