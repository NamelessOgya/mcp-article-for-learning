import asyncio
from google import genai
from google.genai import types

class GeminiMCPClient:
    """
    Gemini APIとMCPサーバーのやり取りを仲介する汎用クライアントクラス
    """
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash", verbose: bool = False):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        
        # verbose引数の意味：
        # True に設定すると、AIの内部の思考過程や、MCPツールの実行経過（引数など）が逐一コンソールに出力されます。
        # False（デフォルト） にすると、途中のデバッグ用ログは一切表示されず、最終結果のみを静かに返します。
        # エージェントの動作検証や勉強時には True に設定することをおすすめします。
        self.verbose = verbose

    def _log(self, text: str):
        """verboseがTrueの場合のみコンソールにメッセージを出力するヘルパー"""
        if self.verbose:
            text_str = str(text)
            if len(text_str) > 1500:
                # ターミナルが埋め尽くされるのを防ぐため、長すぎるログは最初と最後だけ表示して中略する
                print(text_str[:800] + "\n\n... (中略: 長すぎるためコンソールへの出力は制限しています) ...\n\n" + text_str[-300:])
            else:
                print(text_str)

    @staticmethod # インスタンス変数を一切使わない関数につけるらしい。へー
    def _mcp_to_gemini_tool(mcp_tool) -> dict:
        """MCPツール定義をGemini APIが理解できる形式(dict)に変換する"""
        return {
            "function_declarations": [
                {
                    "name": mcp_tool.name,
                    "description": mcp_tool.description or "", # LLMに対して「このツールは何をするものか」を伝える
                    "parameters": mcp_tool.inputSchema # LLMに対して「このツールに渡す引数は何か」を伝える
                }
            ]
        }

    async def execute_task(self, prompt: str, mcp_session, max_steps: int = 5) -> str:
        """
        MCPセッションとプロンプトを受け取り、Geminiとのやり取り〜ツール実行を
        さらに賢くループ（ReAct: Reasoning and Acting）で行う完全自動メソッド
        """
        # 1. 接続先のMCPサーバーから利用可能なツール一覧を取得
        tools_response = await mcp_session.list_tools()
        gemini_tools = [self._mcp_to_gemini_tool(t) for t in tools_response.tools] #ここで利用可能サーバーを整理

        # ちなみに、Geminiには標準でGoogle検索機能をツールとして持たせることも可能です
        # gemini_tools.append({"google_search": {}}) 
        
        self._log(f"🤖 Gemini ({self.model_name}) にタスクの指示を送信中...\nプロンプト: 「{prompt}」")
        
        # 2. ツール定義をセット
        config = types.GenerateContentConfig(
            tools=gemini_tools,
            temperature=0.7
        )
        
        # 単発の generate_content ではなく、会話履歴を保持する chat セッションを開始する (!)
        # この「チャットのやり取り」がReActループの基盤になります。
        chat = self.client.chats.create(model=self.model_name, config=config)
        
        # まずは最初の指示を送信
        self._log("\n🤔 AIが思考を開始しました...")
        response = chat.send_message(prompt)
        self._log(f"\n▼▼▼ AIからの生レスポンス (Raw Response) ▼▼▼\n{response}\n▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲")
        
        # 3. ループ（ReAct）の開始：AIが「もうツールは必要ない（タスク完了）」と判断するまで繰り返す
        for step in range(max_steps):
            if response.function_calls:
                self._log(f"\n🔄 [Step {step+1}] AIが独自の判断でツール実行を要求しています！")
                
                # 複数のツール呼び出しが同時に発生するケースに備え、結果をリストにまとめる
                function_responses = []
                
                for function_call in response.function_calls:
                    tool_name = function_call.name
                    tool_args = function_call.args
                    self._log(f"👉 実行するツール: {tool_name}")
                    self._log(f"📦 ツールの引数: {tool_args}")
                    
                    try:
                        # MCPサーバーにツール実行を依頼
                        result = await mcp_session.call_tool(
                            name=tool_name,
                            arguments=tool_args
                        )
                        # 実行結果を取り出す
                        result_text = result.content[0].text
                        
                        # コンソール出力用（長すぎる場合は省略して表示）
                        display_text = result_text if len(result_text) < 300 else result_text[:300] + "\n... (以下長すぎるためコンソール出力は省略) ..."
                        self._log(f"✅ 実行結果（この結果を再びAIに教えます）: {display_text}")
                        
                        # AIに返すための「ツールの実行結果報告」フォーマット（Part）を作成
                        function_responses.append(
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": result_text}
                            )
                        )
                        
                    except Exception as e:
                        error_msg = f"ツールの実行中にエラーが発生しました: {e}"
                        print(f"❌ {error_msg}")  # エラーは常に表示する
                        function_responses.append(
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"error": error_msg}
                            )
                        )
                
                # 「ツールの実行結果」をチャットメッセージとしてAIに返送（報告）し、AIの次の思考を促す
                self._log("\n🧠 AIに結果を報告し、次の指示（または最終回答）を待っています...")
                response = chat.send_message(function_responses)
                self._log(f"\n▼▼▼ AIからの生レスポンス (Raw Response) ▼▼▼\n{response}\n▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲")
                
            else:
                # ツール呼び出しの要求がない ＝ AIが「自分だけで答えられる」または「必要なタスクが終わった」と判断した
                break
                
        # 思考ループ終了
        self._log("\n🎉 === エージェントの自律タスクが完了しました！ ===")
        # 最終的な回答はプログラムの結果なので、文字出力の制御（self.verbose）に関わらず返り値として必ず返す
        return response.text
