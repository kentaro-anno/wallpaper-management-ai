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
