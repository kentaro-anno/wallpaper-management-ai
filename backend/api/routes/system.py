from fastapi import APIRouter
import os
from ...services.classify_service import ClassifyService

router = APIRouter()
classify_service = ClassifyService()

@router.get("/status")
async def get_status():
    default_folder = os.getenv("WALLPAPER_TARGET_FOLDER", "")
    return {"status": "ok", "folder": default_folder}

@router.get("/info")
async def get_system_info():
    """システム情報を取得する（CPUコア数など）"""
    return {
        "cpu_count": os.cpu_count(),
        "device": "cuda" if classify_service.device == "cuda" else "cpu"
    }
