"""
FFmpeg GUI Kun - 動画エンコードタブ

動画エンコード機能のUIと処理を提供する
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from pathlib import Path
from typing import Optional, Callable

from core.ffmpeg_manager import FFmpegManager, EncodeSettings
from utils.drag_drop import drag_drop
from utils.settings import settings_manager, VideoEncodePreset


class VideoEncodeTab:
    """
    動画エンコードタブのクラス
    """
    
    def __init__(
        self,
        parent,
        ffmpeg_manager: FFmpegManager,
        set_processing_callback: Callable[[bool, Optional[object]], None],
        get_processing_callback: Callable[[], bool]
    ):
        """
        動画エンコードタブの初期化
        
        Args:
            parent: 親ウィジェット
            ffmpeg_manager: FFmpegManagerインスタンス
            set_processing_callback: 処理状態設定コールバック
            get_processing_callback: 処理状態取得コールバック
        """
        self.ffmpeg_manager = ffmpeg_manager
        self.set_processing_callback = set_processing_callback
        self.get_processing_callback = get_processing_callback
        
        self.frame = ttk.Frame(parent)
        self.current_process = None
        
        # UI要素の変数
        self.input_file_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.format_var = tk.StringVar(value='mp4')
        self.video_codec_var = tk.StringVar(value='libx264')
        self.audio_codec_var = tk.StringVar(value='aac')
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.fps_var = tk.StringVar()
        self.crf_var = tk.StringVar(value='23')
        self.preset_var = tk.StringVar(value='medium')
        self.use_crf_var = tk.BooleanVar(value=True)
        self.bitrate_var = tk.StringVar()
        
        # 進行状況変数
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="準備完了")
        
        self._setup_ui()
        self._setup_drag_drop()
        
    def _setup_ui(self):
        """
        UIのセットアップ
        """
        # メインフレーム
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ファイル選択セクション
        self._setup_file_section(main_frame)
        
        # エンコード設定セクション
        self._setup_encode_settings(main_frame)
        
        # 進行状況セクション
        self._setup_progress_section(main_frame)
        
        # ボタンセクション
        self._setup_button_section(main_frame)
        
    def _setup_file_section(self, parent):
        """
        ファイル選択セクションのセットアップ
        """
        file_frame = ttk.LabelFrame(parent, text="ファイル選択", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 入力ファイル
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(input_frame, text="入力ファイル:", width=12).pack(side=tk.LEFT)
        
        self.input_entry = ttk.Entry(
            input_frame,
            textvariable=self.input_file_var,
            width=50
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        ttk.Button(
            input_frame,
            text="参照",
            command=self._browse_input_file
        ).pack(side=tk.RIGHT)
        
        # 出力ファイル
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(output_frame, text="出力ファイル:", width=12).pack(side=tk.LEFT)
        
        self.output_entry = ttk.Entry(
            output_frame,
            textvariable=self.output_file_var,
            width=50
        )
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        ttk.Button(
            output_frame,
            text="参照",
            command=self._browse_output_file
        ).pack(side=tk.RIGHT)
        
    def _setup_encode_settings(self, parent):
        """
        エンコード設定セクションのセットアップ
        """
        settings_frame = ttk.LabelFrame(parent, text="エンコード設定", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 設定を2列に分割
        left_frame = ttk.Frame(settings_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(settings_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左列の設定
        self._setup_format_settings(left_frame)
        self._setup_quality_settings(left_frame)
        
        # 右列の設定
        self._setup_video_settings(right_frame)
        self._setup_audio_settings(right_frame)
        
    def _setup_format_settings(self, parent):
        """
        フォーマット設定のセットアップ
        """
        format_frame = ttk.LabelFrame(parent, text="出力フォーマット", padding=5)
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(format_frame, text="フォーマット:").grid(row=0, column=0, sticky=tk.W, pady=2)
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.format_var,
            values=list(self.ffmpeg_manager.SUPPORTED_FORMATS.keys()),
            state='readonly',
            width=15
        )
        format_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        format_combo.bind('<<ComboboxSelected>>', self._on_format_changed)
        
    def _setup_quality_settings(self, parent):
        """
        品質設定のセットアップ
        """
        quality_frame = ttk.LabelFrame(parent, text="品質設定", padding=5)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        # CRF vs ビットレート選択
        crf_radio = ttk.Radiobutton(
            quality_frame,
            text="CRF (推奨):",
            variable=self.use_crf_var,
            value=True,
            command=self._on_quality_mode_changed
        )
        crf_radio.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.crf_scale = ttk.Scale(
            quality_frame,
            from_=0,
            to=51,
            orient=tk.HORIZONTAL,
            variable=self.crf_var,
            length=150
        )
        self.crf_scale.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        self.crf_label = ttk.Label(quality_frame, text="23 (標準)")
        self.crf_label.grid(row=0, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        self.crf_scale.configure(command=self._on_crf_changed)
        
        # ビットレート
        bitrate_radio = ttk.Radiobutton(
            quality_frame,
            text="ビットレート:",
            variable=self.use_crf_var,
            value=False,
            command=self._on_quality_mode_changed
        )
        bitrate_radio.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.bitrate_entry = ttk.Entry(
            quality_frame,
            textvariable=self.bitrate_var,
            width=15,
            state=tk.DISABLED
        )
        self.bitrate_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(quality_frame, text="(例: 2M, 1000k)").grid(row=1, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
    def _setup_video_settings(self, parent):
        """
        ビデオ設定のセットアップ
        """
        video_frame = ttk.LabelFrame(parent, text="ビデオ設定", padding=5)
        video_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ビデオコーデック
        ttk.Label(video_frame, text="ビデオコーデック:").grid(row=0, column=0, sticky=tk.W, pady=2)
        video_codec_combo = ttk.Combobox(
            video_frame,
            textvariable=self.video_codec_var,
            values=list(self.ffmpeg_manager.VIDEO_CODECS.keys()),
            state='readonly',
            width=15
        )
        video_codec_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        video_codec_combo.bind('<<ComboboxSelected>>', self._on_video_codec_changed)
        
        # プリセット
        ttk.Label(video_frame, text="プリセット:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.preset_combo = ttk.Combobox(
            video_frame,
            textvariable=self.preset_var,
            values=list(self.ffmpeg_manager.PRESETS.keys()),
            state='readonly',
            width=15
        )
        self.preset_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 解像度
        ttk.Label(video_frame, text="解像度:").grid(row=2, column=0, sticky=tk.W, pady=2)
        resolution_frame = ttk.Frame(video_frame)
        resolution_frame.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Entry(
            resolution_frame,
            textvariable=self.width_var,
            width=6,
            validate='key',
            validatecommand=(self.frame.register(self._validate_number), '%P')
        ).pack(side=tk.LEFT)
        
        ttk.Label(resolution_frame, text=" x ").pack(side=tk.LEFT)
        
        ttk.Entry(
            resolution_frame,
            textvariable=self.height_var,
            width=6,
            validate='key',
            validatecommand=(self.frame.register(self._validate_number), '%P')
        ).pack(side=tk.LEFT)
        
        # FPS
        ttk.Label(video_frame, text="FPS:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(
            video_frame,
            textvariable=self.fps_var,
            width=15,
            validate='key',
            validatecommand=(self.frame.register(self._validate_float), '%P')
        ).grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
    def _setup_audio_settings(self, parent):
        """
        オーディオ設定のセットアップ
        """
        audio_frame = ttk.LabelFrame(parent, text="オーディオ設定", padding=5)
        audio_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(audio_frame, text="オーディオコーデック:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(
            audio_frame,
            textvariable=self.audio_codec_var,
            values=list(self.ffmpeg_manager.AUDIO_CODECS.keys()),
            state='readonly',
            width=15
        ).grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
    def _setup_progress_section(self, parent):
        """
        進行状況セクションのセットアップ
        """
        progress_frame = ttk.LabelFrame(parent, text="進行状況", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # プログレスバー
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # ステータスラベル
        self.status_label = ttk.Label(
            progress_frame,
            textvariable=self.status_var,
            style='Status.TLabel'
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # ログ表示フレーム
        log_frame = ttk.LabelFrame(progress_frame, text="処理ログ", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # ログテキストボックスとスクロールバー
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_text_frame,
            height=8,
            width=60,
            wrap=tk.WORD,
            font=('Courier', 9),
            bg='#f0f0f0',
            fg='#333333',
            state=tk.DISABLED
        )
        
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ログクリアボタン
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            log_button_frame,
            text="ログクリア",
            command=self._clear_log
        ).pack(side=tk.RIGHT)
        
    def _setup_button_section(self, parent):
        """
        ボタンセクションのセットアップ
        """
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 開始ボタン
        self.start_button = ttk.Button(
            button_frame,
            text="エンコード開始",
            command=self._start_encoding,
            style='Accent.TButton' if hasattr(ttk.Style(), 'theme_use') else 'TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 中止ボタン
        self.cancel_button = ttk.Button(
            button_frame,
            text="中止",
            command=self._cancel_encoding,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # プリセット読み込み・保存ボタン
        preset_frame = ttk.Frame(button_frame)
        preset_frame.pack(side=tk.RIGHT)
        
        # プリセットコンボボックス
        ttk.Label(preset_frame, text="プリセット:").pack(side=tk.LEFT)
        self.preset_combo = ttk.Combobox(
            preset_frame,
            values=settings_manager.get_video_preset_names(),
            state='readonly',
            width=15
        )
        self.preset_combo.pack(side=tk.LEFT, padx=(5, 5))
        self.preset_combo.bind('<<ComboboxSelected>>', self._on_preset_selected)
        
        ttk.Button(
            preset_frame,
            text="設定を保存",
            command=self._save_settings
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(
            preset_frame,
            text="プリセット削除",
            command=self._delete_preset
        ).pack(side=tk.LEFT, padx=(5, 0))
        
    def _setup_drag_drop(self):
        """
        ドラッグ&ドロップのセットアップ
        """
        # 入力ファイルエントリにドロップ機能を追加
        drag_drop.enable_drop(self.input_entry, self._handle_dropped_file)
        
    def _browse_input_file(self):
        """
        入力ファイルの参照
        """
        # 前回のディレクトリを使用
        initial_dir = settings_manager.app_settings.last_input_dir or os.getcwd()
        
        file_path = filedialog.askopenfilename(
            title="入力動画ファイルを選択",
            initialdir=initial_dir,
            filetypes=[
                ("動画ファイル", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            self.input_file_var.set(file_path)
            self._auto_set_output_path(file_path)
            # ディレクトリを記憶
            settings_manager.update_last_directories(input_dir=str(Path(file_path).parent))
            
    def _browse_output_file(self):
        """
        出力ファイルの参照
        """
        # 前回のディレクトリを使用
        initial_dir = settings_manager.app_settings.last_output_dir or os.getcwd()
        
        file_path = filedialog.asksaveasfilename(
            title="出力ファイル名を指定",
            initialdir=initial_dir,
            defaultextension=f".{self.format_var.get()}",
            filetypes=[
                (f"{self.format_var.get().upper()}ファイル", f"*.{self.format_var.get()}"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            self.output_file_var.set(file_path)
            # ディレクトリを記憶
            settings_manager.update_last_directories(output_dir=str(Path(file_path).parent))
            
    def _handle_dropped_file(self, file_path: str):
        """
        ドロップされたファイルの処理
        """
        if os.path.isfile(file_path):
            self.input_file_var.set(file_path)
            self._auto_set_output_path(file_path)
            
    def _on_drop_input(self, event=None):
        """
        入力ファイルのドロップ処理（互換性のため残す）
        """
        # この関数は標準実装では呼ばれないが、互換性のために残す
        pass
                
    def _auto_set_output_path(self, input_path: str):
        """
        入力ファイルパスから出力ファイルパスを自動設定
        """
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_encoded.{self.format_var.get()}"
        self.output_file_var.set(str(output_path))
        
    def _validate_number(self, value: str) -> bool:
        """
        数値バリデーション
        """
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
            
    def _validate_float(self, value: str) -> bool:
        """
        浮動小数点数バリデーション
        """
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
            
    def _on_format_changed(self, event=None):
        """
        出力フォーマット変更時の処理
        """
        # 出力ファイルパスの拡張子を更新
        if self.output_file_var.get():
            output_path = Path(self.output_file_var.get())
            new_output_path = output_path.with_suffix(f".{self.format_var.get()}")
            self.output_file_var.set(str(new_output_path))
            
    def _on_video_codec_changed(self, event=None):
        """
        ビデオコーデック変更時の処理
        """
        codec = self.video_codec_var.get()
        # プリセットの有効/無効を切り替え
        if codec in ['libx264', 'libx265']:
            self.preset_combo.configure(state='readonly')
        else:
            self.preset_combo.configure(state='disabled')
            
    def _on_quality_mode_changed(self):
        """
        品質設定モード変更時の処理
        """
        if self.use_crf_var.get():
            self.crf_scale.configure(state='normal')
            self.bitrate_entry.configure(state='disabled')
        else:
            self.crf_scale.configure(state='disabled')
            self.bitrate_entry.configure(state='normal')
            
    def _on_crf_changed(self, value):
        """
        CRF値変更時の処理
        """
        crf_value = int(float(value))
        quality_text = {
            range(0, 18): "非常に高品質",
            range(18, 23): "高品質",
            range(23, 28): "標準品質",
            range(28, 35): "低品質",
            range(35, 52): "非常に低品質"
        }
        
        for range_obj, text in quality_text.items():
            if crf_value in range_obj:
                self.crf_label.configure(text=f"{crf_value} ({text})")
                break
        else:
            self.crf_label.configure(text=str(crf_value))
            
    def _start_encoding(self):
        """
        エンコード開始
        """
        if self.get_processing_callback():
            messagebox.showwarning("警告", "他の処理が実行中です。")
            return
            
        # 入力検証
        if not self._validate_inputs():
            return
            
        # エンコード設定の作成
        settings = self._create_encode_settings()
        if not settings:
            return
            
        # UIの状態更新
        self._set_encoding_state(True)
        self._append_log("=== エンコード開始 ===")
        self._append_log(f"入力: {settings.input_file}")
        self._append_log(f"出力: {settings.output_file}")
        self._append_log(f"形式: {settings.output_format}")
        self._append_log(f"映像コーデック: {settings.video_codec}")
        self._append_log(f"音声コーデック: {settings.audio_codec}")
        
        # バックグラウンドでエンコード実行
        thread = threading.Thread(target=self._encode_worker, args=(settings,), daemon=True)
        thread.start()
        
    def _validate_inputs(self) -> bool:
        """
        入力値の検証
        """
        if not self.input_file_var.get():
            messagebox.showerror("エラー", "入力ファイルを選択してください。")
            return False
            
        if not os.path.exists(self.input_file_var.get()):
            messagebox.showerror("エラー", "入力ファイルが存在しません。")
            return False
            
        if not self.output_file_var.get():
            messagebox.showerror("エラー", "出力ファイル名を指定してください。")
            return False
            
        # 数値検証
        if self.width_var.get() and not self.width_var.get().isdigit():
            messagebox.showerror("エラー", "幅は数値で入力してください。")
            return False
            
        if self.height_var.get() and not self.height_var.get().isdigit():
            messagebox.showerror("エラー", "高さは数値で入力してください。")
            return False
            
        if self.fps_var.get():
            try:
                float(self.fps_var.get())
            except ValueError:
                messagebox.showerror("エラー", "FPSは数値で入力してください。")
                return False
                
        if not self.use_crf_var.get() and not self.bitrate_var.get():
            messagebox.showerror("エラー", "ビットレートを指定してください。")
            return False
            
        return True
        
    def _create_encode_settings(self) -> Optional[EncodeSettings]:
        """
        エンコード設定を作成
        """
        try:
            settings = EncodeSettings(
                input_file=self.input_file_var.get(),
                output_file=self.output_file_var.get(),
                output_format=self.format_var.get(),
                video_codec=self.video_codec_var.get(),
                audio_codec=self.audio_codec_var.get()
            )
            
            # オプション設定
            if self.width_var.get():
                settings.width = int(self.width_var.get())
            if self.height_var.get():
                settings.height = int(self.height_var.get())
            if self.fps_var.get():
                settings.fps = float(self.fps_var.get())
                
            if self.use_crf_var.get():
                settings.crf = int(float(self.crf_var.get()))
            else:
                settings.bitrate = self.bitrate_var.get()
                
            if self.video_codec_var.get() in ['libx264', 'libx265']:
                settings.preset = self.preset_var.get()
                
            return settings
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定の作成に失敗しました: {str(e)}")
            return None
            
    def _encode_worker(self, settings: EncodeSettings):
        """
        エンコード処理ワーカー
        """
        try:
            success = self.ffmpeg_manager.encode_video(
                settings,
                progress_callback=self._on_progress_update,
                status_callback=self._on_status_update,
                log_callback=self._on_log_update
            )
            
            # メインスレッドで完了処理
            self.frame.after(0, self._on_encoding_complete, success)
            
        except Exception as e:
            self.frame.after(0, self._on_encoding_error, str(e))
            
    def _cancel_encoding(self):
        """
        エンコードキャンセル
        """
        self.ffmpeg_manager.cancel_current_process()
        self._set_encoding_state(False)
        self._on_status_update("キャンセルされました")
        
    def _set_encoding_state(self, is_encoding: bool):
        """
        エンコード状態の設定
        """
        self.set_processing_callback(is_encoding, self.ffmpeg_manager.current_process)
        
        if is_encoding:
            self.start_button.configure(state=tk.DISABLED)
            self.cancel_button.configure(state=tk.NORMAL)
        else:
            self.start_button.configure(state=tk.NORMAL)
            self.cancel_button.configure(state=tk.DISABLED)
            
    def _on_progress_update(self, progress: float):
        """
        進行状況更新
        """
        self.frame.after(0, lambda: self.progress_var.set(progress * 100))
        
    def _on_status_update(self, status: str):
        """
        ステータス更新
        """
        self.frame.after(0, lambda: [
            self.status_var.set(status),
            self._append_log(f"[STATUS] {status}")
        ])
        
    def _on_log_update(self, log_message: str):
        """
        FFmpeg生ログ更新
        """
        if log_message.strip():  # 空行は無視
            self.frame.after(0, lambda: self._append_log(f"[FFMPEG] {log_message}"))
        
    def _on_encoding_complete(self, success: bool):
        """
        エンコード完了処理
        """
        self._set_encoding_state(False)
        self.progress_var.set(0 if not success else 100)
        
        if success:
            messagebox.showinfo("完了", "エンコードが完了しました。")
            # 出力ファイルの場所を開く
            if settings_manager.app_settings.auto_open_output_folder:
                if messagebox.askyesno("確認", "出力フォルダを開きますか？"):
                    output_dir = str(Path(self.output_file_var.get()).parent)
                    if os.name == 'nt':  # Windows
                        os.startfile(output_dir)
                    else:  # macOS, Linux
                        import subprocess
                        subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', output_dir])
        else:
            messagebox.showerror("エラー", "エンコードに失敗しました。")
            
    def _on_encoding_error(self, error_message: str):
        """
        エンコードエラー処理
        """
        self._set_encoding_state(False)
        self.progress_var.set(0)
        messagebox.showerror("エラー", f"エンコード中にエラーが発生しました:\n{error_message}")
        
    def _on_preset_selected(self, event=None):
        """
        プリセット選択時の処理
        """
        preset_name = self.preset_combo.get()
        if not preset_name:
            return
            
        preset = settings_manager.get_video_preset(preset_name)
        if preset:
            self._load_preset(preset)
            
    def _load_preset(self, preset: VideoEncodePreset):
        """
        プリセットを読み込み
        """
        self.format_var.set(preset.format)
        self.video_codec_var.set(preset.video_codec)
        self.audio_codec_var.set(preset.audio_codec)
        self.use_crf_var.set(preset.use_crf)
        self.preset_var.set(preset.preset)
        
        if preset.width:
            self.width_var.set(str(preset.width))
        else:
            self.width_var.set("")
            
        if preset.height:
            self.height_var.set(str(preset.height))
        else:
            self.height_var.set("")
            
        if preset.fps:
            self.fps_var.set(str(preset.fps))
        else:
            self.fps_var.set("")
            
        if preset.use_crf and preset.crf is not None:
            self.crf_var.set(str(preset.crf))
        elif not preset.use_crf and preset.bitrate:
            self.bitrate_var.set(preset.bitrate)
            
        # UI更新
        self._on_quality_mode_changed()
        self._on_format_changed()
        self._on_video_codec_changed()
        
    def _save_settings(self):
        """
        現在の設定をプリセットとして保存
        """
        # プリセット名を入力
        from tkinter import simpledialog
        preset_name = simpledialog.askstring(
            "プリセット保存",
            "プリセット名を入力してください:",
            initialvalue="カスタムプリセット"
        )
        
        if not preset_name:
            return
            
        # 現在の設定からプリセットを作成
        preset = VideoEncodePreset(
            name=preset_name,
            format=self.format_var.get(),
            video_codec=self.video_codec_var.get(),
            audio_codec=self.audio_codec_var.get(),
            preset=self.preset_var.get(),
            use_crf=self.use_crf_var.get()
        )
        
        if self.width_var.get():
            preset.width = int(self.width_var.get())
        if self.height_var.get():
            preset.height = int(self.height_var.get())
        if self.fps_var.get():
            preset.fps = float(self.fps_var.get())
            
        if self.use_crf_var.get():
            preset.crf = int(float(self.crf_var.get()))
        else:
            preset.bitrate = self.bitrate_var.get()
            
        # プリセットを保存
        settings_manager.add_video_preset(preset)
        
        # コンボボックスを更新
        self.preset_combo.configure(values=settings_manager.get_video_preset_names())
        self.preset_combo.set(preset_name)
        
    def _clear_log(self):
        """
        ログテキストをクリア
        """
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
    def _append_log(self, message: str):
        """
        ログにメッセージを追加
        
        Args:
            message: 追加するメッセージ
        """
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.update_idletasks()
        
    def _delete_preset(self):
        """
        選択されたプリセットを削除
        """
        preset_name = self.preset_combo.get()
        if not preset_name:
            messagebox.showwarning("警告", "削除するプリセットを選択してください。")
            return
            
        # 確認ダイアログ
        if messagebox.askyesno("削除確認", f"プリセット「{preset_name}」を削除しますか？"):
            settings_manager.delete_video_preset(preset_name)
            
            # コンボボックスを更新
            self.preset_combo.configure(values=settings_manager.get_video_preset_names())
            self.preset_combo.set("")
            
            messagebox.showinfo("削除完了", f"プリセット「{preset_name}」を削除しました。")
            
    def _load_settings(self):
        """
        設定の読み込み（互換性のため残す）
        """
        # この機能はプリセット機能に統合されました
        messagebox.showinfo("情報", "プリセット機能をご利用ください。")
        
    def set_input_file(self, file_path: str):
        """
        外部から入力ファイルを設定
        """
        self.input_file_var.set(file_path)
        self._auto_set_output_path(file_path)
