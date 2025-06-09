from fastapi import FastAPI, Depends, HTTPException, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import os
import uuid
import json
import re
import logging

# ✅ ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ 自作モジュール
from models.models import Base, Character, ChatHistory, User, InternalState
from db.database import engine
from schemas.schemas import (
    CharacterCreate,
    CharacterResponse,
    CharacterUpdate,
    ChatMessage,
    ChatHistoryResponse,
    ChatRequest,
    UserCreate,
    EvaluateLikingRequest,
    ConstructCreate,
    ConstructResponse,
)
from crud.crud import (
    get_all_characters,
    create_character,
    get_character_by_name,
    create_construct,
    create_constructs,
    get_constructs,
    delete_construct,
)
from dependencies.dependencies import get_db

app = FastAPI()

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEYが設定されていません。")

client = OpenAI(api_key=api_key)


def extract_intent(user_message: str) -> str:
    """Call GPT to extract a concise conversation intent."""
    system_prompt = (
        "あなたはユーザーの発言から会話の意図を1文で抽出するアシスタントです。"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=50,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("❌ GPT意図抽出エラー: %s", str(e))
        return ""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def map_liking_to_level(liking: int) -> int:
    """Convert raw liking value to a discrete level."""
    if liking <= -5:
        return 0
    elif liking <= -1:
        return 1
    elif liking <= 1:
        return 2
    elif liking <= 5:
        return 3
    else:
        return 4

def build_full_prompt(character, liking_level: int, constructs=None, intent: Optional[str] = None) -> str:
    def get_prompt_by_level(level: int) -> str:
        prompt_map = {
            0: "相手を大嫌いで、極力関わりたくない態度で応答してください。",
            1: "相手をあまり好ましく思っておらず、ぶっきらぼうに応答してください。",
            2: "相手への感情は特になく、淡々と応答してください。",
            3: "相手に好感を抱き、親しげに応答してください。",
            4: "相手が大好きで、喜んで親密に応答してください。"
        }
        return prompt_map.get(level, "")

    prohibited_text = "\n".join(f"- {item}" for item in json.loads(character.prohibited)) if character.prohibited else "なし"
    examples_text = "\n".join(
        f"ユーザー: {ex['user']}\nキャラ: {ex['assistant']}"
        for ex in json.loads(character.examples)
    ) if character.examples else "なし"
    liking_text = get_prompt_by_level(liking_level)
    intent_text = f"\n【ユーザーの意図】\n{intent}" if intent else ""
    def format_construct(c):
        axis = json.loads(c.axis) if isinstance(c.axis, str) else c.axis
        pair = f"{axis[0]} ↔ {axis[1]}" if len(axis) == 2 else ",".join(axis)
        return f"- {c.name} ({pair}) = {c.value} / importance {c.importance}\n  {c.behavior_effect}"

    constructs_text = "\n".join(format_construct(c) for c in constructs) if constructs else "なし"

    return f"""あなたは「{character.name}」というキャラクターとして対話を行います。

このキャラクターの性格は Big Five モデルに基づき、以下の通り数値で表されています。
スコアは 0.0（非常に低い）〜 1.0（非常に高い）の範囲です。

- Openness: {character.openness}
- Conscientiousness: {character.conscientiousness}
- Extraversion: {character.extraversion}
- Agreeableness: {character.agreeableness}
- Neuroticism: {character.neuroticism}

これらの性格特性に基づき、発言内容・話し方・反応を自然に調整してください。

【背景】
{character.background}

【世界観】
{character.world}

【口調】
{character.tone}

【禁止事項】
{prohibited_text}

【会話例】
{examples_text}

【価値軸】
{constructs_text}

{liking_text}{intent_text}
"""

@app.get("/reset-db")
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"status": "✅ データベースをUUID対応で再作成しました"}

@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == request.user_id,
        ChatHistory.character_id == request.character_id
    ).order_by(ChatHistory.timestamp.asc()).limit(10).all()

    messages = [{"role": h.role, "content": h.message} for h in history]
    messages.append({"role": "user", "content": request.user_message})

    character = db.query(Character).filter(Character.id == request.character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    state = db.query(InternalState).filter_by(
        user_id=request.user_id,
        character_id=request.character_id,
        param_name="liking"
    ).first()
    liking = state.value if state else 0
    liking_level = map_liking_to_level(liking)

    constructs = get_constructs(db, request.user_id, request.character_id)

    intent = extract_intent(request.user_message)
    full_system_prompt = build_full_prompt(character, liking_level, constructs, intent)
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
        logger.error("❌ GPT API エラー: %s", str(e))
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

    response_data = {"reply": reply}
    if request.debug:
        response_data["intent"] = intent
    if request.include_prompt:
        response_data["prompt"] = [system_prompt] + messages
    return response_data

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

@app.get("/history/{user_id}/{character_id}")
def get_chat_history(user_id: UUID, character_id: UUID, db: Session = Depends(get_db)):
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id,
        ChatHistory.character_id == character_id
    ).order_by(ChatHistory.timestamp).all()

    return [
        {
            "speaker": h.role,
            "message": h.message,
            "timestamp": h.timestamp.isoformat()
        } for h in history
    ]

@app.post("/characters/", response_model=CharacterResponse)
def create_character_route(character: CharacterCreate, db: Session = Depends(get_db)):
    logger.info("▶️ キャラクター作成リクエスト受信: %s", character.dict())
    db_character = get_character_by_name(db, character.name)
    if db_character:
        raise HTTPException(status_code=400, detail="❌ 名前が既に使われています")
    try:
        result = create_character(db, character)
        result.prohibited = json.loads(result.prohibited) if result.prohibited else None
        result.examples = json.loads(result.examples) if result.examples else None
        logger.info("✅ キャラクター作成成功: %s", result.id)
        return result
    except Exception as e:
        logger.exception("❌ キャラクター作成中にエラー: %s", str(e))
        raise HTTPException(status_code=500, detail="サーバー内部エラーが発生しました")

@app.put("/characters/{name}", response_model=CharacterResponse)
def update_character_route(name: str, update_data: CharacterUpdate, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.name == name).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")

    update_fields = update_data.dict(exclude_unset=True)
    if "prohibited" in update_fields and isinstance(update_fields["prohibited"], list):
        update_fields["prohibited"] = json.dumps(update_fields["prohibited"])
    if "examples" in update_fields and isinstance(update_fields["examples"], list):
        update_fields["examples"] = json.dumps(update_fields["examples"])

    for key, value in update_fields.items():
        setattr(character, key, value)

    db.commit()
    db.refresh(character)
    character.prohibited = json.loads(character.prohibited) if character.prohibited else None
    character.examples = json.loads(character.examples) if character.examples else None
    return character

@app.get("/characters/", response_model=List[CharacterResponse])
def get_characters_route(db: Session = Depends(get_db)):
    characters = get_all_characters(db)
    for char in characters:
        char.prohibited = json.loads(char.prohibited) if char.prohibited else None
        char.examples = json.loads(char.examples) if char.examples else None
    return characters

@app.delete("/characters/{id}")
def delete_character_route(id: UUID, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == id).first()
    if not character:
        raise HTTPException(status_code=404, detail="キャラクターが見つかりません")
    db.delete(character)
    db.commit()
    return {"message": f"キャラクター┈ID: {id}┉を削除しました"}

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

@app.post("/evaluate-liking")
def evaluate_liking(data: EvaluateLikingRequest, db: Session = Depends(get_db)):
    system_prompt = """
    あなたはゲームキャラクターとして、プレイヤーの発言に対する好意度を評価する役割を担っています。
    以下のスケールに基づき、好意度を評価し、出力形式に厳密に従ってください。

    出力スケール:
    -3: 大嫌い
    -2: 嫌い
    -1: あまり好きではない
     0: 中立
    +1: 好き
    +2: かなり好き
    +3: 大好き

    🔒 出力は以下の形式のJSONのみ。全角文字や解説、改行は不要です。
    {
      "score": 整数（-3～+3）, 
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
        param_name="liking"
    ).first()

    if state:
        state.value += score
        state.updated_at = datetime.utcnow()
    else:
        state = InternalState(
            user_id=data.user_id,
            character_id=data.character_id,
            param_name="liking",
            value=score,
            updated_at=datetime.utcnow()
        )
        db.add(state)

    db.commit()

    return {
        "new_liking": state.value,
        "score": score,
        "reason": reason
    }


# --------------------- Construct Endpoints ---------------------

@app.post("/constructs/", response_model=List[ConstructResponse])
def create_construct_route(data: List[ConstructCreate], db: Session = Depends(get_db)):
    constructs = create_constructs(db, data)
    for obj, req in zip(constructs, data):
        obj.axis = req.axis
    return constructs


@app.get("/constructs/{user_id}/{character_id}", response_model=List[ConstructResponse])
def list_constructs_route(user_id: UUID, character_id: UUID, db: Session = Depends(get_db)):
    constructs = get_constructs(db, user_id, character_id)
    for c in constructs:
        c.axis = json.loads(c.axis)
    return constructs


@app.delete("/constructs/{construct_id}")
def delete_construct_route(construct_id: UUID, db: Session = Depends(get_db)):
    c = delete_construct(db, construct_id)
    if not c:
        raise HTTPException(status_code=404, detail="Construct not found")
    return {"message": "deleted"}


@app.post("/constructs/import")
async def import_constructs(file: UploadFile, db: Session = Depends(get_db)):
    content = await file.read()
    lines = content.decode("utf-8").splitlines()
    for line in lines:
        if not line.strip():
            continue
        data = json.loads(line)
        create_construct(db, ConstructCreate(**data))
    return {"status": "imported", "count": len(lines)}


@app.get("/constructs/export/{user_id}/{character_id}")
def export_constructs(user_id: UUID, character_id: UUID, db: Session = Depends(get_db)):
    constructs = get_constructs(db, user_id, character_id)
    jsonl = "\n".join(json.dumps({
        "user_id": str(c.user_id),
        "character_id": str(c.character_id),
        "axis": json.loads(c.axis),
        "name": c.name,
        "importance": c.importance,
        "behavior_effect": c.behavior_effect,
        "value": c.value,
    }) for c in constructs)
    return Response(content=jsonl, media_type="text/plain")

@app.get("/")
def root():
    return {"message": "アプリは動作中です"}
