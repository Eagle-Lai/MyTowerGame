from search import *
import subprocess
DOC=ROOT/'Docs/BalanceEvidence/L03-CurrentModel-20261025'
deadline=time.monotonic()+1800
while time.monotonic()<deadline:
    p=OUT/'precise-recovery/unity-results.json'
    if p.exists():
        rs=json.loads(p.read_text());passing=[(i,r) for i,r in enumerate(rs) if r['valid'] and r['metrics']['leaked']==0 and r['metrics']['hp']==12]
        if passing:break
    time.sleep(3)
if not passing:raise RuntimeError('No zero-leak refinement passed')
idx,r=passing[0]
status=json.loads((OUT/'precise-recovery/status.json').read_text())
if status['phase']!='complete':
    (OUT/'precise-recovery/cancel.request').write_text('Best zero-leak candidate found; proceed to strict replays')
    time.sleep(8)
subprocess.run([sys.executable,str(OUT/'finalize.py'),str(p),str(idx)],cwd=ROOT,check=True)
ops=json.loads((DOC/'best-operations.json').read_text())
late=[{**o,'timeMs':o['timeMs']+500 if o['timeMs']>0 else 0} for o in ops];dump(OUT/'human-500ms-operations.json',late)
reqpath=request('strict-final',[DOC/'best-operations.json',DOC/'best-operations.json',OUT/'human-500ms-operations.json'],False,step=.02,keep=True)
req=json.loads(reqpath.read_text());req['runs'][-1]['screenshots']=True;req['runs'][-1]['captureStages']=True
dump(reqpath,req);dump(DOC/'replay-request.json',req)
print('STRICT_START',start(reqpath),flush=True)
time.sleep(12)
subprocess.run([sys.executable,str(OUT/'fast_observation.py')],cwd=ROOT)
