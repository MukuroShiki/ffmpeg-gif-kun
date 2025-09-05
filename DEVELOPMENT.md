# FFmpeg GUI Kun - ビルドとデプロイメントガイド

## 概要

FFmpeg GUI KunはPythonで開発された、FFmpegを使用した動画エンコーディング・GIF変換ツールです。  
このドキュメントでは、開発者向けのビルド手順と配布方法について説明します。

## プロジェクト構造

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
├── asset/                       # アセットファイル
├── build.py                     # ビルドスクリプト
├── build_requirements.txt       # ビルド用依存関係
├── requirements.txt             # 実行時依存関係
└── README.txt                   # ユーザー向け説明書
```

## 開発環境のセットアップ

### 1. Pythonの要件
- Python 3.7 以上が必要
- Windows, macOS, Linux に対応

### 2. 開発用依存関係のインストール
```bash
# 基本的な実行環境
pip install -r requirements.txt

# ビルド環境（PyInstaller含む）
pip install -r build_requirements.txt
```

### 3. 開発実行
```bash
# ソースコードから直接実行
python src/ffmpeg_gui_kun.py

# または Pythonパッケージとして実行
cd src
python -m ffmpeg_gui_kun
```

## ビルド手順

### 1. 自動ビルド（推奨）
```bash
# 完全ビルド（クリーンアップ含む）
python build.py

# クリーンアップなしでビルド
python build.py --no-clean

# ビルド成果物のクリーンアップのみ
python build.py --clean-only
```

### 2. 手動ビルド
```bash
# PyInstallerを直接使用
pyinstaller --onefile --windowed --name "FFmpeg-GUI-Kun" src/ffmpeg_gui_kun.py
```

### 3. ビルド成果物
ビルド後、以下のファイル・ディレクトリが作成されます：

```
dist/
├── FFmpeg-GUI-Kun.exe           # 実行ファイル（Windows）
├── FFmpeg-GUI-Kun               # 実行ファイル（Linux/macOS）
├── FFmpeg-GUI-Kun-windows/      # 配布パッケージ（Windows）
│   ├── FFmpeg-GUI-Kun.exe
│   ├── start.bat
│   ├── README.txt
│   └── asset/
└── FFmpeg-GUI-Kun-windows.zip   # 圧縮配布パッケージ
```

## 機能仕様

### コア機能
1. **動画エンコーディング**
   - プリセット形式：Web最適化、高品質、アーカイブ、カスタム
   - 対応形式：MP4, AVI, MOV, WebM
   - リアルタイム進行状況表示

2. **GIF変換**
   - 動画からGIFへの変換
   - フレームレート・品質調整
   - プレビュー機能

3. **ユーザビリティ**
   - ドラッグ&ドロップ対応
   - 設定の保存・読み込み
   - 多言語対応（日本語）

### 技術仕様
- **GUI フレームワーク**: tkinter（Python標準ライブラリ）
- **FFmpeg 統合**: subprocess経由での呼び出し
- **設定管理**: JSON形式でのローカル保存
- **エラーハンドリング**: 包括的な例外処理とユーザーフィードバック

## 配布方法

### 1. スタンドアロン実行ファイル
- PyInstallerでビルドした実行ファイル
- Python環境不要
- FFmpeg自動ダウンロード機能付き

### 2. Pythonパッケージ
```bash
# 直接実行
python src/ffmpeg_gui_kun.py

# 必要に応じてFFmpegを個別インストール
```

### 3. ソースコード配布
- GitHubリポジトリでのソースコード公開
- 開発者向けドキュメント付き

## トラブルシューティング

### よくある問題

#### 1. PyInstallerビルドエラー
```bash
# 仮想環境を使用することを推奨
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

pip install -r build_requirements.txt
python build.py
```

#### 2. tkinterdnd2の問題
- アプリケーションには代替ドラッグ&ドロップ機能が実装済み
- tkinterdnd2が利用不可の場合は自動的にフォールバック

#### 3. FFmpegが見つからない
- アプリケーション初回起動時に自動ダウンロード
- 手動インストールも可能（PATH設定必要）

### デバッグ情報
- ログファイル：`%APPDATA%\FFmpegGUIKun\logs\`（Windows）
- 設定ファイル：`%APPDATA%\FFmpegGUIKun\config.json`（Windows）

## プラットフォーム固有の注意事項

### Windows
- Windows 10以上推奨
- Windows Defender除外設定が必要な場合あり
- 実行ファイル名：`FFmpeg-GUI-Kun.exe`

### macOS
- macOS 10.14以上推奨
- 初回起動時にセキュリティ許可が必要
- Gatekeeper対応が必要な場合あり

### Linux
- 各ディストリビューション対応
- 必要に応じて追加ライブラリのインストール
- AppImageでの配布も検討可能

## コントリビューション

### 開発ガイドライン
1. Python PEP 8 スタイルガイドに準拠
2. 日本語コメントでのコード説明
3. 包括的なエラーハンドリング
4. ユーザビリティ重視の設計

### テスト手順
1. 各プラットフォームでのビルド確認
2. FFmpeg自動ダウンロード機能のテスト
3. ドラッグ&ドロップ機能の動作確認
4. エンコーディング・GIF変換の品質確認

## ライセンス

このプロジェクトは適切なオープンソースライセンスの下で配布されています。  
詳細については、LICENSEファイルを参照してください。

## 更新履歴

### v1.0.0 (最新)
- 初回リリース
- 動画エンコーディング・GIF変換機能
- FFmpeg自動ダウンロード対応
- PyInstallerビルドシステム
- マルチプラットフォーム対応

---

**開発者向け情報**  
本ドキュメントは開発者向けです。エンドユーザー向けの使用方法については、`README.txt`を参照してください。
