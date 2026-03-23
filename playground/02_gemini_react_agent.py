"""
python 02_gemini_react_agent.py
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
    print("=== 日本の首都をMCP経由でファイル保存するテスト ===")
    
    # 1. APIキーを取得して汎用LLMクライアント(GeminiMCPClient)を初期化
    try:
        api_key = get_secret()
        # 今回作成したクラスをインスタンス化（動作理解のためverbose=Trueで詳細な推論ログを出力）
        llm_client = GeminiMCPClient(api_key=api_key, model_name="gemini-2.5-flash", verbose=True)
    except Exception as e:
        print(f"APIキーの取得等でエラーが発生しました: {e}")
        return

    # 2. Local FS MCPサーバー(ファイル操作用)の起動パラメータを設定
    server_params = StdioServerParameters(
        command="python",
        # プロジェクトルートからの相対パス、または絶対パスで最新の配置場所を指定
        args=[os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "mcp", "local_fs", "local_fs_mcp.py")],
    )

    print("🔌 Local FS MCPサーバーを起動し、接続しています...")
    # 3. サーバーと接続してセッションを確立
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ MCPサーバーとの接続が完了しました。\n")

            # 4. LLMに指示を出す
            prompt = "日本の首都はどこですか？その問いに答えて、その結果を 'japan_shuto.txt' というファイル名で保存してください。内容は日本語で記述してください。"
            
            # 5. クラス化したメソッドを呼び出すだけで自動的にツール実行まで行われる
            await llm_client.execute_task(prompt=prompt, mcp_session=session)

    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    asyncio.run(main())
