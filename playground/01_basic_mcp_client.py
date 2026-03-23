import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 実行待ちを他の仕事に回せる。並列処理が可能。
async def main():
    # サーバーを起動するためのパラメータを定義 (python src/mcp/local_fs_mcp.py を実行するのと同じ)
    import os
    server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "mcp", "local_fs", "local_fs_mcp.py")],
    )

    print("MCPサーバーを起動し、接続しています...")
    # stdio_clientを使ってサーバープロセスを起動・接続。
    # 第一引数がStreamReader、第二引数がStreamWriter
    # StreamReaderはサーバーから送られてくるデータ、StreamWriterはサーバーに送るデータ
    # どのサーバーを起動するよ、という情報もここで渡している。
    async with stdio_client(server_params) as (read, write):
        # セッションを開始
        # セッションがIDの管理や送信文字列のバイト型変換、エラーハンドリングなどを行ってくれる
        async with ClientSession(read, write) as session:
            # サーバーの初期化 (クライアント側の情報を渡す)
            await session.initialize()

            # 1. サーバーが提供しているツール（関数）のリストを取得する
            print("\n--- 利用可能なツール一覧 ---")
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")

            # 2. ツールを手動で呼び出してみる
            # 関数名と引数を渡す形になっている。
            print("\n--- 'write_file' ツールを実行してファイルを作成 ---")
            result = await session.call_tool(
                "write_file",
                arguments={
                    "filename": "hello_from_client.txt",
                    "content": "これはPythonクライアントから手動で実行されたテストです！"
                }
            )
            # 実行結果（テキスト）を取り出して表示
            print("結果:", result.content[0].text)

            print("\n--- 'list_workspace_files' ツールを実行して一覧を取得 ---")
            result = await session.call_tool("list_workspace_files", arguments={})
            print("結果:\n", result.content[0].text)

if __name__ == "__main__":
    # 非同期処理を実行
    asyncio.run(main())
