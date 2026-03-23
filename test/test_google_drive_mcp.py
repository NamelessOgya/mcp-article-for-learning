import pytest
from unittest.mock import patch, MagicMock
import os
import sys
import shutil
import re

# srcディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.google_drive.google_drive_mcp import download_drive_file, list_drive_files, BASE_DIR

@patch('src.mcp.google_drive.google_drive_mcp.verify_safe_file', return_value=True)
@patch('src.mcp.google_drive.google_drive_mcp.get_allowed_folder_id', return_value='allowed_root')
@patch('src.mcp.google_drive.google_drive_mcp.get_drive_service')
@patch('src.mcp.google_drive.google_drive_mcp.MediaIoBaseDownload')
@patch('src.mcp.google_drive.google_drive_mcp.io.FileIO')
def test_download_google_doc(mock_file_io, mock_downloader, mock_get_service, mock_get_allowed, mock_verify):
    # Drive APIサービスのモック
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    # files().get (メタデータ取得)のモック
    mock_get_request = MagicMock()
    mock_get_request.execute.return_value = {
        'id': '123456789',
        'name': 'Test Document',
        'mimeType': 'application/vnd.google-apps.document'  # Google Docsネイティブ形式
    }
    mock_service.files().get.return_value = mock_get_request
    
    # files().export_media (docs用エクスポート)のモック
    mock_export_request = MagicMock()
    mock_service.files().export_media.return_value = mock_export_request
    
    # ダウンロードのチャンク処理を1回で終わるようにモック
    mock_downloader_instance = MagicMock()
    mock_downloader_instance.next_chunk.return_value = (None, True)
    mock_downloader.return_value = mock_downloader_instance
    
    # ツールの実行
    result = download_drive_file('123456789')
    
    # 検証：Google Docsなので export_media('text/plain') が正しく呼ばれているか
    mock_service.files().get.assert_called_once_with(fileId='123456789', fields='id, name, mimeType')
    mock_service.files().export_media.assert_called_once_with(fileId='123456789', mimeType='text/plain')
    
    # 結果にファイル名が含まれているか
    assert "成功しました" in result
    assert "Test Document.txt" in result


@patch('src.mcp.google_drive.google_drive_mcp.verify_safe_file', return_value=True)
@patch('src.mcp.google_drive.google_drive_mcp.get_allowed_folder_id', return_value='allowed_root')
@patch('src.mcp.google_drive.google_drive_mcp.get_drive_service')
@patch('src.mcp.google_drive.google_drive_mcp.MediaIoBaseDownload')
@patch('src.mcp.google_drive.google_drive_mcp.io.FileIO')
def test_download_regular_pdf(mock_file_io, mock_downloader, mock_get_service, mock_get_allowed, mock_verify):
    # Drive APIサービスのモック
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    # files().get (メタデータ取得)のモック
    mock_get_request = MagicMock()
    mock_get_request.execute.return_value = {
        'id': '987654321',
        'name': 'research_paper.pdf',
        'mimeType': 'application/pdf'  # 一般的なPDFファイル（論文など）
    }
    mock_service.files().get.return_value = mock_get_request
    
    # files().get_media (通常ファイル用ダウンロード)のモック
    mock_get_media_request = MagicMock()
    mock_service.files().get_media.return_value = mock_get_media_request
    
    # ダウンロードのチャンク処理を1回で終わるようにモック
    mock_downloader_instance = MagicMock()
    mock_downloader_instance.next_chunk.return_value = (None, True)
    mock_downloader.return_value = mock_downloader_instance
    
    # ツールの実行
    result = download_drive_file('987654321')
    
    # 検証：通常のPDFなので export_media ではなく get_media が呼ばれているか
    mock_service.files().get_media.assert_called_once_with(fileId='987654321')
    assert "research_paper.pdf" in result

@patch('src.mcp.google_drive.google_drive_mcp.verify_safe_file', return_value=True)
@patch('src.mcp.google_drive.google_drive_mcp.get_allowed_folder_id', return_value='allowed_root')
@patch('src.mcp.google_drive.google_drive_mcp.get_drive_service')
def test_list_drive_files(mock_get_service, mock_get_allowed, mock_verify):
    # Drive APIサービスのモック
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    # files().list のモック
    mock_list_request = MagicMock()
    mock_list_request.execute.return_value = {
        'files': [
            {'id': 'folder123', 'name': '研究計画かすみん', 'mimeType': 'application/vnd.google-apps.folder'},
            {'id': 'file456', 'name': 'hello.md', 'mimeType': 'text/markdown'}
        ]
    }
    mock_service.files().list.return_value = mock_list_request
    
    # ツールの実行 (引数なしでルート検索)
    result = list_drive_files()
    
    # 検証
    mock_service.files().list.assert_called_once()
    assert "研究計画かすみん" in result
    assert "📁 フォルダ" in result
    assert "hello.md" in result
    assert "📄 ファイル" in result


@patch('src.mcp.google_drive.google_drive_mcp.get_allowed_folder_id', return_value='allowed_folder_id')
@patch('src.mcp.google_drive.google_drive_mcp.get_drive_service')
@patch('src.mcp.google_drive.google_drive_mcp.MediaIoBaseDownload')
@patch('src.mcp.google_drive.google_drive_mcp.io.FileIO')
def test_download_allowed_file(mock_file_io, mock_downloader, mock_get_service, mock_get_allowed):
    """
    指定階層（article-for-learning 等の allowed_folder_id）の配下にある test.md のダウンロードが
    セキュリティチェックをパスして成功することを確認するテスト
    """
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    # files().get のモック (URLや親フォルダを確認するために呼ばれる)
    def mock_get_side_effect(**kwargs):
        file_id = kwargs.get('fileId')
        fields = kwargs.get('fields')
        mock_request = MagicMock()
        
        if fields == 'parents':
            if file_id == 'safe_file_id':
                # 安全なファイルは親フォルダが allowed_folder_id
                mock_request.execute.return_value = {'parents': ['allowed_folder_id']}
            else:
                mock_request.execute.return_value = {'parents': []}
        else: # fields == 'id, name, mimeType'
            mock_request.execute.return_value = {
                'id': 'safe_file_id',
                'name': 'test.md',
                'mimeType': 'text/markdown'
            }
        return mock_request
        
    mock_service.files().get.side_effect = mock_get_side_effect
    
    # ダウンロードのチャンク処理のモック
    mock_get_media_request = MagicMock()
    mock_service.files().get_media.return_value = mock_get_media_request
    mock_downloader_instance = MagicMock()
    mock_downloader_instance.next_chunk.return_value = (None, True)
    mock_downloader.return_value = mock_downloader_instance
    
    # ツールの実行
    result = download_drive_file('safe_file_id')
    
    # 検証: セキュリティに弾かれずにダウンロードが完了していること
    assert "成功しました" in result
    assert "test.md" in result


@patch('src.mcp.google_drive.google_drive_mcp.get_allowed_folder_id', return_value='allowed_folder_id')
@patch('src.mcp.google_drive.google_drive_mcp.get_drive_service')
def test_download_rejected_file(mock_get_service, mock_get_allowed):
    """
    許可された階層の外（はるか上のルートなど）にある test.md をダウンロードしようとした時に、
    指定階層外へのアクセスとしてセキュリティエラーになることを確認するテスト
    """
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    def mock_get_side_effect(**kwargs):
        file_id = kwargs.get('fileId')
        fields = kwargs.get('fields')
        mock_request = MagicMock()
        
        if fields == 'parents':
            if file_id == 'unsafe_file_id':
                # 危険なファイルの親は全く別のフォルダ
                mock_request.execute.return_value = {'parents': ['some_other_root_folder_id']}
            elif file_id == 'some_other_root_folder_id':
                # その先は最上位
                mock_request.execute.return_value = {'parents': []}
        return mock_request
        
    mock_service.files().get.side_effect = mock_get_side_effect
    
    # ツールの実行 (無関係な場所のファイルIDを指定)
    result = download_drive_file('unsafe_file_id')
    
    # 検証: セキュリティエラーが出力されてダウンロードがブロックされること
    assert "セキュリティエラー" in result
    assert "外部にあるためダウンロードできません" in result

def test_actual_network_download():
    """
    モックを使わず、実際にGoogle Drive APIへアクセスして 'test.md' を検索・ダウンロードするE2E（結合）テスト。
    実際のファイルを落とし、意図通りダウンロードできたか（かつ tmp/test/ 配下に隔離されているか）を確認します。
    """
    # 1. テスト用のクリーンな保存先 (tmp/test/) を用意
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(project_root, 'tmp', 'test')
    
    # 既存の tmp/test/ 及び中身があれば削除して綺麗にする
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)
    
    # srcモジュールの BASE_DIR だけを一時的にパッチして、保存先を tmp/test に差し替える
    with patch('src.mcp.google_drive.google_drive_mcp.BASE_DIR', test_dir):
        from src.mcp.google_drive.google_drive_mcp import list_drive_files, download_drive_file
        
        # 2. 実際のDriveにアクセスし「test.md」という名前のファイルが存在するか検索する
        list_result = list_drive_files()
        
        # 結果文字列から test.md の ID を探し出す
        match = re.search(r"📄 ファイル: 'test\.md' \(ID: ([a-zA-Z0-9_-]+)\)", list_result)
        
        if not match:
            pytest.skip("許可されたGoogle Driveの階層に 'test.md' が見つからなかったため、ダウンロードテストはスキップします。")
            
        file_id = match.group(1)
        
        # 3. 実際のフルダウンロード処理を実行（APIを叩く）
        download_result = download_drive_file(file_id)
        
        # 4. 期待通りダウンロードが完了したか検証
        assert "成功しました" in download_result
        
        # 指定したフォルダ (tmp/test/) にちゃんと作られているか？ (テストファイルがGoogle Docの場合 .txt が付与される)
        expected_path1 = os.path.join(test_dir, "test.md")
        expected_path2 = os.path.join(test_dir, "test.md.txt")
        actual_path = expected_path1 if os.path.exists(expected_path1) else expected_path2
        
        assert os.path.exists(actual_path), "test.md または test.md.txt が期待通り tmp/test/ の中に保存されていません！"
        
        # さらに、ファイルが存在するだけでなく中身が空でないか？
        with open(actual_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0, "ダウンロードされたファイルの中身が空っぽです！"

