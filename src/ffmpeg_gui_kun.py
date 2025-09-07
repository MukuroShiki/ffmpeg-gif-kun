"""
FFmpeg GIF Kun - GIF変換GUIアプリケーション

This application provides a user-friendly GUI for GIF conversionusing FFmpeg. 
It supports various output formats, encoders, and customizable settings.

Author: 屍鬼 骸 | Mukuro Shiki
License: Open Source
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
from pathlib import Path

# アプリケーションのベースディレクトリを取得
if getattr(sys, 'frozen', False):
    # PyInstallerでビルドされた場合
    BASE_DIR = Path(sys._MEIPASS)
else:
    # 開発環境の場合
    BASE_DIR = Path(__file__).parent.parent

# モジュールのインポート
from gui.main_window import FFmpegGUIApp

def main():
    """
    アプリケーションのメイン関数
    """
    try:
        # メインウィンドウの作成と実行
        app = FFmpegGUIApp()
        app.run()
    except Exception as e:
        messagebox.showerror("Error", f"アプリケーションの起動に失敗しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
