---
title: Wiki Log
type: overview
tags: [log]
sources: []
created: 2026-04-11
updated: 2026-04-11
---

## [2026-04-11] Ingest | NTC と PTC の基礎整理
`TDK`、`Littelfuse`、`TI` の公開資料をもとに `wiki/raw/` へソース記録を追加し、`NTC Thermistor`、`PTC Thermistor`、`NTC vs PTC`、各 `source-summary`、`index` を作成した。

## [2026-04-11] Ingest | Qi の基礎整理
`WPC` と `TI` の公開資料をもとに `Qi` の一般概念、`BPP/EPP`、`FOD`、認証の意味、Cup Warmer への適用を `wiki/raw/`、各 `source-summary`、`Qi Wireless Power`、`Qi for Cup Warmer` として追加し、`index` を更新した。

## [2026-04-11] Ingest | Qi 15W 受電候補
`ST`、`Renesas`、`Infineon` の公開資料をもとに `15W EPP` 受電候補の比較を追加した。現時点の第一候補を `STWLC38JRM`、参考候補を obsolete な `P9221-R` として整理し、送電側エコシステム補助情報も追加した。

## [2026-04-11] Ingest | Qi 15W 非 WLCSP 候補
`WLCSP` を避けたい前提で、`ST` と `Renesas` の受電評価ボード・参照設計を追加した。結論として、IC 単体より評価ボード起点の方が現実的という整理に更新した。

## [2026-04-11] Ingest | NXP MWPR1516 候補追加
`NXP MWPR1516` を追加調査した。`15W`、`Arm Cortex-M0+`、`FOD`、`I2C/UART` に加えて `HUQFN32` 版 `MWPR1516CFM` があるため、`WLCSP` を避けたい条件では第一候補へ更新した。一方で、公開資料の日付が古い点はリスクとして記録した。

データシート `WPR1516.pdf` を追加で読んだ結果、`15W` は外付けトランジスタ前提であること、`5V / 3A` LDO、`3.5-20V` の整流入力範囲を確認した。

## [2026-04-11] Ingest | FOD の独立ページ追加
既存の `WPC` / `TI` ソースを再整理し、`Foreign Object Detection` の概念ページを追加した。あわせて `Qi Wireless Power` と `Qi for Cup Warmer` から相互リンクし、`index` を更新した。

## [2026-04-11] Ingest | FOD 非金属カップ前提の追補
`FOD` ページに、金属カップ非対応前提で残る課題、評価表、磁石による位置ずれ対策の整理を追記した。あわせて `Qi2` の磁気位置合わせに関する `WPC` ソース記録と要約を追加し、`index` を更新した。

## [2026-04-11] Maintenance | 5W 系 wiki ページ削除
`BQ51013B` / `BQ500511` を中心にした `5W` 系の wiki ページと raw/source-summary を削除した。あわせて `Qi Wireless Power`、`Foreign Object Detection`、`NTC` 関連ページの参照を `15W` と一般概念中心へ整理し、`index` を更新した。

## [2026-04-11] Ingest | STWLC38JRM PDF 追補
`/Users/mash/Downloads/stwlc38jrm.pdf` を `wiki/raw/assets/stwlc38jrm.pdf` として取り込み、2025年6月の data brief ノートを追加した。既存の `STWLC38JRM` 要約と `Qi 15W Receiver Options` に、`RRAM`、firmware patching、過電流 / 過熱 / 過電圧保護の情報を反映した。

## [2026-04-11] Ingest | STEVAL-WLC38RX Mouser 追補
`STEVAL-WLC38RX` について、Mouser 商品ページと掲載 data brief から `Qi 1.3`、`5W BPP` / `15W EPP`、`USB-to-I2C bridge`、`STSW-WPSTUDIO`、`ARC`、`FOD` 用の電圧 / 電流測定、on-chip thermal management の情報を追記した。評価開始手段としての価値を source-summary と比較ページへ反映した。

## [2026-04-11] Ingest | STWLC38JRM 外注実装前提
`STWLC38JRM` を採用し、`WLCSP40` 実装は外注する前提で整理した。`ST` の flip-chip 一般推奨、`JLCPCB`、`PCBWay`、`Sierra` の公式能力情報をもとに、`X-ray`、`fixture`、`DFM`、`via-in-pad` を確認項目としてまとめた。

## [2026-04-11] Docs | STWLC38JRM レイアウト制約と外注確認テンプレート
`STWLC38JRM` の初回基板向けレイアウト制約メモと、外注先へ送る日本語の確認テンプレートを `docs/` に追加した。あわせて外注実装分析ページへ、設計時に先に固定すべき点と未確定事項を追記した。

## [2026-04-11] Ingest | AI支援EDA比較
`KiCad`、`Flux`、`CELUS`、`Altium` の公式情報をもとに、AI 支援と実設計能力を比較するページを追加した。結論として、AI 内蔵の強さは `Flux`、今回の Cup Warmer 案に対する実用バランスは `KiCad` が最も妥当という整理にした。

## [2026-04-29] Ingest | AO3400 MOSFET データシート
Shenzhen Hottech 版 `AO3400` データシート (PDF) を `wiki/raw/` に追加し、`source-ao3400-mosfet-datasheet-hottech` として要約ページを作成した。`SOT-23` ロジックレベル N-MOSFET (`30V`/`5.8A`/`RDS(ON)=28mΩ@VGS=10V`) で、Cup Warmer の補助系ロードスイッチや PWM 制御に使える汎用品としての位置づけを整理した。
