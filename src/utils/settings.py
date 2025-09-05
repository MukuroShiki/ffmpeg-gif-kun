"""
FFmpeg GUI Kun - 設定管理

アプリケーション設定の保存・読み込み機能を提供する
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class VideoEncodePreset:
    """動画エンコードプリセット"""
    name: str
    format: str = 'mp4'
    video_codec: str = 'libx264'
    audio_codec: str = 'aac'
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    crf: Optional[int] = 23
    preset: str = 'medium'
    use_crf: bool = True
    bitrate: Optional[str] = None


@dataclass
class GifConvertPreset:
    """GIF変換プリセット"""
    name: str
    width: Optional[int] = None
    height: Optional[int] = None
    fps: float = 10.0
    quality: str = 'medium'
    maintain_aspect: bool = True


@dataclass
class AppSettings:
    """アプリケーション設定"""
    last_input_dir: str = ""
    last_output_dir: str = ""
    remember_directories: bool = True
    show_tooltips: bool = True
    auto_open_output_folder: bool = True
    theme: str = "system"  # system, light, dark


class SettingsManager:
    """
    設定管理クラス
    """
    
    def __init__(self):
        self.settings_dir = Path.home() / ".ffmpeg_gui_kun"
        self.settings_file = self.settings_dir / "settings.json"
        self.presets_file = self.settings_dir / "presets.json"
        
        # ディレクトリを作成
        self.settings_dir.mkdir(exist_ok=True)
        
        # デフォルト設定とプリセットを初期化
        self.app_settings = AppSettings()
        self.video_presets = self._get_default_video_presets()
        self.gif_presets = self._get_default_gif_presets()
        
        # 設定を読み込み
        self.load_settings()
        self.load_presets()
        
    def _get_default_video_presets(self) -> Dict[str, VideoEncodePreset]:
        """デフォルトの動画エンコードプリセット"""
        return {
            "高品質 (H.264)": VideoEncodePreset(
                name="高品質 (H.264)",
                format="mp4",
                video_codec="libx264",
                audio_codec="aac",
                crf=18,
                preset="slow",
                use_crf=True
            ),
            "標準品質 (H.264)": VideoEncodePreset(
                name="標準品質 (H.264)",
                format="mp4",
                video_codec="libx264",
                audio_codec="aac",
                crf=23,
                preset="medium",
                use_crf=True
            ),
            "高速変換 (H.264)": VideoEncodePreset(
                name="高速変換 (H.264)",
                format="mp4",
                video_codec="libx264",
                audio_codec="aac",
                crf=25,
                preset="fast",
                use_crf=True
            ),
            "高効率 (H.265)": VideoEncodePreset(
                name="高効率 (H.265)",
                format="mp4",
                video_codec="libx265",
                audio_codec="aac",
                crf=25,
                preset="medium",
                use_crf=True
            ),
            "WebM (VP9)": VideoEncodePreset(
                name="WebM (VP9)",
                format="webm",
                video_codec="libvpx-vp9",
                audio_codec="libopus",
                crf=30,
                preset="medium",
                use_crf=True
            ),
            "720p標準": VideoEncodePreset(
                name="720p標準",
                format="mp4",
                video_codec="libx264",
                audio_codec="aac",
                width=1280,
                height=720,
                crf=23,
                preset="medium",
                use_crf=True
            ),
            "1080p高品質": VideoEncodePreset(
                name="1080p高品質",
                format="mp4",
                video_codec="libx264",
                audio_codec="aac",
                width=1920,
                height=1080,
                crf=20,
                preset="slow",
                use_crf=True
            )
        }
        
    def _get_default_gif_presets(self) -> Dict[str, GifConvertPreset]:
        """デフォルトのGIF変換プリセット"""
        return {
            "ウェブ用小サイズ": GifConvertPreset(
                name="ウェブ用小サイズ",
                width=320,
                height=240,
                fps=8.0,
                quality="low"
            ),
            "SNS用標準": GifConvertPreset(
                name="SNS用標準",
                width=480,
                height=360,
                fps=12.0,
                quality="medium"
            ),
            "高品質": GifConvertPreset(
                name="高品質",
                width=640,
                height=480,
                fps=15.0,
                quality="high"
            ),
            "Twitter用": GifConvertPreset(
                name="Twitter用",
                width=480,
                height=270,
                fps=10.0,
                quality="medium"
            ),
            "Discord用": GifConvertPreset(
                name="Discord用",
                width=400,
                height=300,
                fps=10.0,
                quality="medium"
            )
        }
        
    def load_settings(self):
        """設定を読み込み"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 辞書からAppSettingsオブジェクトを作成
                    self.app_settings = AppSettings(**data)
        except Exception as e:
            print(f"設定の読み込みに失敗しました: {e}")
            self.app_settings = AppSettings()
            
    def save_settings(self):
        """設定を保存"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.app_settings), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"設定の保存に失敗しました: {e}")
            
    def load_presets(self):
        """プリセットを読み込み"""
        try:
            if self.presets_file.exists():
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 動画プリセット
                    if 'video_presets' in data:
                        video_data = {}
                        for name, preset_data in data['video_presets'].items():
                            video_data[name] = VideoEncodePreset(**preset_data)
                        # デフォルトプリセットとマージ
                        self.video_presets.update(video_data)
                        
                    # GIFプリセット
                    if 'gif_presets' in data:
                        gif_data = {}
                        for name, preset_data in data['gif_presets'].items():
                            gif_data[name] = GifConvertPreset(**preset_data)
                        # デフォルトプリセットとマージ
                        self.gif_presets.update(gif_data)
                        
        except Exception as e:
            print(f"プリセットの読み込みに失敗しました: {e}")
            
    def save_presets(self):
        """プリセットを保存"""
        try:
            data = {
                'video_presets': {name: asdict(preset) for name, preset in self.video_presets.items()},
                'gif_presets': {name: asdict(preset) for name, preset in self.gif_presets.items()}
            }
            
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"プリセットの保存に失敗しました: {e}")
            
    def add_video_preset(self, preset: VideoEncodePreset):
        """動画エンコードプリセットを追加"""
        self.video_presets[preset.name] = preset
        self.save_presets()
        
    def add_gif_preset(self, preset: GifConvertPreset):
        """GIF変換プリセットを追加"""
        self.gif_presets[preset.name] = preset
        self.save_presets()
        
    def delete_video_preset(self, name: str):
        """動画エンコードプリセットを削除"""
        if name in self.video_presets:
            del self.video_presets[name]
            self.save_presets()
            
    def delete_gif_preset(self, name: str):
        """GIF変換プリセットを削除"""
        if name in self.gif_presets:
            del self.gif_presets[name]
            self.save_presets()
            
    def get_video_preset_names(self) -> list:
        """動画エンコードプリセット名のリストを取得"""
        return list(self.video_presets.keys())
        
    def get_gif_preset_names(self) -> list:
        """GIF変換プリセット名のリストを取得"""
        return list(self.gif_presets.keys())
        
    def get_video_preset(self, name: str) -> Optional[VideoEncodePreset]:
        """動画エンコードプリセットを取得"""
        return self.video_presets.get(name)
        
    def get_gif_preset(self, name: str) -> Optional[GifConvertPreset]:
        """GIF変換プリセットを取得"""
        return self.gif_presets.get(name)
        
    def update_last_directories(self, input_dir: str = None, output_dir: str = None):
        """最後に使用したディレクトリを更新"""
        if self.app_settings.remember_directories:
            if input_dir:
                self.app_settings.last_input_dir = input_dir
            if output_dir:
                self.app_settings.last_output_dir = output_dir
            self.save_settings()


# グローバル設定管理インスタンス
settings_manager = SettingsManager()
