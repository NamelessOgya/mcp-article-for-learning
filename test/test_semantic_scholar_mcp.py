import pytest
from unittest.mock import patch, MagicMock
from src.mcp.semantic_scholar_mcp import get_paper_citations
import requests

@patch("src.mcp.semantic_scholar_mcp.requests.get")
@patch("src.mcp.semantic_scholar_mcp.time.sleep")
def test_get_paper_citations_success(mock_sleep, mock_get):
    # Setup mock responses
    mock_search_response = MagicMock()
    mock_search_response.json.return_value = {
        "data": [{"paperId": "test-id-123", "title": "Test Paper Title"}]
    }
    mock_search_response.raise_for_status.return_value = None

    mock_citations_response = MagicMock()
    mock_citations_response.json.return_value = {
        "data": [
            {
                "citingPaper": {
                    "paperId": "c1",
                    "title": "Citation 1 (Low)",
                    "abstract": "Abstract 1",
                    "citationCount": 5
                }
            },
            {
                "citingPaper": {
                    "paperId": "c2",
                    "title": "Citation 2 (High)",
                    "abstract": "Abstract 2",
                    "citationCount": 100
                }
            },
            {
                "citingPaper": {
                    "paperId": "c3",
                    "title": "Citation 3 (Medium)",
                    "abstract": "Abstract 3",
                    "citationCount": 50
                }
            }
        ]
    }
    mock_citations_response.raise_for_status.return_value = None

    # mock_get should return search response first, then citations response
    mock_get.side_effect = [mock_search_response, mock_citations_response]

    # Run the function
    result = get_paper_citations("Test Paper", limit=2)

    # Asserts
    assert mock_get.call_count == 2
    assert mock_sleep.call_count == 1
    mock_sleep.assert_called_with(1)
    
    # Check that sorting worked (High should be first, Medium second, Low dropped because limit=2)
    assert "Citation 2 (High)" in result
    assert "Citation 3 (Medium)" in result
    assert "Citation 1 (Low)" not in result
    
    # Check that the format includes the citation counts properly
    assert "(引用数: 100)" in result
    assert "(引用数: 50)" in result

@patch("src.mcp.semantic_scholar_mcp.requests.get")
def test_get_paper_citations_empty_search(mock_get):
    # Setup mock responses for empty search
    mock_search_response = MagicMock()
    mock_search_response.json.return_value = {"data": []}
    mock_search_response.raise_for_status.return_value = None
    mock_get.return_value = mock_search_response

    result = get_paper_citations("Nonexistent Paper")

    assert mock_get.call_count == 1
    assert "見つかりませんでした" in result

@patch("src.mcp.semantic_scholar_mcp.requests.get")
@patch("src.mcp.semantic_scholar_mcp.time.sleep")
def test_get_paper_citations_empty_citations(mock_sleep, mock_get):
    # Setup mock responses
    mock_search_response = MagicMock()
    mock_search_response.json.return_value = {
        "data": [{"paperId": "test-id-123", "title": "Test Paper Title"}]
    }
    mock_search_response.raise_for_status.return_value = None

    mock_citations_response = MagicMock()
    mock_citations_response.json.return_value = {"data": []}
    mock_citations_response.raise_for_status.return_value = None

    mock_get.side_effect = [mock_search_response, mock_citations_response]

    result = get_paper_citations("Test Paper")

    assert mock_get.call_count == 2
    assert "引用論文が登録されていません" in result
