#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把关卡录像转成指定倍速的观感版本（默认 2 倍速）。

为什么不在录制时开倍速：回放器是固定步长手动时钟，
`BalancePlayModeVerifier` 调用 `StepManualFrame(step / Speed)`，
而 `GameClock` 内部又乘回 `Speed`，两者抵消，
所以游戏内点 2x 不会改变每步推进的模拟时长，
既不会加快录制，也不会让视频变快。真正的倍速只能在输出端用 setpts 做。

用法：
    python Tools/make_video_speed.py L02              # 生成 2x 版
    python Tools/make_video_speed.py L02 --speed 3    # 生成 3x 版
    python Tools/make_video_speed.py --all --speed 2  # 全部关卡

产出：与源文件同目录，文件名追加 _2x / _3x。源文件保留不变。
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(ROOT, "Docs", "LevelVideos")
FFMPEG = os.path.expanduser(r"~\.workbuddy\tools\ffmpeg\bin\ffmpeg.exe")
FFPROBE = os.path.expanduser(r"~\.workbuddy\tools\ffmpeg\bin\ffprobe.exe")


def duration(path):
    cmd = [FFPROBE, "-v", "error", "-show_entries", "format=duration",
           "-of", "json", path]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return float(json.loads(out.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def convert(src, speed):
    if not os.path.isfile(src):
        print("缺少源文件:", src)
        return None
    tag = ("%g" % speed).replace(".", "p")
    dst = os.path.join(os.path.dirname(src),
                       os.path.splitext(os.path.basename(src))[0] + "_%sx.mp4" % tag)
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "warning",
           "-i", src,
           "-vf", "setpts=%.8f*PTS" % (1.0 / speed),
           "-r", "30",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst]
    before = duration(src)
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0 or not os.path.isfile(dst):
        print("转码失败:", (result.stderr or "").strip()[:300])
        return None
    after = duration(dst)
    size_mb = os.path.getsize(dst) / 1048576
    print("%-6s %6.1fs -> %6.1fs (%.0f%%)  %5.1fMB  %s" % (
        os.path.basename(src), before, after, (after / before * 100) if before else 0,
        size_mb, os.path.relpath(dst, ROOT)))
    return dst


def main():
    args = sys.argv[1:]
    speed = 2.0
    if "--speed" in args:
        index = args.index("--speed")
        speed = float(args[index + 1])
        del args[index:index + 2]
    levels = args
    if "--all" in levels:
        levels = sorted(d for d in os.listdir(VIDEO_DIR)
                        if d.startswith("L") and os.path.isdir(os.path.join(VIDEO_DIR, d)))
    if not levels:
        print("用法: python Tools/make_video_speed.py L02 [--speed 2] | --all")
        return 2
    if not os.path.isfile(FFMPEG):
        print("ffmpeg 不存在:", FFMPEG)
        return 2

    done = []
    for level in levels:
        src = os.path.join(VIDEO_DIR, level, "%s_完整通关.mp4" % level)
        if not os.path.isfile(src):
            print("%-5s 缺少视频" % level)
            continue
        out = convert(src, speed)
        if out:
            done.append({"level": level, "speed": speed, "output": os.path.relpath(out, ROOT),
                         "duration": duration(out)})
    if done:
        print("\n完成 %d 个" % len(done))
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
