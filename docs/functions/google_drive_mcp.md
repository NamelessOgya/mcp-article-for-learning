# Google Drive MCP Server

## 機能 (What it does)
Google Drive上にある指定されたファイル（Googleドキュメントやスプレッドシート、さらには論文などのPDFファイル等も）を検索およびダウンロードし、ローカルの `tmp/` フォルダに保存するMCPサーバーです。

- `list_drive_files(folder_id)`: ドライブ内の「フォルダ」や「ファイル」を一覧取得してファイルIDを見つけ出します。
- `download_drive_file(file_id)`: 指定したIDのファイルをダウンロードします。

ファイルのMIMEタイプ（種類）に応じて、自動で「エクスポート」と「そのままのダウンロード」を賢く切り替えます。
- **Google Docs** ⇨ LLMがテキストとして読み込みやすいよう、プレーンテキスト (`.txt`) として自動エクスポート
- **Google スプレッドシート** ⇨ `.csv` としてエクスポート
- **通常の論文PDFなどの外部ファイル** ⇨ `.pdf` としてそのままダウンロード

## 事前準備
1. [GCPコンソール](https://console.cloud.google.com/)からGoogle Drive APIを有効化。
2. 「OAuth クライアント ID」を作成し、JSONファイルをダウンロード。
3. ダウンロードしたJSONファイルを `credentials.json` という名前で、プロジェクトルートに配置しておく。

## 使い方 (How to use it)

### 初回認証（トークン生成）
Dockerコンテナ内のターミナルで手動で以下のMCPスクリプトを実行し、ブラウザ認証を通します。
```bash
python src/mcp/google_drive_mcp.py
```
するとターミナルに以下のようなURLが表示されます。
`Please visit this URL to authorize this application: https://accounts.google.com/...`
ホストOSのブラウザからこのURLにアクセスし、Googleアカウントでログインと許可を行います。最後に表示された「認証コード」をターミナルに貼り付けてEnterを押すと認証が完了します。
認証成功後、プロジェクトルートに `token.json` が生成され、次回からは全自動でアクセスできるようになります。

### AIと連携して使う
`playground/` にあるようなLLMエージェントクライアントで読み込ませるか、Claude Desktopなどの設定ファイルに以下のようなコマンドを追加します。
```python
# LLMスクリプト用の起動パラメータ
server_params = StdioServerParameters(
    command="python",
    args=["src/mcp/google_drive_mcp.py"],
)
```

LLMには**「GoogleドライブのファイルID `xxxxxxxxxxxxxx` の論文PDFをダウンロードして、中身の要約を作ってください」**と指示を出すだけで、LLMが自らダウンロードから解析まで繋げてくれるようになります。
※ファイルIDは、Googleドライブでそのファイルを開いた時のURL（`https://docs.google.com/document/d/ココ/edit`）の部分です。
