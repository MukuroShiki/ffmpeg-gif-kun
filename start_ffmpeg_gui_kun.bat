@echo off
REM FFmpeg GUI Kun 起動バッチファイル
REM このファイルをダブルクリックしてアプリケーションを起動

cd /d "%~dp0"

REM Python仮想環境がある場合は使用
if exist ".venv\Scripts\python.exe" (
    echo 仮想環境でFFmpeg GUI Kunを起動中...
    ".venv\Scripts\python.exe" ./src/ffmpeg_gui_kun.py
) else (
    REM システムのPythonを使用
    echo システムPythonでFFmpeg GUI Kunを起動中...
    python ./src/ffmpeg_gui_kun.py
)

REM エラーが発生した場合は一時停止
if errorlevel 1 (
    echo.
    echo エラーが発生しました。
    echo Pythonがインストールされているか、またはFFmpegがPATHに追加されているか確認してください。
    pause
)
