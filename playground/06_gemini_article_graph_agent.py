"""
python playground/06_gemini_article_graph_agent.py
"""
import asyncio
import sys
import os

# プロジェクトルートを追加してsrc配下のモジュールを読み込めるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.llm.gcp.secret_manager import get_secret
from src.llm.gcp.gemini_client import GeminiMCPClient


async def main():
    print("=== Article Graph MCPを使って特定の論文の引用関係を分析するテスト ===")
    
    # 1. APIキーを取得して汎用LLMクライアント(GeminiMCPClient)を初期化
    try:
        api_key = get_secret()
        # 動作理解のためverbose=Trueで詳細な推論ログを出力
        llm_client = GeminiMCPClient(api_key=api_key, model_name="gemini-2.5-flash", verbose=True)
    except Exception as e:
        print(f"APIキーの取得等でエラーが発生しました: {e}")
        return

    # 2. Article Graph MCPサーバーの起動パラメータを設定
    server_params = StdioServerParameters(
        command="python",
        # プロジェクトルートからの相対パス、または絶対パスで配置場所を指定
        args=[os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "mcp", "article_graph", "article_graph_mcp.py")],
    )

    print("🔌 Article Graph MCPサーバーを起動し、接続しています...")
    # 3. サーバーと接続してセッションを確立
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ MCPサーバーとの接続が完了しました。\n")

            # 4. ユーザーから分析対象の論文名を受け取る
            try:
                user_input = input("🔍 分析したい対象論文名を入力してください (Enterでデフォルト: 'Attention Is All You Need'): ").strip()
            except EOFError:
                user_input = ""
                
            paper_title = user_input if user_input else "Attention Is All You Need"
            print(f"\n👉 「{paper_title}」の引用分析を開始します（時間がかかる場合があります）...\n")

            # 5. LLMに指示を出す
            prompt = f"Article Graph MCPツールを使って、「{paper_title}」という論文の引用分析を実行し、その結果（生成された出力や保存先など）をそのままユーザーに教えてください。"
            
            # 6. クラス化したメソッドを呼び出すだけで自動的にツール実行まで行われる
            await llm_client.execute_task(prompt=prompt, mcp_session=session)

    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    asyncio.run(main())
