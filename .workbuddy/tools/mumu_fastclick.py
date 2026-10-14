# -*- coding: utf-8 -*-
"""MuMu 快速点击（含激活）：用于需要"轻点"的 ScrollView 卡片等场景。
用法: python mumu_fastclick.py <x> <y>   （屏幕坐标）
"""
import ctypes
import sys
import time

user32 = ctypes.windll.user32
HWND = 91817136  # MuMu 主窗口（重启模拟器后需更新，可从 MuMuManager info 的 main_wnd 获取十六进制值换算）


def main():
    x, y = int(sys.argv[1]), int(sys.argv[2])
    user32.ShowWindow(HWND, 9)          # SW_RESTORE
    time.sleep(0.2)
    user32.SetForegroundWindow(HWND)
    time.sleep(0.4)
    user32.SetCursorPos(x, y)
    time.sleep(0.15)
    user32.mouse_event(0x0002, 0, 0, 0, 0)   # LEFTDOWN
    time.sleep(0.08)
    user32.mouse_event(0x0004, 0, 0, 0, 0)   # LEFTUP
    print(f"fast click ({x},{y})")


if __name__ == '__main__':
    main()
