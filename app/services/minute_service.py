from sqlalchemy.orm import Session
from app.models.minute import Minute
from app.schemas.minute import MinuteCreate


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
