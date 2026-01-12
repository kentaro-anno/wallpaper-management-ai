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
    device = "CUDA" if classify_service.device == "cuda" else "CPU"
    cores = os.cpu_count() or 4
    recommended = max(1, int(cores * 0.75))
    
    # 環境変数から取得（失敗時は推奨値）
    try:
        raw_workers = os.getenv("WALLPAPER_WORKERS", "")
        # 数字を抽出
        import re
        numeric_match = re.search(r'\d+', str(raw_workers))
        workers = int(numeric_match.group()) if numeric_match else recommended
    except Exception:
        workers = recommended

    return {
        "device": device,
        "cpu_cores": cores,
        "workers": workers
    }
