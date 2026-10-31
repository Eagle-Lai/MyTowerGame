from search import *
for p in OUT.glob('*/status.json'):
    s=json.loads(p.read_text());print(p.parent.name,s['phase'],str(s.get('completed'))+'/'+str(s.get('total')),'wave',s.get('round'),'hp',s.get('hp'))
for p in OUT.glob('*/unity-results.json'):
    for i,r in enumerate(json.loads(p.read_text())):
        m=r['metrics']; print('RESULT',p.parent.name,i,r['state'],'valid',r['valid'],'stars',r['stars'],'wave',m['completedWaveCount'],'kills',m['killed'],'leaks',m['leaked'],'hp',m['hp'],'seconds',round(m['combatElapsedSeconds'],2),'ops',len(r['operations']),r.get('operationError',''))
if '--hash' in sys.argv:
    hashes=json.loads((OUT/'input-hashes.json').read_text());diff=[]
    for name,h in hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h:diff.append(name)
    print('INPUT_CHANGES',diff)
