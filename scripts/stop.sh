#!/bin/bash

# 起動中のコンテナを停止する
# コンテナ起動時に --rm オプションをつけているため停止と同時にコンテナは自動削除されます
echo "コンテナ 'mcp-article' を停止しています..."
docker stop mcp-article

echo "コンテナの停止が完了しました。"
