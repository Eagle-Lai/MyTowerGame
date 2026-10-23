"""Summarize only recorded Unity outcomes, including unfinished/failed trials."""
from formal_tools import *
import sys,collections,datetime
tag=sys.argv[1]
rows=json.loads((ROOT/f'Library/BalanceWorkbench/{tag}/unity-results.json').read_text(encoding='utf-8'))
summary=[]
for i,r in enumerate(rows):
    m=r['metrics'];waves={w['ordinal']:w for w in m['waves']};leaks=[e for e in r['enemyOutcomes']if e['leaked']]
    points=[]
    for e in leaks:
        start=round(waves[e['waveOrdinal']]['combatStartSeconds']*1000)
        points.append(dict(wave=e['waveOrdinal'],flying=e['isFlying'],type=e['type'],remainingHp=e['remainingHp'],waveMs=e['combatMs']-start,enemyId=e['enemyId']))
    summary.append(dict(index=i,level=r['levelId'],strategy=r['strategy'],runId=m['runId'],runtimeHash=r['profile']['runtimeContentHash'],state=r['state'],victory=r['victory'],stars=r['stars'],completedWaves=m['completedWaveCount'],killed=m['killed'],leaked=m['leaked'],hp=m['hp'],initialGold=r['initialGold'],finalGold=r['finalGold'],operations=len(r['operations']),timedOperations=sum(o['timeMs']>0 for o in r['operations']),pendingOperations=r['pendingOperations'],combatSeconds=m['combatElapsedSeconds'],leakWindows=points,finalPreparationCash=r['waveBoundaries'][-1]['cash']if r['waveBoundaries']else None))
value=dict(batch=tag,capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualCompletedTrials=len(rows),actualZeroLeakLevels=sorted({x['level']for x in summary if x['victory']and x['leaked']==0 and x['completedWaves']==25}),trials=summary)
(REPORT/f'audit/{tag}-observed-diagnostics.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
lines=[f'# {tag} 实测诊断','', '只统计真实已记录的结果；零漏不自动代表最终五星认证。','', '|序号|关|策略|完成波|击杀|漏怪|生命|金币|星|失败窗口|','|---:|---:|---|---:|---:|---:|---:|---:|---:|---|']
for x in summary:
    failures=collections.Counter((p['wave'],'空'if p['flying']else'地')for p in x['leakWindows'])
    desc='；'.join(f'W{wave}{kind}{count}'for (wave,kind),count in failures.items())or x['state']
    lines.append(f"|{x['index']}|{x['level']}|{x['strategy']}|{x['completedWaves']}|{x['killed']}|{x['leaked']}|{x['hp']}|{x['finalGold']}|{x['stars']}|{desc}|")
(REPORT/f'audit/{tag}-实测诊断.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('actual trials',len(summary),'zero-leak levels',value['actualZeroLeakLevels'])
