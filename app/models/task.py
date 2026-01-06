from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    minute_id = Column(Integer, ForeignKey("minutes.id", ondelete="CASCADE"), nullable=False)
    assignee = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    due_date = Column(Date, nullable=True)  # 期限未定の場合はNULL
    status = Column(String(20), default="pending")  # pending/in_progress/completed
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Minuteとのリレーション
    minute = relationship("Minute", back_populates="tasks")
    