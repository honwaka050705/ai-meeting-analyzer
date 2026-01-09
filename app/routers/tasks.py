from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.task import Task
from app.schemas.task import TaskResponse
from app.services.task_service import (
    get_task as service_get_task,
    get_tasks as service_get_tasks,
)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    minute_id: Optional[int] = None,
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=100, description="取得する最大件数"),
    db: Session = Depends(get_db)
):
    """
    タスク一覧の取得
    
    - **minute_id**: 議事録IDでフィルタ（オプション）
    - ページネーション対応（skip/limit）
    """
    tasks = service_get_tasks(db, minute_id=minute_id, skip=skip, limit=limit)
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """
    タスク詳細の取得
    
    - **task_id**: タスクID
    """
    task = service_get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"タスク ID={task_id} が見つかりません"
        )
    return task
