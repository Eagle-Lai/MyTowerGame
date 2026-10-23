"""Publish complete formal values and source addresses; never writes configuration."""
from formal_tools import *
import collections,itertools,math
parser=argparse.ArgumentParser();parser.add_argument('--tag',default='r1');args=parser.parse_args();tag=args.tag
assert tag in ['r1','r2','r3','r4','final']
waves=json.loads((REPORT/f'audit/formal-waves-{tag}.json').read_text(encoding='utf-8'))
levels=json.loads((REPORT/f'audit/formal-levels-{tag}.json').read_text(encoding='utf-8'))
t=tables();scenes={s['id']:s for s in t['tbsceneinfo']};maps={s['id']:s for s in t['tblevelmap']}
reasons={};edits=collections.defaultdict(list)
for p in sorted(REPORT.glob('design-*.json')):
    if p.name.endswith('.proposal.json'):continue
    data=json.loads(p.read_text(encoding='utf-8'))
    if isinstance(data,dict):
        for row in data.get('waves',[]):reasons[row['level'],row['wave']]=row['reason']
for p in sorted(REPORT.glob('design-*.cells.json')):
    if p.name.endswith('-remaining.cells.json'):continue
    for e in json.loads(p.read_text(encoding='utf-8')):
        for level in range(2,31):
            if f'/L{level:02}/'in e['path']:edits[level].append(e);break
def loc(x):return f"`{pathlib.Path(x['path']).name} / {x['sheet']} / 行 {x['row']}`"
index=[f'# 正式配置 725 波明细（{tag}）','',f'正规 Luban 导出后只读提取。当前战役封印：`{runtime_hash()}`。这是已落盘数据与设计意图；通关与五星以逐关报告为准。', '', '怪物顺序由 SceneInfo.RoundList → RoundData.EnemyIndexs → EnemyList.EnemyIndexs 展开，重复 ID 保留。EHP 只用于分析。源地址映射只含位置，当前数值均来自正式导出并已与源单元格核对。', '', '|关卡|怪数|飞行数/占比|EHP|击杀金|清波金|含100金总理论收入|明细|','|---|---:|---:|---:|---:|---:|---:|---|']
for level in range(2,31):
    ls=[w for w in waves if w['level']==level];s=scenes[level];mp=maps[s['mapId']];summary=next(x for x in levels if x['level']==level)
    coords={ch:(c,r)for r,row in enumerate(mp['cells'])for c,ch in enumerate(row)if ch in 'SE'}
    distance=math.dist(coords['S'],coords['E']);space=sum(ch=='.'for row in mp['cells']for ch in row)
    out=REPORT/f'L{level:02}/设计与725波明细.md'
    lines=[f'# L{level:02} 正式配置与 25 波完整数据（r1）','',f"100 初始金币；{s['initialHp'] if 'initialHp'in s else s.get('hp','见SceneInfo')} 初始生命；{mp['rows']} 行 × {mp['cols']} 列，普通可建格 {space}；S=(行{coords['S'][1]},列{coords['S'][0]})，E=(行{coords['E'][1]},列{coords['E'][0]})。空中直达几何长度 {distance:.3f} 格；实际减速和战斗覆盖另以回放为准。",'',f'数据封印：`{runtime_hash()}`。完整有序引用及源单元格位置：[原始提取](../audit/formal-waves-r1.json)。', '', '本版逐项重定开局 HP、后续空袭阈值、出怪间隔和清波金；大部分既有地面变体、数量与有序组合保留并接受实测。保留项不是新生成的数值。首次全杀解、替代策略、经济紧凑性和最终时间门槛仍在验证。','', '## 完整波次','', '单位：HP、速度、护甲为正式表值；interval、延迟、间隔均为毫秒。空中时间“距离/速度”为无减速几何预测，不是击杀或通关证明。', '']
    for w in ls:
        lines += [f"### W{w['wave']} / Round {w['roundId']} / EnemyList {','.join(map(str,w['groupIds']))}",'',f"共 {w['count']} 只，飞行 {w['air']}；相邻出生 {w['gap']} ms，Round 延迟 {w['roundDelay']} ms，组延迟 {w['groupDelay']} ms；全杀金 {w['kill']}，清波金 {w['clear']}；EHP {w['ehp']:.2f}。",'',f"本波安排：{reasons.get((level,w['wave']),'保持本波结构，按实际机制验证。')}",'',f"源行：{loc(w['sourceRound'])}；"+'；'.join(loc(g)for g in w['sourceGroups'])+'。', '', '|变体ID/角色|名称|数量|HP|护甲|速度|击杀金|漏怪扣血|EnemyData.interval|空中无减速秒|源行|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
        for v in w['variants']:
            e=v['data'];role='Boss'if e['type']==5 else '飞行'if e['isFlying']else '地面'
            air=f"{distance/e['speed']:.3f}"if e['isFlying']else'—'
            lines.append(f"|{e['id']} / {role}|{e['name']}|{v['count']}|{e['hp']}|{e['armor']}|{e['speed']}|{e['reward']}|{e['damageToPlayer']}|{e['interval']}|{air}|{loc(v['source'])}|")
        ordered=' → '.join(f'{key} × {len(list(group))}' for key,group in itertools.groupby(w['orderedEnemyIds']))
        lines += ['',f'实际出生有序段（连续重复压缩，保持顺序）：`{ordered}`。','']
    lines += ['## 本关正式单元格改动及理由','','所有新值均为已明确决定的字面数值；代码仅定位并写入具体单元格。以下清单保留旧值、位置与理由，未使用统一倍率或公式生成战役。','','|源表 / Sheet / 单元格|原值|当前字面值|理由|','|---|---|---|---|']
    for e in edits[level]:lines.append(f"|{pathlib.Path(e['path']).name} / {e['sheet']} / {e['cell']}|{e['before']}|{e['after']}|{e['reason']}|")
    content='\n'.join(lines).replace('（r1）',f'（{tag}）').replace('formal-waves-r1.json',f'formal-waves-{tag}.json').replace('|当前字面值|','|该次字面值|').replace('首次全杀解、替代策略、经济紧凑性和最终时间门槛仍在验证。','实际通关、经济和评级状态见总索引，配置明细本身不代表实测结论。')
    out.write_text(content+'\n',encoding='utf-8')
    index.append(f"|L{level:02}|{summary['count']}|{summary['air']} / {summary['air']/summary['count']:.2%}|{summary['ehp']:.2f}|{summary['kill']}|{summary['clear']}|{100+summary['kill']+summary['clear']}|[25波/变体/源位置](L{level:02}/设计与725波明细.md)|")
(REPORT/'725波正式配置明细.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
print('29 complete source detail reports; 725 waves; no config writes')
