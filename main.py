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
    # ✅ 最新10件の履歴を取得
    history = db.query(ChatHistory)\
        .filter(ChatHistory.user_id == request.user_id,
                ChatHistory.character_id == request.character_id)\
        .order_by(ChatHistory.timestamp.asc())\
        .limit(10).all()

    messages = [{"role": h.role, "content": h.message} for h in history]
    messages.append({"role": "user", "content": request.user_message})

    # ✅ キャラクター情報の取得
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

    # ✅ 信頼度に応じたレベル変換
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

    # ✅ 各レベルに応じたトーン変化を定義
    def get_prompt_by_level(level: int) -> str:
        prompt_map = {
            0: "相手を全く信用していないように、冷たく、距離を取って応答してください。",
            1: "相手に警戒しており、慎重に言葉を選んでください。",
            2: "",  # 中立
            3: "少し心を許し、優しく応答してください。",
            4: "非常に親しい相手として、温かく、積極的に応答してください。"
        }
        return prompt_map.get(level, "")

    # ✅ 信頼度に応じたプロンプト生成
    trust_level = trust_to_level(int(trust))
    prompt_adjustment = get_prompt_by_level(trust_level)
    full_system_prompt = character.system_prompt + " " + prompt_adjustment
    system_prompt = {"role": "system", "content": full_system_prompt}

    # ✅ GPTに会話送信
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

    # ✅ 履歴保存
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
# ✅ 会話履歴保存（任意）
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

# ✅ 会話履歴取得（UUID対応）
@app.get("/history/{user_id}/{character_id}", response_model=List[ChatHistoryResponse])
def get_chat_history(user_id: UUID, character_id: UUID, db: Session = Depends(get_db)):
    history = db.query(ChatHistory)\
        .filter(ChatHistory.user_id == user_id, ChatHistory.character_id == character_id)\
        .order_by(ChatHistory.timestamp)\
        .all()
    return history

# ✅ キャラクター登録
@app.post("/characters/", response_model=CharacterResponse)
def create_character_route(character: CharacterCreate, db: Session = Depends(get_db)):
    db_character = get_character_by_name(db, character.name)
    if db_character:
        raise HTTPException(status_code=400, detail="❌ 名前が既に使われています")
    return create_character(db, character)

# ✅ キャラクター更新
@app.put("/characters/{name}", response_model=CharacterResponse)
def update_character_route(name: str, update_data: CharacterUpdate, db: Session = Depends(get_db)):
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

# ✅ キャラクター一覧取得
@app.get("/characters/", response_model=List[CharacterResponse])
def get_characters_route(db: Session = Depends(get_db)):
    characters = get_all_characters(db)
    return characters

# ✅ キャラクター削除（UUID対応）
@app.delete("/characters/{id}")
def delete_character_route(id: UUID, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == id).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    db.delete(character)
    db.commit()
    return {"message": f"キャラクター（ID: {id}）を削除しました"}

# ✅ ユーザー登録エンドポイントを追加
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="ユーザー名は既に存在します")

    new_user = User(username=user.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username}

# ✅ 信頼度評価エンドポイント
@app.post("/evaluate-trust")
def evaluate_trust(data: EvaluateTrustRequest, db: Session = Depends(get_db)):
    system_prompt = """
    あなたはゲームキャラクターとして、プレイヤーの発言に対する信頼度を評価する役割を担っています。
    以下のスケールに基づき、信頼度を評価し、出力形式に厳密に従ってください。

    出力スケール:
    -3: 全く信頼できない
    -2: かなり疑わしい
    -1: 少し怪しい
     0: 中立
    +1: やや信頼できる
    +2: かなり信頼できる
    +3: 非常に信頼できる

    🔒 出力は以下の形式のJSONのみ。全角文字や解説、改行は不要です。
    {
      "score": 整数（-3〜+3）, 
      "reason": "理由（簡潔に）"
    }
    """

    user_input = f'プレイヤーの発言: "{data.player_message}" を評価してください。'

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        raw_output = response.choices[0].message.content.strip()

        match = re.search(r'{.*}', raw_output, re.DOTALL)
        if not match:
            raise HTTPException(status_code=500, detail="GPTの応答からJSONを抽出できませんでした")

        result = json.loads(match.group())
        score = int(result["score"])
        reason = result.get("reason", "")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT呼び出しエラー: {str(e)}")

    state = db.query(InternalState).filter_by(
        user_id=data.user_id,
        character_id=data.character_id,
        param_name="trust"
    ).first()

    if state:
        state.value += score
        state.updated_at = datetime.utcnow()
    else:
        state = InternalState(
            user_id=data.user_id,
            character_id=data.character_id,
            param_name="trust",
            value=score,
            updated_at=datetime.utcnow()
        )
        db.add(state)

    db.commit()

    return {
        "new_trust": state.value,
        "score": score,
        "reason": reason
    }

# ✅ ルート確認
@app.get("/")
def root():
    return {"message": "アプリは動作中です"}
