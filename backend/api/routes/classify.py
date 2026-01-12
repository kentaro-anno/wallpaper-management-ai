from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import shutil
import asyncio
from pathlib import Path
from ...services.classify_service import ClassifyService

router = APIRouter()
classify_service = ClassifyService()

DEFAULT_FOLDER = os.getenv("WALLPAPER_TARGET_FOLDER", "")

class ScanRequest(BaseModel):
    folder: str = DEFAULT_FOLDER
    threshold: float = 0.5
    metric: str = "probability"
    workers: int = 4

class ExecuteRequest(BaseModel):
    results: List[Dict]
    mode: str
    folder: str
    output_folder: Optional[str] = None

@router.get("/preview")
async def preview_image(path: str):
    """画像をプレビュー用に配信する"""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return FileResponse(path)

@router.post("/scan")
async def scan_seasons(request: ScanRequest):
    if not os.path.exists(request.folder):
        raise HTTPException(status_code=404, detail="Folder not found")
        
    filenames = [f for f in os.listdir(request.folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    results = []
    
    try:
        classify_service.load_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model load failed: {str(e)}")
    
    targets = filenames
    loop = asyncio.get_event_loop()
    
    async def process_batch(paths):
        tasks = [loop.run_in_executor(None, classify_service.analyze_image_sync, p) for p in paths]
        return await asyncio.gather(*tasks)

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
                    
                result['path'] = Path(result['path']).absolute().as_posix()
                result['is_unknown'] = is_unknown
                results.append(result)
            
    return {"results": results, "total_processed": len(results), "skipped": len(filenames) - len(results)}

@router.post("/execute")
async def execute_classification(request: ExecuteRequest):
    success_count = 0
    errors = []
    base_target = request.output_folder if request.output_folder else request.folder
    
    for item in request.results:
        src_path = item['path']
        if not os.path.exists(src_path):
            errors.append(f"File not found: {src_path}")
            continue
            
        if item.get('is_unknown'):
            subfolder = "unknown"
        else:
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
