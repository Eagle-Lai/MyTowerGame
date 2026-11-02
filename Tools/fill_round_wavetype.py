# -*- coding: utf-8 -*-
"""
fill_round_wavetype.py —— 给 L01..L30 的 RoundData.xlsx 补一列 waveType（一次性工具）

================================ 授权与边界 ================================
本次批量写表是用户 2026-11-02 明确授权的**单次、单列**操作：
  · 只写 `waveType` 一列（只在表尾追加，或在已存在时覆盖该列的值）；
  · 不改任何现有数值（id / EnemyIndexs / interval / name / rewardGold 一律不动）；
  · 不新增、不删除、不重排任何数据行。
与 AGENTS.md「禁止脚本批量改写关卡配置表」的关系：
  该禁令针对的是**数值改写**（hp / 金币 / 出怪等）。本脚本的授权**仅限本次、仅限该列**，
  不构成对其他列或其他批次的长期授权。需要再跑一次前应先重新取得用户确认。
===========================================================================

为什么不能用表行号推断波次序号：
  L01 / L02 的 RoundData 表内行顺序与 SceneInfo.RoundList 顺序**不一致**
  （L01 的 RoundList 是 1..20,401..405，而表里 401 排在 13..20 之前）。
  唯一可靠的序号来源是 `name` 里的 N（格式「第 N/25 波」），并用
  `RoundList` 的位置做交叉校验，两者不一致立即 abort。

用法：
    python Tools/fill_round_wavetype.py --dry-run      # 只打印报告，不写盘
    python Tools/fill_round_wavetype.py --apply        # 写入（自动备份）
    python Tools/fill_round_wavetype.py --verify       # 逐格对比 .bak，确认只改了 waveType
    python Tools/fill_round_wavetype.py --apply --every 5   # 默认就是 5
"""

import argparse
import os
import re
import shutil
import sys
import tempfile

import openpyxl

# ---------------------------------------------------------------------------
# 路径与常量
# ---------------------------------------------------------------------------
LEVELS_ROOT = os.path.join("Luban", "Config", "Datas", "Levels")
LEVELS = ["L%02d" % i for i in range(1, 31)]

COL_WAVE_TYPE = "waveType"
COL_TYPE_ROW = "int"
COL_NOTE = "波型 1=普通 2=困难（工具统一填写，禁止留空/填0）"

ROW_HEADER = 1
ROW_TYPE = 2
ROW_NOTE = 3
ROW_DATA_START = 4

NAME_RE = re.compile(r"第\s*(\d+)\s*/")
BAK_SUFFIX = ".bak_20261102_wavetype"

EXPECTED_LEVELS = 30
EXPECTED_ROWS_PER_LEVEL = 25
EXPECTED_TOTAL_ROWS = 750


class Abort(Exception):
    """整批中止（不写盘）。"""


def log(msg=""):
    print(msg)


def _stdout_utf8():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 读取
# ---------------------------------------------------------------------------
def read_roundlist(level_dir):
    """读 SceneInfo.xlsx 的 RoundList（权威波次顺序）。"""
    path = os.path.join(level_dir, "SceneInfo.xlsx")
    if not os.path.isfile(path):
        raise Abort("缺少文件：%s" % path)
    try:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    except Exception as exc:
        raise Abort("打不开 %s：%s" % (path, exc))
    try:
        ws = wb["Sheet1"] if "Sheet1" in wb.sheetnames else wb.worksheets[0]
        rows = list(ws.iter_rows(min_row=ROW_HEADER, max_row=ROW_DATA_START, values_only=True))
        if len(rows) < ROW_DATA_START:
            raise Abort("%s 行数不足（需要表头 3 行 + 1 行数据）" % path)
        header = [str(v).strip() if v is not None else "" for v in rows[0]]
        if "RoundList" not in header:
            raise Abort("%s 表头缺少 RoundList 列：%r" % (path, header))
        idx = header.index("RoundList")
        data = rows[ROW_DATA_START - 1]
        raw = data[idx] if idx < len(data) else None
        if raw is None or str(raw).strip() == "":
            raise Abort("%s 的 RoundList 为空" % path)
        order = [int(x) for x in str(raw).replace("，", ",").split(",") if str(x).strip() != ""]
        if not order:
            raise Abort("%s 的 RoundList 解析后为空" % path)
        return order
    finally:
        wb.close()


def load_rounddata(level_dir):
    """读 RoundData.xlsx，返回 (workbook, worksheet, header_index_map, data_rows)。"""
    path = os.path.join(level_dir, "RoundData.xlsx")
    if not os.path.isfile(path):
        raise Abort("缺少文件：%s" % path)
    try:
        wb = openpyxl.load_workbook(path)
    except Exception as exc:
        raise Abort("打不开 %s：%s" % (path, exc))
    ws = wb["Sheet1"] if "Sheet1" in wb.sheetnames else wb.worksheets[0]

    header = [ws.cell(ROW_HEADER, c).value for c in range(1, ws.max_column + 1)]
    names = [str(v).strip() if v is not None else "" for v in header]
    for required in ("id", "name"):
        if required not in names:
            wb.close()
            raise Abort("%s 表头缺少 %s 列：%r" % (path, required, names))
    idx = {"id": names.index("id") + 1, "name": names.index("name") + 1}

    # 现有最后一列（以表头行最后一个非空单元格为准；L01 的 max_column 含空列，不能直接用）
    last_col = 0
    for c in range(1, ws.max_column + 1):
        if ws.cell(ROW_HEADER, c).value is not None and str(ws.cell(ROW_HEADER, c).value).strip() != "":
            last_col = c
    if last_col == 0:
        wb.close()
        raise Abort("%s 表头行全空" % path)

    return wb, ws, idx, last_col, names


def parse_level(level, every):
    """解析一关，返回 dict（含每行 waveType）。只读，不写盘。"""
    level_dir = os.path.join(LEVELS_ROOT, level)
    if not os.path.isdir(level_dir):
        raise Abort("关卡目录不存在：%s" % level_dir)

    order = read_roundlist(level_dir)
    wb, ws, idx, last_col, header_names = load_rounddata(level_dir)
    try:
        pos = {rid: i + 1 for i, rid in enumerate(order)}

        existing_col = header_names.index(COL_WAVE_TYPE) + 1 if COL_WAVE_TYPE in header_names else None
        target_col = existing_col if existing_col is not None else last_col + 1

        rows = []
        for r in range(ROW_DATA_START, ws.max_row + 1):
            rid = ws.cell(r, idx["id"]).value
            if rid is None or str(rid).strip() == "":
                continue
            try:
                rid = int(rid)
            except (TypeError, ValueError):
                raise Abort("%s 第 %d 行 id 非整数：%r" % (level, r, rid))
            nm = ws.cell(r, idx["name"]).value
            m = NAME_RE.search(str(nm) if nm is not None else "")
            if not m:
                raise Abort("%s 第 %d 行 name 无法解析波次序号：%r" % (level, r, nm))
            n = int(m.group(1))
            if rid not in pos:
                raise Abort("%s 的 id=%s 不在 RoundList 中" % (level, rid))
            if pos[rid] != n:
                raise Abort("%s id=%s 的 name 序号(%d) 与 RoundList 位置(%d) 不一致"
                            % (level, rid, n, pos[rid]))
            rows.append({"row": r, "id": rid, "n": n,
                         "waveType": 2 if n % every == 0 else 1})

        if len(rows) != EXPECTED_ROWS_PER_LEVEL:
            raise Abort("%s 数据行数为 %d，期望 %d" % (level, len(rows), EXPECTED_ROWS_PER_LEVEL))

        # name 序号必须覆盖 1..len(rows) 恰好一次
        ns = sorted(x["n"] for x in rows)
        if ns != list(range(1, len(rows) + 1)):
            raise Abort("%s 的 name 序号不是 1..%d 的排列：%r" % (level, len(rows), ns))

        # 报告里按波次序号升序排（表行顺序在 L01/L02 是乱的，直接输出会误导）
        hard = sorted(x["n"] for x in rows if x["waveType"] == 2)
        return {
            "level": level,
            "path": os.path.join(level_dir, "RoundData.xlsx"),
            "wb": wb,
            "ws": ws,
            "target_col": target_col,
            "existing": existing_col is not None,
            "rows": rows,
            "hard": hard,
            "total": len(rows),
        }
    except Exception:
        wb.close()
        raise


# ---------------------------------------------------------------------------
# 写盘
# ---------------------------------------------------------------------------
def apply_level(info):
    ws = info["ws"]
    col = info["target_col"]
    if not info["existing"]:
        ws.cell(ROW_HEADER, col, COL_WAVE_TYPE)
        ws.cell(ROW_TYPE, col, COL_TYPE_ROW)
        ws.cell(ROW_NOTE, col, COL_NOTE)
    for item in info["rows"]:
        ws.cell(item["row"], col, item["waveType"])
    info["wb"].save(info["path"])
    info["wb"].close()


def backup(path):
    bak = path + BAK_SUFFIX
    if os.path.exists(bak):
        return bak, False
    shutil.copy2(path, bak)
    return bak, True


def open_backup_as_workbook(bak_path):
    """openpyxl 只认 .xlsx/.xlsm 等扩展名，备份文件要先转成临时 .xlsx 才能读。"""
    tmp_dir = tempfile.mkdtemp(prefix="wavetype_bak_")
    tmp = os.path.join(tmp_dir, "book.xlsx")
    shutil.copy2(bak_path, tmp)
    return openpyxl.load_workbook(tmp, data_only=True), tmp_dir


# ---------------------------------------------------------------------------
# 校验（--verify）
# ---------------------------------------------------------------------------
def verify_level(info):
    """逐单元格比较 .bak 与当前文件：除 waveType 列外任何一格不同 → 失败。"""
    level = info["level"]
    path = info["path"]
    bak = path + BAK_SUFFIX
    if not os.path.isfile(bak):
        raise Abort("%s 缺少备份文件 %s，无法比对" % (level, bak))

    # openpyxl 按扩展名判断格式，.bak_xxx 会被拒；先复制成临时 .xlsx 再读
    wb_old, tmp = open_backup_as_workbook(bak)
    wb_new = openpyxl.load_workbook(path, data_only=True)
    try:
        ws_old = wb_old["Sheet1"] if "Sheet1" in wb_old.sheetnames else wb_old.worksheets[0]
        ws_new = wb_new["Sheet1"] if "Sheet1" in wb_new.sheetnames else wb_new.worksheets[0]
        col = info["target_col"]

        max_row = max(ws_old.max_row, ws_new.max_row)
        max_col = max(ws_old.max_column, ws_new.max_column)
        diffs = []
        for r in range(1, max_row + 1):
            for c in range(1, max_col + 1):
                if c == col:
                    continue
                a = ws_old.cell(r, c).value
                b = ws_new.cell(r, c).value
                if a != b:
                    diffs.append("R%dC%d 旧=%r 新=%r" % (r, c, a, b))
        if diffs:
            raise Abort("%s 出现 waveType 之外的改动：\n    %s" % (level, "\n    ".join(diffs[:10])))

        # waveType 列的值必须与期望一致
        bad = []
        for item in info["rows"]:
            v = ws_new.cell(item["row"], col).value
            try:
                v = int(v)
            except (TypeError, ValueError):
                bad.append("第 %d 行 waveType=%r（非整数）" % (item["row"], v))
                continue
            if v != item["waveType"]:
                bad.append("第 %d 行 waveType=%d（期望 %d）" % (item["row"], v, item["waveType"]))
        if bad:
            raise Abort("%s 的 waveType 值与期望不符：\n    %s" % (level, "\n    ".join(bad[:10])))

        return len(info["rows"])
    finally:
        wb_old.close()
        wb_new.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    _stdout_utf8()
    ap = argparse.ArgumentParser(description="给 RoundData.xlsx 补 waveType 列（一次性单列授权操作）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="只打印报告，不写盘")
    g.add_argument("--apply", action="store_true", help="写入（自动备份为 .bak_20261102_wavetype）")
    g.add_argument("--verify", action="store_true", help="逐格对比 .bak，确认只改了 waveType")
    ap.add_argument("--every", type=int, default=5, help="每 N 波一次困难波（默认 5）")
    args = ap.parse_args()

    if args.every <= 0:
        log("[错误] --every 必须为正整数")
        return 1

    mode = "DRY-RUN" if args.dry_run else ("APPLY" if args.apply else "VERIFY")
    log("=" * 78)
    log("fill_round_wavetype  mode=%s  every=%d  levels=%d" % (mode, args.every, len(LEVELS)))
    log("=" * 78)

    # ---- 阶段 1：只读解析全部 30 关（任何一处失败都 abort，不写盘） ----
    infos = []
    try:
        for level in LEVELS:
            infos.append(parse_level(level, args.every))
    except Abort as exc:
        for info in infos:
            info["wb"].close()
        log("[中止] %s" % exc)
        return 1

    total_rows = sum(i["total"] for i in infos)
    total_hard = sum(len(i["hard"]) for i in infos)
    if len(infos) != EXPECTED_LEVELS:
        log("[中止] 解析到 %d 关，期望 %d 关" % (len(infos), EXPECTED_LEVELS))
        return 1
    if total_rows != EXPECTED_TOTAL_ROWS:
        log("[中止] 总行数 %d，期望 %d" % (total_rows, EXPECTED_TOTAL_ROWS))
        return 1
    expected_hard = EXPECTED_TOTAL_ROWS // args.every
    if total_hard != expected_hard:
        log("[中止] 困难波行数 %d，期望 %d" % (total_hard, expected_hard))
        return 1

    # ---- 阶段 2：执行 ----
    exit_code = 0
    try:
        if args.verify:
            for info in infos:
                verify_level(info)
                info["wb"].close()
        elif args.apply:
            for info in infos:
                bak, created = backup(info["path"])
                apply_level(info)
                log("  [写入] %s  备份=%s%s" % (info["level"], os.path.basename(bak),
                                              "" if created else "（已存在，保留首次备份）"))
        else:
            for info in infos:
                info["wb"].close()
    except Abort as exc:
        log("[中止] %s" % exc)
        return 1
    except Exception as exc:
        log("[中止] 未预期异常：%r" % exc)
        return 1

    # ---- 阶段 3：报告 ----
    for info in infos:
        hard_txt = "/".join(str(n) for n in info["hard"])
        normal = info["total"] - len(info["hard"])
        log("%s 数据行=%d 困难波=[第%s波] 普通=%d 困难=%d  %s"
            % (info["level"], info["total"], hard_txt, normal, len(info["hard"]),
               "列已存在(覆盖)" if info["existing"] else "新追加列#%d" % info["target_col"]))

    log("-" * 78)
    log("处理关卡=%d/%d 总行数=%d 困难波=%d" % (len(infos), EXPECTED_LEVELS, total_rows, total_hard))

    if exit_code == 0 and (args.verify or args.apply or args.dry_run):
        log("[OK] %s 完成" % mode)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
