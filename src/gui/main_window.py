"""
FFmpeg GIF Kun - メインウィンドウ

メインアプリケーションウィンドウと基本的なGUI要素を提供する
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from pathlib import Path
from typing import Optional, Callable

from gui.gif_convert_tab import GifConvertTab
from core.ffmpeg_manager import FFmpegManager


class FFmpegGUIApp:
    """
    FFmpeg GIF Kunのメインアプリケーションクラス
    
    動画エンコードとGIF変換の機能を提供するGUIアプリケーション
    """
    
    def __init__(self):
        """
        アプリケーションの初期化
        """
        self.root = None
        self.is_processing = False
        self.current_process = None
        self.ffmpeg_manager = FFmpegManager()
        
        # ウィンドウが閉じられる際のフラグ
        self.is_closing = False
        
        self._setup_window()
        self._setup_styles()
        self._setup_tabs()
        self._setup_bindings()
        
    def _setup_window(self):
        """
        メインウィンドウのセットアップ
        """
        # 標準Tkinterルートウィンドウの作成
        self.root = tk.Tk()
        self.root.title("FFmpeg GIF Kun - GIF変換ツール")
        
        # アイコンを設定
        self._set_app_icon()
        
        # ログ表示エリアを含めた最適なサイズを設定
        # 計算基準:
        # - 基本UI: 幅900px、高さ600px
        # - ログエリア: 高さ200px追加
        # - パディング・マージン: 各50px
        optimal_width = 950
        optimal_height = 850
        
        self.root.geometry(f"{optimal_width}x{optimal_height}")
        self.root.minsize(900, 750)  # 最小サイズも調整
        
        # ウィンドウ閉じるイベントのバインド
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 中央配置
        self._center_window()
        
    def _center_window(self):
        """
        ウィンドウを画面中央に配置
        画面が小さい場合は適切に調整
        """
        self.root.update_idletasks()
        
        # 指定したサイズを取得
        width = 950
        height = 850
        
        # 画面サイズを取得
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 画面が小さい場合はサイズを調整
        if width > screen_width * 0.9:
            width = int(screen_width * 0.9)
        if height > screen_height * 0.9:
            height = int(screen_height * 0.9)
            
        # 中央配置の座標を計算
        x = max(0, (screen_width // 2) - (width // 2))
        y = max(0, (screen_height // 2) - (height // 2))
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def _set_app_icon(self):
        """
        アプリケーションアイコンを設定（Windows 11対応）
        """
        try:
            # プロジェクトルートからの相対パスでアイコンファイルを探す
            if hasattr(sys, '_MEIPASS'):
                # PyInstallerで実行される場合の一時フォルダ
                base_path = Path(sys._MEIPASS)
            else:
                # 開発環境での実行
                base_path = Path(__file__).resolve().parent.parent.parent
            
            # アイコンファイルのパス
            icon_ico = base_path / "asset" / "icon.ico"
            icon_png = base_path / "asset" / "logo.png"  # PNGも用意している場合
            
            # Windows: タスクバーアイコン設定
            if sys.platform.startswith("win"):
                # 1. AppUserModelIDを設定（Windows 11で重要）
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # 固有のAppUserModelIDを設定
                    app_id = "FFmpegGIFKun.MediaConverter.Application"
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                    
                    # アプリケーションの実行可能ファイルパスを取得
                    if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
                        # PyInstallerでビルドされた実行ファイル
                        exe_path = sys.executable
                        print(f"Executable path: {exe_path}")
                        
                        # タスクバーに表示される実行ファイルのパスを明示的に設定
                        try:
                            # SetCurrentProcessExplicitAppUserModelIDを再度呼び出し
                            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                        except Exception as e:
                            print(f"Warning: Could not set AppUserModelID: {e}")
                    
                except Exception as e:
                    print(f"Warning: Could not set Windows-specific icon properties: {e}")
                    
                # 2. .icoファイルでウィンドウアイコンを設定
                if icon_ico.exists():
                    self.root.iconbitmap(str(icon_ico))
                    print(f"Window icon set: {icon_ico}")
                else:
                    print(f"Warning: Icon file not found: {icon_ico}")
                    
                # 3. タスクバーアイコンを強制更新（Windows 11対応）
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # タスクバーのアイコンキャッシュをクリアする
                    # これによりPyInstallerの羽アイコンから切り替わる
                    user32 = ctypes.windll.user32
                    hwnd = user32.GetActiveWindow()
                    if hwnd:
                        # ウィンドウを一度隠して再表示（タスクバー更新のため）
                        user32.ShowWindow(hwnd, 0)  # SW_HIDE
                        self.root.after(10, lambda: user32.ShowWindow(hwnd, 1))  # SW_NORMAL
                        
                except Exception as e:
                    print(f"Warning: Could not refresh taskbar icon: {e}")
            
            # macOS/Linux: PNGファイルでアイコンを設定
            elif icon_png.exists():
                try:
                    from tkinter import PhotoImage
                    icon_img = PhotoImage(file=str(icon_png))
                    self.root.iconphoto(True, icon_img)
                    print(f"Icon set: {icon_png}")
                except Exception as e:
                    print(f"Warning: Could not set PNG icon: {e}")
                    
        except Exception as e:
            print(f"Warning: Could not set application icon: {e}")

    def _setup_styles(self):
        """
        UIスタイルのセットアップ
        """
        style = ttk.Style()
        
        # 使用可能なテーマを確認してモダンなものを選択
        available_themes = style.theme_names()
        if 'winnative' in available_themes:
            style.theme_use('winnative')
        elif 'clam' in available_themes:
            style.theme_use('clam')
            
        # カスタムスタイルの設定
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 9))
        
    def _setup_tabs(self):
        """
        タブウィジェットのセットアップ
        """
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タブノートブック
        self.notebook = ttk.Notebook(main_frame)
        
        # GIF変換タブ
        self.gif_convert_tab = GifConvertTab(
            self.notebook,
            self.ffmpeg_manager,
            self._set_processing_state,
            self._get_processing_state
        )
        self.notebook.add(
            self.gif_convert_tab.frame,
            text="GIF変換",
            padding=10
        )
        
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # ステータスバー
        self._setup_status_bar(main_frame)
        
    def _setup_status_bar(self, parent):
        """
        ステータスバーのセットアップ
        """
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        # ステータスラベル
        self.status_label = ttk.Label(
            status_frame,
            text="準備完了",
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # FFmpegステータス
        self.ffmpeg_status_label = ttk.Label(
            status_frame,
            text="",
            style='Status.TLabel'
        )
        self.ffmpeg_status_label.pack(side=tk.RIGHT)
        
        # FFmpegの利用可能性をチェック
        self._check_ffmpeg_availability()
        
    def _check_ffmpeg_availability(self):
        """
        FFmpegの利用可能性をチェック
        """
        if self.ffmpeg_manager.is_ffmpeg_available():
            self.ffmpeg_status_label.config(
                text="FFmpeg: 利用可能",
                foreground="green"
            )
        else:
            self.ffmpeg_status_label.config(
                text="FFmpeg: 利用不可",
                foreground="red"
            )
            
            # FFmpegの自動ダウンロードを提案
            result = messagebox.askyesnocancel(
                "FFmpeg未検出",
                "FFmpegが見つかりません。\n\n"
                "「はい」: 自動ダウンロード（推奨）\n"
                "「いいえ」: 手動インストール情報を表示\n"
                "「キャンセル」: 後で設定"
            )
            
            if result is True:
                self._download_ffmpeg()
            elif result is False:
                self._show_ffmpeg_install_info()
            
    def _setup_bindings(self):
        """
        イベントバインディングのセットアップ
        """
        # キーボードショートカット
        self.root.bind('<Control-o>', lambda e: self._open_file_dialog())
        self.root.bind('<Control-q>', lambda e: self._on_closing())
        self.root.bind('<F1>', lambda e: self._show_help())
        
    def _open_file_dialog(self):
        """
        ファイル選択ダイアログを開く
        """
        file_path = filedialog.askopenfilename(
            title="動画ファイルを選択",
            filetypes=[
                ("動画ファイル", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            # 現在アクティブなタブに応じてファイルパスを設定
            current_tab = self.notebook.index(self.notebook.select())
            if current_tab == 0:  # GIF変換タブ
                self.gif_convert_tab.set_input_file(file_path)
                
    def _show_help(self):
        """
        ヘルプ情報を表示
        """
        help_text = """FFmpeg GIF Kun - ヘルプ

【基本操作】
• ファイル選択: 「参照」ボタンまたはCtrl+Oでファイルを選択
• ドラッグ&ドロップ: 動画ファイルを直接ドラッグして入力欄に設定
• 処理開始: 設定完了後「開始」ボタンをクリック
• 処理中止: 処理中は「中止」ボタンで強制終了可能

【GIF変換タブ】
• 動画からGIFアニメーションを作成
• 解像度、FPS、品質設定で最適化
• ファイルサイズと品質のバランス調整

【キーボードショートカット】
• Ctrl+O: ファイルを開く
• Ctrl+Q: アプリケーション終了
• F1: このヘルプを表示
"""
        messagebox.showinfo("ヘルプ", help_text)
        
    def _set_processing_state(self, is_processing: bool, process=None):
        """
        処理状態を設定
        
        Args:
            is_processing: 処理中フラグ
            process: 現在のプロセス（終了用）
        """
        self.is_processing = is_processing
        self.current_process = process
        
        if is_processing:
            self.status_label.config(text="処理中...")
            # タブの切り替えを無効化
            for i in range(self.notebook.index("end")):
                self.notebook.tab(i, state="disabled" if i != self.notebook.index("current") else "normal")
        else:
            self.status_label.config(text="準備完了")
            self.current_process = None
            # すべてのタブを有効化
            for i in range(self.notebook.index("end")):
                self.notebook.tab(i, state="normal")
                
    def _get_processing_state(self) -> bool:
        """
        現在の処理状態を取得
        
        Returns:
            処理中の場合True
        """
        return self.is_processing
        
    def _on_closing(self):
        """
        ウィンドウを閉じる際の処理
        """
        if self.is_closing:
            return
            
        if self.is_processing:
            # 処理中の場合は警告を表示
            result = messagebox.askyesnocancel(
                "終了確認",
                "処理中です。終了しますか？\n\n"
                "「はい」: 処理を中止して終了\n"
                "「いいえ」: 処理完了を待って終了\n"
                "「キャンセル」: 終了をキャンセル"
            )
            
            if result is True:
                # 処理を中止して終了
                if self.current_process:
                    try:
                        self.current_process.terminate()
                    except:
                        pass
                self._force_quit()
            elif result is False:
                # 処理完了を待つ（実際の実装では処理完了後に自動終了する仕組みが必要）
                messagebox.showinfo("待機中", "処理完了をお待ちください...")
                return
            else:
                # キャンセル
                return
        else:
            self._force_quit()
            
    def _force_quit(self):
        """
        強制終了
        """
        self.is_closing = True
        try:
            self.root.destroy()
        except:
            sys.exit(0)
                
    def _download_ffmpeg(self):
        """
        FFmpegの自動ダウンロード
        """
        # ダウンロード確認ダイアログ
        import platform
        system_name = platform.system()
        
        if system_name == "Darwin":  # macOS
            messagebox.showinfo(
                "macOS用の情報",
                "macOSではHomebrewを使用してFFmpegをインストールすることを推奨します。\n\n"
                "ターミナルで以下のコマンドを実行してください:\n"
                "brew install ffmpeg"
            )
            return
            
        size_mb = self.ffmpeg_manager.ffmpeg_downloader.get_download_size_mb()
        result = messagebox.askyesno(
            "FFmpeg自動ダウンロード",
            f"FFmpegを自動ダウンロードします。\n\n"
            f"サイズ: 約{size_mb}MB\n"
            f"時間: 数分程度\n\n"
            f"ダウンロードを開始しますか？"
        )
        
        if not result:
            return
            
        # ダウンロードウィンドウを作成
        self._show_download_dialog()
        
    def _show_download_dialog(self):
        """
        ダウンロード進行状況ダイアログを表示
        """
        import tkinter as tk
        from tkinter import ttk
        import threading
        
        # ダウンロードダイアログ
        download_window = tk.Toplevel(self.root)
        download_window.title("FFmpegダウンロード中...")
        download_window.geometry("400x150")
        download_window.resizable(False, False)
        download_window.transient(self.root)
        download_window.grab_set()
        
        # 中央配置
        download_window.update_idletasks()
        x = (download_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (download_window.winfo_screenheight() // 2) - (150 // 2)
        download_window.geometry(f"400x150+{x}+{y}")
        
        # ダイアログ内容
        frame = ttk.Frame(download_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        status_label = ttk.Label(frame, text="ダウンロード準備中...")
        status_label.pack(pady=(0, 10))
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            frame,
            variable=progress_var,
            maximum=100,
            length=350
        )
        progress_bar.pack(pady=(0, 10))
        
        cancel_button = ttk.Button(
            frame,
            text="キャンセル",
            command=download_window.destroy
        )
        cancel_button.pack()
        
        # ダウンロード処理
        def progress_callback(current, total):
            if total > 0:
                progress = (current / total) * 100
                download_window.after(0, lambda: progress_var.set(progress))
                
        def status_callback(message):
            download_window.after(0, lambda: status_label.config(text=message))
            
        def download_worker():
            try:
                success = self.ffmpeg_manager.download_ffmpeg_if_needed(
                    progress_callback=progress_callback,
                    status_callback=status_callback
                )
                
                download_window.after(0, lambda: self._on_download_complete(download_window, success))
            except Exception as e:
                download_window.after(0, lambda: self._on_download_error(download_window, str(e)))
                
        # バックグラウンドでダウンロード開始
        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
        
    def _on_download_complete(self, download_window, success):
        """
        ダウンロード完了処理
        """
        download_window.destroy()
        
        if success:
            messagebox.showinfo("完了", "FFmpegのダウンロードが完了しました！")
            # ステータスを更新
            self._check_ffmpeg_availability()
        else:
            messagebox.showerror(
                "ダウンロード失敗", 
                "FFmpegのダウンロードに失敗しました。\n\n"
                "手動インストールを試すか、ネットワーク接続を確認してください。"
            )
            self._show_ffmpeg_install_info()
            
    def _on_download_error(self, download_window, error_message):
        """
        ダウンロードエラー処理
        """
        download_window.destroy()
        messagebox.showerror("ダウンロードエラー", f"エラーが発生しました:\n{error_message}")
        self._show_ffmpeg_install_info()
        
    def _show_ffmpeg_install_info(self):
        """
        FFmpeg手動インストール情報を表示
        """
        install_info = """FFmpeg手動インストール方法:

【Windows】
1. https://ffmpeg.org/download.html からダウンロード
2. ダウンロードしたファイルを展開
3. ffmpeg.exe をシステムPATHに追加

【macOS】
ターミナルで以下のコマンドを実行:
brew install ffmpeg

【Ubuntu/Debian】
ターミナルで以下のコマンドを実行:
sudo apt install ffmpeg

インストール後、アプリケーションを再起動してください。"""
        
        messagebox.showinfo("FFmpeg手動インストール", install_info)
        
    def run(self):
        """
        アプリケーションを実行
        """
        try:
            # Windows 11でタスクバーアイコンを確実に表示するため、
            # 起動後に再度AppUserModelIDを設定
            if sys.platform.startswith("win"):
                self.root.after(100, self._refresh_taskbar_icon)
                
            self.root.mainloop()
        except KeyboardInterrupt:
            self._force_quit()
        except Exception as e:
            messagebox.showerror("エラー", f"予期しないエラーが発生しました: {str(e)}")
            self._force_quit()
            
    def _refresh_taskbar_icon(self):
        """
        タスクバーアイコンを強制更新（Windows 11対応）
        """
        if sys.platform.startswith("win"):
            try:
                import ctypes
                app_id = "FFmpegGIFKun.MediaConverter.Application"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                print("Taskbar icon refreshed")
            except Exception as e:
                print(f"Warning: Could not refresh taskbar icon: {e}")
