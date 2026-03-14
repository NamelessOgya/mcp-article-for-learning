#!/bin/bash

# 現在のディレクトリ(プロジェクトルート)の絶対パスを取得
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# イメージ名のビルド
echo "Dockerイメージのビルドを開始します..."
docker build -t mcp-article "$PROJECT_ROOT"

# コンテナの起動（バックグラウンド実行、プロセスを維持するためにsleep infinityを指定）
# カレントディレクトリをコンテナの/appにバインドマウントします
echo "コンテナを起動しています..."
docker run -d --rm --name mcp-article -v "$PROJECT_ROOT":/app mcp-article sleep infinity

echo "コンテナの起動が完了しました。'./scripts/enter.sh' でコンテナ内に入ることができます。"
