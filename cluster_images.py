import os
import numpy as np
from sklearn.cluster import KMeans
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model
from PIL import Image
import matplotlib.pyplot as plt

# === パラメータ ===
IMAGE_FOLDER = "./風景"
NUM_CLUSTERS = 5
IMAGE_SIZE = (224, 224)

# === 特徴抽出器（ResNet50） ===
base_model = ResNet50(weights="imagenet", include_top=False, pooling='avg')
model = Model(inputs=base_model.input, outputs=base_model.output)

# === 画像の読み込みと前処理 ===
def load_and_preprocess(img_path):
    img = image.load_img(img_path, target_size=IMAGE_SIZE)
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    return x

# === 特徴ベクトル抽出 ===
def extract_features(img_paths):
    features = []
    for path in img_paths:
        x = load_and_preprocess(path)
        feature = model.predict(x, verbose=0)
        features.append(feature.flatten())
    return np.array(features)

# === メイン処理 ===
def main():
    img_files = [os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER)
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not img_files:
        print("No images found.")
        return
    
    print(f"{len(img_files)} images found. Extracting features...")
    
    features = extract_features(img_files)
    
    print("Clustering...")
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42)
    labels = kmeans.fit_predict(features)
    
    print("\nCluster assignments:")
    for path, label in zip(img_files, labels):
        print(f"{os.path.basename(path)} --> Cluster {label}")
    
    # Optional: クラスタごとの画像を並べて表示
    show_clusters(img_files, labels)

# === クラスタごとに画像を表示 ===
def show_clusters(img_paths, labels):
    cluster_dict = {}
    for path, label in zip(img_paths, labels):
        cluster_dict.setdefault(label, []).append(path)
    
    for cluster_id, paths in cluster_dict.items():
        print(f"\nCluster {cluster_id} ({len(paths)} images):")
        plt.figure(figsize=(12, 3))
        for i, path in enumerate(paths[:10]):
            img = Image.open(path).convert("RGB")
            plt.subplot(1, min(len(paths), 10), i + 1)
            plt.imshow(img)
            plt.axis("off")
        plt.suptitle(f"Cluster {cluster_id}")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
