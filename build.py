"""
FFmpeg GUI Kun - PyInstaller Build Script

実行可能ファイル作成用のビルドスクリプト
"""

import sys
import os
import shutil
from pathlib import Path
import subprocess
import platform


class FFmpegGUIBuilder:
    """
    FFmpeg GUI Kunのビルダークラス
    """
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.src_dir = self.root_dir / "src"
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.spec_file = self.root_dir / "ffmpeg_gui_kun.spec"
        self.system = platform.system().lower()
        
    def clean_build(self):
        """
        ビルド前のクリーンアップ
        """
        print("🧹 Cleaning build directories...")
        
        # 古いビルド成果物を削除
        for directory in [self.dist_dir, self.build_dir]:
            if directory.exists():
                shutil.rmtree(directory)
                print(f"   Removed: {directory}")
                
        # 古いspecファイルを削除
        if self.spec_file.exists():
            self.spec_file.unlink()
            print(f"   Removed: {self.spec_file}")
            
        print("✅ Build directories cleaned")
        
    def check_dependencies(self):
        """
        必要な依存関係をチェック
        """
        print("🔍 Checking dependencies...")
        
        try:
            import PyInstaller
            print(f"   PyInstaller: {PyInstaller.__version__}")
        except ImportError:
            print("❌ PyInstaller not found. Install with:")
            print("   pip install -r build_requirements.txt")
            return False
            
        if not self.src_dir.exists():
            print(f"❌ Source directory not found: {self.src_dir}")
            return False
            
        main_file = self.src_dir / "ffmpeg_gui_kun.py"
        if not main_file.exists():
            print(f"❌ Main file not found: {main_file}")
            return False
            
        print("✅ Dependencies check passed")
        return True
        
    def create_spec_file(self):
        """
        PyInstaller specファイルを作成
        """
        print("📝 Creating PyInstaller spec file...")
        
        # アイコンファイルの確認
        icon_path = self.root_dir / "asset" / "icon.ico"
        icon_option = f"icon=r'{icon_path.as_posix()}'" if icon_path.exists() else ""
        
        # specファイルの内容（Windows パス対応）
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os

# パスを正規化
src_dir = r'{self.src_dir.as_posix()}'
readme_path = r'{self.root_dir / "README.txt"}'
asset_path = r'{self.root_dir / "asset"}'

# 存在するファイルのみをdatasに追加
datas = []
if os.path.exists(readme_path):
    datas.append((readme_path, '.'))
if os.path.exists(asset_path):
    datas.append((asset_path, 'asset'))

a = Analysis(
    [os.path.join(src_dir, 'ffmpeg_gui_kun.py')],
    pathex=[src_dir],
    binaries=[],
    datas=datas,
    hiddenimports=['tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'threading', 'subprocess', 'json', 'pathlib'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FFmpeg-GUI-Kun',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_option}
)
'''
        
        # specファイルを書き込み
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
            
        print(f"✅ Spec file created: {self.spec_file}")
        
    def build_executable(self):
        """
        実行可能ファイルをビルド
        """
        print("🔨 Building executable...")
        
        # PyInstallerコマンド構築（specファイル使用時はオプション不要）
        cmd = [
            sys.executable, 
            "-m", "PyInstaller",
            str(self.spec_file)
        ]
            
        print(f"   Command: {' '.join(cmd)}")
        
        # ビルド実行
        try:
            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Build completed successfully!")
                return True
            else:
                print("❌ Build failed!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
            
    def create_distribution(self):
        """
        配布用パッケージを作成
        """
        print("📦 Creating distribution package...")
        
        # 実行ファイルの確認
        if self.system == 'windows':
            exe_name = "FFmpeg-GUI-Kun.exe"
        else:
            exe_name = "FFmpeg-GUI-Kun"
            
        exe_path = self.dist_dir / exe_name
        if not exe_path.exists():
            print(f"❌ Executable not found: {exe_path}")
            return False
            
        # 配布用ディレクトリ
        package_name = f"FFmpeg-GUI-Kun-{self.system}"
        package_dir = self.dist_dir / package_name
        
        if package_dir.exists():
            shutil.rmtree(package_dir)
            
        package_dir.mkdir(parents=True)
        
        # ファイルをコピー
        shutil.copy2(exe_path, package_dir / exe_name)
        shutil.copy2(self.root_dir / "README.txt", package_dir)
        
        # アセットフォルダがある場合
        asset_dir = self.root_dir / "asset"
        if asset_dir.exists():
            shutil.copytree(asset_dir, package_dir / "asset")
            
        # 起動スクリプト（バックアップ用）
        if self.system == 'windows':
            script_content = f'@echo off\\nstart "" "{exe_name}"'
            script_path = package_dir / "start.bat"
        else:
            script_content = f'#!/bin/bash\\n"./{exe_name}"'
            script_path = package_dir / "start.sh"
            
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        if self.system != 'windows':
            os.chmod(script_path, 0o755)
            
        # ZIP圧縮
        archive_path = self.dist_dir / f"{package_name}.zip"
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'zip',
            str(self.dist_dir),
            package_name
        )
        
        print(f"✅ Distribution package created:")
        print(f"   Directory: {package_dir}")
        print(f"   Archive: {archive_path}")
        
        return True
        
    def build(self, clean=True):
        """
        完全ビルドプロセス
        """
        print("🚀 Starting FFmpeg GUI Kun build process...")
        print(f"   System: {platform.system()} {platform.machine()}")
        print(f"   Python: {sys.version}")
        
        try:
            # ステップ1: クリーンアップ
            if clean:
                self.clean_build()
                
            # ステップ2: 依存関係チェック
            if not self.check_dependencies():
                return False
                
            # ステップ3: specファイル作成
            self.create_spec_file()
            
            # ステップ4: ビルド実行
            if not self.build_executable():
                return False
                
            # ステップ5: 配布パッケージ作成
            if not self.create_distribution():
                return False
                
            print("🎉 Build process completed successfully!")
            print("   Ready for distribution!")
            return True
            
        except KeyboardInterrupt:
            print("\\n❌ Build interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False


def main():
    """
    メイン関数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Build FFmpeg GUI Kun executable')
    parser.add_argument('--no-clean', action='store_true', 
                       help='Skip cleaning build directories')
    parser.add_argument('--clean-only', action='store_true',
                       help='Only clean build directories')
    
    args = parser.parse_args()
    
    builder = FFmpegGUIBuilder()
    
    if args.clean_only:
        builder.clean_build()
        return
        
    success = builder.build(clean=not args.no_clean)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
