# ST STEVAL-WLC38RX Receiver Board Press Release

- Source: [Transmitter and receiver evaluation boards from STMicroelectronics accelerate development of Qi wireless chargers - ST News](https://newsroom.st.com/media-center/press-item.html/n4548.html)
- Accessed: 2026-04-11

## Notes

- ST は 2023-11-22 に `STEVAL-WLC38RX` を発表。
- `STWLC38` ベースの `5W/15W` receiver board と説明している。
- 最大 `15W` の `Qi-compliant` prototype and test を加速する目的。
- `Arm Cortex-M0+` コア、内蔵 NVM、熱管理と電気保護を備える。
- Mouser 掲載の data brief では `Qi 1.3` 準拠、`5W BPP` と `15W EPP` の両対応と読める。
- `Wireless Charging - Receiver` の評価ボードとして扱われている。
- `I2C` による設定変更が可能。
- オンボード `USB-to-I2C bridge` を備える。
- `STSW-WPSTUDIO` GUI で監視・制御できる。
- `Adaptive rectifier configuration (ARC)` を持つ。
- `Accurate voltage/current measurement for FOD` とある。
- `On-chip thermal management and protections` を持つ。

## Relevance

- `STWLC38JRM` 自体は `WLCSP40` だが、評価ボード起点ならそのまま熱検証へ入れる。
- Cup Warmer の初期段階で「IC実装」より「熱と FOD の成立性」を先に見る道筋になる。
