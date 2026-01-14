from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.routers import minutes, tasks

from app.routers.ai import router as ai_router
from app.routers.search import router as search_router

app = FastAPI(
    title="AI Meeting Assistant API",
    description="議事録要約＆タスク抽出API",
    version="0.1.0"
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(minutes.router)
app.include_router(tasks.router)
app.include_router(ai_router)
app.include_router(search_router)


# === カスタム例外 ===
class MinuteNotFoundError(Exception):
    def __init__(self, minute_id: int):
        self.minute_id = minute_id


class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id


# === 例外ハンドラー ===
@app.exception_handler(MinuteNotFoundError)
async def minute_not_found_handler(request: Request, exc: MinuteNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"議事録 ID={exc.minute_id} が見つかりません"}
    )


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"タスク ID={exc.task_id} が見つかりません"}
    )


# === ヘルスチェック ===
@app.get("/")
async def root():
    return {"message": "AI Meeting Assistant API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """DBヘルスチェック"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": str(e)}
        )
