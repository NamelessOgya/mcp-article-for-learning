import os
import tarfile
import gzip
import shutil
import arxiv
from typing import Tuple, Optional
import yaml
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_config_path = os.path.join(PROJECT_ROOT, "src", "mcp", "arxiv", "config.yaml")
with open(_config_path, "r", encoding="utf-8") as f:
    _arxiv_config = yaml.safe_load(f) or {}

ARXIV_MAX_RESULTS = _arxiv_config.get("ARXIV_MAX_RESULTS", 1)
ARXIV_TMP_BASE_DIR = os.path.join(PROJECT_ROOT, _arxiv_config.get("ARXIV_TMP_DIR_REL", "tmp/arxiv"))

def download_and_extract_text(title_query: str, arxiv_id: str = None) -> Tuple[bool, str, Optional[str]]:
    """
    arXivで論文を検索し、ソース(TeXまたは単一gz)をダウンロード・展開して結合テキストを返す。
    
    Returns:
        Tuple[bool, str, Optional[str]]: 
          - success: 成功したかどうか
          - message_or_text: 成功時は結合されたテキスト、失敗時はエラーメッセージ
          - paper_title: 成功時の実際の論文タイトル（失敗時はNone）
    """
    try:
        os.makedirs(ARXIV_TMP_BASE_DIR, exist_ok=True)
        pdf_dir = os.path.join(ARXIV_TMP_BASE_DIR, "pdf")
        tex_dir = os.path.join(ARXIV_TMP_BASE_DIR, "tex")
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(tex_dir, exist_ok=True)

        import re
        client = arxiv.Client()
        
        if arxiv_id:
            # Semantic Scholarから取得したarXiv IDが存在する場合は、IDによる1発検索を行う
            search = arxiv.Search(id_list=[arxiv_id])
        else:
            # arXivの検索APIはコロン等の記号や「for」「with」等の頻出単語（ストップワード）が
            # ti:"..." の中に含まれると検索結果が0件になるバグ質な挙動があります。
            # そのため記号やストップワードを除外抽出します。
            stopwords = {"with", "from", "that", "this", "when", "what", "where", "which", "who", "why", "how", "some", "such", "than", "very", "into", "through", "over"}
            clean_words = [w for w in re.split(r'\W+', title_query) if len(w) > 3 and w.lower() not in stopwords]
            if not clean_words: # もし全て短い単語なら制限を少し緩める
                clean_words = [w for w in re.split(r'\W+', title_query) if len(w) > 1]
    
            if clean_words:
                # 最初の6単語程度でAND検索（ti:WORD AND ti:WORD）に変換する
                robust_query = " AND ".join([f'ti:"{w}"' for w in clean_words[:6]])
            else:
                robust_query = f'ti:"{title_query}"'
                
            search = arxiv.Search(
                query=robust_query,
                max_results=ARXIV_MAX_RESULTS,
                sort_by=arxiv.SortCriterion.Relevance
            )

        results = list(client.results(search))
        if not results:
            return False, f"検索エラー: タイトルに '{title_query}' を含む論文が見つかりませんでした。", None

        paper = results[0]
        safe_title = "".join(c for c in paper.title if c.isalnum() or c in " -_").strip()
        pdf_filename = f"{safe_title}.pdf"
        tex_filename = f"{safe_title}.tar.gz"
        
        import time
        import urllib.error
        
        pdf_path = None
        tex_path = None
        
        # arXivのダウンロードエンドポイントはAPIとは別にレートリミット(429/403)が発生しやすいためリトライを実装
        for attempt in range(3):
            try:
                # urllibのIncompleteReadエラー対策のため、requestsを用いたストリームダウンロードに置き換え
                import requests
                eprint_url = paper.pdf_url.replace('/pdf/', '/e-print/')
                tex_path = os.path.join(tex_dir, tex_filename)
                with requests.get(eprint_url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(tex_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                break
            except Exception as e:
                # urllibのHTTPErrorや429、IncompleteReadなどネットワーク由来のエラーはリトライ
                error_str = str(e).lower()
                is_retryable = (
                    "429" in error_str or "403" in error_str or "too many requests" in error_str or
                    "retrieval incomplete" in error_str or "connection" in error_str or "timeout" in error_str or
                    getattr(e, "code", None) in [403, 429, 500, 502, 503, 504]
                )
                if is_retryable:
                    if attempt < 2:
                        time.sleep(10)
                        continue
                return False, f"ダウンロード中にエラーが発生しました: {e}", paper.title
        
        # 展開先ディレクトリ
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
                return False, f"ダウンロードは成功しましたが、TeXソースの展開に失敗しました ({e})。\n- PDF: {pdf_path}\n- TeXソース(未展開): {tex_result_path}", paper.title
                
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
                            
        rel_tex_result_path = os.path.relpath(tex_result_path, os.path.join(PROJECT_ROOT, "tmp"))
        
        if not combined_text.strip():
            return False, f"ダウンロードと展開は成功しましたが、テキストデータを抽出できませんでした。\n- TeXソース展開先: {rel_tex_result_path}", paper.title

        # 生テキストを保存して返す
        raw_text_dir = os.path.join(ARXIV_TMP_BASE_DIR, "raw_text")
        os.makedirs(raw_text_dir, exist_ok=True)
        raw_text_path = os.path.join(raw_text_dir, f"{safe_title}.txt")
        try:
            with open(raw_text_path, "w", encoding="utf-8") as f:
                f.write(combined_text)
        except Exception:
            pass # 保存失敗時はスルー
            
        # arXivサーバーに優しくするため、成功時最後に必ず少し待機する
        import time
        time.sleep(3)
        return True, combined_text, paper.title
        
    except Exception as e:
         return False, f"エラーが発生しました: {e}", None
