"""
python 03_gemini_drive_agent.py
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
    print("=== Google Driveから論文・資料をダウンロードするテスト ===")
    
    # 1. APIキーを取得して汎用LLMクライアント(GeminiMCPClient)を初期化
    try:
        api_key = get_secret()
        # 動作理解のためverbose=Trueで詳細な推論ログを出力
        llm_client = GeminiMCPClient(api_key=api_key, model_name="gemini-2.5-flash", verbose=True)
    except Exception as e:
        print(f"APIキーの取得等でエラーが発生しました: {e}")
        return

    # 2. Google Drive MCPサーバーの起動パラメータを設定
    server_params = StdioServerParameters(
        command="python",
        # プロジェクトルートからの構成に合わせて絶対パスを動的生成
        args=[os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "mcp", "google_drive", "google_drive_mcp.py")],
    )

    print("🔌 Google Drive MCPサーバーを起動し、接続しています...")
    # 3. サーバーと接続してセッションを確立 (GCE環境なら、この時点で自動的にADCが使われます)
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ MCPサーバーとの接続が完了しました。\n")

            # ユーザーに対象の指示を聞く
            print("💡 Geminiにお願いしたい指示を自然言語で入力してください。")
            print("   （例：「hello.md を探してダウンロードして中身を教えて」「研究計画かすみんフォルダの中身をリストアップして」）")
            user_input = input("\n指示: ").strip()
            
            if not user_input:
                print("指示が空のため終了します。")
                return

            # 4. LLMに指示を出す
            print(f"\n🤖 Geminiに指示を送信しました...\nプロンプト: {user_input}")
            
            # 5. タスク実行（ここでGeminiがツールを実行してファイルの検索やダウンロードを行う）
            await llm_client.execute_task(prompt=user_input, mcp_session=session)

    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    asyncio.run(main())
