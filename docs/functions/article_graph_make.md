# article_graph_forward_agent

## 概要
論文のタイトルを入力として受け取り、その論文について以下のような作業を行うAI-agentをMCP。  
当該論文の研究をさらに発展させた内容があるか？を確認するためのMCPになります。
  
1. **対象論文**の論文名を受け取り、受け取った論文名の論文を引用している論文をDLする。(被引用降 20件まで)
2. DLした論文に関して、中身を確認し、**対象論文**との関係性について**引用種類**と**引用関係詳細**として出力してください。
    - 引用種類
        - **継承引用**: **対象論文**で明らかになった内容を元にそれを発展させたり、異なる切り口で検証している。
        - **例示引用**: **対象論文**で提案されている内容を継承しているわけではないが、近い研究分野の論文として引用している。    
        - **比較引用**: **対象論文**で提案されている内容と比較している。    
        - **利用引用**: **対象論文**で提案されている手法やモデルを、自身の研究で利用している。(特に手法自体を発展させたりしていない。)
    - 引用関係詳細
        - **対象論文**の中で、どのような理由で引用されているかを自然言語で出力 (30文字程度)
3. **継承引用**に該当するもののをMCPの戻り値として出力してください。

## 使い方（How to use it）
MCPサーバー `ArticleGraphServer` を起動し、`article_graph_forward_agent` ツールを実行します。

### 引数
- `target_article_name` (str): **対象論文**のタイトル（例: `"LANGUAGE REPRESENTATIONS CAN BE WHAT RECOMMENDERS NEED: FINDINGS AND POTENTIALS"`）

### 戻り値
分析結果のサマリーテキストと、全引用論文の判定結果（`引用論文名`, `引用種類`, `引用関係詳細`）をまとめたCSV形式の文字列が返されます。
同時に、このCSVデータはローカルの `tmp/article_graph_output/{safe_title}.csv` にファイルとして自動保存されます。

### 動作例
```json
{
  "target_article_name": "Attention Is All You Need"
}
```

**出力文字列の例**:
```
対象論文 'Attention Is All You Need' に対する引用分析が完了しました。
分析対象論文数: 20件
CSV保存先: /home/masashiueno/mcp-article-for-learning/tmp/article_graph_output/AttentionIsAllYouNeed.csv
==================================================
引用論文名,引用種類,引用関係詳細
BERT: Pre-training of Deep Bidirectional Transformers...,継承引用,Transformerアーキテクチャを発展させ双方向モデルを構築した。
Some Other Paper Not On Arxiv,エラー,エラー
...
```

## 注意事項
- 初回実行時や引用数が多い論文の場合、Semantic Scholar や arXiv API から大量の論文を検索・ダウンロードするため、完了までに数分〜十数分かかる場合があります。
- 引用論文全文の取得には arXiv を使用しています。論文が arXiv に存在しない場合やアクセスが制限されている場合、処理は安全にスキップされ、出力CSVの引用種類と詳細はともに「エラー」となります。
- 内部で `gemini-2.5-flash` を使用しているため、GCP Secret Manager にアクセスするための認証設定（APIキー）が済んでいる必要があります。