import os
import imagehash
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Dict
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

logger = logging.getLogger(__name__)

class DuplicateService:
    @staticmethod
    async def find_similar_images(folder: str, max_workers: int = 4) -> List[Dict]:
        hash_dict = {}
        duplicates = []
        
        if not os.path.exists(folder):
            raise FileNotFoundError(f"Folder not found: {folder}")
            
        filenames = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))]
        
        def process_image(filename):
            try:
                full_path = Path(os.path.join(folder, filename)).absolute().as_posix()
                with Image.open(full_path) as img:
                    img_hash = imagehash.phash(img)
                    return (img_hash, full_path)
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(process_image, filenames))

        for result in results:
            if result:
                img_hash, full_path = result
                if img_hash in hash_dict:
                    duplicates.append({
                        "left": hash_dict[img_hash],
                        "right": full_path,
                        "left_name": os.path.basename(hash_dict[img_hash]),
                        "right_name": os.path.basename(full_path)
                    })
                else:
                    hash_dict[img_hash] = full_path
                
        return duplicates

    @staticmethod
    def delete_image(path: str):
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
