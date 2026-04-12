# KiCad Schematic File Format (.kicad_sch) — 仕様と kiutils カバレッジ

原文: [KiCad Schematic File Format](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/) / [S-Expression Common](https://dev-docs.kicad.org/en/file-formats/sexpr-intro/)
Raw: [kicad-schematic-file-format-spec.md](raw/kicad-schematic-file-format-spec.md)

## 概要

KiCad の回路図ファイル (`.kicad_sch`) は S-expression 形式で記述される。KiCad v6 以降の共通フォーマット。v8/v10 で追加されたトークンは公式ドキュメント未反映のものがある。

## kicad_sch トークン一覧と kiutils 1.4.8 カバレッジ

### 凡例

- OK: kiutils が正しくパース・シリアライズする
- PARTIAL: パースするが一部欠落または不正確
- MISSING: 未実装
- BUG: 意味が変わるバグあり

### ルートレベル

| トークン | 型 | 必須 | kiutils | 備考 |
|---|---|---|---|---|
| `version` | int (YYYYMMDD) | YES | OK | |
| `generator` | string | YES | OK | |
| `generator_version` | string | NO | MISSING | v8+。フィールドなし |
| `uuid` | uuid | YES | OK | |
| `paper` | string/W H | YES | OK | PageSettings |
| `title_block` | nested | NO | OK | TitleBlock |
| `embedded_fonts` | yes/no | NO | MISSING | v8+。フィールドなし |
| `lib_symbols` | nested | NO | OK | Symbol リスト |

### lib_symbols > symbol

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `extends` | string | OK | |
| `pin_numbers` | nested/hide | PARTIAL | `(pin_numbers hide)` のみ。`(pin_numbers (hide no))` は item[1] がリストなので不一致 |
| `pin_names` | nested | OK | offset, hide 対応 |
| `exclude_from_sim` | yes/no | MISSING | v8+。Symbol クラスにフィールドなし |
| `in_bom` | yes/no | OK | |
| `on_board` | yes/no | OK | |
| `power` | bare | OK | |
| `property` | nested | OK → BUG | `show_name no` を True にパースする（修正済） |
| `property > do_not_autoplace` | yes/no | MISSING → OK | 修正済 |
| 子 `symbol` (unit) | nested | OK | 再帰パース |
| graphicItems (arc, circle, polyline, rectangle, text, text_box) | nested | OK | |
| `pin` | nested | OK | electrical type, graphic style, name, number, alternate |

### junction

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `at` | X Y | OK | |
| `diameter` | float | BUG | `object.color = item[1]` — diameter を color に代入している |
| `color` | R G B A | OK | |
| `uuid` | uuid | OK | |

### no_connect

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `at` | X Y | OK | |
| `uuid` | uuid | OK | |

### bus_entry

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `at` | X Y | OK | |
| `size` | X Y | OK | |
| `stroke` | nested | OK | |
| `uuid` | uuid | OK | |

### wire / bus

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `pts` | xy リスト | OK | |
| `stroke` | nested | OK | |
| `uuid` | uuid | OK | |

### polyline

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `pts` | xy リスト | OK | |
| `stroke` | nested | OK | |
| `uuid` | uuid | OK | |

### image

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `at` | X Y | OK | |
| `scale` | float | OK | |
| `layer` | string | OK | |
| `uuid` | uuid | OK | |
| `data` | base64 | OK | |

### text

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| text content | string | OK | |
| `exclude_from_sim` | yes/no | MISSING | v8+ |
| `at` | X Y angle | OK | |
| `effects` | nested | OK | |
| `uuid` | uuid | OK | |

### text_box

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| text content | string | OK | |
| `exclude_from_sim` | yes/no | MISSING | v8+ |
| `at` | X Y angle | OK | |
| `size` | W H | OK | |
| `stroke` | nested | OK | |
| `fill` | nested | OK | |
| `effects` | nested | OK | |
| `uuid` | uuid | OK | |

### label

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| text | string | OK | |
| `at` | X Y angle | OK | |
| `fields_autoplaced` | bare | OK | |
| `effects` | nested | OK | |
| `uuid` | uuid | OK | |

### global_label

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| text | string | OK | |
| `shape` | enum | OK | |
| `fields_autoplaced` | bare | OK | |
| `at` | X Y angle | OK | |
| `effects` | nested | OK | |
| `uuid` | uuid | OK | |
| `property` | nested | OK | |

### hierarchical_label

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| text | string | OK | |
| `shape` | enum | OK | |
| `at` | X Y angle | OK | |
| `effects` | nested | OK | |
| `uuid` | uuid | OK | |

### netclass_flag (v7+)

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| text | string | OK | |
| `length` | float | OK | |
| `shape` | enum | OK | |
| `fields_autoplaced` | bare | OK | |
| `at` | X Y angle | OK | |
| `effects` | nested | OK | |
| `uuid` | uuid | OK | |
| `property` | nested | OK | |

### symbol (schematic instance)

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `lib_id` | string | OK | |
| `lib_name` | string | OK | |
| `at` | X Y angle | OK | |
| `mirror` | x/y | OK | |
| `unit` | int | OK | |
| `exclude_from_sim` | yes/no | MISSING | v8+ |
| `in_bom` | yes/no | OK | |
| `on_board` | yes/no | OK | |
| `dnp` | yes/no | OK | v7+ |
| `fields_autoplaced` | bare | OK | |
| `uuid` | uuid | OK | |
| `property` | nested | OK → BUG | show_name 反転（修正済） |
| `pin` | number + uuid | OK | |
| `instances` | nested | OK | v7+ |

### sheet (hierarchical)

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `at` | X Y | OK | |
| `size` | W H | OK | |
| `exclude_from_sim` | yes/no | MISSING | v8+ |
| `in_bom` | yes/no | MISSING | v8+ |
| `on_board` | yes/no | MISSING | v8+ |
| `dnp` | yes/no | MISSING | v8+ |
| `fields_autoplaced` | bare | OK | |
| `stroke` | nested | OK | |
| `fill` | nested | OK | |
| `uuid` | uuid | OK | |
| `property` (Sheetname) | nested | OK → BUG | show_name 反転（修正済） |
| `property` (Sheetfile) | nested | OK → BUG | show_name 反転（修正済） |
| `pin` | nested | OK | HierarchicalPin |
| `instances` | nested | OK | v7+ |

### sheet_instances

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `path` | string | OK | |
| `page` | string | OK | |

### symbol_instances

| トークン | 型 | kiutils | 備考 |
|---|---|---|---|
| `path` | string | OK | |
| `reference` | string | OK | |
| `unit` | int | OK | |
| `value` | string | OK | |
| `footprint` | string | OK | |

## カバレッジサマリー (kicad_sch)

全トークン（v8+ の未ドキュメント含む）に対する kiutils 1.4.8 の対応状況:

| ステータス | 件数 |
|---|---|
| OK | ~75 |
| MISSING | 9 (generator_version, embedded_fonts, exclude_from_sim ×5箇所, sheet の in_bom/on_board/dnp) |
| BUG | 2 (show_name 反転, junction diameter→color 代入) |
| PARTIAL | 1 (pin_numbers hide no) |
| **合計** | ~87 |
| **カバレッジ** | **~86%** (OK / 全体) |

## 修正が必要な項目（優先順）

1. **BUG: Property.show_name no が反転する** — 意味が変わる。修正済み（common.py）
2. **BUG: Junction.diameter が color に代入される** — フィールド名の typo
3. **MISSING: generator_version** — Schematic クラスにフィールド追加
4. **MISSING: embedded_fonts** — Schematic クラスにフィールド追加
5. **MISSING: exclude_from_sim** — Symbol, SchematicSymbol, HierarchicalSheet, Text, TextBox に追加
6. **MISSING: sheet の in_bom, on_board, dnp** — HierarchicalSheet に追加
7. **PARTIAL: pin_numbers (hide no)** — ネストリスト形式のパース対応
