---
title: NTC Thermistor
type: concept
tags: [ntc, thermistor, sensor, temperature, cup-warmer]
sources: [tdk-ntc-thermistors-general-technical-information.md]
created: 2026-04-11
updated: 2026-04-11
---

`NTC` は `Negative Temperature Coefficient` の略で、温度が上がるほど抵抗が下がるサーミスタである。基本定義は [TDK NTC Thermistors 要約](source-tdk-ntc-thermistors-general-technical-information.md) にある。

## 何に向くか

- 温度測定
- 温度補償
- 制御系への温度入力

`NTC` は抵抗値が連続的に変わるので、「今どれくらい熱いか」を読みたい用途に向く。逆に、異常時に強制的に電流を絞る保護素子としては主役ではない。

## 注意点

- 測定電流を流しすぎると自己発熱で誤差が出る
- どの温度を見たいかで実装位置が重要になる
- 温度制御に使う場合、しきい値判断は受け側 IC や MCU に依存する

## Cup Warmer での意味

Cup Warmer の文脈では、`NTC` は「天板が何度か」を見るためのセンサである。したがって PCB 上ではなく、アルミ天板の裏面に貼る設計が合理的になる。`15W` 級の受電・加熱設計では、`NTC` を受電停止や出力デレートの入力に結び付けられる構成が望ましい。

保護部品としての `PTC` とは役割が違うので、比較は [NTC vs PTC](ntc-vs-ptc.md) を参照。
