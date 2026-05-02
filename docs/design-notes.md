# 設計ノート

## 現在の前提

- 受電 IC は `STWLC38JRM`
- 目標は `15W` 級 Qi cup warmer
- 弱い保温専用ではなく、十分な保温と軽い再加熱の中間を狙う
- `15W` でも安全、`FOD`、位置ずれ、金属部材の影響は無視しない
- `WLCSP40` 実装は外注前提
- 初回は KiCad バイナリより先に、テキストで設計判断を固定する

## システム概要

本デバイスは高温化しうるため、温度制御とハード保護を前提にする。

```text
[カップ]
   |
[トッププレート] ← 熱伝導面（TH1 / NTC_A を裏面に配置）
[熱拡散層 / ヒーター層]
[断熱層]
[制御PCB] ← Qi 受電 + 電力制御 + 温度監視
[TH2 / NTC_B] ← 電力系・コイル近傍保護
[フェライトシート]
[Qi 受電コイル]
[底面シェル]
   |
[Qi EPP 15W 送電パッド]
```

## 設計方針

採用する前提:

- 目標出力は `15W` 級
- 互換性は `EPP 15W` を中心に考える
- `5W` より高いが、過剰な高出力設計には寄せない
- 温度監視、Qi 側停止、独立ハード遮断を組み合わせる

捨てる前提:

- `BQ51013B` ベースの `5W` 受電
- ヒーター直結だけで済む単純設計
- 保温用途だから軽い保護で十分という仮定
- どの Qi パッドでも同じように動くという仮定

## 現時点の主要判断

### 1. 受電 IC

`STWLC38JRM` を採用する。理由は、現行 `15W` 候補としての妥当性と、`4-12V` 可変出力、`I2C`、`FOD`、熱保護を持つ点。

受電部の要求:

- `15W` 対応受電コイル
- 共振ネットワークの再設計と実測調整
- 受電後の電力制御段
- 温度、電流、電圧の監視

### 2. 電圧方針

初回は `12V` 出力を第一候補にする。  
理由は `15W` を低電流で扱えるためで、ヒーター、MOSFET、配線損失の面で有利。

### 3. ヒーター方針

初回ヒーター目標:

- `12V`
- `15Ω` 前後（2026-04-26 改定。10Ω では 14.4W となり EPP 15W × 80-85% 効率の利用可能 12-12.75W を超え、VOUT ドループ → OCP トリップの懸念）
- `9.6W` 前後

最終値は熱試験で再調整する。

### 4. 制御方針

初版では外部 `MCU` は載せない。  
`STWLC38JRM` の autonomous 動作、`I2C` service header、独立ハード保護で成立させる。

- 初版は固定 `VOUT_12V` 前提
- **v1 ヒーター gate ドライブ: 常時 ON（VOUT_12V → R1 (10k) → Q1.G、Q1.G → R2 (10k) → GND の分圧）**。VGS ≈ 6V でロジックレベル N-FET を確実に ON しつつ、`AO3400` クラス (VGS_max ±12V) でも VOUT スパイク時のマージンを確保する。Qi 給電中は連続通電。温度保護は F1 サーモスタットのみ。PWM/可変制御は v2 以降。MCU を入れる場合はゲートドライバ IC または低閾値 FET でレベル整合する。
  - Q1 候補: `AO3400` (SOT-23, RDS(ON)=28mΩ@VGS=10V, VGS_max ±12V)。I_heater = 0.8A での損失 ≈ 18mW で熱的に余裕。VGS マージンを上げたい場合は VGS ±20V 品（`DMN3404L` / `NTR4170N` 等）に置換。
- 製品固有の温調ロジックは初版のスコープ外
- `ENB` は未使用時 `GND` 固定を基本にする
- `RX_NTC` には TH2 (10k NTC, board hotspot near Qi coil) を接続し、R7 (10k → RX_VAA) と分圧する。STWLC38 内蔵 OTP がコイル/基板温度で自律的に給電を絞る/停止する。NTC を未配置にする場合は R7 のみで pull-up 終端
- `INTB` は optional な bring-up / service 観測線として扱う
- `IEXT` は `RCL + TVS` の clamp path を前提にする

v2 以降または製品版で必要な制御:

- 出力デレート
- 温度上昇速度での保護
- 空焼き時の停止
- センサ断線 / 短絡時のフェイルセーフ
- `PWM` または段階的出力制御
- ソフトスタート
- 高温時の自動デレート
- カップなし時の停止または強い出力制限

### 5. 保護方針

- `NTC_A`: top plate (TH1 → J2 経由で外部観測)
- `NTC_B`: power board hotspot (TH2 → RX_NTC, IC 内蔵 OTP)
- `F1`: independent hardware cutoff。v1 は `Xucheng KSD9700-70/5JSB/080C` を第一候補にする
- `FOD`: Qi 側の停止系として扱う

Heater / F1 接続方針:

- v1 の `H1` footprint はヒーター本体ではなく、外部 heater/F1 series assembly を受ける大型 solder pads / wire pads として扱う
- 接続順は `VOUT_12V -> F1 -> heater -> Q1 drain`。F1 は PCB 上に寝かせず、トッププレート裏面へ密着固定する
- flexible heater と F1 は手実装ワイヤで接続する。v1 では board-to-wire connector や FPC/FFC connector は採用しない
- pad は `12V`, `0.8A` 連続電流、手はんだ、引張緩和を前提に余裕を持たせる。connector 化は v2/量産検討

F1 採用候補（PDF: `Xucheng Elec KSD9700-70:5JSB:080C.pdf`）:

- 型番/仕様: `KSD9700-70/5JSB/080C/QG`
- 種別: 双金属片突跳式、自動復帰サーモスタット
- 接点: `SPST-NC`（常閉、温度上昇で open）
- 動作温度: `70 ±5°C`
- 復帰温度: `50 ±10°C`
- 定格: `AC250V 5A` 抵抗負荷、10,000 cycles
- 接触抵抗: `≤50mΩ`
- 絶縁抵抗: `DC500V ≥100MΩ`
- 耐圧: `AC1450V / 1min`
- リード: `1015 20AWG black wire`, `80mm`, 先端 `8mm` 予備はんだ
- 実装: トッププレート裏面に密着。JLCPCB 自動実装が難しければ基板側に接続パッド/穴だけ用意して手実装

今回のヒーター電流は `12V / 15Ω ≈ 0.8A` なので、PDF の AC 抵抗負荷定格に対して電流余裕は十分。ただし DC 定格は PDF に明記されていないため、v1 熱試験で開閉挙動と接点温度を確認する。

最低 4 層の保護として考える:

1. 接触面温度監視: 天板裏面の `NTC` / 温度センサ
2. 電力系温度監視: 受電部と電力段の近傍温度
3. Qi 側停止: 通信異常、`FOD`、出力制限時に送電停止へ移行
4. 独立遮断: ヒーター系にハード遮断を入れる

追加で検証する異常:

- カップなし時の急上昇
- センサ断線 / 短絡
- 温度上昇速度の異常
- 位置ずれや金属異物による `FOD`

## 発熱体・熱設計

`15W` は「温かい」ではなく、十分な発熱量として扱う。接触面の安全を優先して評価を始める。

初期熱目標:

- 接触面定常温度はまず `50-55°C` を起点に評価
- カップあり / なし / 金属マグで別々に検証
- 温度上昇速度も監視対象にする

ヒーター要求:

- 面内温度分布が均一
- 局所ホットスポットが出にくい
- 絶縁と接着の耐熱性が十分
- 電気的異常時に安全側へ倒れる

ヒーター候補:

- ポリイミドヒーター
- 金属箔エッチングヒーター

熱経路:

- 上方: カップへの有効熱流
- 下方: PCB と受電部への寄生熱流
- 横方向: 天板内の熱拡散

材料候補と注意点:

- アルミ天板は候補だが、Qi 結合と `FOD` への影響を再評価する
- セラミック天板も比較候補
- 断熱材は `5W` 案の流用前提にしない

## メカニカル設計

位置ずれは `15W` でも性能と `FOD` に効く。

- 底面の滑り止めを入れる
- 中心合わせしやすい外形にする
- 必要なら軽い位置決めガイドを追加する
- 外径 90mm 前後は維持候補
- 高さ `7mm` は参考値
- 断熱とシールドを優先し、必要なら厚みを増やす

## Qi / FOD / 互換性

`FOD` は `15W` でも重要。次を分けて評価する。

- 金属製カップ底面
- 金属トッププレート
- 位置ずれ
- コイルからの距離増加
- ヒーター材の損失

評価で記録すること:

- どの条件で安定給電するか
- どの条件で停止するか
- どこまで位置ずれ耐性があるか

互換性の優先順:

1. `EPP 15W` 送電パッド
2. `5W BPP` パッドでのデグレード動作
3. それ以外はベストエフォート

## プロトタイピング戦略

### Phase 0: 実現性判定

1. `EPP 15W` 送電パッドを確保
2. `15W` 級受電アーキテクチャ候補を確定
3. 想定ヒーターと熱安全域を先に把握

### Phase 1: 熱単体評価

1. ベンチ電源で `15W` 相当のヒーターを駆動
2. カップあり / なし / 金属マグで評価
3. 天板温度、裏面温度、立ち上がり速度を測定

### Phase 2: 電力制御評価

1. センサ入力で出力をデレート
2. 空焼き時に安全停止できるか検証
3. ハード遮断の動作点を確認

### Phase 3: Qi 統合

1. コイル + フェライト + 制御基板 + 断熱 + ヒーターを統合
2. 位置ずれ耐性を測る
3. `FOD` 条件をマッピングする

### Phase 4: 筐体統合

1. 筐体へ組込み
2. 水滴、熱サイクル、長時間運転試験
3. 誤使用試験を追加

## 初回 PCB の考え方

- `4-layer`
- `X-ray` 前提
- `via-in-pad` などは設計前に外注 DFM で確定
- cup contact layer と coil の距離は最小化しつつ、金属干渉は後で実測する
- カップ側は湾曲している可能性が高いため、硬い平板 top plate ではなく、曲面追従できる柔軟な thermal interface / cup contact layer を優先して評価する
- v1 第一候補はアルミナ充填シリコーンパッドにする。電気絶縁性、曲面追従、熱伝導、Qi 近傍での扱いやすさのバランスを優先する
- 比較サンプル候補:
  - 熱伝導シリコーンシート
  - グラファイトシート + 薄い絶縁フィルム

GND 方針:

- 回路図ネット名 `SYS_GND` は、基板全体で共有する system 0V を意味する。`STWLC38JRM` の `VSSP/VSSA/VSSD`、heater return、TVS return、NTC/I2C/service reference は電気的には同じ 0V 系へ接続する
- `SYS_GND` は `PGND` だけでも `AGND` だけでもないため、回路図では役割を限定しない名前にしている
- v1 では `PGND/AGND/DGND` を別ネット化せず、`SYS_GND` 一本のままにする。net-tie や plane split は、return path を切るリスクが高いため初回では使わない
- PCB では `In1.Cu` を solid GND plane とし、GND integrity と熱拡散を優先する
- `VSSP`、`CRECT/COUT`、`Z3`、heater return は power return 領域として短く太く U1 近傍へ戻す
- `VSSA`、`VAA/VDD` decoupling、`NTC`、I2C/service reference は quiet 領域として扱い、大電流 return を通さない
- `VSSP/VSSA/VSSD` の実質合流点は U1 直近の GND via cluster とし、離れた場所で一点合流を作らない

## ブロック図

```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
flowchart TB
    subgraph POWER[Power Path]
        direction LR
        TX[Qi 送電パッド / 外部電源]
        COIL[受電コイル + 共振ネットワーク]
        RX[STWLC38JRM<br/>Qi RX / 整流 / 制御]
        VOUT[VOUT 12V]
        GATE[heater-control<br/>MOSFET + current path]
        HEATER[ヒーター / top plate]

        TX --> COIL
        COIL --> RX
        RX --> VOUT
        VOUT --> GATE
        GATE --> HEATER
    end

    subgraph PROTECT[Protection]
        direction LR
        NTCA[NTC_A<br/>top plate]
        NTCB[NTC_B<br/>power hotspot]
        F1[F1<br/>独立ハード遮断]
        FOD[FOD / thermal protection]
        OTP[STWLC38<br/>internal OTP]

        NTCA --> F1
        NTCB --> F1
        NTCB --> OTP
    end

    subgraph SERVICE[Bring-up / Monitor]
        direction LR
        I2C[I2C service header]
        INTB[INTB optional monitor]
        ENB[ENB = GND 固定]
        IEXT[IEXT<br/>RCL + TVS clamp]

        INTB -. optional .-> I2C
    end

    F1 --> GATE
    I2C -. service / bring-up .-> RX
    ENB -. fixed strap .-> RX
    IEXT -. protection path .-> RX
    RX -. status / shutdown .-> FOD
    FOD -. stop power transfer .-> TX
    OTP -. throttle/stop .-> RX
```

- 初版は外部 `MCU` なし
- 電力の主経路は `Qi TX → coil → STWLC38JRM → VOUT_12V → heater-control → heater`
- 温度・異常時の停止は `FOD` と `F1` の二系統で受け持つ
- `I2C` / `INTB` は製品制御ではなく、bring-up / service 用の観測・設定経路として扱う
- `J1` I2C service header は `RX_VAA` 2.5V 参照の bring-up 専用口とする。v1 ではオンボード level shifter を載せず、外部 USB-I2C adapter は `VREF=RX_VAA` に追従できるものだけを使う。3.3V 固定 pull-up / 3.3V 出力の直結は禁止

## 回路図ステータス（2026-05-01 時点）

DS14078 Figure 13 / Table 36 に合わせた修正後の状態:

- `BOOT1/BOOT2` 各 `47nF` (C5/C6) → **AC1/AC2 に接続**（ブートストラップ）
- `VAA` `4.7uF` (C7) + `NTC → VAA 10k` pull-up (R7)
- `VDD` `1uF` (C8) + HF bypass `100nF` (C4)
- `VRECT` `10uF` (C9)
- `IEXT` clamp: `RCL 300R` (R4) → **VRECT** 接続（OVP クランプ用、IEXT 内部スイッチ経由）
- `AC1/AC2` ESD: `SMF13A` (Z1/Z2) 各 `GND` 直結
- `Cs` 系列共振 `100nF×5` (C1) + **`Cd` 並列共振 `3.3nF` (C15)**
- 受電コイル: v1 は STEVAL-WLC38RX と同じ `Luxshare-ICT LD81FP008-1H` を基準にする（`8±0.2uH @100kHz`, `DCR=190mΩ±10%`, `ACR=225mΩ±10%`）
- フェライト: コイル付属/同等の backing ferrite を優先。別体 ferrite sheet を使う場合は coil L/Q と FOD を再測定する
- COMA/COMB ASK 変調キャパ 4 本: C11=CCOMA1(10n→AC1), C12=CCOMB1(22n→AC1), C13=CCOMA2(10n→AC2), C14=CCOMB2(22n→AC2)
- `VS` は RX-only では未使用。評価ボードでは DNP ジャンパ経由の外部 `VS` 評価点として扱われており、v1 では未接続
- `ENB` → `GND` 固定
- **`SCL/SDA` pull-up `10k` (R5/R6) → `VAA` (2.5V)**（VDD は 1.1V LDO で I2C には低すぎる。J1 経由のホスト接続は `VREF=RX_VAA` 追従または外部レベルシフタ必須。3.3V 固定 pull-up の直結は禁止）
- `VOUT` → heater-control シートへ
- ヒーター gate 分圧: R1 = 10k (VOUT_12V → Q1.G), R2 = 10k (Q1.G → GND) で VGS ≈ 6V
- F1: `KSD9700-70/5JSB/080C` を `heater-control.kicad_sch` / BOM に反映済み。トッププレート裏面に密着固定し、TH1/TH2/F1 open/reset の差は熱試験で確認する
- VOUT OVP: `Z3 = Littelfuse SMBJ15A` を第一候補にする。`VOUT_12V → Z3 cathode`, `Z3 anode → SYS_GND` の一方向 TVS とし、VOUT 出口近傍に配置する
- LED: D1（給電中インジ、VOUT_12V → R10(3k) → D1 → GND）
- GPIO0 LED: D2/R11（RX_VAA → R11(1k) → D2 → GPIO0、GPIO0 は NVM 設定前提の optional indicator）

VOUT OVP 候補（PDF: `SMBJ15A.pdf`）:

- 型番: `SMBJ15A`
- 種別: unidirectional TVS diode, DO-214AA / SMB
- 用途: `VOUT_12V` の過渡過電圧を `SYS_GND` へ逃がし、Qi RX 側の OCP/FOD/停止へ持ち込む
- Peak pulse power: `600W` at `10/1000us`
- Reverse stand-off voltage `VR`: `15.0V`
- Breakdown voltage `VBR`: `16.7-18.5V` at `IT=1mA`
- Maximum clamping voltage `VC`: `24.4V` at `IPP=24.6A`
- Reverse leakage `IR`: `1uA` at `VR`
- Operating junction temperature: `-65 to 150°C`
- MSL: Level 1
- Polarity: cathode band denotes cathode

`VOUT_12V` は通常 12V なので `VR=15V` の TVS は通常動作では導通しない。異常時は 16.7V 以上で breakdown し、25V rated capacitors と 30V class MOSFET の破壊を避けるための短時間 clamp として扱う。TVS は連続過電圧を消費し続ける部品ではないため、故障時は Qi 送電側/受電側保護が停止する前提で評価する。

`sensors-logic.kicad_sch`:

- `J1`: I2C service header（VREF = VAA 2.5V、3.3V 固定ホスト直結禁止）
- `TH1` / `TH2`: `10k NTC` placeholder
- `R8`: `RX_VAA` への `10k` pull-up（NTC_TOP 用）。R9 (旧 NTC_PCB pull-up) は削除
- `RX_NTC` に TH2 (NTC_B) を接続、R7 (10k → RX_VAA) と分圧。STWLC38 内蔵 OTP 入力
- `J2`: `NTC_TOP` / `RX_NTC` thermal monitor header
- `J3`: `RX_INTB` / `I_HEATER_MON` status monitor header
- `R3`: v1 通常実装は `0Ω`。評価時だけ `0.05Ω` に差し替え、R3 両端をテスター/オシロで測ってヒーター電流を推定する。`I_HEATER_MON` は bench bring-up 用の任意観測点で、製品制御には使わない

R3 / STWLC38JRM ADC 方針:

- STWLC38JRM の外部 analog input として使えるのは実質 `NTC/ADCIN2`
- `NTC/ADCIN2` は TH2 (`RX_NTC`) に使うため、R3 の shunt 電圧入力には使わない
- GPIO0-2 は汎用 ADC 入力としては扱わない
- `0.05Ω` shunt は `0.8A` 時でも約 `40mV` と小さく、10-bit ADC に直接入れて製品制御するには弱い
- STWLC38JRM 内部の VOUT/OCP/FOD current measurement は I2C で参考値として見られる可能性があるが、これは R3 の外付け shunt 測定とは別物
- ヒーター電流を製品制御に使うなら、外部 current sense amplifier と MCU/ADC を追加する

`sensors-logic.kicad_sch` には以下を反映済み:

- `J1`: `RX_VAA` 2.5V 参照付き `I2C` service header。外部 adapter は `VREF=RX_VAA` に追従させ、3.3V 固定 pull-up は接続しない
- `TH1` / `TH2`: `10k NTC` placeholder
- `R8`: `RX_VAA` への `10k` pull-up（NTC_TOP 用）。R9 (旧 NTC_PCB pull-up) は削除
- TH2 → `RX_NTC` (R7 と分圧、STWLC38 内蔵 OTP 入力)
- `J2`: `NTC_TOP` / `RX_NTC` の thermal monitor header
- `J3`: `RX_INTB` / `I_HEATER_MON` の status monitor header
- BOM 初回照合: `initial-bom.csv` は回路図 ref に合わせて `TH1/TH2`, `J3`, `R4/R8/R10/R11`, `D1/D2`, `Z1/Z2/Z3`, `C11-C15` を反映済み。`C10` は現行回路図に存在しないため削除

ERC エラー: **0 件**。残りはローカルシンボルの `lib_symbol_mismatch` 警告のみ。

## Open Items

- ~~ST 推奨の完全な最小回路~~ → rx-power に反映済み
- ~~COMA/COMB 変調キャパシタ~~ → 4 本構成で実装済み (CCOMA1/2, CCOMB1/2)
- ~~exact coil baseline~~ → v1 は `Luxshare-ICT LD81FP008-1H` + `Cs=100nF×5` + `Cd=3.3nF` を基準にする。ferrite と実機共振値は積層後に実測で確定
- ~~heater final resistance~~ → 15Ω 採用（暫定）。熱試験で再調整
- ~~heater footprint~~ → v1 は大型 solder pads / wire pads。外部 heater/F1 series assembly を手実装し、F1 はトッププレート裏面へ密着固定する
- ~~cup contact layer material~~ → v1 第一候補はアルミナ充填シリコーンパッド。熱伝導シリコーンシート、グラファイトシート + 薄い絶縁フィルムは比較サンプルとして残す
- ~~hard cutoff implementation choice~~ → F1 は `Xucheng KSD9700-70/5JSB/080C` を第一候補に選定（open `70±5°C`, reset `50±10°C`）
- **F1 取付**: トッププレート裏面に密着させオーバーシュート抑制。手実装または機構固定を前提にする。詳細な固定候補は `hardware/mechanical/README.md`、熱試験記録は `hardware/test/thermal-test-template.md` に分離
- ~~VOUT 過電圧保護 TVS~~ → `SMBJ15A` を第一候補に選定（`VR=15V`, `VBR=16.7-18.5V`, `VC=24.4V`, `600W`）
- ~~LED-2 status indicator~~ → D2/R11 は `RX_VAA → R11(1k) → D2 → U1.F3(GPIO0)` に接続済み。`RX_INTB` は LED 駆動せず、J3 経由の bring-up / status monitor として露出する
- ~~R3 電流センス~~ → v1 通常実装は `0Ω`。評価時のみ `0.05Ω` に差し替えてベンチ測定する。STWLC38JRM には R3 を読ませない
- ~~PCB GND トポロジー~~ → 回路図は `SYS_GND` 一本、PCB は solid GND plane を維持し、`VSSP` power return と `VSSA` quiet reference を配置/配線で分離する
- ~~I2C service header 3.3V 制約~~ → v1 はオンボード level shifter なし。J1 は `RX_VAA` 2.5V VREF 追従アダプタ専用で、3.3V 固定 pull-up の直結は禁止
- ~~BOM 再生成・照合~~ → `initial-bom.csv` を現行 schematic ref と照合済み。採用品未確定の受動部品/ヘッダ/LED は `TBD` のまま管理

## 設計リスクと対策

| リスク | 深刻度 | 対策 |
|--------|--------|------|
| `15W` 受電構成の実装難度 | 中 | 受電アーキテクチャを先に絞る |
| `FOD` 誤検出 | 高 | 金属・位置ずれ・積層距離を早期評価 |
| 火傷リスク | 高 | 接触面温度制限、立ち上がり制御、独立遮断 |
| カップなし運転 | 高 | 急上昇検出と即時デレート |
| 金属製マグカップ | 高 | 実測で許容条件を決める |
| 薄型化との両立 | 中 | 断熱とシールド優先で厚みを調整 |
| 市販パッド相性 | 中 | `EPP` を中心に評価する |

## 検証方法

1. 熱設計検証: `15W` 相当ヒーターを有線で先に評価
2. 制御検証: 多点温度入力で安全停止を確認
3. Qi 統合検証: `EPP 15W` 送電側との結合安定性と `FOD` を確認
4. 安全検証: 空焼き、位置ずれ、金属マグ、無負荷を試験
5. 耐久検証: 長時間連続運転、熱サイクル、水滴試験

最初に閉じるべき事項:

- `15W` 級受電方式の選定
- `15W` 熱負荷の危険域把握
- 天板材と位置ずれ許容の確認
