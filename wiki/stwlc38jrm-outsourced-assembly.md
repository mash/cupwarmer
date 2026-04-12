---
title: STWLC38JRM Outsourced Assembly
type: analysis
tags: [stwlc38jrm, wlcsp, outsourced-assembly, xray, cup-warmer]
sources: [st-stwlc38jrm-15w-wireless-power-receiver.md, st-tn1200-flip-chip-recommendations.md, jlcpcb-wlcsp-assembly-capability.md, pcbway-smt-assembly-capabilities.md, sierra-bga-wlcsp-assembly.md]
created: 2026-04-11
updated: 2026-04-11
---

`STWLC38JRM` を採用しつつ、自前実装はせず外注アセンブリへ載せる前提で考える。

## 前提

[ST STWLC38JRM 要約](source-st-stwlc38jrm-15w-wireless-power-receiver.md) の通り、この IC は `WLCSP40`、`5 x 8 ball`、`0.4 mm pitch`、`2.12 x 3.32 x 0.56 mm` である。`15W` 受電器としては有力だが、個人レベルの手実装には向かない。

## ST 側から読めること

[ST TN1200 Flip-Chip 要約](source-st-tn1200-flip-chip-recommendations.md) では、ST の flip-chip は特別な追加工程なしで標準の SMD 実装へ載せられるとされる。`underfill` 必須でもない。

ただし、これは「誰でも簡単にできる」という意味ではない。`0.4 mm` ピッチ、hidden joints、位置精度、検査の問題があるため、外注先は次を満たすべきである。

- `WLCSP/CSP` を扱う
- `X-ray` を使う
- `DFM` を見てくれる
- 必要なら専用 `fixture` を使う

## PCB 設計で先に固定すべきこと

### 確定情報

- パッケージは `WLCSP40`
- ボール配列は `5 x 8`
- ピッチは `0.4 mm`
- 外形は `2.12 x 3.32 x 0.56 mm`
- `15W` 受電、`4-12V` 可変出力、`FOD` 電流検出、`I2C` を持つ
- ST は EDA シンボル、フットプリント、3D モデルを提供している
- ST の一般推奨では `underfill` は必須ではない

### 初回基板で守る方針

- フットプリントは自作せず、まず ST 提供の EDA モデルを起点にする
- `X-ray inspection` を前提にし、目視前提の検査計画は組まない
- 手ハンダ前提のリワークを期待しない
- 発注前に、実装業者に pad 設計、mask 設計、`via-in-pad` 方針を確認する

### まだ未確定の点

- `via-in-pad` が必須か、dog-bone breakout で許容されるか
- pad を `NSMD` / `SMD` のどちらに寄せるべきか
- 推奨 stencil 厚みと aperture reduction
- 埋めビアや樹脂埋めが必要か

これらは、package drawing または実装業者の DFM 返答で確定する。

## 外注先の見方

### 価格優先

[JLCPCB WLCSP 実装要約](source-jlcpcb-wlcsp-assembly-capability.md) は、JLCPCB が `WLCSP` を SMT 対象として扱い、`fixture` と `X-ray` を要求していることを示す。安価な試作候補として現実的。

### 能力バランス

[PCBWay SMT Capability 要約](source-pcbway-smt-assembly-capabilities.md) は、`uBGA`、`0.2 mm pitch`、`X-ray`、`Via-in-Pad` を持つことを示す。`STWLC38JRM` の明示はないが、能力面ではかなり近い。

### 確実性優先

[Sierra WLCSP 実装要約](source-sierra-bga-wlcsp-assembly.md) は、`CSP / WLCSP` を明示し、`X-ray`、`AOI`、`ICT`、`Functional Testing`、`DFM review` を組み合わせるとしている。価格より歩留まりと支援を優先する場合の本命候補。

## 実務上の推奨

初回は次の順で考えるのがよい。

1. `STWLC38JRM` を前提に PCB を設計
2. 発注前に `0.4 mm WLCSP40`、`X-ray`、`fixture`、`via-in-pad` 可否を業者へ確認
3. 初回試作は少量でよいので、熱と `FOD` の成立性確認を優先

## 業者へ確認すべき項目

- `0.4 mm pitch WLCSP40` の実装可否
- `X-ray inspection` が標準か追加か
- `via-in-pad` と埋めビアが必要か
- 部品持ち込み対応
- リワーク可否
- 試作ロットの最小数量

## 現時点の判断

- `STWLC38JRM` 採用は妥当
- 自前実装より外注前提の方が自然
- `安価に試すなら JLCPCB`
- `中庸なら PCBWay`
- `確実性なら Sierra`
