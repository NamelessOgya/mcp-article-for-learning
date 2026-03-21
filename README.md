# MCP Article for Learning

PythonとDockerを用いて、**MCP（Model Context Protocol）**の仕組みや、LLM（Gemini）が自律的にツールを利用する**ReActエージェント**の挙動を安全に学習・実験するための開発リポジトリです。

## 1. 概要とディレクトリ構成

このプロジェクトは、ホスト環境（ご自身のPCやVM）を汚さずに開発できるようDockerコンテナ化されています。ホストのUID/GIDをコンテナに引き継ぐよう設定されているため、VSCode等から快適にファイルの編集が可能です。

*   **`playground/`**: 🌟 MCP学習用サンプルコード集
*   **`src/`**: システムのコアとなるモジュール群
    *   `mcp/`: 自作MCPサーバーの実装 (`local_fs_mcp.py`, `google_drive_mcp.py`)
    *   `llm/gcp/`: Gemini連携クライアントやGCP Secret Manager連携モジュール
*   **`tmp/`**: サンプルコードやMCPサーバーによって自動生成されるファイル置き場
*   **`scripts/`**: コンテナ起動・運用を補助するコマンド群
*   **`test/`**: `pytest` による各モジュールの単体テスト群

---

## 2. 環境の起動・停止方法

Dockerを利用して、隔離された安全な実験環境を立ち上げ・破棄します。

**① スクリプトへの実行権限付与（初回のみ）**
```bash
chmod +x scripts/*.sh
```

**② コンテナの起動**
```bash
./scripts/start.sh
```

**③ コンテナの中に入る**
```bash
./scripts/enter.sh
```
※ 以降のコマンド（スクリプトの実行など）は、すべてこのコンテナの中で行います。作業が終わって元の手元のターミナルに戻る場合は `exit` を実行します。

**④ コンテナの停止（お片付け）**
作業が完全に終了し、Dockerコンテナを破棄したい場合は、ホスト側（コンテナから `exit` で抜けた状態）のターミナルで以下を実行します。
```bash
./scripts/stop.sh
```
※ コンテナを停止・破棄しても、ホスト側のディレクトリをマウントしているため、`tmp/` に自動作成されたファイルやご自身で編集したコード等は消えずにそのまま手元に残ります。

---

## 3. 事前準備 (APIキーの設定)

LLM（Gemini）を利用するスクリプトを動かすために、リポジトリのルートディレクトリに `.env` というファイルを作成し、以下の**どちらか**の方法で認証情報を設定してください。

**方法A（手軽・ローカル開発向け）**
`.env` の中に直接APIキーを記述します。
```env
GEMINI_API_KEY=AIza...
```

**方法B（安全・GCP運用向け）**
APIキーをGCP Secret Managerに預け、コンテナの認証情報を使って動的に引っ張ってくる高度な設計です。
```env
GCP_PROJECT_ID=your-gcp-project-id
GEMINI_SECRET_ID=gemini-api-key
```

**方法C（Google Drive MCP用：高いセキュリティ設定）**
Google Drive MCPを使う場合、GCPのSecret ManagerにサービスアカウントのJSONキーを保存してセキュアに接続することが可能です。また、操作を許可するフォルダ名も環境変数で制限（ディレクトリトラバーサル対策）できます。
```env
GCP_PROJECT_ID=your-gcp-project-id
DRIVE_CREDENTIALS_SECRET_ID=drive-credentials
ALLOWED_DRIVE_FOLDER_NAME=article-for-learning
```

### 【必須】Google Drive MCPを利用する場合のドライブ側準備
Google Drive MCPを動かすためには、セキュリティ担保のため、ご自身のGoogle Drive側に「LLMにアクセスさせてもよい専用の隔離フォルダ」を作り、サービスアカウントを招待する必要があります。

1. **専用フォルダの作成**: ご自身のGoogle Drive内に、LLMに操作・閲覧を許可するフォルダ（例：`article-for-learning`）を新規作成します。
2. **アクセス権（共有）の付与**: 作成したフォルダの「共有」ボタンを押し、今回利用するGCPサービスアカウントのメールアドレス（`〇〇@〇〇.iam.gserviceaccount.com` 等）を入力し、「編集者」として追加（招待）します。
3. **環境変数への登録**: 上記の環境変数 `ALLOWED_DRIVE_FOLDER_NAME` に、作成したフォルダの一言一句違わぬ正確な名前を設定してください。これにより、指定フォルダ以外のプライベートなファイルへのアクセスを完全に遮断できます。

---

## 4. 学習のステップ (Playground)

コンテナに入った状態で、`playground/` 内のスクリプトを順番に実行することでMCPとか何かを浅く理解できます。

### Step 1: `01_basic_mcp_client.py`
**「MCPクライアントとMCPサーバーはどうやって会話しているの？」**
AI（LLM）を使わず、Pythonの純粋なコードから自作の「ローカルファイル操作MCPサーバー (`src/mcp/local_fs_mcp.py`)」に接続し、サーバーが持つツールのリストを取得したり、手動で `write_file` ツールを実行してファイルを作成する基礎スクリプトです。

```bash
python playground/01_basic_mcp_client.py
```

### Step 2: `02_gemini_react_agent.py`
**「LLMはどうやって自律的にツールを使うの？（ReActエージェント）」**
GeminiにMCPサーバーの「ファイル操作の道具箱」を渡し、「日本の首都はどこか調べて、それをファイルに保存して」というプロンプトを与えます。
Geminiが自身で思考し（Reasoning）、ツールを実行し（Acting）、その結果を受け取ってさらに考える…という完璧な自律型エージェントのループを体験できます。

```bash
python playground/02_gemini_react_agent.py
```
※ ここで生成されたファイルは、リポジトリ内の `tmp/` フォルダに出力されます。

### Step 3: `03_gemini_drive_agent.py`
**「LLMが外部クラウド（Google Drive）のファイル構造を理解して目的のファイルをダウンロードする」**
自作の高度な「Google Drive MCPサーバー (`src/mcp/google_drive_mcp.py`)」に接続し、Geminiに「〇〇フォルダの中にある〇〇を探してダウンロードして」と自然言語で指示を出します。
「フォルダの中身を一覧取得する」→「対象のファイルIDを特定する」→「保存先へダウンロードする」という複雑な自律行動と、意図しない外部ファイルの取得要求をブロックする（ディレクトリトラバーサル対策）堅牢なセキュリティ機構を体験できます。

```bash
python playground/03_gemini_drive_agent.py
```

### Step 4: `04_gemini_arxiv_agent.py`
**「LLMがarXivから論文のソースコードを取得し、解釈する」**
自作の「ArXiv MCPサーバー (`src/mcp/arxiv_mcp.py`)」に接続し、Geminiに「arXivから『Attention Is All You Need』という論文をダウンロードして」と指示を出します。
MCPツールが裏側で自動的にPDFとTeXソースのダウンロード・解凍展開・テキストデータの結合を行い、論文の全テキストを直接LLMに渡す（透過的なデータ抽出機構）を体験できます。

```bash
python playground/04_gemini_arxiv_agent.py
```
※ 抽出されたPDF、TeXファイル群、結合済みテキスト（`raw_text`）は、リポジトリ内の `tmp/arxiv/` フォルダに出力されます。

---

## 5. テストの実行

自作のMCPサーバーやGeminiクライアントが正しく動作するかを確かめるための単体テストが用意されています。コンテナ内で以下を実行してください。

```bash
pytest test/ -v
```
