import os
import io
from dotenv import load_dotenv

# .envファイルから環境変数をロードする
load_dotenv()

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GoogleDrive")

# ダウンロードなど読み取り機能のみを許可する安全なスコープ
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# 認証情報の格納場所とダウンロード先
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_FILE = os.path.join(PROJECT_ROOT, 'token.json')
BASE_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "tmp"))

# セキュリティ対策: 許可するルートフォルダ名 (この中身しか操作できないようにする)
ALLOWED_FOLDER_NAME = os.getenv("ALLOWED_DRIVE_FOLDER_NAME", "研究計画かすみん")

def get_drive_service():
    """Google Drive APIへの認証を通し、サービスインスタンスを返す"""
    creds = None
    
    # 手法S: Secret Manager から動的に JSON キー文字列を取得する (ファイルに保存しない最もセキュアな方法)
    try:
        from src.llm.gcp.secret_manager import get_raw_secret
        import json
        from google.oauth2.service_account import Credentials as SACredentials
        
        secret_json_str = get_raw_secret("DRIVE_CREDENTIALS_SECRET_ID", "drive-credentials")
        if secret_json_str:
            creds_info = json.loads(secret_json_str)
            print("💡 Secret Managerから資格情報(JSON)を動的に取得し、Drive APIに接続します。")
            creds = SACredentials.from_service_account_info(creds_info, scopes=SCOPES)
            return build('drive', 'v3', credentials=creds)
    except Exception:
        pass
    
    # 手法A: 開発者が意図的に credentials.json を配置している場合（個人のGoogleドライブ全体にアクセスしたい時用）
    if os.path.exists(CREDENTIALS_FILE) or os.path.exists(TOKEN_FILE):
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(CREDENTIALS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_console()
                
            if creds:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                    
    # 手法B: GCE等の環境で、OAuth情報が無い場合はVMのデフォルト権限（ADC）を全自動で使用する
    if not creds:
        import google.auth
        print("💡 OAuth認証情報が見つからないため、GCEのデフォルトサービスアカウント(ADC)を使用してDrive APIに接続します。")
        creds, project = google.auth.default(scopes=SCOPES)
        
    return build('drive', 'v3', credentials=creds)

def get_allowed_folder_id(service) -> str:
    """許可されたルートフォルダのIDを取得する"""
    results = service.files().list(
        q=f"name='{ALLOWED_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    if not items:
        raise ValueError(f"許可された安全なフォルダ '{ALLOWED_FOLDER_NAME}' がGoogle Drive内に見つかりません。")
    return items[0]['id']

def verify_safe_file(service, file_id: str, allowed_folder_id: str) -> bool:
    """ディレクトリトラバーサル対策: 対象ファイルが許可されたフォルダ配下に存在するか検証する"""
    current_id = file_id
    visited = set()
    while current_id:
        if current_id == allowed_folder_id:
            return True
        if current_id in visited:
            break
        visited.add(current_id)
        
        try:
            file_meta = service.files().get(fileId=current_id, fields='parents').execute()
            parents = file_meta.get('parents', [])
            if not parents:
                return False
            # ルートまでの最初の親を辿る
            current_id = parents[0]
        except Exception:
            return False
    return False

@mcp.tool()
def list_drive_files(folder_id: str = "") -> str:
    """
    Google Drive上のアクセス可能なファイルとフォルダの一覧を取得します。
    目的のファイルの名前から「ファイルID」を特定したい場合や、フォルダの構造を探索したい場合に使用します。
    
    Args:
        folder_id: (オプショナル) 中身を確認したいフォルダのファイルID。空の場合はアクセス可能な親ディレクトリのファイルから取得します。
    """
    try:
        service = get_drive_service()
        allowed_folder_id = get_allowed_folder_id(service)
        
        # ターゲットフォルダの決定（空の場合は許可ルートフォルダを検索）
        target_folder = folder_id if folder_id else allowed_folder_id
        
        # セキュリティチェック (指定フォルダが許可されたフォルダの配下にあるか)
        if target_folder != allowed_folder_id:
            if not verify_safe_file(service, target_folder, allowed_folder_id):
                return f"セキュリティエラー: フォルダ '{target_folder}' は許可されたディレクトリ（{ALLOWED_FOLDER_NAME}）の外部にあるためアクセスできません。"
        
        # 検索クエリの組み立て
        query = f"'{target_folder}' in parents and trashed=false"
            
        results = service.files().list(
            q=query,
            pageSize=50,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        items = results.get('files', [])
        if not items:
            return "ファイルやフォルダが見つかりませんでした。共有設定などを確認してください。"
            
        output = "ファイル・フォルダ一覧:\n"
        for item in items:
            kind = "📁 フォルダ" if item.get('mimeType') == 'application/vnd.google-apps.folder' else "📄 ファイル"
            output += f"- {kind}: '{item.get('name')}' (ID: {item.get('id')})\n"
            
        return output
        
    except Exception as e:
        return f"ファイル一覧の取得中にエラーが発生しました: {e}"

@mcp.tool()
def download_drive_file(file_id: str) -> str:
    """
    指定されたファイルIDのGoogle Driveファイルをダウンロードし、ローカルディレクトリ(tmp)に保存します。
    ファイルの種類に応じて自動的に適切な形式（テキストやPDF）でダウンロード処理・エクスポートが行われます。
    
    Args:
        file_id: Google ドライブでのファイルのID (ブラウザ上のURLに含まれる英数字の文字列)
    """
    try:
        service = get_drive_service()
        allowed_folder_id = get_allowed_folder_id(service)
        
        # セキュリティチェック (指定ファイルが許可されたフォルダの配下にあるか検証)
        if not verify_safe_file(service, file_id, allowed_folder_id):
            return f"セキュリティエラー: ファイルID '{file_id}' は指定された保護ディレクトリ（{ALLOWED_FOLDER_NAME}）の外部にあるためダウンロードできません。"
        
        # ファイルのメタデータ（種類や名前）を取得
        file_metadata = service.files().get(fileId=file_id, fields='id, name, mimeType').execute()
        mime_type = file_metadata.get('mimeType', '')
        file_name = file_metadata.get('name', f'downloaded_file_{file_id}')
        
        request = None
        
        # Google Docs等（Google Workspace専用形式）の場合は、そのままダウンロードできないためエクスポートする
        if mime_type.startswith('application/vnd.google-apps.'):
            if "document" in mime_type:
                # ドキュメントはLLMが読みやすいようにテキストとして書き出し
                request = service.files().export_media(fileId=file_id, mimeType='text/plain')
                if not file_name.endswith('.txt'): file_name += '.txt'
            elif "spreadsheet" in mime_type:
                # スプレッドシートはCSVで書き出し
                request = service.files().export_media(fileId=file_id, mimeType='text/csv')
                if not file_name.endswith('.csv'): file_name += '.csv'
            else:
                # プレゼンなどはすべてPDFに書き出し
                request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
                if not file_name.endswith('.pdf'): file_name += '.pdf'
        else:
            # 論文（PDF）や画像などの「通常のファイル」は、そのままの形式でダウンロードする
            request = service.files().get_media(fileId=file_id)

        if not request:
            return f"エラー: このタイプのファイル ({mime_type}) に関するダウンロードはサポートされていません。"

        # 保存先ディレクトリの準備と保存処理
        os.makedirs(BASE_DIR, exist_ok=True)
        file_path = os.path.join(BASE_DIR, file_name)

        # メディアダウンロード処理
        fh = io.FileIO(file_path, mode='wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        return f"✅ ファイルのダウンロードが成功しました。保存先: {file_path}"
        
    except Exception as e:
        return f"❌ ファイルのダウンロード中にエラーが発生しました。存在しないIDか、権限がない可能性があります: {e}"

if __name__ == "__main__":
    # 直接実行した場合はMCPサーバーとしてリッスンを開始
    mcp.run()
