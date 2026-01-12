import os
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from typing import List, Dict, Optional
import logging
import gc
import threading

logger = logging.getLogger(__name__)

SEASON_LABELS = [
    "a photo of spring",
    "a photo of summer",
    "a photo of autumn",
    "a photo of winter"
]

class ClassifyService:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.lock = threading.Lock()
        print(f"ClassifyService initialized with device: {self.device}")

    def load_model(self):
        with self.lock:
            if self.model is None:
                try:
                    print(f"Loading CLIP model into {self.device}...")
                    self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
                    self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=False)
                    print("Model loaded successfully.")
                except Exception as e:
                    print(f"FAILED to load model: {e}")
                    raise e

    def calculate_uncertainty(self, probs):
        sorted_probs = np.sort(probs)[::-1]
        epsilon = 1e-10
        entropy = -np.sum(probs * np.log(probs + epsilon))
        return {
            "least_confidence": float(1.0 - sorted_probs[0]),
            "margin_confidence": float(sorted_probs[0] - sorted_probs[1]),
            "entropy": float(entropy)
        }

    def analyze_image_sync(self, image_path: str) -> Optional[Dict]:
        """同期的な解析処理。非同期ループ内での競合を避ける"""
        try:
            self.load_model()
            
            with Image.open(image_path) as raw_img:
                image = raw_img.convert("RGB")
                inputs = self.processor(text=SEASON_LABELS, images=image, return_tensors="pt", padding=True).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                probs = outputs.logits_per_image.softmax(dim=1).detach().cpu().numpy()[0]
                top_idx = probs.argmax()
                uncertainty = self.calculate_uncertainty(probs)
                
                result = {
                    "filename": os.path.basename(image_path),
                    "path": image_path,
                    "prediction": SEASON_LABELS[top_idx],
                    "probs": {label.split()[-1]: float(p) for label, p in zip(SEASON_LABELS, probs)},
                    "uncertainty": uncertainty
                }
                
                # 強力なメモリ解放
                del inputs, outputs, image
                gc.collect()
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                
                return result
                
        except Exception as e:
            print(f"Error analyzing image {image_path}: {e}")
            gc.collect()
            return None
