# cupwarmer-hw

KiCad 10 向けの初回プロジェクト雛形。

## 含まれるもの

- `cupwarmer-hw.kicad_pro`
- `cupwarmer-hw.kicad_sch`
- `cupwarmer-hw.kicad_pcb`

## 方針

- まず KiCad で開ける最小プロジェクトを置く
- `STWLC38JRM` 周辺の具体回路は次段階で回路図へ入れる
- 既存の設計メモは以下を参照
  - `../../schematic/README.md`
  - `../../pcb/README.md`
  - `../../../docs/design-notes.md`

## 次にやること

1. footprint assignment を進める
2. `floorplan-v1.md` の zone に沿って主要部品を placement する
3. actual coil / ferrite geometry で placeholder guide を置き換える
4. PCB DRC と schematic parity を通す
