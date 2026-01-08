from sqlalchemy.orm import Session
from app.models.minute import Minute
from app.schemas.minute import MinuteCreate
from datetime import datetime
from app.models.task import Task


def create_minute(db: Session, minute_data: MinuteCreate) -> Minute:
    """議事録を新規作成"""
    db_minute = Minute(
        title=minute_data.title,
        content=minute_data.content,
        meeting_date=minute_data.meeting_date
    )
    db.add(db_minute)
    db.commit()
    db.refresh(db_minute)
    return db_minute


def get_minute(db: Session, minute_id: int) -> Minute | None:
    """議事録を1件取得"""
    return db.query(Minute).filter(Minute.id == minute_id).first()


def get_minutes(db: Session, skip: int = 0, limit: int = 100) -> list[Minute]:
    """議事録一覧を取得"""
    return db.query(Minute).offset(skip).limit(limit).all()


def delete_minute(db: Session, minute_id: int) -> bool:
    """議事録を削除"""
    db_minute = get_minute(db, minute_id)
    if db_minute:
        db.delete(db_minute)
        db.commit()
        return True
    return False

def update_summary(db: Session, minute_id: int, summary: str) -> Minute | None:
    """議事録の要約を更新"""
    db_minute = get_minute(db, minute_id)
    if db_minute:
        db_minute.summary = summary
        db_minute.updated_at = datetime.now()
        db.commit()
        db.refresh(db_minute)
    return db_minute


def create_tasks_from_ai(db: Session, minute_id: int, tasks_data: list[dict]) -> list[Task]:
    """AI抽出結果からタスクを一括作成"""
    created_tasks = []
    
    for task_data in tasks_data:
        due_date = None
        if task_data.get("due_date"):
            try:
                due_date = datetime.strptime(task_data["due_date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                due_date = None
        
        db_task = Task(
            minute_id=minute_id,
            assignee=task_data["assignee"],
            content=task_data["content"],
            due_date=due_date,
            status="pending"
        )
        db.add(db_task)
        created_tasks.append(db_task)
    
    db.commit()
    for task in created_tasks:
        db.refresh(task)
    
    return created_tasks


def delete_tasks_by_minute(db: Session, minute_id: int) -> int:
    """議事録に紐づくタスクをすべて削除"""
    deleted_count = db.query(Task).filter(Task.minute_id == minute_id).delete()
    db.commit()
    return deleted_count


def analyze_and_save(db: Session, minute_id: int) -> dict:
    """議事録のAI分析を実行し、結果をDBに保存"""
    from app.services.ai_service import analyze_minute as ai_analyze
    
    db_minute = get_minute(db, minute_id)
    if not db_minute:
        raise ValueError(f"議事録 ID={minute_id} が見つかりません")
    
    result = ai_analyze(db_minute.content)
    delete_tasks_by_minute(db, minute_id)
    update_summary(db, minute_id, result["summary"])
    create_tasks_from_ai(db, minute_id, result["tasks"])
    
    return {
        "minute_id": minute_id,
        "summary": result["summary"],
        "tasks": result["tasks"]
    }
