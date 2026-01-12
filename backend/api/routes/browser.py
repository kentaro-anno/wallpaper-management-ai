from fastapi import APIRouter, HTTPException, Query # type: ignore
from fastapi.responses import FileResponse # type: ignore
from pydantic import BaseModel # type: ignore
import os
from pathlib import Path
from typing import List, Optional

router = APIRouter()

DEFAULT_FOLDER = os.getenv("WALLPAPER_TARGET_FOLDER", "")

class DirectoryItem(BaseModel):
    name: str
    path: str

class ImageItem(BaseModel):
    filename: str
    path: str
    size: Optional[int] = 0
    mtime: Optional[float] = 0.0

class ImageListResponse(BaseModel):
    directories: List[DirectoryItem]
    items: List[ImageItem]
    total: int
    page: int
    limit: int

@router.get("/images", response_model=ImageListResponse)
async def list_images(
    folder: Optional[str] = None,
    page: int = Query(1, gt=0),
    limit: int = Query(50, gt=0, le=100),
    sort: str = Query("name", pattern="^(name|date|size)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    search: Optional[str] = None
):
    target_folder = folder or DEFAULT_FOLDER
    # Allow empty folder, just return empty list
    if not target_folder:
         return {"directories": [], "items": [], "total": 0, "page": page, "limit": limit}
         
    if not os.path.exists(target_folder):
        raise HTTPException(status_code=404, detail=f"Folder not found: {target_folder}")

    try:
        entries = os.scandir(target_folder)
        directories = []
        files = []
        
        for entry in entries:
            if entry.name.startswith('.'): continue # Skip hidden files
            
            if entry.is_dir():
                directories.append({
                    "name": entry.name,
                    "path": str(Path(entry.path).absolute().as_posix())
                })
            elif entry.is_file() and entry.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                if search and search.lower() not in entry.name.lower():
                    continue
                    
                stat = entry.stat()
                files.append({
                    "filename": entry.name,
                    "path": str(Path(entry.path).absolute().as_posix()),
                    "size": stat.st_size,
                    "mtime": stat.st_mtime
                })
        
        # Sort Directories (Always by name asc)
        directories.sort(key=lambda x: x['name'].lower())

        # Sort Files
        reverse = (order == "desc")
        if sort == "date":
            files.sort(key=lambda x: x['mtime'], reverse=reverse)
        elif sort == "size":
            files.sort(key=lambda x: x['size'], reverse=reverse)
        else: # name
            files.sort(key=lambda x: x['filename'].lower(), reverse=reverse)
        
        total = len(files)
        start = (page - 1) * limit
        end = start + limit
        
        paginated_files = files[start:end]
            
        return {
            "directories": directories,
            "items": paginated_files,
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/image")
async def get_image(path: str):
    """
    Serve image file.
    """
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
