import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.gcp.gemini_client import GeminiMCPClient

@pytest.mark.asyncio
@patch('src.llm.gcp.gemini_client.genai.Client')
async def test_gemini_mcp_client_execute_task(mock_client_class):
    # 1. Geminiクライアントのモック生成
    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance
    
    # チャットセッションのモック
    mock_chat = MagicMock()
    mock_client_instance.chats.create.return_value = mock_chat
    
    # 最初のレスポンス (ツール実行要求)
    mock_response_1 = MagicMock()
    mock_function_call = MagicMock()
    mock_function_call.name = "write_file"
    mock_function_call.args = {"filename": "weather.txt", "content": "晴れ"}
    mock_response_1.function_calls = [mock_function_call]
    
    # 2回目のレスポンス (タスク完了)
    mock_response_2 = MagicMock()
    mock_response_2.function_calls = None
    mock_response_2.text = "保存が完了しました"
    
    # send_messageが呼ばれるたびに順番にレスポンスを返すように設定
    mock_chat.send_message.side_effect = [mock_response_1, mock_response_2]

    # 2. MCPセッションのモック作成
    mock_mcp_session = AsyncMock()
    
    # list_toolsのモックレスポンス
    mock_tools_response = MagicMock()
    mock_tool = MagicMock()
    mock_tool.name = "write_file"
    mock_tool.description = "Test write tool"
    mock_tool.inputSchema = {"type": "object", "properties": {}}
    mock_tools_response.tools = [mock_tool]
    mock_mcp_session.list_tools.return_value = mock_tools_response
    
    # call_toolのモックレスポンス
    mock_call_result = MagicMock()
    mock_text_content = MagicMock()
    mock_text_content.text = "Success"
    mock_call_result.content = [mock_text_content]
    mock_mcp_session.call_tool.return_value = mock_call_result

    # 3. テスト対象の実行
    client = GeminiMCPClient(api_key="dummy_key", model_name="gemini-2.5-flash")
    result_text = await client.execute_task(prompt="天気を保存して", mcp_session=mock_mcp_session)

    # 4. 検証
    mock_mcp_session.list_tools.assert_called_once()
    mock_mcp_session.call_tool.assert_called_once_with(
        name="write_file",
        arguments={"filename": "weather.txt", "content": "晴れ"}
    )
    mock_client_instance.chats.create.assert_called_once()
    assert mock_chat.send_message.call_count == 2
    assert "保存が完了しました" in result_text
