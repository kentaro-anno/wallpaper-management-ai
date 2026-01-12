from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from ...services.duplicate_service import DuplicateService

router = APIRouter()
duplicate_service = DuplicateService()

DEFAULT_FOLDER = os.getenv("WALLPAPER_TARGET_FOLDER", "")

class ScanRequest(BaseModel):
    folder: str = DEFAULT_FOLDER
    workers: int = 4

class DeleteRequest(BaseModel):
    path: str

@router.post("/scan")
async def scan_duplicates(request: ScanRequest):
    try:
        duplicates = await duplicate_service.find_similar_images(request.folder, request.workers)
        return {"duplicates": duplicates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete")
async def delete_duplicate(request: DeleteRequest):
    if duplicate_service.delete_image(request.path):
        return {"message": "Deleted successfully"}
    raise HTTPException(status_code=404, detail="File not found")
