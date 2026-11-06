# -*- coding: utf-8 -*-
"""只读：扫描 prefab/scene 里 TMP 文本组件使用的字体归属。
用途：改字体/TMP 默认字前，确认哪些界面真正在用 SiYuanSongTi 与 TacticalSans。
"""
import os
import re
import glob
import collections

ROOT = r"E:\MyTowerGame\Assets"
FONTS = {
    "68c477d3ad7f6e14baa3e8e1239d05de": "SiYuanSongTi SDF",
    "02f8ccba7a2f2ea47ba04bb3b1a04744": "NotoSansCJKsc(源otf)",
}
# TMP 字体资产的 guid 单独再查
for p in glob.glob(os.path.join(ROOT, "**", "*.asset.meta"), recursive=True):
    if "TacticalSans" in p:
        t = open(p, encoding="utf-8", errors="ignore").read()
        m = re.search(r"guid: (\w+)", t)
        if m:
            FONTS[m.group(1)] = "TacticalSans SDF"

FILES = []
for ext in ("*.prefab", "*.unity"):
    FILES += glob.glob(os.path.join(ROOT, "**", ext), recursive=True)


def scan():
    usage = collections.Counter()
    detail = collections.defaultdict(list)
    for f in FILES:
        try:
            t = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if "m_fontAsset" not in t:
            continue
        for m in re.finditer(r"m_fontAsset: \{fileID: \d+, guid: (\w+)", t):
            g = m.group(1)
            usage[g] += 1
            detail[g].append(os.path.relpath(f, ROOT))
    print("%-34s %6s  %s" % ("font asset", "refs", "files"))
    for g, c in usage.most_common():
        name = FONTS.get(g, g)
        files = sorted(set(detail[g]))
        print("%-34s %6d  %d 个文件: %s" % (
            name, c, len(files), ", ".join(files[:4]) + (" …" if len(files) > 4 else "")))
    unknown = [g for g in usage if g not in FONTS]
    if unknown:
        print("\n未识别字体 guid：", unknown)


if __name__ == "__main__":
    scan()
