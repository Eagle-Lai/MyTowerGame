from finalize import *
import gzip
r=json.loads((DOC/'selected-result.json').read_text());m=r['metrics']
ops=r['operations'];outcomes=r['enemyOutcomes'];problems=[];prefixes=[]
if len(outcomes)!=5082:problems.append('Outcome count differs from 5082')
if len({e['spawnSerial'] for e in outcomes})!=len(outcomes):problems.append('Duplicate spawn outcome')
kill_total=sum(e['rewardOrDamage'] for e in outcomes if not e['leaked'])
spent=0
for i,o in enumerate(ops):
    prior=[e for e in outcomes if not e['leaked'] and (e['waveOrdinal']<o['waveOrdinal'] or e['waveOrdinal']==o['waveOrdinal'] and e['combatMs']<=round(m['waves'][o['waveOrdinal']-1]['combatStartSeconds']*1000)+o['timeMs'])]
    clear=sum(w['clearGold'] for w in m['waves'] if w['ordinal']<o['waveOrdinal'])
    paid=sum(e['rewardOrDamage'] for e in prior);before=100+paid+clear-spent;spent+=o['cost'];after=100+paid+clear-spent
    ok=before>=o['cost'] and after==o['balanceAfter']
    if not ok:problems.append('Cash prefix mismatch '+str(i+1))
    prefixes.append({'sequence':i+1,'wave':o['waveOrdinal'],'timeMs':o['timeMs'],'earnedKillGold':paid,'clearGold':clear,'before':before,'cost':o['cost'],'after':after,'recordedAfter':o['balanceAfter'],'passed':ok})
total=100+kill_total+sum(w['clearGold'] for w in m['waves'])-sum(o['cost'] for o in ops)
if total!=r['finalGold']:problems.append('Final cash mismatch')
dump(DOC/'cashflow-audit.json',{'passed':not problems,'problems':problems,'killGold':kill_total,'clearGold':sum(w['clearGold'] for w in m['waves']),'spent':spent,'finalGold':total,'prefixes':prefixes})
archive=DOC/'evidence';archive.mkdir(exist_ok=True)
for p in OUT.glob('*/unity-results.json'):
    with gzip.open(archive/(p.parent.name+'-unity-results.json.gz'),'wb') as f:f.write(p.read_bytes())
print('Cash audit',not problems,'prefixes',len(prefixes),'problems',problems,'total',total)
