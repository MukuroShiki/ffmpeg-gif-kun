# FFmpeg GUI Kun

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/MukuroShiki/ffmpeg-gui-kun)

> 🎬 **簡単操作で高品質な動画変換・GIF作成**  
> FFmpegの複雑なコマンドを覚える必要なし！直感的なGUIで誰でも使える動画変換ツール

![Screenshot](https://via.placeholder.com/800x500?text=FFmpeg+GUI+Kun+Screenshot)

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
1. [Releases](https://github.com/MukuroShiki/ffmpeg-gui-kun/releases)から最新の`ffmpeg-gui-kun-windows.zip`をダウンロード
2. 解凍して`FFmpeg-GUI-Kun.exe`を実行

**macOS:**
1. [Releases](https://github.com/MukuroShiki/ffmpeg-gui-kun/releases)から最新の`ffmpeg-gui-kun-macos.zip`をダウンロード
2. 解凍して`FFmpeg-GUI-Kun.app`を実行

**Linux:**
1. [Releases](https://github.com/MukuroShiki/ffmpeg-gui-kun/releases)から最新の`ffmpeg-gui-kun-linux.tar.gz`をダウンロード
2. 解凍して`./FFmpeg-GUI-Kun`を実行

### 🐍 ソースコード版

**必要要件:**
- Python 3.7以上
- 2GB以上のメモリ（推奨）

**インストール:**
```bash
# リポジトリをクローン
git clone https://github.com/MukuroShiki/ffmpeg-gui-kun.git
cd ffmpeg-gui-kun

# 依存関係をインストール
pip install -r requirements.txt

# 実行
python src/ffmpeg_gui_kun.py
```

## 🔧 ビルド方法

**各プラットフォームでのビルド:**

```bash
# 依存関係インストール
pip install -r requirements.txt
pip install -r build_requirements.txt

# ビルド実行
python build.py
```

**プラットフォーム固有の準備:**

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

### 動画エンコード
1. **「動画エンコード」**タブを選択
2. 入力動画ファイルを選択（参照ボタンまたはドラッグ&ドロップ）
3. 出力フォーマット・コーデック・品質を設定
4. **「エンコード開始」**をクリック

### GIF変換
1. **「GIF変換」**タブを選択
2. 入力動画ファイルを選択
3. 解像度・FPS・時間範囲を設定
4. **「GIF変換開始」**をクリック

## 📝 ライセンス

[MIT License](LICENSE) - 自由に使用・改変・配布していただけます。

## 🐛 バグ報告・機能要望

[Issues](https://github.com/MukuroShiki/ffmpeg-gui-kun/issues)からお気軽にご報告ください。

---

cd ffmpeg-gui-kun

# 依存関係をインストール（基本的に標準ライブラリのみ）
pip install -r requirements.txt

# アプリケーションを起動
python src/ffmpeg_gui_kun.py
```

#### 方法2: PyInstallerでビルド

```bash
# ビルド用依存関係をインストール
pip install -r build_requirements.txt

# 実行可能ファイルをビルド
python build.py

# 生成されたファイルを実行（Windows）
./dist/FFmpeg-GUI-Kun.exe

# 生成されたファイルを実行（macOS/Linux）
./dist/FFmpeg-GUI-Kun
```

### 簡単起動スクリプト

Windows:
```batch
start_ffmpeg_gui_kun.bat
```

macOS/Linux:
```bash
./start_ffmpeg_gui_kun.sh
```

## 🎮 使い方

1. アプリケーションを起動
3. 入力ファイルをドラッグ&ドロップで選択
4. 出力設定を調整
5. 「開始」ボタンで変換実行
6. 進行状況を確認し、完了を待つ

## 🏗️ プロジェクト構造

```
ffmpeg-gui-kun/
├── src/                          # ソースコード
│   ├── ffmpeg_gui_kun.py        # メインエントリーポイント
│   ├── gui/                     # GUIコンポーネント
│   │   ├── main_window.py       # メインウィンドウ
│   │   ├── video_encode_tab.py  # 動画エンコードタブ
│   │   └── gif_convert_tab.py   # GIF変換タブ
│   ├── core/                    # コア機能
│   │   └── ffmpeg_manager.py    # FFmpeg管理
│   └── utils/                   # ユーティリティ
│       ├── settings.py          # 設定管理
│       ├── drag_drop.py         # ドラッグ&ドロップ
│       └── ffmpeg_downloader.py # FFmpeg自動ダウンロード
├── build.py                     # ビルドスクリプト
├── requirements.txt             # 実行時依存関係
└── README.md                    # このファイル
```

## 📝 ライセンス

このプロジェクトのライセンスは現在検討中です。配布前に適切なオープンソースライセンスを選択する予定です。

## 🐛 バグ報告・機能要望

バグ報告や機能要望は[Issues](https://github.com/your-username/ffmpeg-gui-kun/issues)までお願いします。

## 📧 お問い合わせ

- 作者: 屍鬼 骸 | Mukuro Shiki
- プロジェクト: [https://github.com/your-username/ffmpeg-gui-kun](https://github.com/your-username/ffmpeg-gui-kun)

## 🙏 謝辞

- [FFmpeg](https://ffmpeg.org/) - 強力な動画処理ライブラリ
- [Python](https://www.python.org/) - 素晴らしいプログラミング言語
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - クロスプラットフォームGUIライブラリ
