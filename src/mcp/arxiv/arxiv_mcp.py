import os
import sys

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from mcp.server.fastmcp import FastMCP
from src.utils.arxiv_api import download_and_extract_text
import yaml
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
with open(_config_path, "r", encoding="utf-8") as f:
    _arxiv_config = yaml.safe_load(f) or {}

ARXIV_TMP_BASE_DIR = os.path.join(PROJECT_ROOT, _arxiv_config.get("ARXIV_TMP_DIR_REL", "tmp/arxiv"))

# サーバーのインスタンスを作成
mcp = FastMCP("ArxivServer")

@mcp.tool()
def download_arxiv_paper(title_query: str) -> str:
    """
    指定されたタイトルでarXivの論文を検索し、存在すればPDFやTeXソースをダウンロードします。

    Args:
        title_query: 検索する論文タイトル
    """
    try:
        success, message_or_text, actual_title = download_and_extract_text(title_query)
        
        if not success:
            return message_or_text
            
        safe_title = "".join(c for c in actual_title if c.isalnum() or c in " -_").strip()
        raw_text_path = os.path.join(ARXIV_TMP_BASE_DIR, "raw_text", f"{safe_title}.txt")
        rel_raw_text_path = os.path.relpath(raw_text_path, os.path.join(PROJECT_ROOT, "tmp"))
        
        return (
            f"論文 '{actual_title}' のダウンロード・展開に成功しました。\n"
            f"(結合テキスト保存先: {rel_raw_text_path})\n"
            f"以下は抽出されたTeXソースコードの全内容です：\n\n"
            f"{message_or_text}"
        )
    except Exception as e:
         return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    mcp.run()
