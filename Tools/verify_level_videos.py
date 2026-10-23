#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 Docs/LevelVideos 下的关卡录像：时长、分辨率、编码，并抽取关键帧。

用法：
    python Tools/verify_level_videos.py            # 校验全部已产出的视频
    python Tools/verify_level_videos.py L02        # 只校验 L02
    python Tools/verify_level_videos.py L02 --frames   # 额外抽帧到 Docs/LevelVideos/_frames
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(ROOT, "Docs", "LevelVideos")
FFMPEG = os.path.expanduser(r"~\.workbuddy\tools\ffmpeg\bin\ffmpeg.exe")
FFPROBE = os.path.expanduser(r"~\.workbuddy\tools\ffmpeg\bin\ffprobe.exe")


def probe(path):
    cmd = [FFPROBE, "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,codec_name,pix_fmt,nb_frames,r_frame_rate,duration",
           "-show_entries", "format=duration,size", "-of", "json", path]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        return {"error": (out.stderr or "").strip()[:300]}
    data = json.loads(out.stdout or "{}")
    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}
    return {
        "codec": stream.get("codec_name"),
        "pix_fmt": stream.get("pix_fmt"),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "fps": stream.get("r_frame_rate"),
        "frames": stream.get("nb_frames"),
        "duration": float(fmt.get("duration") or stream.get("duration") or 0),
        "size_mb": round(float(fmt.get("size") or 0) / 1048576, 1),
    }


def extract_frames(path, level, count=5):
    out_dir = os.path.join(VIDEO_DIR, "_frames", level)
    os.makedirs(out_dir, exist_ok=True)
    info = probe(path)
    duration = info.get("duration") or 0
    if duration <= 0:
        return []
    saved = []
    for i in range(count):
        stamp = duration * (i + 0.5) / count
        target = os.path.join(out_dir, "%s_%02d_%05.0fs.png" % (level, i + 1, stamp))
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
               "-ss", "%.2f" % stamp, "-i", path, "-frames:v", "1", target]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(target) and os.path.getsize(target) > 1024:
            saved.append(target)
    return saved


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want_frames = "--frames" in sys.argv
    targets = args or sorted(
        d for d in os.listdir(VIDEO_DIR)
        if d.startswith("L") and os.path.isdir(os.path.join(VIDEO_DIR, d))
    ) if os.path.isdir(VIDEO_DIR) else []

    if not os.path.isfile(FFPROBE):
        print("ffprobe 不存在:", FFPROBE)
        return 2

    rows = []
    for level in targets:
        path = os.path.join(VIDEO_DIR, level, "%s_完整通关.mp4" % level)
        if not os.path.isfile(path):
            print("%-5s 缺少视频" % level)
            continue
        info = probe(path)
        if info.get("error"):
            print("%-5s ffprobe 失败: %s" % (level, info["error"]))
            continue
        ok = (info["codec"] == "h264" and info["pix_fmt"] == "yuv420p"
              and info["height"] == 720 and info["duration"] > 10)
        print("%-5s %s  %sx%s %s %s  %6.1fs  %5.1fMB  %s" % (
            level, "OK  " if ok else "FAIL",
            info["width"], info["height"], info["codec"], info["pix_fmt"],
            info["duration"], info["size_mb"], info["fps"]))
        rows.append({"level": level, "ok": ok, **info})
        if want_frames:
            for frame in extract_frames(path, level):
                print("        抽帧:", os.path.relpath(frame, ROOT))

    out = os.path.join(VIDEO_DIR, "verify-summary.json")
    if rows:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as handle:
            json.dump(rows, handle, ensure_ascii=False, indent=2)
        print("\n汇总:", out)
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
