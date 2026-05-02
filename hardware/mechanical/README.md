# 初回メカ前提

## 積層案

```
[Cup]
[Cup contact layer]
[Top plate]
[Flexible heater]
[F1 thermostat + TH1 bonded to top plate underside]
[Insulation]
[PCB]
[Ferrite]
[RX coil]
[Bottom shell]
```

## 初回で固定すること

- コイル中心と筐体中心を一致させる
- `NTC_TOP` はトッププレート裏面へ直接接触
- `F1` は `KSD9700-70/5JSB/080C` を使い、トッププレート裏面へ密着固定する
- 電力基板 hottest area に `NTC_B`
- トッププレート材は初回比較候補として
  - aluminum
  - ceramic
- cup contact layer は、硬い金属板ではなく曲面追従できる絶縁 thermal interface を第一候補にする

## F1 / TH1 / heater 固定方針

`F1` は製品制御用センサではなく、ヒーター系の独立ハード遮断として扱う。熱結合が悪いと安全側に働かないため、v1 では PCB 上に置かず、外部 heater/F1 series assembly の一部としてトッププレート裏面へ固定する。

推奨する相対配置:

```text
top plate underside
  ├─ TH1: top surface representative point
  ├─ F1: heater hotspot寄り。ヒーターと同じ熱経路へ密着
  └─ flexible heater: F1 と TH1 の位置が組立ごとに再現できるよう基準を持たせる
```

固定方法の第一候補:

- トッププレート裏面に浅い保持ポケットまたは位置決め面を作る
- F1 と TH1 は電気絶縁を保ったまま、熱伝導性接着材または耐熱絶縁テープ + 機械的押さえで密着させる
- F1 リードは引張緩和を設け、リード線の動きで F1 本体が浮かないようにする
- heater/F1 harness は H1 の大型 solder pads / wire pads へ手はんだする

固定方法の合否:

- F1 本体がトッププレート裏面から浮かない
- リード線に軽い引張がかかっても F1 の接触圧が変わらない
- TH1、F1、heater の相対位置が再現できる
- F1 open 後、F1 本体、リード、接点周辺が許容温度内に残る
- 接着材、テープ、絶縁材が長時間 `70°C` 近傍で劣化しない

## Cup contact layer 評価

v1 の第一候補はアルミナ充填シリコーンパッド。目的はカップ底面の湾曲に追従し、接触熱抵抗を下げつつ、Qi コイル近傍に大きな金属を置かないこと。

比較候補:

| サンプル | 厚み目安 | 期待 | 主な確認 |
| --- | --- | --- | --- |
| アルミナ充填シリコーンパッド | 0.5-1.0mm | 絶縁、追従性、Qi 近傍で扱いやすい | 表面温度、カップへの熱流、清掃性 |
| 低硬度熱伝導シリコーンシート | 1.0-2.0mm | 湾曲底面への追従性 | 立ち上がり、局所ホットスポット |
| グラファイトシート + 薄い絶縁フィルム | 0.1-0.3mm + film | 面内熱拡散 | FOD、渦電流、絶縁余裕 |

金属板は初回標準にしない。比較する場合も、Qi / FOD / 渦電流発熱の別リスクとして扱う。

## Coil / ferrite / top stack 測定

PCB 着手前または初回組立時に、以下の積層条件を記録する。

- coil part number and measured L/Q/DCR
- ferrite part number, thickness, and whether it is coil-bonded
- coil-to-ferrite gap
- ferrite-to-PCB gap
- PCB-to-heater insulation thickness
- heater-to-top plate adhesive or pad thickness
- top plate material and thickness
- cup contact layer material and thickness

EPP 15W pad と BPP 5W pad で、位置ずれ、金属マグ、カップなしの停止境界を別々に記録する。

## Open Items

- 外径
- 厚み
- コイル直径
- フェライト寸法
- F1 固定方法の最終選定
- cup contact layer の具体品番
- thermal test の実測結果
