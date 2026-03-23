import pytest
import os
import shutil
import sys

# arxiv_mcp モジュールをインポートするためにパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.arxiv.arxiv_mcp import download_arxiv_paper
from src.mcp.arxiv.arxiv_mcp import ARXIV_TMP_BASE_DIR as BASE_DIR

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # テスト開始前に tmp/arxiv ディレクトリをクリーンアップ
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)
    
    yield
    
    # テスト終了後にもクリーンアップ
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)

def test_download_existing_paper():
    # 有名な論文でテスト（例：Attention Is All You Need）
    result = download_arxiv_paper("Attention Is All You Need")
    
    assert "抽出されたTeXソースコードの全内容です" in result
    assert "Attention" in result
    
    # PDFファイルが実際に保存されたか確認 (現在は未実装)
    # pdf_dir = os.path.join(BASE_DIR, "pdf")
    # assert os.path.exists(pdf_dir)

    # TeXソースファイルが展開先のディレクトリとして実際に保存されたか確認
    tex_dir = os.path.join(BASE_DIR, "tex")
    assert os.path.exists(tex_dir)
    extracted_dirs = [d for d in os.listdir(tex_dir) if os.path.isdir(os.path.join(tex_dir, d))]
    assert len(extracted_dirs) > 0
    # 中身が存在することを確認
    extracted_path = os.path.join(tex_dir, extracted_dirs[0])
    extracted_files = os.listdir(extracted_path)
    assert len(extracted_files) > 0

    # raw_textとして結合テキストが保存されたか確認
    raw_text_dir = os.path.join(BASE_DIR, "raw_text")
    assert os.path.exists(raw_text_dir)
    raw_text_files = os.listdir(raw_text_dir)
    assert any(f.endswith(".txt") for f in raw_text_files)

def test_download_nonexistent_paper():
    # 存在しないであろうデタラメなタイトルで検索
    result = download_arxiv_paper("NonExistentPaperTitle123456789XYZ")
    
    assert "検索エラー" in result
    assert "見つかりませんでした" in result
    
    # ファイルが保存されていないことを確認 (pdfディレクト内にpdfがないこと)
    pdf_dir = os.path.join(BASE_DIR, "pdf")
    if os.path.exists(pdf_dir):
        assert len(os.listdir(pdf_dir)) == 0
