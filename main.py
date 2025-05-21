from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from uuid import UUID
import os
import uuid
import json
import re

# ✅ 自作モジュール
from models.models import Base, Character, ChatHistory, User, InternalState
from db.database import engine
from schemas.schemas import (
    CharacterCreate, CharacterResponse, CharacterUpdate,
    ChatMessage, ChatHistoryResponse, ChatRequest, UserCreate, EvaluateTrustRequest
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

# ✅ OpenAIクライアントを初期化
client = OpenAI(api_key=api_key)

# ✅ CORSミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ /reset-db エンドポイント（開発用のみ）
@app.get("/reset-db")
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"status": "✅ データベースをUUID対応で再作成しました"}

# ✅ チャット応答エンドポイント
@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    history = db.query(ChatHistory)\
        .filter(ChatHistory.user_id == request.user_id,
                ChatHistory.character_id == request.character_id)\
        .order_by(ChatHistory.timestamp.asc())\
        .limit(10).all()

    messages = [{"role": h.role, "content": h.message} for h in history]
    messages.append({"role": "user", "content": request.user_message})

    character = db.query(Character).filter(Character.id == request.character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    # ✅ 信頼度の取得
    state = db.query(InternalState).filter_by(
        user_id=request.user_id,
        character_id=request.character_id,
        param_name="trust"
    ).first()
    trust = state.value if state else 0

    def trust_to_level(trust: int) -> int:
        if trust >= 7:
            return 4
        elif trust >= 3:
            return 3
        elif trust >= -2:
            return 2
        elif trust >= -6:
            return 1
        else:
            return 0

    def get_prompt_by_level(level: int) -> str:
        prompt_map = {
            0: " 相手を全く信用していないように、冷たく、距離を取って応答してください。",
            1: " 相手に警戒しており、慎重に言葉を選んでください。",
            2: "",
            3: " 少し心を許し、優しく応答してください。",
            4: " 非常に親しい相手として、温かく、積極的に応答してください。"
        }
        return prompt_map.get(level, "")

    trust_level = trust_to_level(int(trust))
    prompt_adjustment = get_prompt_by_level(trust_level)

    full_system_prompt = character.system_prompt + prompt_adjustment
    system_prompt = {"role": "system", "content": full_system_prompt}

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[system_prompt] + messages,
            temperature=0.8,
            max_tokens=200
        )
        reply = response.choices[0].message.content
    except Exception as e:
        print("❌ GPT API エラー:", e)
        return {"reply": f"エラーが発生しました: {str(e)}"}

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
