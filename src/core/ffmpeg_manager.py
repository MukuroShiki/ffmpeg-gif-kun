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
try:
    # 通常の実行環境
    from utils.ffmpeg_downloader import ffmpeg_downloader
except ImportError:
    # PyInstallerでのバイナリ実行時
    try:
        import sys
        from pathlib import Path
        
        # モジュールパスを追加
        if hasattr(sys, '_MEIPASS'):
            # PyInstallerの一時ディレクトリ
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent
            
        sys.path.insert(0, str(base_path))
        from utils.ffmpeg_downloader import ffmpeg_downloader
    except ImportError as e:
        print(f"Warning: Could not import ffmpeg_downloader: {e}")
        ffmpeg_downloader = None


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
    # 時間範囲設定
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    # ハードウェアアクセラレーション設定
    hwaccel: Optional[str] = None
    # オーディオビットレート
    audio_bitrate: Optional[str] = None


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
    # 2段階変換用の新しい設定
    use_advanced_mode: bool = False
    enable_hardware_accel: bool = True
    hardware_accel_type: str = "auto"  # auto, cuda, qsv, videotoolbox, none
    scaling_algorithm: str = "lanczos"  # lanczos, bicubic, bilinear, neighbor
    dither_mode: str = "floyd_steinberg"  # none, floyd_steinberg, sierra2, sierra2_4a


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
        # FFmpegダウンローダーをインスタンス属性として設定
        self.ffmpeg_downloader = ffmpeg_downloader
        self.ffmpeg_path = self._find_ffmpeg()
        self.current_process: Optional[subprocess.Popen] = None
        self.is_processing = False
        self.supported_hwaccels = self._detect_hardware_acceleration()
        
    def _detect_hardware_acceleration(self) -> List[str]:
        """
        利用可能なハードウェアアクセラレーションを検出
        
        Returns:
            利用可能なハードウェアアクセラレーションのリスト
        """
        if not self.ffmpeg_path:
            return []
            
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-hwaccels'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                hwaccels = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Hardware acceleration'):
                        hwaccels.append(line)
                return hwaccels
            else:
                return []
                
        except Exception as e:
            print(f"Hardware acceleration detection failed: {e}")
            return []
    
    def get_optimal_hardware_accel(self) -> Optional[str]:
        """
        利用可能な最適なハードウェアアクセラレーションを取得
        
        Returns:
            最適なハードウェアアクセラレーション。利用できない場合はNone
        """
        # 優先順位：CUDA > QSV > VideoToolbox > VAAPI > D3D11VA
        preferred_order = ['cuda', 'qsv', 'videotoolbox', 'vaapi', 'd3d11va']
        
        for hwaccel in preferred_order:
            if hwaccel in self.supported_hwaccels:
                return hwaccel
                
        return None
        
    def _find_ffmpeg(self) -> Optional[str]:
        """
        システム内のFFmpegパスを検索
        
        Returns:
            FFmpegのパス。見つからない場合はNone
        """
        # まずFFmpegダウンローダーに確認
        if ffmpeg_downloader:
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
        if not ffmpeg_downloader:
            if status_callback:
                status_callback("FFmpegダウンローダーが利用できません")
            return False
            
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
            # ffprobeを使用するように変更
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            
            # ffprobeの存在確認
            try:
                subprocess.run([ffprobe_path, '-version'], 
                             capture_output=True, timeout=5, check=True)
                probe_cmd = ffprobe_path
            except:
                # ffprobeが無い場合はffmpegを使用
                probe_cmd = self.ffmpeg_path
                
            cmd = [
                probe_cmd,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                '-i', file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # より使いやすい形式に変換
                video_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break
                
                if video_stream:
                    info = {
                        'width': video_stream.get('width'),
                        'height': video_stream.get('height'),
                        'duration': float(data.get('format', {}).get('duration', 0)),
                        'fps': self._get_fps_from_stream(video_stream),
                        'bitrate': data.get('format', {}).get('bit_rate'),
                        'codec': video_stream.get('codec_name'),
                        'format': data.get('format', {}).get('format_name'),
                        'size': data.get('format', {}).get('size')
                    }
                    
                    # 値の整形
                    if info['bitrate']:
                        info['bitrate'] = f"{int(info['bitrate']) // 1000} kbps"
                    if info['size']:
                        size_mb = int(info['size']) / (1024 * 1024)
                        info['size'] = f"{size_mb:.1f} MB"
                    if info['duration']:
                        info['duration'] = f"{info['duration']:.1f}"
                        
                    return info
                else:
                    return None
            else:
                print(f"FFprobe error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("FFprobe timeout - file may be inaccessible")
            return None
        except PermissionError:
            print("Permission denied - try running as administrator")
            return None
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def _get_fps_from_stream(self, stream: Dict[str, Any]) -> Optional[str]:
        """
        動画ストリームからFPS情報を取得
        """
        try:
            # r_frame_rateを最優先
            if 'r_frame_rate' in stream:
                fps_str = stream['r_frame_rate']
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    if int(den) != 0:
                        fps = int(num) / int(den)
                        return f"{fps:.2f}"
            
            # avg_frame_rateを次に試す
            if 'avg_frame_rate' in stream:
                fps_str = stream['avg_frame_rate']
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    if int(den) != 0:
                        fps = int(num) / int(den)
                        return f"{fps:.2f}"
                        
            return None
        except:
            return None
    
    def get_ffmpeg_version(self) -> Optional[str]:
        """
        FFmpegのバージョン情報を取得
        
        Returns:
            FFmpegのバージョン情報。エラーの場合はNone
        """
        if not self.is_ffmpeg_available():
            return None
            
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 最初の行を取得（バージョン情報）
                first_line = result.stdout.split('\\n')[0]
                return first_line
            else:
                return None
                
        except Exception as e:
            print(f"Error getting FFmpeg version: {e}")
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
            
    def create_gif_advanced(
        self,
        settings: GifSettings,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        2段階方式による高品質GIF作成
        
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
            
            # 一時パレットファイルの作成
            import tempfile
            palette_file = None
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                palette_file = tmp.name
            
            try:
                # ステップ1: パレット生成
                if status_callback:
                    status_callback("ステップ1/2: 最適パレット生成中...")
                    
                success_palette = self._create_palette(
                    settings, 
                    palette_file, 
                    lambda p: progress_callback(p * 0.5) if progress_callback else None,
                    status_callback,
                    log_callback
                )
                
                if not success_palette:
                    if status_callback:
                        status_callback("パレット生成に失敗しました")
                    return False
                
                # ステップ2: GIF生成
                if status_callback:
                    status_callback("ステップ2/2: GIF生成中...")
                    
                success_gif = self._create_gif_with_palette(
                    settings,
                    palette_file,
                    lambda p: progress_callback(0.5 + p * 0.5) if progress_callback else None,
                    status_callback,
                    log_callback
                )
                
                if success_gif:
                    if status_callback:
                        status_callback("高品質GIF変換完了")
                    return True
                else:
                    if status_callback:
                        status_callback("GIF生成に失敗しました")
                    return False
                    
            finally:
                # 一時ファイルをクリーンアップ
                if palette_file and os.path.exists(palette_file):
                    try:
                        os.unlink(palette_file)
                    except Exception as e:
                        print(f"Failed to cleanup palette file: {e}")
                        
        except Exception as e:
            if status_callback:
                status_callback(f"エラー: {str(e)}")
            return False
            
        finally:
            self.is_processing = False
            self.current_process = None
    
    def _create_palette(
        self,
        settings: GifSettings,
        palette_file: str,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        パレット生成（第1段階）
        """
        try:
            # FFmpegコマンドを構築
            cmd = [self.ffmpeg_path]
            
            # ハードウェアアクセラレーション設定
            hwaccel = self._get_hardware_accel_for_settings(settings)
            if hwaccel:
                cmd.extend(['-hwaccel', hwaccel])
                if log_callback:
                    log_callback(f"ハードウェアアクセラレーション: {hwaccel}")
            
            # 時間範囲設定
            if settings.start_time is not None:
                cmd.extend(['-ss', self._format_time(settings.start_time)])
            if settings.duration is not None:
                cmd.extend(['-t', str(settings.duration)])
            elif settings.start_time is not None:
                # 終了時間の計算（duration優先、なければstart_timeから動画終了まで）
                video_duration = self._get_video_duration(settings.input_file)
                if video_duration:
                    duration = video_duration - settings.start_time
                    cmd.extend(['-t', str(duration)])
            
            # 入力ファイル
            cmd.extend(['-i', settings.input_file])
            
            # フィルター設定
            filters = []
            
            # FPS設定
            if settings.fps:
                filters.append(f'fps={settings.fps}')
            
            # 解像度設定
            if settings.width and settings.height:
                scale_filter = f'scale={settings.width}:{settings.height}:flags={settings.scaling_algorithm}'
                filters.append(scale_filter)
            elif settings.width:
                scale_filter = f'scale={settings.width}:-1:flags={settings.scaling_algorithm}'
                filters.append(scale_filter)
            elif settings.height:
                scale_filter = f'scale=-1:{settings.height}:flags={settings.scaling_algorithm}'
                filters.append(scale_filter)
            
            # RGB24フォーマット変換（パレット生成で重要）
            filters.append('format=rgb24')
            
            # パレット生成フィルター
            palette_colors = self._get_palette_colors_for_quality(settings.quality)
            filters.append(f'palettegen=max_colors={palette_colors}')
            
            # フィルター設定を適用
            if filters:
                cmd.extend(['-vf', ','.join(filters)])
            
            # 出力設定
            cmd.extend(['-y'])  # 上書き許可
            cmd.append(palette_file)
            
            if log_callback:
                log_callback(f"パレット生成コマンド: {' '.join(cmd)}")
            
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
            return return_code == 0
            
        except Exception as e:
            if log_callback:
                log_callback(f"パレット生成エラー: {str(e)}")
            return False
    
    def _create_gif_with_palette(
        self,
        settings: GifSettings,
        palette_file: str,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        パレットを使用してGIF生成（第2段階）
        """
        try:
            # FFmpegコマンドを構築
            cmd = [self.ffmpeg_path]
            
            # ハードウェアアクセラレーション設定
            hwaccel = self._get_hardware_accel_for_settings(settings)
            if hwaccel:
                cmd.extend(['-hwaccel', hwaccel])
            
            # 時間範囲設定（パレット生成と同じ）
            if settings.start_time is not None:
                cmd.extend(['-ss', self._format_time(settings.start_time)])
            if settings.duration is not None:
                cmd.extend(['-t', str(settings.duration)])
            elif settings.start_time is not None:
                video_duration = self._get_video_duration(settings.input_file)
                if video_duration:
                    duration = video_duration - settings.start_time
                    cmd.extend(['-t', str(duration)])
            
            # 入力ファイル（動画とパレット）
            cmd.extend(['-i', settings.input_file])
            cmd.extend(['-i', palette_file])
            
            # フィルター設定
            filters = []
            
            # FPS設定
            if settings.fps:
                filters.append(f'[0:v]fps={settings.fps}')
            else:
                filters.append('[0:v]')
                
            # 解像度設定
            if settings.width and settings.height:
                scale_filter = f'scale={settings.width}:{settings.height}:flags={settings.scaling_algorithm}'
                if filters[-1] != '[0:v]':
                    filters[-1] += f',{scale_filter}'
                else:
                    filters[-1] = f'[0:v]{scale_filter}'
            elif settings.width:
                scale_filter = f'scale={settings.width}:-1:flags={settings.scaling_algorithm}'
                if filters[-1] != '[0:v]':
                    filters[-1] += f',{scale_filter}'
                else:
                    filters[-1] = f'[0:v]{scale_filter}'
            elif settings.height:
                scale_filter = f'scale=-1:{settings.height}:flags={settings.scaling_algorithm}'
                if filters[-1] != '[0:v]':
                    filters[-1] += f',{scale_filter}'
                else:
                    filters[-1] = f'[0:v]{scale_filter}'
            
            # ストリーム出力ラベル
            filters[-1] += '[v]'
            
            # パレット使用フィルター
            filters.append(f'[v][1:v]paletteuse=dither={settings.dither_mode}')
            
            # フィルター設定を適用
            cmd.extend(['-filter_complex', ';'.join(filters)])
            
            # 出力設定
            cmd.extend(['-y'])  # 上書き許可
            cmd.append(settings.output_file)
            
            if log_callback:
                log_callback(f"GIF生成コマンド: {' '.join(cmd)}")
                log_callback(f"フィルター設定: {';'.join(filters)}")
            
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
            return return_code == 0
            
        except Exception as e:
            if log_callback:
                log_callback(f"GIF生成エラー: {str(e)}")
            return False
    
    def _get_hardware_accel_for_settings(self, settings: GifSettings) -> Optional[str]:
        """
        設定に基づいて使用するハードウェアアクセラレーションを決定
        """
        if not settings.enable_hardware_accel:
            return None
            
        if settings.hardware_accel_type == "auto":
            return self.get_optimal_hardware_accel()
        elif settings.hardware_accel_type == "none":
            return None
        elif settings.hardware_accel_type in self.supported_hwaccels:
            return settings.hardware_accel_type
        else:
            return None
    
    def _get_palette_colors_for_quality(self, quality: str) -> int:
        """
        品質設定に基づくパレット色数を取得
        """
        quality_settings = {
            'low': 64,
            'medium': 128,
            'high': 256
        }
        return quality_settings.get(quality, 128)
    
    def _format_time(self, seconds: float) -> str:
        """
        秒数をHH:MM:SS.mmm形式に変換
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
            
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
        if video_info:
            try:
                # 新しい形式のvideo_infoから取得
                if 'duration' in video_info:
                    duration_str = video_info['duration']
                    # "10.5"形式の文字列を浮動小数点に変換
                    return float(duration_str)
                # 古い形式（互換性のため）
                elif 'format' in video_info and 'duration' in video_info['format']:
                    return float(video_info['format']['duration'])
            except (KeyError, ValueError, TypeError):
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
        
    def encode_video_advanced(
        self,
        settings: EncodeSettings,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        高度な動画エンコード（正しいFFmpegコマンド形式に対応）
        正しい順序: ffmpeg [全体オプション] -i input [入力オプション] [出力オプション] output
        
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
            
            # FFmpegコマンドを正しい順序で構築
            cmd = [self.ffmpeg_path]
            
            # 1. グローバルオプション
            cmd.extend(['-y'])  # 上書き許可
            
            # 2. ハードウェアアクセラレーション（入力前に指定）
            if settings.hwaccel:
                if settings.hwaccel == 'auto':
                    cmd.extend(['-hwaccel', 'auto'])
                else:
                    cmd.extend(['-hwaccel', settings.hwaccel])
                if log_callback:
                    log_callback(f"ハードウェアアクセラレーション: {settings.hwaccel}")
            
            # 3. 入力ファイル関連のオプション（-i より前）
            # 時間範囲設定 (-ss は入力前に配置すると高速)
            if settings.start_time is not None:
                cmd.extend(['-ss', str(settings.start_time)])
            if settings.end_time is not None:
                cmd.extend(['-to', str(settings.end_time)])
                
            # 4. 入力ファイル指定
            cmd.extend(['-i', settings.input_file])
            
            # 5. 出力関連のオプション
            
            # ビデオコーデック設定
            cmd.extend(['-c:v', settings.video_codec])
            
            # ビデオ品質設定
            if settings.crf is not None and settings.crf > 0:
                cmd.extend(['-crf', str(settings.crf)])
            elif settings.bitrate:
                cmd.extend(['-b:v', settings.bitrate])
                
            # プリセット設定（対応するコーデックのみ）
            if settings.preset:
                supported_preset_codecs = [
                    'libx264', 'libx265', 
                    'h264_nvenc', 'h264_qsv', 'h264_amf',
                    'hevc_nvenc', 'hevc_qsv', 'hevc_amf'
                ]
                if settings.video_codec in supported_preset_codecs:
                    cmd.extend(['-preset', settings.preset])
                    
            # FPS設定
            if settings.fps:
                cmd.extend(['-r', str(settings.fps)])
                
            # 解像度設定
            if settings.width and settings.height:
                cmd.extend(['-s', f'{settings.width}x{settings.height}'])
                
            # オーディオコーデック設定
            if settings.audio_codec == 'copy':
                cmd.extend(['-c:a', 'copy'])
            else:
                cmd.extend(['-c:a', settings.audio_codec])
                
                # オーディオビットレート設定（copyの場合は不要）
                if settings.audio_bitrate:
                    cmd.extend(['-b:a', settings.audio_bitrate])
                else:
                    # デフォルトのオーディオビットレート
                    if settings.audio_codec == 'aac':
                        cmd.extend(['-b:a', '128k'])
                    elif settings.audio_codec in ['mp3', 'libmp3lame']:
                        cmd.extend(['-b:a', '192k'])
                    elif settings.audio_codec == 'libvorbis':
                        cmd.extend(['-q:a', '5'])  # VorbisはVBR品質指定
                    elif settings.audio_codec == 'libopus':
                        cmd.extend(['-b:a', '96k'])
                        
            # その他の出力オプション
            # ピクセルフォーマット指定（互換性向上）
            if settings.video_codec in ['libx264', 'h264_nvenc', 'h264_qsv', 'h264_amf']:
                cmd.extend(['-pix_fmt', 'yuv420p'])
            elif settings.video_codec in ['libx265', 'hevc_nvenc', 'hevc_qsv', 'hevc_amf']:
                cmd.extend(['-pix_fmt', 'yuv420p'])
                
            # 6. 出力ファイル（最後）
            cmd.append(settings.output_file)
            
            if status_callback:
                status_callback("エンコード開始...")
                
            # デバッグ用: 実行コマンドをログに出力
            if log_callback:
                log_callback(f"実行コマンド: {' '.join(cmd)}")
                
            # 動画の長さを取得（進行状況計算用）
            if settings.start_time is not None and settings.end_time is not None:
                # 時間範囲指定の場合
                duration = settings.end_time - settings.start_time
            else:
                duration = self._get_video_duration(settings.input_file)
                if settings.start_time is not None and duration:
                    duration = duration - settings.start_time
                    
            # プロセス実行
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # stderrもstdoutにリダイレクト
                text=True,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
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
            if log_callback:
                log_callback(f"例外エラー: {str(e)}")
            return False
            
        finally:
            self.is_processing = False
            self.current_process = None
