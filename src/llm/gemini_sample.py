"""
取得したAPIキーを使って、一番安価なGeminiモデルにリクエストを送るサンプル
実行: python -m src.llm.gemini_sample
"""

from google import genai
from src.llm.gcp.secret_manager import get_secret

def main():
    print("🔐 Secret ManagerからAPIキーを取得中...")
    try:
        api_key = get_secret()
    except Exception as e:
        print(f"❌ APIキーの取得に失敗しました: {e}")
        return
        
    print("✅ キーの取得成功！")    
    print("🤖 Geminiクライアントを初期化中...")
    
    # 取得したAPIキーを使ってクライアントを作成
    client = genai.Client(api_key=api_key)
    
    # プロンプト（Geminiへの質問）
    prompt = "あなたは誰ですか？とても短く、1文で自己紹介してください。"
    
    # 現在最も安価でコストパフォーマンスが高いフラッシュモデルを指定
    model_name = "gemini-2.5-flash"
    
    print(f"👉 送信するプロンプト: 「{prompt}」")
    print(f"👉 使用モデル: {model_name}\n")
    print("...リクエスト送信中...\n")
    
    # リクエストの送信
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        print("✨ レスポンスが返ってきました:")
        print("=" * 40)
        print(response.text)
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ リクエストに失敗しました: {e}")

if __name__ == "__main__":
    main()
