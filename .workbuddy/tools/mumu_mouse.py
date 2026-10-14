# -*- coding: utf-8 -*-
"""激活 MuMu 窗口并模拟鼠标点击（用户鼠标路径复现）"""
import ctypes, sys, time
user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SW_RESTORE = 9
HWND = int(sys.argv[1]) if len(sys.argv) > 1 else 267184

def activate(hwnd):
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.2)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.4)

def click(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.2)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

if __name__ == '__main__':
    cmd = sys.argv[2] if len(sys.argv) > 2 else 'click'
    if cmd == 'activate':
        activate(HWND)
        print("activated, foreground =", user32.GetForegroundWindow())
    elif cmd == 'click':
        activate(HWND)
        x, y = int(sys.argv[3]), int(sys.argv[4])
        click(x, y)
        print(f"clicked ({x},{y})")
