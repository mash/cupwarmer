---
title: AI-Assisted Electronics Design Tools
type: comparison
tags: [ai, eda, kicad, flux, celus, altium, comparison]
sources: [kicad-pcb-design-features.md, kicad-plugin-and-rules.md, flux-ai-pcb-design.md, celus-ai-electronics-design.md, altium-designer-and-ai.md]
created: 2026-04-11
updated: 2026-04-11
---

AI 支援のある電子設計ツールを、「AI が強いか」と「今回の Cup Warmer 案に向くか」を分けて比べる。

## 結論

`AI支援が一番強い` という意味なら、[Flux AI PCB 要約](source-flux-ai-pcb-design.md) が最も近い。  
ただし `WLCSP40`、`15W Qi`、`FOD`、外注 DFM のような今回の設計では、最終的に必要なのは高密度 PCB とルール管理である。

その条件を踏まえると、`この案件で一番バランスがよい` のは `KiCad` である。理由は次の通り。

- 無料で始められる
- PCB 機能は十分強い
- `custom design rules` と plugin 拡張がある
- git と相性がよい
- 外部 AI を併用しやすい

ただし、「お金は気にしない、WLCSP や高密度実装をもっと楽にしたい」という条件なら、`Altium` の方が純粋な EDA としては強い。

## 比較表

| ツール | AI の強さ | PCB / 高密度実装 | この案件への適合 | コメント |
|---|---|---|---|---|
| `KiCad` | 低い。AI は外付け前提 | 高い | 高い | 今回の default choice |
| `Flux` | 高い | 中。AI の layout 理解は limited | 中 | 回路図支援は強いが最後の詰めは弱い |
| `CELUS` | 中〜高。前工程自動化 | 低〜中 | 低〜中 | 要件整理と回路初期案向け |
| `Altium Designer` | 中。AI より ML / assistive 機能寄り | 非常に高い | 高い | 予算があれば最強寄り |

## なぜ KiCad を推すか

[KiCad PCB 機能要約](source-kicad-pcb-design-features.md) の通り、KiCad は interactive router、DRC、3D、custom rules、plugin 拡張を備える。今回の `STWLC38JRM` 案で重要なのは、`WLCSP40`、`4-layer`、`via-in-pad`、外注 DFM を丁寧に管理できることなので、AI 自動生成の巧さよりルール管理が効く。

また、KiCad は open source で、テキスト資産と version control と相性がよい。今回のように設計メモ、外注問い合わせ、BOM、`wiki` を並行で育てる流れと相性がよい。

## Flux を使うならどう使うか

[Flux AI PCB 要約](source-flux-ai-pcb-design.md) の通り、Flux は AI が回路図、部品選定、datasheet parsing を直接支援する。したがって、Flux を使うなら「初期探索」と「部品比較」に寄せるのが自然で、最終 PCB を全面的に任せるものではない。

## CELUS を使うならどう使うか

[CELUS AI 設計要約](source-celus-ai-electronics-design.md) の通り、CELUS は schematic generation と component search の自動化が主眼である。つまり、要件定義から回路の叩き台を速く出す用途には向くが、今回の最終設計ツールとしては弱い。

## Altium を使うべき条件

[Altium Designer と AI 要約](source-altium-designer-and-ai.md) の通り、Altium は HDI、constraint management、dense layout に強い。したがって次の条件なら Altium の方がよい。

- `WLCSP` を今後も繰り返し使う
- 高密度・高層板案件が増える
- 商用ライブラリと製造連携を重視する
- ライセンス費用を許容できる

## この案件に対する最終判断

- `コストと実用性のバランス`: `KiCad`
- `AI による回路探索支援`: `Flux` または `CELUS` を補助利用
- `純粋な強さ`: 予算があれば `Altium`

したがって、質問に対する短い答えは次の通り。

`AI内蔵` という意味では KiCad は一番ではない。  
しかし `Cup Warmer` のような個人開発の実設計ツールとしては、今のところ KiCad が最も妥当である。
