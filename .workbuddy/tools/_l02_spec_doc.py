#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 L02 源表实际值生成《L02_重设计规格.md》。改表后重跑即可刷新文档。"""
import json
import pathlib
from collections import Counter

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
ART = ROOT / 'Artifacts/L01_ZeroLeak_20261103_1823/runtime-config.json'
META = ROOT / '.workbuddy/tools/_l02_design_meta.json'
OUT = ROOT / 'Docs/L02_Rebalance_20261108/L02_重设计规格.md'
SYM = {1: 'N', 2: 'P', 3: 'F'}
L1, L2 = 41, 70
Sg1, Sg2 = 1437.0, 2603.0
Da1, Da2 = 2997.0, 3520.0
COST = 6666


def book(p):
    with open(p, 'rb') as fh:
        return openpyxl.load_workbook(fh, data_only=True)


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def main():
    d = json.load(open(ART, encoding='utf-8'))
    ws = book(L02 / 'EnemyData.xlsx').worksheets[0]
    h = heads(ws)
    en = {int(ws.cell(r, h['id']).value): dict(hp=float(ws.cell(r, h['hp']).value),
                                                rw=float(ws.cell(r, h['reward']).value),
                                                spd=float(ws.cell(r, h['speed']).value),
                                                fly=int(ws.cell(r, h['isFlying']).value or 0),
                                                name=ws.cell(r, h['name']).value)
          for r in range(4, ws.max_row + 1) if ws.cell(r, h['id']).value}
    wl = book(L02 / 'EnemyList.xlsx').worksheets[0]
    wls = {int(wl.cell(r, 2).value): dict(ids=[int(x) for x in str(wl.cell(r, 3).value).split(',') if x.strip()],
                                          ivl=float(wl.cell(r, 5).value))
           for r in range(4, wl.max_row + 1) if wl.cell(r, 2).value}
    rd = book(L02 / 'RoundData.xlsx').worksheets[0]
    h2 = heads(rd)
    bon = {int(rd.cell(r, 2).value): rd.cell(r, h2['rewardGold']).value
           for r in range(4, rd.max_row + 1) if rd.cell(r, 2).value}
    sc = book(L02 / 'SceneInfo.xlsx').worksheets[0]
    hs = heads(sc)
    init = sc.cell(4, hs['initialGold']).value
    rl = [int(x) for x in str(sc.cell(4, hs['RoundList']).value).split(',')]
    cell = {tuple(map(int, k.split(','))): tuple(v) for k, v in json.load(open(META, encoding='utf-8'))['cell'].items()}

    tot = [0, 0.0, 0.0, 0]
    inc = init
    rows = []
    for i, rid in enumerate(rl, 1):
        ids = wls[rid]['ids']
        N = len(ids)
        na = sum(1 for e in ids if en[e]['fly'])
        vg = [en[e]['spd'] for e in ids if not en[e]['fly']]
        va = [en[e]['spd'] for e in ids if en[e]['fly']]
        VG = sum(vg) / len(vg)
        VA = (sum(va) / len(va) if va else 1.0)
        ehp = sum(en[e]['hp'] for e in ids)
        kill = sum(en[e]['rw'] for e in ids)
        Tw = N * wls[rid]['ivl'] / 1000.0 + L2 / VG
        eps1 = [e for g in d['rounds'][i - 1]['groups'] for e in g['enemies']]
        N1 = sum(e['count'] for e in eps1)
        ivl1 = d['rounds'][i - 1]['groups'][0]['SpawnIntervalMs'] / 1000.0
        vg1 = [e['Speed'] for e in eps1 if not e['IsFlying']]
        VG1 = sum(vg1) / len(vg1)
        ehp1 = sum(e['count'] * e['Hp'] for e in eps1)
        Tw1 = N1 * ivl1 + L1 / VG1
        ha = max([en[e]['hp'] for e in ids if en[e]['fly']] or [0])
        ha1 = max([e['Hp'] for e in eps1 if e['IsFlying']] or [0])
        gm = max([en[e]['hp'] / next(x['Hp'] for x in eps1 if x['Name'] == en[e]['name'] and not x['IsFlying'])
                  for e in ids if not en[e]['fly']] or [0])
        tot[0] += N; tot[1] += ehp; tot[2] += kill; tot[3] += bon[rid]; inc += kill + bon[rid]
        by = {}
        for e in ids:
            by.setdefault((en[e]['name'], en[e]['fly']), []).append(e)
        rows.append(dict(w=i, rid=rid, N=N, na=na, ng=N - na, ehp=ehp, kill=kill, bonus=bon[rid],
                         Tw=Tw, ivl=wls[rid]['ivl'], g2=Sg2 * Tw / ehp, w2=Sg1 * Tw1 / ehp1,
                         a2=(Da2 / VA / ha if ha else 0), a1=(Da1 / VA / ha1 if ha1 else 0),
                         gmul=gm, inc=inc,
                         ents=sorted(by.items(), key=lambda kv: (kv[0][1], kv[0][0]))))
    G = init + tot[2] + tot[3]
    L = ['# 第二关（L02）数值重设计 — 实施完成规格', '',
         '> 数字直接读自源表，与 `Assets/ConfigJson` 一致；改写后重跑 `_l02_spec_doc.py` 即可刷新。', '',
         '> 口径：以 L01「零漏怪通关版」Λ 曲线为难度基准（α=1.0）；数量 ×1.5；总经济 ≈7,200；'
         '**`initialGold` 恒为 100**（铁律）；地图与塔表未动。', '',
         '## 1. 总纲', '', '| 维度 | L01（基准） | L02 实施后 | 倍数 |', '|---|---|---|---|',
         '| 棋盘 / 地面路径 | 13×7 / 41 格 | 16×9 / 70 格 | ×1.71 |',
         f'| 预期解塔阵 | 40 座 / 3,919 金 / 1,437 DPS | 64 座 / {COST:,} 金 / {Sg2:,.0f} DPS | ×1.81 |',
         f'| 总经济 | 4,138 | {G:,.0f} | ×{G / 4138:.2f} |',
         f'| 塔阵占经济 | 94.7% | {COST / G:.1%} | — |',
         f'| 怪物总数 | 10,236 | {int(tot[0]):,} | ×{tot[0] / 10236:.2f} |',
         f'| 总 EHP | 3,371,860 | {tot[1]:,.0f} | ×{tot[1] / 3371860:.2f} |',
         f'| 地面血量 | 基准 | ×{min(r["gmul"] for r in rows):.2f} ~ ×{max(r["gmul"] for r in rows):.2f} | 见第 4 节 |',
         '| 空中血量 | 基准 | ×0.94 ~ ×1.17 | 受防空产能限制 |',
         '| 单只 reward | 基准 | ×1.16 | 固定单价 |',
         f'| 波次奖励 | 1,305 | {tot[3]:,} | ×{tot[3] / 1305:.2f} |',
         f'| 初始金币 | 100 | {init} | **持平（铁律）** |',
         f'| 总时长 | 47 分钟 | {sum(r["Tw"] for r in rows) / 60:.0f} 分钟 | ×{sum(r["Tw"] for r in rows) / 60 / 47:.2f} |', '',
         '> **前 4 波**：血量与出怪间隔均取 L01 原值（100 金开局只能建 3 座 N1，出怪速率必须与 L01 同水平），'
         '数量仍 ×1.5 —— 表现为「怪更多、节奏更慢」，而不是「每只更硬」。', '',
         '## 2. 预期解塔阵（64 座，供摆阵参考，未写入配置）', '',
         '| |' + '|'.join(f'c{c}' for c in range(16)) + '|', '---|' + '---|' * 16]
    for r in range(9):
        line = [f'**r{r}**']
        for c in range(16):
            if (r, c) == (4, 0):
                line.append('S')
            elif (r, c) == (4, 15):
                line.append('E')
            elif (r, c) in cell:
                line.append(f'{SYM[cell[(r, c)][0]]}{cell[(r, c)][1]}')
            else:
                line.append('·')
        L.append('| ' + ' | '.join(line) + ' |')
    c2 = Counter(f'{SYM[v[0]]}{v[1]}' for v in cell.values())
    L += ['', '构成：' + '、'.join(f'{k} × {v} 座' for k, v in sorted(c2.items())) +
          f'，共 {len(cell)} 座，**{COST:,} 金**（占经济 {COST / G:.1%}）。', '',
          f'- 地面有效 DPS `Σd·μ` = {Sg2:,.0f}；防空 `Σd·μ` = {Da2:,.0f}（仅 N/F 塔）', '',
          '## 3. 逐波规格（已实施）', '',
          '| 波 | roundId | 地 | 空 | 合计 | 间隔ms | 波内时长s | EHP | Λ波 L02 | Λ波 L01 | Λ空 L02 | Λ空 L01 | 击杀金 | 奖励 |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        L.append(f'| W{r["w"]} | {r["rid"]} | {r["ng"]} | {r["na"]} | {r["N"]} | {r["ivl"]:.1f} | {r["Tw"]:.0f} | '
                 f'{r["ehp"]:,.0f} | {r["g2"]:.2f} | {r["w2"]:.2f} | {r["a2"]:.2f} | {r["a1"]:.2f} | {r["kill"]:.0f} | {r["bonus"]:.0f} |')
    L += ['', f'合计 **{int(tot[0]):,} 只**（空中 {sum(r["na"] for r in rows):,}）｜EHP **{tot[1]:,.0f}**｜'
          f'击杀金 {tot[2]:,.0f}｜波次奖励 {tot[3]:,}｜初始 {init}｜**总经济 {G:,.0f}**', '',
          '## 4. 怪物明细（按波 × 类型）', '',
          '| 波 | 类型 | 数量 | 血量 | 速度 | 单只金币 | 空/地 | 血量/L01 |', '|---|---|---|---|---|---|---|---|']
    for r in rows:
        for (name, fly), ids in r['ents']:
            hp = en[ids[0]]['hp']
            eps1 = [e for g in d['rounds'][r['w'] - 1]['groups'] for e in g['enemies']]
            h1 = next((e['Hp'] for e in eps1 if e['Name'] == name), 0)
            L.append(f'| W{r["w"]} | {name} | {len(ids)} | {hp:,.2f} | {en[ids[0]]["spd"]:.4f} | '
                     f'{en[ids[0]]["rw"]:.4f} | {"空" if fly else "地"} | ' + (f'×{hp / h1:.2f} |' if h1 else '— |'))
    L += ['', '## 5. 收入曲线', '', f'| 波 | 击杀金 | 奖励 | 累计 | 占 {G:,.0f} |', '|---|---|---|---|---|']
    for r in rows:
        L.append(f'| W{r["w"]} | {r["kill"]:.0f} | {r["bonus"]:.0f} | {r["inc"]:,.0f} | {r["inc"] / G:.1%} |')
    L += ['', '## 6. 实施记录', '', '| 表 | 字段 | 结果 |', '|---|---|---|',
          '| `Levels/L02/SceneInfo.xlsx` | `initialGold` | 100（**铁律，未改**） |',
          '| `Levels/L02/RoundData.xlsx` | `rewardGold` | 25 波；W1–W4 = 82/82/81/81（含初始金拆出的 74 金），合计 2,346 |',
          '| `Levels/L02/EnemyList.xlsx` | `EnemyIndexs` / `enemyInterval` | 25 组；W1–W4 间隔回到 L01 原值 280/273/266/259 |',
          '| `Levels/L02/EnemyData.xlsx` | `hp` / `reward` / `speed` | 106 行；W1–W4 血量回到 L01 原值 |', '',
          '- 备份：`.bak_20261108_before_redesign`、`.bak_20261108_before_gold100`、`.bak_20261108_before_w14fix`',
          '- 导表：19:49:07 `== succ ==`，11 张表；源表↔JSON 全量比对 0 差异',
          '- 运行时：`IsLoaded=True / FailedTables=0`；list2001–2004 = 46/56/64/73 只，间隔 280/273/266/259，'
          '平均血 8.26/8.65/10.27/11.87',
          '- 校验：`check_air_spawn_order.py --levels 1 2` → `adjacent_air_pairs=0` PASS', '',
          '## 7. 遗留与风险', '',
          '1. **前 4 波在 100 金开局下的余量**：W1 出怪 3.57/s vs 3 座 N1 击杀 4.84/s（+36%）；'
          'W2 +26%；W3/W4 依赖「已攒到 500~900 金」这一前提，若玩家不建塔则不足。',
          '2. **空中血量只能 ×0.94~1.17**：防空产能 3,520 仅比 L01 的 2,997 高 17%。',
          '3. **Λ 是相对标尺**：L01 通关版 Λ波 最低 0.51 仍零漏怪，L02 落在同一区间。',
          '4. **未实机验证**：需按第 2 节塔阵摆一遍，观察 W15–W25 漏怪点再微调。',
          '5. `EnemyList.desc` / `EnemyData.desc` 中 `N=…/EHP=…` 文本已过期（不在授权字段内，未改）。', '']
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(L), encoding='utf-8')
    print(f'已生成 {OUT}')
    print(f'总经济 {G:,.2f}｜怪物 {int(tot[0]):,}｜EHP {tot[1]:,.0f}｜初始 {init}')


if __name__ == '__main__':
    main()
