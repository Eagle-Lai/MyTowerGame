"""Summarize real and predicted failure mechanisms without changing data."""
from formal_tools import *
import collections
for level in [8,9,10,14,15,16,18,19,20,21,22,23,24,25,27,28,29,30]:
    ix=json.loads((REPORT/f'L{level:02}/trial-index.json').read_text(encoding='utf-8'))
    options=[x for x in ix if x.get('state')=='finished'and not x.get('pending',0)]
    best=sorted(options,key=lambda x:(-x['waves'],x['leaked'],-x['hp']))[:2]
    rows=[]
    for b in best:
        r=json.loads((REPORT/f'raw-trials/{b["batch"]}/unity-results.json').read_text(encoding='utf-8'))[b['index']]
        leaks=collections.Counter((e['waveOrdinal'],'air'if e['isFlying']else'ground')for e in r['enemyOutcomes']if e['leaked'])
        rows.append(dict(batch=b['batch'],index=b['index'],strategy=b['strategy'],waves=b['waves'],leaks={str(k):v for k,v in leaks.items()},operations=b['operations'],gold=b['finalGold']))
    print(level,json.dumps(rows,ensure_ascii=False),flush=True)
