from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

# 🔸 登録リクエスト用
class CharacterCreate(BaseModel):
    name: str
    personality: str
    system_prompt: str

# 🔹 取得レスポンス用（UUID対応）
class CharacterResponse(BaseModel):
    id: UUID
    name: str
    personality: str
    system_prompt: str

    class Config:
        from_attributes = True

# 🛠️ 更新リクエスト用
class CharacterUpdate(BaseModel):
    personality: Optional[str] = None
    system_prompt: Optional[str] = None

# 🔸 チャットリクエスト用（UUID）
class ChatRequest(BaseModel):
    user_id: UUID
    character_id: UUID
    user_message: str

# 🔸 会話保存リクエスト用（UUIDに変更）
class ChatMessage(BaseModel):
    user_id: UUID
    character_id: UUID
    role: Literal["user", "assistant"]
    message: str

# 🔹 会話履歴取得レスポンス用
class ChatHistoryResponse(BaseModel):
    role: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

# 🔸 ユーザー登録リクエスト用スキーマ
class UserCreate(BaseModel):
    username: str

# ✅ 信頼度評価リクエスト用スキーマ（新規追加）
class EvaluateTrustRequest(BaseModel):
    user_id: UUID
    character_id: UUID
    player_message: str
