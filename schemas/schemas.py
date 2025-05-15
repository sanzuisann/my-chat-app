from pydantic import BaseModel

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
        from_attributes = True  # ✅ Pydantic v2で必要な設定（旧：orm_mode）
