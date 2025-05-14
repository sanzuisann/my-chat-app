from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os

from models.models import Base
from db.database import engine

# ✅ FastAPIアプリ初期化（ここだけ！）
app = FastAPI()

# ✅ テーブル作成用のルート（1回だけアクセス）
@app.get("/init-db")
def init_db_route():
    Base.metadata.create_all(bind=engine)
    return {"message": "✅ テーブル作成完了"}

# ✅ .envの読み込み
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# ✅ APIキーを取得
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEYが設定されていません。")

# ✅ OpenAIクライアントを初期化（新方式）
client = OpenAI(api_key=api_key)

# ✅ CORSミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 会話履歴
chat_history = []

# ✅ Pydanticモデル
class MessageData(BaseModel):
    message: str

# ✅ チャットエンドポイント
@app.post("/chat")
async def chat(data: MessageData):
    chat_history.append({"role": "user", "content": data.message})

    system_prompt = {
        "role": "system",
        "content": "あなたは静かな村に住む親切な魔法使いです。旅人に丁寧に応対し、時に謎めいたヒントを与えます。"
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[system_prompt] + chat_history[-10:],
            temperature=0.8,
            max_tokens=200
        )
        reply = response.choices[0].message.content
    except Exception as e:
        print("❌ GPT API エラー:", e)
        return {"reply": f"エラーが発生しました: {str(e)}"}

    chat_history.append({"role": "assistant", "content": reply})
    return {"reply": reply}
