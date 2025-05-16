from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

# 🔸 登録リクエスト用
class CharacterCreate(BaseModel):
    name: str
    personality: str
    system_prompt: str

# 🔹 取得レスポンス用
class CharacterResponse(BaseModel):
    id: int
    name: str
    personality: str
    system_prompt: str

    class Config:
        from_attributes = True  # ※ Pydantic v2 で必要

# 🛠️ 更新リクエスト用
class CharacterUpdate(BaseModel):
    personality: Optional[str] = None
    system_prompt: Optional[str] = None

# 🔸 会話保存リクエスト用
class ChatMessage(BaseModel):
    user_id: int
    character_id: int
    role: Literal["user", "assistant"]
    message: str

# 🔹 会話履歴取得レスポンス用
class ChatHistoryResponse(BaseModel):
    role: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True
