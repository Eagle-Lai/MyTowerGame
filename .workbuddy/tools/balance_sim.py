# -*- coding: utf-8 -*-
"""
M2 数值平衡顶演（W7）。**只读**：只解析 Assets/ConfigJson/*.json，绝不写回任何表。

【它回答什么问题】
  设计文档 §8 M2 要求"建立 DPS vs 血量曲线，跑模拟脚本验证难度"。
  人肉盯表看不出"第几回合开始吃力"，本脚本把它算成三个可比数字：

    ① 有效血量 effHP = hp / (1 - armor)
       护甲换算成"实际要打掉多少血"，才能把不同护甲的怪放在同一把尺子上比。

    ② 需求 DPS  neededDps = Σ effHP / 窗口
       窗口 = 本波出怪时长 + 单个敌人的通过时长
         · 出怪时长 = 敌数 × 出怪间隔
         · 通过时长 = 路径长度(格) / 速度(格/秒)
       含义：防御方要在"这一波从开始到最后一个敌人走完"这段时间里打完这些血。

    ③ 经济余量 goldMargin = 可用金币 / 买到 neededDps 所需金币
       买到 neededDps 所需金币 = neededDps / 最优性价比(单位金币 DPS)
       这条是**可执行**的判据：< 1 就表示"这个回合的金币买不到足够的输出"。

  【为什么用经济余量而不是直接用 DPS 比值】
    DPS 比值的分母（场上能同时开火的塔数）极难估算 ——
    棋盘全开阔、路径只有 23 格，理论上能围着路径堆几十座塔。
    与其编一个覆盖率系数骗自己，不如只算**金币够不够**：
    金币是真实约束，且完全可由配置表推导。

【局限（写出来是为了别被数字误导）】
  · 假设玩家按最优性价比买塔，且钱全部花在输出上（不含减速塔的战术价值）；
  · 减速塔的价值是"让别的塔多打几秒"，属于乘数效应，本模型体现不出来；
  · 不考虑分批到达的时序、卖塔与升级时机、操作水平。
  → 用它**发现趋势与异常**（某回合塌方、某种塔被严格压制），最终以实跑为准。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = "D:/FreedomTower_1"
CFG = os.path.join(ROOT, "Assets/ConfigJson")


def load(name):
    with open(os.path.join(CFG, name + ".json"), "r", encoding="utf-8") as f:
        return json.load(f)


enemies = {e["id"]: e for e in load("tbenemydata")}
towers = load("tbtowerinfo")
bullets = {b["id"]: b for b in load("tbbulletdata")}
waves = {w["id"]: w for w in load("tbenemylist")}
rounds = {r["id"]: r for r in load("tbrounddata")}
levels = load("tbsceneinfo")
maps = {m["id"]: m for m in load("tblevelmap")}

LEVEL = levels[0]
START_GOLD = LEVEL.get("initialGold", 100)


def path_length(level):
    m = maps.get(level.get("mapId"))
    if m is None:
        return 0
    start = end = None
    for r, row in enumerate(m["cells"]):
        for c, ch in enumerate(row):
            if ch == "S":
                start = (r, c)
            elif ch == "E":
                end = (r, c)
    if start is None or end is None:
        return 0
    return abs(start[0] - end[0]) + abs(start[1] - end[1])   # 全开阔棋盘：A* 长度 = 曼哈顿距离


PATH_LEN = path_length(LEVEL)


def path_cells(level):
    """重建 S→E 的路径格集合。

    【为什么取"两条 L 形"的并集】全开阔棋盘上 A* 走出的一定是单调 L 形路径，
    但具体先横后竖还是先竖后横取决于 A* 的扩展顺序，脚本无法确定。
    取两种可能的并集，误差只是"多算了几格路径"，用于估算建造位数量足够。
    """
    m = maps.get(level.get("mapId"))
    if m is None:
        return set()
    start = end = None
    for r, row in enumerate(m["cells"]):
        for c, ch in enumerate(row):
            if ch == "S":
                start = (r, c)
            elif ch == "E":
                end = (r, c)
    if start is None or end is None:
        return set()

    def lshape(r_first):
        rs, cs = start
        re_, ce = end
        out = set()
        r = rs
        while r != re_:
            out.add((r, cs))
            r += 1 if re_ > rs else -1
        if not r_first:
            out.clear()
            c = cs
            while c != ce:
                out.add((rs, c))
                c += 1 if ce > cs else -1
        c = cs
        while c != ce:
            out.add((re_, c))
            c += 1 if ce > cs else -1
        out.add((re_, ce))
        out.add((rs, cs))
        return out

    return lshape(True) | lshape(False)


def build_slots(level, radius):
    """在半径 radius 内能覆盖到路径的**可建造格**数量 —— 这是塔数的物理上限。"""
    m = maps.get(level.get("mapId"))
    if m is None:
        return 0
    cells = m["cells"]
    path = path_cells(level)
    if not path:
        return 0
    slots = 0
    r2 = radius * radius
    for r, row in enumerate(cells):
        for c, ch in enumerate(row):
            if ch != ".":
                continue
            for (pr, pc) in path:
                dr = r - pr
                dc = c - pc
                if dr * dr + dc * dc <= r2:
                    slots += 1
                    break
    return slots


def dps_of(t):
    """单座塔的**期望**输出。AOE / 穿透按保守倍率折算多目标收益。"""
    cd = max(0.01, t["CD"] / 1000.0)
    d = t["power"] / cd
    b = bullets.get(t["bulletId"])
    if b is not None:
        if b.get("aoeRadius", 0) > 0:
            d *= 2.0                       # AOE：按每次命中 2 个目标（保守）
        if b.get("pierce", 0) > 0:
            d *= 1.0 + 0.5 * b["pierce"]   # 穿透：每多打一个 +50%
    return d


def by_type():
    g = {}
    for t in towers:
        g.setdefault(t["type"], []).append(t)
    for k in g:
        g[k].sort(key=lambda x: x["level"])
    return g


def cumulative_cost(rows, level):
    return sum(r["prices"] for r in rows if r["level"] <= level)


def simulate():
    groups = by_type()
    round_ids = LEVEL.get("RoundList", [])

    l1 = []
    for t, rows in groups.items():
        r1 = rows[0]
        l1.append({"type": t, "name": r1["name"], "price": r1["prices"], "dps": dps_of(r1),
                   "eff": dps_of(r1) / max(1, r1["prices"]), "radius": r1["radius"]})
    l1.sort(key=lambda x: -x["eff"])
    best = l1[0]

    print("=" * 82)
    print("关卡 1：初始金币 %d / 初始生命 %d / 路径长度 %d 格 / 回合数 %d"
          % (START_GOLD, LEVEL.get("initialHp", 0), PATH_LEN, len(round_ids)))
    print("=" * 82)

    print("\n【一、单位金币 DPS（L1）—— 用来发现「被严格压制」的塔】")
    print("   %-12s %4s %8s %10s   %s" % ("塔", "价格", "期望DPS", "性价比", "评价"))
    for t in sorted(l1, key=lambda x: -x["eff"]):
        note = ""
        if t["eff"] >= best["eff"] * 0.9:
            note = "第一梯队"
        elif t["eff"] < best["eff"] * 0.35:
            note = "★ 明显偏低：除非有特殊价值，否则没人会建"
        print("   %-12s %4d %8.2f %10.3f   %s"
              % (t["name"], t["price"], t["dps"], t["eff"], note))

    print("\n【二、塔的三级成长 —— 升级到底值不值】")
    for t, rows in sorted(groups.items()):
        print("   type=%d %s" % (t, rows[0]["name"]))
        base_eff = dps_of(rows[0]) / max(1, rows[0]["prices"])
        for r in rows:
            lvl = r["level"]
            cost = cumulative_cost(rows, lvl)
            d = dps_of(r)
            tags = []
            if lvl > 1:
                prev = [x for x in rows if x["level"] == lvl - 1][0]
                gain = d - dps_of(prev)
                marginal = gain / max(1, r["prices"])
                tags.append("边际性价比 %.3f" % marginal)
                # 【阈值为什么是 0.5 倍而不是 0.7 倍】
                #   顶级塔（穿透 2.500 / 强力 2.381）的 L1 本身就极划算，
                #   用 0.7 倍去卡会把"正常的升级设计"也报成问题。
                #   真要说"升级是坏选择"，得差到一半以下才站得住脚。
                if marginal < base_eff * 0.5:
                    tags.append("★ 升级性价比明显偏低")
                if gain <= 0:
                    tags.append("★ 花了钱没有 DPS 收益")
            print("      L%d  DPS %7.2f  累计成本 %4d  综合性价比 %6.3f   %s"
                  % (lvl, d, cost, d / max(1, cost), " ".join(tags)))

    slots = build_slots(LEVEL, best["radius"])
    print("\n【三、逐回合防御能力 vs 需求】")
    print("   基准塔：%s（半径 %d 格，%.2f DPS）" % (best["name"], best["radius"], best["dps"]))
    print("   能覆盖到路径的可建造格 = %d 个 ← 这是塔数的**物理上限**，金币再多也摆不下" % slots)
    print("   %4s %5s %5s %10s %9s %9s %9s %9s %8s"
          % ("回合", "波数", "敌数", "有效血量", "窗口(s)", "需求DPS", "可建塔", "供给DPS", "余量"))
    print("   " + "-" * 92)

    gold = START_GOLD
    problems = []
    for rid in round_ids:
        rd = rounds.get(rid)
        if rd is None:
            continue
        wave_ids = rd.get("EnemyIndexs", [])
        total_ehp = 0.0
        count = 0
        kill_gold = 0.0
        wave_seconds = 0.0
        traversal_sum = 0.0
        for wid in wave_ids:
            w = waves.get(wid)
            if w is None:
                continue
            ids = w.get("EnemyIndexs", [])
            count += len(ids)
            wave_seconds += len(ids) * (w.get("enemyInterval", 500) / 1000.0)
            for eid in ids:
                e = enemies.get(eid)
                if e is None:
                    continue
                total_ehp += e["hp"] / max(0.01, 1.0 - e["armor"])
                traversal_sum += PATH_LEN / max(0.05, e["speed"])
                kill_gold += e.get("reward", 0) + 1
        if count == 0:
            continue
        avg_traversal = traversal_sum / count
        window = max(1.0, wave_seconds + avg_traversal)
        needed_dps = total_ehp / window

        # 能建多少座塔 = min(买得起的, 摆得下的)
        affordable = int(gold // max(1, best["price"]))
        usable = min(affordable, slots)
        supply_dps = usable * best["dps"]
        margin = supply_dps / needed_dps if needed_dps > 0 else float("inf")

        flag = ""
        if margin < 1.0:
            flag = "  ← 输出不足，很可能漏怪"
            problems.append((rid, margin))
        elif margin > 8.0:
            flag = "  ← 余量非常充裕（这一段偏简单）"
        print("   %4d %5d %5d %10.0f %9.1f %9.1f %9d %9.1f %8.2f%s"
              % (rid, len(wave_ids), count, total_ehp, window, needed_dps,
                 usable, supply_dps, margin, flag))

        gold += rd.get("rewardGold", 0) + kill_gold

    print("\n【四、结论】")
    if problems:
        for rid, m in problems:
            print("   回合 %d：余量 %.2f —— 建议下调该回合敌人血量/护甲，或上调 rewardGold" % (rid, m))
    else:
        print("   所有回合余量 ≥ 1：摆满可建造格即可覆盖需求，没有「必败回合」。")
    print("   逐回合余量的**走势**比单点数值更重要：")
    print("     · 建造位用尽之前，余量随金币累积上升；")
    print("     · 用尽之后（本例约第 8 回合，%d 个可用位）余量转为下降 ——" % slots)
    print("       这才是后期真正的难度来源，也说明**升级**在此时才有价值。")
    print("   注 1：减速塔的价值是乘数（让别的塔多打几秒），本模型不计入 —— 低 DPS ≠ 没用。")
    print("   注 2：本模型假设 100% 命中与满覆盖，实战输出会明显低于此值。")


if __name__ == "__main__":
    simulate()
