# 初回メカ前提

## 部品名（正式名称 — 以後この名前を使う）

このプロジェクトの説明・レビュー・コミットでは、必ず下記の **正式名称（Canonical name）** を使う。
正式名称は `enclosure-proto.scad` のモジュール名／`show_*` トグルに一致させる。
右端の「使わない別名」は過去の表記揺れで、今後は使わない。

| 正式名称 (Canonical) | SCAD 識別子 | 現行寸法 (OD×厚) | 役割 | 使わない別名 |
| --- | --- | --- | --- | --- |
| **cup contact pad** | `cup_contact_pad` / `pad_*` | Ø56.5 × 0.80 | カップ底に触れる接触面（凸クラウン）。素材はシリコーン等を評価中 | cup contact layer, cup contact silicone pad, pad（口語可） |
| **aluminum spreader** | `aluminum_spreader` / `spreader_*` | Ø54.5 × 0.30 | 内部ヒートスプレッダ。cup contact pad の下で熱を面拡散 | internal heat spreader, support plate, metal spreader |
| **flexible heater** | `flexible_heater` / `heater_*` | Ø55 × 0.35 | JLC フレキヒータ。heater seat 段差に乗る。NTC 内蔵 | heater stack |
| **F1** | `f1_reference` / `f1_*` | 4.8×3.2×0.89 | Bourns NR72CB0 (C183007) サーマルカットオフ。flexible heater 下面に密着 | thermostat, thermal cutoff（説明補足は可） |
| **insulation** | `insulation_layer` / `insulation_*` | Ø50 × 0.70 | 下方への熱漏れを抑える断熱層 | insulation sheet |
| **PCB** | `pcb_reference` / `pcb_*` | Ø50 × 1.0 | メイン基板 | board |
| **ferrite** | `ferrite_reference` / `ferrite_*` | Ø50 × 0.50 | Qi 磁束シールド | shield |
| **RX coil** | `rx_coil_reference` / `coil_*` | 40×40 × 1.20 | Qi 受電コイル L1 (Würth 760308102207) | L1（補足可）, rx coil reference |
| **bottom tray** | `bottom_tray` | enclosure_od Ø60 | 開いた樹脂トレイ。全スタックを保持。底面は Qi 面。内向き庇・棚なし（pad まで上から落とし込める） | bottom shell, enclosure（文脈で可） |
| **top retaining ring** | `top_retaining_ring` / `ring_*` | 外径Ø60 / 内径Ø54.5 | bottom tray とは**別体**の印刷パーツ。pad 装着後に被せ、内フランジが pad エッジを抑えて抜け止め。固定方法（ネジ/ねじ込み/接着）は未定 | integrated retaining lip, lip, retaining lip |
| **heater seat** | bottom tray の bore 段差 @z_heater | 下部 Ø50.7 / 上部 Ø57.2 | flexible heater が乗る段差。下の Ø50 部品は素通り、上部ボアは pad クリアランス | ledge |
| **PCB support ribs** | `pcb_support_ribs` | 2本 ×幅5.0 | PCB を H1/H2 で支持・ねじ留め（Ø50 化で要再設計） | support rib |
| **stack retention ribs** | `stack_retention_ribs` | 4本 ×幅4.0 | 外周の高さ基準・横ずれガイド（Ø50 化で要再検討） | retention rib |

> スタック順（下→上）は下記「積層案」を参照。現行の試作寸法変更は
> `docs/plans/20260606-enclosure-grow-topload-heater-seat.md` で進行中（PCB/ferrite/insulation→Ø50、
> heater→Ø55、heater seat 段差化、底面溝削除、lip を別体 top retaining ring に分離）。下表「初期寸法目安」の一部はこの plan で更新中。

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
- `F1` は `Bourns NR72CB0` (`C183007`) を使い、internal heat spreader / support plate または heater stack へ密着固定する
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

F1 は JLCPCB flexible-heater service で heater assembly に組み込む前提にする。低背化のため `Bourns NR72CB0` (`LCSC C183007`) の図面寸法を基準にし、body envelope は `4.8 x 3.2 x 0.89mm` とする。`NR72CB0` は `DC12V/12A` rating の低電圧 DC heater protector として扱い、trip 後 leakage は熱試験で確認する。

JLC heater の `Adhesive Position = Non-soldering Side` は、heater を internal aluminum spreader へ貼る面として予約する。F1 は heater bottom side、すなわち spreader adhesive bond の反対側に載る前提で扱う。このため heater 下側には F1 body `0.89mm` + installation clearance の逃げを確保し、PCB / insulation と干渉させない。mechanical model では `f1_clearance_gap = 1.4mm` を初期値にする。

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

v1 enclosure は一体型の非金属樹脂 bottom tray を第一候補にする。cup contact layer の保持は、別体 top ring ではなく bottom tray 一体の低い integrated retaining lip で行う。

OpenSCAD study model: `enclosure-proto.scad`

- bottom tray: 浅い凹型トレー。PCB、coil/ferrite clearance、断熱材、heater stack を保持する
- integrated retaining lip: bottom tray 一体の低い外周リムで cup contact layer を保持し、内部 metal spreader のエッジを隠す
- bottom tray の Qi pad 側底面は薄くし、金属を入れない
- H1 heater cable は側面から外へ逃がさず、heater underside からPCB側へ落として H1 pads / wire pads へ接続する。bottom tray side wall には heater cable 用の横穴を作らない。heater board の `J1` leadout pads は基板中心 `(100,100)` から `(0,+22.5mm)` の位置で、pad row envelope は約 `24 x 5mm`
- 滑り止めは底面外周の薄いシリコーンリングまたは足で行う
- コイル中心付近の金属ねじは避け、必要なら perimeter の樹脂スナップ、樹脂ボス、nylon M2 ねじを使う
- カップ底面は凹形状が多いため、cup contact layer の上面は浅い凸形状にする。integrated retaining lip は pad 上面より低くし、カップ側に凹形状を作らない
- 旧 PCB mounting holes `H3=(116,84)`, `H4=(116,116)`, `H5=(84,84)` は、board/enclosure center `(100,100)` 基準で `(16,-16)`, `(16,16)`, `(-16,-16)` にあり、`40x40mm` L1 coil envelope 内へ入っていたため KiCad から削除済み。現行 PCB mounting holes は `H1=(123.5,92)`, `H2=(76.5,108)`、中心基準で `(+23.5,-8)`, `(-23.5,+8)`、穴径 `2.4mm`。
- PCB support ribs は H1/H2 に合わせた2本を初期値にする。各 rib は bottom floor から PCB underside まで立ち上げ、width `5.0mm`、radial depth `2.4mm` とし、M2 plastic self-tap boss の中心を PCB の H1/H2 と一致させる。中心の L1 / ferrite keepout は開ける。
- aluminum spreader + heater stack の保持は、heater の `3M 468MP` 接着、spreader pocket、cup contact pad の軽い圧縮、integrated retaining lip の横ずれ防止を主にする。追加で bottom floor から立ち上がり outer tray wall へつながる4本の stack retention ribs を入れ、rib top は retaining lip / spreader pocket の下面高さに揃える。PCB と insulation sheet は外周ノッチで避け、縦リブが基板を貫通する形にする。これらの rib は heater を強く点押しする clamp ではなく、外周の高さ基準と横位置ガイドとして扱う

別体 top retaining ring は使わず、bottom tray 一体の低い integrated retaining lip へ統合する。理由は、カップ側に凹形状を作らず、部品点数を減らしつつ、cup contact layer の横ずれ防止と internal aluminum spreader のエッジ隠しを維持するため。分解性は下がるため、v1 では pad を圧入/摩擦保持できる寸法にして、必要な場合のみ外周少量の neutral-cure silicone で補助固定する。

integrated retaining lip は独立部品として製造しない。bottom tray と同じ樹脂材料で、同じ造形/成形プロセスの一部として作る。試作では SLA/MJF/SLS/切削樹脂のいずれかで bottom tray と一体造形し、内径側だけ軽く面取りして pad を入れやすくする。量産では射出成形の固定側/可動側で上端リップを抜ける形状にし、必要なら内側に小さい C 面または R を付ける。アンダーカットになる snap lip にはせず、浅い垂直リム + 摩擦保持 + 必要最小限の外周 silicone 固定で始める。

L1 receiver coil は `Wuerth Elektronik 760308102207` を基準にする。外形は `40x40x1.2mm` の rounded-square Qi RX coil、visible corner radius は DS 図から `5-8mm` 程度として扱う。coil termination は 2 holes `φ1.2mm` / `5.0mm` pitch の solder-pad termination。datasheet は integrated ferrite shield を明記していないため、受領品で背面 ferrite / EMI shield の有無を確認し、`SHIELD1` を削除するか別体フェライトを併用するかは L/Q/DCR/FOD 実測で決める。

初期寸法目安:

| Feature | Initial value | Notes |
| --- | ---: | --- |
| Enclosure OD | 60.0mm max | design-notes の改定方針に合わせる |
| PCB OD | 50.0mm | 現行 control PCB Gerber（Ø50 resize 済み）と整合 |
| flexible heater OD | 55.0mm | 現行 heater Gerber（Ø55）と整合。spreader Ø54.5 を覆い heater seat に乗る |
| Internal aluminum spreader OD | 54-55mm | cup contact layer より小さくし、エッジを隠す |
| Cup contact silicone pad OD | 56-57mm | spreader を完全に覆う |
| Bottom floor over RX coil | 0.8-1.2mm | Qi 距離を増やしすぎない |
| Side wall | 1.5-2.0mm | 56mm PCB とのクリアランスは要確認 |
| F1 clearance gap below heater | 1.4mm | C183007 body `0.89mm` + installation clearance |
| Bottom tray wall height | ~8.0mm | F1 組込み後の current stack に追従。pad top `~8.25mm` より `0.25mm` 低い |
| PCB support ribs | 2x, 5.0mm wide x 2.4mm radial | H1/H2 `2.4mm` PCB clearance holes と boss center を一致させる |
| Stack retention ribs | 4x, 4.0mm wide x ~3.0mm radial | bottom floor から retaining lip / spreader pocket 下面まで。outer tray wall へ接続し、PCB / insulation は外周ノッチで避ける |
| Integrated retaining lip inner OD | 55.6mm | pad を保持しつつ凸接触面を邪魔しない |
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

cup contact layer は接着を主固定にしない。integrated retaining lip と浅いポケットで機械保持し、internal spreader / heater stack へ軽く圧縮する。必要な場合も、neutral-cure silicone または thermal silicone adhesive の外周少量固定に留め、全面の硬い接着、cyanoacrylate、epoxy、通常両面テープは避ける。

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
- exact resin material for bottom tray / integrated retaining lip
- コイル直径
- ~~フェライト寸法~~ → 別体候補は `SHIELD1 = Wuerth Elektronik WE-FSFS 364105`、60x60x0.5mm。最終外形は実コイル外形に合わせてトリム/固定し、L/Q/FOD 実測で採否を決める
- JLC heater `3M 468MP` / `Non-soldering Side` の向き確認
- internal aluminum spreader の厚み / OD
- F1 固定方法の最終選定
- cup contact layer の具体品番
- thermal test の実測結果
- bottom tray の側壁に PCB 上の 2 個の LED を外から視認できる穴 / 導光窓を追加する
