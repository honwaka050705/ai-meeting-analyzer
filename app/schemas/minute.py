from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# 作成時のリクエスト
class MinuteCreate(BaseModel):
    title: str
    content: str
    meeting_date: datetime


# レスポンス用（タスクなし）
class MinuteBase(BaseModel):
    id: int
    title: str
    content: str
    meeting_date: datetime
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# レスポンス用（タスクあり） - 後で TaskResponse を作成後に更新
class MinuteResponse(MinuteBase):
    pass
