#!/usr/bin/env python3
"""数值体系 V2 落表（用户 2026-11-15 授权「全部关卡应用」）。

输入：Docs/BalanceV2/sim/table_plan.json（RefSim 生成）。
范围（逐关 L01–L30，仅以下表/字段）：
  TowerInfo   9 行：radius / power / CD / prices / sellPrice(=累计投入) / effectValue / canAttackAir / airDamageScale / desc
  BulletData  范围塔引用的 3 行：aoeRadius
  LevelRules  sellRefundRate = 0.7
  LevelMap    新增列 airSpawnRow / airSpawnCol（-1 = 沿用 S）
  RoundData   25 行：EnemyIndexs(出怪组) / interval=0 / rewardGold / waveType（行 id 不变）
  EnemyList   数据行整体替换为新出怪组（用户授权一波拆多组）
  EnemyData   数据行整体替换为新怪物行（用户授权删除未引用旧行；外观字段沿用本关同角色旧行）
不改：SceneInfo（initialGold=100、initialHp、RoundList）、地图 cells、WaveTuning、Global。

用法：
  python apply_v2_tables.py --dry-run     只打印改动清单
  python apply_v2_tables.py --apply       备份 → 写入 → 回读校验
"""
import argparse, json, pathlib, shutil, sys, datetime, time, io
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[3]
LV = ROOT / "Luban/Config/Datas/Levels"
PLAN = ROOT / "Docs/BalanceV2/sim/table_plan.json"
BACKUP = ROOT / "Docs/BalanceV2/backup_20261115_before_v2.3"

# 02_全局参数.md（与 RefSim TowerDef 同值）：(radius, power, CD ms, 增量价, effectValue, canAttackAir)
TOWER = {
    (1, 1): (2.00, 8, 800, 20, 0, 1), (1, 2): (2.25, 20, 800, 30, 0, 1), (1, 3): (2.50, 44, 800, 50, 0, 1),
    (2, 1): (2.00, 12, 1500, 30, 0, 0), (2, 2): (2.10, 30, 1500, 40, 0, 0), (2, 3): (2.20, 60, 1500, 60, 0, 0),
    (3, 1): (2.00, 0, 250, 25, 0.20, 1), (3, 2): (2.25, 0, 250, 35, 0.30, 1), (3, 3): (2.50, 0, 250, 50, 0.40, 1),
}
AOE = {1: 0.90, 2: 1.05, 3: 1.20}
SELL_RATE = 0.7
HDR = 1          # 表头行
DATA0 = 4        # 第一条数据行


def hdr(ws):
    return {ws.cell(HDR, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(HDR, c).value}


def data_rows(ws, key="id"):
    c = hdr(ws)[key]
    return [r for r in range(DATA0, ws.max_row + 1) if ws.cell(r, c).value not in (None, "")]


def snapshot(ws):
    return {(r, c): ws.cell(r, c).value for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)}


class Level:
    def __init__(self, plan):
        self.p = plan; self.L = plan["level"]; self.d = LV / f"L{self.L:02d}"
        self.wb = {}; self.changes = []; self.whitelist = {}

    def ws(self, t):
        if t not in self.wb:
            self.wb[t] = openpyxl.load_workbook(self.d / f"{t}.xlsx")
        return self.wb[t].active

    def set(self, t, r, col, new):
        ws = self.ws(t); c = hdr(ws)[col] if isinstance(col, str) else col
        old = ws.cell(r, c).value
        self.whitelist.setdefault(t, set()).add((r, c))
        if old != new and not (isinstance(old, (int, float)) and isinstance(new, (int, float)) and abs(old - new) < 1e-9):
            self.changes.append((t, r, ws.cell(HDR, c).value, old, new)); ws.cell(r, c).value = new

    # ------------------------------------------------------------------ 定点表
    def towers(self):
        ws = self.ws("TowerInfo"); h = hdr(ws); cum = {}
        for r in data_rows(ws):
            t, lv = ws.cell(r, h["type"]).value, ws.cell(r, h["level"]).value
            rad, pw, cd, price, eff, air = TOWER[(t, lv)]
            cum[(t, lv)] = cum.get((t, lv - 1), 0) + price
            for col, v in (("radius", rad), ("power", pw), ("CD", cd), ("prices", price), ("sellPrice", cum[(t, lv)]),
                           ("effectValue", eff), ("canAttackAir", air), ("airDamageScale", 1)):
                self.set("TowerInfo", r, col, v)
            self.set("TowerInfo", r, "desc", f"V2 2026-11-15; incremental {price}; cumulative {cum[(t, lv)]}; sell = cumulative x sellRefundRate {SELL_RATE}")
            if t == 2:
                self.bullet(ws.cell(r, h["bulletId"]).value, AOE[lv])

    def bullet(self, bid, aoe):
        ws = self.ws("BulletData"); h = hdr(ws)
        rows = [r for r in data_rows(ws) if ws.cell(r, h["id"]).value == bid]
        if len(rows) != 1: raise SystemExit(f"L{self.L:02d} BulletData 找不到唯一 id={bid}")
        self.set("BulletData", rows[0], "aoeRadius", aoe)

    def rules(self):
        ws = self.ws("LevelRules"); rows = data_rows(ws)
        if len(rows) != 1: raise SystemExit(f"L{self.L:02d} LevelRules 行数 {len(rows)} != 1")
        self.set("LevelRules", rows[0], "sellRefundRate", SELL_RATE)

    def levelmap(self):
        ws = self.ws("LevelMap"); h = hdr(ws)
        for name, comment in (("airSpawnRow", "空中怪出生格的行（0 起，自上而下）；-1=沿用起点 S"),
                              ("airSpawnCol", "空中怪出生格的列（0 起，自左向右）；-1=沿用起点 S")):
            if name not in h:
                c = ws.max_column + 1
                for r, v in ((1, name), (2, "int"), (3, comment)):
                    self.set("LevelMap", r, c, v)
                h = hdr(ws)
        rows = data_rows(ws)
        if len(rows) != 1: raise SystemExit(f"L{self.L:02d} LevelMap 行数 {len(rows)} != 1")
        a = self.p.get("airSpawn") or [-1, -1]
        self.set("LevelMap", rows[0], "airSpawnRow", a[0]); self.set("LevelMap", rows[0], "airSpawnCol", a[1])

    def rounds(self):
        si = self.ws("SceneInfo"); rl = [int(x) for x in str(si.cell(DATA0, hdr(si)["RoundList"]).value).split(",")]
        ws = self.ws("RoundData"); h = hdr(ws)
        byid = {ws.cell(r, h["id"]).value: r for r in data_rows(ws)}
        if len(rl) != 25 or set(rl) != set(byid): raise SystemExit(f"L{self.L:02d} RoundList 与 RoundData 不一致")
        for w in self.p["waves"]:
            r = byid[rl[w["wave"] - 1]]
            self.set("RoundData", r, "EnemyIndexs", ",".join(str(g["id"]) for g in w["groups"]))
            self.set("RoundData", r, "interval", 0)
            self.set("RoundData", r, "rewardGold", w["rewardGold"])
            self.set("RoundData", r, "waveType", 2 if w["hard"] else 1)

    # ------------------------------------------------------------------ 整体替换
    def replace(self, t, rows):
        ws = self.ws(t); old = data_rows(ws); h = hdr(ws)
        for r in range(DATA0, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).value = None
        for i, row in enumerate(rows):
            for k, v in row.items():
                ws.cell(DATA0 + i, h[k]).value = v
        self.changes.append((t, "*", "数据行整体替换", f"{len(old)} 行", f"{len(rows)} 行"))
        self.replaced = getattr(self, "replaced", {}); self.replaced[t] = rows

    def groups(self):
        rows = []
        for w in self.p["waves"]:
            for g in w["groups"]:
                rows.append({"id": g["id"], "EnemyIndexs": ",".join(map(str, g["enemies"])), "interval": 0,
                             "enemyInterval": g["enemyIntervalMs"], "desc": f"V2 L{self.L:02d} W{w['wave']} 组{g['id'] % 100} t0={g['firstT']}s"})
        self.replace("EnemyList", rows)

    def enemies(self):
        ws = self.ws("EnemyData"); h = hdr(ws); donor = {}
        for r in data_rows(ws):
            desc = str(ws.cell(r, h["desc"]).value or ""); fly = ws.cell(r, h["isFlying"]).value or 0
            role = next((p.split("=")[1] for p in desc.replace(" ", "").split(";") if p.startswith("role=")), None)
            look = {k: ws.cell(r, h[k]).value for k in ("name", "resName", "scale", "bodyRadius", "animController")}
            donor.setdefault((role, fly), look); donor.setdefault((None, fly), look)
            if role == "air" and look["resName"] != donor[("air", fly)]["resName"]: donor.setdefault(("air2", 1), look)
        rows = []
        for w in self.p["waves"]:
            for e in w["enemies"]:
                key = ("air2" if e["arche"] == "A2" else e["role"], e["fly"])
                look = donor.get(key) or donor.get((e["role"], e["fly"])) or donor[(None, e["fly"])]
                rows.append({"id": e["id"], "speed": e["speed"], "hp": e["hp"], "name": look["name"], "type": e["type"],
                             "interval": 100, "resName": look["resName"], "armor": e["armor"], "reward": e["reward"],
                             "damageToPlayer": e["leak"], "scale": look["scale"], "bodyRadius": look["bodyRadius"],
                             "isFlying": e["fly"], "animController": look["animController"],
                             "desc": f"V2 2026-11-15; arche={e['arche']}; role={e['role']}; level={self.L}; wave={w['wave']}", "levelId": self.L})
        self.replace("EnemyData", rows)

    # ------------------------------------------------------------------ 校验
    def verify(self, before):
        bad = []
        for t, wb in self.wb.items():
            ws = openpyxl.load_workbook(self.d / f"{t}.xlsx").active
            now = snapshot(ws); was = before[t]
            if t in getattr(self, "replaced", {}):
                h = hdr(ws); rows = self.replaced[t]
                for (r, c), v in was.items():
                    if r < DATA0 and now.get((r, c)) != v: bad.append(f"{t} 表头 {r},{c} 被改")
                for i, row in enumerate(rows):
                    for k, v in row.items():
                        got = ws.cell(DATA0 + i, h[k]).value
                        if got != v and not (v in ("", None) and got in ("", None)): bad.append(f"{t} 行{DATA0 + i} {k}: {got!r} != {v!r}")
                if len(data_rows(ws)) != len(rows): bad.append(f"{t} 数据行数 {len(data_rows(ws))} != {len(rows)}")
                continue
            wl = self.whitelist.get(t, set())
            for k in set(now) | set(was):
                if k in wl: continue
                if now.get(k) != was.get(k): bad.append(f"{t} 白名单外 {k}: {was.get(k)!r} -> {now.get(k)!r}")
            for (t2, r, col, old, new) in self.changes:
                if t2 != t or r == "*": continue
                c = hdr(ws)[col] if isinstance(col, str) and col in hdr(ws) else None
        return bad


def save_retry(wb, path, tries=20):
    """先写到内存再整体落盘；文件被同步/杀毒短暂占用（Errno 22/13）时等待重试，避免写出半截文件。"""
    buf = io.BytesIO(); wb.save(buf); data = buf.getvalue()
    for i in range(tries):
        try:
            with open(path, "r+b") as f:
                f.seek(0); f.write(data); f.truncate()
            return
        except OSError as e:
            if i == tries - 1:
                raise
            print(f"  文件被占用，{0.5 * (i + 1):.1f}s 后重试：{path.name}（{e.errno}）", flush=True)
            time.sleep(0.5 * (i + 1))


def main():
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true"); g.add_argument("--apply", action="store_true")
    ap.add_argument("--resume", action="store_true", help="上次写入被文件占用中断时使用：沿用已有备份目录作为改前基准")
    a = ap.parse_args()
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if sorted(p["level"] for p in plan) != list(range(1, 31)): raise SystemExit("plan 不是完整 30 关")
    report = []; failures = []
    if a.apply:
        if BACKUP.exists() and not a.resume: raise SystemExit(f"备份目录已存在：{BACKUP}（防止覆盖改前基准；中断续写请加 --resume）")
        if not BACKUP.exists(): shutil.copytree(LV, BACKUP, ignore=shutil.ignore_patterns("*.bak*", "*.meta"))
    for p in plan:
        lv = Level(p)
        tables = ["TowerInfo", "BulletData", "LevelRules", "LevelMap", "SceneInfo", "RoundData", "EnemyList", "EnemyData"]
        before = {t: snapshot(lv.ws(t)) for t in tables}
        lv.towers(); lv.rules(); lv.levelmap(); lv.rounds(); lv.groups(); lv.enemies()
        lv.wb.pop("SceneInfo")   # 只读
        if a.apply:
            for t, wb in lv.wb.items(): save_retry(wb, lv.d / f"{t}.xlsx")
            bad = lv.verify(before)
            failures += [f"L{lv.L:02d} {b}" for b in bad]
        cnt = {}
        for t, *_ in lv.changes: cnt[t] = cnt.get(t, 0) + 1
        report.append((lv.L, cnt, lv.changes))
        print(f"L{lv.L:02d} " + " ".join(f"{t}:{n}" for t, n in sorted(cnt.items())), flush=True)
    out = ROOT / "Docs/BalanceV2/sim" / ("apply_report.json" if a.apply else "dryrun_report.json")
    out.write_text(json.dumps([{"level": L, "counts": c, "changes": [list(map(str, x)) for x in ch]} for L, c, ch in report], ensure_ascii=False, indent=1), encoding="utf-8")
    if failures:
        print("\n回读校验失败：", *failures[:50], sep="\n"); sys.exit(1)
    print(f"\n{'已写入并回读通过' if a.apply else '演练完成（未写入）'}；明细 {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
