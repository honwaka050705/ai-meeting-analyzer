"""
Embedding Service - Gemini Embedding API連携モジュール

議事録のembedding生成と類似検索を行う
"""
from typing import Optional
import google.generativeai as genai

from app.config import settings
from app.services.ai_service import AIServiceError, retry_on_error


# =============================================================================
# Gemini Embedding クライアント
# =============================================================================
def get_embedding_model():
    """Gemini Embedding モデルを取得"""
    genai.configure(api_key=settings.gemini_api_key)
    return "models/text-embedding-004"


# =============================================================================
# Embedding 生成
# =============================================================================
@retry_on_error(max_retries=3, delay=1.0)
def generate_embedding(text: str) -> list[float]:
    """
    テキストからembeddingを生成

    Args:
        text: embedding化するテキスト

    Returns:
        768次元のembeddingベクトル

    Raises:
        AIServiceError: embedding生成に失敗した場合
    """
    if not text or not text.strip():
        raise AIServiceError("テキストが空です")

    try:
        genai.configure(api_key=settings.gemini_api_key)

        # テキストが長すぎる場合は先頭を使用（最大10000文字程度）
        truncated_text = text[:10000] if len(text) > 10000 else text

        result = genai.embed_content(
            model="models/text-embedding-004",
            content=truncated_text,
            task_type="retrieval_document"
        )

        embedding = result['embedding']

        if not embedding or len(embedding) != 768:
            raise AIServiceError(f"不正なembedding次元: {len(embedding) if embedding else 0}")

        return embedding

    except AIServiceError:
        raise
    except Exception as e:
        raise AIServiceError(f"Embedding生成中にエラーが発生しました: {str(e)}")


@retry_on_error(max_retries=3, delay=1.0)
def generate_query_embedding(query: str) -> list[float]:
    """
    検索クエリからembeddingを生成

    Args:
        query: 検索クエリテキスト

    Returns:
        768次元のembeddingベクトル
    """
    if not query or not query.strip():
        raise AIServiceError("検索クエリが空です")

    try:
        genai.configure(api_key=settings.gemini_api_key)

        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )

        embedding = result['embedding']

        if not embedding or len(embedding) != 768:
            raise AIServiceError(f"不正なembedding次元: {len(embedding) if embedding else 0}")

        return embedding

    except AIServiceError:
        raise
    except Exception as e:
        raise AIServiceError(f"Query embedding生成中にエラーが発生しました: {str(e)}")


# =============================================================================
# 接続テスト
# =============================================================================
def test_embedding_connection() -> dict:
    """
    Gemini Embedding APIへの接続テスト

    Returns:
        {"status": "ok", "dimensions": int} または {"status": "error", "message": str}
    """
    try:
        test_text = "これはテストです"
        embedding = generate_embedding(test_text)
        return {
            "status": "ok",
            "model": "text-embedding-004",
            "dimensions": len(embedding)
        }
    except Exception as e:
        return {
            "status": "error",
            "model": "text-embedding-004",
            "message": str(e)
        }
