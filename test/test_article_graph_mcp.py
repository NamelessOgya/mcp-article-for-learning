import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from unittest.mock import patch, MagicMock
from src.mcp.article_graph.article_graph_mcp import article_graph_forward_agent

@patch("src.mcp.article_graph.article_graph_mcp.get_secret")
@patch("src.mcp.article_graph.article_graph_mcp.genai.Client")
@patch("src.mcp.article_graph.article_graph_mcp.search_paper")
@patch("src.mcp.article_graph.article_graph_mcp.fetch_top_citations")
@patch("src.mcp.article_graph.article_graph_mcp.download_and_extract_text")
def test_article_graph_forward_agent(mock_download, mock_fetch, mock_search, mock_genai, mock_secret):
    # Mock setups
    mock_secret.return_value = "fake_api_key"
    
    # Mock Semantic Scholar
    mock_search.return_value = {"paperId": "tgt123", "title": "Target Paper Title"}
    mock_fetch.return_value = [
        {"title": "Citing Paper 1", "citationCount": 10}, 
        {"title": "Citing Paper 2", "citationCount": 5}
    ]
    
    # Mock ArXiv Download
    # Citing Paper 1 -> Success
    # Citing Paper 2 -> Error
    def download_side_effect(title, arxiv_id=None):
        if "1" in title:
            # 返り値: success, text, actual_title
            return True, "This is a long extracted text for testing. " * 50, "Citing Paper 1"
        return False, "Not found", None
        
    mock_download.side_effect = download_side_effect
    
    # Mock Gemini
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"citation_type": "継承引用", "details": "発展させた検証"}'
    mock_model.generate_content.return_value = mock_response
    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_model
    mock_genai.return_value = mock_client_instance
    
    # Execute
    result = article_graph_forward_agent("Target Paper Title")
    
    # Assertions
    assert "対象論文 'Target Paper Title' に対する引用分析が完了しました。" in result
    assert "Citing Paper 1,継承引用,発展させた検証" in result
    assert "Citing Paper 2,エラー,エラー" in result
    
    # Verify the API calls
    mock_search.assert_called_once_with("Target Paper Title")
    mock_fetch.assert_called_once()
    assert mock_download.call_count == 2
