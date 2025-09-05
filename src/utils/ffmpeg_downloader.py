"""
FFmpeg GUI Kun - FFmpeg自動ダウンロード・管理

FFmpegが環境にインストールされていない場合の自動ダウンロード機能
"""

import os
import sys
import zipfile
import tempfile
import shutil
import platform
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from typing import Optional, Callable
import json


class FFmpegDownloader:
    """
    FFmpegの自動ダウンロード・管理クラス
    """
    
    # FFmpegダウンロードURL (Windows用)
    FFMPEG_URLS = {
        'windows': {
            'url': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
            'extract_path': 'ffmpeg-*-essentials_build/bin/ffmpeg.exe'
        },
        'linux': {
            # Linuxはstatic buildを使用
            'url': 'https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz',
            'extract_path': 'ffmpeg-*-static/ffmpeg'
        }
    }
    
    def __init__(self, base_dir: Path = None):
        """
        FFmpegDownloaderの初期化
        
        Args:
            base_dir: FFmpegを保存するベースディレクトリ
        """
        if base_dir is None:
            # PyInstallerでの実行時を考慮したパス設定
            if hasattr(sys, '_MEIPASS'):
                # PyInstallerのバイナリ実行時：実行ファイルと同じディレクトリ
                base_dir = Path(sys.executable).parent
            else:
                # 開発環境：アプリケーションのルートディレクトリ
                base_dir = Path(__file__).parent.parent.parent
            
        self.base_dir = Path(base_dir)
        self.ffmpeg_dir = self.base_dir / "ffmpeg_bin"
        self.system_name = platform.system().lower()
        
        # WindowsとLinuxのみサポート（macOSはHomebrew推奨）
        self.supported_systems = ['windows', 'linux']
        
    def get_ffmpeg_path(self) -> Optional[str]:
        """
        FFmpegのパスを取得
        
        Returns:
            FFmpegのパス。見つからない場合はNone
        """
        # まずシステムのPATHから確認
        system_path = self._find_system_ffmpeg()
        if system_path:
            return system_path
            
        # ローカルディレクトリから確認
        local_path = self._find_local_ffmpeg()
        if local_path:
            return str(local_path)
            
        return None
        
    def _find_system_ffmpeg(self) -> Optional[str]:
        """
        システムにインストールされたFFmpegを検索
        """
        try:
            if self.system_name == 'windows':
                result = subprocess.run(['where', 'ffmpeg'], capture_output=True, text=True)
            else:
                result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
                
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
            
        return None
        
    def _find_local_ffmpeg(self) -> Optional[Path]:
        """
        ローカルディレクトリのFFmpegを検索
        """
        if self.system_name == 'windows':
            ffmpeg_exe = self.ffmpeg_dir / "ffmpeg.exe"
        else:
            ffmpeg_exe = self.ffmpeg_dir / "ffmpeg"
            
        if ffmpeg_exe.exists():
            return ffmpeg_exe
            
        # サブディレクトリも検索
        for exe_file in self.ffmpeg_dir.rglob("ffmpeg*"):
            if exe_file.is_file() and exe_file.suffix in ['', '.exe']:
                return exe_file
                
        return None
        
    def is_ffmpeg_available(self) -> bool:
        """
        FFmpegが利用可能かチェック
        """
        ffmpeg_path = self.get_ffmpeg_path()
        if not ffmpeg_path:
            return False
            
        try:
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def download_ffmpeg(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        FFmpegをダウンロード
        
        Args:
            progress_callback: 進行状況コールバック (現在, 総計)
            status_callback: ステータスメッセージコールバック
            
        Returns:
            成功した場合True
        """
        if self.system_name not in self.supported_systems:
            if status_callback:
                status_callback(f"{self.system_name}は自動ダウンロードをサポートしていません")
            return False
            
        try:
            if status_callback:
                status_callback("FFmpegをダウンロード中...")
                
            # ダウンロードURL取得
            download_info = self.FFMPEG_URLS[self.system_name]
            
            # 一時ディレクトリでダウンロード
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                archive_path = temp_path / "ffmpeg_archive"
                
                # ダウンロード
                if not self._download_file(
                    download_info['url'], 
                    archive_path, 
                    progress_callback, 
                    status_callback
                ):
                    return False
                    
                # 展開
                if status_callback:
                    status_callback("FFmpegを展開中...")
                    
                if not self._extract_archive(
                    archive_path, 
                    temp_path, 
                    download_info['extract_path']
                ):
                    if status_callback:
                        status_callback("FFmpegの展開に失敗しました")
                    return False
                    
                if status_callback:
                    status_callback("FFmpegのセットアップ完了")
                    
            return True
            
        except Exception as e:
            if status_callback:
                status_callback(f"FFmpegダウンロードエラー: {str(e)}")
            return False
            
    def _download_file(
        self,
        url: str,
        output_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        ファイルをダウンロード
        """
        try:
            # User-Agentを設定してリクエスト
            request = Request(url, headers={
                'User-Agent': 'FFmpeg-GUI-Kun/1.0'
            })
            
            with urlopen(request) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                
                if status_callback:
                    if total_size > 0:
                        status_callback(f"ダウンロード中... (0/{total_size // 1024 // 1024}MB)")
                    else:
                        status_callback("ダウンロード中...")
                        
                downloaded_size = 0
                chunk_size = 8192
                
                with open(output_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                            
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded_size, total_size)
                            
                        if status_callback and total_size > 0:
                            mb_downloaded = downloaded_size // 1024 // 1024
                            mb_total = total_size // 1024 // 1024
                            status_callback(f"ダウンロード中... ({mb_downloaded}/{mb_total}MB)")
                            
            return True
            
        except Exception as e:
            print(f"Download error: {e}")
            return False
            
    def _extract_archive(self, archive_path: Path, extract_dir: Path, target_pattern: str) -> bool:
        """
        アーカイブを展開してFFmpegを取得
        """
        try:
            # ファイル形式を判定
            if archive_path.suffix == '.zip' or self._is_zip_file(archive_path):
                return self._extract_zip(archive_path, extract_dir, target_pattern)
            elif archive_path.suffix in ['.tar', '.tar.xz', '.tar.gz']:
                return self._extract_tar(archive_path, extract_dir, target_pattern)
            else:
                # バイナリファイルとして直接コピー
                return self._copy_binary(archive_path, target_pattern)
                
        except Exception as e:
            print(f"Extract error: {e}")
            return False
            
    def _is_zip_file(self, file_path: Path) -> bool:
        """
        ZIPファイルかどうか判定
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                return True
        except:
            return False
            
    def _extract_zip(self, archive_path: Path, extract_dir: Path, target_pattern: str) -> bool:
        """
        ZIPファイルを展開
        """
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                # すべて展開
                zf.extractall(extract_dir)
                
                # FFmpegバイナリを検索
                return self._find_and_copy_ffmpeg(extract_dir, target_pattern)
                
        except Exception as e:
            print(f"ZIP extract error: {e}")
            return False
            
    def _extract_tar(self, archive_path: Path, extract_dir: Path, target_pattern: str) -> bool:
        """
        TARファイルを展開
        """
        try:
            import tarfile
            
            with tarfile.open(archive_path, 'r:*') as tf:
                # すべて展開
                tf.extractall(extract_dir)
                
                # FFmpegバイナリを検索
                return self._find_and_copy_ffmpeg(extract_dir, target_pattern)
                
        except Exception as e:
            print(f"TAR extract error: {e}")
            return False
            
    def _copy_binary(self, binary_path: Path, target_pattern: str) -> bool:
        """
        バイナリファイルを直接コピー
        """
        try:
            # 出力ディレクトリを作成
            self.ffmpeg_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名を決定
            if self.system_name == 'windows':
                output_name = "ffmpeg.exe"
            else:
                output_name = "ffmpeg"
                
            output_path = self.ffmpeg_dir / output_name
            
            # コピー
            shutil.copy2(binary_path, output_path)
            
            # 実行権限を付与（Unix系）
            if self.system_name != 'windows':
                os.chmod(output_path, 0o755)
                
            return True
            
        except Exception as e:
            print(f"Copy binary error: {e}")
            return False
            
    def _find_and_copy_ffmpeg(self, search_dir: Path, pattern: str) -> bool:
        """
        展開されたディレクトリからFFmpegを検索してコピー
        """
        try:
            # パターンをワイルドカード展開
            import glob
            
            # パターンに基づいて検索
            pattern_parts = pattern.split('/')
            current_path = search_dir
            
            for part in pattern_parts:
                if '*' in part:
                    # ワイルドカードマッチング
                    matches = list(current_path.glob(part))
                    if matches:
                        current_path = matches[0]  # 最初にマッチしたものを使用
                    else:
                        # 代替検索
                        for item in current_path.iterdir():
                            if item.is_dir() and 'ffmpeg' in item.name.lower():
                                current_path = item
                                break
                        else:
                            return False
                else:
                    current_path = current_path / part
                    
            # FFmpegバイナリが見つかった場合
            if current_path.exists() and current_path.is_file():
                # 出力ディレクトリを作成
                self.ffmpeg_dir.mkdir(parents=True, exist_ok=True)
                
                # ファイル名を決定
                if self.system_name == 'windows':
                    output_name = "ffmpeg.exe"
                else:
                    output_name = "ffmpeg"
                    
                output_path = self.ffmpeg_dir / output_name
                
                # コピー
                shutil.copy2(current_path, output_path)
                
                # 実行権限を付与（Unix系）
                if self.system_name != 'windows':
                    os.chmod(output_path, 0o755)
                    
                return True
                
            return False
            
        except Exception as e:
            print(f"Find and copy error: {e}")
            return False
            
    def get_download_size_mb(self) -> int:
        """
        ダウンロードサイズ（MB）の概算を取得
        """
        if self.system_name == 'windows':
            return 75  # 約75MB
        elif self.system_name == 'linux':
            return 65  # 約65MB
        else:
            return 50  # 概算


# グローバルインスタンス
ffmpeg_downloader = FFmpegDownloader()
