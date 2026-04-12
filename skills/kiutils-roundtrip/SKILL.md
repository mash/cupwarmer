---
name: kiutils-roundtrip
description: kiutils の roundtrip 忠実度を検証し、カバレッジを計測・改善する。.kicad_sch ファイルを kiutils で読み書きし、トークン単位で差分を検出して数値レポートを出す。kiutils の修正 → 再計測 → 100% を目指すサイクルで使う。
---

# kiutils Roundtrip Validation

## 目的

kiutils で KiCad ファイルを読み → 書き戻したとき、意味のあるトークンが失われないことを検証する。カバレッジを数値で出し、修正のたびに回帰を確認する。

## 前提

- kiutils ソース: `/Users/mash/src/github.com/mvnmgrx/kiutils/src/kiutils/`
- テスト対象: `hardware/kicad/cupwarmer-hw/*.kicad_sch`
- 検証スクリプト: `tmp/roundtrip_sch.py`
- 仕様: `wiki/raw/kicad-schematic-file-format-spec.md`
- カバレッジ分析: `wiki/source-kicad-schematic-file-format-spec.md`

## ワークフロー

### 1. 現状計測

全 .kicad_sch ファイルに対して roundtrip を実行し、ベースラインを記録する。

```bash
for f in hardware/kicad/cupwarmer-hw/*.kicad_sch; do
  echo "=== $(basename $f) ==="
  python3 tmp/roundtrip_sch.py "$f" 2>&1 | grep -E '(OVERALL|LOST|CHANGED|SUMMARY|Top-level|UUID|Token)'
  echo
done
```

### 2. 問題を特定

検証スクリプトの出力から LOST / CHANGED を抽出する。典型的な問題カテゴリ:

| カテゴリ | 例 | 深刻度 |
|---|---|---|
| LOST (トークン欠落) | `generator_version`, `embedded_fonts`, `exclude_from_sim` | HIGH — フィールド追加が必要 |
| CHANGED (値反転) | `show_name no` → `show_name` | CRITICAL — 意味が変わる |
| CHANGED (format差分) | 整形、数値精度 | LOW — 意味は同じ |

### 3. kiutils を修正

修正は `/Users/mash/src/github.com/mvnmgrx/kiutils` の `fix/roundtrip-fidelity` ブランチで行う。

修正対象ファイル（.kicad_sch 関連）:
- `src/kiutils/schematic.py` — Schematic クラス
- `src/kiutils/items/schitems.py` — SchematicSymbol, HierarchicalSheet, Text 等
- `src/kiutils/items/common.py` — Property, Effects 等
- `src/kiutils/symbol.py` — Symbol (lib_symbols 内)

修正パターン:

**フィールド追加** (LOST → OK にする):
1. データクラスにフィールドを追加（Optional[type] = None）
2. `from_sexpr()` にパースロジックを追加
3. `to_sexpr()` に出力ロジックを追加（None なら出力しない）

**値解釈修正** (CHANGED → OK にする):
1. `from_sexpr()` の条件式を修正（例: `yes`/`no` の正しいパース）
2. `to_sexpr()` の出力形式を修正

### 4. 再計測

```bash
python3 tmp/roundtrip_sch.py hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

### 5. 繰り返し

OVERALL COVERAGE が 100% になるまで 2–4 を繰り返す。

## 検証スクリプトの出力の読み方

```
=== Top-level tokens ===
  generator_version   LOST (was: 10.0)    ← フィールドが kiutils にない
  embedded_fonts      LOST (was: no)      ← フィールドが kiutils にない
  version             OK                  ← 正常に保持
  
=== UUID-bearing elements ===
  sheet    total=3  ok=0  changed=3  lost=0  (0.0%)  ← 3枚のシート全部で差分あり
    uuid=...: child 'exclude_from_sim' LOST           ← このトークンが落ちている
    uuid=...: child 'property' CHANGED                ← property の内容が変わった

=== Token inventory ===
  LOST  kicad_sch > sheet > exclude_from_sim  orig=3  ← 3回出現するトークンが全部消えた

=== SUMMARY ===
  OVERALL COVERAGE: 53.5%                             ← 目標は 100%
```

## 現在の kicad_sch 残課題一覧

ref: `wiki/source-kicad-schematic-file-format-spec.md`

### CRITICAL (意味変化)
- [ ] `Property.show_name no` の反転 → common.py 修正済（fix/roundtrip-fidelity ブランチ）
- [ ] `Junction.diameter` が `color` に代入される → schitems.py

### HIGH (トークン欠落)
- [ ] `Schematic.generator_version` — schematic.py にフィールド追加
- [ ] `Schematic.embedded_fonts` — schematic.py にフィールド追加
- [ ] `SchematicSymbol.exclude_from_sim` — schitems.py にフィールド追加
- [ ] `HierarchicalSheet.exclude_from_sim` — schitems.py にフィールド追加
- [ ] `HierarchicalSheet.in_bom` — schitems.py にフィールド追加
- [ ] `HierarchicalSheet.on_board` — schitems.py にフィールド追加
- [ ] `HierarchicalSheet.dnp` — schitems.py にフィールド追加
- [ ] `Text.exclude_from_sim` — schitems.py にフィールド追加
- [ ] `TextBox.exclude_from_sim` — schitems.py にフィールド追加
- [ ] `Symbol.exclude_from_sim` (lib_symbols内) — symbol.py にフィールド追加

### MEDIUM (明示デフォルト)
- [ ] `Symbol.pin_numbers (hide no)` — symbol.py パース改善
- [ ] `Effects.hide yes` vs bare `hide` — common.py 形式差異

## ローカル kiutils の使い方

検証スクリプトは自動的にローカルの kiutils ソースを優先ロードする:
```python
LOCAL_KIUTILS = os.path.expanduser("~/src/github.com/mvnmgrx/kiutils/src")
sys.path.insert(0, LOCAL_KIUTILS)
```

修正をローカルに書いて即座に検証スクリプトで確認できる。pip install は不要。
