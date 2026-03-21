import os
import tarfile
import gzip
import shutil
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
        pdf_filename = f"{safe_title}.pdf"
        tex_filename = f"{safe_title}.tar.gz"  # arXivのソースファイルは通常tar.gzで提供されます
        
        # PDFとTeXそれぞれのディレクトリを準備
        pdf_dir = os.path.join(BASE_DIR, "pdf")
        tex_dir = os.path.join(BASE_DIR, "tex")
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(tex_dir, exist_ok=True)
        
        # PDFとTeXソース（tar.gz/gz）をダウンロード
        pdf_path = paper.download_pdf(dirpath=pdf_dir, filename=pdf_filename)
        tex_path = paper.download_source(dirpath=tex_dir, filename=tex_filename)
        
        # 展開先ディレクトリ: tmp/arxiv/tex/{safe_title}/
        extracted_dir = os.path.join(tex_dir, safe_title)
        os.makedirs(extracted_dir, exist_ok=True)
        
        # 展開を試みる
        tex_result_path = tex_path
        try:
            # tar.gz形式の場合
            with tarfile.open(tex_path, "r:gz") as tar:
                tar.extractall(path=extracted_dir)
            os.remove(tex_path)
            tex_result_path = extracted_dir
        except tarfile.ReadError:
            # tar形式ではない単一の.gzの場合 (画像がない単一ファイルなど)
            try:
                single_tex_path = os.path.join(extracted_dir, f"{safe_title}.tex")
                with gzip.open(tex_path, 'rb') as f_in:
                    with open(single_tex_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(tex_path)
                tex_result_path = extracted_dir
            except Exception as e:
                return f"ダウンロードは成功しましたが、TeXソースの展開に失敗しました ({e})。\n- PDF: {pdf_path}\n- TeXソース(未展開): {tex_result_path}"
                
        # 展開されたディレクトリ内の全 .tex と .bbl ファイルの中身を結合する
        combined_text = ""
        if os.path.isdir(tex_result_path):
            for root, dirs, files in os.walk(tex_result_path):
                for file in files:
                    if file.endswith((".tex", ".bbl")):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                combined_text += f"\n\n--- Start of {file} ---\n\n"
                                combined_text += f.read()
                                combined_text += f"\n\n--- End of {file} ---\n\n"
                        except Exception as e:
                            combined_text += f"\n\n[ファイルの読み取りに失敗しました: {file} - {e}]\n\n"
                            
        tmp_dir = os.path.join(PROJECT_ROOT, "tmp")
        rel_tex_result_path = os.path.relpath(tex_result_path, tmp_dir)
        
        if not combined_text.strip():
            return f"ダウンロードと展開は成功しましたが、テキストデータを抽出できませんでした。\n- TeXソース展開先: {rel_tex_result_path}"

        # 結合されたテキストを raw_text ディレクトリに保存する
        raw_text_dir = os.path.join(BASE_DIR, "raw_text")
        os.makedirs(raw_text_dir, exist_ok=True)
        raw_text_path = os.path.join(raw_text_dir, f"{safe_title}.txt")
        try:
            with open(raw_text_path, "w", encoding="utf-8") as f:
                f.write(combined_text)
        except Exception as e:
            pass # 保存失敗時は一旦スルーし、結果自体はLLMに返す方針とする

        rel_raw_text_path = os.path.relpath(raw_text_path, tmp_dir)

        return (
            f"論文 '{paper.title}' のダウンロード・展開に成功しました。\n"
            f"(結合テキスト保存先: {rel_raw_text_path})\n"
            f"以下は抽出されたTeXソースコードの全内容です：\n\n"
            f"{combined_text}"
        )
    except Exception as e:
         return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    mcp.run()
