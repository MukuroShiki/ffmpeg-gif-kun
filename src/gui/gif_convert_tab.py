"""
FFmpeg GUI Kun - GIF変換タブ

動画からGIF変換機能のUIと処理を提供する
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from pathlib import Path
from typing import Optional, Callable

from core.ffmpeg_manager import FFmpegManager, GifSettings
from utils.drag_drop import drag_drop
from utils.settings import settings_manager, GifConvertPreset


class GifConvertTab:
    """
    GIF変換タブのクラス
    """
    
    def __init__(
        self,
        parent,
        ffmpeg_manager: FFmpegManager,
        set_processing_callback: Callable[[bool, Optional[object]], None],
        get_processing_callback: Callable[[], bool]
    ):
        """
        GIF変換タブの初期化
        
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
        
        # UI要素の変数
        self.input_file_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.fps_var = tk.StringVar(value='10')
        self.start_time_var = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.quality_var = tk.StringVar(value='medium')
        self.maintain_aspect_var = tk.BooleanVar(value=True)
        self.use_time_range_var = tk.BooleanVar(value=False)
        
        # 進行状況変数
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="準備完了")
        
        # 品質プリセット
        self.quality_presets = {
            'low': {'description': '低品質 (ファイルサイズ小)', 'colors': 64},
            'medium': {'description': '標準品質 (バランス)', 'colors': 128},
            'high': {'description': '高品質 (ファイルサイズ大)', 'colors': 256}
        }
        
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
        
        # GIF設定セクション
        self._setup_gif_settings(main_frame)
        
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
        
    def _setup_gif_settings(self, parent):
        """
        GIF設定セクションのセットアップ
        """
        settings_frame = ttk.LabelFrame(parent, text="GIF設定", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 設定を2列に分割
        left_frame = ttk.Frame(settings_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(settings_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左列の設定
        self._setup_size_settings(left_frame)
        self._setup_time_settings(left_frame)
        
        # 右列の設定
        self._setup_quality_settings(right_frame)
        self._setup_preview_info(right_frame)
        
    def _setup_size_settings(self, parent):
        """
        サイズ設定のセットアップ
        """
        size_frame = ttk.LabelFrame(parent, text="サイズ設定", padding=5)
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 解像度設定
        ttk.Label(size_frame, text="解像度:").grid(row=0, column=0, sticky=tk.W, pady=2)
        resolution_frame = ttk.Frame(size_frame)
        resolution_frame.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        self.width_entry = ttk.Entry(
            resolution_frame,
            textvariable=self.width_var,
            width=6,
            validate='key',
            validatecommand=(self.frame.register(self._validate_number), '%P')
        )
        self.width_entry.pack(side=tk.LEFT)
        self.width_entry.bind('<FocusOut>', self._on_width_changed)
        
        ttk.Label(resolution_frame, text=" x ").pack(side=tk.LEFT)
        
        self.height_entry = ttk.Entry(
            resolution_frame,
            textvariable=self.height_var,
            width=6,
            validate='key',
            validatecommand=(self.frame.register(self._validate_number), '%P')
        )
        self.height_entry.pack(side=tk.LEFT)
        self.height_entry.bind('<FocusOut>', self._on_height_changed)
        
        # アスペクト比維持チェックボックス
        maintain_aspect_cb = ttk.Checkbutton(
            size_frame,
            text="アスペクト比を維持",
            variable=self.maintain_aspect_var
        )
        maintain_aspect_cb.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 2))
        
        # FPS設定
        ttk.Label(size_frame, text="FPS:").grid(row=2, column=0, sticky=tk.W, pady=2)
        fps_frame = ttk.Frame(size_frame)
        fps_frame.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Entry(
            fps_frame,
            textvariable=self.fps_var,
            width=8,
            validate='key',
            validatecommand=(self.frame.register(self._validate_float), '%P')
        ).pack(side=tk.LEFT)
        
        ttk.Label(fps_frame, text="fps").pack(side=tk.LEFT, padx=(5, 0))
        
        # よく使われるサイズのプリセットボタン
        preset_frame = ttk.Frame(size_frame)
        preset_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(preset_frame, text="プリセット:").pack(side=tk.LEFT)
        
        presets = [
            ("320x240", 320, 240),
            ("480x360", 480, 360),
            ("640x480", 640, 480),
            ("800x600", 800, 600)
        ]
        
        for text, width, height in presets:
            ttk.Button(
                preset_frame,
                text=text,
                command=lambda w=width, h=height: self._set_resolution_preset(w, h),
                width=8
            ).pack(side=tk.LEFT, padx=(5, 0))
            
    def _setup_time_settings(self, parent):
        """
        時間設定のセットアップ
        """
        time_frame = ttk.LabelFrame(parent, text="時間設定", padding=5)
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 時間範囲指定チェックボックス
        time_range_cb = ttk.Checkbutton(
            time_frame,
            text="時間範囲を指定",
            variable=self.use_time_range_var,
            command=self._on_time_range_toggled
        )
        time_range_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # 開始時間
        ttk.Label(time_frame, text="開始時間:").grid(row=1, column=0, sticky=tk.W, pady=2)
        start_frame = ttk.Frame(time_frame)
        start_frame.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        self.start_time_entry = ttk.Entry(
            start_frame,
            textvariable=self.start_time_var,
            width=10,
            state=tk.DISABLED
        )
        self.start_time_entry.pack(side=tk.LEFT)
        
        ttk.Label(start_frame, text="秒").pack(side=tk.LEFT, padx=(5, 0))
        
        # 継続時間
        ttk.Label(time_frame, text="継続時間:").grid(row=2, column=0, sticky=tk.W, pady=2)
        duration_frame = ttk.Frame(time_frame)
        duration_frame.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        self.duration_entry = ttk.Entry(
            duration_frame,
            textvariable=self.duration_var,
            width=10,
            state=tk.DISABLED
        )
        self.duration_entry.pack(side=tk.LEFT)
        
        ttk.Label(duration_frame, text="秒").pack(side=tk.LEFT, padx=(5, 0))
        
        # 時間フォーマットの説明
        ttk.Label(
            time_frame,
            text="※ 例: 10.5 (10.5秒から), 5 (5秒間)",
            font=('Arial', 8),
            foreground='gray'
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
    def _setup_quality_settings(self, parent):
        """
        品質設定のセットアップ
        """
        quality_frame = ttk.LabelFrame(parent, text="品質設定", padding=5)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(quality_frame, text="品質:").grid(row=0, column=0, sticky=tk.W, pady=2)
        quality_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.quality_var,
            values=list(self.quality_presets.keys()),
            state='readonly',
            width=15
        )
        quality_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        quality_combo.bind('<<ComboboxSelected>>', self._on_quality_changed)
        
        # 品質の説明ラベル
        self.quality_desc_label = ttk.Label(
            quality_frame,
            text=self.quality_presets['medium']['description'],
            font=('Arial', 8),
            foreground='blue'
        )
        self.quality_desc_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # 最適化のヒント
        hints_text = """【最適化のヒント】
• 低品質: ウェブ用、プレビュー用
• 標準品質: 一般的な用途に最適
• 高品質: 詳細が重要な場合
• 低FPS: ファイルサイズ削減
• 小さい解像度: 読み込み高速化"""
        
        hints_label = ttk.Label(
            quality_frame,
            text=hints_text,
            font=('Arial', 8),
            foreground='gray',
            justify=tk.LEFT
        )
        hints_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
    def _setup_preview_info(self, parent):
        """
        プレビュー情報のセットアップ
        """
        info_frame = ttk.LabelFrame(parent, text="ファイル情報", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(
            info_frame,
            height=6,
            width=30,
            wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.insert(tk.END, "動画ファイルを選択すると\n情報を表示します")
        self.info_text.configure(state=tk.DISABLED)
        
        # 情報更新ボタン
        ttk.Button(
            info_frame,
            text="情報を更新",
            command=self._update_file_info
        ).pack(pady=(5, 0))
        
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
            text="GIF変換開始",
            command=self._start_conversion,
            style='Accent.TButton' if hasattr(ttk.Style(), 'theme_use') else 'TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 中止ボタン
        self.cancel_button = ttk.Button(
            button_frame,
            text="中止",
            command=self._cancel_conversion,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # プレビューボタンとプリセット
        preset_frame = ttk.Frame(button_frame)
        preset_frame.pack(side=tk.RIGHT)
        
        # プリセットコンボボックス
        ttk.Label(preset_frame, text="プリセット:").pack(side=tk.LEFT)
        self.preset_combo = ttk.Combobox(
            preset_frame,
            values=settings_manager.get_gif_preset_names(),
            state='readonly',
            width=15
        )
        self.preset_combo.pack(side=tk.LEFT, padx=(5, 5))
        self.preset_combo.bind('<<ComboboxSelected>>', self._on_preset_selected)
        
        ttk.Button(
            preset_frame,
            text="設定保存",
            command=self._save_preset
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(
            preset_frame,
            text="プリセット削除",
            command=self._delete_preset
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(
            preset_frame,
            text="プレビュー作成",
            command=self._create_preview
        ).pack(side=tk.LEFT, padx=(10, 0))
        
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
            self._update_file_info()
            # ディレクトリを記憶
            settings_manager.update_last_directories(input_dir=str(Path(file_path).parent))
            
    def _browse_output_file(self):
        """
        出力ファイルの参照
        """
        # 前回のディレクトリを使用
        initial_dir = settings_manager.app_settings.last_output_dir or os.getcwd()
        
        file_path = filedialog.asksaveasfilename(
            title="出力GIFファイル名を指定",
            initialdir=initial_dir,
            defaultextension=".gif",
            filetypes=[
                ("GIFファイル", "*.gif"),
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
            self._update_file_info()
            
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
        output_path = input_path_obj.parent / f"{input_path_obj.stem}.gif"
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
            
    def _set_resolution_preset(self, width: int, height: int):
        """
        解像度プリセットの設定
        """
        self.width_var.set(str(width))
        self.height_var.set(str(height))
        
    def _on_width_changed(self, event=None):
        """
        幅変更時の処理（アスペクト比維持）
        """
        if not self.maintain_aspect_var.get():
            return
            
        if not self.width_var.get() or not self.input_file_var.get():
            return
            
        try:
            new_width = int(self.width_var.get())
            video_info = self.ffmpeg_manager.get_video_info(self.input_file_var.get())
            if video_info:
                # 元の動画のアスペクト比を取得
                for stream in video_info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        orig_width = stream.get('width')
                        orig_height = stream.get('height')
                        if orig_width and orig_height:
                            aspect_ratio = orig_width / orig_height
                            new_height = int(new_width / aspect_ratio)
                            self.height_var.set(str(new_height))
                            break
        except (ValueError, TypeError):
            pass
            
    def _on_height_changed(self, event=None):
        """
        高さ変更時の処理（アスペクト比維持）
        """
        if not self.maintain_aspect_var.get():
            return
            
        if not self.height_var.get() or not self.input_file_var.get():
            return
            
        try:
            new_height = int(self.height_var.get())
            video_info = self.ffmpeg_manager.get_video_info(self.input_file_var.get())
            if video_info:
                # 元の動画のアスペクト比を取得
                for stream in video_info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        orig_width = stream.get('width')
                        orig_height = stream.get('height')
                        if orig_width and orig_height:
                            aspect_ratio = orig_width / orig_height
                            new_width = int(new_height * aspect_ratio)
                            self.width_var.set(str(new_width))
                            break
        except (ValueError, TypeError):
            pass
            
    def _on_time_range_toggled(self):
        """
        時間範囲指定の切り替え
        """
        if self.use_time_range_var.get():
            self.start_time_entry.configure(state=tk.NORMAL)
            self.duration_entry.configure(state=tk.NORMAL)
        else:
            self.start_time_entry.configure(state=tk.DISABLED)
            self.duration_entry.configure(state=tk.DISABLED)
            
    def _on_quality_changed(self, event=None):
        """
        品質設定変更時の処理
        """
        quality = self.quality_var.get()
        if quality in self.quality_presets:
            desc = self.quality_presets[quality]['description']
            self.quality_desc_label.configure(text=desc)
            
    def _update_file_info(self):
        """
        ファイル情報の更新
        """
        if not self.input_file_var.get() or not os.path.exists(self.input_file_var.get()):
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "ファイルが選択されていません")
            self.info_text.configure(state=tk.DISABLED)
            return
            
        video_info = self.ffmpeg_manager.get_video_info(self.input_file_var.get())
        
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        if video_info:
            info_text = "【ファイル情報】\n"
            
            # フォーマット情報
            if 'format' in video_info:
                format_info = video_info['format']
                duration = float(format_info.get('duration', 0))
                file_size = int(format_info.get('size', 0))
                
                info_text += f"時間: {duration:.1f}秒\n"
                info_text += f"サイズ: {file_size / (1024*1024):.1f}MB\n"
                
            # 動画ストリーム情報
            for stream in video_info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width = stream.get('width', 'N/A')
                    height = stream.get('height', 'N/A')
                    fps = stream.get('avg_frame_rate', 'N/A')
                    codec = stream.get('codec_name', 'N/A')
                    
                    if fps != 'N/A' and '/' in str(fps):
                        try:
                            num, den = fps.split('/')
                            fps = f"{float(num)/float(den):.1f}"
                        except:
                            pass
                            
                    info_text += f"解像度: {width}x{height}\n"
                    info_text += f"FPS: {fps}\n"
                    info_text += f"コーデック: {codec}\n"
                    break
                    
            # 推奨設定の提案
            info_text += "\n【推奨設定】\n"
            if 'streams' in video_info:
                for stream in video_info['streams']:
                    if stream.get('codec_type') == 'video':
                        orig_width = stream.get('width', 0)
                        orig_height = stream.get('height', 0)
                        
                        if orig_width and orig_height:
                            # 適切な解像度を提案
                            if orig_width > 800:
                                rec_width = 800
                                rec_height = int(800 * orig_height / orig_width)
                                info_text += f"解像度: {rec_width}x{rec_height}\n"
                            else:
                                info_text += f"解像度: 元のまま\n"
                                
                            info_text += "FPS: 10-15fps\n"
                            info_text += "品質: 標準\n"
                        break
        else:
            info_text = "ファイル情報の取得に失敗しました"
            
        self.info_text.insert(tk.END, info_text)
        self.info_text.configure(state=tk.DISABLED)
        
    def _start_conversion(self):
        """
        GIF変換開始
        """
        if self.get_processing_callback():
            messagebox.showwarning("警告", "他の処理が実行中です。")
            return
            
        # 入力検証
        if not self._validate_inputs():
            return
            
        # GIF設定の作成
        settings = self._create_gif_settings()
        if not settings:
            return
            
        # UIの状態更新
        self._set_conversion_state(True)
        self._append_log("=== GIF変換開始 ===")
        self._append_log(f"入力: {settings.input_file}")
        self._append_log(f"出力: {settings.output_file}")
        self._append_log(f"指定サイズ: {settings.width}x{settings.height}" if settings.width and settings.height else f"指定サイズ: 未設定")
        self._append_log(f"指定FPS: {settings.fps}")
        self._append_log(f"品質: {settings.quality}")
        if settings.start_time is not None:
            self._append_log(f"開始時間: {settings.start_time}秒")
        if settings.duration is not None:
            self._append_log(f"継続時間: {settings.duration}秒")
        
        # バックグラウンドで変換実行
        thread = threading.Thread(target=self._conversion_worker, args=(settings,), daemon=True)
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
            
        # FPS検証
        if self.fps_var.get():
            try:
                fps = float(self.fps_var.get())
                if fps <= 0:
                    messagebox.showerror("エラー", "FPSは正の値で入力してください。")
                    return False
            except ValueError:
                messagebox.showerror("エラー", "FPSは数値で入力してください。")
                return False
                
        # 時間範囲検証
        if self.use_time_range_var.get():
            if self.start_time_var.get():
                try:
                    float(self.start_time_var.get())
                except ValueError:
                    messagebox.showerror("エラー", "開始時間は数値で入力してください。")
                    return False
                    
            if self.duration_var.get():
                try:
                    float(self.duration_var.get())
                except ValueError:
                    messagebox.showerror("エラー", "継続時間は数値で入力してください。")
                    return False
                    
        return True
        
    def _create_gif_settings(self) -> Optional[GifSettings]:
        """
        GIF変換設定を作成
        """
        try:
            settings = GifSettings(
                input_file=self.input_file_var.get(),
                output_file=self.output_file_var.get(),
                quality=self.quality_var.get()
            )
            
            # オプション設定
            if self.width_var.get():
                settings.width = int(self.width_var.get())
            if self.height_var.get():
                settings.height = int(self.height_var.get())
            if self.fps_var.get():
                settings.fps = float(self.fps_var.get())
                
            if self.use_time_range_var.get():
                if self.start_time_var.get():
                    settings.start_time = float(self.start_time_var.get())
                if self.duration_var.get():
                    settings.duration = float(self.duration_var.get())
                    
            return settings
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定の作成に失敗しました: {str(e)}")
            return None
            
    def _conversion_worker(self, settings: GifSettings):
        """
        GIF変換処理ワーカー
        """
        try:
            success = self.ffmpeg_manager.create_gif(
                settings,
                progress_callback=self._on_progress_update,
                status_callback=self._on_status_update,
                log_callback=self._on_log_update
            )
            
            # メインスレッドで完了処理
            self.frame.after(0, self._on_conversion_complete, success)
            
        except Exception as e:
            self.frame.after(0, self._on_conversion_error, str(e))
            
    def _cancel_conversion(self):
        """
        GIF変換キャンセル
        """
        self.ffmpeg_manager.cancel_current_process()
        self._set_conversion_state(False)
        self._on_status_update("キャンセルされました")
        
    def _create_preview(self):
        """
        プレビューGIF作成（短時間・低品質）
        """
        if not self.input_file_var.get():
            messagebox.showwarning("警告", "まず入力ファイルを選択してください。")
            return
            
        # プレビュー設定（3秒間、低品質）
        input_path = Path(self.input_file_var.get())
        preview_path = input_path.parent / f"{input_path.stem}_preview.gif"
        
        settings = GifSettings(
            input_file=self.input_file_var.get(),
            output_file=str(preview_path),
            width=320,
            height=240,
            fps=5,
            start_time=0,
            duration=3,
            quality='low'
        )
        
        # UIの状態更新
        self._set_conversion_state(True)
        
        # バックグラウンドで変換実行
        thread = threading.Thread(
            target=lambda: self._preview_worker(settings),
            daemon=True
        )
        thread.start()
        
    def _preview_worker(self, settings: GifSettings):
        """
        プレビュー作成ワーカー
        """
        try:
            success = self.ffmpeg_manager.create_gif(
                settings,
                progress_callback=self._on_progress_update,
                status_callback=lambda s: self._on_status_update(f"プレビュー作成中: {s}")
            )
            
            # メインスレッドで完了処理
            self.frame.after(0, self._on_preview_complete, success, settings.output_file)
            
        except Exception as e:
            self.frame.after(0, self._on_conversion_error, str(e))
            
    def _set_conversion_state(self, is_converting: bool):
        """
        変換状態の設定
        """
        self.set_processing_callback(is_converting, self.ffmpeg_manager.current_process)
        
        if is_converting:
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
        
    def _on_conversion_complete(self, success: bool):
        """
        GIF変換完了処理
        """
        self._set_conversion_state(False)
        self.progress_var.set(0 if not success else 100)
        
        if success:
            messagebox.showinfo("完了", "GIF変換が完了しました。")
            # 出力ファイルの場所を開く
            if settings_manager.app_settings.auto_open_output_folder:
                if messagebox.askyesno("確認", "出力フォルダを開きますか？"):
                    output_dir = str(Path(self.output_file_var.get()).parent)
                    if os.name == 'nt':  # Windows
                        os.startfile(output_dir)
                    else:  # macOS, Linux
                        import subprocess
                        import sys
                        subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', output_dir])
        else:
            messagebox.showerror("エラー", "GIF変換に失敗しました。")
            
    def _on_preview_complete(self, success: bool, preview_path: str):
        """
        プレビュー作成完了処理
        """
        self._set_conversion_state(False)
        self.progress_var.set(0 if not success else 100)
        
        if success:
            result = messagebox.askyesno(
                "プレビュー完了",
                f"プレビューGIFが作成されました。\n{preview_path}\n\nフォルダを開きますか？"
            )
            if result:
                output_dir = str(Path(preview_path).parent)
                if os.name == 'nt':  # Windows
                    os.startfile(output_dir)
                else:  # macOS, Linux
                    import subprocess
                    import sys
                    subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', output_dir])
        else:
            messagebox.showerror("エラー", "プレビュー作成に失敗しました。")
            
    def _on_conversion_error(self, error_message: str):
        """
        GIF変換エラー処理
        """
        self._set_conversion_state(False)
        self.progress_var.set(0)
        messagebox.showerror("エラー", f"変換中にエラーが発生しました:\n{error_message}")
        
    def _on_preset_selected(self, event=None):
        """
        プリセット選択時の処理
        """
        preset_name = self.preset_combo.get()
        if not preset_name:
            return
            
        preset = settings_manager.get_gif_preset(preset_name)
        if preset:
            self._load_preset(preset)
            
    def _load_preset(self, preset: GifConvertPreset):
        """
        プリセットを読み込み
        """
        if preset.width:
            self.width_var.set(str(preset.width))
        else:
            self.width_var.set("")
            
        if preset.height:
            self.height_var.set(str(preset.height))
        else:
            self.height_var.set("")
            
        self.fps_var.set(str(preset.fps))
        self.quality_var.set(preset.quality)
        self.maintain_aspect_var.set(preset.maintain_aspect)
        
        # UI更新
        self._on_quality_changed()
        
    def _save_preset(self):
        """
        現在の設定をプリセットとして保存
        """
        # プリセット名を入力
        from tkinter import simpledialog
        preset_name = simpledialog.askstring(
            "プリセット保存",
            "プリセット名を入力してください:",
            initialvalue="カスタムGIFプリセット"
        )
        
        if not preset_name:
            return
            
        # 現在の設定からプリセットを作成
        preset = GifConvertPreset(
            name=preset_name,
            fps=float(self.fps_var.get()) if self.fps_var.get() else 10.0,
            quality=self.quality_var.get(),
            maintain_aspect=self.maintain_aspect_var.get()
        )
        
        if self.width_var.get():
            preset.width = int(self.width_var.get())
        if self.height_var.get():
            preset.height = int(self.height_var.get())
            
        # プリセットを保存
        settings_manager.add_gif_preset(preset)
        
        # コンボボックスを更新
        self.preset_combo.configure(values=settings_manager.get_gif_preset_names())
        self.preset_combo.set(preset_name)
        
        messagebox.showinfo("保存完了", f"プリセット「{preset_name}」を保存しました。")
        
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
            settings_manager.delete_gif_preset(preset_name)
            
            # コンボボックスを更新
            self.preset_combo.configure(values=settings_manager.get_gif_preset_names())
            self.preset_combo.set("")
            
            messagebox.showinfo("削除完了", f"プリセット「{preset_name}」を削除しました。")
        
    def set_input_file(self, file_path: str):
        """
        外部から入力ファイルを設定
        """
        self.input_file_var.set(file_path)
        self._auto_set_output_path(file_path)
        self._update_file_info()
        
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
