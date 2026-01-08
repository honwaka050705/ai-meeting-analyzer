from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.minute import Minute
from app.schemas.analyze import AnalyzeResponse
from app.schemas.minute import MinuteCreate, MinuteResponse
from app.services.minute_service import (
    create_minute as service_create_minute,
    get_minute as service_get_minute,
    get_minutes as service_get_minutes,
    delete_minute as service_delete_minute,
    analyze_and_save as service_analyze_and_save,
)
from app.services.ai_service import AIServiceError

router = APIRouter(prefix="/api/v1/minutes", tags=["minutes"])


@router.post("", response_model=MinuteResponse, status_code=201)
async def create_minute(minute: MinuteCreate, db: Session = Depends(get_db)):
    """
    議事録の新規作成
    
    - **title**: 会議タイトル（必須、255文字以内）
    - **content**: 議事録本文（必須）
    - **meeting_date**: 会議日時（必須、ISO 8601形式）
    """
    # バリデーション: タイトルの長さチェック
    if len(minute.title) > 255:
        raise HTTPException(
            status_code=400,
            detail="タイトルは255文字以内で入力してください"
        )
    
    # バリデーション: 本文の空チェック
    if not minute.content.strip():
        raise HTTPException(
            status_code=400,
            detail="議事録本文を入力してください"
        )
    
    db_minute = service_create_minute(db, minute)
    return db_minute


@router.get("", response_model=List[MinuteResponse])
async def get_minutes(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=100, description="取得する最大件数"),
    db: Session = Depends(get_db)
):
    """
    議事録一覧の取得
    
    ページネーション対応（skip/limit）
    """
    minutes = service_get_minutes(db, skip=skip, limit=limit)
    return minutes


@router.get("/{minute_id}", response_model=MinuteResponse)
async def get_minute(minute_id: int, db: Session = Depends(get_db)):
    """
    議事録詳細の取得
    
    - **minute_id**: 議事録ID
    """
    db_minute = service_get_minute(db, minute_id)
    if db_minute is None:
        raise HTTPException(
            status_code=404,
            detail=f"議事録 ID={minute_id} が見つかりません"
        )
    return db_minute


@router.delete("/{minute_id}", status_code=204)
async def delete_minute(minute_id: int, db: Session = Depends(get_db)):
    """
    議事録の削除
    
    - **minute_id**: 削除する議事録ID
    - 関連するタスクも同時に削除されます（CASCADE）
    """
    success = service_delete_minute(db, minute_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"議事録 ID={minute_id} が見つかりません"
        )
    return None


@router.post("/{minute_id}/analyze", response_model=AnalyzeResponse)
async def analyze_minute(minute_id: int, db: Session = Depends(get_db)):
    """
    要約＆タスク抽出を実行
    
    - **minute_id**: 分析する議事録ID
    - 議事録本文をAIで分析し、要約とタスクを自動生成
    - 結果はDBに保存され、議事録詳細から確認可能
    - 再実行時は既存のタスクが削除され、新しい結果で上書き
    """
    # 議事録の存在確認
    db_minute = service_get_minute(db, minute_id)
    if db_minute is None:
        raise HTTPException(
            status_code=404,
            detail=f"議事録 ID={minute_id} が見つかりません"
        )
    
    try:
        # AI分析を実行し、結果をDBに保存
        result = service_analyze_and_save(db, minute_id)
        return AnalyzeResponse(
            minute_id=result["minute_id"],
            summary=result["summary"],
            tasks=result["tasks"]
        )
    except AIServiceError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI分析中にエラーが発生しました: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"予期しないエラーが発生しました: {str(e)}"
        )
