from backend.db.database import engine
from backend.models.models import Base

print("🔧 テーブルを作成中...")
Base.metadata.create_all(bind=engine)
print("✅ テーブル作成完了！")
