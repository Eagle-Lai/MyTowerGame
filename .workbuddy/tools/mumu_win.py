# -*- coding: utf-8 -*-
"""MuMu 窗口工具：查找窗口位置 + 鼠标点击模拟（用户鼠标路径复现）"""
import ctypes, ctypes.wintypes as wt, sys, time

user32 = ctypes.windll.user32

def enum_windows():
    results = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            pid = wt.DWORD(0)
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            rect = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            results.append({
                'hwnd': hwnd, 'pid': pid.value, 'title': title,
                'rect': (rect.left, rect.top, rect.right, rect.bottom),
                'w': rect.right - rect.left, 'h': rect.bottom - rect.top,
            })
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return results

if __name__ == '__main__':
    wins = enum_windows()
    # 过滤 MuMu 相关：标题或运行中进程
    import subprocess
    procs = subprocess.run(['tasklist'], capture_output=True, text=True, encoding='gbk', errors='ignore').stdout
    mumu_pids = set()
    for line in procs.splitlines():
        if 'MuMu' in line or 'Nx' in line:
            parts = line.split()
            if len(parts) > 1 and parts[1].isdigit():
                mumu_pids.add(int(parts[1]))
    print("=== MuMu PIDs:", sorted(mumu_pids))
    for w in wins:
        if w['pid'] in mumu_pids or 'MuMu' in w['title'] or '模拟' in w['title']:
            print(w)
