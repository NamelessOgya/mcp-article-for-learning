FROM python:3.11-slim

# gcloud CLI (Google Cloud CLI) のインストール
RUN apt-get update && apt-get install -y curl && \
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz && \
    tar -xf google-cloud-cli-linux-x86_64.tar.gz -C /opt && \
    /opt/google-cloud-sdk/install.sh -q && \
    rm google-cloud-cli-linux-x86_64.tar.gz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# gcloudコマンドのパスを通す
ENV PATH $PATH:/opt/google-cloud-sdk/bin

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