import os
import time
import requests
from mcp.server.fastmcp import FastMCP

# サーバーのインスタンスを作成
mcp = FastMCP("SemanticScholarServer")

@mcp.tool()
def get_paper_citations(query: str, limit: int = 10) -> str:
    """
    指定されたタイトルやキーワードでSemantic Scholarの論文を検索し、
    その論文を引用している他の論文のタイトルとAbstractを被引用数が多い順に取得します。
    
    Args:
        query: 検索する対象の論文タイトルまたはキーワード
        limit: 取得する引用論文の最大件数（デフォルト: 10、最大: 1000）
    """
    try:
        # Helper function to handle Rate Limits (429) gracefully
        def make_api_request_with_retry(url, params, max_retries=3):
            for attempt in range(max_retries):
                response = requests.get(url, params=params)
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(3)  # 429エラー時は3秒待機してリトライ
                        continue
                response.raise_for_status()
                return response.json()
            raise Exception("Max retries exceeded for HTTP 429")

        # 1. 論文の検索 (Search API)
        search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        search_params = {
            "query": query,
            "limit": 1
        }
        
        search_data = make_api_request_with_retry(search_url, search_params)
        
        if not search_data.get("data") or len(search_data["data"]) == 0:
            return f"検索エラー: クエリ '{query}' に一致する論文が見つかりませんでした。"
            
        target_paper = search_data["data"][0]
        paper_id = target_paper["paperId"]
        paper_title = target_paper.get("title", "Unknown Title")
        
        # 2. Rate Limit対策としてのWait (1秒)
        time.sleep(1)
        
        # 3. 引用論文の取得 (Citations API)
        # 1回のリクエストで最大1000件を取得する
        citations_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
        citations_params = {
            "fields": "title,abstract,citationCount",
            "limit": 1000
        }
        
        citations_data = make_api_request_with_retry(citations_url, citations_params)
        
        citations_list = citations_data.get("data", [])
        if not citations_list:
            return f"論文 '{paper_title}' にはまだ引用論文が登録されていません。"
            
        # 4. 取得した引用リストを被引用数（citationCount）の降順でクライアントサイドソート
        # Semantic Scholarのデータ構造上、引用論文の情報は 'citingPaper' キーの中に格納されている
        valid_citations = []
        for c in citations_list:
            citing_paper = c.get("citingPaper")
            if citing_paper:
                # Noneの場合は0として扱う
                citation_count = citing_paper.get("citationCount") or 0
                title = citing_paper.get("title") or "No Title"
                abstract = citing_paper.get("abstract") or "No Abstract Available"
                
                valid_citations.append({
                    "title": title,
                    "abstract": abstract,
                    "citationCount": citation_count
                })
                
        # citationCountの降順でソート
        valid_citations.sort(key=lambda x: x["citationCount"], reverse=True)
        
        # 上位limit件を抽出
        top_citations = valid_citations[:limit]
        
        # 5. 結果を文字列として整形
        result_str = f"入力クエリ '{query}' から特定された元論文: '{paper_title}'\n"
        result_str += f"取得した引用論文総数からの上位 {len(top_citations)} 件（被引用数順）:\n"
        result_str += "=" * 50 + "\n\n"
        
        for i, doc in enumerate(top_citations, 1):
            result_str += f"[{i}] {doc['title']} (引用数: {doc['citationCount']})\n"
            result_str += f"Abstract: {doc['abstract']}\n"
            result_str += "-" * 50 + "\n"
            
        return result_str
        
    except requests.exceptions.HTTPError as http_err:
        return f"APIリクエストエラーが発生しました（HTTP {http_err.response.status_code}）: {http_err}"
    except Exception as e:
        return f"予期せぬエラーが発生しました: {e}"

if __name__ == "__main__":
    mcp.run()
