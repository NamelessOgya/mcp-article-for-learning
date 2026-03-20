# Class: GeminiMCPClient

## 機能 (What it does)
`src.llm.gcp.gemini_client` モジュールに定義されている、LLM（Gemini）とMCPサーバー間のやり取りを仲介・自動化する汎用クラアントクラスです。

このクラスを利用することで、「ユーザーからの指示（プロンプト）をLLMに投げる」→「LLMが利用可能なMCPツールを解析する」→「必要に応じてツール（ファイル書き込みなど）を実行する」という一連のAIエージェント的な動作を簡単に実装できます。

## 使い方 (How to use it)

事前にMCPサーバーとのセッション（`mcp_session`）を確立しておく必要があります。

### 実装例
```python
import asyncio
from src.llm.gcp.gemini_client import GeminiMCPClient
# MCPセッション確立部分のインポート (詳細はサンプルを参照)
from mcp import ClientSession

async def main():
    # 1. クラスのインスタンス化 (取得済みのAPIキーを渡す)
    llm_client = GeminiMCPClient(api_key="your_api_key", model_name="gemini-2.5-flash")
    
    # 2. MCPセッションが確立されたスコープ内で execute_task() を呼ぶ
    # session = await ... (MCPサーバーとの接続を確立)
    
    prompt = "tmpディレクトリに 'hello.txt' を作成してください。"
    
    # 3. 実行（ツールの取得、推論、ツール実行が全て自動で行われる）
    result = await llm_client.execute_task(prompt=prompt, mcp_session=session)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 主なメソッド
*   `__init__(self, api_key: str, model_name: str = "gemini-2.5-flash")`
    *   APIキーと使用するLLMのモデル名を受け取って初期化します。
*   `execute_task(self, prompt: str, mcp_session) -> str`
    *   **メインの非同期メソッド**です。MCPセッションからツール一覧を取得してGeminiに渡し、関数の呼び出し要求があれば自動でMCPサーバーに実行を依頼します。
