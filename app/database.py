from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# データベースエンジンの作成
engine = create_engine(settings.database_url)

# セッションの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Baseクラス（モデルの基底クラス）
Base = declarative_base()

def get_db():
    """依存性注入用のDB接続関数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
