from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.task import Task
from app.schemas.task import TaskResponse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    minute_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """タスク一覧の取得（議事録ID指定可能）"""
    # Phase 2で実装
    pass


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """タスク詳細の取得"""
    # Phase 2で実装
    pass
