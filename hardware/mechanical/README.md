# 初回メカ前提

## 部品名（正式名称 — 以後この名前を使う）

このプロジェクトの説明・レビュー・コミットでは、必ず下記の **正式名称（Canonical name）** を使う。
正式名称は `enclosure-proto.scad` のモジュール名／`show_*` トグルに一致させる。
右端の「使わない別名」は過去の表記揺れで、今後は使わない。

| 正式名称 (Canonical) | SCAD 識別子 | 現行寸法 (OD×厚) | 役割 | 使わない別名 |
| --- | --- | --- | --- | --- |
| **cup contact pad** | `cup_contact_pad` / `pad_*` | Ø55.0 × 1.00 | カップ底に触れる接触面。初回はARCTIC TP-4を平面シートとして扱う | cup contact layer, cup contact silicone pad, pad（口語可） |
| **aluminum spreader** | `aluminum_spreader` / `spreader_*` | Ø54.5 × 0.30 | 内部ヒートスプレッダ。cup contact pad の下で熱を面拡散 | internal heat spreader, support plate, metal spreader |
| **flexible heater** | `flexible_heater` / `heater_*` | Ø55 × 0.50 | JLC フレキヒータ。heater seat 段差に乗る。NTC 内蔵 | heater stack |
| **F1** | `f1_reference` / `f1_*` | 28×8.9×5.1（外装包絡）+ 80mm リード | Xucheng Elec KSD9700-70/5JSB/080C (C156512) リード式バイメタルサーモスタット。heater hotspot に密着、H+ 直列 | thermostat, thermal cutoff（説明補足は可） |
| **insulation** | `insulation_layer` / `insulation_*` | Ø50 × 0.70 | 下方への熱漏れを抑える断熱層 | insulation sheet |
| **PCB** | `pcb_reference` / `pcb_*` | Ø50 × 1.6 | メイン基板。JLCPCB実発注厚に合わせる | board |
| **ferrite** | `ferrite_reference` / `ferrite_*` | Ø50 × 0.50 | Qi 磁束シールド | shield |
| **RX coil** | `rx_coil_reference` / `coil_*` | 40×40 × 1.20 | Qi 受電コイル L1 (Würth 760308102207) | L1（補足可）, rx coil reference |
| **bottom tray** | `bottom_tray` | enclosure_od Ø60 | 開いた樹脂トレイ。全スタックを保持。底面は Qi 面。pad まで上から落とし込める | bottom shell, enclosure（文脈で可） |
| **integrated centering rim** | bottom tray 一体 / `rim_*` | 外径Ø60 / 内径Ø55.8 / 高さ0.5 | cup contact padを横方向に位置決めする低い一体リム。pad上面や外周に被せない | top retaining ring, retaining lip, lip |
| **heater seat** | bottom tray の bore 段差 @z_heater | 下部 Ø52.3 / 上部 Ø55.8 | flexible heater が乗る段差。下の Ø50部品と40mm角coil cornerを逃がし、上部ボアはpad/rim内径に一致 | ledge |
| **lower stack support shelf** | `lower_stack_support_shelf` | 左右2面 / 高さ1.6 | 40mm角coilの上下リード出口を避け、左右の余白面でferrite/PCB stackを下から受ける | PCB support ribs, support rib |

> スタック順（下→上）は下記「積層案」を参照。現行方針は
> `hardware/mechanical/enclosure-proto.scad` を正とする。旧案の別体リングは使わず、
> bottom tray 一体の低い integrated centering rim で cup contact pad を横方向に位置決めする。

## 積層案

```
[Cup]
[Cup contact pad]
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
- `F1` は `Xucheng Elec KSD9700-70/5JSB/080C` (`C156512`) を使い、internal heat spreader / support plate または heater stack へ密着固定する
- heater 内蔵 NTC を `H1` の4線ハーネスで受け、`RX_NTC` へ接続する
- カップに触れる面へ金属を露出させない
- 内部 heat spreader / support plate は、カップから完全に隠れる場合に限り thin aluminum を比較候補にする
- cup contact pad は、硬い金属板ではなく曲面追従できる絶縁 thermal interface を第一候補にする
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

F1 は JLCPCB flexible-heater service で heater assembly に組み込む前提にする。当初は低背化のため SMD の `Bourns NR72CB0` (`C183007`) を候補にしたが、JLC 工程では `NR72CB0` も `SA77SB0` (`C143808`) も laser welding 必須で手はんだ不可だったため、手はんだ可能なリード品 `Xucheng Elec KSD9700-70/5JSB/080C` (`LCSC C156512`) に戻した。body は外装包絡 `28 × 8.9 × 5.1mm`、内部can相当が約 `20 × 7.5 × 3.7mm`、リードは `80mm` 浸錫ワイヤ。`KSD9700-70` は `AC250V/5A`・`DC12V/12A` rating のバイメタルサーモスタット（trip 70±5°C / reset 50±10°C, 自己復帰 NC）として扱い、trip/reset/再投入挙動を熱試験で確認する。OpenSCAD では外装包絡を heater 下面に横置きする実寸参照として扱い、heater 下クリアランスを `5.1 + 0.6 = 5.7mm` とする。

JLC heater の `Adhesive Position = Non-soldering Side` は、heater を internal aluminum spreader へ貼る面として予約する。F1 は heater bottom side、すなわち spreader adhesive bond の反対側に載る前提で扱う。このため heater 下側には F1 body + installation clearance の逃げを確保し、PCB / insulation と干渉させない。`KSD9700-70` の外装包絡は `28 × 8.9 × 5.1mm` と大きく、heater 下面に寝かせると約 5.7mm の高さを食う。初回SCADではこの高さを積んで干渉を避けるが、低背化するなら F1 を heater 中央から外周・harness 側へ寄せて hotspot 熱結合を別途確保する案を比較する。

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

v1 enclosure は一体型の非金属樹脂 bottom tray を第一候補にする。cup contact pad は bottom tray 一体の低い integrated centering rim で横方向に位置決めし、pad上面や外周には被せない。

OpenSCAD study model: `enclosure-proto.scad`

- bottom tray: 浅い凹型トレー。PCB、coil/ferrite clearance、断熱材、heater stack を保持する
- integrated centering rim: bottom tray 一体の低い外周リムで cup contact pad を横方向に位置決めし、内部 metal spreader のエッジを隠す
- bottom tray の Qi pad 側底面は薄くし、金属を入れない
- H1 heater cable は側面から外へ逃がさず、heater underside からPCB側へ落として H1 pads / wire pads へ接続する。bottom tray side wall には heater cable 用の横穴を作らない。heater board の `J1` leadout pads は基板中心 `(100,100)` から `(0,+22.5mm)` の位置で、pad row envelope は約 `24 x 5mm`
- 滑り止めは底面外周の薄いシリコーンリングまたは足で行う
- コイル中心付近の金属ねじは避け、必要なら perimeter の樹脂スナップ、樹脂ボス、nylon M2 ねじを使う
- カップ底面は凹形状が多いが、初回TP-4 direct-pad構成では cup contact pad を平面シートとして扱う。integrated centering rim は pad 上面より低くし、カップ側に凹形状を作らない
- 旧 PCB mounting holes `H3=(116,84)`, `H4=(116,116)`, `H5=(84,84)` は、board/enclosure center `(100,100)` 基準で `(16,-16)`, `(16,16)`, `(-16,-16)` にあり、`40x40mm` L1 coil envelope 内へ入っていたため KiCad から削除済み。現行 PCB mounting holes は `H1=(121,92)`, `H2=(79,108)`、中心基準で `(+21,-8)`, `(-21,+8)`、穴径 `2.4mm`。
- lower stack support shelf は左右2面だけにする。coilの導線が出る上下方向にはsupportを置かず、40mm角coilの外形とbottom tray内側の間に残る左右の余白面でferrite/PCB stackを下から受ける。
- 旧PCB support ribs / screw bosses は現行v1ではdefault offにする。H1/H2 screw boss候補はcoil referenceと干渉しやすいため、受領coilとPCB実物で余白を確認してから戻す。
- aluminum spreader + heater stack の保持は、heater の `3M 468MP` 接着、cup contact pad の軽い圧縮、integrated centering rim の横ずれ防止を主にする。旧stack retention ribsは40mm角coilと干渉するためSCADから削除した。

別体リングは使わず、bottom tray 一体の低い integrated centering rim へ統合する。理由は、カップ側に凹形状を作らず、部品点数を減らしつつ、cup contact pad の横ずれ防止と internal aluminum spreader のエッジ隠しを維持するため。分解性は下がるため、v1 ではpadを上から落とし込み、必要な場合のみ外周少量の neutral-cure silicone で補助固定する。

integrated centering rim は独立部品として製造しない。bottom tray と同じ樹脂材料で、同じ造形/成形プロセスの一部として作る。試作では SLA/MJF/SLS/切削樹脂のいずれかで bottom tray と一体造形し、内径側だけ軽く面取りして pad を入れやすくする。量産では射出成形の固定側/可動側で上端リムを抜ける形状にし、必要なら内側に小さい C 面または R を付ける。アンダーカットになる snap lip にはせず、浅い垂直リム + 摩擦保持 + 必要最小限の外周 silicone 固定で始める。

L1 receiver coil は `Wuerth Elektronik 760308102207` を基準にする。外形は `40x40x1.2mm` の rounded-square Qi RX coil、visible corner radius は DS 図から `5-8mm` 程度として扱う。coil termination は 2 holes `φ1.2mm` / `5.0mm` pitch の solder-pad termination。datasheet は integrated ferrite shield を明記していないため、受領品で背面 ferrite / EMI shield の有無を確認し、`SHIELD1` を削除するか別体フェライトを併用するかは L/Q/DCR/FOD 実測で決める。

初期寸法目安:

| Feature | Initial value | Notes |
| --- | ---: | --- |
| Enclosure OD | 60.0mm max | design-notes の改定方針に合わせる |
| PCB OD | 50.0mm | 現行 control PCB Gerber（Ø50 resize 済み）と整合 |
| flexible heater OD | 55.0mm | 現行 heater Gerber（Ø55）と整合。spreader Ø54.5 を覆い heater seat に乗る |
| Internal aluminum spreader OD | 54-55mm | cup contact pad より小さくし、エッジを隠す |
| Cup contact silicone pad OD | 55.0mm | 初回direct-pad構成。rim内へ上から落とし込む |
| Bottom floor over RX coil | 1.2mm | 初回3Dプリントは反り・薄肉破損を避けるため0.8-1.2mm範囲の上限を使う |
| Side wall | 1.5-2.0mm | Ø50mm PCB / ferrite と40mm角coilの実物クリアランスは要確認 |
| F1 clearance below heater | 5.7mm | KSD9700-70 外装包絡 `28 × 8.9 × 5.1mm` + installation clearance 0.6mm。heater下面に横置きする仮モデル |
| Bottom tray wall height | 12.9mm | 現行SCADのrim top。F1横置き込みでpad topは約 `13.4mm` |
| Lower stack support shelf | 左右2面 / support height 1.6mm | coil導線が出る上下を開け、左右の余白面でferrite/PCB stackを受ける |
| Integrated centering rim inner OD | 55.8mm | Ø55mm pad に対して radial gap 0.40mm。DMM PA12 MJF と手切りTP-4の逃げ |
| Cup contact pad compression | 5-15% | まず軽い圧縮から評価 |

高さ `7mm` は参考値に留める。断熱、F1 固定、Qi 安定性を優先し、必要なら厚みを増やす。

## Internal heat spreader / support plate

カップ接触金属は却下する。ただし、金属が cup contact pad と integrated centering rim で完全に覆われ、通常使用・清掃・摩耗でカップへ触れない場合に限り、内部 heat spreader として thin aluminum を試験候補にする。

第一候補:

- material: `A5052` または `A6061` thin aluminum sheet
- thickness: `0.3mm` initial、比較用に `0.2mm` / `0.5mm`
- OD: `54-55mm`
- edge: deburred。integrated centering rim と cup contact pad で必ず隠す
- bonding: JLC flexible heater の `3M 468MP` adhesive backing を使い、heater を aluminum spreader underside へ貼る

JLC flexible heater 注文時の候補:

- Adhesive Backing: `3M 468MP`
- Adhesive Position: `Non-soldering Side`

発注前に、lead-pad side と `Non-soldering Side` の向きを確認し、粘着面が aluminum spreader 側になり、lead exit が組立可能な向きになることを確認する。

v1 は 2026-06-13 に発注済み (JLCPCB `FH2026061328500004`、2026-06-23 発送)。受領品で adhesive の有無・貼付面が上記どおりか、および engineering review で変更された NTC の dot adhesive 実装位置を実測で確認すること。review の詳細は `docs/design-notes.md` の「v1 engineering review の結果」を参照。

## Cup Contact Pad 評価

v1 の第一候補はアルミナ充填シリコーンパッド。目的はカップ底面の湾曲に追従し、接触熱抵抗を下げつつ、Qi コイル近傍に大きな金属を置かないこと。

比較候補:

| サンプル | 厚み目安 | 期待 | 主な確認 |
| --- | --- | --- | --- |
| アルミナ充填シリコーンパッド | 0.5-1.0mm | 絶縁、追従性、Qi 近傍で扱いやすい | 表面温度、カップへの熱流、清掃性 |
| 低硬度熱伝導シリコーンシート | 1.0-2.0mm | 湾曲底面への追従性 | 立ち上がり、局所ホットスポット |
| グラファイトシート + 薄い絶縁フィルム | 0.1-0.3mm + film | 面内熱拡散 | FOD、渦電流、絶縁余裕 |

金属板は初回標準にしない。比較する場合も、Qi / FOD / 渦電流発熱の別リスクとして扱う。

cup contact pad は接着を主固定にしない。integrated centering rim と浅いポケットで機械保持し、internal spreader / heater stack へ軽く圧縮する。必要な場合も、neutral-cure silicone または thermal silicone adhesive の外周少量固定に留め、全面の硬い接着、cyanoacrylate、epoxy、通常両面テープは避ける。

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
- cup contact pad material and thickness
- bottom shell material and bottom floor thickness

EPP 15W pad と BPP 5W pad で、位置ずれ、金属マグ、カップなしの停止境界を別々に記録する。

## Open Items

- exact enclosure height
- exact resin material for bottom tray / integrated centering rim
- RX coil実物外形とcorner radius
- ~~フェライト寸法~~ → 別体候補は `SHIELD1 = Wuerth Elektronik WE-FSFS 364105`、60x60x0.5mm。最終外形は実コイル外形に合わせてトリム/固定し、L/Q/FOD 実測で採否を決める
- JLC heater `3M 468MP` / `Non-soldering Side` の向き確認
- internal aluminum spreader の厚み / OD
- F1 固定方法の最終選定
- **F1 低背化検討**: 現行SCADは `KSD9700-70` (`28 × 8.9 × 5.1mm` 外装包絡) を heater 下面に横置きし、`f1_clearance_gap=5.7mm` で干渉を避ける。背を下げる場合は、F1 を heater 中央から外周・harness 側へ移設して hotspot 熱結合を別途確保するか決める
- cup contact pad の具体品番
- thermal test の実測結果
- bottom tray の側壁に PCB 上の 2 個の LED を外から視認できる穴 / 導光窓を追加する
