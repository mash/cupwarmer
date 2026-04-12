# NXP WPR1516 Datasheet Notes

- Source: [WPR1516 Data Sheet PDF](assets/WPR1516.pdf)
- Accessed: 2026-04-11

## Notes

- データシート表紙では `24 MHz Cortex-M0+ Based Microcontroller` と説明されている。
- `Up to 15 W with proper external transistors` とあり、`15W` 達成には外付けトランジスタが前提。
- `QFN package for industrial application and WLCSP package for space constrained consumer applications` とある。
- `LDO provides 5 V and 3 A output to down system`。
- `Input from rectifier voltage range: 3.5 to 20 V`。
- `One UART module`、`One I2C module`。
- 部品型番として `MWPR1516CFM(R)` と `MWPR1516CALR` を記載。
- データシートは `Freescale` 名義で、`Document Number: WPR1516`、`Rev 2, 1/2015`。

## Relevance

- `HUQFN32` 版があるため、`WLCSP` を避けたい条件に合う。
- 一方で `15W` が外付けトランジスタ前提という点は、`STWLC38JRM` より実装負荷が増える可能性がある。
