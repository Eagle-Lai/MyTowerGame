"""Create strict reference groups plus bounded legal player controls/alternatives."""
from formal_tools import *
from evidence_accounting import reconcile
import collections
selected=json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels'];assert len(selected)==29
current=tables();h=runtime_hash();tc={x['id']:x for x in current['tbtowerinfo']};snapshots={};allrows=[]
for f in (REPORT/'raw-trials').glob('*/unity-results.json'):
 for index,r in enumerate(json.loads(f.read_text(encoding='utf-8'))):
  if not r['valid']or not r['victory']or r['state']!='finished'or r['pendingOperations']or r.get('initialGold')!=100 or len(r.get('enemyOutcomes',[]))!=r['metrics']['successfulSpawned']:continue
  sh=r['profile']['runtimeContentHash']
  if sh not in snapshots:
   folder=REPORT/'audit/runtime-snapshots'/sh;snapshots[sh]={k:json.loads((folder/f'{k}.json').read_text(encoding='utf-8-sig'))for k in KEYS}if all((folder/f'{k}.json').exists()for k in KEYS)else None
  if snapshots[sh]and level_gameplay_identity(r['levelId'],snapshots[sh])==level_gameplay_identity(r['levelId'],current):allrows.append((f,index,r))
def signature(r):return {(x['row'],x['col']):x['towerId']for x in r['towerContributions']}
def difference(a,b):
 x,y=signature(a),signature(b);return sum(x.get(p)!=y.get(p)for p in x.keys()|y.keys())
def clean(r):return[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
groups=[[]for _ in range(5)];decisions=[]
for entry in selected:
 level=entry['level'];main=json.loads((REPORT/entry['source']).read_text(encoding='utf-8'))[entry['sourceIndex']];reconcile(main)
 out=REPORT/f'L{level:02}/final-player-plans';out.mkdir(exist_ok=True)
 def write(name,ops):
  f=out/f'{name}.json'
  if f.exists():assert json.loads(f.read_text(encoding='utf-8'))==ops,'Prepared player input drift: '+str(f)
  else:f.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
  return str(f)
 primary=write('strict-reference',clean(main));batch=min(4,(level-2)//6);runs=groups[batch]
 for n in range(3):runs.append(dict(profileId='D04',levelId=level,strategy=f'final-reference-L{level:02}-{n}',speed=1,operationsPath=primary,waitForFunds=False,screenshots=True,captureStages=True))
 alternatives=[(f,i,r)for f,i,r in allrows if r['levelId']==level and difference(main,r)>=2]
 assert alternatives,f'L{level:02} lacks a materially different legal full-wave victory'
 alternatives.sort(key=lambda x:(x[2]['profile']['runtimeContentHash']!=h,-difference(main,x[2]),x[2]['metrics']['leaked'],len(x[2]['operations'])))
 f,i,alternate=alternatives[0];reconcile(alternate)
 alternative_record=dict(source=f.relative_to(REPORT).as_posix(),sourceIndex=i,runId=alternate['metrics']['runId'],differentFinalCells=difference(main,alternate),routeSteps=len(alternate['finalPathCells'])-1,leaked=alternate['metrics']['leaked'],exactFinalHash=alternate['profile']['runtimeContentHash']==h)
 # Replay every alternative after the coordinated art handoff, even when data SHA256 is unchanged.
 ops=write('alternative',clean(alternate));runs.append(dict(profileId='D04',levelId=level,strategy=f'final-alternative-L{level:02}',speed=1,operationsPath=ops,waitForFunds=True,screenshots=False,captureStages=False));alternative_record['finalReplayScheduled']=True
 # Independent controls preserve reference spending intent, using actual prices.
 converted=[]
 for o in clean(main):
  if tc[o['towerId']]['type']==1:o['towerId']+=3
  converted.append(o)
 noair=write('ground-only-no-air',converted);runs.append(dict(profileId='D04',levelId=level,strategy=f'final-control-ground-only-L{level:02}',speed=1,operationsPath=noair,waitForFunds=True,screenshots=False,captureStages=False))
 noslow=[];has_slow=any(tc[o['towerId']]['type']==3 for o in main['operations'])
 stable_normal=sorted([x for x in main['towerContributions']if tc[x['towerId']]['type']==1 and not any(o['action']=='sell'and o['row']==x['row']and o['col']==x['col']for o in main['operations'])],key=lambda x:(x['airHits'],x['damage']),reverse=True)
 add_slow={(x['row'],x['col'])for x in stable_normal[:3]}if not has_slow else set()
 assert has_slow or add_slow
 for o in clean(main):
  if has_slow and tc[o['towerId']]['type']==3:
   if o['action']=='upgrade':continue
   o['towerId']=1
  elif not has_slow and(o['row'],o['col'])in add_slow:
   assert tc[o['towerId']]['type']==1;o['towerId']+=6
  noslow.append(o)
 noslowpath=write('slow-allocation',noslow);runs.append(dict(profileId='D04',levelId=level,strategy=f'final-control-slow-allocation-L{level:02}',speed=1,operationsPath=noslowpath,waitForFunds=True,screenshots=False,captureStages=False))
 sold={(o['row'],o['col'])for o in main['operations']if o['action']=='sell'}
 candidates=[x for x in main['towerContributions']if tc[x['towerId']]['level']==1 and tc[x['towerId']]['type']!=3 and(x['row'],x['col'])not in sold]
 removed_grade=1
 if not candidates:
  stable=[x for x in main['towerContributions']if tc[x['towerId']]['type']!=3 and(x['row'],x['col'])not in sold]
  assert stable;removed_grade=min(tc[x['towerId']]['level']for x in stable)
  candidates=[x for x in stable if tc[x['towerId']]['level']==removed_grade]
 candidates.sort(key=lambda x:(-x['shortcutPreventedSteps'],x['damage'],x['row'],x['col']))
 removed={(x['row'],x['col'])for x in candidates[:6]};assert removed
 shorter=write('fewer-route-walls',[o for o in clean(main)if(o['row'],o['col'])not in removed]);runs.append(dict(profileId='D04',levelId=level,strategy=f'final-control-fewer-walls-L{level:02}',speed=1,operationsPath=shorter,waitForFunds=True,screenshots=False,captureStages=False))
 decisions.append(dict(level=level,reference=entry,alternative=alternative_record,controls=dict(groundOnly='Keep each reference coordinate and grade, replace ordinary tower chain1/2/3 with ground-only4/5/6. Actual higher prices and income waits apply; no new income.',fewerWalls=dict(removedCells=sorted(removed),removedGrade=removed_grade,rule='Remove up to6 stable lowest-available-grade ordinary/group towers, prefer grade1; prioritize measured shortcut prevention then low damage; exclude all sale/rebuild coordinates. If no grade1 remains, the removal also changes upgraded firepower and is reported as such. Observe actual route and result; no assumed failure.')),strictFunding=False,finalHash=h))
for decision in decisions:
 decision['referenceWaitForFunds']=decision.pop('strictFunding');decision['comparisonWaitForFunds']=True
 entry=decision['reference'];original=json.loads((REPORT/entry['source']).read_text(encoding='utf-8'))[entry['sourceIndex']];had_slow=any(tc[o['towerId']]['type']==3 for o in original['operations'])
 decision['controls']['slowAllocation']='Replace every slow build with ordinary1 and omit slow upgrades; retain savings'if had_slow else'Replace three stable ordinary cores with the same-grade slow chain; retain actual cost differences'
baseline=json.loads((REPORT/'L01-current-check/result.json').read_text(encoding='utf-8'));baselinepath=REPORT/'requests/final-suite-L01-exact-operations.json';assert not baselinepath.exists();baselinepath.write_text(json.dumps(clean(baseline),ensure_ascii=False,indent=2),encoding='utf-8')
groups[0].insert(0,dict(profileId='D04',levelId=1,strategy='final-baseline-L01',speed=1,operationsPath=str(baselinepath),waitForFunds=False,screenshots=True,captureStages=True))
for n,runs in enumerate(groups):
 tag=f'final-suite-{n+1}';f=REPORT/f'requests/{tag}.json';assert not f.exists();f.write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench'/tag),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8');print(tag,len(runs),'actual runs scheduled')
(REPORT/'audit/final-suite-decisions.json').write_text(json.dumps(dict(runtimeContentHash=h,scope='Three exact-affordability reference runs, one materially different alternative and three controls per level in same batch, all after coordinated art handoff. No game-data writes.',levels=decisions),ensure_ascii=False,indent=2),encoding='utf-8')
