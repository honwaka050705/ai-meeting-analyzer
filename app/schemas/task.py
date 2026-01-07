from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_serializer


class TaskBase(BaseModel):
    assignee: str
    content: str
    due_date: Optional[date] = None


class TaskCreate(TaskBase):
    minute_id: int


class TaskResponse(TaskBase):
    id: int
    minute_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('due_date')
    def serialize_due_date(self, value: Optional[date]) -> str:
        """due_dateがNullの場合は'期限未定'を返す"""
        if value is None:
            return "期限未定"
        return value.strftime("%Y-%m-%d")
