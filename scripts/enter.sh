#!/bin/bash

# 起動中のコンテナ内でbashを実行する
echo "コンテナ 'mcp-article' の中に入ります..."
docker exec -it -u $(id -u):$(id -g) -e HOME=/app mcp-article bash
