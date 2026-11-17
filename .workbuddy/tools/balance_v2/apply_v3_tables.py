#!/usr/bin/env python3
"""数值体系 V3 落表（用户 2026-11-16 授权「全部关卡应用」，并同意直接铺到全部关卡）。

基准：git tag「L01关卡数值定稿！！！」（commit b27d9c3）。
  · L01：EnemyData / EnemyList / RoundData / TowerInfo / BulletData / LevelRules 六张表整文件恢复为 tag 原样。
  · L02–L30：
      TowerInfo / BulletData / LevelRules —— 整文件恢复为 tag 原样（tag 时 30 关同值；不含地图与空中出生点）
      RoundData   25 行：EnemyIndexs（单组）/ interval=0 / rewardGold / waveType（行 id 不变）
      EnemyList   数据行整体替换：每波一组，序列与 L01 定稿逐只对应，间隔同 L01
      EnemyData   数据行整体替换：属性同 L01 定稿，血量 × 本图地面/空中系数，赏金 × 经济系数 k，外观按本关挑选
不改：SceneInfo、LevelMap（含 2026-11-13 后的地图与空中出生点列）、WaveTuning、Global、代码。

用法：python apply_v3_tables.py --dry-run | --apply [--resume]
"""
import argparse, io, json, pathlib, shutil, subprocess, sys, time
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[3]
LV = ROOT / "Luban/Config/Datas/Levels"
PLAN = ROOT / "Docs/BalanceV2/v3/plan_v3.json"
BACKUP = ROOT / "Docs/BalanceV2/backup_20261116_before_v3"
TAG = "L01关卡数值定稿！！！"
RESTORE_ALL = ("TowerInfo", "BulletData", "LevelRules")
RESTORE_L01 = ("EnemyData", "EnemyList", "RoundData")
HDR, DATA0 = 1, 4


def hdr(ws):
    return {ws.cell(HDR, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(HDR, c).value}


def data_rows(ws):
    c = hdr(ws)["id"]
    return [r for r in range(DATA0, ws.max_row + 1) if ws.cell(r, c).value not in (None, "")]


def tag_bytes(rel):
    return subprocess.run(["git", "show", f"{TAG}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout


def write_retry(path, data, tries=20):
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


def save_retry(wb, path):
    buf = io.BytesIO(); wb.save(buf); write_retry(path, buf.getvalue())


def replace_rows(ws, rows):
    h = hdr(ws)
    for r in range(DATA0, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(r, c).value = None
    for i, row in enumerate(rows):
        for k, v in row.items():
            ws.cell(DATA0 + i, h[k]).value = v


def main():
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true"); g.add_argument("--apply", action="store_true")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    plan = {p["level"]: p for p in json.loads(PLAN.read_text(encoding="utf-8"))}
    if sorted(plan) != list(range(1, 31)):
        raise SystemExit(f"plan 关卡不完整：{sorted(plan)}")
    if a.apply:
        if BACKUP.exists() and not a.resume:
            raise SystemExit(f"备份目录已存在：{BACKUP}（中断续写请加 --resume）")
        if not BACKUP.exists():
            shutil.copytree(LV, BACKUP, ignore=shutil.ignore_patterns("*.bak*", "*.meta"))
    report, fails = [], []
    for L in range(1, 31):
        d = LV / f"L{L:02d}"; rel = f"Luban/Config/Datas/Levels/L{L:02d}"
        done = []
        # ① 整文件恢复为 tag 原样
        for t in RESTORE_ALL + (RESTORE_L01 if L == 1 else ()):
            data = tag_bytes(f"{rel}/{t}.xlsx")
            if (d / f"{t}.xlsx").read_bytes() != data:
                done.append(f"{t}=tag")
                if a.apply:
                    write_retry(d / f"{t}.xlsx", data)
        # ② L02–L30 换算后的出怪
        if L != 1:
            p = plan[L]
            si = openpyxl.load_workbook(d / "SceneInfo.xlsx").active
            rl = [int(x) for x in str(si.cell(DATA0, hdr(si)["RoundList"]).value).split(",")]
            byw = {g["wave"]: g for g in p["groups"]}
            if len(rl) != 25 or sorted(byw) != list(range(1, 26)):
                raise SystemExit(f"L{L:02d} RoundList 不是 25 波")   # 按波序对应：第 w 波 = 本关 RoundList 第 w 个 roundId
            wb_r = openpyxl.load_workbook(d / "RoundData.xlsx"); ws = wb_r.active; h = hdr(ws)
            rowof = {ws.cell(r, h["id"]).value: r for r in data_rows(ws)}
            for w in range(1, 26):
                gp = byw[w]; r = rowof[rl[w - 1]]
                ws.cell(r, h["EnemyIndexs"]).value = str(gp["id"]); ws.cell(r, h["interval"]).value = 0
                ws.cell(r, h["rewardGold"]).value = gp["rewardGold"]; ws.cell(r, h["waveType"]).value = gp["waveType"]
            wb_l = openpyxl.load_workbook(d / "EnemyList.xlsx")
            replace_rows(wb_l.active, [{"id": g["id"], "EnemyIndexs": ",".join(map(str, g["enemies"])), "interval": 0,
                                        "enemyInterval": g["enemyIntervalMs"], "desc": f"V3 L{L:02d} W{g['wave']}（序列同 tag L01）"} for g in p["groups"]])
            wb_e = openpyxl.load_workbook(d / "EnemyData.xlsx")
            cols = hdr(wb_e.active)
            replace_rows(wb_e.active, [{k: v for k, v in e.items() if k in cols} for e in p["enemies"]])
            done += ["RoundData", f"EnemyList={len(p['groups'])}组", f"EnemyData={len(p['enemies'])}行"]
            if a.apply:
                save_retry(wb_r, d / "RoundData.xlsx"); save_retry(wb_l, d / "EnemyList.xlsx"); save_retry(wb_e, d / "EnemyData.xlsx")
                # 回读
                ws = openpyxl.load_workbook(d / "EnemyData.xlsx").active; h = hdr(ws)
                if len(data_rows(ws)) != len(p["enemies"]): fails.append(f"L{L:02d} EnemyData 行数")
                for i, e in enumerate(p["enemies"]):
                    for k in ("id", "hp", "speed", "reward", "isFlying", "resName"):
                        if ws.cell(DATA0 + i, h[k]).value != e[k]: fails.append(f"L{L:02d} EnemyData 行{DATA0 + i} {k}"); break
                ws = openpyxl.load_workbook(d / "EnemyList.xlsx").active
                if len(data_rows(ws)) != len(p["groups"]): fails.append(f"L{L:02d} EnemyList 行数")
        if a.apply:
            for t in RESTORE_ALL + (RESTORE_L01 if L == 1 else ()):
                if (d / f"{t}.xlsx").read_bytes() != tag_bytes(f"{rel}/{t}.xlsx"): fails.append(f"L{L:02d} {t} 未与 tag 一致")
        report.append({"level": L, "changes": done}); print(f"L{L:02d} " + " ".join(done), flush=True)
    out = ROOT / "Docs/BalanceV2/v3" / ("apply_report.json" if a.apply else "dryrun_report.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if fails:
        print("回读校验失败：", *fails[:40], sep="\n"); sys.exit(1)
    print(("已写入并回读通过" if a.apply else "演练完成（未写入）") + f"；明细 {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
