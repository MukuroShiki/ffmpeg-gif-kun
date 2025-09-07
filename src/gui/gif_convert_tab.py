"""
FFmpeg GIF Kun - 高品質GIF変換タブ

2段階方式による高品質GIF変換機能のUIと処理を提供する
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from pathlib import Path
from typing import Optional, Callable

from core.ffmpeg_manager import FFmpegManager, GifSettings
from utils.settings import settings_manager, GifConvertPreset


class GifConvertTab:
    """
    高品質GIF変換タブのクラス
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
        self.fps_var = tk.StringVar(value='15')
        self.start_time_var = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.quality_var = tk.StringVar(value='medium')
        self.maintain_aspect_var = tk.BooleanVar(value=True)
        self.use_time_range_var = tk.BooleanVar(value=False)
        
        # 高品質変換用の新しい変数
        self.use_advanced_mode_var = tk.BooleanVar(value=True)
        self.enable_hardware_accel_var = tk.BooleanVar(value=True)
        self.hardware_accel_var = tk.StringVar(value='auto')
        self.scaling_algorithm_var = tk.StringVar(value='lanczos')
        self.dither_mode_var = tk.StringVar(value='floyd_steinberg')
        
        # 進行状況変数
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="準備完了")
        
        # 品質プリセット（拡張版）
        self.quality_presets = {
            'low': {'description': '低品質 (64色, ファイルサイズ最小)', 'colors': 64},
            'medium': {'description': '標準品質 (128色, バランス良好)', 'colors': 128},
            'high': {'description': '高品質 (256色, ファイルサイズ大)', 'colors': 256}
        }
        
        # ハードウェアアクセラレーションの選択肢
        self.hardware_accel_options = {
            'auto': '自動選択',
            'cuda': 'NVIDIA CUDA',
            'qsv': 'Intel Quick Sync',
            'videotoolbox': 'Apple VideoToolbox',
            'vaapi': 'Video Acceleration API',
            'd3d11va': 'Direct3D 11',
            'none': '使用しない'
        }
        
        # スケーリングアルゴリズムの選択肢
        self.scaling_algorithms = {
            'lanczos': 'Lanczos (最高品質)',
            'bicubic': 'Bicubic (高品質)',
            'bilinear': 'Bilinear (高速)',
            'neighbor': 'Nearest Neighbor (最高速)'
        }
        
        # ディザリング方式の選択肢
        self.dither_modes = {
            'floyd_steinberg': 'Floyd-Steinberg (推奨)',
            'sierra2': 'Sierra2',
            'sierra2_4a': 'Sierra2_4a',
            'none': 'なし (高速)'
        }
        
        self._setup_ui()
        # ドラッグ&ドロップは一時的に無効化（問題解決後に再実装）
        # self._setup_drag_drop()
        
        # UI構築完了後にシステム情報を更新
        self.frame.after(100, self._update_hardware_accel_options)
        
    def _setup_ui(self):
        """
        コンパクトなUIのセットアップ
        """
        # メインフレーム
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 上段：ファイル選択とボタン
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        self._setup_file_and_buttons_section(top_frame)
        
        # 中段：設定セクション（タブ形式）
        settings_notebook = ttk.Notebook(main_frame)
        settings_notebook.pack(fill=tk.X, pady=(0, 5))
        
        # 基本設定タブ
        basic_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(basic_tab, text="基本設定")
        self._setup_basic_settings(basic_tab)
        
        # 高度な設定タブ
        advanced_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(advanced_tab, text="高度な設定")
        self._setup_advanced_settings_tab(advanced_tab)
        
        # システム情報タブ
        info_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(info_tab, text="動画情報")
        self._setup_info_tab(info_tab)
        
        # 下段：進行状況セクション（コンパクト）
        progress_frame = ttk.LabelFrame(main_frame, text="変換進行状況", padding=5)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        self._setup_compact_progress_section(progress_frame)
        
    def _setup_file_and_buttons_section(self, parent):
        """
        ファイル選択とボタンをまとめたセクション
        """
        # ファイル選択部分
        file_frame = ttk.LabelFrame(parent, text="ファイル", padding=5)
        file_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))
        
        # 入力ファイル行
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Label(input_frame, text="動画:", width=6).pack(side=tk.LEFT)
        
        self.input_entry = ttk.Entry(
            input_frame,
            textvariable=self.input_file_var,
            font=('Arial', 9)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 3))
        
        ttk.Button(
            input_frame,
            text="...",
            command=self._browse_input_file,
            width=3
        ).pack(side=tk.RIGHT)
        
        # 出力ファイル行
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Label(output_frame, text="GIF:", width=6).pack(side=tk.LEFT)
        
        self.output_entry = ttk.Entry(
            output_frame,
            textvariable=self.output_file_var,
            font=('Arial', 9)
        )
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 3))
        
        ttk.Button(
            output_frame,
            text="...",
            command=self._browse_output_file,
            width=3
        ).pack(side=tk.RIGHT)
        
        # ボタン部分
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, side=tk.TOP)
        
        # 左側：変換・中止ボタン
        convert_frame = ttk.Frame(button_frame)
        convert_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.start_button = ttk.Button(
            convert_frame,
            text="🎬 変換開始",
            command=self._start_conversion
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_button = ttk.Button(
            convert_frame,
            text="⏹ 中止",
            command=self._cancel_conversion,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT)
        
        # 右側：プリセット管理
        preset_frame = ttk.Frame(button_frame)
        preset_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(preset_frame, text="プリセット:", font=('Arial', 9)).pack(side=tk.LEFT)
        
        self.preset_combo = ttk.Combobox(
            preset_frame,
            values=settings_manager.get_gif_preset_names(),
            state='readonly',
            width=12,
            font=('Arial', 9)
        )
        self.preset_combo.pack(side=tk.LEFT, padx=(3, 3))
        self.preset_combo.bind('<<ComboboxSelected>>', self._on_preset_selected)
        
        ttk.Button(
            preset_frame,
            text="保存",
            command=self._save_preset,
            width=5
        ).pack(side=tk.LEFT, padx=(0, 2))
        
        ttk.Button(
            preset_frame,
            text="削除",
            command=self._delete_preset,
            width=5
        ).pack(side=tk.LEFT)
        
    def _setup_basic_settings(self, parent):
        """
        基本設定タブの内容
        """
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左列
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # サイズ・FPS設定
        size_frame = ttk.LabelFrame(left_frame, text="サイズ・FPS", padding=5)
        size_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 解像度行
        res_frame = ttk.Frame(size_frame)
        res_frame.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Label(res_frame, text="解像度:", width=8).pack(side=tk.LEFT)
        
        self.width_entry = ttk.Entry(
            res_frame,
            textvariable=self.width_var,
            width=6,
            validate='key',
            validatecommand=(self.frame.register(self._validate_number), '%P')
        )
        self.width_entry.pack(side=tk.LEFT)
        
        ttk.Label(res_frame, text="×").pack(side=tk.LEFT, padx=2)
        
        self.height_entry = ttk.Entry(
            res_frame,
            textvariable=self.height_var,
            width=6,
            validate='key',
            validatecommand=(self.frame.register(self._validate_number), '%P')
        )
        self.height_entry.pack(side=tk.LEFT)
        
        maintain_cb = ttk.Checkbutton(
            res_frame,
            text="比率維持",
            variable=self.maintain_aspect_var
        )
        maintain_cb.pack(side=tk.LEFT, padx=(10, 0))
        
        # FPS行
        fps_frame = ttk.Frame(size_frame)
        fps_frame.pack(fill=tk.X, pady=(3, 0))
        
        ttk.Label(fps_frame, text="FPS:", width=8).pack(side=tk.LEFT)
        
        ttk.Entry(
            fps_frame,
            textvariable=self.fps_var,
            width=6,
            validate='key',
            validatecommand=(self.frame.register(self._validate_float), '%P')
        ).pack(side=tk.LEFT)
        
        ttk.Label(fps_frame, text="fps").pack(side=tk.LEFT, padx=(3, 0))
        
        # プリセットボタン
        preset_buttons_frame = ttk.Frame(fps_frame)
        preset_buttons_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        presets = [("320×240", 320, 240), ("480×360", 480, 360), ("640×480", 640, 480)]
        for text, w, h in presets:
            ttk.Button(
                preset_buttons_frame,
                text=text,
                command=lambda width=w, height=h: self._set_resolution_preset(width, height),
                width=8
            ).pack(side=tk.LEFT, padx=(0, 2))
        
        # 時間範囲設定
        time_frame = ttk.LabelFrame(left_frame, text="時間範囲", padding=5)
        time_frame.pack(fill=tk.X)
        
        # 時間範囲有効化
        time_cb_frame = ttk.Frame(time_frame)
        time_cb_frame.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Checkbutton(
            time_cb_frame,
            text="時間範囲を指定",
            variable=self.use_time_range_var,
            command=self._on_time_range_toggled
        ).pack(side=tk.LEFT)
        
        # 開始時間・継続時間
        time_values_frame = ttk.Frame(time_frame)
        time_values_frame.pack(fill=tk.X)
        
        ttk.Label(time_values_frame, text="開始:", width=6).pack(side=tk.LEFT)
        
        self.start_time_entry = ttk.Entry(
            time_values_frame,
            textvariable=self.start_time_var,
            width=8,
            state=tk.DISABLED
        )
        self.start_time_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(time_values_frame, text="秒 継続:").pack(side=tk.LEFT)
        
        self.duration_entry = ttk.Entry(
            time_values_frame,
            textvariable=self.duration_var,
            width=8,
            state=tk.DISABLED
        )
        self.duration_entry.pack(side=tk.LEFT, padx=(3, 0))
        
        ttk.Label(time_values_frame, text="秒").pack(side=tk.LEFT, padx=(3, 0))
        
        # 右列
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 変換モード
        mode_frame = ttk.LabelFrame(right_frame, text="変換モード", padding=5)
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Checkbutton(
            mode_frame,
            text="高品質モード (2段階変換)",
            variable=self.use_advanced_mode_var,
            command=self._on_advanced_mode_changed
        ).pack(anchor=tk.W)
        
        self.mode_desc_label = ttk.Label(
            mode_frame,
            text="✓ より高品質なGIFを生成",
            font=('Arial', 8),
            foreground='blue'
        )
        self.mode_desc_label.pack(anchor=tk.W, pady=(2, 0))
        
        # 品質設定
        quality_frame = ttk.LabelFrame(right_frame, text="品質", padding=5)
        quality_frame.pack(fill=tk.X)
        
        quality_select_frame = ttk.Frame(quality_frame)
        quality_select_frame.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Label(quality_select_frame, text="品質:", width=6).pack(side=tk.LEFT)
        
        quality_combo = ttk.Combobox(
            quality_select_frame,
            textvariable=self.quality_var,
            values=list(self.quality_presets.keys()),
            state='readonly',
            width=10
        )
        quality_combo.pack(side=tk.LEFT)
        quality_combo.bind('<<ComboboxSelected>>', self._on_quality_changed)
        
        self.quality_desc_label = ttk.Label(
            quality_frame,
            text=self.quality_presets['medium']['description'],
            font=('Arial', 8),
            foreground='gray'
        )
        self.quality_desc_label.pack(anchor=tk.W)
        
    def _setup_advanced_settings_tab(self, parent):
        """
        高度な設定タブの内容
        """
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左列
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # ハードウェアアクセラレーション
        hw_frame = ttk.LabelFrame(left_frame, text="ハードウェアアクセラレーション", padding=5)
        hw_frame.pack(fill=tk.X, pady=(0, 5))
        
        hw_enable_frame = ttk.Frame(hw_frame)
        hw_enable_frame.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Checkbutton(
            hw_enable_frame,
            text="有効",
            variable=self.enable_hardware_accel_var,
            command=self._on_hardware_accel_toggled
        ).pack(side=tk.LEFT)
        
        self.hwaccel_combo = ttk.Combobox(
            hw_enable_frame,
            textvariable=self.hardware_accel_var,
            values=list(self.hardware_accel_options.keys()),
            state='readonly',
            width=12
        )
        self.hwaccel_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.hwaccel_combo.bind('<<ComboboxSelected>>', self._on_hardware_accel_changed)
        
        self.hwaccel_desc_label = ttk.Label(
            hw_frame,
            text=self.hardware_accel_options.get(self.hardware_accel_var.get(), ''),
            font=('Arial', 8),
            foreground='gray'
        )
        self.hwaccel_desc_label.pack(anchor=tk.W)
        
        # スケーリング・ディザリング
        filter_frame = ttk.LabelFrame(left_frame, text="画像処理", padding=5)
        filter_frame.pack(fill=tk.X)
        
        # スケーリング
        scale_frame = ttk.Frame(filter_frame)
        scale_frame.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Label(scale_frame, text="スケーリング:", width=12).pack(side=tk.LEFT)
        
        scaling_combo = ttk.Combobox(
            scale_frame,
            textvariable=self.scaling_algorithm_var,
            values=list(self.scaling_algorithms.keys()),
            state='readonly',
            width=12
        )
        scaling_combo.pack(side=tk.LEFT)
        scaling_combo.bind('<<ComboboxSelected>>', self._on_scaling_algorithm_changed)
        
        # ディザリング
        dither_frame = ttk.Frame(filter_frame)
        dither_frame.pack(fill=tk.X, pady=(3, 0))
        
        ttk.Label(dither_frame, text="ディザリング:", width=12).pack(side=tk.LEFT)
        
        dither_combo = ttk.Combobox(
            dither_frame,
            textvariable=self.dither_mode_var,
            values=list(self.dither_modes.keys()),
            state='readonly',
            width=12
        )
        dither_combo.pack(side=tk.LEFT)
        dither_combo.bind('<<ComboboxSelected>>', self._on_dither_mode_changed)
        
        # 右列：説明
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        desc_frame = ttk.LabelFrame(right_frame, text="設定説明", padding=5)
        desc_frame.pack(fill=tk.BOTH, expand=True)
        
        # 説明テキスト
        desc_text = tk.Text(
            desc_frame,
            height=6,
            width=30,
            wrap=tk.WORD,
            font=('Arial', 9),
            bg='#f8f8f8',
            state=tk.DISABLED
        )
        desc_text.pack(fill=tk.BOTH, expand=True)
        
        desc_content = """スケーリング:
• Lanczos: 最高品質、処理時間長
• Bicubic: 高品質、バランス良
• Bilinear: 標準品質、高速
• Neighbor: 最高速、品質低

ディザリング:
• Floyd-Steinberg: 推奨
• Sierra2: 細かい処理
• None: 高速処理"""
        
        desc_text.configure(state=tk.NORMAL)
        desc_text.insert(tk.END, desc_content)
        desc_text.configure(state=tk.DISABLED)
        
        self.scaling_desc_label = ttk.Label(desc_frame, text="", font=('Arial', 8), foreground='blue')
        self.scaling_desc_label.pack(anchor=tk.W, pady=(3, 0))
        
        self.dither_desc_label = ttk.Label(desc_frame, text="", font=('Arial', 8), foreground='blue')
        self.dither_desc_label.pack(anchor=tk.W)
        
    def _setup_info_tab(self, parent):
        """
        動画情報タブの内容
        """
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左列：動画情報
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        video_info_frame = ttk.LabelFrame(left_frame, text="動画情報", padding=5)
        video_info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.info_text = tk.Text(
            video_info_frame,
            height=6,
            width=30,
            wrap=tk.WORD,
            font=('Courier', 9),
            bg='#f8f8f8'
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.insert(tk.END, "動画ファイルを選択すると\\n情報を表示します")
        self.info_text.configure(state=tk.DISABLED)
        
        ttk.Button(
            left_frame,
            text="情報を更新",
            command=self._update_file_info
        ).pack(pady=(5, 0))
        
        # 右列：システム情報
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        sys_info_frame = ttk.LabelFrame(right_frame, text="システム情報", padding=5)
        sys_info_frame.pack(fill=tk.BOTH, expand=True)
        
        self.hwaccel_info_text = tk.Text(
            sys_info_frame,
            height=6,
            width=30,
            wrap=tk.WORD,
            font=('Courier', 8),
            bg='#f8f8f8'
        )
        self.hwaccel_info_text.pack(fill=tk.BOTH, expand=True)
        self.hwaccel_info_text.configure(state=tk.DISABLED)
        
    def _setup_compact_progress_section(self, parent):
        """
        コンパクトな進行状況セクション
        """
        # プログレスバーとステータス
        progress_info_frame = ttk.Frame(parent)
        progress_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # プログレスバー
        self.progress_bar = ttk.Progressbar(
            progress_info_frame,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 3))
        
        # ステータスラベル
        self.status_label = ttk.Label(
            progress_info_frame,
            textvariable=self.status_var,
            font=('Arial', 9)
        )
        self.status_label.pack(anchor=tk.W)
        
        # ログ表示（高さを制限）
        log_frame = ttk.LabelFrame(parent, text="ログ", padding=3)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_text_frame,
            height=4,  # 高さを4行に制限
            wrap=tk.WORD,
            font=('Courier', 8),
            bg='#f8f8f8',
            fg='#333333',
            state=tk.DISABLED
        )
        
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ログクリアボタン
        ttk.Button(
            log_frame,
            text="クリア",
            command=self._clear_log,
            width=8
        ).pack(side=tk.RIGHT, anchor=tk.SE, pady=(2, 0))
        
    def _update_file_info(self):
        """
        動画ファイルの情報を更新
        """
        input_file = self.input_file_var.get()
        if not input_file or not os.path.exists(input_file):
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "動画ファイルを選択すると\\n情報を表示します")
            self.info_text.configure(state=tk.DISABLED)
            return
            
        try:
            # より安全な動画情報取得
            info = self.ffmpeg_manager.get_video_info(input_file)
            
            if info:
                info_text = f"ファイル: {os.path.basename(input_file)}\\n"
                info_text += f"解像度: {info.get('width', 'N/A')}×{info.get('height', 'N/A')}\\n"
                info_text += f"継続時間: {info.get('duration', 'N/A')}秒\\n"
                info_text += f"FPS: {info.get('fps', 'N/A')}\\n"
                info_text += f"ビットレート: {info.get('bitrate', 'N/A')}\\n"
                info_text += f"コーデック: {info.get('codec', 'N/A')}"
            else:
                info_text = f"ファイル: {os.path.basename(input_file)}\\n動画情報の取得に失敗しました\\n\\n※ 実行ファイルの場合、管理者権限で\\n実行してください"
            
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, info_text)
            self.info_text.configure(state=tk.DISABLED)
            
        except Exception as e:
            error_text = f"ファイル: {os.path.basename(input_file) if input_file else 'N/A'}\\n"
            error_text += f"情報取得エラー:\\n{str(e)}\\n\\n"
            error_text += "※ 実行ファイルの場合、管理者権限で\\n実行してください"
            
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, error_text)
            self.info_text.configure(state=tk.DISABLED)
        
    def _update_hardware_accel_options(self):
        """
        利用可能なハードウェアアクセラレーションオプションを更新
        """
        try:
            supported_hwaccels = self.ffmpeg_manager.supported_hwaccels
            
            # システム情報を更新
            self.hwaccel_info_text.configure(state=tk.NORMAL)
            self.hwaccel_info_text.delete(1.0, tk.END)
            
            info_text = "【ハードウェアアクセラレーション】\\n"
            if supported_hwaccels:
                info_text += "利用可能:\\n"
                for hwaccel in supported_hwaccels:
                    info_text += f"• {hwaccel}\\n"
                    
                optimal_hwaccel = self.ffmpeg_manager.get_optimal_hardware_accel()
                if optimal_hwaccel:
                    info_text += f"\\n推奨: {optimal_hwaccel}\\n"
                else:
                    info_text += "\\n推奨: ソフトウェア処理\\n"
            else:
                info_text += "利用可能: なし\\n"
                info_text += "ソフトウェア処理のみ\\n"
                
            # FFmpegの情報も追加
            info_text += "\\n【FFmpeg情報】\\n"
            try:
                # FFmpegのバージョン情報を取得
                ffmpeg_version = self.ffmpeg_manager.get_ffmpeg_version()
                if ffmpeg_version:
                    info_text += f"バージョン: {ffmpeg_version[:20]}...\\n"
                else:
                    info_text += "FFmpeg未検出\\n"
            except:
                info_text += "FFmpeg未検出\\n"
                
            self.hwaccel_info_text.insert(tk.END, info_text)
            self.hwaccel_info_text.configure(state=tk.DISABLED)
            
        except Exception as e:
            # エラー時のフォールバック情報
            fallback_text = "【システム情報取得エラー】\\n"
            fallback_text += f"エラー: {str(e)}\\n\\n"
            fallback_text += "ハードウェアアクセラレーション: 不明\\n"
            fallback_text += "FFmpeg: 検出状況不明\\n\\n"
            fallback_text += "※ 詳細情報が必要な場合は\\n管理者権限で実行してください"
            
            self.hwaccel_info_text.configure(state=tk.NORMAL)
            self.hwaccel_info_text.delete(1.0, tk.END)
            self.hwaccel_info_text.insert(tk.END, fallback_text)
            self.hwaccel_info_text.configure(state=tk.DISABLED)
        
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
            
    def _auto_set_output_path(self, input_path: str):
        """
        入力ファイルパスから出力ファイルパスを自動設定
        """
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_hq.gif"
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
        
    def _on_advanced_mode_changed(self):
        """
        高品質モード切り替え時の処理
        """
        if self.use_advanced_mode_var.get():
            self.mode_desc_label.config(
                text="✓ より高品質なGIFを生成します（処理時間は約2倍）",
                foreground='blue'
            )
        else:
            self.mode_desc_label.config(
                text="標準的なGIF変換を行います",
                foreground='gray'
            )
            
    def _on_hardware_accel_toggled(self):
        """
        ハードウェアアクセラレーション有効/無効切り替え
        """
        if self.enable_hardware_accel_var.get():
            self.hwaccel_combo.config(state='readonly')
        else:
            self.hwaccel_combo.config(state='disabled')
            
    def _on_hardware_accel_changed(self, event=None):
        """
        ハードウェアアクセラレーション設定変更時の処理
        """
        hwaccel = self.hardware_accel_var.get()
        desc = self.hardware_accel_options.get(hwaccel, '')
        self.hwaccel_desc_label.config(text=desc)
        
    def _on_quality_changed(self, event=None):
        """
        品質設定変更時の処理
        """
        quality = self.quality_var.get()
        if quality in self.quality_presets:
            desc = self.quality_presets[quality]['description']
            self.quality_desc_label.config(text=desc)
            
    def _on_scaling_algorithm_changed(self, event=None):
        """
        スケーリングアルゴリズム変更時の処理
        """
        algorithm = self.scaling_algorithm_var.get()
        desc = self.scaling_algorithms.get(algorithm, '')
        self.scaling_desc_label.config(text=desc)
        
    def _on_dither_mode_changed(self, event=None):
        """
        ディザリング方式変更時の処理
        """
        dither = self.dither_mode_var.get()
        desc = self.dither_modes.get(dither, '')
        self.dither_desc_label.config(text=desc)
        
    def _on_width_changed(self, event=None):
        """
        幅変更時の処理（アスペクト比維持）
        """
        if not self.maintain_aspect_var.get() or not self.width_var.get() or not self.input_file_var.get():
            return
            
        try:
            new_width = int(self.width_var.get())
            # 元動画の情報を取得してアスペクト比を計算
            video_info = self.ffmpeg_manager.get_video_info(self.input_file_var.get())
            if video_info and 'streams' in video_info:
                for stream in video_info['streams']:
                    if stream.get('codec_type') == 'video':
                        orig_width = stream.get('width')
                        orig_height = stream.get('height')
                        if orig_width and orig_height:
                            aspect_ratio = orig_height / orig_width
                            new_height = int(new_width * aspect_ratio)
                            self.height_var.set(str(new_height))
                        break
        except (ValueError, TypeError):
            pass
            
    def _on_height_changed(self, event=None):
        """
        高さ変更時の処理（アスペクト比維持）
        """
        if not self.maintain_aspect_var.get() or not self.height_var.get() or not self.input_file_var.get():
            return
            
        try:
            new_height = int(self.height_var.get())
            # 元動画の情報を取得してアスペクト比を計算
            video_info = self.ffmpeg_manager.get_video_info(self.input_file_var.get())
            if video_info and 'streams' in video_info:
                for stream in video_info['streams']:
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
            self.start_time_entry.config(state=tk.NORMAL)
            self.duration_entry.config(state=tk.NORMAL)
        else:
            self.start_time_entry.config(state=tk.DISABLED)
            self.duration_entry.config(state=tk.DISABLED)
            
    def _update_file_info(self):
        """
        ファイル情報の更新
        """
        if not self.input_file_var.get() or not os.path.exists(self.input_file_var.get()):
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "有効な動画ファイルを\\n選択してください")
            self.info_text.configure(state=tk.DISABLED)
            return
            
        video_info = self.ffmpeg_manager.get_video_info(self.input_file_var.get())
        
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        if video_info:
            # 新しい形式のvideo_infoから情報を取得
            info_text = f"ファイル: {Path(self.input_file_var.get()).name}\n"
            
            # 解像度
            width = video_info.get('width', 'N/A')
            height = video_info.get('height', 'N/A')
            info_text += f"解像度: {width}×{height}\n"
            
            # 継続時間（既に文字列形式で整形済み）
            duration = video_info.get('duration', 'N/A')
            info_text += f"時間: {duration}秒\n"
            
            # FPS
            fps = video_info.get('fps', 'N/A')
            info_text += f"FPS: {fps}\n"
            
            # ビットレート（既に整形済み）
            bitrate = video_info.get('bitrate', 'N/A')
            info_text += f"ビットレート: {bitrate}\n"
            
            # コーデック
            codec = video_info.get('codec', 'N/A')
            info_text += f"コーデック: {codec}\n"
            
            # フォーマット
            format_name = video_info.get('format', 'N/A')
            info_text += f"フォーマット: {format_name}\n"
            
            # ファイルサイズ（既に整形済み）
            size = video_info.get('size', 'N/A')
            info_text += f"サイズ: {size}\n"
            
            # 推奨設定
            info_text += "\n📋 推奨設定:\n"
            if isinstance(width, int) and isinstance(height, int):
                # アスペクト比を保った推奨サイズ
                if width > 640:
                    new_width = 640
                    new_height = int(height * 640 / width)
                    info_text += f"• サイズ: {new_width}×{new_height}\n"
                else:
                    info_text += f"• サイズ: そのまま\n"
            
            if isinstance(fps, str) and fps != 'N/A':
                try:
                    fps_val = float(fps)
                    if fps_val > 15:
                        info_text += "• FPS: 15fps (推奨)\n"
                    else:
                        info_text += f"• FPS: {fps}fps\n"
                except:
                    pass
                    
        else:
            info_text = f"ファイル: {Path(self.input_file_var.get()).name}\n動画情報の取得に失敗しました\n\n※ 実行ファイルの場合、管理者権限で\n実行してください"
            
        self.info_text.insert(tk.END, info_text)
        self.info_text.configure(state=tk.DISABLED)
        
    def _start_conversion(self):
        """
        GIF変換開始
        """
        if self.get_processing_callback():
            messagebox.showwarning("警告", "他の処理が実行中です")
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
        self._append_log("=== 高品質GIF変換開始 ===")
        self._append_log(f"入力: {settings.input_file}")
        self._append_log(f"出力: {settings.output_file}")
        self._append_log(f"サイズ: {settings.width}×{settings.height}" if settings.width and settings.height else "サイズ: 未指定")
        self._append_log(f"FPS: {settings.fps}")
        self._append_log(f"品質: {settings.quality}")
        self._append_log(f"変換モード: {'2段階高品質' if settings.use_advanced_mode else '標準'}")
        self._append_log(f"ハードウェアアクセラレーション: {'有効' if settings.enable_hardware_accel else '無効'}")
        
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
            messagebox.showerror("エラー", "入力ファイルを選択してください")
            return False
            
        if not os.path.exists(self.input_file_var.get()):
            messagebox.showerror("エラー", "入力ファイルが見つかりません")
            return False
            
        if not self.output_file_var.get():
            messagebox.showerror("エラー", "出力ファイルを指定してください")
            return False
            
        # FPS検証
        if self.fps_var.get():
            try:
                fps = float(self.fps_var.get())
                if fps <= 0:
                    messagebox.showerror("エラー", "FPSは0より大きい値を指定してください")
                    return False
            except ValueError:
                messagebox.showerror("エラー", "FPSに無効な値が設定されています")
                return False
                
        # 時間範囲検証
        if self.use_time_range_var.get():
            try:
                if self.start_time_var.get():
                    start_time = float(self.start_time_var.get())
                    if start_time < 0:
                        messagebox.showerror("エラー", "開始時間は0以上を指定してください")
                        return False
                        
                if self.duration_var.get():
                    duration = float(self.duration_var.get())
                    if duration <= 0:
                        messagebox.showerror("エラー", "継続時間は0より大きい値を指定してください")
                        return False
            except ValueError:
                messagebox.showerror("エラー", "時間設定に無効な値が含まれています")
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
                quality=self.quality_var.get(),
                use_advanced_mode=self.use_advanced_mode_var.get(),
                enable_hardware_accel=self.enable_hardware_accel_var.get(),
                hardware_accel_type=self.hardware_accel_var.get(),
                scaling_algorithm=self.scaling_algorithm_var.get(),
                dither_mode=self.dither_mode_var.get()
            )
            
            # サイズ設定
            if self.width_var.get():
                settings.width = int(self.width_var.get())
            if self.height_var.get():
                settings.height = int(self.height_var.get())
                
            # FPS設定
            if self.fps_var.get():
                settings.fps = float(self.fps_var.get())
                
            # 時間範囲設定
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
            # 変換方式に応じて適切なメソッドを呼び出し
            if settings.use_advanced_mode:
                success = self.ffmpeg_manager.create_gif_advanced(
                    settings,
                    self._on_progress_update,
                    self._on_status_update,
                    self._on_log_update
                )
            else:
                success = self.ffmpeg_manager.create_gif(
                    settings,
                    self._on_progress_update,
                    self._on_status_update,
                    self._on_log_update
                )
            
            # メインスレッドで完了処理を実行
            self.frame.after(0, lambda: self._on_conversion_complete(success))
            
        except Exception as e:
            self.frame.after(0, lambda: self._on_conversion_error(str(e)))
            
    def _cancel_conversion(self):
        """
        GIF変換キャンセル
        """
        self.ffmpeg_manager.cancel_current_process()
        self._set_conversion_state(False)
        self._on_status_update("変換がキャンセルされました")
        
    def _set_conversion_state(self, is_converting: bool):
        """
        変換状態の設定
        """
        self.set_processing_callback(is_converting, self.ffmpeg_manager.current_process)
        
        if is_converting:
            self.start_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            
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
        if log_message.strip():
            self.frame.after(0, lambda: self._append_log(log_message))
            
    def _on_conversion_complete(self, success: bool):
        """
        GIF変換完了処理
        """
        self._set_conversion_state(False)
        self.progress_var.set(100 if success else 0)
        
        if success:
            self._append_log("=== 変換完了 ===")
            messagebox.showinfo("完了", f"GIF変換が完了しました\\n\\n出力: {self.output_file_var.get()}")
        else:
            self._append_log("=== 変換失敗 ===")
            messagebox.showerror("エラー", "GIF変換に失敗しました")
            
    def _on_conversion_error(self, error_message: str):
        """
        GIF変換エラー処理
        """
        self._set_conversion_state(False)
        self.progress_var.set(0)
        self._append_log(f"=== エラー ===\\n{error_message}")
        messagebox.showerror("エラー", f"変換中にエラーが発生しました:\\n{error_message}")
        
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
            initialvalue="高品質GIFプリセット"
        )
        
        if not preset_name:
            return
            
        # 現在の設定からプリセットを作成
        preset = GifConvertPreset(
            name=preset_name,
            fps=float(self.fps_var.get()) if self.fps_var.get() else 15.0,
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
            messagebox.showwarning("警告", "削除するプリセットを選択してください")
            return
            
        # 確認ダイアログ
        if messagebox.askyesno("削除確認", f"プリセット「{preset_name}」を削除しますか？"):
            settings_manager.delete_gif_preset(preset_name)
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
        self.log_text.insert(tk.END, f"{message}\\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.update_idletasks()
