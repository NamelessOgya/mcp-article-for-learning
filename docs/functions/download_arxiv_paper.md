# download_arxiv_paper

## 概要
arXivに登録されている学術論文をタイトルで検索し、最も関連性の高い1件の論文のPDFファイルを自動的にダウンロードするMCPツールです。保存先はプロジェクト内の `tmp/arxiv/` ディレクトリになります。

## 使い方（How to use it）
MCPクライアント（AI等）を介してサーバーから `download_arxiv_paper` ツールを呼び出します。引数として検索したい論文のタイトルを指定してください。

### 引数
- `title_query` (str): 検索したい論文のタイトル（例: `"Attention Is All You Need"`）

### 戻り値
- 成功時: ダウンロードされた論文のタイトルと、保存先の絶対パスを含む成功メッセージ。
- 失敗時（見つからないなど）: 論文が見つからなかった旨、もしくは例外エラーのメッセージ。

### 動作例
```python
# MCPツールとしての呼び出し例
# download_arxiv_paper(title_query="Attention Is All You Need")
# -> "ダウンロード成功: 論文 'Attention Is All You Need' を /path/to/tmp/arxiv/Attention Is All You Need.pdf に保存しました。"
```

## 注意事項
- 指定されたタイトルに基づく検索結果がない場合は、エラーメッセージが返されます。
- PDFは `tmp/arxiv/` ディレクトリ配下に保存されるため、必要に応じて定期的なクリーンアップを行ってください。
