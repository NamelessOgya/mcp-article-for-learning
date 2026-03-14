FROM python:3.9-slim

# コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 依存パッケージのリスト(requirements.txt)を先にコピー
COPY requirements.txt .

# パッケージのインストールを実行
RUN pip install --no-cache-dir -r requirements.txt

# Dockerfileと同階層以下のファイルをすべてコンテナの/appディレクトリにコピー(マウントに相当)
COPY . .

# （必要に応じて）コンテナ起動時のコマンドを追加してください
# CMD ["python", "app.py"]