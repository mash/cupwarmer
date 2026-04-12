# STEVAL-WLC38RX BOM 抜粋

ソース: `wiki/raw/assets/st-steval-wlc38rx-um3154.pdf` (UM3154 Rev 2, Table 7-8)

## コイル

| Ref | Part Number | Manufacturer | Spec |
|-----|------------|-------------|------|
| COIL | **LD81FP008-1H** | Luxshare-ICT | 8 ±0.2 µH @100kHz, DCR 190mΩ, ACR 225mΩ |

コイルと PCB の接続: CNC Tech 610224 ワイヤペア

## IC

| Ref | Part | Manufacturer | Order Code |
|-----|------|-------------|------------|
| U1 | STWLC38JRM | STMicroelectronics | STWLC38JRM |

## キャパシタ（Qi 関連）

| Ref | Value | 用途 | Manufacturer | Order Code |
|-----|-------|------|-------------|------------|
| C1, C2, C3, C4, C21, C26, C28, C30, C31 | 100nF | 共振 / デカップリング (0603) | Wurth | 885012206095 |
| C7, C12 | 47nF | BOOT1/BOOT2 bootstrap (0603) | Wurth | 885012206093 |
| C8, C11, C15 | 22nF | COMB modulation (0603) | Wurth | 885012206091 |
| C9, C10 | 10nF | COMA modulation (0603) | Wurth | 885012206089 |
| C6, C13 | 3.3nF | CD diagnostic bypass (0603) | Wurth | 885012206086 |
| C14, C27, C33, C35 | 4.7µF | VAA decoupling (0603) | Murata | GRM188R61E475KE11D |
| C18, C19, C20, C24, C25 | 10µF | CRECT/COUT (0603) | Murata | GRM188R6YA106MA73D |
| C29 | 1µF | VDD decoupling (0603) | Wurth | 885012206052 |
| C16 | 1.5nF | (0603) | Wurth | 885012206084 |
| C36 | 100pF | (0603) | Wurth | 885012206077 |
| C41, C42 | 47pF | (0603) | Wurth | 885012006055 |
| C37, C38 | 390pF | (0603) | Samsung | CL10B391KB8NNNC |

## 保護部品

| Ref | Value | Manufacturer | Order Code |
|-----|-------|-------------|------------|
| D1, D2 | TVS SMF13A | Littelfuse | SMF13A |
| D11 | Schottky 1A | Diodes | B220A-13-F |

## 抵抗（Qi 関連）

| Ref | Value | 用途 | Manufacturer | Order Code |
|-----|-------|------|-------------|------------|
| R4, R5 | 200Ω | RCL clamp (0805) | Panasonic | ERJ-P06F2000V |
| R19-R25 | 4.7kΩ | I2C pull-up 等 (0603) | Panasonic | ERJ-3EKF4701V |
| R3, R7, R18, R30, R31 | 10kΩ | (0603) | Panasonic | ERJ-3GEYJ103V |
| RTC | NTC | (0603) | Vishay | NTCS0603E3104FXT |

## eval board 固有の違い（cupwarmer との差異）

- RCL = 200Ω×2 並列 (=100Ω)。DS14078 ref BOM は 300Ω → eval board は独自チューニング
- eval board は USB-C (FT260Q USB-I2C bridge) を搭載。cupwarmer では不要
- eval board は LED/スイッチ/ジャンパーを多数搭載。cupwarmer では不要
- コイルは Luxshare 製。Wurth WE-WPCC も互換候補
