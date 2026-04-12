---
title: WPC Qi v1.3 Power Delivery 要約
type: source-summary
tags: [qi, wpc, bpp, epp, coil, ferrite]
sources: [wpc-qi-v13-power-delivery.md]
created: 2026-04-11
updated: 2026-04-11
---

[WPC Qi v1.3 Power Delivery 原文](raw/wpc-qi-v13-power-delivery.md) は、`Power Profile` と受電側構成を理解するための中核ソースである。`BPP` と `EPP` は単なる「ワット数の違い」ではなく、送電側と受電側の互換性レベルを規定するプロファイルである。

また、受電側は `Secondary Coil`、整流、通信変調、出力切り離し、制御部、シールドなどで構成されることが明文化されている。ここから、コイル裏面のフェライトや共振コンデンサが「付属品」ではなく必須構成要素だと分かる。

Cup Warmer への落とし込みは [Qi Wireless Power](qi-wireless-power.md) と [Foreign Object Detection](fod-foreign-object-detection.md) に反映した。
