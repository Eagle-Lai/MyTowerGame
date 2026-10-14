# -*- coding: utf-8 -*-
"""MuMu 标定：按住拖动到 4 个位置，供截图分析"""
import ctypes, sys, time
user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SW_RESTORE = 9
HWND = 91817136

def rect():
    r = ctypes.wintypes.RECT() if hasattr(ctypes, 'wintypes') else None
    import ctypes.wintypes as wt
    r = wt.RECT()
    user32.GetWindowRect(HWND, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)

import ctypes.wintypes as wt

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'rect':
        print('rect:', rect())
    elif cmd == 'down':
        user32.ShowWindow(HWND, SW_RESTORE); time.sleep(0.2)
        user32.SetForegroundWindow(HWND); time.sleep(0.4)
        x, y = int(sys.argv[2]), int(sys.argv[3])
        user32.SetCursorPos(x, y); time.sleep(0.2)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        print(f'down at ({x},{y})')
    elif cmd == 'move':
        x, y = int(sys.argv[2]), int(sys.argv[3])
        user32.SetCursorPos(x, y)
        print(f'move to ({x},{y})')
    elif cmd == 'up':
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        print('up')
