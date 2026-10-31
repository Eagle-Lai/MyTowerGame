from candidates import *
r=json.loads((OUT/'fixed-batch/unity-results.json').read_text())[0]
base=[{k:o[k] for k in ['waveOrdinal','timeMs','action','row','col','towerId']} for o in r['operations']]
paths=[]
for i,targets in enumerate([[(7,9)],[(0,9)],[(7,9),(0,9)],[(1,9)],[(7,9),(8,9)],[(0,9),(8,9)]]):
    ops=[]
    moves=[]
    for c in targets:
        nextop=next((o for o in base if o['waveOrdinal']>20 and (o['row'],o['col'])==c and o['action']=='upgrade'),None)
        if nextop:moves.append(nextop)
    for o in base:
        if o in moves:continue
        ops.append(dict(o))
    for o in moves:ops.append({**o,'waveOrdinal':20,'timeMs':1000})
    ops.sort(key=lambda o:(o['waveOrdinal'],o['timeMs']))
    p=OUT/'candidates'/('reactive-'+str(i)+'.json');dump(p,ops);paths.append(p)
print(request('reactive-batch',paths,True,step=.02))
