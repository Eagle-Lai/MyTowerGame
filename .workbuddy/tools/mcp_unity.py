# -*- coding: utf-8 -*-
"""极简 Unity MCP(streamable HTTP) 客户端 —— 用于无人值守验证。

用法：
  python mcp_unity.py list                      # 列工具
  python mcp_unity.py call <tool> '<json-args>' # 调工具

实现：MCP streamable HTTP（POST /mcp，握手拿 Mcp-Session-Id，后续带同一会话头）。
响应可能是 text/event-stream（data: {...} 行）或裸 JSON，都兼容。
"""
import json
import sys
import urllib.request
import urllib.error

URL = __import__("os").environ.get("UNITY_MCP_URL", "http://127.0.0.1:8082/mcp")
SESSION = None
_next_id = [100]


def _post(payload, expect_result=True):
    global SESSION
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if SESSION:
        headers["Mcp-Session-Id"] = SESSION
    req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            SESSION = sid
        body = resp.read().decode("utf-8", "replace")
    if not expect_result:
        return None
    # SSE: 取最后一个 data: 行；否则整体按 JSON 解析
    data_line = None
    for line in body.splitlines():
        if line.startswith("data:"):
            data_line = line[5:].strip()
    raw = data_line if data_line is not None else body
    try:
        return json.loads(raw)
    except Exception:
        print("RAW>>", body[:2000])
        return None


def init():
    r = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "wb-verify", "version": "1.0"},
    }})
    if r is None or "result" not in r:
        raise SystemExit("initialize 失败: %r" % (r,))
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    info = r["result"].get("serverInfo", {})
    print("# server:", info.get("name"), info.get("version"))


def list_tools():
    r = _post({"jsonrpc": "2.0", "id": _next_id[0], "method": "tools/list"})
    _next_id[0] += 1
    for t in r["result"]["tools"]:
        print(t["name"], "|", (t.get("description") or "").split("\n")[0][:80])


def call(tool, args):
    _next_id[0] += 1
    r = _post({"jsonrpc": "2.0", "id": _next_id[0], "method": "tools/call",
               "params": {"name": tool, "arguments": args}})
    if r is None or "result" not in r:
        print("CALL FAIL:", json.dumps(r, ensure_ascii=False)[:2000] if r else "None")
        return
    res = r["result"]
    for c in res.get("content", []):
        if c.get("type") == "text":
            print(c["text"][:6000])
    if res.get("isError"):
        print("# isError=true")


if __name__ == "__main__":
    init()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        list_tools()
    elif cmd == "call":
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        tool = sys.argv[2]
        if tool == "execute_code":
            # 【会话级激活】scripting_ext 工具集每次新连接都要先 activate，且必须
            # 在同一进程（=同一 MCP 会话）内完成，否则 execute_code 会报未启用。
            try:
                _next_id[0] += 1
                _post({"jsonrpc": "2.0", "id": _next_id[0], "method": "tools/call",
                       "params": {"name": "manage_tools",
                                  "arguments": {"action": "activate", "tool": "scripting_ext"}}})
                print("# scripting_ext activated")
            except Exception as e:
                print("# activate scripting_ext skipped: %s" % e)
        call(tool, args)
