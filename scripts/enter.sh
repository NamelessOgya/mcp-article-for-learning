#!/bin/bash

# 起動中のコンテナ内でbashを実行する
echo "コンテナ 'mcp-article' の中に入ります..."
docker exec -it mcp-article bash
