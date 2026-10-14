# -*- coding: utf-8 -*-
"""模拟鼠标点击屏幕坐标（用户鼠标路径）"""
import ctypes, sys, time
user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
def click(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.15)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    print(f"clicked ({x},{y})")
if __name__ == '__main__':
    click(int(sys.argv[1]), int(sys.argv[2]))
