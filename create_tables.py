from db.database import engine
from models.models import Base

print("🔧 テーブルを作成中...")
Base.metadata.create_all(bind=engine)
print("✅ テーブル作成完了！")
