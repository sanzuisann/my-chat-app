from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

from backend.db.database import engine
from backend.models.models import Base

print("🔧 テーブルを作成中...")
Base.metadata.create_all(bind=engine)
print("✅ テーブル作成完了！")
