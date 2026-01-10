import os
import argparse
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import imagehash
from tqdm import tqdm

# ====== 類似画像の検出 ======
def find_similar_images(folder):
    hash_dict = {}
    duplicates = []
    
    filenames = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))]
    
    for filename in tqdm(filenames, desc="画像処理中"):
        full_path = os.path.join(folder, filename)
        try:
            img = Image.open(full_path)
            img_hash = imagehash.phash(img)
            if img_hash in hash_dict:
                duplicates.append((hash_dict[img_hash], full_path))
            else:
                hash_dict[img_hash] = full_path
        except Exception as e:
            tqdm.write(f"Failed to process {filename}: {e}")
    return duplicates

# ====== UI の表示クラス ======
class DuplicateViewer:
    def __init__(self, root, duplicates):
        self.root = root
        self.duplicates = duplicates
        self.index = 0
        self.img1 = None
        self.img2 = None
        
        # 画像フレーム
        img_frame = tk.Frame(root)
        img_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.label1 = tk.Label(img_frame)
        self.label2 = tk.Label(img_frame)
        self.label1.pack(side="left", padx=10)
        self.label2.pack(side="right", padx=10)
        
        # ボタンフレーム
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn1 = tk.Button(btn_frame, text="左を削除", command=self.delete_left)
        self.btn2 = tk.Button(btn_frame, text="右を削除", command=self.delete_right)
        self.btn1.pack(side="left", padx=5)
        self.btn2.pack(side="right", padx=5)
        
        self.show_pair()
    
    def resize_image(self, path, maxsize=(400, 400)):
        img = Image.open(path)
        img.thumbnail(maxsize)
        return ImageTk.PhotoImage(img)
    
    def show_pair(self):
        if self.index >= len(self.duplicates):
            messagebox.showinfo("完了", "すべての重複を処理しました")
            self.root.quit()
            return
        
        left, right = self.duplicates[self.index]
        self.left_path, self.right_path = left, right
        
        try:
            self.img1 = self.resize_image(left)
            self.img2 = self.resize_image(right)
            self.label1.config(image=self.img1)
            self.label2.config(image=self.img2)
            self.root.title(f"{os.path.basename(left)} vs {os.path.basename(right)}")
        except Exception as e:
            messagebox.showerror("エラー", f"画像を開けません: {e}")
            self.index += 1
            self.show_pair()
    
    def delete_left(self):
        os.remove(self.left_path)
        print(f"削除: {self.left_path}")
        self.index += 1
        self.show_pair()
    
    def delete_right(self):
        os.remove(self.right_path)
        print(f"削除: {self.right_path}")
        self.index += 1
        self.show_pair()

# ====== メイン処理 ======
def main():
    print("スクリプト開始")
    parser = argparse.ArgumentParser(description="重複画像を見つけて手動で削除")
    parser.add_argument("folder", help="画像が入っているフォルダのパス")
    args = parser.parse_args()
    
    folder_path = args.folder
    print(f"フォルダパス: {folder_path}")
    
    if not os.path.isdir(folder_path):
        print(f"Error: フォルダが見つかりません → {folder_path}")
        return
    
    print("重複画像を検出中...")
    duplicates = find_similar_images(folder_path)
    print(f"見つかった重複数: {len(duplicates)}")
    
    if not duplicates:
        print("重複画像は見つかりませんでした。")
    else:
        print("UI を起動中...")
        root = tk.Tk()
        app = DuplicateViewer(root, duplicates)
        print("ウィンドウが表示されます。")
        root.mainloop()

if __name__ == "__main__":
    main()
