from fastapi import APIRouter
import os
from pydantic import BaseModel
from ...services.settings_service import SettingsService

router = APIRouter()
settings_service = SettingsService()

DEFAULT_FOLDER = os.getenv("WALLPAPER_TARGET_FOLDER", "")

class SaveSettingsRequest(BaseModel):
    target_folder: str
    output_folder: str
    workers: int

@router.post("/save")
async def save_settings(request: SaveSettingsRequest):
    """設定を保存する"""
    settings_service.update_env_variable("WALLPAPER_TARGET_FOLDER", request.target_folder)
    settings_service.update_env_variable("WALLPAPER_OUTPUT_FOLDER", request.output_folder)
    settings_service.update_env_variable("WALLPAPER_WORKERS", str(request.workers))
    return {"message": "Settings saved successfully"}

@router.get("/browse")
async def browse_folder(initial_dir: str = DEFAULT_FOLDER):
    """フォルダ選択ダイアログを開く"""
    selected_path = settings_service.browse_folder(initial_dir)
    return {"path": selected_path}

@router.get("/stats")
async def get_stats(folder: str = DEFAULT_FOLDER):
    """統計情報を取得する"""
    if not os.path.exists(folder):
        return {"total_images": 0, "duplicates": 0, "classified": 0}
        
    filenames = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    return {
        "total_images": len(filenames),
        "duplicates": 0,
        "classified": 0
    }
