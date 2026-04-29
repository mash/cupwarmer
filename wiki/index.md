---
title: Wiki Index
type: overview
tags: [index]
sources: []
created: 2026-04-11
updated: 2026-04-11
---

# Index

## Analysis

- [STWLC38JRM Outsourced Assembly](stwlc38jrm-outsourced-assembly.md) - `STWLC38JRM` を外注実装前提で使うための整理。 `analysis`
- [STWLC38 Internal CPU and External MCU](stwlc38-internal-cpu-and-external-mcu.md) - `STWLC38` の内蔵 CPU 能力と、外部 `MCU` なし初版の考え方の整理。 `analysis`
- [Qi for Cup Warmer](qi-for-cup-warmer.md) - Cup Warmer 設計における `Qi` の制約と実装上の含意。 `analysis`

## Comparison
- [NTC vs PTC](ntc-vs-ptc.md) - Cup Warmer 文脈を含めた `NTC` と `PTC/PPTC` の役割比較。 `comparison`
- [AI-Assisted Electronics Design Tools](ai-assisted-electronics-design-tools.md) - AI支援EDAと KiCad の位置づけ比較。 `comparison`
- [Qi 15W Receiver Options](qi-15w-receiver-options.md) - `15W EPP` 受電候補の比較と推奨。 `comparison`

## Concepts

- [Foreign Object Detection](fod-foreign-object-detection.md) - `Qi` における異物発熱検出と Cup Warmer 設計への含意。 `concept`
- [NTC Thermistor](ntc-thermistor.md) - 温度測定向けサーミスタとしての `NTC` の整理。 `concept`
- [PTC Thermistor](ptc-thermistor.md) - セラミック `PTC` と `PPTC` の違いを含む保護部品整理。 `concept`
- [Qi Wireless Power](qi-wireless-power.md) - `Qi` 標準、プロファイル、認証、安全機能の基本整理。 `concept`

## Reference

- [KiCad Schematic File Format Spec](source-kicad-schematic-file-format-spec.md) - `.kicad_sch` の全トークン仕様と kiutils 1.4.8 カバレッジ分析。 `reference`

## Source Summaries

- [TDK NTC Thermistors 要約](source-tdk-ntc-thermistors-general-technical-information.md) - `NTC` の基本特性と用途の要約。 `source-summary`
- [TDK PTC Thermistors 要約](source-tdk-ptc-thermistors-general-technical-information.md) - `PTC` の温度特性と代表用途の要約。 `source-summary`
- [Littelfuse PolySwitch PPTC 要約](source-littelfuse-polyswitch-resettable-pptc-devices.md) - リセッタブル `PPTC` 保護素子の整理。 `source-summary`
- [WPC Qi Wireless Charging 要約](source-wpc-qi-wireless-charging.md) - `Qi` 標準と認証全体の概観。 `source-summary`
- [WPC Qi Specification 要約](source-wpc-qi-specification.md) - `Qi` 仕様バージョンの歴史整理。 `source-summary`
- [WPC Qi v1.3 Power Delivery 要約](source-wpc-qi-v13-power-delivery.md) - `BPP/EPP`、コイル、シールド構成の要約。 `source-summary`
- [WPC Qi2 Magnetic Alignment 要約](source-wpc-qi2-magnetic-alignment.md) - `Qi2` の磁気位置合わせが示す設計含意。 `source-summary`
- [WPC Qi Certified Products 要約](source-wpc-qi-certified-products.md) - `Qi Certified` 表記の意味整理。 `source-summary`
- [ST STWLC38JRM 要約](source-st-stwlc38jrm-15w-wireless-power-receiver.md) - 現行 `15W` 受電候補としての ST 製品整理。 `source-summary`
- [Renesas P9221-R 要約](source-renesas-p9221-r-15w-wireless-power-receiver.md) - `15W` 受電器だが obsolete な候補整理。 `source-summary`
- [Infineon WLC1115 要約](source-infineon-wlc1115-15w-transmitter.md) - 現行 `15W` 送電側の `EPP/BPP/FOD` 整理。 `source-summary`
- [NXP MWPR1516 要約](source-nxp-mwpr1516-15w-wireless-charging-receiver.md) - `HUQFN32` を持つ `15W` 受電候補の整理。 `source-summary`
- [ST STEVAL-ISB042V1 要約](source-st-steval-isb042v1-15w-rx-eval-board.md) - 旧 `15W EPP` 受電評価ボードの参照設計整理。 `source-summary`
- [ST STEVAL-WLC38RX 要約](source-st-steval-wlc38rx-receiver-board-press-release.md) - `STWLC38` ベース評価ボードの位置づけ整理。 `source-summary`
- [Renesas P9415-R-EVK 要約](source-renesas-p9415-r-evk-15w-rx-eval-board.md) - `15W` 受電評価ボードの参考資料整理。 `source-summary`
- [ST TN1200 Flip-Chip 要約](source-st-tn1200-flip-chip-recommendations.md) - ST の flip-chip 一般実装推奨整理。 `source-summary`
- [JLCPCB WLCSP 実装要約](source-jlcpcb-wlcsp-assembly-capability.md) - `WLCSP` 試作実装時の fixture / X-ray 条件整理。 `source-summary`
- [PCBWay SMT Capability 要約](source-pcbway-smt-assembly-capabilities.md) - `uBGA`、`0.2 mm pitch`、`X-ray`、`via-in-pad` 能力整理。 `source-summary`
- [Sierra WLCSP 実装要約](source-sierra-bga-wlcsp-assembly.md) - `WLCSP` 明示対応と検査フロー整理。 `source-summary`
- [KiCad PCB 機能要約](source-kicad-pcb-design-features.md) - KiCad の PCB / rules / plugin 基盤整理。 `source-summary`
- [Flux AI PCB 要約](source-flux-ai-pcb-design.md) - Flux の AI 支援範囲と layout 制限整理。 `source-summary`
- [CELUS AI 設計要約](source-celus-ai-electronics-design.md) - CELUS の前工程自動化の位置づけ整理。 `source-summary`
- [Altium Designer と AI 要約](source-altium-designer-and-ai.md) - Altium の強みと AI の位置づけ整理。 `source-summary`
- [AO3400 MOSFET 要約](source-ao3400-mosfet-datasheet-hottech.md) - SOT-23 ロジックレベル N-MOSFET (`30V`/`5.8A`/`28mΩ`) の整理。 `source-summary`
