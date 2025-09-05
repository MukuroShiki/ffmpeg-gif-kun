#!/bin/bash
# FFmpeg GUI Kun 起動スクリプト (macOS/Linux用)

cd "$(dirname "$0")"

# Python仮想環境がある場合は使用
if [ -f ".venv/bin/python" ]; then
    echo "仮想環境でFFmpeg GUI Kunを起動中..."
    .venv/bin/python ./src/ffmpeg_gui_kun.py
else
    # システムのPythonを使用
    echo "システムPythonでFFmpeg GUI Kunを起動中..."
    if command -v python3 &> /dev/null; then
        python3 ./src/ffmpeg_gui_kun.py
    elif command -v python &> /dev/null; then
        python ./src/ffmpeg_gui_kun.py
    else
        echo "エラー: Pythonが見つかりません。"
        echo "Python 3.7以上をインストールしてください。"
        exit 1
    fi
fi

# エラーが発生した場合
if [ $? -ne 0 ]; then
    echo ""
    echo "エラーが発生しました。"
    echo "Pythonがインストールされているか、またはFFmpegがPATHに追加されているか確認してください。"
    read -p "Enterキーで終了..."
fi
