---
title: STWLC38 Internal CPU and External MCU
type: analysis
tags: [stwlc38, stwlc38jrm, mcu, i2c, interrupt, cup-warmer]
sources: [st-stwlc38-datasheet-ds14078.md, st-stwlc38jrm-data-brief-db5568.md, st-stwlc38jrm-15w-wireless-power-receiver.md]
created: 2026-04-12
updated: 2026-04-12
---

`STWLC38` は内蔵 `Cortex-M0+` を持ち、初版 cup warmer では外部 `MCU` なしで進める前提を取れる。

## datasheet で増えた確定情報

2025 年の data brief で見えていたのは `32-bit, 64 MHz Arm Cortex-M0+`, `I2C`, `RRAM`, `FOD`, `4-12V programmable output` までだった。  
今回の datasheet では、さらに次が見えた。

- `32kB RRAM`
- `16kB SRAM`
- `64kB ROM`
- `10-bit ADC`
- `GPIO0..2`
- `INTB`
- `ENB`
- `I2C register map`
- RX protection / `EPT` / `VOUT OFF` の細かな制御
- reference schematic と PCB routing guidelines

これで、`STWLC38` が「CPU 内蔵の受電 IC」であるだけでなく、「host からレジスタ監視と設定ができる受電制御 IC」であることがかなり明確になった。

## 内蔵 CPU がやっていること

datasheet 自身が、内蔵 `32-bit core MCU` はデバイス全体の supervisor であり、次を担うとしている。

- transmitter との通信維持
- `Qi` 仕様順守
- 効率最適化
- 負荷とデバイス自身の監視と保護

ここで重要なのは、これらが `ROM` にある resident firmware によって実行されると書かれている点である。  
つまり、内蔵 CPU は「空の汎用 MCU」ではなく、まず ST の受電ファームウェアを走らせるためのコアである。

## 単体でできること

datasheet の記述だけでも、`STWLC38` 単体でかなり多くのことができる。

- `Qi 1.3` 受電
- `4-12V` の `VOUT` 制御
- `FOD`
- `OVP`, `OCP`, `UVLO`, `SCP`, thermal shutdown
- `NTC` を使った coil thermal protection
- `INTB` によるイベント通知
- `I2C` 経由の設定、監視、割り込み処理
- `RRAM` への設定保存と power-up 時の自動読込

この意味では、`STWLC38` は host なしでも stand-alone 受電器として成立する。

## それでも弱くなる点

Cup Warmer はスマートフォン充電とは違い、負荷がヒーターである。  
受電を成立させるだけでは足りず、「どう熱を使うか」のポリシーが別に必要になる。

このプロジェクトで欲しいロジックは次である。

- ヒーター `PWM` デレート
- カップなし急上昇検出
- `NTC_TOP` と `NTC_PCB` の 2 点監視
- センサ断線 / 短絡の異常判定
- cup warmer としての停止条件の決定

datasheet からは `NTC` 1 系統、受電保護、割り込み、レジスタ設定までは見えるが、製品固有の熱制御ポリシーを自由に書けるとは読めない。  
したがって、外部 `MCU` を外すなら、初版の要求もそこに合わせて絞る必要がある。

## 外部 MCU を減らせるか

減らせる。だが、残るのは「固定的な加熱器」に近い。

外部 `MCU` を省いた場合に成立しやすいのは次である。

- `STWLC38` による受電
- 固定 `VOUT`
- `NTC` 1 系統の coil protection
- `F1` のような独立ハード遮断
- 必要なら host なしの autonomous 動作

一方で、次は弱くなる。

- top plate 温度の直接制御
- board hotspot を見たデレート
- ヒーター `PWM`
- カップ有無や熱上昇速度による判断
- 複数条件の論理合成による停止

なので「温かくなるデモ」はできても、「製品として気持ちよく制御された cup warmer」にはなりにくい。

## このプロジェクトへの具体的な含意

回路図で先に固定すべきなのは次である。

- `I2C_SCL`
- `I2C_SDA`
- `ENB` を使うかどうか
- `NTC` 系の責務分担
- `I2C` service header を残すかどうか
- `HEATER_CTRL` の駆動源
- `I_HEATER_MON` を残すかどうか

さらに、GND は datasheet 自体が `VSSA`, `VSSD`, `VSSP` を分けているので、少なくとも KiCad 上では `PGND` と静かな return を意識しておくべきである。

## 実務的な結論

- `STWLC38` の内蔵 CPU は弱いわけではない
- ただしそれは主に受電制御と保護のための CPU と読むべきである
- 初版設計では外部 `MCU` を載せない方針を取れる
- その代わり、初版は `STWLC38` の stand-alone 動作、固定 `VOUT`、独立ハード遮断、service `I2C` に要求を絞るべきである
- 製品固有の温調ロジックは後段の検討対象として分離した方がよい

## 関連ページ

- [ST STWLC38JRM 要約](source-st-stwlc38jrm-15w-wireless-power-receiver.md)
- [STWLC38JRM Outsourced Assembly](stwlc38jrm-outsourced-assembly.md)
- [Qi 15W Receiver Options](qi-15w-receiver-options.md)
