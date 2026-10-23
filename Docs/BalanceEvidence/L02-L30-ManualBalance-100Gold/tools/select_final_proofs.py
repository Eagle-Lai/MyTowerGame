"""Choose the best observed final-seal plan; schedule missing strict triples only."""
from formal_tools import *
from compare_replays import compare
from evidence_accounting import reconcile
import collections,sys
tag=sys.argv[1]if len(sys.argv)>1 else'final-refinements-1';h=runtime_hash();by=collections.defaultdict(list)
def digest(r):return hashlib.sha256(json.dumps([{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']],sort_keys=True,separators=(',',':')).encode()).hexdigest()
for f in (REPORT/'raw-trials').glob('*/unity-results.json'):
 if not trial_inputs_match_current(f):continue
 for index,r in enumerate(json.loads(f.read_text(encoding='utf-8'))):
  if r['levelId']==1 or r['profile']['runtimeContentHash']!=h or not r['valid']or not r['victory']or r['state']!='finished'or r['stars']!=5 or r['pendingOperations']or r['metrics']['leaked']or r.get('initialGold')!=100:continue
  assert len(r['enemyOutcomes'])==r['metrics']['successfulSpawned'];by[r['levelId']].append((f,index,r,digest(r)))
assert set(by)==set(range(2,31)),sorted(set(range(2,31))-set(by));runs=[];proofs=[];choices=[]
for level,candidates in sorted(by.items()):
 candidates.sort(key=lambda p:(sum(o['timeMs']>0 for o in p[2]['operations']),len(p[2]['operations']),p[2]['metrics']['combatElapsedSeconds']))
 f,index,r,d=candidates[0];reconcile(r);choice=dict(level=level,source=f.relative_to(REPORT).as_posix(),sourceIndex=index,runId=r['metrics']['runId'],operationsSha256=d,waveTimeOperations=sum(o['timeMs']>0 for o in r['operations']),operations=len(r['operations']),combatSeconds=r['metrics']['combatElapsedSeconds']);choices.append(choice)
 triples=collections.defaultdict(list)
 for cf,ci,cr,cd in candidates:
  if cd==d and cr['strategy'].startswith('final-reference-')and cr['fundingPolicy']=='Exact scheduled affordability required':triples[cf].append((ci,cr))
 existing=None
 for tf,group in triples.items():
  if len(group)==3:
   proof=compare([x[1]for x in group]);assert proof['allMatch'],(level,proof);existing=dict(level=level,results=tf.relative_to(REPORT).as_posix(),indices=[x[0]for x in group],operationsSha256=d);break
 if existing:proofs.append(existing);continue
 out=REPORT/f'L{level:02}/final-player-plans'/f'{tag}-strict.json';assert not out.exists();out.write_text(json.dumps([{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']],ensure_ascii=False,indent=2),encoding='utf-8')
 for n in range(3):runs.append(dict(profileId='D04',levelId=level,strategy=f'final-reference-{tag}-L{level:02}-{n}',speed=1,operationsPath=str(out),waitForFunds=False,screenshots=True,captureStages=True))
(REPORT/'audit/final-selected-candidates.json').write_text(json.dumps(dict(runtimeContentHash=h,criterion='Fewest wave-time transactions, then total transactions, then combat seconds among all actual final-seal five-star candidates including controls. No claim of global optimum.',levels=choices),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/'audit/selected-final-proofs.json').write_text(json.dumps(dict(runtimeContentHash=h,levels=proofs,missingStrictTriples=sorted(set(range(2,31))-{x['level']for x in proofs})),ensure_ascii=False,indent=2),encoding='utf-8')
if runs:
 out=REPORT/f'requests/{tag}.json';assert not out.exists();out.write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench'/tag),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8');print(len(runs),'strict refinement runs prepared for',sorted({x['levelId']for x in runs}))
else:print('All29 preferred observed candidates already have matching strict triples')
