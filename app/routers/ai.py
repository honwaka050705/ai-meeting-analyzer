"""
AI関連のルーター（テスト・デバッグ用）
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai_service import (
    test_connection,
    generate_summary,
    extract_tasks,
    analyze_minute,
    AIServiceError
)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class TestAnalyzeRequest(BaseModel):
    """テスト用分析リクエスト"""
    content: str

    class Config:
        json_schema_extra = {
            "example": {
                "content": """
【出席者】田中、佐藤、鈴木

【議題】
1. プロジェクトAの進捗確認
2. 新機能の仕様検討

【内容】
田中より、プロジェクトAは予定通り進行中との報告。
来週月曜日までに佐藤がデザインカンプを作成する。
鈴木は今週金曜までにAPI設計書を完成させる。

【決定事項】
- 新機能はReactで実装することに決定
- 次回MTGは1/15（水）14:00
                """
            }
        }


@router.get("/health")
async def ai_health_check():
    """
    Gemini APIへの接続テスト
    
    Returns:
        接続状態とモデル情報
    """
    result = test_connection()
    return result


@router.post("/test/summarize")
async def test_summarize(request: TestAnalyzeRequest):
    """
    要約生成のテスト
    
    テスト用エンドポイント。DBへの保存は行わない。
    """
    try:
        summary = generate_summary(request.content)
        return {
            "status": "success",
            "summary": summary
        }
    except AIServiceError as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/test/extract-tasks")
async def test_extract_tasks(request: TestAnalyzeRequest):
    """
    タスク抽出のテスト
    
    テスト用エンドポイント。DBへの保存は行わない。
    """
    try:
        tasks = extract_tasks(request.content)
        return {
            "status": "success",
            "tasks": tasks
        }
    except AIServiceError as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/test/analyze")
async def test_analyze(request: TestAnalyzeRequest):
    """
    要約生成＆タスク抽出の統合テスト
    
    テスト用エンドポイント。DBへの保存は行わない。
    """
    try:
        result = analyze_minute(request.content)
        return {
            "status": "success",
            **result
        }
    except AIServiceError as e:
        return {
            "status": "error",
            "message": str(e)
        }
