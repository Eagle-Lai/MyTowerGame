# -*- coding: utf-8 -*-
"""MuMu 鼠标工具：支持按下/抬起分离，用于坐标追踪"""
import ctypes, sys, time
user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SW_RESTORE = 9
HWND = 91817136

def activate():
    user32.ShowWindow(HWND, SW_RESTORE)
    time.sleep(0.2)
    user32.SetForegroundWindow(HWND)
    time.sleep(0.3)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'down':
        activate()
        x, y = int(sys.argv[2]), int(sys.argv[3])
        user32.SetCursorPos(x, y)
        time.sleep(0.2)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        print(f"mouse DOWN at ({x},{y})")
    elif cmd == 'up':
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        print("mouse UP")
    elif cmd == 'move':
        x, y = int(sys.argv[2]), int(sys.argv[3])
        user32.SetCursorPos(x, y)
        print(f"moved to ({x},{y})")
