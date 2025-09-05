@echo off
REM FFmpeg GUI Kun - Quick Build Script for Windows
REM Windows用の簡易ビルドスクリプト

echo 🚀 FFmpeg GUI Kun - Windows Build Script
echo ===========================================

REM Python バージョンチェック
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python not found. Please install Python 3.7 or higher
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 📍 Python Version: %PYTHON_VERSION%

REM 依存関係インストール
echo 📦 Installing dependencies...
pip install -r build_requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM ビルド実行
echo 🔨 Running build script...
python build.py %*
if %ERRORLEVEL% neq 0 (
    echo ❌ Build failed
    pause
    exit /b 1
)

echo ✅ Build completed!
echo    Check the dist\ directory for the executable
pause
