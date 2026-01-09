from sqlalchemy.orm import Session
from typing import Optional

from app.models.task import Task


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """タスクを1件取得"""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session,
    minute_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> list[Task]:
    """タスク一覧を取得（議事録IDでフィルタ可能）"""
    query = db.query(Task)
    if minute_id:
        query = query.filter(Task.minute_id == minute_id)
    return query.offset(skip).limit(limit).all()
