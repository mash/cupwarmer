# Wiki スキーマ

[LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) パターンに従った、LLM が管理する個人ナレッジベース。

## ディレクトリ構成

```
raw/            # Markdown テキスト（grep 検索対象）。基本的に不変。
raw/assets/     # バイナリ原本（PDF・画像・Office ファイル等）
wiki/           # LLM が生成・管理する Markdown ファイル
wiki/index.md   # 全 wiki ページのカタログ
wiki/log.md     # 時系列の操作ログ
```

PDF はバイナリを `raw/assets/<name>.pdf` に保存し、テキスト抽出可能なら同名の `raw/<name>.md` を並置する（grep 用）。画像は `raw/assets/` のみ。

## ページフォーマット

frontmatter は配置パスで 2 種類に分かれる。**`raw/*.md` には形式 A、`wiki/*.md` には形式 B** を必ず使う。

### 形式 A: `raw/*.md`（1 次情報）

```yaml
---
title: ドキュメントタイトル
source: https://example.com/article  # 元 URL または raw/assets/ パス。重複検知のキー。
fetched: YYYY-MM-DD                  # 任意
format: PDF (37 pages)               # 任意
---
```

`source`（**単数**）は会話中のテキスト貼り付けで外部出典がない場合を除き必須。

### 形式 B: `wiki/*.md`（派生ページ。全タイプ共通）

```yaml
---
title: ページタイトル
type: source-summary | entity | concept | analysis | overview
tags: [tag1, tag2]
sources: [wiki/source-file-1.md, wiki/source-file-2.md]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

`sources`（**複数**）の中身はページタイプで変わる:

階層: `raw or 外部URL ← source-summary ← entity / concept / analysis / overview`

- **source-summary**: 出典そのものを参照。`raw/<file>.md` `raw/assets/<file>.<ext>`。
- **entity / concept / analysis / overview**: 自身を裏付ける source-summary を `wiki/source-xxx.md` 形式で参照。raw への参照は source-summary 側が担う。
- 出典なし、または言及履歴のみで追跡する場合は `[]`。

**パス表記規則**: `sources:` の値はリポジトリルート（`wiki/` プロジェクト直下）からの相対パス。`raw/` `raw/assets/` `wiki/` のいずれかのプレフィックスを必ず付ける。bare ファイル名や `assets/` 単独は禁止。外部 URL は `https://...` をそのまま記載。

## ページタイプ

- **source-summary**: 単一の raw ソース（または外部 URL ソース）の要約
- **entity**: 人物・組織・会社・製品その他の固有名詞
- **concept**: アイデア・技術・フレームワーク・抽象的トピック
- **analysis**: 複数ソース・複数エンティティ／コンセプトにまたがる深掘り・統合・比較分析
- **overview**: 広いトピック領域を俯瞰するページ

## 命名規則

- ファイル名: 小文字、スペースはハイフン（例: `machine-learning.md`）
- source-summary: `source-` プレフィックス（例: `source-attention-is-all-you-need.md`）

## 相互リンク

`[ページタイトル](filename.md)` で積極的にリンクする。ページ間のつながりはページそのものと同じくらい価値がある。

## 取り込み (Ingest)

### 重複チェック（必ず最初に実行）

1. **URL 全体ではなくユニーク ID 部分**（プレスリリース番号、記事スラッグ等）を `raw/` および `wiki/` ツリー**全体**に対して `grep -rn` で検索する。表記揺れ（末尾スラッシュ・クエリ・www 有無）を吸収し、entity 言及履歴に直接 URL が書かれているケースも検出するため、対象ディレクトリを限定しない。
   - 主なヒット先: `raw/*.md` の `source:`、`wiki/source-meeting-*.md` の `sources:`、entity ページ等の言及履歴本文中の URL
2. ヒット時:
   - **同一ソースの再取り込み**: 既存ファイル名を提示し 3 択でユーザー確認:
     1. 最新版を再取得して更新
     2. 既存の要約のみ提示
     3. スキップ
   - **同一サイトの別ページ**（URL 異なる）: 新規取り込み

### 入力種別と保存先

| 入力 | raw 保存 | source-summary の `sources:` |
|---|---|---|
| 外部 Web コンテンツ（記事・ブログ・プレスリリース・公開論文等） | `WebFetch` → `raw/` に Markdown 保存 | `[raw/<file>.md]` |
| 外部公開 PDF | バイナリを `raw/assets/<name>.pdf`、テキスト抽出版を `raw/<name>.md` | `[raw/<name>.md, raw/assets/<name>.pdf]`（両方記載） |
| ローカルバイナリ（ユーザー指定 PDF・画像等） | `raw/assets/` にコピー | `[raw/assets/<file>]` |
| 会話中のテキスト貼り付け | `raw/` に Markdown 保存 | `[raw/<file>.md]` |
| 既に `raw/` にあるファイル | 保存不要 | `[raw/<file>.md]` |

迷ったらユーザーに「正本の在りか」を確認する。

### 共通ルール

**raw 保存時**:
- ファイル名は内容を反映した小文字ハイフン区切り（例: `ev-charging-guide-2026.md`）
- 本文中の出典タイトル・名称は元 URL リンクで埋め込む（例: `[製品名](https://example.com/product)`）
- **網羅性**: 章立てがあるソースは要約せず全セクションを書き出す。後の grep ヒットを優先し省略しない。

**アクセス権**:
- **外部公開 URL でアクセス不可**（404 / 有料 / ログイン必須等）: raw も source-summary も**作らない**。ユーザーに失敗を報告。

### wiki 反映手順

1. ソースを全文読む
2. 主要ポイントをユーザーと議論する
3. `wiki/source-<名前>.md`（source-summary）を作成
4. 関連する entity / concept ページを**該当する全てに対して**作成または更新する（`sources:` に source-summary を追加。複数ページ可）。**紐付け先が無いケースは、対応する concept か overview をその場で新設する**（孤立 source-summary は禁止）
5. 影響を受けるページに相互リンクを追加
6. `wiki/index.md` の該当カテゴリ（後述）を更新
7. `wiki/log.md` にエントリを追記

### entity ページ

人物・組織・会社・製品が登場したら entity ページを作成または更新する（**新規作成より既存ページへの追記を優先**）。

**新規作成の閾値**: cupwarmer 開発との関係（部品メーカー・製造委託先・規格団体等）が文脈から特定できる、または複数ソースで言及されている場合のみ。プレスリリース等で単に名前が列挙されているだけの場合は entity 化せず、source-summary 内の記述に留める。

標準セクション:

- `## 概要`: 何の人物／組織／製品か（初出時に記載、以降更新）
- `## cupwarmer 開発との関係`: 採用部品・製造委託・関連規格など（関係がない場合は省略可）
- `## 言及履歴`: ソースごとの文脈を**降順（新しい順）**で記録。新規エントリは末尾ではなく**先頭**に追記する

```markdown
## 言及履歴

- [YYYY-MM-DD] [ソース要約タイトル](source-xxx.md) — 文脈の要約
```

## クエリ (Query)

1. `wiki/index.md` を読み関連ページを見つける
2. 関連ページを読む
3. wiki ページへの引用付きで回答を統合する
4. 会話中に既存 wiki にない新しい知見が得られたら、自動でページを作成・更新する（重複するだけなら更新しない）

## リント (Lint)

ヘルスチェック依頼時:

- ページ間の矛盾を探す
- 古くなった記述を見つける
- 被リンクのない孤立ページを特定する
- 言及されているが専用ページのない重要コンセプトを記録する
- 不足している相互リンクを見つける
- 調査すべき新しい問いやソースを提案する

## インデックス (`wiki/index.md`)

**source-summary は index に載せない**（出典の参照は entity / concept / analysis / overview の `sources:` から辿るため、index で重複させない）。残り 4 タイプのみページタイプ別カテゴリで掲載（リンク + 一行要約 + ページタイプ）。**カテゴリはページタイプと 1:1 対応**:

```markdown
## Entities            # type: entity
## Concepts            # type: concept
## Analyses            # type: analysis
## Overviews           # type: overview
```

該当ページがないカテゴリは省略可。新カテゴリは作らない（新タイプを足す前提でない限り）。取り込みのたびに更新する。

## ログ (`wiki/log.md`)

追記専用の時系列記録:

```
## [YYYY-MM-DD] 操作 | タイトル
行った内容の簡潔な説明。
```

## 運用ノート

- LLM が wiki コンテンツを執筆・管理する。ユーザーはソースのキュレーションと指示を行う。
- 新情報が既存 wiki と矛盾する場合、矛盾を明示的にフラグして影響ページを更新する。
- トピックが大きく重複する場合、新規ページ作成より既存ページの更新を優先する。
- **作業用一時ファイルは `./tmp/` を使わない**。このリポジトリは Google Drive 同期下にあり、`./tmp/` 配下も同期対象になる。一時ファイルは OS の tmp ディレクトリ（`$TMPDIR` または `/tmp`）配下に作成すること（例: `/tmp/normalize_sources.py`）。グローバル CLAUDE.md の `./tmp/` 規約はこのリポジトリでは無効。
