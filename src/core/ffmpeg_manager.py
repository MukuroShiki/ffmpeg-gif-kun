"""
FFmpeg GUI Kun - FFmpegマネージャー

FFmpegコマンドの実行と管理を行うクラス
"""

import subprocess
import os
import sys
import threading
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass

# FFmpegダウンローダーのインポート
from utils.ffmpeg_downloader import ffmpeg_downloader


@dataclass
class EncodeSettings:
    """エンコード設定を格納するデータクラス"""
    input_file: str
    output_file: str
    output_format: str
    video_codec: str
    audio_codec: str
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    crf: Optional[int] = None
    preset: Optional[str] = None
    bitrate: Optional[str] = None


@dataclass
class GifSettings:
    """GIF変換設定を格納するデータクラス"""
    input_file: str
    output_file: str
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    start_time: Optional[float] = None
    duration: Optional[float] = None
    quality: str = "medium"  # low, medium, high


class FFmpegManager:
    """
    FFmpegの実行と管理を行うクラス
    """
    
    # サポートされている出力フォーマット
    SUPPORTED_FORMATS = {
        'mp4': 'MP4 (H.264)',
        'avi': 'AVI',
        'mov': 'MOV (QuickTime)',
        'mkv': 'MKV (Matroska)',
        'webm': 'WebM',
        'wmv': 'WMV',
        'flv': 'FLV',
        'mpg': 'MPEG',
        'm4v': 'M4V',
    }
    
    # ビデオコーデック
    VIDEO_CODECS = {
        'libx264': 'H.264 (x264) - 汎用性が高い',
        'libx265': 'H.265 (x265) - 高圧縮',
        'libvpx': 'VP8 - WebM用',
        'libvpx-vp9': 'VP9 - WebM用（高効率）',
        'mpeg4': 'MPEG-4 - 古い形式',
        'copy': 'コピー（無変換）',
    }
    
    # オーディオコーデック
    AUDIO_CODECS = {
        'aac': 'AAC - 汎用性が高い',
        'mp3': 'MP3',
        'libmp3lame': 'MP3 (LAME)',
        'libvorbis': 'Vorbis - WebM用',
        'libopus': 'Opus - 高効率',
        'copy': 'コピー（無変換）',
    }
    
    # エンコードプリセット
    PRESETS = {
        'ultrafast': '超高速（低品質）',
        'superfast': 'かなり高速',
        'veryfast': 'とても高速',
        'faster': '高速',
        'fast': '普通より高速',
        'medium': '標準',
        'slow': '低速（高品質）',
        'slower': 'かなり低速',
        'veryslow': 'とても低速（最高品質）',
    }
    
    def __init__(self):
        """
        FFmpegManagerの初期化
        """
        self.ffmpeg_path = self._find_ffmpeg()
        self.current_process: Optional[subprocess.Popen] = None
        self.is_processing = False
        
    def _find_ffmpeg(self) -> Optional[str]:
        """
        システム内のFFmpegパスを検索
        
        Returns:
            FFmpegのパス。見つからない場合はNone
        """
        # まずFFmpegダウンローダーに確認
        ffmpeg_path = ffmpeg_downloader.get_ffmpeg_path()
        if ffmpeg_path:
            return ffmpeg_path
            
        # 従来の検索も継続
        possible_paths = [
            'ffmpeg',  # PATH環境変数内
            'ffmpeg.exe',  # Windows
            '/usr/bin/ffmpeg',  # Linux
            '/usr/local/bin/ffmpeg',  # macOS (Homebrew)
            './ffmpeg',  # 同一ディレクトリ
            './ffmpeg.exe',  # 同一ディレクトリ (Windows)
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except (subprocess.SubprocessError, FileNotFoundError, OSError):
                continue
                
        return None
        
    def is_ffmpeg_available(self) -> bool:
        """
        FFmpegが利用可能かチェック
        
        Returns:
            利用可能な場合True
        """
        return self.ffmpeg_path is not None
        
    def download_ffmpeg_if_needed(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        必要に応じてFFmpegをダウンロード
        
        Args:
            progress_callback: 進行状況コールバック (現在, 総計)
            status_callback: ステータスメッセージコールバック
            
        Returns:
            FFmpegが利用可能になった場合True
        """
        if self.is_ffmpeg_available():
            return True
            
        # FFmpegをダウンロード
        success = ffmpeg_downloader.download_ffmpeg(progress_callback, status_callback)
        
        if success:
            # パスを再取得
            self.ffmpeg_path = self._find_ffmpeg()
            return self.is_ffmpeg_available()
            
        return False
        
    def get_video_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        動画ファイルの情報を取得
        
        Args:
            file_path: 動画ファイルのパス
            
        Returns:
            動画情報の辞書。エラーの場合はNone
        """
        if not self.is_ffmpeg_available():
            return None
            
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', file_path,
                '-hide_banner',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                '-v', 'quiet'
            ]
            
            # ffprobeがある場合はそちらを使用
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            try:
                subprocess.run([ffprobe_path, '-version'], capture_output=True, timeout=2)
                cmd[0] = ffprobe_path
            except:
                pass
                
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"FFmpeg error: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
            
    def encode_video(
        self,
        settings: EncodeSettings,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        動画をエンコード
        
        Args:
            settings: エンコード設定
            progress_callback: 進行状況コールバック（0.0-1.0）
            status_callback: ステータスメッセージコールバック
            log_callback: ログメッセージコールバック（FFmpegの生ログ）
            
        Returns:
            成功した場合True
        """
        if not self.is_ffmpeg_available():
            if status_callback:
                status_callback("FFmpegが利用できません")
            return False
            
        if self.is_processing:
            if status_callback:
                status_callback("他の処理が実行中です")
            return False
            
        try:
            self.is_processing = True
            
            # FFmpegコマンドを構築
            cmd = [self.ffmpeg_path]
            cmd.extend(['-i', settings.input_file])
            
            # 出力設定
            if settings.video_codec != 'copy':
                cmd.extend(['-c:v', settings.video_codec])
                
                # 解像度設定
                if settings.width and settings.height:
                    cmd.extend(['-s', f'{settings.width}x{settings.height}'])
                    
                # FPS設定
                if settings.fps:
                    cmd.extend(['-r', str(settings.fps)])
                    
                # 品質設定
                if settings.crf is not None:
                    cmd.extend(['-crf', str(settings.crf)])
                elif settings.bitrate:
                    cmd.extend(['-b:v', settings.bitrate])
                    
                # プリセット設定
                if settings.preset and settings.video_codec in ['libx264', 'libx265']:
                    cmd.extend(['-preset', settings.preset])
                    
            else:
                cmd.extend(['-c:v', 'copy'])
                
            # オーディオ設定
            cmd.extend(['-c:a', settings.audio_codec])
            
            # 出力ファイル
            cmd.extend(['-y'])  # 上書き許可
            cmd.append(settings.output_file)
            
            # 出力ファイル
            cmd.extend(['-y'])  # 上書き許可
            cmd.append(settings.output_file)
            
            if status_callback:
                status_callback("エンコード開始...")
                
            # デバッグ用: 実行コマンドをログに出力
            if log_callback:
                log_callback(f"実行コマンド: {' '.join(cmd)}")
                
            # 動画の長さを取得（進行状況計算用）
            duration = self._get_video_duration(settings.input_file)
            
            # プロセス実行
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # 進行状況を監視
            self._monitor_progress(
                self.current_process,
                duration,
                progress_callback,
                status_callback,
                log_callback
            )
            
            # 完了待ち
            return_code = self.current_process.wait()
            
            if return_code == 0:
                if status_callback:
                    status_callback("エンコード完了")
                return True
            else:
                if status_callback:
                    status_callback("エンコードエラー")
                return False
                
        except Exception as e:
            if status_callback:
                status_callback(f"エラー: {str(e)}")
            return False
            
        finally:
            self.is_processing = False
            self.current_process = None
            
    def create_gif(
        self,
        settings: GifSettings,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        動画からGIFを作成
        
        Args:
            settings: GIF変換設定
            progress_callback: 進行状況コールバック（0.0-1.0）
            status_callback: ステータスメッセージコールバック
            log_callback: ログメッセージコールバック（FFmpegの生ログ）
            
        Returns:
            成功した場合True
        """
        if not self.is_ffmpeg_available():
            if status_callback:
                status_callback("FFmpegが利用できません")
            return False
            
        if self.is_processing:
            if status_callback:
                status_callback("他の処理が実行中です")
            return False
            
        try:
            self.is_processing = True
            
            # 品質設定マッピング
            quality_settings = {
                'low': {'colors': '64', 'dither': 'none'},
                'medium': {'colors': '128', 'dither': 'floyd_steinberg'},
                'high': {'colors': '256', 'dither': 'floyd_steinberg'}
            }
            
            quality_config = quality_settings.get(settings.quality, quality_settings['medium'])
            
            # FFmpegコマンドを構築
            cmd = [self.ffmpeg_path]
            cmd.extend(['-i', settings.input_file])
            
            # 開始時間と長さ
            if settings.start_time is not None:
                cmd.extend(['-ss', str(settings.start_time)])
            if settings.duration is not None:
                cmd.extend(['-t', str(settings.duration)])
                
            # フィルター設定
            filters = []
            
            # 解像度設定（明示的に指定）
            if settings.width and settings.height:
                filters.append(f'scale={settings.width}:{settings.height}:flags=lanczos')
            elif settings.width:
                filters.append(f'scale={settings.width}:-1:flags=lanczos')
            elif settings.height:
                filters.append(f'scale=-1:{settings.height}:flags=lanczos')
                
            # FPS設定
            if settings.fps:
                filters.append(f'fps={settings.fps}')
                
            # パレット生成とディザリング
            palette_filter = f'palettegen=max_colors={quality_config["colors"]}'
            use_filter = f'paletteuse=dither={quality_config["dither"]}'
            
            # フィルターチェインを正しく構築
            if filters:
                # フィルター適用済み映像に対してパレット処理
                base_filters = ','.join(filters)
                filter_complex = f'[0:v]{base_filters}[v];[v]{palette_filter}[p];[v][p]{use_filter}'
            else:
                # フィルターなしの場合は元映像に対してパレット処理
                filter_complex = f'[0:v]{palette_filter}[p];[0:v][p]{use_filter}'
                
            cmd.extend(['-filter_complex', filter_complex])
            
            # 出力設定
            cmd.extend(['-y'])  # 上書き許可
            cmd.append(settings.output_file)
            
            if status_callback:
                status_callback("GIF変換開始...")
                
            # デバッグ用: 実行コマンドをログに出力
            if log_callback:
                log_callback(f"実行コマンド: {' '.join(cmd)}")
                log_callback(f"フィルター設定: {filter_complex}")
                
            if status_callback:
                status_callback("GIF変換開始...")
                
            # 動画の長さを取得
            duration = settings.duration if settings.duration else self._get_video_duration(settings.input_file)
            
            # プロセス実行
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # 進行状況を監視
            self._monitor_progress(
                self.current_process,
                duration,
                progress_callback,
                status_callback,
                log_callback
            )
            
            # 完了待ち
            return_code = self.current_process.wait()
            
            if return_code == 0:
                if status_callback:
                    status_callback("GIF変換完了")
                return True
            else:
                if status_callback:
                    status_callback("GIF変換エラー")
                return False
                
        except Exception as e:
            if status_callback:
                status_callback(f"エラー: {str(e)}")
            return False
            
        finally:
            self.is_processing = False
            self.current_process = None
            
    def cancel_current_process(self):
        """
        現在実行中のプロセスをキャンセル
        """
        if self.current_process and self.is_processing:
            try:
                self.current_process.terminate()
                # Windowsの場合、強制終了が必要な場合がある
                if os.name == 'nt':
                    import signal
                    try:
                        self.current_process.send_signal(signal.CTRL_BREAK_EVENT)
                    except:
                        self.current_process.kill()
            except Exception as e:
                print(f"Error canceling process: {e}")
                
    def _get_video_duration(self, file_path: str) -> Optional[float]:
        """
        動画の長さを秒で取得
        
        Args:
            file_path: 動画ファイルのパス
            
        Returns:
            長さ（秒）。取得できない場合はNone
        """
        video_info = self.get_video_info(file_path)
        if video_info and 'format' in video_info:
            try:
                return float(video_info['format']['duration'])
            except (KeyError, ValueError):
                pass
        return None
        
    def _monitor_progress(
        self,
        process: subprocess.Popen,
        total_duration: Optional[float],
        progress_callback: Optional[Callable[[float], None]],
        status_callback: Optional[Callable[[str], None]],
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        FFmpegプロセスの進行状況を監視
        
        Args:
            process: FFmpegプロセス
            total_duration: 動画の総時間（秒）
            progress_callback: 進行状況コールバック
            status_callback: ステータスコールバック
        """
        def monitor():
            # 正規表現パターン
            time_pattern = re.compile(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
            fps_pattern = re.compile(r'fps=\s*(\d+\.?\d*)')
            bitrate_pattern = re.compile(r'bitrate=\s*(\d+\.?\d*\w*)')
            speed_pattern = re.compile(r'speed=\s*(\d+\.?\d*x)')
            
            while process.poll() is None:
                try:
                    line = process.stderr.readline()
                    if line:
                        # 生ログをコールバック
                        if log_callback:
                            log_callback(line.strip())
                        
                        # 詳細な進行状況情報を解析
                        time_match = time_pattern.search(line)
                        fps_match = fps_pattern.search(line)
                        bitrate_match = bitrate_pattern.search(line)
                        speed_match = speed_pattern.search(line)
                        
                        if time_match and total_duration:
                            hours, minutes, seconds, centiseconds = time_match.groups()
                            current_time = (
                                int(hours) * 3600 +
                                int(minutes) * 60 +
                                int(seconds) +
                                int(centiseconds) / 100
                            )
                            progress = min(current_time / total_duration, 1.0)
                            
                            # プログレスコールバック
                            if progress_callback:
                                progress_callback(progress)
                            
                            # 詳細ステータス情報
                            if status_callback:
                                status_parts = []
                                status_parts.append(f"進行: {progress*100:.1f}%")
                                status_parts.append(f"時間: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
                                
                                if fps_match:
                                    fps = fps_match.group(1)
                                    status_parts.append(f"FPS: {fps}")
                                
                                if bitrate_match:
                                    bitrate = bitrate_match.group(1)
                                    status_parts.append(f"ビットレート: {bitrate}")
                                
                                if speed_match:
                                    speed = speed_match.group(1)
                                    status_parts.append(f"速度: {speed}")
                                
                                # 推定残り時間
                                if progress > 0.01:  # 1%以上進行した場合
                                    elapsed_time = current_time
                                    estimated_total = elapsed_time / progress
                                    remaining = estimated_total - elapsed_time
                                    remaining_minutes = int(remaining // 60)
                                    remaining_seconds = int(remaining % 60)
                                    status_parts.append(f"残り時間: {remaining_minutes:02d}:{remaining_seconds:02d}")
                                
                                status_callback(" | ".join(status_parts))
                        
                        # エラーメッセージの検出
                        elif 'error' in line.lower() or 'failed' in line.lower():
                            if status_callback:
                                status_callback(f"エラー: {line.strip()}")
                            
                except Exception as e:
                    if status_callback:
                        status_callback(f"監視エラー: {str(e)}")
                    break
        
        # 監視スレッドを開始
        import threading
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
                    
    def download_ffmpeg_if_needed(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        必要に応じてFFmpegをダウンロード
        
        Args:
            progress_callback: 進行状況コールバック (現在, 総計)
            status_callback: ステータスメッセージコールバック
            
        Returns:
            FFmpegが利用可能になった場合True
        """
        if self.is_ffmpeg_available():
            return True
            
        # FFmpegをダウンロード
        success = ffmpeg_downloader.download_ffmpeg(progress_callback, status_callback)
        
        if success:
            # パスを再取得
            self.ffmpeg_path = self._find_ffmpeg()
            return self.is_ffmpeg_available()
            
        return False
