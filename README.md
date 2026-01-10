# Wallpaper Management AI Tool

AI を活用した壁紙（画像）管理ツールです。重複画像の検出・削除や、CLIP モデルを使用した季節ごとの自動分類機能を提供します。

## ✨ 主な機能

- **ダッシュボード**: ライブラリ全体の統計情報を可視化。
- **重複削除**: 類似度の高い画像を検出し、プレビューを確認しながら片方を削除。
- **季節分類 (AI)**:
  - CLIP モデルによる「春・夏・秋・冬」の自動判定。
  - 3つの判定ロジック（確信度・競合度・迷い度）から選択可能。
  - 不確実な画像 (Unknown) の手動振り分け UI。
  - 判定結果に基づいたフォルダ一括整理（移動またはコピー）。
- **出力先指定**: 整理した画像の出力先を任意に設定可能。

## 🚀 クイックスタート

### 準備
- Python 3.10以上
- Node.js (npm)

### セットアップ
```powershell
# バックエンドの依存関係インストール
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt

# フロントエンドの依存関係インストール
cd frontend
npm install
cd ..
```

### 実行
ルートディレクトリにあるバッチファイルを実行してください。
```powershell
.\start_app.bat
```
※ 自動的にブラウザが開き、 `http://localhost:5173` で UI が表示されます。

### 停止
ターミナルで `Ctrl + C` を押すか、 `stop_app.bat` を実行してください。

## 🛠 技術構成

- **Frontend**: React (TypeScript), Vite, Tailwind CSS, Framer Motion
- **Backend**: FastAPI (Python), Uvicorn
- **AI Model**: OpenAI CLIP (transformers)
- **Icons**: Lucide React
