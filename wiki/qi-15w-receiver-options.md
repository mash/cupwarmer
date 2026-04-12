---
title: Qi 15W Receiver Options
type: comparison
tags: [qi, epp, 15w, receiver, comparison, cup-warmer]
sources: [st-stwlc38jrm-15w-wireless-power-receiver.md, st-stwlc38jrm-data-brief-db5568.md, renesas-p9221-r-15w-wireless-power-receiver.md, infineon-wlc1115-15w-transmitter.md, st-steval-isb042v1-15w-rx-eval-board.md, st-steval-wlc38rx-receiver-board-press-release.md, renesas-p9415-r-evk-15w-rx-eval-board.md, nxp-mwpr1516-15w-wireless-charging-receiver.md, nxp-mwpr1516-package-quality.md, wpc-qi-v13-power-delivery.md, wpc-qi-certified-products.md]
created: 2026-04-11
updated: 2026-04-11
---

Cup Warmer の `15W EPP` 受電候補を、2026-04-11 時点の公開一次情報ベースで比べる。

## 結論

「IC 単体」で見ると、候補は [ST STWLC38JRM 要約](source-st-stwlc38jrm-15w-wireless-power-receiver.md)、`KTE7001`、[NXP MWPR1516 要約](source-nxp-mwpr1516-15w-wireless-charging-receiver.md) の 3 つが強い。

- 規格の新しさと現行感を重視するなら `STWLC38JRM`
- 外付けトランジスタを避けつつ `Qi v1.3 EPP` の統合度を取りたいなら `KTE7001`
- 実装性を重視するなら `MWPR1516CFM (HUQFN32)`

[Renesas P9221-R 要約](source-renesas-p9221-r-15w-wireless-power-receiver.md) は仕様面では近いが、`Obsolete` なので新規設計の本命にはしにくい。

ここで重要なのは、`MWPR1516` の公式ページは `15W`、`WPC/MPWG`、`FOD`、`Arm Cortex-M0+`、`I2C/UART` を明記している一方、最近の `EPP` 文言を前面には出していない点である。したがって「`15W` 候補としては有力だが、最新世代の `EPP` 整合は追加確認が必要」という扱いにする。

ただし、`WLCSP` を避けたいという条件を入れると結論は変わる。2026-04-11 時点で公開一次情報から見つかる `15W` 受電 IC は、実質 `WLCSP` 系が中心である。したがって、実装難度を下げる現実的な道は `IC 単体` ではなく `評価ボード / 参照設計` を起点にすることになる。

## 候補比較

| 候補 | 状態 | 強み | 弱み | Cup Warmer 向き |
|---|---|---|---|---|
| `MWPR1516CFM` | Active | `15W`、`HUQFN32`、`Arm Cortex-M0+`、`FOD`、`I2C/UART` | `15W` は外付けトランジスタ前提、BOM とレイアウト負荷が増える、公開資料が古い、最近の `EPP` 文言が薄い | 高い |
| `STWLC38JRM` | Active / volume production | `15W`、`4-12V` 可変出力、`I2C`、`FOD`、`RRAM`、firmware patching、過電流 / 過熱 / 過電圧保護 | `WLCSP` 実装難度、外部 MCU 連携前提が自然 | 高い |
| `KTE7001` | Active 相当 | `Qi v1.3 EPP`、`Single Chip Solution`、`FOD` 調整、内蔵 `MCU`、`NTC` 保護 | `WLCSP69-52` 実装難度、`13.5W/15W` の条件差が読み取りづらい、流通情報の厚みが薄い | 高い |
| `P9221-R` | Obsolete | `15W`、`9/12V` 出力、内蔵 Cortex-M0、`I2C` | 新規採用しにくい、継続性が弱い | 中 |

## WLCSP を避けたい場合

`WLCSP` を避ける前提では、次の並びになる。

| 候補 | 種別 | 状態 | 意味 |
|---|---|---|---|
| `MWPR1516CFM` | NXP 受電 IC | Active | `HUQFN32` があるため、非 `WLCSP` の本命候補 |
| `STEVAL-WLC38RX` | ST 評価ボード | 公式公開あり | `STWLC38` の直接実装を避けて `15W` 評価を始めやすい |
| `STEVAL-ISB042V1` | ST 評価ボード | Out of Production | 古いが `15W EPP` と `5W BPP` の参照設計として有用 |
| `P9415-R-EVK` | Renesas 評価ボード | Obsolete | 学習素材としては有用だが新規採用には弱い |

ここでのポイントは、`MWPR1516CFM` によって「非 `WLCSP` の現行 `15W` 受電 IC」候補が 1 つ見つかったことにある。したがって `WLCSP` を避けるなら、第一候補は `MWPR1516CFM`、第二候補は評価ボード起点という並びになる。

## 外部 MCU は必要か

受電 IC の中には内部コアや NVM を持つものがあるので、理屈の上では外部 `MCU` なしでも受電自体は成立しうる。  
このプロジェクトでも、初版は `STWLC38JRM` の stand-alone 動作、固定 `VOUT`、独立ハード遮断、service `I2C` で進める方針を取れる。

ただし Cup Warmer では、負荷がバッテリーではなくヒーターである点が決定的に違う。  
そのため、外部 `MCU` を置かない場合は要求を絞る必要がある。

弱くなる点:

- 出力デレート
- カップなし時の停止
- 温度上昇速度による異常判定
- センサ異常時のフェイルセーフ

したがって、初版の固定加熱構成なら外部 `MCU` は不要だが、製品固有の温調ロジックまで入れるなら別途再検討が必要である。

## 送電側の考え方

[Infineon WLC1115 要約](source-infineon-wlc1115-15w-transmitter.md) のような現行送電側は `EPP` と `BPP` を併せ持つ。これは、評価用パッドを `EPP 15W` 中心に選びつつ、必要なら `5W BPP` デグレードも観察できることを意味する。

Cup Warmer の評価方針としては次が妥当である。

1. `EPP 15W` パッドで本命評価
2. `BPP 5W` パッドで縮退動作確認
3. 金属カップ、位置ずれ、天板材で `FOD` 条件を確認

## 実装上の示唆

- `WLCSP` を避けるなら `MWPR1516CFM` が第一候補
- ただし `MWPR1516CFM` は `15W` を外付けトランジスタ前提で実現するので、BOM は増え、完全ワンチップでは済まない
- 外付けトランジスタ前提の不利は、部品点数だけでなく、大電流経路のレイアウト、外付け素子の発熱管理、デバッグ対象の増加にも出る
- 規格世代の新しさを優先するなら `STWLC38JRM` は依然強い。2025年6月の data brief でも `15W`、`programmable output`、`FOD`、`RRAM`、firmware patching、過電流 / 過熱 / 過電圧保護が確認できる
- ただし `WLCSP40` 実装難度は高い
- `KTE7001` は、`Qi v1.3 EPP`、`Single Chip Solution`、`NTC` 保護、`FOD` 調整の点で、当初見積もりより強い候補である
- 一方で `WLCSP69-52` の実装難度は高く、`13.5W/15W` は条件差をさらに読み解く必要があるため、現時点では `STWLC38JRM` と並ぶか一段下の候補とみなす
- `WLCSP` 実装が厳しければ、[ST STEVAL-WLC38RX 要約](source-st-steval-wlc38rx-receiver-board-press-release.md) のような評価ボード起点で進める方が安全である。`USB-to-I2C bridge` と `STSW-WPSTUDIO` があるため、熱評価だけでなく初期 bring-up も楽になる
- 受電候補選定と並行して、天板材とヒーター構成を `FOD` 前提で見直す必要がある

## 未解決事項

- `MWPR1516` の `15W` 動作条件を、参照設計 User Guide レベルでもう一段確認したい
- `STWLC38JRM` の実際の `EPP` 実装自由度を、データブリーフ / 評価資料レベルでもう一段確認したい
- `KTE7001` の `13.5W/15W` の条件差と、`Single Chip` の実動作条件を正式データシートでさらに詰めたい
- `15W` 級で量産継続中の「受電モジュール」があるかは追加調査余地がある
