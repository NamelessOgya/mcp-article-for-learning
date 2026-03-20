import pytest
import os
import shutil
import sys

# local_fs_mcp モジュールをインポートするためにパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.local_fs_mcp import write_file, read_file, list_workspace_files, BASE_DIR

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # テスト開始前にworkspaceディレクトリをクリーンアップ
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR, exist_ok=True)
    
    yield
    
    # テスト終了後にもクリーンアップ
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)

def test_write_and_read_file():
    # ファイル書き込みテスト
    write_result = write_file("test.txt", "Hello MCP World!")
    assert "成功しました" in write_result
    
    # ファイル読み込みテスト
    read_result = read_file("test.txt")
    assert read_result == "Hello MCP World!"

def test_read_nonexistent_file():
    # 存在しないファイルの読み込み
    result = read_file("not_exist.txt")
    assert "見つかりませんでした" in result

def test_list_files():
    # 最初は空
    assert "空です" in list_workspace_files()
    
    # ファイルを2つ作成
    write_file("file1.txt", "content1")
    write_file("file2.txt", "content2")
    
    # 一覧取得
    result = list_workspace_files()
    assert "file1.txt" in result
    assert "file2.txt" in result

def test_directory_traversal_prevention():
    # セキュリティ機能: 上位ディレクトリへのアクセスブロック
    result = write_file("../hacked_file.txt", "hacked")
    assert "エラーが発生しました" in result
    assert "アクセスが拒否されました" in result
