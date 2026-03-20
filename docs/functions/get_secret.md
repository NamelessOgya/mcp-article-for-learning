# Function: get_secret

## 機能 (What it does)
`src.llm.gcp.secret_manager` モジュールに定義されている関数です。
GCPのSecret Managerから、指定されたシークレット（デフォルトではGeminiのAPIキー）の最新バージョンを安全に取得し、文字列として返します。

内部的に `.env` ファイルやOSの環境変数を読み込み、GCPプロジェクトID（`GCP_PROJECT_ID`）とシークレット名（`GEMINI_SECRET_ID`）を動的に決定します。これにより、コード上に直接パスワードやキーをハードコーディングすることを防ぎます。

## 使い方 (How to use it)

事前の準備として、以下の**どちらか**の設定が必要です：

**方法A（手軽・ローカル開発向け）**
`.env` ファイルに直接APIキーを設定する。
`GEMINI_API_KEY=AIzaSy...`

**方法B（安全・本番運用向け）**
Secret Manager経由で取得するために、以下を設定して認証を通しておく。
1. `GCP_PROJECT_ID` と `GEMINI_SECRET_ID` を `.env` に設定しておく。
2. 実行する環境（VMやDockerコンテナなど）が、対象のGCPプロジェクトにおける `Secret Manager のシークレット アクセサー` 権限を持っていること。

### 実装例
```python
from src.llm.gcp.secret_manager import get_secret

def main():
    try:
        # 引数なしで呼び出すと.envや環境変数から自動でプロジェクトやシークレット名を解決して取得します。
        api_key = get_secret()
        print(f"APIキーを正常にロードしました（先頭10文字: {api_key[:10]}...）")
    except Exception as e:
        print(f"取得エラー: {e}")

if __name__ == "__main__":
    main()
```
