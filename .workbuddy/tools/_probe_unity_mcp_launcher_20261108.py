#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读烟雾测试：经 unity_mcp_launcher.py 起 stdio MCP，发 initialize 看能否收到响应。

不调用任何 Unity 工具、不写任何文件（除 launcher 自己的 stderr 日志）。
"""
import json
import os
import subprocess
import sys
import time

PY = os.path.expandvars(r"%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe")
LAUNCHER = os.path.expandvars(r"%USERPROFILE%\.codex\unity_mcp_launcher.py")

init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "workbuddy-probe", "version": "0"}}}

proc = subprocess.Popen([PY, LAUNCHER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL)
try:
    proc.stdin.write((json.dumps(init) + "\n").encode())
    proc.stdin.flush()
    start = time.time()
    line = b""
    while time.time() - start < 90:
        chunk = proc.stdout.readline()
        if not chunk:
            break
        line += chunk
        if line.strip().endswith(b"}") and b'"result"' in line or b'"error"' in line:
            break
    text = line.decode("utf-8", "replace").strip()
    if not text:
        print("❌ 无响应（超时 90s）")
        sys.exit(1)
    print("✅ 收到响应：")
    print(text[:1200])
finally:
    proc.kill()
