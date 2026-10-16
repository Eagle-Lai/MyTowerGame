"""Use the installed Unity-MCP local framed transport; no source injection to Assets.
Usage: python unity_probe.py request.json evidence/result.json
Requests and results stay in ReleaseReadiness; inspect each request before running.
"""
import json
import pathlib
import socket
import struct
import sys

def recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n-len(buf))
        if not chunk:
            raise EOFError("Unity bridge closed connection")
        buf.extend(chunk)
    return bytes(buf)

def call(request, port=6400):
    with socket.create_connection(("127.0.0.1", port), timeout=8) as sock:
        sock.settimeout(55)
        greeting = bytearray()
        while not greeting.endswith(b"\n"):
            greeting.extend(recv_exact(sock, 1))
        if b"UNITY-MCP" not in greeting:
            raise RuntimeError("Unexpected Unity bridge greeting")
        payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
        sock.sendall(struct.pack(">Q",len(payload))+payload)
        n = struct.unpack(">Q",recv_exact(sock,8))[0]
        if n > 32*1024*1024:
            raise RuntimeError("Unexpectedly large Unity bridge response")
        return json.loads(recv_exact(sock,n))

if __name__ == "__main__":
    request_path = pathlib.Path(sys.argv[1])
    if request_path.name.endswith(".cs.txt"):
        request = {"type":"execute_code", "params":{"action":"execute", "code":request_path.read_text(encoding="utf-8-sig")}}
    else:
        request = json.loads(request_path.read_text(encoding="utf-8-sig"))
    try:
        result = call(request)
    except Exception as exc:
        result = {"probe_failed":type(exc).__name__,"message":str(exc)}
    pathlib.Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False,indent=2),encoding="utf-8")
    printable=json.dumps(result,ensure_ascii=False,indent=2)
    print(printable if len(printable)<15000 else printable[:6500]+"\n[Full response saved in evidence file]")
