from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List
from schemas.schemas import CharacterUpdate
from models.models import Character
import os

from models.models import Base
from db.database import engine
from schemas.schemas import CharacterCreate, CharacterResponse  # ✅ CharacterCreate を追加
from crud.crud import get_all_characters, create_character, get_character_by_name  # ✅ 2つ追加
from dependencies.dependencies import get_db

# ✅ FastAPIアプリ初期化
app = FastAPI()

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

# ✅ キャラクター登録エンドポイント ← ★ここを追加！
@app.post("/characters/", response_model=CharacterResponse)
def create_character_route(character: CharacterCreate, db: Session = Depends(get_db)):
    db_character = get_character_by_name(db, character.name)
    if db_character:
        raise HTTPException(status_code=400, detail="❌ 名前が既に使われています")
    return create_character(db, character)

# ✅ キャラクター情報更新エンドポイント
@app.put("/characters/{name}", response_model=CharacterResponse)
def update_character_route(
    name: str,
    update_data: CharacterUpdate,
    db: Session = Depends(get_db)
):
    character = db.query(Character).filter(Character.name == name).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    if update_data.personality is not None:
        character.personality = update_data.personality
    if update_data.system_prompt is not None:
        character.system_prompt = update_data.system_prompt

    db.commit()
    db.refresh(character)

    return character

# ✅ キャラクター一覧取得エンドポイント
@app.get("/characters/", response_model=List[CharacterResponse])
def get_characters_route(db: Session = Depends(get_db)):
    characters = get_all_characters(db)
    return characters

# ✅ キャラクター削除エンドポイント
@app.delete("/characters/{name}")
def delete_character_route(name: str, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.name == name).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    db.delete(character)
    db.commit()
    return {"message": f"キャラクター「{name}」を削除しました"}

@app.get("/")
def root():
    return {"message": "アプリは動作中です"}
