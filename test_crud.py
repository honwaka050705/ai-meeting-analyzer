from datetime import datetime
from app.database import SessionLocal
from app.models.minute import Minute
from app.models.task import Task

db = SessionLocal()

# 議事録作成
minute = Minute(
    title="テスト会議",
    content="テスト内容です",
    meeting_date=datetime.now()
)
db.add(minute)
db.commit()
db.refresh(minute)
print(f"作成された議事録: ID={minute.id}, Title={minute.title}")

# タスク作成
task = Task(
    minute_id=minute.id,
    assignee="田中",
    content="テストタスク",
    due_date=None
)
db.add(task)
db.commit()
db.refresh(task)
print(f"作成されたタスク: ID={task.id}, Assignee={task.assignee}")

# リレーション確認
print(f"議事録のタスク: {minute.tasks}")

db.close()
