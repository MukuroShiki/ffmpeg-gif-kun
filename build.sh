#!/bin/bash
# FFmpeg GUI Kun - Quick Build Script for Linux/macOS
# Linux/macOS用の簡易ビルドスクリプト

set -e  # エラーで停止

echo "🚀 FFmpeg GUI Kun - Linux/macOS Build Script"
echo "=============================================="

# Python バージョンチェック
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "📍 Python Version: $PYTHON_VERSION"

# 必要な最小バージョンチェック
REQUIRED_VERSION="3.7"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required"
    exit 1
fi

# 依存関係インストール
echo "📦 Installing dependencies..."
pip3 install -r build_requirements.txt

# ビルド実行
echo "🔨 Running build script..."
python3 build.py "$@"

echo "✅ Build completed!"
echo "   Check the dist/ directory for the executable"
