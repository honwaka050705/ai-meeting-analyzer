from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
async def root():
    """ヘルスチェック用エンドポイント"""
    return {"message": "AI Meeting Assistant API is running"}

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy"}
