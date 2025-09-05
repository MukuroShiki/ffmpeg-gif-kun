# FFmpeg GUI Kun - 動画エンコード・GIF変換ツール

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/downloads/)

## 概要

FFmpeg GUI Kunは、FFmpegを使用した動画エンコードとGIF変換を簡単に行えるGUIアプリケーションです。
直感的なタブ式インターフェースで、複雑なFFmpegコマンドを知らなくても高品質な動画変換が可能です。

![Screenshot](https://via.placeholder.com/600x400?text=Screenshot+Placeholder)

## 🎯 特徴

- **簡単操作**: ドラッグ&ドロップでファイル選択
- **FFmpeg不要**: 自動ダウンロード機能付き（初回起動時）
- **日本語対応**: 完全日本語インターフェース
- **リアルタイム**: 進行状況をリアルタイム表示

## 📋 主な機能

### 動画エンコード
- 様々な出力フォーマット対応 (MP4, AVI, MOV, MKV, WebM等)
- 豊富なコーデック選択 (H.264, H.265, VP8, VP9等)
- 解像度・FPS・品質の自由な設定
- CRF/ビットレート両方の品質設定対応
- エンコードプリセットによる速度・品質調整
- カスタムプリセット保存機能

### GIF変換
- 動画からGIFアニメーション作成
- 解像度・FPS調整可能
- 品質レベル選択 (低・標準・高)
- 時間範囲指定対応
- プレビュー機能付き

## 🚀 インストールと使用方法

### 必要要件
- Python 3.7 以上
- Windows 10以上推奨（macOS、Linuxでも動作）
- メモリ: 2GB以上推奨
- ディスク容量: 200MB以上（FFmpeg含む）

### インストール方法

#### 方法1: ソースコードから実行（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/your-username/ffmpeg-gui-kun.git
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
2. 「動画エンコード」または「GIF変換」タブを選択
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

## 🤝 貢献方法

このプロジェクトへの貢献を歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### 開発者向け情報

詳細な開発情報については [DEVELOPMENT.md](DEVELOPMENT.md) を参照してください。

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
