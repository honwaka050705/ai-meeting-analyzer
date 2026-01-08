"""
AI分析結果のスキーマ
"""
from typing import List, Optional
from pydantic import BaseModel


class TaskExtracted(BaseModel):
    """AI抽出されたタスク（DB保存前）"""
    assignee: str
    content: str
    due_date: Optional[str] = None  # "YYYY-MM-DD" or None


class AnalyzeResponse(BaseModel):
    """分析結果のレスポンス"""
    minute_id: int
    summary: str
    tasks: List[TaskExtracted]

    class Config:
        json_schema_extra = {
            "example": {
                "minute_id": 1,
                "summary": "## 議題\n- 今週の進捗確認\n\n## 決定事項\n- 新機能の実装方針を決定",
                "tasks": [
                    {
                        "assignee": "田中",
                        "content": "要件定義書の初稿作成",
                        "due_date": "2025-01-20"
                    },
                    {
                        "assignee": "佐藤",
                        "content": "デザインモックのレビュー",
                        "due_date": None
                    }
                ]
            }
        }
