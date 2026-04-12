---
name: kiutils-roundtrip-fix
description: kiutils の kicad_sch roundtrip カバレッジを自動で 100% に上げる。計測 → 最大インパクトの LOST トークン特定 → kiutils ソース修正 → 再計測のサイクルを自律的に繰り返す。
---

# kiutils Roundtrip Fix Agent

## 動作

このスキルは自律的に以下のサイクルを回す:

```
計測 → 分析 → 修正 → 検証 → 次へ
```

OVERALL COVERAGE が全ファイルで 100% になるか、修正不能な問題のみ残るまで続ける。

## 環境

- kiutils ソース: `/Users/mash/src/github.com/mvnmgrx/kiutils/src/kiutils/`
- ブランチ: `fix/roundtrip-fidelity`
- テスト対象: `hardware/kicad/cupwarmer-hw/*.kicad_sch`
- 検証スクリプト: `tmp/roundtrip_sch.py`
- 仕様: `wiki/raw/kicad-schematic-file-format-spec.md`

## サイクル手順

### Step 1: 計測

全ファイルで roundtrip テストを実行:

```bash
for f in hardware/kicad/cupwarmer-hw/*.kicad_sch; do
  python3 tmp/roundtrip_sch.py "$f" 2>&1
done
```

結果から以下を記録:
- 各ファイルの OVERALL COVERAGE %
- LOST トークンの一覧（トークンパスと出現数）
- CHANGED トークンの一覧

**100% なら終了。ユーザーに最終レポートを報告。**

### Step 2: 次の修正対象を決定

LOST/CHANGED トークンを以下の優先順で選ぶ:

1. **CRITICAL**: 値が反転するバグ（例: `show_name no` → `show_name`）
2. **HIGH / 広範囲**: 出現数が多い LOST トークン（影響ファイル数 × 出現数）
3. **HIGH / 単純**: フィールド追加だけで直る LOST トークン
4. **MEDIUM**: 形式差異（`hide yes` vs bare `hide`）

1つのトークン問題に集中する。複数を同時に直さない。

### Step 3: kiutils ソースを修正

修正対象ファイルを特定し、Read ツールで該当箇所を読む。

典型的な修正パターン:

#### パターン A: フィールド追加（LOST → OK）

対象の dataclass に Optional フィールドを追加:

```python
# 1. フィールド定義
excludeFromSim: Optional[bool] = None

# 2. from_sexpr() にパース追加
if item[0] == 'exclude_from_sim':
    object.excludeFromSim = True if item[1] == 'yes' else False

# 3. to_sexpr() に出力追加（None なら省略）
if self.excludeFromSim is not None:
    efs = 'yes' if self.excludeFromSim else 'no'
    expression += f'{indents}  (exclude_from_sim {efs})\n'
```

#### パターン B: 値パース修正（CHANGED → OK）

条件式を修正:

```python
# Before (バグ):
if item[0] == 'show_name': object.showName = True

# After (修正):
if item[0] == 'show_name':
    if len(item) > 1 and item[1] == 'no':
        object.showName = False
    else:
        object.showName = True
```

#### パターン C: 出力形式の修正

`to_sexpr()` が元ファイルと異なる形式で出力する場合:

```python
# Before: bare token
expression += f'{indents}  hide\n'

# After: KiCad v8+ 形式
expression += f'{indents}  (hide yes)\n'
```

### Step 4: 検証

修正後、最も影響のあるファイルで検証:

```bash
python3 tmp/roundtrip_sch.py hardware/kicad/cupwarmer-hw/cupwarmer-hw.kicad_sch
```

確認ポイント:
- 修正対象の LOST/CHANGED が消えたか
- 新たな LOST/CHANGED が増えていないか（回帰）
- OVERALL COVERAGE が上がったか

**回帰が発生した場合**: 修正を revert してやり直す。

### Step 5: 進捗報告してループ

ユーザーに 1行で報告:
```
✓ Schematic.generator_version 追加 — cupwarmer-hw.kicad_sch: 53.5% → 58.2%
```

Step 1 に戻る。

## 修正時のルール

1. **kiutils のパブリック API を壊さない**: 既存フィールドの型を変えない。新フィールドは Optional[T] = None にして後方互換を保つ
2. **1サイクル1トークン**: 修正は小さく保つ。複数を同時に直すと回帰の原因がわからなくなる
3. **from_sexpr と to_sexpr は必ずセットで修正**: パースだけ直して出力を忘れるとカバレッジが上がらない
4. **to_sexpr の出力位置は元ファイルの出現順に合わせる**: S-expression のトークン順序は KiCad が期待する順序がある
5. **テスト対象の .kicad_sch ファイルは絶対に編集しない**: テストデータは不変

## 修正対象ファイルの場所

kiutils ソースツリー (`/Users/mash/src/github.com/mvnmgrx/kiutils/src/kiutils/`):

| kiutils ファイル | 対応する kicad_sch 要素 |
|---|---|
| `schematic.py` | ルート `kicad_sch`（version, generator, generator_version, embedded_fonts, uuid, paper, lib_symbols, sheet_instances, symbol_instances） |
| `items/schitems.py` | SchematicSymbol, HierarchicalSheet, HierarchicalPin, Text, TextBox, Junction, NoConnect, BusEntry, Connection (wire/bus), LocalLabel, GlobalLabel, HierarchicalLabel |
| `items/common.py` | Property, Effects, Stroke, Font, Position |
| `symbol.py` | Symbol（lib_symbols 内の定義）, SymbolLib |

## 終了条件

- 全 4 ファイルで OVERALL COVERAGE 100% → 成功。最終レポートを出す
- LOST が残るが kiutils の設計上修正不可能 → ユーザーに説明して判断を仰ぐ
- 5 サイクル連続でカバレッジが上がらない → ユーザーに状況報告して方針転換を相談
