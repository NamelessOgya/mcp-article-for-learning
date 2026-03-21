import os
import arxiv
from mcp.server.fastmcp import FastMCP

# サーバーのインスタンスを作成
mcp = FastMCP("ArxivServer")

# 操作を許可するディレクトリ (プロジェクトルートの tmp/arxiv ディレクトリを指す)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "tmp", "arxiv"))
os.makedirs(BASE_DIR, exist_ok=True)

@mcp.tool()
def download_arxiv_paper(title_query: str) -> str:
    """
    指定されたタイトルでarXivの論文を検索し、存在すればPDFをダウンロードします。

    Args:
        title_query: 検索する論文タイトル
    """
    try:
        # arxiv パッケージを使用した検索設定 (max_results=1)
        client = arxiv.Client()
        # タイトルのフレーズ検索（完全一致検索）を行うため、ダブルクォーテーションで囲む
        search = arxiv.Search(
            query=f'ti:"{title_query}"',
            max_results=1,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = list(client.results(search))
        if not results:
            return f"検索エラー: タイトルに '{title_query}' を含む論文が見つかりませんでした。"

        paper = results[0]
        
        # 安全なファイル名の作成 (英数字と一部の記号以外を除外)
        safe_title = "".join(c for c in paper.title if c.isalnum() or c in " -_").strip()
        filename = f"{safe_title}.pdf"
        
        # tmp/arxiv/ ディレクトリが存在することを確認
        os.makedirs(BASE_DIR, exist_ok=True)
        
        # PDFをダウンロード
        downloaded_path = paper.download_pdf(dirpath=BASE_DIR, filename=filename)
        
        return f"ダウンロード成功: 論文 '{paper.title}' を {downloaded_path} に保存しました。"
    except Exception as e:
         return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    mcp.run()
