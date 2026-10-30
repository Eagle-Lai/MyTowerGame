#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批次录制进度快照：已完成关卡、正在录的关卡、磁盘、报错。

用法：
    python Tools/watch_video_batch.py            # 打印一次快照
    python Tools/watch_video_batch.py --watch 60  # 每 60 秒重复打印（前台阻塞）

判定口径（2026-10-23 修正）：
只有运行日志 `Lxx_完整通关.log.txt` 里出现 `end ok=True` 且成片 > 16MB 才算"已完成"。
早期版本只看 mp4 大小，会把 ffmpeg 正在写入的半成品误判成完成（L10 实测踩到：
16:44:56 成片已 276MB 但日志要到 16:45:04 才写 end 行）。
另外区分三种中间态：录制中（有 _frames_* 目录）、编码中（有 mp4 但无 end 行）、
已完成。注意 `BalancePlayModeVerifier.StartVideoBatch` 的断点续跑仍用 16MB 阈值，
若批次中途重启，恰好停在编码中的那一关会被跳过——重启后需人工核对该关日志。
"""
import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(ROOT, "Docs", "LevelVideos")
BATCH_DIR = os.path.join(ROOT, "Library", "BalanceWorkbench", "Video-Batch")
MIN_BYTES = 16 * 1024 * 1024


def human(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return "%.1f%s" % (size, unit)
        size /= 1024.0


def snapshot():
    lines = []
    # 逐关扫目录，按运行日志的 end 行判定状态，避免把编码中的半成品算成完成。
    # 2026-10-24 起视频平铺在 VIDEO_DIR 根下（用户要求归拢一个文件夹），
    # 这里同时兼容旧的每关子目录布局：平铺文件与子目录都会被发现。
    done, total_bytes, encoding, active, active_frames = [], 0, [], None, 0
    if os.path.isdir(VIDEO_DIR):
        for name in sorted(os.listdir(VIDEO_DIR)):
            if not name.startswith("L"):
                continue
            if os.path.isfile(os.path.join(VIDEO_DIR, name)) and name.endswith(".mp4"):
                level = name.split("_")[0]  # 平铺：L01_完整通关_2x.mp4 -> L01
                level_dir = VIDEO_DIR
            elif os.path.isdir(os.path.join(VIDEO_DIR, name)):
                level, level_dir = name, os.path.join(VIDEO_DIR, name)  # 旧布局
            else:
                continue
            mp4 = os.path.join(level_dir, level + "_完整通关_2x.mp4")
            log = os.path.join(level_dir, level + "_完整通关.log.txt")
            frames_dir = os.path.join(level_dir, "_frames_" + level + "_完整通关")
            finished = False
            if os.path.isfile(log):
                try:
                    with open(log, encoding="utf-8", errors="replace") as handle:
                        finished = "end ok=True" in handle.read()
                except Exception:
                    pass
            if finished and os.path.isfile(mp4) and os.path.getsize(mp4) > MIN_BYTES:
                size = os.path.getsize(mp4)
                done.append(level)
                total_bytes += size
            elif os.path.isfile(mp4):
                encoding.append(level)  # 有 mp4 但没写 end 行：ffmpeg 还在编码
            elif os.path.isdir(frames_dir):
                active = level
                try:
                    active_frames = len(os.listdir(frames_dir))
                except Exception:
                    active_frames = 0
    # 批次状态
    phase, round_no, combat, gold, hp, elapsed = "?", "?", 0.0, "?", "?", 0.0
    status_path = os.path.join(BATCH_DIR, "status.json")
    if os.path.isfile(status_path):
        try:
            with open(status_path, encoding="utf-8") as handle:
                status = json.load(handle)
            phase = status.get("phase")
            round_no = status.get("round")
            combat = (status.get("combatMs") or 0) / 1000.0
            gold, hp = status.get("gold"), status.get("hp")
            elapsed = status.get("elapsedSeconds") or 0.0
        except Exception:
            pass  # status.json 正在被重写，下一轮再读
    # 报错
    errors = []
    if os.path.isdir(BATCH_DIR):
        errors = sorted(f for f in os.listdir(BATCH_DIR) if f.startswith("video-error"))
    # 磁盘
    try:
        usage = shutil.disk_usage(ROOT)
        disk = "%s 可用 / 共 %s" % (human(usage.free), human(usage.total))
    except Exception:
        disk = "?"

    lines.append("批次进度  %d/29 关完成  已产 %s" % (len(done), human(total_bytes)))
    lines.append("当前关卡  %s  第 %s 波  战斗 %.0fs  生命 %s  金币 %s" % (
        active or "(无)", round_no, combat, hp, gold))
    lines.append("本关已抓  %d 帧   批次已跑 %.0f 分钟" % (active_frames, elapsed / 60.0))
    if encoding:
        lines.append("编码中    %s（ffmpeg 收尾中，暂无 _frames_* 目录）" % ", ".join(encoding))
    lines.append("磁盘      %s" % disk)
    if errors:
        lines.append("!! 报错文件 %d 个: %s" % (len(errors), ", ".join(errors[:5])))
        for name in errors[:3]:
            path = os.path.join(BATCH_DIR, name)
            try:
                with open(path, encoding="utf-8", errors="replace") as handle:
                    lines.append("   %s: %s" % (name, handle.read().strip()[:200]))
            except Exception:
                pass
    lines.append("已完成    %s" % (", ".join(done) if done else "(无)"))
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    interval = 0
    if "--watch" in args:
        index = args.index("--watch")
        interval = int(args[index + 1]) if index + 1 < len(args) else 60
        del args[index:index + 2]
    if args:
        print("用法: python Tools/watch_video_batch.py [--watch 秒]")
        return 2
    while True:
        print("[%s]" % time.strftime("%H:%M:%S"))
        print(snapshot())
        print()
        if interval <= 0:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())
