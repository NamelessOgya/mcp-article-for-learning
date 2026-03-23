import os
import sys
import json
import csv
import io
import yaml
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# プロジェクトルートを追加して src 以下のパッケージをインポートできるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from pydantic import BaseModel, Field
from google import genai
from mcp.server.fastmcp import FastMCP

from src.utils.semantic_scholar_api import search_paper, fetch_top_citations
from src.utils.arxiv_api import download_and_extract_text
from src.llm.gcp.secret_manager import get_secret

# 設定とプロンプトの読み込み
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(CURRENT_DIR, "config.yaml"), "r", encoding="utf-8") as f:
    _config = yaml.safe_load(f) or {}
ARTICLE_GRAPH_MAX_ANALYZE_LIMIT = _config.get("ARTICLE_GRAPH_MAX_ANALYZE_LIMIT", 20)
GEMINI_MODEL_NAME = _config.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")

with open(os.path.join(CURRENT_DIR, "prompt.toml"), "rb") as f:
    _prompt_data = tomllib.load(f)
system_instruction_prompt = _prompt_data.get("content", {}).get("prompt", "")

# サーバーのインスタンスを作成
mcp = FastMCP("ArticleGraphServer")

class CitationAnalysis(BaseModel):
    citation_type: str = Field(description="引用種類。['継承引用', '例示引用', '比較引用', '利用引用', 'エラー']のいずれか")
    details: str = Field(description="引用関係詳細(30文字程度)。情報不足で判断できない場合もエラーの理由を詳細に記述すること。")

@mcp.tool()
def article_graph_forward_agent(target_article_name: str) -> str:
    """
    対象の論文を引用している論文（最大20件）を取得・ダウンロードし、AIで引用関係を分析します。
    すべての結果はCSV形式（文字列）として出力され、同時に tmp/article_graph_output/*.csv にも保存されます。

    Args:
        target_article_name: 分析対象となる元論文のタイトル
    """
    try:
        # Gemini Client Init
        api_key = get_secret()
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"Gemini APIの初期化に失敗しました: {e}"

    # Semantic Scholar で検索と引用取得
    try:
        target_paper = search_paper(target_article_name)
        paper_id = target_paper["paperId"]
        paper_title = target_paper.get("title", "Unknown Title")
        
        top_citations = fetch_top_citations(paper_id, ARTICLE_GRAPH_MAX_ANALYZE_LIMIT)
    except Exception as e:
        return f"Semantic Scholarからの論文検索・引用取得に失敗しました: {e}"

    if not top_citations:
        return f"論文 '{paper_title}' を引用している論文が見つかりませんでした。"

    csv_rows = []
    
    # 分析実行
    system_instruction = system_instruction_prompt

    for citation in top_citations:
        citing_title = citation["title"]
        arxiv_id = citation.get("arxivId")
        
        success, extracted_text, actual_title = download_and_extract_text(citing_title, arxiv_id=arxiv_id)
        
        display_title = actual_title if actual_title else citing_title
        
        if not success:
            # arXivからのダウンロード失敗等のエラー
            csv_rows.append((display_title, "エラー", "エラー"))
            continue
            
        # 短すぎるものはテキスト抽出失敗とみなしてエラー扱い
        if not extracted_text or len(extracted_text) < 100:
            csv_rows.append((display_title, "エラー", "エラー"))
            continue

        try:
            # プロンプトの組み立て (最大文字数を概ね 50万文字 程度に切り詰めてGeminiの入力制限に配慮)
            prompt = f"対象論文のタイトル: {paper_title}\n\n"
            prompt += f"引用論文のタイトル: {display_title}\n\n"
            prompt += f"引用論文の本文:\n{extracted_text[:500000]}"
            
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CitationAnalysis,
                    system_instruction=system_instruction
                )
            )
            
            # JSONパース
            ans = json.loads(response.text)
            c_type = ans.get("citation_type", "エラー")
            c_details = ans.get("details", "エラー")
            
            csv_rows.append((display_title, c_type, c_details))

        except Exception:
            # Gemini側のエラー (JSONパースエラーや通信エラー)
            csv_rows.append((display_title, "エラー", "エラー"))

    # CSV出力の作成
    safe_title = "".join(c for c in paper_title if c.isalnum() or c in " -_").strip()
    out_dir = os.path.join(PROJECT_ROOT, "tmp", "article_graph_output")
    os.makedirs(out_dir, exist_ok=True)
    out_csv_path = os.path.join(out_dir, f"{safe_title}.csv")
    
    # StringIOでCSV文字列も生成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["引用論文名", "引用種類", "引用関係詳細"])
    
    with open(out_csv_path, "w", encoding="utf-8", newline="") as f:
        file_writer = csv.writer(f)
        file_writer.writerow(["引用論文名", "引用種類", "引用関係詳細"])
        for row in csv_rows:
            writer.writerow(row)
            file_writer.writerow(row)
            
    result_csv_str = output.getvalue()
    
    summary = f"対象論文 '{paper_title}' に対する引用分析が完了しました。\n"
    summary += f"分析対象論文数: {len(csv_rows)}件\n"
    summary += f"CSV保存先: {out_csv_path}\n"
    summary += "=" * 50 + "\n"
    summary += result_csv_str
    
    return summary

if __name__ == "__main__":
    mcp.run()
