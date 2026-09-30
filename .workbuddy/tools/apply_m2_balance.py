# -*- coding: utf-8 -*-
"""
M2 数值平衡回调（W7）。依据 .workbuddy/tools/balance_sim.py 的输出调整 TowerInfo.xlsx 的 power。

【为什么只改 power，不改 CD / 价格】
  CD 与价格牵动"手感"（射速）与"经济门槛"（什么时候能起塔），
  而本次要解决的是纯粹的**性价比失衡**，改 power 是最小侵入的手段。

【本次修掉的两个实测问题】
  问题 1：激光塔被严格压制
    调整前 L1：40 金 / 28 DPS = 0.700 性价比，而普通塔是 1.667、穿透塔 2.500。
    激光既没有 AOE 也没有穿透，价格还更贵 —— 在"纯输出"这个维度上没有任何理由建它。
    调整后：40 金 / 48 DPS = 1.200，仍低于普通塔（这是有意的：瞬发命中不浪费输出，
    属于"贵一点但更稳"的定位），但不再是被碾压的选项。

  问题 2：所有塔的 L1→L2 升级都"不如再建一座 L1"
    边际性价比（每多花 1 金换来的 DPS）：
      普通 0.889 / 强力 0.812 / 减速 0.167 / 穿透 0.948 / 激光 0.200
    全都低于各自 L1 的综合性价比 → 玩家的最优解永远是"铺满 L1"，升级形同虚设。
    本次把各级 power 重排，使 L2/L3 的边际性价比回到 L1 的 0.6~1.0 倍区间：
    升级仍然是"用金币换空间与集中火力"，但不再是被严格压制的坏选择。

【幂等性】按 id 定位并直接赋值，重复执行结果一致。
"""
import os
import shutil
import sys
import datetime

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

ROOT = "D:/FreedomTower_1"
DATAS = os.path.join(ROOT, "Luban/Config/Datas")
BACKUP_ROOT = os.path.join(ROOT, ".workbuddy/backup")

# id -> (旧 power, 新 power, 说明)
POWER_CHANGES = {
    # 普通塔：L1 不动；L2 提到"边际性价比 > 1"，L3 保持
    2: (12, 14, "普通 L2：12→14，消除「不如再建一座 L1」"),
    3: (15, 15, "普通 L3：不变"),
    # 强力塔（AOE）
    5: (32, 38, "强力 L2：32→38"),
    6: (45, 50, "强力 L3：45→50"),
    # 减速塔（utility，DPS 本就该低，但不能低到没人建）
    7: (5, 8, "减速 L1：5→8（性价比 0.417→0.667）"),
    8: (7, 17, "减速 L2：7→17"),
    9: (10, 27, "减速 L3：10→27"),
    # 穿透塔
    11: (8, 10, "穿透 L2：8→10"),
    12: (11, 14, "穿透 L3：11→14"),
    # 激光塔（本次调整的重点）
    13: (14, 24, "激光 L1：14→24（性价比 0.700→1.200）"),
    14: (18, 50, "激光 L2：18→50"),
    15: (24, 78, "激光 L3：24→78"),
}


def backup():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, stamp, "Config", "Datas")
    os.makedirs(dst, exist_ok=True)
    src = os.path.join(DATAS, "TowerInfo.xlsx")
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(dst, "TowerInfo.xlsx"))
    return dst


def header_index(ws, name, header_row=1):
    for c in range(1, ws.max_column + 2):
        v = ws.cell(row=header_row, column=c).value
        if v is not None and str(v).strip() == name:
            return c
    return None


def main():
    wb = openpyxl.load_workbook(os.path.join(DATAS, "TowerInfo.xlsx"))
    ws = wb.active
    id_c = header_index(ws, "id")
    power_c = header_index(ws, "power")

    changed = 0
    for r in range(4, ws.max_row + 1):
        v = ws.cell(row=r, column=id_c).value
        if v is None:
            continue
        tid = int(v)
        if tid not in POWER_CHANGES:
            continue
        old, new, note = POWER_CHANGES[tid]
        cur = ws.cell(row=r, column=power_c).value
        if cur is None:
            continue
        if int(cur) != old and int(cur) != new:
            print("  ! id=%d 现值 %s 与预期旧值 %d 不符，仍按新值 %d 写入" % (tid, cur, old, new))
        ws.cell(row=r, column=power_c).value = new
        changed += 1
        print("  id=%-3d power %3s → %-3d  %s" % (tid, cur, new, note))

    wb.save(os.path.join(DATAS, "TowerInfo.xlsx"))
    print("共修改 %d 行" % changed)


if __name__ == "__main__":
    print("已备份到:", backup())
    main()
    print("OK")
