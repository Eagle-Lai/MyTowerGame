"""Strict actual replay comparison. Never evaluates stars outside the real evaluator."""
from formal_tools import *
import sys,math
def differences(a,b,path=''):
    if isinstance(a,dict)and isinstance(b,dict):
        if a.keys()!=b.keys():return [dict(path=path,problem='keys',a=list(a),b=list(b))]
        return [d for k in a for d in differences(a[k],b[k],path+'/'+str(k))]
    if isinstance(a,list)and isinstance(b,list):
        if len(a)!=len(b):return [dict(path=path,problem='length',a=len(a),b=len(b))]
        return [d for i,(x,y)in enumerate(zip(a,b))for d in differences(x,y,path+'/'+str(i))]
    if isinstance(a,(int,float))and isinstance(b,(int,float)):
        if abs(a-b)<=1e-5:return []
    elif a==b:return []
    return [dict(path=path,a=a,b=b)]
def canonical(r):
    metrics={k:v for k,v in r['metrics'].items()if k!='runId'}
    fields=['waveOrdinal','timeMs','action','row','col','towerId','cost','balanceAfter','pathLength']
    boundaries=[{k:v for k,v in b.items()if k not in['screenshot','screenshotTiming']}for b in r['waveBoundaries']]
    stages=[{k:v for k,v in s.items()if k not in['screenshot','screenshotTiming']}for s in r['operationStages']]
    return dict(stars=r['stars'],valid=r['valid'],victory=r['victory'],state=r['state'],profile=r['profile'],metrics=metrics,initialGold=r['initialGold'],initialHp=r['initialHp'],finalGold=r['finalGold'],operations=[{k:o[k]for k in fields}for o in r['operations']],waveBoundaries=boundaries,operationStages=stages,finalPathCells=r['finalPathCells'],towerContributions=r['towerContributions'],pendingOperations=r['pendingOperations'],enemyOutcomes=[{k:v for k,v in e.items()if k!='spawnSerial'}for e in r['enemyOutcomes']])
def compare(group):
    assert len(group)==3
    assert len({r['metrics']['runId']for r in group})==3,'Independent actual runs require distinct run IDs'
    first=group[0];h=runtime_hash()
    for r in group:
        assert r['stars']==5 and r['valid'] and r['victory'] and r['state']=='finished'
        assert r['initialGold']==100 and not r['metrics']['debugOverride'] and not r['pendingOperations']
        assert r['metrics']['completedWaveCount']==25 and r['metrics']['leaked']==0
        assert r['profile']['runtimeContentHash']==h
        assert r['fundingPolicy']=='Exact scheduled affordability required'
    checks=[dict(runId=r['metrics']['runId'],differences=differences(canonical(first),canonical(r)))for r in group[1:]]
    return dict(level=first['levelId'],runtimeContentHash=h,firstRunId=first['metrics']['runId'],reruns=checks,allMatch=all(not x['differences']for x in checks),comparison='All wave, enemy outcome, operation affordability, cash, per-wave boundaries, operation stages, routes, final layout and tower contribution fields; runId, screenshot identity and global spawn serial excluded; numeric tolerance 0.00001')
if __name__=='__main__':
    source=pathlib.Path(sys.argv[1]);rows=json.loads(source.read_text(encoding='utf-8'));out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    for level in sorted({r['levelId']for r in rows}):
        result=compare([r for r in rows if r['levelId']==level]);(out/f'L{level:02}-reproducibility.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');assert result['allMatch'],level
    print('all strict replay comparisons matched')
