# 初回メカ前提

## 積層案

```
[Cup]
[Cup contact layer]
[Internal heat spreader / support plate]
[Flexible heater]
[F1 thermostat bonded near heater hotspot]
[Insulation]
[PCB]
[Ferrite]
[RX coil]
[Bottom shell]
```

## 初回で固定すること

- コイル中心と筐体中心を一致させる
- `F1` は `KSD9700-70/5JSB/080C` を使い、internal heat spreader / support plate または heater stack へ密着固定する
- heater 内蔵 NTC を `H1` の4線ハーネスで受け、`RX_NTC` へ接続する
- カップに触れる面へ金属を露出させない
- 内部 heat spreader / support plate は、カップから完全に隠れる場合に限り thin aluminum を比較候補にする
- cup contact layer は、硬い金属板ではなく曲面追従できる絶縁 thermal interface を第一候補にする
- bottom shell は Qi 側に近いため非金属樹脂にする

## F1 / TH1 / heater 固定方針

`F1` は製品制御用センサではなく、ヒーター系の独立ハード遮断として扱う。熱結合が悪いと安全側に働かないため、v1 では PCB 上に置かず、外部 heater/F1 series assembly の一部として internal heat spreader / support plate または heater stack へ密着固定する。

heater 内蔵 NTC (`TH2`) も PCB 温度ではなく、coil / ferrite / spreader / heater stack の過熱を STWLC38 の `RX_NTC` OTP 入力へ伝える保護点として扱う。`H1` のピン割りは `1=H+`, `2=NTC/RX_NTC`, `3=NTC_GND`, `4=H-` とし、heater NTC は F1 と同じ熱経路の代表点または hotspot 近傍に再現性を持って固定する。

推奨する相対配置:

```text
heat spreader / heater stack underside
  ├─ heater NTC: flexible heater の代表温度点（heater側に実装）
  ├─ F1: heater hotspot寄り。ヒーターと同じ熱経路へ密着
  └─ flexible heater: F1 と heater NTC の位置が組立ごとに再現できるよう基準を持たせる
```

固定方法の第一候補:

- spreader / heater stack 側に浅い保持ポケットまたは位置決め面を作る
- F1 は電気絶縁を保ったまま、熱伝導性接着材または耐熱絶縁テープ + 機械的押さえで密着させる
- F1 リードは引張緩和を設け、リード線の動きで F1 本体が浮かないようにする
- heater/F1/NTC harness は H1 の4線大型 solder pads / wire pads へ手はんだする

固定方法の合否:

- F1 本体が spreader / heater stack から浮かない
- リード線に軽い引張がかかっても F1 の接触圧が変わらない
- heater NTC、F1、heater の相対位置が再現できる
- F1 open 後、F1 本体、リード、接点周辺が許容温度内に残る
- 接着材、テープ、絶縁材が長時間 `70°C` 近傍で劣化しない

## 筐体プロト方針

v1 enclosure は二分割の非金属樹脂筐体を第一候補にする。

OpenSCAD study model: `enclosure-proto.scad`

- bottom tray: 浅い凹型トレー。PCB、coil/ferrite clearance、断熱材、heater stack を保持する
- top retaining ring: cup contact layer を外周で保持し、内部 metal spreader のエッジを隠す
- bottom tray の Qi pad 側底面は薄くし、金属を入れない
- H1 heater pigtail は一箇所から半径方向へまっすぐ逃がし、PCB 外周を回り込ませない
- 滑り止めは底面外周の薄いシリコーンリングまたは足で行う
- コイル中心付近の金属ねじは避け、必要なら perimeter の樹脂スナップ、樹脂ボス、nylon M2 ねじを使う
- カップ底面は凹形状が多いため、cup contact layer の上面は浅い凸形状にする。top retaining ring は pad 上面より低くし、カップ側に凹形状を作らない
- 旧 PCB mounting holes `H3=(116,84)`, `H4=(116,116)`, `H5=(84,84)` は、board/enclosure center `(100,100)` 基準で `(16,-16)`, `(16,16)`, `(-16,-16)` にあり、`40x40mm` L1 coil envelope 内へ入っていたため KiCad から削除済み。PCB は bottom tray の perimeter ledge / rims で outer edge を支える
- PCB support ledge は `φ56mm` PCB の外周 `~2.2mm` だけを受け、中心の L1 / ferrite keepout を開ける。初期値は support outer OD `56.7mm`、inner OD `51.6mm`、thickness `0.3mm`

top retaining ring は v1 では残すが、cup contact surface より低い保持リングとして扱う。理由は、cup contact layer を接着主固定にせず機械保持すること、internal aluminum spreader のエッジを隠すこと、水滴が直接内部へ落ちる経路を減らすこと、熱/FOD 試験後に分解できること。将来、cup contact pad を別手段で確実に固定でき、金属エッジ露出と水滴経路を別構造で潰せる場合だけ削除候補にする。

L1 receiver coil は `Wuerth Elektronik 760308102207` を基準にする。外形は `40x40x1.2mm` の rounded-square Qi RX coil、visible corner radius は DS 図から `5-8mm` 程度として扱う。coil termination は 2 holes `φ1.2mm` / `5.0mm` pitch の solder-pad termination。datasheet は integrated ferrite shield を明記していないため、受領品で背面 ferrite / EMI shield の有無を確認し、`SHIELD1` を削除するか別体フェライトを併用するかは L/Q/DCR/FOD 実測で決める。

初期寸法目安:

| Feature | Initial value | Notes |
| --- | ---: | --- |
| Enclosure OD | 60.0mm max | design-notes の改定方針に合わせる |
| PCB / heater OD | 56.0mm max | 現行 heater Gerber と整合 |
| Internal aluminum spreader OD | 54-55mm | cup contact layer より小さくし、エッジを隠す |
| Cup contact silicone pad OD | 56-57mm | spreader を完全に覆う |
| Bottom floor over RX coil | 0.8-1.2mm | Qi 距離を増やしすぎない |
| Side wall | 1.5-2.0mm | 56mm PCB とのクリアランスは要確認 |
| Cup contact layer compression | 5-15% | まず軽い圧縮から評価 |

高さ `7mm` は参考値に留める。断熱、F1 固定、Qi 安定性を優先し、必要なら厚みを増やす。

## Internal heat spreader / support plate

カップ接触金属は却下する。ただし、金属が cup contact layer と retaining ring で完全に覆われ、通常使用・清掃・摩耗でカップへ触れない場合に限り、内部 heat spreader として thin aluminum を試験候補にする。

第一候補:

- material: `A5052` または `A6061` thin aluminum sheet
- thickness: `0.3mm` initial、比較用に `0.2mm` / `0.5mm`
- OD: `54-55mm`
- edge: deburred。retaining ring で必ず隠す
- bonding: JLC flexible heater の `3M 468MP` adhesive backing を使い、heater を aluminum spreader underside へ貼る

JLC flexible heater 注文時の候補:

- Adhesive Backing: `3M 468MP`
- Adhesive Position: `Non-soldering Side`

発注前に、lead-pad side と `Non-soldering Side` の向きを確認し、粘着面が aluminum spreader 側になり、lead exit が組立可能な向きになることを確認する。

## Cup contact layer 評価

v1 の第一候補はアルミナ充填シリコーンパッド。目的はカップ底面の湾曲に追従し、接触熱抵抗を下げつつ、Qi コイル近傍に大きな金属を置かないこと。

比較候補:

| サンプル | 厚み目安 | 期待 | 主な確認 |
| --- | --- | --- | --- |
| アルミナ充填シリコーンパッド | 0.5-1.0mm | 絶縁、追従性、Qi 近傍で扱いやすい | 表面温度、カップへの熱流、清掃性 |
| 低硬度熱伝導シリコーンシート | 1.0-2.0mm | 湾曲底面への追従性 | 立ち上がり、局所ホットスポット |
| グラファイトシート + 薄い絶縁フィルム | 0.1-0.3mm + film | 面内熱拡散 | FOD、渦電流、絶縁余裕 |

金属板は初回標準にしない。比較する場合も、Qi / FOD / 渦電流発熱の別リスクとして扱う。

cup contact layer は接着を主固定にしない。top retaining ring と浅いポケットで機械保持し、internal spreader / heater stack へ軽く圧縮する。必要な場合も、neutral-cure silicone または thermal silicone adhesive の外周少量固定に留め、全面の硬い接着、cyanoacrylate、epoxy、通常両面テープは避ける。

## Coil / ferrite / top stack 測定

PCB 着手前または初回組立時に、以下の積層条件を記録する。

- coil part number and measured L/Q/DCR
- L1 physical size and received construction (`760308102207` baseline: `40x40x1.2mm` rounded-square, `8uH`, DCR `60mΩ typ / 80mΩ max`, `Q=30 typ @125kHz`)
- ferrite part number, thickness, and whether it is coil-bonded (`SHIELD1` baseline: Wuerth Elektronik WE-FSFS 364105, 60x60x0.5mm, trimmed/fixtured to coil backing envelope)
- coil-to-ferrite gap
- ferrite-to-PCB gap
- PCB-to-heater insulation thickness
- heater-to-spreader adhesive thickness
- internal spreader material, thickness, and OD
- cup contact layer material and thickness
- bottom shell material and bottom floor thickness

EPP 15W pad と BPP 5W pad で、位置ずれ、金属マグ、カップなしの停止境界を別々に記録する。

## Open Items

- exact enclosure height
- exact resin material for bottom tray / top retaining ring
- コイル直径
- ~~フェライト寸法~~ → 別体候補は `SHIELD1 = Wuerth Elektronik WE-FSFS 364105`、60x60x0.5mm。最終外形は実コイル外形に合わせてトリム/固定し、L/Q/FOD 実測で採否を決める
- JLC heater `3M 468MP` / `Non-soldering Side` の向き確認
- internal aluminum spreader の厚み / OD
- F1 固定方法の最終選定
- cup contact layer の具体品番
- thermal test の実測結果
