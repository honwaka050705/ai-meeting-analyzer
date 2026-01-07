"""
AI Service - Gemini API連携モジュール

議事録の要約生成とタスク抽出を行う
"""
import json
import re
from datetime import datetime
from typing import Optional
import google.generativeai as genai

from app.config import settings


# =============================================================================
# カスタム例外
# =============================================================================
class AIServiceError(Exception):
    """AI Service の基底例外クラス"""
    pass


class AIConnectionError(AIServiceError):
    """API接続エラー"""
    pass


class AIResponseParseError(AIServiceError):
    """AIレスポンスのパースエラー"""
    pass


class AIRateLimitError(AIServiceError):
    """レート制限エラー"""
    pass


# =============================================================================
# プロンプト定義
# =============================================================================
SUMMARY_PROMPT = """
以下の会議議事録を、ビジネスパーソンが素早く内容を把握できるように要約してください。

【要約のルール】
- セクション（見出し）と箇条書きの構成で記述
- 以下のセクションを含める：
  * 議題
  * 決定事項
  * 課題・懸念点
  * その他
- 各セクションは2-4項目程度の箇条書き
- 該当する内容がないセクションは「特になし」と記載

【出力フォーマット例】
## 議題
- 〇〇について
- △△の進捗確認

## 決定事項
- 〇〇を採用することに決定
- △△は来週再検討

## 課題・懸念点
- 〇〇のリソース不足
- △△の納期調整が必要

## その他
- 次回MTGは1/20（月）14:00

【議事録】
{content}
"""

TASK_EXTRACTION_PROMPT = """
以下の会議議事録から、アクションアイテム（タスク）を抽出してください。

【抽出ルール】
- 明確な担当者が指定されているタスクのみ抽出
- 「〜を検討する」などの曖昧な表現は除外
- 期限が明記されている場合は"YYYY-MM-DD"形式
- 期限が明記されていない場合はnull
- 担当者が設定されていれば、期限がなくても抽出する
- タスクが見つからない場合は空の配列を返す

以下のJSON形式のみで出力してください（説明文は不要）：
{{
  "tasks": [
    {{
      "assignee": "担当者名",
      "content": "タスク内容",
      "due_date": "YYYY-MM-DD または null"
    }}
  ]
}}

【例】
入力: 「田中さんは1月20日までに要件定義書を作成」
出力: {{"assignee": "田中", "content": "要件定義書を作成", "due_date": "2025-01-20"}}

入力: 「佐藤さんはデザインモックを作成お願いします」
出力: {{"assignee": "佐藤", "content": "デザインモックを作成", "due_date": null}}

【議事録】
{content}
"""


# =============================================================================
# Gemini クライアント初期化
# =============================================================================
def get_gemini_client():
    """Gemini APIクライアントを取得"""
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)


# =============================================================================
# リトライデコレータ
# =============================================================================
def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """API呼び出し失敗時のリトライデコレータ"""
    import time
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_message = str(e).lower()
                    
                    # レート制限エラーの場合は長めに待機
                    if "rate" in error_message or "quota" in error_message:
                        wait_time = delay * (2 ** attempt) * 2  # より長い待機
                        print(f"Rate limit hit, waiting {wait_time}s...")
                    else:
                        wait_time = delay * (2 ** attempt)
                    
                    if attempt < max_retries - 1:
                        print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                        time.sleep(wait_time)
            
            # 最終的に失敗した場合
            raise AIConnectionError(f"API call failed after {max_retries} retries: {last_exception}")
        return wrapper
    return decorator


# =============================================================================
# AI処理関数
# =============================================================================
@retry_on_error(max_retries=3, delay=1.0)
def generate_summary(content: str) -> str:
    """
    議事録から要約を生成
    
    Args:
        content: 議事録本文
        
    Returns:
        要約テキスト（Markdown形式）
        
    Raises:
        AIServiceError: AI処理に失敗した場合
    """
    if not content or not content.strip():
        raise AIServiceError("議事録の内容が空です")
    
    try:
        model = get_gemini_client()
        prompt = SUMMARY_PROMPT.format(content=content)
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # 安定した出力のため低めに設定
                max_output_tokens=2048,
            )
        )
        
        if not response.text:
            raise AIResponseParseError("AIからの応答が空です")
        
        return response.text.strip()
        
    except AIServiceError:
        raise
    except Exception as e:
        raise AIServiceError(f"要約生成中にエラーが発生しました: {str(e)}")


@retry_on_error(max_retries=3, delay=1.0)
def extract_tasks(content: str) -> list[dict]:
    """
    議事録からタスクを抽出
    
    Args:
        content: 議事録本文
        
    Returns:
        タスクのリスト [{"assignee": str, "content": str, "due_date": str|None}, ...]
        
    Raises:
        AIServiceError: AI処理に失敗した場合
    """
    if not content or not content.strip():
        raise AIServiceError("議事録の内容が空です")
    
    try:
        model = get_gemini_client()
        prompt = TASK_EXTRACTION_PROMPT.format(content=content)
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # JSON出力の安定性のためさらに低く
                max_output_tokens=2048,
            )
        )
        
        if not response.text:
            raise AIResponseParseError("AIからの応答が空です")
        
        # JSONをパース
        tasks = _parse_tasks_response(response.text)
        return tasks
        
    except AIServiceError:
        raise
    except Exception as e:
        raise AIServiceError(f"タスク抽出中にエラーが発生しました: {str(e)}")


def _parse_tasks_response(response_text: str) -> list[dict]:
    """
    AIのレスポンスからタスクリストをパース
    
    Args:
        response_text: AIからのレスポンステキスト
        
    Returns:
        タスクのリスト
    """
    try:
        # マークダウンのコードブロックを除去
        text = response_text.strip()
        if text.startswith("```"):
            # ```json や ``` を除去
            text = re.sub(r'^```\w*\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        # JSONパース
        data = json.loads(text)
        
        if "tasks" not in data:
            raise AIResponseParseError("レスポンスに'tasks'キーがありません")
        
        tasks = data["tasks"]
        
        # 各タスクのバリデーションと正規化
        validated_tasks = []
        for task in tasks:
            validated_task = _validate_and_normalize_task(task)
            if validated_task:
                validated_tasks.append(validated_task)
        
        return validated_tasks
        
    except json.JSONDecodeError as e:
        raise AIResponseParseError(f"JSONパースエラー: {str(e)}\nレスポンス: {response_text[:200]}")


def _validate_and_normalize_task(task: dict) -> Optional[dict]:
    """
    タスクデータのバリデーションと正規化
    
    Args:
        task: タスクの辞書
        
    Returns:
        正規化されたタスク、または無効な場合はNone
    """
    # 必須フィールドの確認
    if not task.get("assignee") or not task.get("content"):
        return None
    
    # due_dateの正規化
    due_date = task.get("due_date")
    if due_date:
        # "期限未定" や "null" 文字列の場合はNoneに
        if due_date in ["期限未定", "null", "None", ""]:
            due_date = None
        else:
            # 日付形式の検証
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                # 不正な日付形式の場合はNoneに
                due_date = None
    
    return {
        "assignee": task["assignee"].strip(),
        "content": task["content"].strip(),
        "due_date": due_date
    }


# =============================================================================
# 統合処理関数
# =============================================================================
def analyze_minute(content: str) -> dict:
    """
    議事録の要約生成とタスク抽出を一括実行
    
    Args:
        content: 議事録本文
        
    Returns:
        {
            "summary": str,
            "tasks": list[dict]
        }
    """
    summary = generate_summary(content)
    tasks = extract_tasks(content)
    
    return {
        "summary": summary,
        "tasks": tasks
    }


# =============================================================================
# 接続テスト用関数
# =============================================================================
def test_connection() -> dict:
    """
    Gemini APIへの接続テスト
    
    Returns:
        {"status": "ok", "model": str} または {"status": "error", "message": str}
    """
    try:
        model = get_gemini_client()
        response = model.generate_content(
            "Say 'Hello' in Japanese.",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=50,
            )
        )
        return {
            "status": "ok",
            "model": settings.gemini_model,
            "test_response": response.text.strip()
        }
    except Exception as e:
        return {
            "status": "error",
            "model": settings.gemini_model,
            "message": str(e)
        }
