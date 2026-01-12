import tkinter as tk
from tkinter import filedialog
import os

class SettingsService:
    @staticmethod
    def browse_folder(initial_dir: str = None) -> str:
        """
        Windows 標準のフォルダ選択ダイアログを表示する。
        """
        root = tk.Tk()
        root.withdraw()  # メインウィンドウを非表示にする
        root.attributes('-topmost', True)  # ダイアログを最前面に表示
        
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
            
        selected_path = filedialog.askdirectory(
            initialdir=initial_dir,
            title="壁紙フォルダを選択してください"
        )
        
        root.destroy()
        return selected_path
    @staticmethod
    def update_env_variable(key: str, value: str):
        """
        .env ファイルの特定の値を更新し、現在のプロセスにも反映させる。
        """
        # 現在のプロセスに即座に反映
        os.environ[key] = value
        
        # backend/.env を探す
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(backend_dir, ".env")
        if not os.path.exists(env_path):
            # 存在しない場合は作成
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
            return

        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        found = False
        new_lines = []
        for line in lines:
            # key= が含まれている行を探す（先頭の文字化けを考慮）
            if f"{key}=" in line:
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"{key}={value}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
