---
title: ST STWLC38JRM 要約
type: source-summary
tags: [qi, epp, 15w, receiver, st]
sources: [st-stwlc38jrm-15w-wireless-power-receiver.md, st-stwlc38jrm-data-brief-db5568.md]
created: 2026-04-11
updated: 2026-04-11
---

[ST STWLC38JRM 原文](raw/st-stwlc38jrm-15w-wireless-power-receiver.md) と [ST STWLC38JRM Data Brief DB5568](raw/st-stwlc38jrm-data-brief-db5568.md) は、`STWLC38JRM` を量産中の `15W` 受電 IC として示している。`4-12V` の可変出力、`32-bit 64 MHz Arm Cortex-M0+`、`I2C target interface`、`FOD` 用の電流検出に加え、`overcurrent`、`thermal protection`、`overvoltage clamping` も明記されている。

さらに data brief では、`embedded RRAM` による `I2C` 経由の customization と proprietary communication / charging protocols、`additional firmware patching` による柔軟性も示されている。Cup Warmer 文脈では、単なるスマホ受電器よりも「制御余地があり、まだ新規採用できる `15W` 受電候補」という点が重要である。

比較は [Qi 15W Receiver Options](qi-15w-receiver-options.md) を参照。
