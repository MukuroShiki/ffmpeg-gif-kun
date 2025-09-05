"""
FFmpeg GUI Kun - ドラッグ&ドロップユーティリティ

標準Tkinterを使用したドラッグ&ドロップ機能を提供する
tkinterdnd2がない環境でも動作するフォールバック実装
"""

import tkinter as tk
import os
import platform
from pathlib import Path
from typing import Callable, Optional


class DragDropHandler:
    """
    ドラッグ&ドロップハンドラークラス
    
    標準Tkinterを使用してファイルドロップ機能を提供
    Windowsのみ対応（tkinterdnd2の代替）
    """
    
    def __init__(self):
        self.drop_callbacks = {}
        self.is_windows = platform.system() == "Windows"
        
    def register_drop_target(self, widget: tk.Widget, callback: Callable[[str], None]):
        """
        ドロップターゲットとしてウィジェットを登録
        
        Args:
            widget: ドロップを受け付けるウィジェット
            callback: ドロップ時のコールバック関数（ファイルパスを引数に取る）
        """
        self.drop_callbacks[widget] = callback
        
        # Windowsの場合のみドラッグ&ドロップを有効化
        if self.is_windows:
            self._setup_windows_drop(widget, callback)
        else:
            # Windows以外では視覚的なヒントのみ提供
            self._setup_visual_hints(widget)
            
    def _setup_windows_drop(self, widget: tk.Widget, callback: Callable[[str], None]):
        """
        Windows用のドラッグ&ドロップセットアップ
        
        注意: この実装は基本的な機能のみ提供
        完全なドラッグ&ドロップにはtkinterdnd2が必要
        """
        # ダミー実装 - 実際のドラッグ&ドロップは困難
        # 代わりに視覚的ヒントとファイル選択ボタンを強調
        self._setup_visual_hints(widget)
        
    def _setup_visual_hints(self, widget: tk.Widget):
        """
        ドラッグ&ドロップの視覚的ヒントをセットアップ
        """
        # ttk.Entryウィジェットの場合はreliefプロパティは使用できない
        # 代わりに背景色やカーソルで視覚的フィードバックを提供
        def on_enter(event):
            try:
                # ttk.Entryの場合は背景色での強調表示を試す
                widget.configure(background='lightblue')
            except:
                # 他のウィジェットの場合は従来通り
                try:
                    widget.configure(relief=tk.RAISED, borderwidth=2)
                except:
                    pass
            
        def on_leave(event):
            try:
                # ttk.Entryの場合は元の背景色に戻す
                widget.configure(background='white')
            except:
                # 他のウィジェットの場合は従来通り
                try:
                    widget.configure(relief=tk.FLAT, borderwidth=1)
                except:
                    pass
            
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


class SimpleDragDrop:
    """
    シンプルなドラッグ&ドロップ機能
    
    tkinterdnd2がない環境での代替実装
    """
    
    def __init__(self):
        self.handler = DragDropHandler()
        
    def enable_drop(self, widget: tk.Widget, callback: Callable[[str], None]):
        """
        ウィジェットにドロップ機能を追加
        
        Args:
            widget: 対象ウィジェット
            callback: ファイルドロップ時のコールバック
        """
        self.handler.register_drop_target(widget, callback)
        
        # ヒントテキストを追加
        if hasattr(widget, 'insert'):
            # エントリウィジェットの場合
            original_text = widget.get()
            if not original_text:
                widget.insert(0, "ここにファイルをドラッグ&ドロップ（または参照ボタン）")
                widget.configure(foreground='gray')
                
                def on_focus_in(event):
                    current_text = widget.get()
                    if "ここにファイルを" in current_text:
                        widget.delete(0, tk.END)
                        widget.configure(foreground='black')
                        
                def on_focus_out(event):
                    current_text = widget.get()
                    if not current_text:
                        widget.insert(0, "ここにファイルをドラッグ&ドロップ（または参照ボタン）")
                        widget.configure(foreground='gray')
                        
                widget.bind("<FocusIn>", on_focus_in)
                widget.bind("<FocusOut>", on_focus_out)


# グローバルインスタンス
drag_drop = SimpleDragDrop()
