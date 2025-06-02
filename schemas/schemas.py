from pydantic import BaseModel
from typing import Optional, Literal, List, Dict
from uuid import UUID
from datetime import datetime

# 🔸 登録リクエスト用（キャラ新規作成）
class CharacterCreate(BaseModel):
    name: str                                 # キャラ名
    personality: str                          # 性格
    system_prompt: str                        # 基本プロンプト（予備）

    # ✅ 拡張項目
    background: Optional[str] = None          # 背景設定（ストーリー的な役割）
    tone: Optional[str] = None                # 口調（丁寧語・砕けた口調など）
    world: Optional[str] = None               # 世界観（どんな世界にいるキャラか）
    prohibited: Optional[List[str]] = None    # 禁止事項（文字列のリスト）
    examples: Optional[List[Dict[str, str]]] = None  # 対話例（{"user": "...", "assistant": "..."} のリスト）

# 🔹 取得レスポンス用（キャラ情報表示）
class CharacterResponse(BaseModel):
    id: UUID
    name: str
    personality: str
    system_prompt: str

    # ✅ 拡張項目
    background: Optional[str] = None
    tone: Optional[str] = None
    world: Optional[str] = None
    prohibited: Optional[List[str]] = None
    examples: Optional[List[Dict[str, str]]] = None

    class Config:
        from_attributes = True

# 🛠️ 更新リクエスト用（キャラ編集）
class CharacterUpdate(BaseModel):
    personality: Optional[str] = None
    system_prompt: Optional[str] = None

    # ✅ 拡張項目（更新可能に）
    background: Optional[str] = None
    tone: Optional[str] = None
    world: Optional[str] = None
    prohibited: Optional[List[str]] = None
    examples: Optional[List[Dict[str, str]]] = None

# 🔸 チャット送信用リクエスト（UUID指定）
class ChatRequest(BaseModel):
    user_id: UUID
    character_id: UUID
    user_message: str

# 🔸 会話履歴保存用リクエスト（UUID対応）
class ChatMessage(BaseModel):
    user_id: UUID
    character_id: UUID
    role: Literal["user", "assistant"]
    message: str

# 🔹 会話履歴取得用レスポンス
class ChatHistoryResponse(BaseModel):
    role: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

# 🔸 ユーザー登録用
class UserCreate(BaseModel):
    username: str

# ✅ 信頼度評価用リクエスト
class EvaluateTrustRequest(BaseModel):
    user_id: UUID
    character_id: UUID
    player_message: str
