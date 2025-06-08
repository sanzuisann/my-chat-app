import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID  # PostgreSQL用UUID型

# ✅ SQLAlchemyのベースモデル
Base = declarative_base()

# 🧠 キャラクター情報（AIの人格設定など）
class Character(Base):
    __tablename__ = "characters"

    # 一意のID（UUID）
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # キャラクター名（ユニーク）
    name = Column(String, unique=True, nullable=False)

    # キャラクターの基本的な性格・人格（例：「冷静で優しい」など）
    personality = Column(String, nullable=False)

    # 最低限のSystem Prompt（バックアップ用）
    system_prompt = Column(Text, nullable=False)

    # ✅ 拡張項目 -----------------------------

    # キャラクターの背景設定（例：「古代のAI」「記憶を失っている」など）
    background = Column(Text, nullable=True)

    # 口調の指定（例：「丁寧語」「乱暴」「関西弁」など）
    tone = Column(String, nullable=True)

    # 世界観（キャラクターが属する物語世界や時代背景など）
    world = Column(Text, nullable=True)

    # 禁止事項リスト（JSON文字列で保存）
    # 例: '["現実世界の話をしない", "攻撃的な発言をしない"]'
    prohibited = Column(Text, nullable=True)

    # 対話例（ユーザーとキャラクターの例会話をJSONで保存）
    # 例: '[{"user": "こんにちは", "assistant": "やあ、よく来たね"}]'
    examples = Column(Text, nullable=True)

    # Big Five スコア
    openness = Column(Float, nullable=False, default=0.5)
    conscientiousness = Column(Float, nullable=False, default=0.5)
    extraversion = Column(Float, nullable=False, default=0.5)
    agreeableness = Column(Float, nullable=False, default=0.5)
    neuroticism = Column(Float, nullable=False, default=0.5)

# 👤 ユーザー（プレイヤー）情報
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, nullable=False)

# 💬 チャット履歴（ユーザーとキャラクターのやり取り）
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # 発言したユーザー
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 会話相手となるキャラクター
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)

    # 発言者の区別："user" または "assistant"
    role = Column(String, nullable=False)

    # 発言内容
    message = Column(Text, nullable=False)

    # 発言タイムスタンプ
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# 🔧 内部状態（信頼度などの内部パラメータ）を管理
class InternalState(Base):
    __tablename__ = "internal_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # 対象ユーザー
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 対象キャラクター
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)

    # 状態の名前（例："trust", "affection", "anger" など）
    param_name = Column(String, nullable=False)

    # 値（整数）例：信頼度 -10〜+10
    value = Column(Integer, default=0)

    # 最終更新日時（自動更新）
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# 🏷️ 価値軸（コンストラクト）
class Construct(Base):
    """User specific value axis for a character."""

    __tablename__ = "constructs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # 関連ユーザー
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 関連キャラクター
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)

    # 軸の両極値ペアをJSON文字列で保持
    axis = Column(Text, nullable=False)

    # 軸の名称
    name = Column(String, nullable=False)

    # 重要度（0〜5程度を想定）
    importance = Column(Integer, default=0)

    # 行動への影響説明
    behavior_effect = Column(Text, nullable=False)

    # 値（-5～+5 程度を想定）
    value = Column(Integer, default=0)
