from pydantic import BaseModel
from typing import Optional

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

