import sys
import os

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from mcp.server.fastmcp import FastMCP
from src.utils.semantic_scholar_api import search_paper, fetch_top_citations
import yaml
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
with open(_config_path, "r", encoding="utf-8") as f:
    _ss_config = yaml.safe_load(f) or {}

SEMANTIC_SCHOLAR_DEFAULT_RETURN_LIMIT = _ss_config.get("SEMANTIC_SCHOLAR_DEFAULT_RETURN_LIMIT", 10)

# サーバーのインスタンスを作成
mcp = FastMCP("SemanticScholarServer")

@mcp.tool()
def get_paper_citations(query: str, limit: int = SEMANTIC_SCHOLAR_DEFAULT_RETURN_LIMIT) -> str:
    """
    指定されたタイトルやキーワードでSemantic Scholarの論文を検索し、
    その論文を引用している他の論文のタイトルとAbstractを被引用数が多い順に取得します。
    
    Args:
        query: 検索する対象の論文タイトルまたはキーワード
        limit: 取得する引用論文の最大件数
    """
    try:
        # 1. 論文の検索 (Search API)
        target_paper = search_paper(query)
        paper_id = target_paper["paperId"]
        paper_title = target_paper.get("title", "Unknown Title")
        
        # 2. 引用論文の取得 (Citations API)
        top_citations = fetch_top_citations(paper_id, limit)
        
        if not top_citations:
            return f"論文 '{paper_title}' にはまだ引用論文が登録されていません。"
            
        # 3. 結果を文字列として整形
        result_str = f"入力クエリ '{query}' から特定された元論文: '{paper_title}'\n"
        result_str += f"取得した引用論文総数からの上位 {len(top_citations)} 件（被引用数順）:\n"
        result_str += "=" * 50 + "\n\n"
        
        for i, doc in enumerate(top_citations, 1):
            result_str += f"[{i}] {doc['title']} (引用数: {doc['citationCount']})\n"
            result_str += f"Abstract: {doc['abstract']}\n"
            result_str += "-" * 50 + "\n"
            
        return result_str
        
    except Exception as e:
        return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    mcp.run()
