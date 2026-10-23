"""Select development references using real outcomes, with independent cash proofs."""
from formal_tools import *
from evidence_accounting import reconcile
import collections
cache={};selections=[];incomplete=[];current=tables();snapshot_cache={};local_current={level:level_gameplay_identity(level,current)for level in range(2,31)}
for level in range(2,31):
    path=REPORT/f'L{level:02}/trial-index.json';index=json.loads(path.read_text(encoding='utf-8'))
    candidates=[]
    for row in index:
        if not row.get('victory')or row.get('leaked')!=0 or row.get('waves')!=25 or row.get('pending',0):continue
        source=(path.parent/row['source']).resolve()
        if source not in cache:cache[source]=json.loads(source.read_text(encoding='utf-8'))
        r=cache[source][row['index']]
        assert r['metrics']['runId']==row['runId']
        campaign=r['profile']['runtimeContentHash']
        if campaign not in snapshot_cache:
            folder=REPORT/'audit/runtime-snapshots'/campaign
            snapshot_cache[campaign]={k:json.loads((folder/f'{k}.json').read_text(encoding='utf-8-sig'))for k in KEYS}if all((folder/f'{k}.json').exists()for k in KEYS)else None
        snapshot=snapshot_cache[campaign]
        if not snapshot or level_gameplay_identity(level,snapshot)!=local_current[level]:
            incomplete.append(dict(level=level,runId=row['runId'],reason='Original full gameplay snapshot unavailable or differs from current referenced gameplay/shared combat tables; retained as historical evidence'))
            continue
        if r.get('initialGold')!=100 or len(r.get('enemyOutcomes',[]))!=r['metrics']['successfulSpawned']:
            incomplete.append(dict(level=level,runId=row['runId'],reason='Historical victory lacks initial-gold or full independent enemy-event observations; retain raw evidence, exclude from cash-certified selections'))
            continue
        candidates.append((row,r,source))
    if not candidates:continue
    candidates.sort(key=lambda x:(sum(o['timeMs']>0 for o in x[1]['operations']),len(x[1]['operations']),x[1]['metrics']['combatElapsedSeconds']))
    selected,r,source=candidates[0];account=reconcile(r)
    summary=dict(level=level,runId=selected['runId'],source=source.relative_to(REPORT).as_posix(),sourceIndex=selected['index'],runtimeContentHash=r['profile']['runtimeContentHash'],selectionCriterion='Fewest actual wave-time transactions, then total transactions, then combat time, among archived real zero-leak victories; development only',stars=r['stars'],combatSeconds=r['metrics']['combatElapsedSeconds'],operations=len(r['operations']),waveTimeOperations=sum(o['timeMs']>0 for o in r['operations']),actualZeroLeakCandidates=len(candidates),account=account)
    selections.append(summary)
(REPORT/'audit/development-reference-selections.json').write_text(json.dumps(dict(finalCertified=False,selectionScope='Archived real trials with observed initialGold=100 and complete enemy outcomes; oldest observations without this coverage are listed separately',excludedIncompleteObservations=incomplete,levels=selections),ensure_ascii=False,indent=2),encoding='utf-8')
print('Current-gameplay development references:',[r['level']for r in selections]);print('Missing:',[l for l in range(2,31)if l not in {r['level']for r in selections}])
