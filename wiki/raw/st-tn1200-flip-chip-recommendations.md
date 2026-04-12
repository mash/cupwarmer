# ST TN1200 Flip-Chip Recommendations

- Source: [TN1200: IPAD, micro-bump Flip Chip: package description and recommendations for use (STMicroelectronics)](https://www.st.com/resource/en/technical_note/dm00151294-micro-bump-flip-chip-package-description-and-recommendations-for-use-stmicroelectronics.pdf)
- Accessed: 2026-04-11

## Notes

- 文書は `200 µm` 以上ピッチの flip-chip 向け一般推奨資料。
- ST は、この種の flip-chip は `special or additional process steps required` なしで PCB 実装でき、`underfill` も必須ではないと説明している。
- `compatible with existing pick and place equipment` としている。
- `mini-stencil and solder paste` が placement の preferred solution と説明されている。
- リワークでは、`soldering irons should be avoided`、側面やバンプ面を押す工具も避けるべきとしている。

## Relevance

- `STWLC38JRM` の個別実装ガイドではないが、ST の WLCSP / flip-chip 実装思想の一般論として使える。
- 外注実装前提では、underfill 必須ではないこと、通常の pick-and-place と reflow に載ることが重要。
