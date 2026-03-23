from mcp.server.fastmcp import FastMCP
import os

# サーバーのインスタンスを作成
mcp = FastMCP("LocalFileSystem")

# 操作を許可するベースディレクトリ (このディレクトリ配下のみ操作可能とする安全対策)
# src/mcp/local_fs_mcp.py からプロジェクトルートの tmp ディレクトリを指すように修正
import yaml
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
with open(_config_path, "r", encoding="utf-8") as f:
    _lf_config = yaml.safe_load(f) or {}

BASE_DIR_REL = _lf_config.get("BASE_DIR_REL", "tmp")
BASE_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, BASE_DIR_REL))
os.makedirs(BASE_DIR, exist_ok=True)


def get_safe_path(filename: str) -> str:
    """
    指定されたファイル名がベースディレクトリ配下にあるか検証し、安全な絶対パスを返す。
    ディレクトリトラバーサル攻撃 (例: ../../etc/passwd) を防ぐための対策。
    """
    # 結合して絶対パスにする
    safe_path = os.path.abspath(os.path.join(BASE_DIR, filename))
    
    # 最終的なパスが BASE_DIR で始まっているか確認
    if not safe_path.startswith(BASE_DIR):
        raise ValueError(f"アクセスが拒否されました: {filename} は許可されたディレクトリ外です。")
    return safe_path

@mcp.tool()
def read_file(filename: str) -> str:
    """
    指定されたファイルの内容を読み込みます。
    
    Args:
        filename: 読み込むファイルの名前 (tmpディレクトリからの相対パス)
    """
    try:
        path = get_safe_path(filename)
        if not os.path.exists(path):
            return f"エラー: ファイル '{filename}' が見つかりませんでした。"
            
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"エラーが発生しました: {e}"

@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """
    指定されたファイルに内容を書き込みます（ファイルがない場合は新規作成）。
    
    Args:
        filename: 書き込むファイルの名前 (tmpディレクトリからの相対パス)
        content: 書き込む内容
    """
    try:
        path = get_safe_path(filename)
        # 親ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"ファイル '{filename}' への書き込みが成功しました。"
    except Exception as e:
        return f"エラーが発生しました: {e}"

@mcp.tool()
def list_workspace_files() -> str:
    """
    tmpディレクトリ内のファイル一覧を取得します。
    """
    try:
        files = os.listdir(BASE_DIR)
        if not files:
            return "tmpディレクトリは空です。"
        
        output = "ファイル一覧:\n"
        for file in files:
            output += f"- {file}\n"
        return output
    except Exception as e:
        return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    # MCPサーバーを起動
    mcp.run()
