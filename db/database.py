from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 環境変数からDB URLを取得
DATABASE_URL = os.getenv("DATABASE_URL")

# 接続エンジンとセッション作成
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
