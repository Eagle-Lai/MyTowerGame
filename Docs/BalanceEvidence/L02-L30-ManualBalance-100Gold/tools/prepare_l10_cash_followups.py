"""Spend observed uninvested conversion cash through legal player upgrades only."""
from formal_tools import *
tag='l10-investment-r4-t';rows=json.loads((REPORT/'raw-trials/references-r4-s/unity-results.json').read_text(encoding='utf-8'));tc={x['id']:x for x in tables()['tbtowerinfo']};runs=[];notes=[]
for sourceindex in [0,1]:
 r=rows[sourceindex];base=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']];time=max(o['timeMs']for o in base if o['waveOrdinal']==25)
 path=r['finalPathCells']
 def score(x):
  c=tc[x['towerId']];return sum((.2+i/max(1,len(path)-1))for i,(col,row)in enumerate(path)if(col-x['col'])**2+(row-x['row'])**2<=tc[c['upgradeTo']]['radius']**2)
 choices=sorted([x for x in r['towerContributions']if tc[x['towerId']]['type']==2 and tc[x['towerId']]['upgradeTo']],key=score,reverse=True)
 for count in [2,3,4]:
  extra=[dict(waveOrdinal=25,timeMs=time,action='upgrade',row=x['row'],col=x['col'],towerId=tc[x['towerId']]['upgradeTo'])for x in choices[:count]]
  ops=base+extra;name=f's{sourceindex}-group{count}';out=REPORT/f'L10/search-{tag}';out.mkdir(exist_ok=True);f=out/f'{name}.json';assert not f.exists();f.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
  runs.append(dict(profileId='D04',levelId=10,strategy=tag+'-'+name,speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
  notes.append(dict(sourceIndex=sourceindex,sourceRunId=r['metrics']['runId'],uninvestedCashAfterConversion=[o['balanceAfter']for o in r['operations']if o['waveOrdinal']==25][-1],firstObservedLeakMs=min(e['combatMs']-round(r['metrics']['waves'][-1]['combatStartSeconds']*1000)for e in r['enemyOutcomes']if e['leaked']),added=extra,reason='Actual prior defense left 644/673 gold after conversion before its first ground leak. Test normal upgrades using that existing cash; do not infer data impossible or reduce more enemy values.'))
request=dict(output=str(ROOT/'Library/BalanceWorkbench'/tag),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs);f=REPORT/f'requests/{tag}.json';assert not f.exists();f.write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8');(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf-8');print(len(runs),'player investment tests; no configuration changes')
