from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Minute(Base):
    __tablename__ = "minutes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    meeting_date = Column(DateTime, nullable=False)
    summary = Column(Text, nullable=True)  # AI生成の要約
    embedding = Column(Vector(768), nullable=True)  # Gemini embedding (768次元)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Taskとのリレーション
    tasks = relationship("Task", back_populates="minute", cascade="all, delete-orphan")
