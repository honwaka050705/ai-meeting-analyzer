"""
検索関連のスキーマ
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """類似検索リクエスト"""
    query: str = Field(..., min_length=1, max_length=1000, description="検索クエリ")
    limit: int = Field(5, ge=1, le=20, description="取得件数")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "プロジェクトの進捗確認について",
                "limit": 5
            }
        }


class SimilarMinute(BaseModel):
    """類似議事録の検索結果"""
    id: int
    title: str
    meeting_date: datetime
    similarity: float = Field(..., description="類似度スコア（0-1、1が最も類似）")
    summary: Optional[str] = None
    content_preview: str = Field(..., description="本文の先頭200文字")

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """検索結果レスポンス"""
    query: str
    results: List[SimilarMinute]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "query": "プロジェクトの進捗確認について",
                "results": [
                    {
                        "id": 1,
                        "title": "2025年1月プロジェクト定例会",
                        "meeting_date": "2025-01-15T14:00:00",
                        "similarity": 0.92,
                        "summary": "## 議題\n- 進捗確認...",
                        "content_preview": "本日の定例会議では..."
                    }
                ],
                "total": 1
            }
        }
