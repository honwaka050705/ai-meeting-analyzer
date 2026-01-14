"""
Search Service - ベクトル検索モジュール

pgvectorを使った類似議事録検索を行う
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.minute import Minute
from app.services.embedding_service import generate_embedding, generate_query_embedding
from app.services.ai_service import AIServiceError


def update_minute_embedding(db: Session, minute_id: int) -> bool:
    """
    議事録のembeddingを生成・更新

    Args:
        db: DBセッション
        minute_id: 議事録ID

    Returns:
        成功した場合True
    """
    minute = db.query(Minute).filter(Minute.id == minute_id).first()
    if not minute:
        return False

    try:
        # タイトルと本文を結合してembedding生成
        text_for_embedding = f"{minute.title}\n\n{minute.content}"
        embedding = generate_embedding(text_for_embedding)

        # embeddingを更新（SQLで直接更新）
        db.execute(
            text("UPDATE minutes SET embedding = :embedding WHERE id = :id"),
            {"embedding": str(embedding), "id": minute_id}
        )
        db.commit()
        return True

    except AIServiceError:
        raise
    except Exception as e:
        db.rollback()
        raise AIServiceError(f"Embedding更新中にエラーが発生しました: {str(e)}")


def search_similar_minutes(
    db: Session,
    query: str,
    limit: int = 5,
    exclude_id: Optional[int] = None
) -> List[dict]:
    """
    類似議事録を検索

    Args:
        db: DBセッション
        query: 検索クエリ
        limit: 取得件数
        exclude_id: 除外する議事録ID（自身を除外する場合）

    Returns:
        類似議事録のリスト（similarity付き）
    """
    try:
        # クエリのembeddingを生成
        query_embedding = generate_query_embedding(query)
        
        # ベクトルを文字列に変換
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # コサイン類似度で検索（1 - cosine_distance = similarity）
        exclude_clause = "AND id != :exclude_id" if exclude_id else ""

        sql = text(f"""
            SELECT
                id,
                title,
                content,
                meeting_date,
                summary,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM minutes
            WHERE embedding IS NOT NULL
            {exclude_clause}
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """)

        params = {
            "query_embedding": str(query_embedding),
            "limit": limit
        }
        if exclude_id:
            params["exclude_id"] = exclude_id

        result = db.execute(sql, params)
        rows = result.fetchall()

        similar_minutes = []
        for row in rows:
            similar_minutes.append({
                "id": row.id,
                "title": row.title,
                "meeting_date": row.meeting_date,
                "similarity": round(float(row.similarity), 4),
                "summary": row.summary,
                "content_preview": row.content[:200] + "..." if len(row.content) > 200 else row.content
            })

        return similar_minutes

    except AIServiceError:
        raise
    except Exception as e:
        raise AIServiceError(f"類似検索中にエラーが発生しました: {str(e)}")


def update_all_embeddings(db: Session) -> dict:
    """
    全議事録のembeddingを一括更新

    Returns:
        {"updated": int, "failed": int, "errors": list}
    """
    minutes = db.query(Minute).all()
    updated = 0
    failed = 0
    errors = []

    for minute in minutes:
        try:
            success = update_minute_embedding(db, minute.id)
            if success:
                updated += 1
            else:
                failed += 1
                errors.append(f"ID={minute.id}: 議事録が見つかりません")
        except Exception as e:
            failed += 1
            errors.append(f"ID={minute.id}: {str(e)}")

    return {
        "updated": updated,
        "failed": failed,
        "errors": errors[:10]  # 最大10件のエラーのみ返す
    }
