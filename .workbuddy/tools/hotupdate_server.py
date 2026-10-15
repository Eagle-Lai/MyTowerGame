#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自由人塔防 · 热更服务器一键启动（HTTP 静态服务 + UDP 自动发现广播）。

==================================================================
【解决什么问题】
  真机（手机）需要访问电脑的局域网 IP 下载热更，但家里/公司的
  DHCP IP 会变。本脚本在起 http 服务的同时，**周期性向局域网
  广播自己的存在**；游戏 Boot 阶段监听 UDP，收到广播即可自动
  拿到电脑当前 IP —— IP 怎么变都不用改代码、不用填候选。
  （模拟器不受影响：模拟器走 10.0.2.2 NAT 网关，收不到也无需收。）

【职责】
  1) HTTP：把 HotUpdateServer/ 根目录静态发布到 :8000
     （AB 平铺部署区 + Android/HybridCLR junction，布局见
       deploy_free_tower_cdn.py 的注释，与本脚本无关）。
  2) UDP：每个本机 IPv4 网卡，各向
       · 定向广播 x.y.z.255（假设 /24）
       · 全网广播 255.255.255.255
     每 ~1s 发一包，载荷："FTHOTUPD1|port=8000"。
     客户端校验魔数前缀，取**来源 IP** 为服务器地址。

【用法】
  python hotupdate_server.py               # 常驻（Ctrl+C 停）
  python hotupdate_server.py --self-test   # 额外自收自听验证广播

【防火墙提示（首次）】
  · 出站广播默认放行，无需操作。
  · 手机→电脑的 HTTP :8000 入站：若手机连不上，需放行
    （管理员 PowerShell：
      netsh advfirewall firewall add rule name="FT HotUpdate 8000" ^
        dir=in action=allow protocol=TCP localport=8000 )
==================================================================
"""
import argparse
import ipaddress
import re
import socket
import subprocess
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAGIC = b"FTHOTUPD1|"

ROOT = Path(__file__).resolve().parents[2] / "HotUpdateServer"

_IPV4_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")


def local_ipv4s() -> list:
    """枚举本机 IPv4（排除回环 127.* 与链路本地 169.254.*）。

    返回 [(网卡名, ip, 广播地址)]；零依赖（优先 psutil，否则解析 ipconfig）。
    """
    out = []

    # ① psutil（若已装）：跨平台、带网卡名
    try:
        import psutil
        for name, addrs in psutil.net_if_addrs().items():
            ip = mask = None
            for a in addrs:
                if a.family == socket.AF_INET:
                    ip, mask = a.address, a.netmask
            if ip and mask and not ip.startswith(("127.", "169.254.")):
                bc = str(ipaddress.ip_network(f"{ip}/{mask}", strict=False).broadcast_address)
                out.append((name, ip, bc))
        if out:
            return out
    except ImportError:
        pass

    # ② ipconfig 解析（Windows 零依赖兜底；中文系统=GBK，英文=ASCII 亦兼容）
    try:
        raw = subprocess.run(["ipconfig"], capture_output=True).stdout
    except OSError:
        return out
    txt = ""
    for enc in ("gbk", "utf-8", "latin-1"):
        try:
            cand = raw.decode(enc, errors="replace")
        except LookupError:
            continue
        if "IPv4" in cand and ("子网掩码" in cand or "Subnet Mask" in cand):
            txt = cand
            break
        if not txt:
            txt = cand  # 至少留一份，让 IPv4 行仍可解析

    adapter = "?"
    ip = mask = None
    for raw_line in txt.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if (":" in line or "：" in line) and line.strip().endswith((":", "：")) \
                and ". ." not in line:
            # 新适配器标题行（如 "无线局域网适配器 WLAN:"；含 . . 点阵的是取值行）
            adapter = line.strip().rstrip(":：").strip()
            ip = mask = None
            continue
        if "IPv4" in line:
            m = _IPV4_RE.search(line)
            if m:
                ip = m.group(1)
        if ("子网掩码" in line) or ("Subnet Mask" in line):
            m = _IPV4_RE.search(line)
            if m:
                mask = m.group(1)
        if ip and mask:
            # 排除：回环 / 链路本地 / TUN·fake-ip 劫持段（198.18.0.0/15，广播无意义）
            bad = ip.startswith(("127.", "169.254.", "198.18.", "198.19."))
            if not bad:
                try:
                    bc = str(ipaddress.ip_network(f"{ip}/{mask}", strict=False).broadcast_address)
                    out.append((adapter, ip, bc))
                except ValueError:
                    pass
            ip = mask = None
    return out


def broadcaster(udp_port: int, interval: float, stop_evt: threading.Event) -> None:
    """每个网卡各绑一个 UDP socket 发定向/全网广播。"""
    ifaces = local_ipv4s()
    if not ifaces:
        print("[bcast] 未发现可用的局域网 IPv4，广播线程退出（HTTP 仍正常）")
        return
    print("[bcast] 广播网卡：")
    for name, ip, bc in ifaces:
        print(f"[bcast]   {name:<24} ip={ip:<16} broadcast={bc}")

    socks = []
    for _name, ip, bc in ifaces:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.bind((ip, 0))
            s.settimeout(0.2)
            socks.append((s, ip, bc))
        except OSError as e:
            print(f"[bcast] 绑定 {ip} 失败（跳过）：{e}")

    payload_tail = f"port={udp_port}".encode("ascii")
    n = 0
    while not stop_evt.is_set():
        for s, ip, bc in socks:
            for dst in (bc, "255.255.255.255"):
                try:
                    s.sendto(MAGIC + payload_tail, (dst, udp_port))
                except OSError:
                    pass  # 目标网段不可广播时静默（如虚拟网卡）
        n += 1
        stop_evt.wait(interval)
    print(f"[bcast] 已停止（共发送 {n} 轮）")


def self_test(udp_port: int, seconds: float = 3.0) -> None:
    """收自己的广播：验证 payload/端口/广播链路。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("", udp_port))
    except OSError as e:
        print(f"[self-test] 绑定 {udp_port} 失败：{e}")
        return
    s.settimeout(1.0)
    t0 = time.time()
    hits = 0
    while time.time() - t0 < seconds:
        try:
            data, addr = s.recvfrom(1024)
        except socket.timeout:
            continue
        if data.startswith(MAGIC):
            hits += 1
            print(f"[self-test] 收到广播 ← {addr[0]}:{addr[1]} payload={data!r}")
    print(f"[self-test] {seconds}s 共收到 {hits} 包 "
          + ("→ 广播链路 OK" if hits else "→ 未收到！检查防火墙/网卡"))
    s.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--http-port", type=int, default=8000)
    ap.add_argument("--udp-port", type=int, default=28000)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--root", default=str(ROOT), help="HTTP 根目录（默认 HotUpdateServer/）")
    ap.add_argument("--self-test", action="store_true",
                    help="起服务前先自收广播验证（约 3s）")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"[http] 根目录不存在：{root}")
        return 1

    if args.self_test:
        threading.Thread(target=broadcaster,
                         args=(args.udp_port, 0.3, threading.Event()),
                         daemon=True).start()
        self_test(args.udp_port)
    else:
        threading.Thread(target=broadcaster,
                         args=(args.udp_port, args.interval, threading.Event()),
                         daemon=True).start()

    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    httpd = ThreadingHTTPServer(("0.0.0.0", args.http_port), handler)
    print(f"[http] serving {root} at 0.0.0.0:{args.http_port}")
    print(f"[udp ] broadcasting FTHOTUPD1 to port {args.udp_port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[http] bye")
    return 0


if __name__ == "__main__":
    sys.exit(main())
