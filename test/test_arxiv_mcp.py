import pytest
import os
import shutil
import sys

# arxiv_mcp モジュールをインポートするためにパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.arxiv_mcp import download_arxiv_paper, BASE_DIR

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
    
    assert "ダウンロード成功" in result
    assert "Attention Is All You Need" in result
    
    # ファイルが実際に保存されたか確認
    files = os.listdir(BASE_DIR)
    assert len(files) > 0
    assert any(f.endswith(".pdf") for f in files)

def test_download_nonexistent_paper():
    # 存在しないであろうデタラメなタイトルで検索
    result = download_arxiv_paper("NonExistentPaperTitle123456789XYZ")
    
    assert "検索エラー" in result
    assert "見つかりませんでした" in result
    
    # ファイルが保存されていないことを確認
    files = os.listdir(BASE_DIR)
    assert len(files) == 0
