# classify_seasons_clip.py 使い方ガイド

CLIP モデルを使用して画像を季節（春・夏・秋・冬）で自動分類するスクリプト

## 基本的な使い方

### 最もシンプルな実行
```bash
python .\classify_seasons_clip.py --folder .\風景\
```
指定フォルダの画像を分析・分類して、季節ごとのフォルダに振り分けます。

## 主なオプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `--folder` | 入力画像フォルダ（必須） | `--folder .\風景\` |
| `--output` | 出力フォルダ | `--output C:\path\to\output` |
| `--analyze-only` | 分析のみ実行（分類はしない） | `--analyze-only` |
| `--force` | 既存の CSV があっても再分析 | `--force` |
| `--workers` | 並列処理の数（デフォルト：4） | `--workers 8` |
| `--uncertainty-threshold` | 不確実性の閾値（デフォルト：0.5） | `--uncertainty-threshold 0.3` |
| `--uncertainty-metric` | 不確実性の指標 | `--uncertainty-metric margin_confidence` |
| `--annotate` | 分類結果を画像に追記 | `--annotate` |
| `--annotate-size` | アノテーション時の出力サイズ | `--annotate-size 1280x720` |
| `--diagnose-unknown` | unknown 分類の原因を診断 | `--diagnose-unknown` |
| `--auto` | unknown を最小化する最適閾値を自動探索 | `--auto` |
| `--debug` | デバッグモード | `--debug` |

## 不確実性の指標について

分類が不確かな画像を検出するために使用する指標：

- **`entropy`** (デフォルト)：エントロピー。大きいほど不確実
- **`margin_confidence`**：最大確率と2番目の確率の差。小さいほど不確実
- **`least_confidence`**：1 - 最大確率。大きいほど不確実
- **`ratio_confidence`**：2番目の確率 / 最大確率。大きいほど不確実

## 使用例

### 1. 基本的な分類
```bash
python .\classify_seasons_clip.py --folder .\風景\
```

### 2. 不確実な画像を厳しく判定（閾値を下げる）
```bash
python .\classify_seasons_clip.py --folder .\風景\ --uncertainty-threshold 0.3
```

### 3. 分析結果だけ見たい（フォルダ移動なし）
```bash
python .\classify_seasons_clip.py --folder .\風景\ --analyze-only
```

### 4. 以前の分析結果を無視して再実行
```bash
python .\classify_seasons_clip.py --folder .\風景\ --force
```

### 5. 分類結果を画像に追記して出力
```bash
python .\classify_seasons_clip.py --folder .\風景\ --annotate --annotate-size 1280x720
```

### 6. 並列処理を増やして高速化
```bash
python .\classify_seasons_clip.py --folder .\風景\ --workers 16
```

### 7. unknown を最小化する最適閾値を自動探索して分類（推奨）
```bash
python .\classify_seasons_clip.py --folder .\風景\ --auto
```
未確実な画像（unknown）の数を最小化する最適な閾値を自動で見つけて分類します。

### 8. unknown に分類された画像の原因を診断
```bash
python .\classify_seasons_clip.py --folder .\風景\ --diagnose-unknown
```
以下の情報を表示します：
- unknown に分類された全画像一覧
- 異なる閾値でのシミュレーション結果
- 各季節の平均確率と不確実性スコア

### 9. 特定の不確実性指標を使用して自動最適化
```bash
python .\classify_seasons_clip.py --folder .\風景\ --auto --uncertainty-metric margin_confidence
```

## 出力結果

実行後、以下が生成されます：

- **`clip_season_analysis.csv`**：分析結果（確率、不確実性スコアなど）
- **分類フォルダ**：
  - `spring/` - 春と判定された画像
  - `summer/` - 夏と判定された画像
  - `autumn/` - 秋と判定された画像
  - `winter/` - 冬と判定された画像
  - `unknown/` - 判定不可の画像
- **`season_classifier.log`**：実行ログ

## トラブルシューティング

### メモリ不足の場合
`--workers` の値を減らしてください：
```bash
python .\classify_seasons_clip.py --folder .\風景\ --workers 2
```

### GPU がない場合
自動的に CPU で実行されます（遅くなります）

### 日本語フォントが文字化けする場合
以下をインストール：
```bash
pip install japanize-matplotlib
```

## 自動最適化モード（--auto）について

`--auto` フラグを使用すると、以下のプロセスが自動実行されます：

1. **閾値探索** - 0.0～1.0 の範囲で複数の閾値を試す
2. **結果分析** - 各閾値で unknown の数を計算
3. **最適値選択** - unknown が最も少ない閾値を選択
4. **分類実行** - その閾値で画像を分類

これにより、手動で閾値を調整する手間が省けます。

### 例
```bash
# エントロピーで最適化（デフォルト）
python .\classify_seasons_clip.py --folder .\風景\ --auto

# margin_confidence で最適化
python .\classify_seasons_clip.py --folder .\風景\ --auto --uncertainty-metric margin_confidence
```

## 診断モード（--diagnose-unknown）について

unknown に分類された画像が多い場合、`--diagnose-unknown` で原因を分析できます。

出力内容：
- ✅ unknown に分類されたすべての画像一覧
- 📊 異なる閾値（0.1～0.8）での影響予測
- 📈 各季節の統計情報（平均確率、平均スコア）
- 💡 改善のためのヒント

### 例
```bash
# エントロピーの詳細分析
python .\classify_seasons_clip.py --folder .\風景\ --diagnose-unknown

# margin_confidence で詳細分析
python .\classify_seasons_clip.py --folder .\風景\ --diagnose-unknown --uncertainty-metric margin_confidence
```
