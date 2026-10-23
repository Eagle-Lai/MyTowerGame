"""Bounded player-action followups to actual r2 failures; never edits game data."""
from formal_tools import *
import collections,copy

tag='targeted-r2-d'
source=ROOT/'Library/BalanceWorkbench/references-r2-a/unity-results.json'
rows=json.loads(source.read_text(encoding='utf-8'))
t=tables();tc={x['id']:x for x in t['tbtowerinfo']}
runs=[];notes=[]
fields=['waveOrdinal','timeMs','action','row','col','towerId']

def plain(r):return [{k:o[k] for k in fields}for o in r['operations']]
def board_at(ops,wave,time):
    board={}
    for o in ops:
        if (o['waveOrdinal'],o['timeMs'])>(wave,time):continue
        point=(o['row'],o['col'])
        if o['action']=='sell':board.pop(point,None)
        else:board[point]=o['towerId']
    return board
def op(wave,time,action,point,tid):return dict(waveOrdinal=wave,timeMs=time,action=action,row=point[0],col=point[1],towerId=tid)
def invest(r,ops,wave,time,budget,kind=2,limit=12):
    board=board_at(ops,wave,time);path=r['finalPathCells'];extra=[]
    if kind==1:
        scene=next(x for x in t['tbsceneinfo']if x['id']==r['levelId'])
        mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId'])
        ends={ch:(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch in'SE'}
        a,b=ends['S'],ends['E'];path=[(a[0]+(b[0]-a[0])*j/80,a[1]+(b[1]-a[1])*j/80)for j in range(81)]
    for _ in range(limit):
        choices=[]
        for point,tid in board.items():
            old=tc[tid];new=tc.get(old['upgradeTo'])
            if old['type']!=kind or not new or new['prices']>budget:continue
            if any(o['row']==point[0]and o['col']==point[1]and(o['waveOrdinal'],o['timeMs'])>(wave,time)for o in ops):continue
            cover=sum((.4+j/max(1,len(path)-1))for j,(c,row)in enumerate(path)if(c-point[1])**2+(row-point[0])**2<=new['radius']**2)
            score=cover*(new['power']/new['CD']-old['power']/old['CD'])/new['prices']
            if score:choices.append((score,point,new['id']))
        if not choices:break
        _,point,tid=max(choices);extra.append(op(wave,time,'upgrade',point,tid));budget-=tc[tid]['prices'];board[point]=tid
    ops.extend(extra);ops.sort(key=lambda o:(o['waveOrdinal'],o['timeMs']))
    return extra,budget
def save(r,name,ops,why,detail=None):
    out=REPORT/f'L{r["levelId"]:02}/search-{tag}';out.mkdir(parents=True,exist_ok=True)
    f=out/f'{name}.json';assert not f.exists(),f
    ops.sort(key=lambda o:(o['waveOrdinal'],o['timeMs']))
    f.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=r['levelId'],strategy=f'{tag}-{name}',speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
    notes.append(dict(level=r['levelId'],name=name,sourceRunId=r['metrics']['runId'],sourceIndex=rows.index(r),runtimeContentHash=runtime_hash(),reason=why,detail=detail,tested=False))

# Delayed conversions use observed air completion, with all refunds before builds.
ground=json.loads((REPORT/'requests/ground-r2-c.json').read_text(encoding='utf-8'))
for level,policies in {14:['upgrade3','convert3'],23:['upgrade3','convert6'],29:['upgrade3','convert6'],15:['convert6'],16:['convert6'],19:['convert6'],24:['convert6'],30:['upgrade3']}.items():
    for policy in policies:
        run=next(x for x in ground['runs']if x['levelId']==level and f'-{policy}-'in x['strategy'])
        runs.append(run)
        notes.append(dict(level=level,name=run['strategy'],reason='Independent bounded option from ground-r2-c; air-first one-time ground investment',tested=False))

# Real idle cash in these failures can fund ground output before the final wave.
for index in [12,18,21,22,27]:
    r=rows[index];cash=r['waveBoundaries'][-1]['cash'];ops=plain(r)
    extra,left=invest(r,ops,25,0,max(0,cash-24))
    save(r,'preparation-group-investment',ops,'Spend observed unused final preparation funds; same occupied cells and unchanged route.',dict(observedCash=cash,extra=extra,predictedRemaining=left+24))

# L09 has 395 gold after its six conversions at 15s; spend 330 of that at 16s.
r=rows[13];ops=plain(r);extra,left=invest(r,ops,25,16000,330,limit=3)
save(r,'post-conversion-group',ops,'Strengthen existing group towers before the observed 34.84s ground leak; retain every air tower transaction.',extra)

# L10: compare a preparation allocation with a later one-time conversion.
r=rows[14];ops=plain(r);removed=[o for o in ops if o['waveOrdinal']==25 and o['timeMs']==0 and o['towerId']==3]
assert len(removed)==2
ops=[o for o in ops if o not in removed];extra,left=invest(r,ops,25,0,402,limit=4)
save(r,'redirect-two-normal-upgrades',ops,'Reassign two last-wave 180-gold normal upgrades to real group upgrades before ground leakage at 29.72s.',dict(removed=removed,added=extra,predictedCash=left))

# L25: W21 leaks precede the final wave. Upgrade after observed air completion,
# then invest conservative portions of later observed cash in preparation.
r=rows[25]
for redirect in [False,True]:
    ops=plain(r);removed=[]
    if redirect:
        removed=[o for o in ops if o['waveOrdinal']==21 and o['towerId']==3 and o['row']==4 and o['col']==0]
        assert len(removed)==1;ops=[o for o in ops if o not in removed]
    changes=[]
    extra,left=invest(r,ops,21,34000,330 if redirect else 220,limit=3);changes+=extra
    extra,left=invest(r,ops,22,0,500,limit=4);changes+=extra
    extra,left=invest(r,ops,24,0,850,limit=6);changes+=extra
    extra,left=invest(r,ops,25,0,800,limit=6);changes+=extra
    save(r,'w21-ground-'+('redirect'if redirect else'keep-air'),ops,'W21 last air 32.16s, first ground leak 38.38s. Test 34s investment and later preparation upgrades; real waiting/transactions only.',dict(removed=removed,added=changes))

# L27 fails while retaining 3389 cash. Spend earlier cash on the straight air lane.
r=rows[26]
for budget in [1700,2400]:
    ops=plain(r);changes=[]
    extra,left=invest(r,ops,19,0,budget,kind=1,limit=18);changes+=extra
    extra,left=invest(r,ops,20,0,800,kind=1,limit=6);changes+=extra
    extra,left=invest(r,ops,22,0,1400,limit=10);changes+=extra
    extra,left=invest(r,ops,25,0,1600,limit=12);changes+=extra
    save(r,f'w19-air-{budget}',ops,'W20 air leakage starts at20.84s with3389 idle gold. Upgrade existing air-covered normals before the pressure wave, then test later ground investment.',changes)

request=dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs)
(REPORT/f'requests/{tag}.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-search-bounds.json').write_text(json.dumps(dict(maxRuns=len(runs),termination='one actual replay per listed operation file; preserve all failures',notes=notes),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'unexecuted targeted player-action candidates')
