# FFmpeg GIF Kun - 動画をGIF画像に変換するGUIアプリケーション

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/MukuroShiki/ffmpeg-gui-kun)
![License](https://img.shields.io/github/license/MukuroShiki/ffmpeg-gif-kun)

> 🎬 **簡単操作で高品質な動画変換・GIF作成**  
> FFmpegの複雑なコマンドを覚える必要なし。直感的なGUIで誰でも使える動画変換ツール

<div align="center"><img src="https://github.com/MukuroShiki/ffmpeg-gif-kun/blob/c91fdd30d38c13b30a3b0cc8bed693aef3b859d2/.brand/readme_top.png" alt="READMEトップ画像" width="500" /></div>
## � 特徴

- **🖱️ 簡単操作**: ドラッグ&ドロップでファイル選択
- **⚡ すぐ使える**: FFmpeg自動ダウンロード（初回のみ）
- **🌍 日本語完全対応**: わかりやすい日本語インターフェース
- **📊 リアルタイム表示**: 変換の進行状況をリアルタイムで確認
- **💾 設定保存**: よく使う設定をプリセットとして保存

## 📋 主な機能

### 🎨 GIF変換
- **高品質変換**: 2段階パレット生成による最適化
- **詳細設定**: 解像度・FPS・時間範囲を指定
- **ハードウェア加速**: NVIDIA CUDA、Intel QSV等に対応
- **品質選択**: 低・標準・高品質から選択

## 🚀 インストール・使用方法

### 📦 実行ファイル版（推奨）

**Windows:**
1. [Releases](https://github.com/MukuroShiki/ffmpeg-gui-kun/releases)から最新の`ffmpeg-gif-kun-windows.zip`をダウンロード
2. 解凍して`FFmpeg-GIF-Kun.exe`を実行

**macOS:**
1. 開発者がmacOSを有していないため、現在ビルド版はありません。

**Linux:**
1. [Releases](https://github.com/MukuroShiki/ffmpeg-gui-kun/releases)から最新の`ffmpeg-gif-kun-linux.tar.gz`をダウンロード
2. 解凍して`./FFmpeg-GIF-Kun`を実行

**必要要件:**
- Python 3.7以上
- 2GB以上のメモリ（推奨）
- FFmpegが満足に動く程度の環境

## 🔧 ビルド方法

Linux環境では、Pythonの仮想環境.venvの使用を推奨します。

<details>
<summary>🐧 <strong>Linux (Ubuntu/Debian)</strong></summary>

```bash
# システム依存関係
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-tk
sudo apt install -y build-essential pkg-config libffi-dev

# ビルド
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r build_requirements.txt
python build.py
```
</details>

<details>
<summary>🍎 <strong>macOS</strong></summary>

```bash
# Homebrewでの依存関係インストール
brew install python3 python-tk

# ビルド
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r build_requirements.txt
python build.py
```
</details>

<details>
<summary>🪟 <strong>Windows</strong></summary>

```powershell
# 仮想環境作成
python -m venv venv
venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
pip install -r build_requirements.txt

# ビルド
python build.py
```
</details>

## 📖 使い方

### GIF変換
1. 「**GIF変換**」タブを選択
2. 入力動画ファイルを選択
3. 解像度・FPS・時間範囲を設定
4. 「**GIF変換開始**」をクリック

## 🏗️ プロジェクト構造

```
ffmpeg-gif-kun/
├── src/                         # ソースコード
│   ├── ffmpeg_gif_kun.py        # メインエントリーポイント
│   ├── gui/                     # GUIコンポーネント
│   │   ├── main_window.py       # メインウィンドウ
│   │   └── gif_convert_tab.py   # GIF変換タブ
│   ├── core/                    # コア機能
│   │   └── ffmpeg_manager.py    # FFmpeg管理
│   └── utils/                   # ユーティリティ
│       ├── settings.py          # 設定管理
│       └── ffmpeg_downloader.py # FFmpeg自動ダウンロード
├── build.py                     # ビルドスクリプト
├── requirements.txt             # 実行時依存関係
├── build_requirements.txt       # 実行時依存関係
└── README.md                    # このファイル
```

## 📝 ライセンス

このプロジェクトは **BSD 2-Clause ライセンス** に基づいて提供されています。

## 🐛 バグ報告・機能要望

バグ報告や機能要望は[Issues](https://github.com/MukuroShiki/ffmpeg-gif-kun/issues)までお願いします。

## 📧 お問い合わせ

- 作者: 屍鬼 骸 | Mukuro Shiki
- プロジェクト: [https://github.com/MukuroShiki/ffmpeg-gif-kun](https://github.com/MukuroShiki/ffmpeg-gif-kun)

## 🙏 謝辞

- [FFmpeg](https://ffmpeg.org/) - 強力な動画処理ライブラリ
- [Python](https://www.python.org/) - お馴染みの万能インタプリタ言語
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - クロスプラットフォームGUIライブラリ
