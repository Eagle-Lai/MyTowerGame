"""Print observed investment and air-completion windows; no inferred certification."""
from formal_tools import *
for row in json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels']:
    r=json.loads((REPORT/row['source']).read_text(encoding='utf-8'))[row['sourceIndex']];ops=r['operations'];metrics=r['metrics'];last=metrics['waves'][-1];start=round(last['combatStartSeconds']*1000)
    airs=[e['combatMs']-start for e in r['enemyOutcomes']if e['waveOrdinal']==25 and e['isFlying']]
    times=sorted({(o['waveOrdinal'],o['timeMs'])for o in ops if o['timeMs']})
    print(json.dumps(dict(level=row['level'],lastWaveAirLastOutcomeMs=max(airs)if airs else None,lastWaveCombatMs=round((last['combatEndSeconds']-last['combatStartSeconds'])*1000),actualWaveTimeTransactionGroups=times,firstUpgrade=next((o for o in ops if o['action']=='upgrade'),None),wave25Cash=next(w for w in row['account']['waves']if w['waveOrdinal']==25)),ensure_ascii=False),flush=True)
