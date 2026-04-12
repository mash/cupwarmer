# WPC Qi v1.3 Power Delivery

- Source: [Qi Specification Power Delivery Version 1.3 (Wireless Power Consortium)](https://www.wirelesspowerconsortium.com/media/o3wi4bug/qi-v13-power-delivery.pdf)
- Accessed: 2026-04-11

## Notes

- 文書は `Power Profile` が送電側と受電側の互換レベルを決めるとしている。
- 利用可能なプロファイルとして `BPP PTx`、`EPP5 PTx`、`EPP PTx`、`BPP PRx`、`EPP PRx` を列挙している。
- `EPP5 PTx` は拡張系だが送電能力を `5W` に制限したプロファイルとして定義されている。
- 受電側は `Secondary Coil`、整流回路、通信変調器、出力切り離し、制御部などから構成される。
- 受電側のデュアル共振回路は `Secondary Coil` と 2 つの共振容量で構成され、電力伝送効率と位置検出に関与する。
- シールドは受電コイル全体を覆うべきで、 stray magnetic fields の影響に応じて追加シールドが必要になりうるとされる。

## Relevance

- Cup Warmer のコイル、共振コンデンサ、フェライトシールドの必要性を裏付ける。
- `BPP` と `EPP` の違いを、単なる出力値ではなく互換プロファイルとして理解するための基礎になる。
