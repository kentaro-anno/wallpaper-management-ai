import os
import imagehash
from PIL import Image
from typing import List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)

class DuplicateService:
    @staticmethod
    async def find_similar_images(folder: str) -> List[Dict]:
        hash_dict = {}
        duplicates = []
        
        if not os.path.exists(folder):
            raise FileNotFoundError(f"Folder not found: {folder}")
            
        filenames = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))]
        
        for filename in filenames:
            full_path = os.path.join(folder, filename)
            try:
                # PIL Image を開く
                with Image.open(full_path) as img:
                    img_hash = imagehash.phash(img)
                    if img_hash in hash_dict:
                        duplicates.append({
                            "left": hash_dict[img_hash],
                            "right": full_path,
                            "left_name": os.path.basename(hash_dict[img_hash]),
                            "right_name": os.path.basename(full_path)
                        })
                    else:
                        hash_dict[img_hash] = full_path
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                
        return duplicates

    @staticmethod
    def delete_image(path: str):
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
