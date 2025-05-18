from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os

# ✅ 自作モジュール
from models.models import Base, Character, ChatHistory
from db.database import engine
from schemas.schemas import (
    CharacterCreate, CharacterResponse, CharacterUpdate,
    ChatMessage, ChatHistoryResponse, ChatRequest
)
from crud.crud import get_all_characters, create_character, get_character_by_name
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

# ✅ チャット応答エンドポイント（UUID対応 & 履歴保存）
@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # 過去の履歴を取得（最大10件）
    history = db.query(ChatHistory)\
        .filter(ChatHistory.user_id == request.user_id,
                ChatHistory.character_id == request.character_id)\
        .order_by(ChatHistory.timestamp.asc())\
        .limit(10).all()

    messages = [{"role": h.role, "content": h.message} for h in history]
    messages.append({"role": "user", "content": request.user_message})

    # キャラクターの system_prompt を取得
    character = db.query(Character).filter(Character.id == request.character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    system_prompt = {"role": "system", "content": character.system_prompt}

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[system_prompt] + messages,
            temperature=0.8,
            max_tokens=200
        )
        reply = response.choices[0].message.content
    except Exception as e:
        print("❌ GPT API エラー:", e)
        return {"reply": f"エラーが発生しました: {str(e)}"}

    # ユーザーの発言とAIの返答を保存
    db.add(ChatHistory(
        user_id=request.user_id,
        character_id=request.character_id,
        role="user",
        message=request.user_message
    ))
    db.add(ChatHistory(
        user_id=request.user_id,
        character_id=request.character_id,
        role="assistant",
        message=reply
    ))
    db.commit()

    return {"reply": reply}

# ✅ 会話履歴保存エンドポイント（必要なら残してもOK）
@app.post("/history/")
def save_chat_message(chat: ChatMessage, db: Session = Depends(get_db)):
    new_message = ChatHistory(
        user_id=chat.user_id,
        character_id=chat.character_id,
        role=chat.role,
        message=chat.message
    )
    db.add(new_message)
    db.commit()
    return {"status": "success"}

# ✅ 会話履歴取得エンドポイント
@app.get("/history/{user_id}/{character_id}", response_model=List[ChatHistoryResponse])
def get_chat_history(user_id: str, character_id: str, db: Session = Depends(get_db)):
    history = db.query(ChatHistory)\
        .filter(ChatHistory.user_id == user_id, ChatHistory.character_id == character_id)\
        .order_by(ChatHistory.timestamp)\
        .all()
    return history

# ✅ キャラクター登録エンドポイント
@app.post("/characters/", response_model=CharacterResponse)
def create_character_route(character: CharacterCreate, db: Session = Depends(get_db)):
    db_character = get_character_by_name(db, character.name)
    if db_character:
        raise HTTPException(status_code=400, detail="❌ 名前が既に使われています")
    return create_character(db, character)

# ✅ キャラクター更新エンドポイント
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
@app.delete("/characters/{id}")
def delete_character_route(id: str, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == id).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    db.delete(character)
    db.commit()
    return {"message": f"キャラクター（ID: {id}）を削除しました"}

# ✅ 動作確認用ルート
@app.get("/")
def root():
    return {"message": "アプリは動作中です"}
