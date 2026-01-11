from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import shutil
from ..services.duplicate_service import DuplicateService
from ..services.classify_service import ClassifyService
from ..services.settings_service import SettingsService

router = APIRouter()
duplicate_service = DuplicateService()
classify_service = ClassifyService()
settings_service = SettingsService()

# 壁紙フォルダのデフォルトパス（環境変数から読み込み、未設定なら空文字）
DEFAULT_FOLDER = os.getenv("WALLPAPER_TARGET_FOLDER", "")

class ScanRequest(BaseModel):
    folder: str = DEFAULT_FOLDER
    threshold: float = 0.5
    metric: str = "probability"  # "probability", "margin", "entropy"
    workers: int = 4

class ExecuteRequest(BaseModel):
    results: List[Dict]
    mode: str  # 'move' or 'copy'
    folder: str
    output_folder: Optional[str] = None

class DeleteRequest(BaseModel):
    path: str

@router.get("/status")
async def get_status():
    return {"status": "ok", "folder": DEFAULT_FOLDER}

@router.get("/system/info")
async def get_system_info():
    """システム情報を取得する（CPUコア数など）"""
    return {
        "cpu_count": os.cpu_count(),
        "device": "cuda" if classify_service.device == "cuda" else "cpu"
    }

@router.get("/images/preview")
async def preview_image(path: str):
    """画像をプレビュー用に配信する"""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)

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

@router.get("/settings/browse")
async def browse_folder(initial_dir: str = DEFAULT_FOLDER):
    """フォルダ選択ダイアログを開く"""
    selected_path = settings_service.browse_folder(initial_dir)
    return {"path": selected_path}

@router.post("/duplicates/scan")
async def scan_duplicates(request: ScanRequest):
    try:
        duplicates = await duplicate_service.find_similar_images(request.folder, request.workers)
        return {"duplicates": duplicates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/duplicates/delete")
async def delete_duplicate(request: DeleteRequest):
    if duplicate_service.delete_image(request.path):
        return {"message": "Deleted successfully"}
    raise HTTPException(status_code=404, detail="File not found")

@router.post("/classify/scan")
async def scan_seasons(request: ScanRequest):
    if not os.path.exists(request.folder):
        raise HTTPException(status_code=404, detail="Folder not found")
        
    filenames = [f for f in os.listdir(request.folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    results = []
    
    try:
        classify_service.load_model()
    except Exception as e:
        print(f"Model load error: {e}")
        raise HTTPException(status_code=500, detail=f"Model load failed: {str(e)}")
    
    targets = filenames # 制限を解除 (全件処理)
    print(f"Starting classification for {len(targets)} images (Metric: {request.metric}, Threshold: {request.threshold}, Workers: {request.workers})...")
    
    import asyncio
    loop = asyncio.get_event_loop()
    
    async def process_batch(paths):
        tasks = [loop.run_in_executor(None, classify_service.analyze_image_sync, p) for p in paths]
        return await asyncio.gather(*tasks)

    # バッチサイズをワーカー数に合わせる
    batch_size = request.workers
    for i in range(0, len(targets), batch_size):
        batch_filenames = targets[i:i + batch_size]
        batch_paths = [os.path.join(request.folder, f) for f in batch_filenames]
        batch_results = await process_batch(batch_paths)
        
        for result in batch_results:
            if result:
                u = result['uncertainty']
                is_unknown = False
                if request.metric == "probability":
                    max_prob = max(result['probs'].values())
                    is_unknown = max_prob < request.threshold
                elif request.metric == "margin":
                    is_unknown = u['margin_confidence'] < request.threshold
                elif request.metric == "entropy":
                    is_unknown = u['entropy'] > request.threshold
                    
                result['is_unknown'] = is_unknown
                results.append(result)
            
    return {"results": results, "total_processed": len(results), "skipped": len(filenames) - len(results)}

@router.post("/classify/execute")
async def execute_classification(request: ExecuteRequest):
    """結果に基づいてファイルを移動またはコピーする"""
    success_count = 0
    errors = []
    
    # 出力先を決定（指定がなければ入力フォルダと同じ）
    base_target = request.output_folder if request.output_folder else request.folder
    
    for item in request.results:
        src_path = item['path']
        if not os.path.exists(src_path):
            errors.append(f"File not found: {src_path}")
            continue
            
        if item.get('is_unknown'):
            subfolder = "unknown"
        else:
            # prediction から季節名を取得 (e.g. "a photo of spring" -> "spring")
            subfolder = item['prediction'].split(' ').pop().lower()
            
        target_dir = os.path.join(base_target, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        
        dest_path = os.path.join(target_dir, os.path.basename(src_path))
        
        try:
            if request.mode == 'move':
                shutil.move(src_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)
            success_count += 1
        except Exception as e:
            errors.append(f"Error {request.mode}ing {os.path.basename(src_path)}: {e}")
            
    return {"message": f"Successfully {request.mode}d {success_count} files", "errors": errors}
