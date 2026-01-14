"""
検索関連のルーター
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import SearchQuery, SearchResponse, SimilarMinute
from app.services.search_service import (
    search_similar_minutes,
    update_minute_embedding,
    update_all_embeddings,
)
from app.services.embedding_service import test_embedding_connection
from app.services.ai_service import AIServiceError
from app.services.minute_service import get_minute

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("/health")
async def embedding_health_check():
    """
    Gemini Embedding APIへの接続テスト

    Returns:
        接続状態とモデル情報
    """
    result = test_embedding_connection()
    return result


@router.post("", response_model=SearchResponse)
async def search_minutes(
    request: SearchQuery,
    db: Session = Depends(get_db)
):
    """
    類似議事録を検索（セマンティック検索）

    - **query**: 検索クエリ（自然言語）
    - **limit**: 取得件数（1-20、デフォルト5）

    embeddingが未生成の議事録は検索対象外です。
    """
    try:
        results = search_similar_minutes(
            db=db,
            query=request.query,
            limit=request.limit
        )

        return SearchResponse(
            query=request.query,
            results=[SimilarMinute(**r) for r in results],
            total=len(results)
        )

    except AIServiceError as e:
        raise HTTPException(
            status_code=503,
            detail=f"検索中にエラーが発生しました: {str(e)}"
        )


@router.post("/minutes/{minute_id}/embedding")
async def generate_minute_embedding(
    minute_id: int,
    db: Session = Depends(get_db)
):
    """
    指定した議事録のembeddingを生成・更新

    - **minute_id**: 議事録ID

    既存のembeddingがある場合は上書きされます。
    """
    # 議事録の存在確認
    minute = get_minute(db, minute_id)
    if not minute:
        raise HTTPException(
            status_code=404,
            detail=f"議事録 ID={minute_id} が見つかりません"
        )

    try:
        success = update_minute_embedding(db, minute_id)
        if success:
            return {
                "status": "success",
                "message": f"議事録 ID={minute_id} のembeddingを生成しました",
                "minute_id": minute_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Embedding生成に失敗しました"
            )

    except AIServiceError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Embedding生成中にエラーが発生しました: {str(e)}"
        )


@router.post("/embeddings/batch")
async def batch_generate_embeddings(db: Session = Depends(get_db)):
    """
    全議事録のembeddingを一括生成

    既存のembeddingがある議事録も再生成されます。
    大量のデータがある場合は時間がかかります。
    """
    try:
        result = update_all_embeddings(db)
        return {
            "status": "success",
            "updated": result["updated"],
            "failed": result["failed"],
            "errors": result["errors"] if result["errors"] else None
        }

    except AIServiceError as e:
        raise HTTPException(
            status_code=503,
            detail=f"一括生成中にエラーが発生しました: {str(e)}"
        )


@router.get("/minutes/{minute_id}/similar", response_model=SearchResponse)
async def find_similar_minutes(
    minute_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    指定した議事録に類似する議事録を検索

    - **minute_id**: 基準となる議事録ID
    - **limit**: 取得件数（1-20、デフォルト5）

    指定した議事録自身は結果から除外されます。
    """
    # 議事録の存在確認
    minute = get_minute(db, minute_id)
    if not minute:
        raise HTTPException(
            status_code=404,
            detail=f"議事録 ID={minute_id} が見つかりません"
        )

    try:
        # 議事録の内容をクエリとして検索
        query_text = f"{minute.title}\n{minute.content}"
        results = search_similar_minutes(
            db=db,
            query=query_text,
            limit=limit,
            exclude_id=minute_id
        )

        return SearchResponse(
            query=f"議事録 ID={minute_id} に類似",
            results=[SimilarMinute(**r) for r in results],
            total=len(results)
        )

    except AIServiceError as e:
        raise HTTPException(
            status_code=503,
            detail=f"類似検索中にエラーが発生しました: {str(e)}"
        )
