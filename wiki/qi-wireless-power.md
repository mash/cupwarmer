---
title: Qi Wireless Power
type: concept
tags: [qi, wpc, wireless-power, bpp, epp, fod, cup-warmer]
sources: [wpc-qi-wireless-charging.md, wpc-qi-specification.md, wpc-qi-v13-power-delivery.md, wpc-qi-certified-products.md, infineon-wlc1115-15w-transmitter.md, nxp-mwpr1516-15w-wireless-charging-receiver.md, wpc-qi2-magnetic-alignment.md]
created: 2026-04-11
updated: 2026-04-11
---

`Qi` は `Wireless Power Consortium` が策定するワイヤレス給電標準で、送電側 (`PTx` / `TX`) と受電側 (`PRx` / `RX`) が相互運用できることを重視する。一般説明は [WPC Qi Wireless Charging 要約](source-wpc-qi-wireless-charging.md) にある。

## 何が標準化されているか

`Qi` は「コイルで電力を飛ばす」という概念だけでなく、少なくとも次を含む。

- 送受電の互換性
- 通信手順
- 電力プロファイル
- 安全機能
- 認証と相互運用試験

したがって、単に無線給電できるだけでは `Qi` とは言い切れない。認証の意味は [WPC Qi Certified Products 要約](source-wpc-qi-certified-products.md) を参照。

## 版の見方

WPC の公開情報では、`Qi v1.0` は 2010 年、`v1.2` は 2015 年、`v1.3` は 2021 年、`v2.0` は 2023 年に登場している。2026-04-11 時点での最新仕様は `v2.3` である。これは [WPC Qi Specification 要約](source-wpc-qi-specification.md) に基づく。

## 受電側の基本構成

WPC の `Power Delivery v1.3` 文書では、受電側は `Secondary Coil`、整流回路、通信変調器、出力切り離し、制御部などを含む構成として説明される。さらに、デュアル共振回路とシールドも受電設計の重要要素である。

このため、以下は本質部品である。

- 受電コイル
- 共振コンデンサ
- 整流・制御 IC
- シールド材

Cup Warmer のフェライトシートや共振ネットワークは、この構成の延長にある。

## BPP と EPP

WPC 文書では、`BPP` と `EPP` は `Power Profile` として定義される。実務上は次の理解で足りる。

- `BPP`: ベースライン互換の低出力系
- `EPP`: 拡張互換の高出力系

同じ文書では `EPP5` という `5W` 制限の拡張プロファイルも記載されているため、出力ワット数だけで全体を語るのは不十分である。

## FOD

`FOD` は `Foreign Object Detection` の略で、送受電コイル間に金属などの異物があるときの損失や発熱を抑える仕組みである。現行の送電側では、たとえば [Infineon WLC1115 要約](source-infineon-wlc1115-15w-transmitter.md) にあるように `Q-factor`、共振周波数、電力損失など複数の指標が使われる。受電側でも [NXP MWPR1516 要約](source-nxp-mwpr1516-15w-wireless-charging-receiver.md) のように `Optimized FOD algorithm` を備えるものがある。

したがって `FOD` は送電側単独の雑な判定ではなく、送受電系全体の損失挙動を監視する安全機能として理解すべきである。

詳細は [Foreign Object Detection](fod-foreign-object-detection.md) を参照。

## Cup Warmer との関係

Cup Warmer では、`Qi` はバッテリー充電ではなく、ヒーターへ電力を渡すための無線電源インターフェースとして使う。現在の検討は `15W` 級受電を主軸にしているので、受電候補の整理は [Qi 15W Receiver Options](qi-15w-receiver-options.md) を参照。
