import os
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm
import pandas as pd
import matplotlib.pyplot as plt
import argparse

# === 設定 ===
DEFAULT_IMAGE_FOLDER = "./images"
OUTPUT_CSV = "clip_season_results.csv"

SEASON_LABELS = [
    "a photo of spring",
    "a photo of summer",
    "a photo of autumn",
    "a photo of winter"
]

# === モデル読み込み ===
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# === 分類処理 ===
def classify_image(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Failed to load image: {image_path} ({e})")
        return None, None, None
    
    inputs = processor(text=SEASON_LABELS, images=image, return_tensors="pt", padding=True).to(device)
    outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1).detach().cpu().numpy()[0]
    top_idx = probs.argmax()
    return image, SEASON_LABELS[top_idx], probs

# === 表示処理 ===
def show_image(image, label, probs):
    plt.imshow(image)
    plt.axis("off")
    title = f"{label}\n" + " / ".join([f"{name.split()[-1]}: {p:.2f}" for name, p in zip(SEASON_LABELS, probs)])
    plt.title(title)
    plt.tight_layout()
    plt.show()

# === メイン処理 ===
def main(image_folder, preview=False):
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    results = []
    
    print(f"Classifying {len(image_files)} images...")
    
    for filename in tqdm(image_files):
        image_path = os.path.join(image_folder, filename)
        image, label, probs = classify_image(image_path)
        if image is not None:
            results.append({
                "filename": filename,
                "predicted_label": label,
                "spring": probs[0],
                "summer": probs[1],
                "autumn": probs[2],
                "winter": probs[3],
            })
            if preview:
                show_image(image, label, probs)
    
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Done! Results saved to: {OUTPUT_CSV}")

# === CLI 引数対応 ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify images into seasons using CLIP")
    parser.add_argument("--folder", type=str, default=DEFAULT_IMAGE_FOLDER, help="Image folder path")
    parser.add_argument("--preview", action="store_true", help="Show image and prediction")
    args = parser.parse_args()
    main(args.folder, args.preview)
