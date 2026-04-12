# ST STWLC38 Datasheet DS14078

- Source: Local PDF `wiki/raw/assets/stwlc38-ds14078.pdf`
- Accessed: 2026-04-12
- Notes extraction: local text extraction via `fitz`

## Document identity

- 文書は `DS14078 - Rev 1 - September 2022`
- タイトルは `Qi-compliant dual mode wireless power receiver for up to 15W applications`
- 抽出上は `64` ページ見える
- 実質の datasheet 本体は `pp.1-63`
- `p.64` は Mouser の付加ページ

## Front matter / summary (`p.1`)

- `Up to 15 W output power`
- `Up to 5W output power in Tx mode`
- `Qi 1.3 inductive wireless standard communication protocol compliant`
- `High efficiency (98% typical) synchronous rectifier operating up to 800 kHz`
- `Low drop-out linear regulator with output current limit and input voltage control loop`
- `Adaptive Rectifier Configuration (ARC) Mode`
- `4 V to 12 V programmable output voltage`
- `Above 85% overall system efficiency`
- `32-bit, 64 MHz ARM Cortex M0+ core with 32kB RRAM,16 kB SRAM,64kB ROM`
- `10-bit A/D Converter`
- `Configurable GPIOs`
- `I2C Slave interface`
- `Output Over-Voltage clamping protection`
- `Accurate voltage/current measurement for FOD`
- `On-chip thermal management and protections`
- `Flip chip 40 bumps (2.12mm x 3.32mm)`
- Applications は `Smartphones`, `Wearable/Hearables TWS`, `Asset tracking devices`, `Medical and healthcare equipment`

## 1. Introduction (`p.2`)

- `STWLC38` は RX coil に発生した AC を整流し、regulated DC を出力する wireless power receiver
- 内蔵 `32-bit core MCU` が device supervisor
- MCU の役割
  - transmitter との通信維持
  - `Qi` 仕様順守
  - 効率最適化
  - 負荷とデバイス自身の監視と保護
- 上記処理は `ROM` 上の resident firmware が実行する
- 設定パラメータは internal `RRAM` に保存でき、power-up で自動読込される
- そのため `fully autonomous stand-alone chip` として動作可能
- host が直接監視や制御を行う用途では `I2C` で internal registers にアクセスする

## 2. Block diagram (`p.3`)

- 全体ブロック図の章
- 受電コイル入力、同期整流、主 `LDO`、`ASK` modulator、digital core、`I2C`、`GPIO`、`NTC`、`VRECT/VOUT` 関係を示す

## 3. Device pin out (`pp.4-5`)

### Pin groups

- `AC1`, `AC2`: RX series resonant circuit 接続
- `BOOT1`, `BOOT2`: synchronous rectifier bootstrap capacitor 接続
- `COMA1`, `COMA2`, `COMB1`, `COMB2`: `ASK` modulation capacitor 用
- `VRECT`: rectifier output / main LDO input
- `VOUT`: main LDO output
- `VDD`: `1.1V` LDO output
- `VAA`: `2.5V` LDO output
- `VS`: `ASK` demodulation input
- `NTC`: coil temperature sensing input
- `ENB`: chip enable / disable input
- `SCL`, `SDA`: `I2C`
- `GPIO0`, `GPIO1`, `GPIO2`: programmable GPIO
- `INTB`: active-low open-drain interrupt output
- `IEXT`: active over-voltage clamper 用抵抗接続

### Ground domains

- `VSSA`: analog ground
- `VSSD`: digital ground
- `VSSP`: power ground

### Important pin notes

- `BOOT1/BOOT2` には各 `47 nF typ.` ceramic capacitor
- `NTC` は low-side NTC divider の center tap を接続
- `NTC` 未使用時は `VAA` へ `10kΩ` pull-up 必須
- `NTC` は未使用時に `ADCIN2` sampling input としても使える
- `VDD` は `1 μF` filtering capacitor 推奨
- `VAA` は `4.7 μF` filtering capacitor 推奨
- `ENB` 未使用時は GND 接続
- `SCL/SDA` は host supply rail への pull-up が必要

## 4. Electrical and thermal specifications (`pp.6-9`)

### 4.1 Absolute maximum ratings (`p.6`)

- 絶対最大定格の章
- `AC1/AC2/COMA/COMB` 系は高い電圧条件を扱う
- `GPIO/INTB/ENB/SCL/SDA` は `3.6V` 上限の low-voltage digital domain

### 4.2 Thermal characteristics (`p.6`)

- 熱特性表あり

### 4.3 Electrical characteristics (`pp.7-8`)

- `VRECT UVLO` 立上りしきい値 `2.5V typ`
- `VRECT UVLO` 立下りしきい値 `2.3V typ`
- `VOUT` programmable step size `25mV`
- `LDO` dropout `80mV typ @ 1A`
- output current limit / overcurrent protection の規定あり
- `AC1-AC2` operating frequency は `100kHz` 〜 `800kHz`
- `AC1-AC2` は `14Vpp`, `1.25A RMS` 目安

### 4.4 Recommended operating conditions (`p.9`)

- `VRECT` 推奨動作範囲 `4.5V` 〜 `13V`

### 4.5 Typical characteristics (`p.9`)

- efficiency / thermal performance 図あり

### 4.6 Start up waveforms (`p.9`)

- power-up と `ARC mode` waveform 図あり

## 5. Device description (`pp.10-11`)

- 受電動作の中心説明
- `ENB`, synchronous rectifier, `ASK/FSK`, `ARC`, protections, `GPIO/INTB`, `RRAM` の説明が入る

### 5.1 Chip-Enable Pin (`p.10`)

- `ENB = HIGH` で reset mode
- この状態では rectifier low-side switches on, high-side switches off
- `ENB` 開放で通常動作へ復帰

### 5.2 Synchronous rectifier (`p.10`)

- 4 個の N-MOS から成る H-bridge
- `AC1/AC2` を監視し最適駆動を選ぶ
- external output capacitor は ripple 抑制と transient energy の両方に必要

### 5.3 ASK and FSK communication (`p.10`)

- `COMA1/2` と `COMB1/2` を使う `ASK` modulation を説明
- modulation capacitor により ASK index を調整

### 5.4 ARC Mode (`p.10`)

- coupling 変動時に rectifier configuration を自動調整し、効率と spatial freedom を改善

### 5.5 Protections (`p.11`)

- 過電圧は少なくとも 3 段
  - `POVP`
  - `SOVP`
  - `HOVP`
- `POVP`
  - power-up 中に `VAA/VDD` が UVLO 未満のとき `VRECT > 14V` で動作
  - `VRECT < 11V` で解除
- `SOVP`
  - `VRECT > VOUT + SOVP threshold` で `IEXT` switch on
  - threshold は GUI で設定
- `HOVP`
  - `VRECT > HOVP threshold` で rectifier low-side on / high-side off
  - threshold は internal register で設定
- 過温は internal temperature, `NTC`, `TSHUT`
- 過電流は programmable current limit

### 5.6 GPIOx and INTB pins (`p.11`)

- `GPIO0-2` は NVM で機能割当できる programmable I/O
- input / output として使える
- push-pull / open-drain 選択可能
- `INTB` は host へ内部イベントを通知する open-drain interrupt output
- datasheet 上は `GPIO3` 相当の役割として扱われる

### 5.7 RRAM (`p.11`)

- `32kB RRAM`
- 複数回 erase/write 可能
- configuration parameter 保存に加え、custom firmware / protocol 調整用途の示唆あり
- standalone programming や GUI 経由書込みの説明あり

## 6. TX Mode (`p.12`)

- `STWLC38` は `Tx mode` にも設定可能
- `5W` 送電可能
- input voltage `5V` 〜 `12V`
- `VOUT` pin が Tx 時には `VIN` として動く
- full bridge inverter が primary coil + series capacitor を駆動
- switching frequency 変化で transmitted power を制御
- `VS` pin で `ASK` demodulation を扱う

## 7. Wireless power interface (`pp.13-14`)

- power transfer procedure の説明
- stages
  - `Selection`
  - `Ping`
  - `Digital ping`
  - `Identification & Configuration`
  - `Negotiation`
  - `Power transfer`
- `BPP` / `EPP` の flow-chart あり
- `STWLC38` は `Selection` から `Power Transfer` まで autonomously 進む
- `Power Transfer` 中は `Received-Power` と `Control-Error` packet を周期送信
- fatal `OVP/OCP/OTP` では automatic `End-Power-Transfer`

## 8. I2C interface (`pp.15-17`)

- host なしでも動作可能
- host 管理下では `SDA/SCL` を既存 `I2C bus` に接続
- device は `I2C slave`
- `100 kbps` / `400 kbps`
- `7-bit hardware address = 0x61`
- pins are up to `3.3V tolerant`
- single register write / page write / single read / page read をサポート
- register pointer auto-increment に対応

## 9. I2C register map (`pp.18-47`)

- internal registers を `I2C` で monitor / control 可能
- 未記載アドレスや空ビットは reserved で変更禁止
- `CFG` parameters は GUI から変更し、`memh` 再生成後に `NVM` へプログラムする前提

### 9.1 Chip / system information (`pp.18-19`)

- chip ID
- chip revision
- customer ID
- ROM ID
- NVM patch ID
- RAM patch ID
- configuration ID
- production ID
- operation mode
  - standalone debug
  - `Qi RX`
  - `Qi TX`
- system command
- system error information
  - core hard fault
  - HW watchdog
  - NVM boot / CRC / section error

### 9.2 Communication / DTS (`pp.19-20`)

- `RX DTS SEND`
- `RX DTS RCV`
- ADC request / response stream 関連

### 9.3 GPIO and RX interrupts (`pp.21-26`)

- `GPIO0-3` 機能設定
- `RX Interrupt Enable`
- `RX Interrupt Clear`
- `RX Interrupt Latch`
- `RX Interrupt Status`
- `system error`
- `output off`
- packet 送受信
- protection event などを個別ビットで扱う

### 9.4 RX commands (`p.27`)

- `RX command`
- `EPT reason` 指定
- `charge complete` などの code を送れる

### 9.5 RX VOUT / ARC / LDO / FOD (`pp.28-30`)

- `RX BPP VOUT SET`
- `RX EPP VOUT SET`
- `0.5V` 〜 `13.2V`, `0.1V step`
- `12V` は register value `73` の例
- `RX ARC mode configuration`
- input voltage loop / `UVLO` / auto VOUT enable
- `RX LDO DROP 0..3`
- `RX LDO current threshold`
- `RX BPP FOD configuration`
- `RX EPP FOD configuration`
- FOD current threshold, offset, coil series resistance を持つ

### 9.6 RX protections / EPT / VOUT OFF (`pp.30-32`)

- enable できる protection
  - ADC over-temperature
  - `NTC`
  - `TSHUT`
  - `OVP`
  - `SOVP`
  - short circuit
  - `UVLO`
  - ADC `OCP`
  - `OCP`
- 各 protection ごとに
  - interrupt update
  - `EPT`
  - `VOUT OFF`
  の選択肢がある

### 9.7 RX Power Transfer Contract / Qi config (`pp.33-35`)

- `RX Power Transfer Contract`
- `RX MAX POWER`
- `RX OB`
- `RX configuration Qi`
- `RX BPP FOD RF`
- `RX CE NUM/DENOM`
- `Q-factor` / resonance / negotiation 用パラメータ

### 9.8 ASK modulation and thresholds (`pp.35-36`)

- `ASK MOD Setting`
- `COMA/COMB` の modulation capacitor に対応
- 高電圧 / 低電圧 / 電流条件で modulation depth を設定
- `RX Protection threshold`
  - `RX OCP`
  - `RX HOVP`
  - `RX SOVP`
- 例として default 付近は `1.75A`, `16V`, `4V`

### 9.9 RX XID (`p.37`)

- extended device ID bytes

### 9.10 TX interrupt / TX config / TX EPT / PTC (`pp.38-47`)

- `TX Interrupt Enable`
- `TX Interrupt Clear`
- `TX Interrupt Latch`
- `TX Interrupt Status`
- events
  - `CE packet received`
  - packet sent
  - bridge mode changed
  - `FOD detect`
  - `OCP/OVP/system error`
  - `CEP timeout`
  - `RPP timeout`
- `TX FOD / timeout`
  - `PLOSS FOD threshold`
  - debounce count
  - retry count
- `TX custom control`
  - bridge mode
  - ping mode
- `EPT reason`
  - `TX HOST`
  - `TX RX EPT`
  - negotiation / packet / timeout error
- `PTC`
  - `AI`
  - `PCH`
  - extended protocol
  - guaranteed power
  - re-ping delay

## 10. Application information (`pp.48-52`)

### 10.1 Reference application (`p.48`)

- `Rx` と `RTx` の basic application diagram
- 完成設計ではなく baseline reference

### 10.2 Reference BOM (`pp.49-50`)

- `15W RTx` typical components list
- 抽出できた代表値
  - `LS 8uH` receiving coil
  - `CS 100nF/50V x5`
  - `CD 3.3nF/50V`
  - `CBOOT 47nF/50V`
  - `COMB 22nF/50V`
  - `COMA 10nF/50V`
  - `CVAA 4.7uF/25V`
  - `CVDD 1uF/16V`
  - `CRECT 10uF/25V`
  - `COUT 10uF/25V`
  - `TVS SMF13A`
  - `RCL 300R`
- wearable / TWS 向け低電力構成の別表あり

### 10.3 PCB routing guidelines (`p.51`)

- `VAA` / `VDD` filtering caps は IC 直近、top layer、短配線
- `CRECT` / `COUT` は `RCL` より優先して近接配置
- `AC1`, `AC2`, `VRECT`, `VOUT` は太配線
- `AC1` と `AC2` は近接配線で loop area 最小化
- bottom layer の GND integrity を維持し thermal performance を優先

### 10.4 External components selection (`pp.51-52`)

- 共振 capacitor は high `Q`, high `RMS current`, stable capacitance が必要
- `X5R/X7R/C0G` MLCC を想定
- `CS` は複数小型 MLCC 並列が実務的
- voltage rating は `50V` が一般に良い選択
- `ASK modulation capacitors` の初期値例
  - `22nF`
  - `10nF`
- `VRECT` over-voltage clamping は `RCL` + internal switch + `TVS`
- `AC1/AC2` の個別クランプも推奨
- coil thermal protection は `NTC pin` 経由

## 11. Reference schematic (`p.53`)

- typical application schematic
- 注記として、部品選択次第で動作と性能は制限されうる

## 12. Glossary/Abbreviations (`p.54`)

- `ADC`
- `ASK`
- `BPP`
- `CEP`
- `CFG`
- `EPP`
- `EPT`
- `FOD`
- `FSK`
- `ID`
- `PP`
- `RP`
- `SS`
- `XID`

## 13. Package information (`pp.55-57`)

- `WLCSP40 2.126 x 3.327 x 0.546`
- `0.4 pitch`
- `0.25 ball`
- package outline と mechanical data 表あり

## Back matter (`pp.58-63`)

- `p.58` revision history
- `pp.59-60` contents
- `p.61` list of tables
- `p.62` list of figures
- `p.63` legal notice

## Non-datasheet appended page (`p.64`)

- Mouser distributor page

## Relevance

- data brief より情報が深く、`CPU`, `memory`, `ADC`, `GPIO`, `INTB`, `ENB`, `register map`, `BOM`, `PCB routing`, `reference schematic` まで含む
- `STWLC38` は単なる受電ブラックボックスではなく、register-configurable power receiver / controller として扱う方が自然
- 一方で内蔵 MCU は `ROM resident firmware` を前提にした supervisor であり、製品固有ロジックを自由に実装する汎用 MCU と断定はできない
