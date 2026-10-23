"""Publish a level only after three real final-data five-star exact replays agree."""
from formal_tools import *
from evidence_accounting import reconcile
from evidence_drawing import draw_board,label
from compare_replays import compare
import argparse,shutil,collections
p=argparse.ArgumentParser();p.add_argument('results',type=pathlib.Path);p.add_argument('level',type=int);p.add_argument('notes',type=pathlib.Path);a=p.parse_args()
allresults=json.loads(a.results.read_text(encoding='utf-8'));group=[r for r in allresults if r['levelId']==a.level and r['strategy'].startswith('final-reference-')]
assert trial_inputs_match_current(a.results),'Current code, resources or meta file set differs from the selected real proof'
proof=compare(group);assert proof['allMatch']
notes=json.loads(a.notes.read_text(encoding='utf-8'))
for k in ['mapAnalysis','bottleneck','selectionReason','searchBounds','timingWindows','economyAnalysis','alternativeAnalysis','limitations','calibrationReason']:assert notes[k],k
r=group[0];assert 'pending'not in r['profile']['calibrationStatus'].lower()
for required in [REPORT/'audit/runtime-load-final.json',REPORT/'audit/formal-integrity-final.json',REPORT/f'audit/batch-inputs/{a.results.parent.name}/input-manifest.json']:assert required.exists(),required
manifest=json.loads((REPORT/f'audit/batch-inputs/{a.results.parent.name}/input-manifest.json').read_text(encoding='utf-8'))
assert manifest['phase']=='before_start'and manifest['runtimeContentHash']==runtime_hash()
closed=REPORT/f'audit/{a.results.parent.name}-completion.json';assert closed.exists(),closed
closed_audit=json.loads(closed.read_text(encoding='utf-8'));assert closed_audit['inputsUnchanged']and not closed_audit['errors']
out=REPORT/f'L{a.level:02}';assert not(out/'完整逐波操作与测试报告.md').exists(),'Preserve previous final delivery before replacing it'
evidence=out/'evidence';evidence.mkdir(exist_ok=True);stagedir=out/'阶段图';stagedir.mkdir(exist_ok=True)
account=reconcile(r);ops=r['operations'];t=tables();tower={x['id']:x for x in t['tbtowerinfo']};scene=next(x for x in t['tbsceneinfo']if x['id']==a.level);mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId']);m=r['metrics']
board={};old=[];investment={}
for i,o in enumerate(ops):
    key=(o['row'],o['col']);old.append(board.get(key))
    if o['action']=='sell':assert board.pop(key)==o['towerId']
    elif o['action']=='build':assert key not in board;board[key]=o['towerId']
    else:assert tower[board[key]]['upgradeTo']==o['towerId'];board[key]=o['towerId']
    investment[key]=(o['waveOrdinal'],o['timeMs'],i+1)
assert board=={(x['row'],x['col']):x['towerId']for x in r['towerContributions']}
for filename,value in [('best-result.json',r),('best-operations.json',ops),('reproducibility.json',proof)]:
    (out/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
(evidence/'three-actual-replays.json').write_text(json.dumps(group,ensure_ascii=False,indent=2),encoding='utf-8')
(evidence/'cashflow-and-prefixes.json').write_text(json.dumps(account,ensure_ascii=False,indent=2),encoding='utf-8')
replay=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in ops]
(evidence/'replay-operations.json').write_text(json.dumps(replay,ensure_ascii=False,indent=2),encoding='utf-8')
screens=evidence/'screenshots';screens.mkdir(exist_ok=True);images={}
for trial in group:
    observed=trial['waveBoundaries']+trial['operationStages']
    for s in observed:
        if not s.get('screenshot'):continue
        name=pathlib.Path(s['screenshot']).name;source=a.results.parent/name
        assert source.exists(),source
        shutil.copy2(source,screens/name);images[name]=f'evidence/screenshots/{name}'
    for w in [1,10,25]:assert any(s['beforeWave']==w and s.get('screenshot')for s in trial['waveBoundaries'])
subtitle=f"25/25 波 · {m['killed']}/{m['expectedEnemyCount']} 击杀 · 0漏怪 · 生命{m['hp']}/{m['maxHp']} · 实际5星"
draw_board(out/'最终布阵图.png',board,r['finalPathCells'],f'L{a.level:02}：本轮已验证候选中的最佳推荐（最终操作后）',subtitle,{(o['row'],o['col'])for o in ops if o['timeMs']>0},t=tower,mp=mp,footer=f"runId {m['runId']}；同版首次成功及两次严格复跑一致。")
stageentries=[]
for i,s in enumerate(r['operationStages']):
    filename=f"W{s['waveOrdinal']}-{s['timeMs']}ms-{s['phase']}-{i:02}.png";point={(x['row'],x['col']):x['towerId']for x in s['layout']}
    if s['phase']=='before':
        following=next((x for x in r['operationStages'][i+1:]if x['phase']=='after'and x['waveOrdinal']==s['waveOrdinal']and x['timeMs']==s['timeMs']),None)
        changed=ops[s['operationCount']:following['operationCount']]if following else []
    else:changed=[o for o in ops[:s['operationCount']]if o['waveOrdinal']==s['waveOrdinal']and o['timeMs']==s['timeMs']]
    title=f"L{a.level:02} W{s['waveOrdinal']} {s['timeMs']/1000:.2f}秒 "+('操作前'if s['phase']=='before'else'操作后')
    draw_board(stagedir/filename,point,s['pathCells'],title,f"余额{s['cash']}；生命{s['hp']}；完成{s['operationCount']}笔；实际路径{len(s['pathCells'])-1}步",{(o['row'],o['col'])for o in changed},t=tower,mp=mp,footer=f"真实交易阶段；runId {m['runId']}；与最终证据同版。")
    stageentries.append((title,f'阶段图/{filename}',s))
lines=[f'# L{a.level:02} 最佳玩法布局方案与完整逐波操作、测试报告','', '本方案是本轮已验证候选中的最佳推荐；有限搜索未覆盖全部玩家策略，不声称全局最优。', '', '## 结果摘要','',f"{subtitle}。实际出生{m['successfulSpawned']}、击杀{m['killed']}、漏怪{m['leaked']}、扣血{account['totals']['damage']}，终局金币{r['finalGold']}；模拟战斗{m['combatElapsedSeconds']:.2f}秒，完整关卡{m['levelElapsedSeconds']:.2f}秒。零漏、正常胜利和五星均由当前正式配置的真实回放及唯一评级入口确认。",'', '## 调整依据与方案选择','',notes['mapAnalysis'],'',notes['bottleneck'],'',notes['selectionReason'],'',notes['alternativeAnalysis'],'', '## 首次成功与两次严格复跑','', '|记录|runId|封印|波/击杀/漏|生命|金币|战斗秒|星级|','|---|---|---|---|---|---:|---:|---:|']
for i,x in enumerate(group):
    q=x['metrics'];lines.append(f"|{'首次'if i==0 else '严格复跑'+str(i)}|{q['runId']}|{x['profile']['runtimeContentHash']}|25/{q['killed']}/0|{q['hp']}/{q['maxHp']}|{x['finalGold']}|{q['combatElapsedSeconds']:.6f}|{x['stars']}|")
lines+=['',proof['comparison']+'。全部相同。原始结果和逐项比较分别见 [三次实测](evidence/three-actual-replays.json)、[一致性记录](reproducibility.json)。','', '## 当前配置与执行范围','',f"初始金币100，初始生命{r['initialHp']}，25波；Unity 2022.3.62f3c1，MyTowerGame / unityMCP 8082。通过 BalancePlayModeVerifier.StartBatch，在空闲编辑器进入隔离 PlayMode；使用正式导出，无候选配置，无注资、回血、清怪、跳波或改倍率。步长{r['stepSeconds']}秒，倍速{r['speed']}，严格按实际时机购买，waitForFunds=false。正式存档与原场景由既有隔离机制保护。",'',f"版本：`{r['versionKey']}`；封印：`{r['profile']['runtimeContentHash']}`；校准状态：`{r['profile']['calibrationStatus']}`；Par={r['profile']['parCombatTimeMs']}ms。",'',notes['calibrationReason'],'',f"完整输入和源码指纹：[批次输入清单](../audit/batch-inputs/{a.results.parent.name}/input-manifest.json)。运行时加载：[正式封印日志](../audit/runtime-load-final.json)。",'', '## 最终布阵与关键变化','', '![最后一次关键操作后的最终布局](最终布阵图.png)','']
if stageentries:
    for title,path,s in stageentries:
        lines += [f'### {title}','',f'![{title}]({path})','']
        if s.get('screenshot'):lines += [f"[真实Unity截图]({images[pathlib.Path(s['screenshot']).name]})",'']
else:lines += ['无波中动态改造；各波准备期交易均在下表按真实顺序列出。','']
lines+=['### 最终逐塔清单','', '|坐标(行,列)|塔型等级|最后投资波/时机/序号|实际职责证据|伤害|对空命中|减速次数|重复生效敌人数|','|---|---|---|---|---:|---:|---:|---:|']
for x in sorted(r['towerContributions'],key=lambda x:(x['row'],x['col'])):
    key=(x['row'],x['col']);v=investment[key];role='缓速覆盖'if tower[x['towerId']]['type']==3 else '地面群攻'if tower[x['towerId']]['type']==2 else '地空单体'
    lines.append(f"|{key}|{label(x['towerId'],tower)}|W{v[0]} / {v[1]/1000:.2f}s / #{v[2]}|{role}；阻止捷径{x['shortcutPreventedSteps']}步|{x['damage']:.2f}|{x['airHits']}|{x['slowApplications']}|{x['repeatEffectEnemies']}|")
lines+=['', '## W1—W25 完整操作','', '“波前”指该波启动前的准备/结算阶段；波中时刻从该波 combatStartSeconds 起算。相同时刻的交易必须保持编号顺序。', '', '|波|实际时机|序号/动作|坐标|等级变化|支出/退款|操作后余额|','|---:|---|---|---|---|---:|---:|']
for wave in range(1,26):
    rows=[(i,o)for i,o in enumerate(ops)if o['waveOrdinal']==wave]
    if not rows:lines.append(f'|{wave}|—|无|—|—|0|—|')
    for i,o in rows:
        when='波前'if o['timeMs']==0 else f"本波{o['timeMs']/1000:.2f}秒";action={'build':'建造','upgrade':'升级','sell':'出售'}[o['action']]
        previous=label(old[i],tower)if old[i]else'空格';after='空格'if o['action']=='sell'else label(o['towerId'],tower)
        money=f"退款{-o['cost']}"if o['cost']<0 else f"支出{o['cost']}"
        lines.append(f"|{wave}|{when}|#{i+1} {action}|({o['row']},{o['col']})|{previous} → {after}|{money}|{o['balanceAfter']}|")
lines+=['','## 逐波结果与现金流','','波前金是上一波结束余额；开战金已经扣除本波准备期操作。波中击杀金只在对应敌人实际结算后可用。','','|波|波前金|开战金|击杀金|清波金|建造|升级|退款|清波结余|生/杀/漏|扣血/生命|战斗秒|峰值/暂缓|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|']
for w in account['waves']:lines.append(f"|{w['waveOrdinal']}|{w['beforePreparing']}|{w['afterPreparing']}|{w['killGold']}|{w['clearGold']}|{w['buildSpent']}|{w['upgradeSpent']}|{w['sellRefund']}|{w['after']}|{w['spawned']}/{w['killed']}/{w['leaked']}|{w['damage']} / {w['hp']}|{w['seconds']:.2f}|{w['peakAlive']} / {w['spawnDeferredCount']}|")
lines+=['',notes['economyAnalysis'],'', '## 搜索范围与全部对照','',notes['searchBounds'],'', '|批次/策略|波数|漏怪|生命|星|状态|操作数|原始结果|','|---|---:|---:|---:|---:|---|---:|---|']
index=json.loads((out/'trial-index.json').read_text(encoding='utf-8'));index=index.get('trials',[])if isinstance(index,dict)else index
for x in index:lines.append(f"|{x.get('batch','')} / {x.get('strategy','')}|{x.get('waves','')}|{x.get('leaked','')}|{x.get('hp','')}|{x.get('stars','')}|{x.get('state','')}|{x.get('operations','')}|[结果]({x['source']})|")
total=account['totals'];lines += ['', '开发候选和失败保留原始封印与版本；本报告最终五星结论只引用上方同版三次严格回放。完整索引：[JSON](trial-index.json)、[CSV](trial-index.csv)。', '', '## 总账与证据完整性','',f"`100 + 实际击杀{total['killGold']} + 清波{total['clearGold']} + 出售退款{total['sellRefund']} − 建造{total['buildSpent']} − 升级{total['upgradeSpent']} = {total['finalGold']}`。实际结算事件共{total['enemyOutcomeCount']}条，已核对全部{total['operationPrefixesChecked']}个操作前缀，最低操作后余额{total['minBalanceAfterOperation']}。所有逐波与逐笔余额均一致，无负余额。",'', '[独立事件对账和现金流](evidence/cashflow-and-prefixes.json) · [完整实际操作](best-operations.json) · [可回放操作](evidence/replay-operations.json) · [最佳完整结果](best-result.json)', '', '## 操作可执行性与限制','', notes['timingWindows'],'',notes['limitations'],'', '固定步长脚本运行成功不等于已验证手动触控。相同时刻多笔交易按列表顺序执行，期间模拟不推进；人工是否可利用当前暂停交互完成这些操作，仍应按已验证的操作范围理解，不能由脚本结果推断。','', '## 原始证据与配置明细','', '[全部25波正式变体、顺序及源位置](设计与725波明细.md) · [首轮及两次复跑](evidence/three-actual-replays.json) · [正式配置审计](../audit/formal-integrity-final.json) · [30关总索引](../README.md)','']
for b in r['waveBoundaries']:
    if b.get('screenshot'):lines.append(f"- [W{b['beforeWave']}实际截图]({images[pathlib.Path(b['screenshot']).name]})")
(out/'完整逐波操作与测试报告.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(a.level,'final report, stages, operations and accounting published')
