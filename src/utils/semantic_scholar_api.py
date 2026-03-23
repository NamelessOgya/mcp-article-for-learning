import time
import requests
from typing import List, Dict, Any
import yaml
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os

_ss_config_path = os.path.join(PROJECT_ROOT, "src", "mcp", "semantic_scholar", "config.yaml")
with open(_ss_config_path, "r", encoding="utf-8") as f:
    _ss_config = yaml.safe_load(f) or {}

SEMANTIC_SCHOLAR_MAX_FETCH_LIMIT = _ss_config.get("SEMANTIC_SCHOLAR_MAX_FETCH_LIMIT", 1000)

def make_api_request_with_retry(url: str, params: dict, max_retries: int = 5) -> dict:
    for attempt in range(max_retries):
        response = requests.get(url, params=params)
        if response.status_code == 429:
            if attempt < max_retries - 1:
                time.sleep(5)  # 429エラー時は5秒待機してリトライ
                continue
        response.raise_for_status()
        return response.json()
    raise Exception("Max retries exceeded for HTTP 429")

def search_paper(query: str) -> Dict[str, Any]:
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    search_params = {
        "query": query,
        "limit": 1
    }
    
    search_data = make_api_request_with_retry(search_url, search_params)
    if not search_data.get("data") or len(search_data["data"]) == 0:
        raise ValueError(f"検索エラー: クエリ '{query}' に一致する論文が見つかりませんでした。")
        
    return search_data["data"][0]

def fetch_top_citations(paper_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    # 1回のリクエストで最大1000件（設定値）を取得する
    citations_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
    fields = "title,abstract,citationCount,externalIds"
    citations_params = {
        "fields": fields,
        "limit": SEMANTIC_SCHOLAR_MAX_FETCH_LIMIT
    }
    
    citations_data = make_api_request_with_retry(citations_url, citations_params)
    citations_list = citations_data.get("data", [])
    if not citations_list:
        return []
        
    # 取得した引用リストを被引用数（citationCount）の降順でクライアントサイドソート
    valid_citations = []
    for c in citations_list:
        citing_paper = c.get("citingPaper")
        if citing_paper:
            # Noneの場合は0として扱う
            citation_count = citing_paper.get("citationCount") or 0
            title = citing_paper.get("title") or "No Title"
            abstract = citing_paper.get("abstract") or "No Abstract Available"
            
            external_ids = citing_paper.get("externalIds") or {}
            arxiv_id = external_ids.get("ArXiv", None)
            
            valid_citations.append({
                "title": title,
                "abstract": abstract,
                "citationCount": citation_count,
                "arxivId": arxiv_id
            })
            
    # citationCountの降順でソート
    valid_citations.sort(key=lambda x: x["citationCount"], reverse=True)
    
    # 上位limit件を抽出
    return valid_citations[:limit]
