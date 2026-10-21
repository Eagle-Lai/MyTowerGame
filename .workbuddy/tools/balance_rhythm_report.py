#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""节奏验收报告：拿配方生成 D0x 计划，逐关算 7.2 的量化指标（离线，不写盘）。

为什么单独写一份：7.2 里有几条指标（坎/普比、开局可建塔数、单关节拍）没有现成的
报表出口，而它们正是"节奏是否紧张"的全部依据。这里不改数据，只读 plan。

坎/普比有两种口径，都输出：
  vsPrev   = 坎波环比 ÷ 前一波环比      —— 最严格，但规范自己的目标表也过不了
  vsMedian = 坎波环比 ÷ 非坎波中位环比  —— 与"坎/普 ≥1.40"的设计意图一致
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import balance_pipeline as bp

PEAKS = (5, 10, 15, 20, 25)


def level_metrics(plan, level_id):
    waves = [w for w in plan['waves'] if w['levelId'] == level_id]
    level = next(x for x in plan['levels'] if x['levelId'] == level_id)
    towers = plan['tables']['tbtowerinfo']
    cheapest = min(t['prices'] for t in towers if t['type'] != 3)
    gap = plan['recipe']['formula']['autoNextRoundDelayMs']
    rows = []
    for wave in waves:
        rows.append({'w': wave['waveOrdinal'], 'count': wave['count'], 'ehp': wave['actualEhp'],
                     'span': wave['plannedSpawnSpanMs'], 'interval': wave['spawnIntervalMs'],
                     'flying': wave['flyingCount']})
    for i, row in enumerate(rows):
        row['ratioEhp'] = None if i == 0 else row['ehp'] / rows[i - 1]['ehp']
        row['ratioCount'] = None if i == 0 else row['count'] / rows[i - 1]['count']
    ratios = [r['ratioEhp'] for r in rows[1:]]
    normal = [r['ratioEhp'] for r in rows[1:] if r['w'] not in PEAKS]
    med = statistics.median(normal) if normal else None
    peaks = {}
    for p in PEAKS:
        ratio = next(r['ratioEhp'] for r in rows if r['w'] == p)
        prev = next((r['ratioEhp'] for r in rows if r['w'] == p - 1), None)
        peaks[p] = {'ratio': ratio, 'vsPrev': ratio / prev if prev else None,
                    'vsMedian': ratio / med if med else None,
                    'count': next(r['count'] for r in rows if r['w'] == p)}
    duration = sum(r['span'] for r in rows) + (len(rows) - 1) * gap
    flying_waves = [r['w'] for r in rows if r['flying'] > 0]
    gaps = [b - a for a, b in zip(flying_waves, flying_waves[1:])]
    # 占比只在"含飞行波的波"上取：W1~W2 按设计没有空军，记 0 会污染区间
    share = [r['flying'] / r['count'] for r in rows if r['flying'] > 0]
    return {
        'levelId': level_id,
        'initialGold': level['initialGold'],
        'openingTowers': level['initialGold'] / cheapest,
        'durationSec': duration / 1000.0,
        'w1SpanSec': rows[0]['span'] / 1000.0,
        'w25SpanSec': rows[-1]['span'] / 1000.0,
        'ehpGrowthW25OverW1': rows[-1]['ehp'] / rows[0]['ehp'],
        'normalRatioMedian': med,
        'normalRatioMin': min(normal) if normal else None,
        'normalRatioMax': max(normal) if normal else None,
        'countRatioMax': max(r['ratioCount'] for r in rows[1:]),
        'peaks': peaks,
        'minPeakVsMedian': min(v['vsMedian'] for v in peaks.values()),
        'minPeakVsPrev': min(v['vsPrev'] for v in peaks.values() if v['vsPrev']),
        'flyingFirstWave': flying_waves[0] if flying_waves else None,
        'flyingMaxGap': max(gaps) if gaps else None,
        'flyingShareMin': min(share), 'flyingShareMax': max(share),
        'hp': level['initialGold'] and plan['recipe']['formula']['initialHp'],
        'totalEnemies': sum(r['count'] for r in rows),
    }


def render_markdown(summary, gate=None):
    w = summary['worst']
    rows = summary['levels']

    def mark(ok):
        return '✅ 通过' if ok else '⚠️ 未达标'

    checks = [
        ('1 坎/普比 ≥1.40（坎波环比 ÷ 非坎波中位）', '≥ 1.40', f"{w['minPeakVsMedian']:.3f}", w['minPeakVsMedian'] >= 1.40),
        ('1b 坎/普比（备用口径：坎波 ÷ 前一普通波）', '≥ 1.40', f"{w['minPeakVsPrev']:.3f}", w['minPeakVsPrev'] >= 1.40),
        ('2 普通波环比区间', '[1.01, 1.30]', f"{w['normalRatioMin']:.3f} ~ {w['normalRatioMax']:.3f}",
         w['normalRatioMin'] >= 1.01 and w['normalRatioMax'] <= 1.30),
        ('3 相邻波数量环比', '≤ 1.20', f"{w['countRatioMax']:.3f}", w['countRatioMax'] <= 1.20),
        ('4 开局可建塔数（L1）', '[2.5, 3.5]', f"{w['openingTowersL1']:.2f}", 2.5 <= w['openingTowersL1'] <= 3.5),
        ('4b 开局可建塔数相邻关比值', '≤ 1.25', f"{w['openingRatioMax']:.3f}", w['openingRatioMax'] <= 1.25),
        ('5 单关节拍（含波间空档）', '[420, 540] s', f"{w['durationMin']:.1f} ~ {w['durationMax']:.1f}",
         420 <= w['durationMin'] and w['durationMax'] <= 540),
        ('6 单波 span W1', '[5, 9] s', f"{w['w1SpanMin']:.2f} ~ {w['w1SpanMax']:.2f}",
         5 <= w['w1SpanMin'] and w['w1SpanMax'] <= 9),
        ('6b 单波 span W25', '[18, 28] s', f"{w['w25SpanMin']:.2f} ~ {w['w25SpanMax']:.2f}",
         18 <= w['w25SpanMin'] and w['w25SpanMax'] <= 28),
        ('8 漏怪痛感', 'initialHp = 12', str(summary['formula']['initialHp']),
         summary['formula']['initialHp'] == 12),
        ('9a 空军首现波', 'W3', 'W3' if rows[0]['flyingFirstWave'] == 3 else str(rows[0]['flyingFirstWave']),
         rows[0]['flyingFirstWave'] == 3),
        ('9b 含飞行波间隔', '≤ 5 波', str(w['flyingMaxGap']), (w['flyingMaxGap'] or 99) <= 5),
        ('9c 空军占比（含飞行波）', '[12%, 18%]', f"{w['flyingShareMin']*100:.1f}% ~ {w['flyingShareMax']*100:.1f}%",
         0.12 <= w['flyingShareMin'] and w['flyingShareMax'] <= 0.18),
        ('派生 W25/W1 EHP 倍率', '[120, 200]', f"{w['ehpGrowthMin']:.1f} ~ {w['ehpGrowthMax']:.1f}",
         120 <= w['ehpGrowthMin'] and w['ehpGrowthMax'] <= 200),
    ]
    out = [f"# 节奏验收报告 · {summary['balanceRevision']} / {summary['profileId']}", '',
           '离线由 `balance_pipeline.generate()` 产出的解析计划计算，不含真实 Unity 证据。', '',
           '## 7.2 逐项结论', '', '| 指标 | 通过线 | 实测 | 结论 |', '|---|---|---|---|']
    for name, limit, value, ok in checks:
        out.append(f'| {name} | {limit} | {value} | {mark(ok)} |')
    out += ['', '## 每关明细', '',
            '| 关 | 开局金币 | 可建塔 | 时长 s | W1 span | W25 span | 坎比 W5/10/15/20/25 | 坎/普比 | W25÷W1 |',
            '|---:|---:|---:|---:|---:|---:|---|---:|---:|']
    for r in rows:
        peaks = '/'.join(f"{r['peaks'][p]['ratio']:.2f}" for p in (5, 10, 15, 20, 25))
        out.append(f"| {r['levelId']} | {r['initialGold']} | {r['openingTowers']:.2f} | {r['durationSec']:.1f} | "
                   f"{r['w1SpanSec']:.1f} | {r['w25SpanSec']:.1f} | {peaks} | "
                   f"{r['minPeakVsMedian']:.2f} | {r['ehpGrowthW25OverW1']:.1f} |")
    if gate:
        out += ['', '## Fill-gate（更严格的附加判据）', '', '| 关 | 满驻防漏血 | 剩余血量 | 用时/Par | 备注 |', '|---:|---:|---:|---:|---|']
        for L, v in gate.items():
            note = (v.get('notes') or {}).get('G4', '')
            detail = (v.get('detail') or {}).get('G4', {})
            out.append(f"| {L} | {detail.get('leaked')} | {detail.get('hp')} | {detail.get('ratio')} | {note} |")
    return '\n'.join(out) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description='7.2 节奏指标离线报告')
    parser.add_argument('--recipe', default=str(bp.DEFAULT_RECIPE))
    parser.add_argument('--profile', default=None)
    parser.add_argument('--out', default=None)
    parser.add_argument('--levels', default=None)
    parser.add_argument('--markdown', default=None, help='输出 markdown 验收报告路径')
    parser.add_argument('--gate', default=None, help='gate-summary.json，附在报告末尾')
    args = parser.parse_args(argv)
    recipe = bp.read_json(args.recipe)
    profile = args.profile or recipe['selectedProfileId']
    plan = bp.generate(recipe, profile)
    levels = [int(x) for x in args.levels.split(',')] if args.levels else \
        list(range(1, plan['levelCount'] + 1))
    rows = [level_metrics(plan, L) for L in levels]
    summary = {
        'profileId': profile,
        'balanceRevision': recipe['balanceRevision'],
        'formula': {k: recipe['formula'][k] for k in
                    ('initialGold', 'goldPerLevel', 'initialHp', 'autoNextRoundDelayMs',
                     'spawnBaseMs', 'spawnWaveReductionMs', 'minSpawnMs', 'maxSpawnMs',
                     'pressureMultiplier', 'waveLinear', 'waveQuadratic', 'finalMultiplier',
                     'minBudgetGrowth', 'tailBaseMs', 'tailTierGrowthMs')},
        'levels': rows,
        'worst': {
            'minPeakVsMedian': min(r['minPeakVsMedian'] for r in rows),
            'minPeakVsPrev': min(r['minPeakVsPrev'] for r in rows),
            'countRatioMax': max(r['countRatioMax'] for r in rows),
            'durationMin': min(r['durationSec'] for r in rows),
            'durationMax': max(r['durationSec'] for r in rows),
            'w1SpanMin': min(r['w1SpanSec'] for r in rows),
            'w1SpanMax': max(r['w1SpanSec'] for r in rows),
            'w25SpanMin': min(r['w25SpanSec'] for r in rows),
            'w25SpanMax': max(r['w25SpanSec'] for r in rows),
            'openingTowersL1': rows[0]['openingTowers'],
            'openingRatioMax': max((b['openingTowers'] / a['openingTowers']) for a, b in zip(rows, rows[1:])) if len(rows) > 1 else None,
            'normalRatioMin': min(r['normalRatioMin'] for r in rows),
            'normalRatioMax': max(r['normalRatioMax'] for r in rows),
            'ehpGrowthMin': min(r['ehpGrowthW25OverW1'] for r in rows),
            'ehpGrowthMax': max(r['ehpGrowthW25OverW1'] for r in rows),
            'flyingShareMin': min(r['flyingShareMin'] for r in rows),
            'flyingShareMax': max(r['flyingShareMax'] for r in rows),
            'flyingMaxGap': max(r['flyingMaxGap'] or 0 for r in rows),
        },
    }
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.out:
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + '\n', encoding='utf-8')
    if args.markdown:
        gate = None
        if args.gate:
            gate = json.loads(pathlib.Path(args.gate).read_text(encoding='utf-8-sig')).get('levels')
        md = pathlib.Path(args.markdown)
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(render_markdown(summary, gate), encoding='utf-8')
        print('markdown -> ' + str(md))
    print(json.dumps(summary['worst'], ensure_ascii=False))
    if not args.out and not args.markdown:
        print(text)


if __name__ == '__main__':
    main()
