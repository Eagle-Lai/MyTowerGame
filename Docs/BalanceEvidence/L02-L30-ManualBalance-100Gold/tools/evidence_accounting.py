"""Reconcile independent enemy outcomes, real transaction costs, and wave balances."""
from formal_tools import *
import collections
def reconcile(result):
    m=result['metrics'];assert result['initialGold']==100
    assert result['victory']and m['completedWaveCount']==25 and result['state']=='finished'
    assert not result['pendingOperations']and not m['debugOverride']
    events=result['enemyOutcomes'];assert len(events)==m['successfulSpawned']
    assert sum(not x['leaked']for x in events)==m['killed']
    assert sum(x['leaked']for x in events)==m['leaked']
    gold=100;hp=result['initialHp'];cash=[];checks=[]
    for w in m['waves']:
        ordinal=w['ordinal'];ops=[o for o in result['operations']if o['waveOrdinal']==ordinal];outcomes=[e for e in events if e['waveOrdinal']==ordinal]
        assert len(outcomes)==w['successfulSpawned']
        assert sum(e['rewardOrDamage']for e in outcomes if not e['leaked'])==w['killGold']
        loss=sum(e['rewardOrDamage']for e in outcomes if e['leaked']);assert hp-loss==w['hp']
        start=round(w['combatStartSeconds']*1000);net=0
        for o in ops:
            earned=sum(e['rewardOrDamage']for e in outcomes if not e['leaked']and e['combatMs']<=start+o['timeMs'])
            expected=gold+earned+net-o['cost']
            assert expected==o['balanceAfter'],(ordinal,o,earned,net,expected)
            assert o['balanceAfter']>=0
            checks.append(dict(waveOrdinal=ordinal,timeMs=o['timeMs'],before=o['balanceAfter']+o['cost'],cost=o['cost'],after=o['balanceAfter'],actualKillIncomeArrived=earned))
            net-=o['cost']
        after=gold+w['killGold']+w['clearGold']+net;assert after==w['gold']
        boundary=next(b for b in result['waveBoundaries']if b['beforeWave']==ordinal)
        row=dict(waveOrdinal=ordinal,beforePreparing=gold,afterPreparing=boundary['cash'],killGold=w['killGold'],clearGold=w['clearGold'],buildSpent=sum(o['cost']for o in ops if o['action']=='build'),upgradeSpent=sum(o['cost']for o in ops if o['action']=='upgrade'),sellRefund=-sum(o['cost']for o in ops if o['action']=='sell'),after=after,damage=loss,hp=w['hp'],spawned=w['successfulSpawned'],killed=w['killed'],leaked=w['leaked'],seconds=w['combatEndSeconds']-w['combatStartSeconds'],peakAlive=w['peakAlive'],spawnDeferredCount=w['spawnDeferredCount'])
        cash.append(row);gold=after;hp=w['hp']
    assert gold==result['finalGold']
    totals={k:sum(w[k]for w in cash)for k in ['killGold','clearGold','buildSpent','upgradeSpent','sellRefund','damage']}
    totals.update(initialGold=100,finalGold=gold,minBalanceAfterOperation=min(o['balanceAfter']for o in result['operations']),operationPrefixesChecked=len(checks),allOperationPrefixesNonnegative=True,enemyOutcomeCount=len(events))
    assert 100+totals['killGold']+totals['clearGold']+totals['sellRefund']-totals['buildSpent']-totals['upgradeSpent']==gold
    return dict(runId=m['runId'],runtimeContentHash=result['profile']['runtimeContentHash'],waves=cash,operationChecks=checks,totals=totals)
if __name__=='__main__':
    import sys
    rows=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'));result=rows[int(sys.argv[2])]if isinstance(rows,list)else rows
    account=reconcile(result);out=pathlib.Path(sys.argv[3]);out.write_text(json.dumps(account,ensure_ascii=False,indent=2),encoding='utf-8');print(account['totals'])
