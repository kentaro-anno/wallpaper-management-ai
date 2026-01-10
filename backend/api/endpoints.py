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

# 壁紙フォルダのデフォルトパス
DEFAULT_FOLDER = r"[PRIVATE_PATH]"

class ScanRequest(BaseModel):
    folder: str = DEFAULT_FOLDER
    threshold: float = 0.5
    metric: str = "probability"  # "probability", "margin", "entropy"

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
        duplicates = await duplicate_service.find_similar_images(request.folder)
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
    
    targets = filenames[:50]
    print(f"Starting classification for {len(targets)} images (Metric: {request.metric}, Threshold: {request.threshold})...")
    
    import asyncio
    loop = asyncio.get_event_loop()
    
    for i, filename in enumerate(targets):
        path = os.path.join(request.folder, filename)
        result = await loop.run_in_executor(None, classify_service.analyze_image_sync, path)
        if result:
            u = result['uncertainty']
            # メトリックに応じて判定
            is_unknown = False
            if request.metric == "probability":
                # 自信の最大値が閾値以下なら Unknown
                max_prob = max(result['probs'].values())
                is_unknown = max_prob < request.threshold
            elif request.metric == "margin":
                # 1位と2位の差が閾値以下なら Unknown
                is_unknown = u['margin_confidence'] < request.threshold
            elif request.metric == "entropy":
                # エントロピー（迷い度）が閾値以上なら Unknown
                is_unknown = u['entropy'] > request.threshold
                
            result['is_unknown'] = is_unknown
            results.append(result)
            
    return {"results": results, "total_processed": len(results), "skipped": len(filenames) - len(targets)}

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
