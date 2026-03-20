"""
Google Cloud Secret ManagerからAPIキーを取得する
python -m src.llm.gcp.secret_manager
"""

import os
from dotenv import load_dotenv
from google.cloud import secretmanager

# .envファイルが存在すれば環境変数として読み込む
load_dotenv()

def get_secret_info() -> dict[str, str]:
    project_id = os.getenv("GCP_PROJECT_ID")
    secret_id = os.getenv("GEMINI_SECRET_ID", "gemini-api-key")  # デフォルト値を設定することも可能
    
    if not project_id:
        raise ValueError("環境変数 'GCP_PROJECT_ID' が設定されていません。")
    
    return {
        "project_id": project_id,
        "secret_id": secret_id
    }

def get_secret() -> str:
    """
    .envに直接GEMINI_API_KEYが設定されていればそれを返し、
    設定されていなければプロジェクトのSecret Managerから最新バージョンを取得して返す
    """
    # 1. まずリポジトリ内の.env（環境変数）に直接APIキーが書かれているかチェック
    direct_key = os.getenv("GEMINI_API_KEY")
    if direct_key:
        return direct_key

    # 2. 直接書かれていない場合はSecret Managerから取得する
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{get_secret_info()['project_id']}/secrets/{get_secret_info()['secret_id']}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# 使い方
if __name__ == "__main__":    
    api_key = get_secret()
    print(f"取得したAPIキーの前半: {api_key[:10]}...")
