from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.minute import Minute
from app.schemas.minute import MinuteCreate, MinuteResponse

router = APIRouter(prefix="/api/v1/minutes", tags=["minutes"])


@router.post("", response_model=MinuteResponse)
async def create_minute(minute: MinuteCreate, db: Session = Depends(get_db)):
    """議事録の新規作成"""
    # Phase 2で実装
    pass


@router.get("", response_model=List[MinuteResponse])
async def get_minutes(db: Session = Depends(get_db)):
    """議事録一覧の取得"""
    # Phase 2で実装
    pass


@router.get("/{minute_id}", response_model=MinuteResponse)
async def get_minute(minute_id: int, db: Session = Depends(get_db)):
    """議事録詳細の取得"""
    # Phase 2で実装
    pass


@router.delete("/{minute_id}")
async def delete_minute(minute_id: int, db: Session = Depends(get_db)):
    """議事録の削除"""
    # Phase 2で実装
    pass


@router.post("/{minute_id}/analyze")
async def analyze_minute(minute_id: int, db: Session = Depends(get_db)):
    """要約＆タスク抽出を実行"""
    # Phase 2で実装
    pass
