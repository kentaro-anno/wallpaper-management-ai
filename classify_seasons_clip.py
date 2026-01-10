import os
import sys
import logging
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
from transformers import CLIPProcessor, CLIPModel
import matplotlib.pyplot as plt
import argparse
import shutil

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("season_classifier.log", mode="w", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# === 設定 ===
DEFAULT_IMAGE_FOLDER = "./images"
DESKTOP = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")
DEFAULT_OUTPUT_FOLDER = f"{DESKTOP}/classified_images"
BASE_CSV_NAME = "clip_season_analysis.csv"  # 基本的な分析結果を保存する CSV

SEASON_LABELS = [
    "a photo of spring",
    "a photo of summer",
    "a photo of autumn",
    "a photo of winter"
]

SEASON_FOLDERS = {
    "a photo of spring": "spring",
    "a photo of summer": "summer",
    "a photo of autumn": "autumn",
    "a photo of winter": "winter",
    "unknown": "unknown"
}

# 日本語フォント対応
def setup_japanese_fonts():
    try:
        import japanize_matplotlib
        logger.info("japanize_matplotlib を使用して日本語フォントを設定しました。")
        return True
    except ImportError:
        logger.warning("japanize_matplotlib がインストールされていません。pip install japanize-matplotlib でインストールすることをお勧めします。")
        try:
            plt.rcParams['font.family'] = 'IPAGothic'
            logger.info("IPAGothic フォントを設定しました。")
            return True
        except:
            logger.warning("日本語フォントの設定に失敗しました。表示が文字化けする可能性があります。")
            return False

# === モデル読み込み（必要な場合のみ） ===
def load_model():
    logger.info("CLIP モデルを読み込んでいます...")
    start_time = time.time()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=False)
    
    elapsed_time = time.time() - start_time
    logger.info(f"デバイス: {device}, モデルを読み込みました。(所要時間: {elapsed_time:.2f}秒)")
    return model, processor, device

# === 不確実性スコア計算関数 ===
def calculate_uncertainty_scores(probs):
    """
    不確実性スコアを計算する関数
    
    Args:
        probs: 確率分布の配列
        
    Returns:
        dict: 各種不確実性スコア
    """
    # ソートした確率分布
    sorted_probs = np.sort(probs)[::-1]
    
    # 1. 最小確信度 (1 - 最大確率)
    least_confidence = 1.0 - sorted_probs[0]
    
    # 2. 確信度マージン (最大確率 - ２番目の確率)
    margin_confidence = sorted_probs[0] - sorted_probs[1]
    
    # 3. 確信度比率 (２番目の確率 / 最大確率)
    ratio_confidence = sorted_probs[1] / sorted_probs[0] if sorted_probs[0] > 0 else 1.0
    
    # 4. エントロピー
    # 0 の確率がある場合は log(0) を避けるための小さな値を追加
    epsilon = 1e-10
    entropy = -np.sum(probs * np.log(probs + epsilon))
    
    return {
        "least_confidence": least_confidence,
        "margin_confidence": margin_confidence,
        "ratio_confidence": ratio_confidence,
        "entropy": entropy
    }

# === 不確実性の判定を行う関数 ===
def is_uncertain(value, metric, threshold):
    """
    不確実性を判定する関数
    
    Args:
        value: 不確実性の値
        metric: 不確実性の指標
        threshold: 閾値
        
    Returns:
        bool: 不確実かどうか
    """
    if metric == "margin_confidence":
        # margin_confidence は小さいほど不確実
        return value < threshold
    else:
        # 他の指標は大きいほど不確実
        return value > threshold

# === 分類処理 ===
def analyze_image(image_path, model, processor, device):
    """
    画像を分析し、季節を予測する関数
    
    Args:
        image_path: 画像ファイルのパス
        model: CLIPモデル
        processor: CLIPプロセッサ
        device: 計算デバイス
        
    Returns:
        tuple: (画像, 予測ラベル, 確率, 不確実性スコア)
    """
    try:
        image = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        logger.error(f"画像ファイルが見つかりません: {image_path}")
        return None, None, None, None
    except PermissionError:
        logger.error(f"画像ファイルにアクセスできません: {image_path}")
        return None, None, None, None
    except Exception as e:
        logger.error(f"画像の読み込みに失敗しました: {image_path} ({e})")
        return None, None, None, None
    
    try:
        inputs = processor(text=SEASON_LABELS, images=image, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():  # 推論時は勾配計算不要
            outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1).detach().cpu().numpy()[0]
        top_idx = probs.argmax()
        
        # 不確実性スコアを計算
        uncertainty_scores = calculate_uncertainty_scores(probs)
        
        return image, SEASON_LABELS[top_idx], probs, uncertainty_scores
    except Exception as e:
        logger.error(f"画像の分析に失敗しました: {image_path} ({e})")
        return None, None, None, None

# === 画像に情報を追加する関数 ===
def add_text_to_image(image, label, probs, uncertainty_scores, uncertainty_metric):
    """
    画像に分析結果のテキスト情報を追加する関数
    
    Args:
        image: 元の画像
        label: 予測ラベル
        probs: 確率分布
        uncertainty_scores: 不確実性スコア
        uncertainty_metric: 使用する不確実性指標
        
    Returns:
        Image: テキスト情報が追加された画像
    """
    # 元の画像サイズを取得
    width, height = image.size
    
    # 新しい画像サイズ（下部にテキスト領域を追加）
    new_height = height + 60  # テキスト用に60ピクセル追加
    new_image = Image.new("RGB", (width, new_height), (255, 255, 255))
    new_image.paste(image, (0, 0))
    
    # 描画オブジェクト
    draw = ImageDraw.Draw(new_image)
    
    # フォントの設定（システムにインストールされているフォントを使用）
    font = get_font(16)
    
    # テキスト情報を一行にまとめて追加
    y_position = height + 10
    
    # 判定結果と季節スコア
    season_name = label.split()[-1]
    season_scores = " | ".join([f"{name.split()[-1]}: {prob:.3f}" for name, prob in zip(SEASON_LABELS, probs)])
    result_text = f"判定: {season_name} | {season_scores}"
    draw.text((10, y_position), result_text, fill=(0, 0, 0), font=font)
    y_position += 25
    
    # 不確実性スコア（使用した指標を強調表示）
    uncertainty_text = " | ".join([
        f"{metric}: {value:.3f}" + ("*" if metric == uncertainty_metric else "") 
        for metric, value in uncertainty_scores.items()
    ])
    uncertainty_text = f"不確実性: {uncertainty_text} (*=使用指標)"
    draw.text((10, y_position), uncertainty_text, fill=(0, 0, 0), font=font)
    
    return new_image

# === フォントを取得する関数 ===
def get_font(size=16):
    """
    システムにインストールされている日本語フォントを取得する関数
    
    Args:
        size: フォントサイズ
        
    Returns:
        ImageFont: フォントオブジェクト
    """
    # 日本語フォントのパスを指定（環境によって異なる）
    font_paths = [
        '/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc',  # macOS
        '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',  # Ubuntu
        'C:/Windows/Fonts/meiryo.ttc',  # Windows
        'C:/Windows/Fonts/msgothic.ttc',  # Windows
        '/usr/share/fonts/truetype/ipafont/ipagp.ttf',  # Linux
    ]
    
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    
    # フォントが見つからない場合はデフォルトフォントを使用
    return ImageFont.load_default()

# === フォルダ作成関数（画像数を含む） ===
def create_output_folders(base_output_folder, uncertainty_metric, uncertainty_threshold):
    """
    出力フォルダを作成する関数
    
    Args:
        base_output_folder: 基本出力フォルダのパス
        uncertainty_metric: 不確実性指標
        uncertainty_threshold: 閾値
        
    Returns:
        str: 作成したフォルダのパス
    """
    # 「不確実性指標_閾値」フォルダを作成
    metric_folder_name = f"{uncertainty_metric}_{uncertainty_threshold}"
    output_folder = os.path.join(base_output_folder, metric_folder_name)
    
    # 季節ごとのフォルダを作成（この時点では画像数は不明なので、後で名前を更新）
    for folder_name in SEASON_FOLDERS.values():
        folder_path = os.path.join(output_folder, folder_name)
        os.makedirs(folder_path, exist_ok=True)
    
    logger.info(f"出力フォルダを作成しました: {output_folder.replace('\\', '/')}" )
    return output_folder

# === フォルダ名を更新する関数（画像数を含める） ===
def update_folder_names(output_folder, folder_counts):
    """
    フォルダ名を更新して画像数を含める関数
    
    Args:
        output_folder: 出力フォルダのパス
        folder_counts: フォルダごとの画像数
    """
    for folder_name, count in folder_counts.items():
        old_path = os.path.join(output_folder, folder_name)
        new_folder_name = f"{folder_name} ({count})"
        new_path = os.path.join(output_folder, new_folder_name)
        
        # 既に画像数を含むフォルダが存在する場合は削除
        if os.path.exists(new_path) and old_path != new_path:
            shutil.rmtree(new_path)
        
        # フォルダ名を変更（同じ名前の場合はスキップ）
        if old_path != new_path and os.path.exists(old_path):
            os.rename(old_path, new_path)
            logger.info(f"フォルダ名を更新: {folder_name} → {new_folder_name} ({new_path.replace('\\', '/')})")

# === 画像を分析して CSV に保存する関数 ===
def analyze_images(image_folder, base_output_folder, force_recalculate=False, max_workers=4):
    """
    画像を分析して結果をCSVに保存する関数
    
    Args:
        image_folder: 入力画像フォルダのパス
        base_output_folder: 出力フォルダのパス
        force_recalculate: 強制再計算フラグ
        max_workers: 並列処理の最大ワーカー数
        
    Returns:
        DataFrame: 分析結果のデータフレーム
    """
    # 基本CSVファイルのパス
    csv_path = os.path.join(base_output_folder, BASE_CSV_NAME)
    
    # CSV ファイルが存在し、強制再計算フラグが False の場合
    if os.path.exists(csv_path) and not force_recalculate:
        logger.info(f"既存の分析結果 CSV ファイルが見つかりました: {csv_path.replace('\\', '/')}" )
        return pd.read_csv(csv_path)
    
    # モデルを読み込む
    model, processor, device = load_model()
    
    # 出力フォルダの作成（なければ）
    os.makedirs(base_output_folder, exist_ok=True)
    
    # 画像ファイルの取得
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        logger.warning(f"画像ファイルが見つかりません: {image_folder}")
        return None
    
    logger.info(f"{len(image_files)} 枚の画像を分析しています...")
    
    results = []
    
    # 画像分析関数をパーシャル適用して並列処理用に準備
    analyze_func = partial(analyze_single_image, 
                          image_folder=image_folder, 
                          model=model, 
                          processor=processor, 
                          device=device)
    
    # 並列処理で画像を分析
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in tqdm(executor.map(analyze_func, image_files), total=len(image_files)):
            if result is not None:
                results.append(result)
    
    # 結果をCSVに保存
    if results:
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)
        
        logger.info(f"\n✅ 分析完了！結果は {csv_path.replace('\\', '/')} に保存されました")
        return df
    else:
        logger.warning("分析結果がありません。")
        return None

# === 単一画像を分析する関数（並列処理用） ===
def analyze_single_image(filename, image_folder, model, processor, device):
    """
    単一の画像を分析する関数（並列処理用）
    
    Args:
        filename: 画像ファイル名
        image_folder: 入力画像フォルダのパス
        model: CLIPモデル
        processor: CLIPプロセッサ
        device: 計算デバイス
        
    Returns:
        dict: 分析結果
    """
    image_path = os.path.join(image_folder, filename)
    image, label, probs, uncertainty_scores = analyze_image(image_path, model, processor, device)
    
    if image is not None:
        # 結果を記録
        return {
            "filename": filename,
            "predicted_label": label,
            "spring": probs[0],
            "summer": probs[1],
            "autumn": probs[2],
            "winter": probs[3],
            "least_confidence": uncertainty_scores["least_confidence"],
            "margin_confidence": uncertainty_scores["margin_confidence"],
            "ratio_confidence": uncertainty_scores["ratio_confidence"],
            "entropy": uncertainty_scores["entropy"]
        }
    return None

# === CSV から画像を分類する関数 ===
def classify_images(df, image_folder, base_output_folder, uncertainty_threshold, uncertainty_metric, max_workers=4, annotate=False, annotate_size=None):
    """
    CSVから画像を分類する関数
    
    Args:
        df: 分析結果のデータフレーム
        image_folder: 入力画像フォルダのパス
        base_output_folder: 出力フォルダのパス
        uncertainty_threshold: 不確実性の閾値
        uncertainty_metric: 不確実性の指標
        max_workers: 並列処理の最大ワーカー数
        annotate: 画像にテキスト情報を追加するかどうか
        annotate_size: --annotate時の出力画像サイズ (例: 1280x720)
        
    Returns:
        tuple: (出力フォルダのパス, 分類結果のリスト)
    """
    # 出力フォルダの作成
    output_folder = create_output_folders(base_output_folder, uncertainty_metric, uncertainty_threshold)
    
    logger.info(f"{len(df)} 枚の画像を分類しています...")
    logger.info(f"不確実性指標: {uncertainty_metric}, 閾値: {uncertainty_threshold}")
    
    # 不確実性の判定
    if uncertainty_metric == "margin_confidence":
        # margin_confidence は小さいほど不確実
        df["is_uncertain"] = df[uncertainty_metric] < uncertainty_threshold
    else:
        # 他の指標は大きいほど不確実
        df["is_uncertain"] = df[uncertainty_metric] > uncertainty_threshold
    
    # 分類結果を保存するためのリスト
    classification_results = []
    
    # フォルダごとの画像数をカウントするための辞書
    folder_counts = {folder: 0 for folder in SEASON_FOLDERS.values()}
    
    # annotate時は指定サイズ or デフォルトサイズ
    pad_width, pad_height = None, None
    if annotate:
        if annotate_size:
            pad_width, pad_height = annotate_size
        else:
            pad_width, pad_height = 1920, 1080
    # annotate時は全画像の中央値サイズを取得
    """
    pad_width, pad_height = None, None
    if annotate:
        sizes = []
        for filename in df["filename"].tolist():
            image_path = os.path.join(image_folder, filename)
            if os.path.exists(image_path):
                with Image.open(image_path) as img:
                    sizes.append(img.size)
        if sizes:
            widths = [w for w, h in sizes]
            heights = [h for w, h in sizes]
            widths.sort()
            heights.sort()
            mid = len(widths) // 2
            pad_width = widths[mid]
            pad_height = heights[mid]
    """
    # 分類処理関数をパーシャル適用して並列処理用に準備
    classify_func = partial(classify_single_image, 
                           df=df, 
                           image_folder=image_folder, 
                           output_folder=output_folder, 
                           uncertainty_metric=uncertainty_metric,
                           uncertainty_threshold=uncertainty_threshold,
                           annotate=annotate,
                           pad_width=pad_width,
                           pad_height=pad_height)
    
    # 並列処理で画像を分類
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        filenames = df["filename"].tolist()
        for result in tqdm(executor.map(classify_func, filenames), total=len(filenames)):
            if result:
                classification_result, target_folder = result
                classification_results.append(classification_result)
                folder_counts[target_folder] += 1
    
    # フォルダ名を更新（画像数を含める）
    update_folder_names(output_folder, folder_counts)
    
    # 分類結果を CSV に保存
    if classification_results:
        classification_df = pd.DataFrame(classification_results)
        classification_csv_path = os.path.join(base_output_folder, f"classification_{uncertainty_metric}_{uncertainty_threshold}.csv")
        classification_df.to_csv(classification_csv_path, index=False)
        logger.info(f"分類結果を保存しました: {classification_csv_path.replace('\\', '/')}" )
    
    # 統計情報の表示
    print_statistics(df, uncertainty_metric, folder_counts, uncertainty_threshold)
    
    logger.info(f"✅ 分類完了！分類された画像は {output_folder.replace('\\', '/')} に保存されました")
    
    return output_folder, classification_results

# === unknown に分類された画像を診断する関数 ===
def diagnose_unknown(df, image_folder, uncertainty_metric, uncertainty_threshold):
    """
    unknown に分類された画像の原因を特定する関数
    
    Args:
        df: 分析結果のデータフレーム
        image_folder: 入力画像フォルダのパス
        uncertainty_metric: 不確実性の指標
        uncertainty_threshold: 不確実性の閾値
    """
    # 不確実性の判定
    if uncertainty_metric == "margin_confidence":
        df["is_uncertain"] = df[uncertainty_metric] < uncertainty_threshold
    else:
        df["is_uncertain"] = df[uncertainty_metric] > uncertainty_threshold
    
    # unknown に分類された画像
    unknown_df = df[df["is_uncertain"] == True].copy()
    
    if len(unknown_df) == 0:
        print(f"✅ unknown に分類された画像はありません（閾値: {uncertainty_threshold}）")
        return
    
    print(f"\n📊 unknown 分析（閾値: {uncertainty_threshold}、指標: {uncertainty_metric}）")
    print(f"総 {len(unknown_df)} 枚の画像が unknown に分類されています\n")
    
    # unknown 画像の情報を表示
    print(f"{'ファイル名':<50} {'判定':<10} {'確率':<8} {uncertainty_metric:<15}")
    print("-" * 90)
    
    for idx, row in unknown_df.iterrows():
        filename = row["filename"]
        prediction = row["prediction"]
        max_prob = row["max_prob"]
        metric_value = row[uncertainty_metric]
        print(f"{filename:<50} {prediction:<10} {max_prob:<8.4f} {metric_value:<15.4f}")
    
    # 異なる閾値でのシミュレーション
    print(f"\n\n🔍 閾値変更シミュレーション")
    print(f"現在の設定: {uncertainty_metric} = {uncertainty_threshold}\n")
    
    test_thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    
    print(f"{'閾値':<10} {'unknown':<15} {'判定変更画像':<20} {'説明'}")
    print("-" * 70)
    
    for test_threshold in test_thresholds:
        if uncertainty_metric == "margin_confidence":
            test_uncertain = (df[uncertainty_metric] < test_threshold).sum()
        else:
            test_uncertain = (df[uncertainty_metric] > test_threshold).sum()
        
        changed = abs(test_uncertain - len(unknown_df))
        
        if test_threshold == uncertainty_threshold:
            marker = " ← 現在"
        else:
            marker = ""
        
        print(f"{test_threshold:<10.1f} {test_uncertain:<15} {changed:<20} {marker}")
    
    # 各季節ごとの平均信頼度
    print(f"\n\n📈 季節ごとの統計")
    print(f"{'季節':<15} {'平均確率':<15} {'平均{}'.format(uncertainty_metric):<20}")
    print("-" * 50)
    
    for season_label in SEASON_LABELS:
        season_name = SEASON_FOLDERS[season_label]
        season_df = df[df["prediction"] == season_label]
        if len(season_df) > 0:
            avg_prob = season_df["max_prob"].mean()
            avg_metric = season_df[uncertainty_metric].mean()
            print(f"{season_name:<15} {avg_prob:<15.4f} {avg_metric:<20.4f}")
    
    print("\n💡 ヒント: unknown が多い場合は、閾値を上げる（不確実性を高く）ことで減らせます。")

# === unknown を最小化する最適な閾値を見つける関数 ===
def find_optimal_threshold(df, uncertainty_metric):
    """
    unknown を最小化する最適な閾値を見つける関数
    
    Args:
        df: 分析結果のデータフレーム
        uncertainty_metric: 不確実性の指標
        
    Returns:
        tuple: (最適な閾値, unknown の最小数)
    """
    test_thresholds = np.arange(0.0, 1.01, 0.05)
    best_threshold = 0.5
    min_unknown_count = len(df)
    
    print(f"\n🔍 最適閾値を探索中...（指標: {uncertainty_metric}）")
    print(f"{'閾値':<10} {'unknown数':<15} {'率':<10}")
    print("-" * 35)
    
    for threshold in test_thresholds:
        if uncertainty_metric == "margin_confidence":
            uncertain = (df[uncertainty_metric] < threshold).sum()
        else:
            uncertain = (df[uncertainty_metric] > threshold).sum()
        
        rate = (uncertain / len(df)) * 100
        
        # unknown が最も少ない閾値を記録
        if uncertain < min_unknown_count:
            min_unknown_count = uncertain
            best_threshold = threshold
        
        marker = " ← 最適" if uncertain == min_unknown_count else ""
        print(f"{threshold:<10.2f} {uncertain:<15} {rate:<10.1f}%{marker}")
    
    return best_threshold, min_unknown_count

# === 単一画像を分類する関数（並列処理用） ===
def classify_single_image(filename, df, image_folder, output_folder, uncertainty_metric, uncertainty_threshold, annotate=False, pad_width=None, pad_height=None):
    """
    単一の画像を分類する関数（並列処理用）
    
    Args:
        filename: 画像ファイル名
        df: 分析結果のデータフレーム
        image_folder: 入力画像フォルダのパス
        output_folder: 出力フォルダのパス
        uncertainty_metric: 不確実性の指標
        uncertainty_threshold: 不確実性の閾値
        annotate: 画像にテキスト情報を追加するかどうか
        pad_width: 出力画像の幅
        pad_height: 出力画像の高さ
        
    Returns:
        tuple: (分類結果, ターゲットフォルダ)
    """
    image_path = os.path.join(image_folder, filename)
    
    try:
        # ファイルが存在するか確認
        if not os.path.exists(image_path):
            logger.warning(f"警告: 画像ファイルが見つかりません: {image_path}")
            return None
        
        # データフレームから該当行を取得
        row = df[df["filename"] == filename].iloc[0]
        
        # 元の画像を読み込む
        image = Image.open(image_path).convert("RGB")
        
        # annotate時は中央値サイズにパディング
        if annotate and pad_width and pad_height:
            w, h = image.size
            new_img = Image.new("RGB", (pad_width, pad_height), (255, 255, 255))
            left = (pad_width - w) // 2
            top = (pad_height - h) // 2
            new_img.paste(image, (left, top))
            image = new_img
        
        # 不確実性が閾値を超えるかチェック
        is_uncertain_flag = row["is_uncertain"]
        
        # 保存先フォルダの決定
        if is_uncertain_flag:
            target_folder = "unknown"
        else:
            target_folder = SEASON_FOLDERS[row["predicted_label"]]
        
        # 画像に情報を追加
        probs = [row["spring"], row["summer"], row["autumn"], row["winter"]]
        uncertainty_scores = {
            "least_confidence": row["least_confidence"],
            "margin_confidence": row["margin_confidence"],
            "ratio_confidence": row["ratio_confidence"],
            "entropy": row["entropy"]
        }
        
        output_path = os.path.join(output_folder, target_folder, filename)
        if annotate:
            annotated_image = add_text_to_image(image, row["predicted_label"], probs, uncertainty_scores, uncertainty_metric)
            annotated_image.save(output_path)
        else:
            image.save(output_path)
        
        # 分類結果を記録
        classification_result = {
            "filename": filename,
            "predicted_label": row["predicted_label"],
            "classified_folder": target_folder,
            "is_uncertain": is_uncertain_flag,
            "uncertainty_value": row[uncertainty_metric],
            "uncertainty_metric": uncertainty_metric,
            "uncertainty_threshold": uncertainty_threshold
        }
        
        return classification_result, target_folder
        
    except FileNotFoundError:
        logger.error(f"エラー: 画像ファイルが見つかりません: {image_path}")
    except PermissionError:
        logger.error(f"エラー: 画像ファイルにアクセスできません: {image_path}")
    except Exception as e:
        logger.error(f"エラー: 画像 {filename} の処理中に問題が発生しました: {e}")
    
    return None

# === 統計情報を表示する関数 ===
def print_statistics(df, uncertainty_metric, folder_counts, uncertainty_threshold):
    """
    統計情報を表示する関数
    
    Args:
        df: 分析結果のデータフレーム
        uncertainty_metric: 不確実性の指標
        folder_counts: フォルダごとの画像数
        uncertainty_threshold: 不確実性の閾値
    """
    logger.info("\n=== 分類結果 ===")
    for folder_name, count in folder_counts.items():
        logger.info(f"{folder_name}: {count} 枚")
    
    # 不確実性指標の統計情報
    logger.info(f"\n=== 不確実性指標「{uncertainty_metric}」の統計 ===")
    logger.info(f"平均値: {df[uncertainty_metric].mean():.4f}")
    logger.info(f"中央値: {df[uncertainty_metric].median():.4f}")
    logger.info(f"最小値: {df[uncertainty_metric].min():.4f}")
    logger.info(f"最大値: {df[uncertainty_metric].max():.4f}")
    logger.info(f"閾値: {uncertainty_threshold:.4f}")
    
    # 季節ごとの不確実性の平均
    logger.info("\n=== 季節ごとの不確実性平均 ===")
    for season in SEASON_LABELS:
        season_name = season.split()[-1]
        season_df = df[df["predicted_label"] == season]
        if len(season_df) > 0:
            # 不確実性の判定
            if uncertainty_metric == "margin_confidence":
                uncertain_count = sum(season_df[uncertainty_metric] < uncertainty_threshold)
            else:
                uncertain_count = sum(season_df[uncertainty_metric] > uncertainty_threshold)
                
            logger.info(f"{season_name}: {season_df[uncertainty_metric].mean():.4f} (全 {len(season_df)} 枚中、不確実 {uncertain_count} 枚)")

# === メイン処理 ===
def main(image_folder, base_output_folder, uncertainty_threshold=0.5, uncertainty_metric="entropy", 
         force_recalculate=False, analyze_only=False, max_workers=4, annotate=False, annotate_size=None, diagnose_unknown_mode=False, auto_mode=False):
    """
    メイン処理関数
    
    Args:
        image_folder: 入力画像フォルダのパス
        base_output_folder: 出力フォルダのパス
        uncertainty_threshold: 不確実性の閾値
        uncertainty_metric: 不確実性の指標
        force_recalculate: 強制再計算フラグ
        analyze_only: 分析のみフラグ
        max_workers: 並列処理の最大ワーカー数
        annotate: 画像にテキスト情報を追加するかどうか
        annotate_size: --annotate時の出力画像サイズ (例: 1280x720)
        diagnose_unknown_mode: unknown診断モード
        auto_mode: 自動最適化モード
        
    Returns:
        tuple: (分析結果のデータフレーム, 出力フォルダのパス, 分類結果のリスト)
    """
    # 日本語フォントの設定
    setup_japanese_fonts()
    
    # 画像の分析（CSV がなければ実行）
    df = analyze_images(image_folder, base_output_folder, force_recalculate, max_workers)
    
    if df is None:
        logger.error("画像の分析に失敗しました。")
        return None
    
    # diagnose-unknown モードなら実行
    if diagnose_unknown_mode:
        diagnose_unknown(df, image_folder, uncertainty_metric, uncertainty_threshold)
        return df, None, None
    
    # auto モードなら最適閾値を見つけて実行
    if auto_mode:
        optimal_threshold, min_unknown = find_optimal_threshold(df, uncertainty_metric)
        logger.info(f"\n✅ 最適閾値が見つかりました: {optimal_threshold:.2f}（unknown数: {min_unknown}）")
        uncertainty_threshold = optimal_threshold
    
    # 分析のみのモードなら終了
    if analyze_only:
        logger.info("分析のみモードが指定されました。分類は行いません。")
        return df, None, None
    
    # 画像の分類
    output_folder, classification_results = classify_images(
        df, image_folder, base_output_folder, uncertainty_threshold, uncertainty_metric, max_workers, annotate, annotate_size
    )
    
    return df, output_folder, classification_results

# === CLI 引数対応 ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="季節ごとに画像を分類し、不確実な画像を特定します")
    parser.add_argument("--folder", type=str, default=DEFAULT_IMAGE_FOLDER, help="入力画像フォルダのパス")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_FOLDER, help="出力フォルダのパス")
    parser.add_argument("--uncertainty-threshold", type=float, default=0.5, help="不確実性の閾値")
    parser.add_argument("--uncertainty-metric", type=str, default="entropy", 
                        choices=["least_confidence", "margin_confidence", "ratio_confidence", "entropy"],
                        help="不確実性の指標")
    parser.add_argument("--force", action="store_true", help="既存の CSV ファイルがあっても強制的に再分析する")
    parser.add_argument("--analyze-only", action="store_true", help="分析のみを行い、分類は行わない")
    parser.add_argument("--workers", type=int, default=4, help="並列処理の最大ワーカー数")
    parser.add_argument("--debug", action="store_true", help="デバッグモードを有効にする")
    parser.add_argument("--annotate", action="store_true", help="画像に判定結果や指標テキストを追加する")
    parser.add_argument("--annotate-size", type=str, default=None, help="--annotate時の出力画像サイズ (例: 1280x720)")
    parser.add_argument("--diagnose-unknown", action="store_true", help="unknown に分類された画像の原因を診断する")
    parser.add_argument("--auto", action="store_true", help="unknown を最小化する最適な閾値を自動で見つけて分類する")
    
    args = parser.parse_args()
    
    # --auto と --diagnose-unknown は同時に使えない
    if args.auto and args.diagnose_unknown:
        logger.error("--auto と --diagnose-unknown は同時に使用できません。")
        sys.exit(1)
    
    # デバッグモードの設定
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("デバッグモードが有効になりました")
    
    try:
        # annotate-sizeのパース
        annotate_size = None
        if args.annotate_size:
            try:
                w, h = args.annotate_size.lower().split('x')
                annotate_size = (int(w), int(h))
            except Exception:
                logger.warning(f"--annotate-size の形式が不正です: {args.annotate_size}")
        main(args.folder, args.output, args.uncertainty_threshold, args.uncertainty_metric, 
             args.force, args.analyze_only, args.workers, args.annotate, annotate_size, args.diagnose_unknown, args.auto)
    except KeyboardInterrupt:
        logger.info("処理が中断されました。")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"エラーが発生しました: {e}")
        sys.exit(1)
