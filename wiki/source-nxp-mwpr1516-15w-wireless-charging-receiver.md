---
title: NXP MWPR1516 要約
type: source-summary
tags: [qi, 15w, receiver, nxp, fod, arm]
sources: [nxp-mwpr1516-15w-wireless-charging-receiver.md, nxp-mwpr1516-package-quality.md, nxp-wpr1516-datasheet.md]
created: 2026-04-11
updated: 2026-04-11
---

[NXP MWPR1516 原文](raw/nxp-mwpr1516-15w-wireless-charging-receiver.md) は、`MWPR1516` を `up to 15 watt charging power`、`Arm Cortex-M0+`、`Optimized FOD algorithm`、`I2C/UART` を備えた `Active` な受電 IC として示している。

さらに [Package / Quality](raw/nxp-mwpr1516-package-quality.md) では、`MWPR1516CFM` が `HUQFN32`、`MWPR1516CAL` が `WLCSP36` だと確認できる。これは `WLCSP` を避けたい条件にとって大きい。

[WPR1516 Datasheet Notes](raw/nxp-wpr1516-datasheet.md) からは、`15W` が `proper external transistors` 前提であること、`5V / 3A` LDO、`3.5-20V` rectifier input range、`QFN` / `WLCSP` の二系統パッケージが読み取れる。

一方で、公開資料の日付は古い。データシートは `2015-01` 相当、参照設計の User Guide は `2016-09-21`、ファクトシートは `2020-02-12` で、最近の `Qi 1.3/EPP` 文言より前の世代感がある。したがって、`15W` 候補としては強いが、規格世代の新しさでは慎重に扱うべき候補である。
