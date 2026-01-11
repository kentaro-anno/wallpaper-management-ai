from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from .api import endpoints

# 環境変数の読み込み
load_dotenv()

app = FastAPI(title="Wallpaper Management API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境のため
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Wallpaper Management API is running"}
