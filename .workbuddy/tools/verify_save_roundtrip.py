#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关卡星级持久化端到端验证（用真实 SQLite 跑源码里的建表/读写语句）。

【为什么需要它】
  沙箱里跑不了 C#，于是"存档到底能不能跨进程读回来"这类问题只能靠等价手段验证。
  这里不复刻业务逻辑，而是**把 SaveSchema.cs / SqliteSaveStorage.cs 里的 SQL 字面量
  原样抽出来，交给真正的 SQLite 执行** —— 这样列名拼错、占位符个数不对、
  表结构写错之类的错误都会当场暴露，而不是等到真机上"通关了、星级却没记住"。

【覆盖的场景】
  1. 建表语句可重复执行（IF NOT EXISTS），7 张表齐备
  2. SaveLevel / LoadLevels 用到的列与表结构一致（防列名漂移）
  3. 星级往返：写入 → **关闭并重新打开数据库** → 读回（这就是"重启游戏"）
  4. 只升不降：复刻 RecordClear 的合并规则，验证变差的成绩不会覆盖历史最好成绩
  5. 密文列：`ft1:` 开头的信封能被 TEXT 列原样存取（不被类型转换破坏）
  6. 加密格式常量与源码一致（Version / IV / MAC / 前缀 / 派生标签）

【明确不覆盖】
  AES 与 HMAC 的实际加解密（标准库无 AES，且那属于 C# 侧的运行时行为）。
  这里只保证"信封形状"与源码一致 —— 真正的加解密正确性需在 Unity 里验证。

用法：
    python .workbuddy/tools/verify_save_roundtrip.py
退出码：0 = 全部通过，1 = 有失败项。
"""

import io
import os
import re
import sqlite3
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(_HERE))
SCHEMA_CS = os.path.join(PROJ, 'Assets', 'Scripts', 'Data', 'Persistence', 'SaveSchema.cs')
STORAGE_CS = os.path.join(PROJ, 'Assets', 'Scripts', 'Data', 'Persistence', 'SqliteSaveStorage.cs')
CRYPTO_CS = os.path.join(PROJ, 'Assets', 'Scripts', 'Data', 'Persistence', 'CryptoService.cs')

FAILS = []
PASSES = []


def ok(msg):
    PASSES.append(msg)
    print('  [OK]   ' + msg)


def bad(msg):
    FAILS.append(msg)
    print('  [FAIL] ' + msg)


def read(path):
    with io.open(path, encoding='utf-8-sig', errors='replace') as f:
        return f.read()


# ---------------------------------------------------------------- 源码抽取
def concat_strings(block):
    """把 C# 里 'A' + 'B' + 'C' 相邻字面量拼成完整字符串，返回 [(offset, text)]。"""
    lit_re = re.compile(r'"((?:[^"\\]|\\.)*)"')
    lits = [(m.start(), m.end(), m.group(1)) for m in lit_re.finditer(block)]
    out = []
    i = 0
    while i < len(lits):
        s, e, txt = lits[i]
        j = i + 1
        while j < len(lits):
            if block[e:lits[j][0]].strip() == '+':
                txt += lits[j][2]
                e = lits[j][1]
                j += 1
            else:
                break
        out.append((s, txt.replace('\\"', '"').replace('\\\\', '\\')))
        i = j
    return out


def statements_from(section, prefix):
    """取某段代码里所有以 prefix 开头的拼接字符串。"""
    return [t for _, t in concat_strings(section) if t.startswith(prefix)]


def slice_from(text, start_marker, end_marker):
    a = text.find(start_marker)
    if a < 0:
        return ''
    b = text.find(end_marker, a + len(start_marker))
    return text[a:b if b > 0 else len(text)]


# ---------------------------------------------------------------- 主流程
def main():
    for p in (SCHEMA_CS, STORAGE_CS, CRYPTO_CS):
        if not os.path.isfile(p):
            print('找不到源码：' + p)
            return 1

    schema_src = read(SCHEMA_CS)
    storage_src = read(STORAGE_CS)
    crypto_src = read(CRYPTO_CS)

    print('=' * 78)
    print('[1] 从 SaveSchema.cs 抽取建表语句')
    creates = statements_from(
        slice_from(schema_src, 'CreateStatements', '};'), 'CREATE TABLE')
    tables = [re.search(r'CREATE TABLE IF NOT EXISTS\s+(\w+)', s).group(1)
              for s in creates if re.search(r'CREATE TABLE IF NOT EXISTS\s+(\w+)', s)]
    expect_tables = ['meta', 'player_profile', 'level_progress', 'game_settings',
                     'level_snapshot', 'snapshot_tower', 'kv_store']
    missing = [t for t in expect_tables if t not in tables]
    if missing:
        bad('建表语句缺少表：%s' % ', '.join(missing))
    else:
        ok('7 张表的建表语句齐备：%s' % ', '.join(tables))

    # 建表时必须全部 IF NOT EXISTS（否则重复执行会抛"表已存在"）
    no_if = [t for s, t in zip(creates, tables) if 'IF NOT EXISTS' not in s]
    if no_if:
        bad('以下建表语句没带 IF NOT EXISTS：%s' % ', '.join(no_if))
    else:
        ok('全部建表语句带 IF NOT EXISTS（可重复执行）')

    print()
    print('=' * 78)
    print('[2] 从 SqliteSaveStorage.cs 抽取读写语句，核对列名')
    save_block = slice_from(storage_src, 'public void SaveLevel', 'public void DeleteLevel')
    load_block = slice_from(storage_src, 'public List<LevelProgress> LoadLevels', 'public void SaveLevel')

    ins = statements_from(save_block, 'INSERT')
    sel = statements_from(load_block, 'SELECT')
    if not ins:
        bad('没抽到 SaveLevel 的 INSERT 语句')
    if not sel:
        bad('没抽到 LoadLevels 的 SELECT 语句')

    # 建表时声明的 level_progress 列
    lp_create = next((s for s in creates if 'level_progress' in s), '')
    declared_cols = set(re.findall(r'\b([a-z_]+)\s+(?:INTEGER|TEXT|REAL)', lp_create))
    used_cols = set()
    for stmt in ins + sel:
        used_cols.update(re.findall(r'\b([a-z_]+)\b', stmt))
    unknown = sorted(c for c in used_cols
                     if c not in declared_cols
                     and c not in expect_tables          # 表名不是列名（INSERT INTO <表>）
                     and c not in ('select', 'from', 'where',
                                   'order', 'by', 'values', 'insert',
                                   'or', 'replace', 'into', 'asc'))
    if unknown:
        bad('读写语句里出现了建表未声明的标识符：%s' % ', '.join(unknown))
    else:
        ok('读写语句引用的列都在建表里存在（%d 列：%s）'
           % (len(declared_cols), ', '.join(sorted(declared_cols))))

    print()
    print('=' * 78)
    print('[3] 真实 SQLite：建表 + 星级往返 + 重启读回')

    tmpdir = tempfile.mkdtemp(prefix='ftverify_')
    dbfile = os.path.join(tmpdir, 'freetower.db')

    def open_db():
        return sqlite3.connect(dbfile)

    try:
        con = open_db()
        for s in creates:
            con.execute(s)
        con.commit()
        have = set(r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"))
        miss = [t for t in expect_tables if t not in have]
        if miss:
            bad('建表后仍缺表：%s' % ', '.join(miss))
        else:
            ok('真实 SQLite 建表成功，7 张表全部存在')
        # 再跑一遍，验证幂等（每次启动都会跑）
        for s in creates:
            con.execute(s)
        con.commit()
        ok('建表语句第二次执行无异常（等于每次启动自动补表）')
    except sqlite3.Error as e:
        bad('建表失败：%s' % e)
        return 1

    # Python 的 sqlite3 对 ?1 这种编号占位符支持依驱动而异，这里归一化成 ?
    # （源码里就是按 1..6 顺序书写，语义等价）
    ins_norm = re.sub(r'\?\d+', '?', ins[0]) if ins else ''
    sel_norm = sel[0] if sel else ''
    now = int(time.time())

    def protect_plain(v):
        """降级模式（密钥不可用）下明文直存 —— 与 Protect() 的行为一致。"""
        return str(v)

    rows = [
        # level_id, stars, best_hp_left, clear_count
        (1, 3, 20, 4),
        (2, 2, 12, 2),
        (3, 1, 5, 1),
    ]
    try:
        for lid, st, hp, cc in rows:
            con.execute(ins_norm, (lid, protect_plain(st), protect_plain(hp),
                                   protect_plain(cc), now, now))
        con.commit()
        ok('写入 3 关成绩（星级 3 / 2 / 1）')

        # ---- 关键：关掉连接再重开 = 模拟"退出游戏后重新启动" ----
        con.close()
        con = open_db()
        got = con.execute(sel_norm).fetchall()
        got = [(int(r[0]), int(r[1]), int(r[2]), int(r[3])) for r in got]
        if got == rows:
            ok('重开数据库后读回一致：%s' % (got,))
        else:
            bad('重开后读回不一致\n        写入=%s\n        读回=%s' % (rows, got))
    except sqlite3.Error as e:
        bad('读写失败：%s' % e)

    print()
    print('=' * 78)
    print('[4] 只升不降：复刻 SaveManager.RecordClear 的合并规则')
    # 源码：if (stars > p.stars) p.stars = Mathf.Clamp(stars, 0, 3);
    #       先合并到内存，再把**合并后的值**整体写回 —— 所以库里永远是历史最好。
    try:
        def record_clear(con, lid, stars, hp, memo):
            old = memo.get(lid, (0, 0, 0))       # stars, bestHp, clearCount
            st = old[0]
            if stars > st:
                st = max(0, min(3, stars))
            best = max(old[1], hp)
            cc = old[2] + 1
            memo[lid] = (st, best, cc)
            con.execute(ins_norm, (lid, protect_plain(st), protect_plain(best),
                                   protect_plain(cc), now, now))
            con.commit()

        memo = {1: (3, 20, 4)}                   # 从上一节的状态继续
        record_clear(con, 1, 1, 6, memo)          # 再打一次只得 1 星
        record_clear(con, 1, 2, 9, memo)          # 再打一次 2 星
        con.close()
        con = open_db()
        r = con.execute("SELECT stars, best_hp_left, clear_count FROM level_progress "
                        "WHERE level_id = 1").fetchone()
        st, best, cc = int(r[0]), int(r[1]), int(r[2])
        if st == 3:
            ok('反复通关不会掉星：3 → 1星 → 2星 后仍为 %d 星' % st)
        else:
            bad('星级被覆盖了！期望 3，实际 %d' % st)
        if cc == 6:
            ok('通关次数正确累加：4 → 6')
        else:
            bad('通关次数不对：期望 6，实际 %d' % cc)
        if best == 20:
            ok('历史最好剩余生命只取更高值：20（未被 9 覆盖）')
        else:
            bad('bestHpLeft 被覆盖：期望 20，实际 %d' % best)
    except sqlite3.Error as e:
        bad('合并规则验证失败：%s' % e)

    print()
    print('=' * 78)
    print('[5] 密文列：ft1: 信封能否被 TEXT 列原样存取')
    try:
        # 形状与 AesCryptoService 的输出一致：前缀 + Base64(1B 版本 + 16B IV + 16B MAC + 密文)
        import base64
        blob = bytes([1]) + bytes(range(16)) + bytes(range(16)) + b'cipher-block-here'
        envelope = 'ft1:' + base64.b64encode(blob).decode('ascii')
        con.execute(ins_norm, (9, envelope, envelope, envelope, now, now))
        con.commit()
        con.close()
        con = open_db()
        r = con.execute(ins_norm and "SELECT stars, typeof(stars) FROM level_progress "
                        "WHERE level_id = 9").fetchone()
        if r[0] == envelope:
            ok('密文信封原样读回（列类型 %s，长度 %d）' % (r[1], len(r[0])))
        else:
            bad('密文被改动了：%r' % (r[0],))
        if r[1] == 'text':
            ok('密文列的 SQLite 类型是 text（与 Protect 返回 string 一致）')
        else:
            bad('密文列类型是 %s，期望 text' % r[1])
    except Exception as e:
        bad('密文列验证失败：%s' % e)

    print()
    print('=' * 78)
    print('[6] 加密格式常量与源码一致（防止格式悄悄漂移）')
    checks = [
        ('AesCryptoService.Prefix', r'Prefix\s*=\s*"([^"]+)"', 'ft1:'),
        ('Version', r'\bVersion\s*=\s*(\d+)\s*;', '1'),
        ('IvSize', r'\bIvSize\s*=\s*(\d+)\s*;', '16'),
        ('MacSize', r'\bMacSize\s*=\s*(\d+)\s*;', '16'),
        ('enc 子密钥标签', r'"(FT\.Persistence/enc/v1)"', 'FT.Persistence/enc/v1'),
        ('mac 子密钥标签', r'"(FT\.Persistence/mac/v1)"', 'FT.Persistence/mac/v1'),
    ]
    for label, pat, expect in checks:
        m = re.search(pat, crypto_src)
        if not m:
            bad('%s 在 CryptoService.cs 里找不到（是不是改了？）' % label)
        elif m.group(1) != expect:
            bad('%s 变成了 %r（文档与测试都按 %r 写的）' % (label, m.group(1), expect))
        else:
            ok('%s = %s' % (label, expect))

    try:
        con.close()
    except Exception:
        pass
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    print()
    print('=' * 78)
    print('通过 %d 项，失败 %d 项' % (len(PASSES), len(FAILS)))
    if FAILS:
        for f in FAILS:
            print('  ! ' + f)
        print('RESULT: FAIL')
        return 1
    print('RESULT: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
