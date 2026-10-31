from search import *
import subprocess
PY=sys.executable;DOC=ROOT/'Docs/BalanceEvidence/L03-CurrentModel-20261025'
deadline=time.monotonic()+2000
while time.monotonic()<deadline:
    p=OUT/'precise-zero/status.json'
    if p.exists() and json.loads(p.read_text()).get('phase')=='complete':break
    time.sleep(3)
results=json.loads((OUT/'precise-zero/unity-results.json').read_text())
passing=[(i,r) for i,r in enumerate(results) if r['valid'] and r['metrics']['victory'] and r['metrics']['leaked']==0 and r['metrics']['hp']==12]
if not passing:
    seed=results[0]
    paths=[]
    choices=[[(3,3),(4,5)],[(6,6),(8,7)],[(4,5),(6,6)],[(3,3),(6,6)]]
    for i,targets in enumerate(choices):
        ops=[{k:o[k] for k in ['waveOrdinal','timeMs','action','row','col','towerId']} for o in seed['operations']]
        for row,col in targets:
            oldid=next(t['towerId'] for t in seed['towerContributions'] if t['row']==row and t['col']==col)
            if oldid!=5:raise ValueError(('expected level2 blast',row,col,oldid))
            ops.append({'waveOrdinal':25,'timeMs':1000,'action':'upgrade','row':row,'col':col,'towerId':6})
        p=OUT/'candidates'/('recovery-'+str(i)+'.json');dump(p,ops);paths.append(p)
    requestpath=request('precise-recovery',paths,True,step=.02)
    time.sleep(5);print('Running legitimate final-wave reinforcements',start(requestpath),flush=True)
    raise SystemExit(0)
idx,r=min(passing,key=lambda item:(len(item[1]['operations']),item[1]['metrics']['combatElapsedSeconds']))
subprocess.run([PY,str(OUT/'finalize.py'),str(OUT/'precise-zero/unity-results.json'),str(idx)],check=True,cwd=ROOT)
ops=json.loads((DOC/'best-operations.json').read_text())
late=[{**o,'timeMs':o['timeMs']+500 if o['timeMs']>0 else 0} for o in ops]
dump(OUT/'human-500ms-operations.json',late)
p=request('strict-final',[DOC/'best-operations.json',DOC/'best-operations.json',OUT/'human-500ms-operations.json'],False,step=.02,keep=True)
req=json.loads(p.read_text());req['runs'][-1]['screenshots']=True;req['runs'][-1]['captureStages']=True
dump(p,req);dump(DOC/'replay-request.json',req)
time.sleep(5)
print('Selected 20ms candidate',idx,'run',r['metrics']['runId'],flush=True)
print(start(p),flush=True)
