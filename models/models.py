# models.py
import uuid  # ← ファイル先頭に追加
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Character(Base):
    __tablename__ = "characters"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))  # ✅ UUID自動生成
    name = Column(String, unique=True, nullable=False)
    personality = Column(String, nullable=False)
    system_prompt = Column(String, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))  # ✅ UUID自動生成
    username = Column(String, unique=True, nullable=False)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))  # ✅ UUID自動生成
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    character_id = Column(String, ForeignKey("characters.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
