# -*- coding: utf-8 -*-
"""
把 Unity 地图编辑器导出的 .workbuddy/levelmap_export.json 写回 LevelMap.xlsx（M3-7）。

【为什么中间要隔一个文件，而不是让编辑器直接写 xlsx】
  工程里能在编辑器侧读写 Excel 的库（ClosedXML）只存在于 Luban 工具目录；
  把它引进 Assets/Editor 会污染编辑器程序集、也可能和 Unity 自带的
  Newtonsoft/OpenXml 版本打架。所以分工是：
      Unity 窗口只负责"画 + 校验" → 导出 json → 本脚本写 xlsx → Luban 导出成运行时数据。

【自检】写回前再验一遍：行长一致、S/E 各一个、S→E 可达。
  窗口里已经验过，但"导出的文件被手改过"是常有的事，这里再挡一次。
"""
import json
import os
import shutil
import sys
import datetime
from collections import deque

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

ROOT = "D:/FreedomTower_1"
EXPORT = os.path.join(ROOT, ".workbuddy/levelmap_export.json")
DATAS = os.path.join(ROOT, "Luban/Config/Datas")
BACKUP_ROOT = os.path.join(ROOT, ".workbuddy/backup")


def reachable(cells, cols, rows):
    sr = sc = er = ec = -1
    for r in range(rows):
        for c in range(cols):
            ch = cells[r][c]
            if ch == "S":
                sr, sc = r, c
            elif ch == "E":
                er, ec = r, c
    if sr < 0 or er < 0:
        return False, -1
    dist = {(sr, sc): 0}
    q = deque([(sr, sc)])
    while q:
        r, c = q.popleft()
        if (r, c) == (er, ec):
            return True, dist[(r, c)]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in dist and cells[nr][nc] not in "#X":
                dist[(nr, nc)] = dist[(r, c)] + 1
                q.append((nr, nc))
    return False, -1


def main():
    if not os.path.exists(EXPORT):
        raise SystemExit("找不到导出文件：%s\n请先在 Unity 里用「Tools ▸ 塔防 ▸ 地图编辑器」导出。" % EXPORT)

    with open(EXPORT, "r", encoding="utf-8") as f:
        data = json.load(f)

    level_id = int(data["levelId"])
    cols = int(data["cols"])
    rows = int(data["rows"])
    cells = list(data.get("cells") or [])
    desc = data.get("desc") or ""

    print("导出内容：关卡 %d，%d×%d" % (level_id, cols, rows))
    for line in cells:
        print("   " + line)

    problems = []
    if len(cells) != rows:
        problems.append("行数 %d != rows %d" % (len(cells), rows))
    for i, line in enumerate(cells):
        if len(line) != cols:
            problems.append("第 %d 行长度 %d != cols %d" % (i, len(line), cols))
    s_count = sum(line.count("S") for line in cells)
    e_count = sum(line.count("E") for line in cells)
    if s_count != 1:
        problems.append("起点 S 有 %d 个（必须 1 个）" % s_count)
    if e_count != 1:
        problems.append("终点 E 有 %d 个（必须 1 个）" % e_count)
    if not problems:
        ok, plen = reachable(cells, cols, rows)
        if not ok:
            problems.append("S→E 不可达")
        else:
            buildable = sum(line.count(".") for line in cells)
            print("\n校验通过：可建造格 %d，最短路径 %d 格" % (buildable, plen))

    if problems:
        for p in problems:
            print("  ✘ " + p)
        raise SystemExit("校验未通过，未写文件")

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, stamp, "Config", "Datas")
    os.makedirs(dst, exist_ok=True)
    shutil.copy2(os.path.join(DATAS, "LevelMap.xlsx"), os.path.join(dst, "LevelMap.xlsx"))
    print("已备份到:", dst)

    wb = openpyxl.load_workbook(os.path.join(DATAS, "LevelMap.xlsx"))
    ws = wb.active
    hdr = {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}

    target = None
    for r in range(4, ws.max_row + 1):
        v = ws.cell(row=r, column=hdr["id"]).value
        if v is not None and int(v) == level_id:
            target = r
            break
    if target is None:
        target = ws.max_row + 1
        ws.cell(row=target, column=hdr["id"]).value = level_id
        ws.cell(row=target, column=hdr["levelId"]).value = level_id

    ws.cell(row=target, column=hdr["cols"]).value = cols
    ws.cell(row=target, column=hdr["rows"]).value = rows
    ws.cell(row=target, column=hdr["cells"]).value = "|".join(cells)
    if desc:
        ws.cell(row=target, column=hdr["desc"]).value = desc

    wb.save(os.path.join(DATAS, "LevelMap.xlsx"))
    print("已写回 LevelMap.xlsx 的第 %d 行（关卡 %d）" % (target, level_id))
    print("")
    print("下一步：跑一次 Luban 导出，Unity 里才会看到新棋盘。")
    print("  （Unity 菜单：Tools ▸ 塔防 ▸ 3. 导出配置表（Luban））")


if __name__ == "__main__":
    main()
