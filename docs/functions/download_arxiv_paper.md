# download_arxiv_paper

## 概要
arXivに登録されている学術論文をタイトルで検索し、最も関連性の高い1件の論文の「PDFファイル」と「TeXソースコード（.tar.gz）」を自動的に同時ダウンロードするMCPツールです。

ファイルは以下の階層に整理されて保存されます。
- PDF: `tmp/arxiv/pdf/`
- TeXソース（展開前アーカイブおよび展開先）: `tmp/arxiv/tex/`
- 結合済みテキストデータ: `tmp/arxiv/raw_text/`

## 使い方（How to use it）
MCPクライアント（AI等）を介してサーバーから `download_arxiv_paper` ツールを呼び出します。引数として検索したい論文のタイトルを指定してください。

### 引数
- `title_query` (str): 検索したい論文のタイトル（例: `"Attention Is All You Need"`）

### 戻り値
- 成功時: ダウンロード・展開の成功メッセージ（`tmp/`からの結合テキスト保存先の相対パスを含む）と、展開された全てのTeXソースコード（`.tex`, `.bbl`）の中身を結合した全テキストデータ。
- 失敗時（見つからないなど）: 論文が見つからなかった旨、もしくは例外エラーのメッセージ。

### 動作例
```python
# MCPツールとしての呼び出し例
# download_arxiv_paper(title_query="Attention Is All You Need")
# -> "論文 'Attention Is All You Need' のダウンロード・展開に成功しました。\n(結合テキスト保存先: arxiv/raw_text/Attention Is All You Need.txt)\n以下は抽出されたTeXソースコードの全内容です：\n\n--- Start of main.tex ---\n..."
```

## 注意事項
- 指定されたタイトルに基づく検索結果がない場合は、エラーメッセージが返されます。
- TeXソースコードは複数のファイル（`.tex`本体や画像ファイル等）が同梱された `.tar.gz` 形式のアーカイブとしてダウンロードされます。
- ファイルは `tmp/arxiv/` ディレクトリ配下に保存されるため、必要に応じて定期的なクリーンアップを行ってください。
