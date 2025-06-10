# db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# ✅ Render上に登録したDATABASE_URLを読み込む
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URLが設定されていません。")

# ✅ SQLAlchemyエンジンとセッションの初期化
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
