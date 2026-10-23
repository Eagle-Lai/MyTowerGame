"""Search bounded legal final-wave route extensions; no game-data writes."""
from formal_tools import *
import collections,sys,math
tag=sys.argv[1];source=ROOT/'Library/BalanceWorkbench/references-r2-a/unity-results.json'
actual=json.loads(source.read_text(encoding='utf-8'));t=tables();tc={x['id']:x for x in t['tbtowerinfo']};runs=[];notes=[]
requested=list(map(int,sys.argv[2:]))if len(sys.argv)>2 else[8,10,15,16,19,24]
for index in [i for i in [12,13,14,16,17,18,19,22,24,25,27]if actual[i]['levelId']in requested]:
    r=actual[index];level=r['levelId'];scene=next(x for x in t['tbsceneinfo']if x['id']==level);mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId']);cells=mp['cells']
    ends={ch:(c,row)for row,line in enumerate(cells)for c,ch in enumerate(line)if ch in'SE'};S,E=ends['S'],ends['E']
    original=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    assert level==9 or not any(o['waveOrdinal']==25 and o['timeMs']for o in original)
    phase=21 if level==25 else 25
    # Preserve cells involved in a sale/build chain. Independent normal upgrades
    # in preparation can instead buy new route-shaping low-tier towers.
    replacements={(o['row'],o['col'])for o in original if o['waveOrdinal']==phase and o['action']in['sell','build']}
    removed=[o for o in r['operations']if o['waveOrdinal']==phase and o['action']=='upgrade'and tc[o['towerId']]['type']==1 and(o['row'],o['col'])not in replacements]
    stripped=[o for o in original if not(o['waveOrdinal']==phase and o['action']=='upgrade'and tc[o['towerId']]['type']==1 and(o['row'],o['col'])not in replacements)]
    budget=next(b['cash']for b in r['waveBoundaries']if b['beforeWave']==phase)+sum(o['cost']for o in removed)
    insertion=0
    if level==9:
        stripped=list(original);removed=[];budget=[o['balanceAfter']for o in r['operations']if o['waveOrdinal']==25][-1];insertion=16000
    def board_of(ops):
        board={}
        for o in ops:
            p=(o['col'],o['row'])
            if o['action']=='sell':assert board.pop(p)==o['towerId']
            else:board[p]=o['towerId']
        return board
    def path_for(board):
        todo=collections.deque([S]);prev={S:None}
        while todo:
            p=todo.popleft()
            if p==E:
                path=[]
                while p is not None:path.append(p);p=prev[p]
                return path[::-1]
            for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
                q=p[0]+dx,p[1]+dy
                if 0<=q[0]<mp['cols']and 0<=q[1]<mp['rows']and cells[q[1]][q[0]]in'.SE'and q not in board and q not in prev:prev[q]=p;todo.append(q)
        return []
    def coverage(point,path,tid):return sum((.3+j/max(1,len(path)-1))for j,(c,row)in enumerate(path)if(c-point[0])**2+(row-point[1])**2<=tc[tid]['radius']**2)
    out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=False)
    for name,sequence in [('ordinary-route',[1]),('mixed-route',[4,1,4,1])]:
        ops=list(stripped);board=board_of(ops);cash=budget;added=[]
        for n in range(20):
            tid=sequence[n%len(sequence)]
            if cash<tc[tid]['prices']:break
            path=path_for(board);best=None
            # Two placements of lookahead overcome equal-length alternate paths.
            for p in path:
                if cells[p[1]][p[0]]!='.'or p in board:continue
                board[p]=tid;first=path_for(board)
                if not first:del board[p];continue
                future=len(first)
                if cash>=2*tc[tid]['prices']:
                    for q in first:
                        if cells[q[1]][q[0]]!='.'or q in board:continue
                        board[q]=tid;second=path_for(board);del board[q]
                        if second:future=max(future,len(second))
                del board[p]
                score=3*future+1.5*len(first)+coverage(p,first,tid)
                option=score,p,first
                if best is None or option[:2]>best[:2]:best=option
            if best is None:break
            _,point,predicted=best;board[point]=tid;cash-=tc[tid]['prices']
            added.append(dict(waveOrdinal=phase,timeMs=insertion,action='build',row=point[1],col=point[0],towerId=tid))
        ops.extend(added)
        def strengthen_group(wave,time,available):
            extra=[];path=path_for(board)
            for _ in range(20):
                upgrades=[]
                for point,tid in board.items():
                    new=tc.get(tc[tid]['upgradeTo'])
                    if tc[tid]['type']!=2 or not new or new['prices']>available:continue
                    if any(o['row']==point[1]and o['col']==point[0]and(o['waveOrdinal'],o['timeMs'])>(wave,time)for o in ops):continue
                    score=coverage(point,path,new['id'])*(new['power']/new['CD']-tc[tid]['power']/tc[tid]['CD'])/new['prices']
                    if score:upgrades.append((score,point,new['id']))
                if not upgrades:break
                _,point,tid=max(upgrades);available-=tc[tid]['prices'];board[point]=tid
                extra.append(dict(waveOrdinal=wave,timeMs=time,action='upgrade',row=point[1],col=point[0],towerId=tid))
            ops.extend(extra);return extra,available
        reinvested=[]
        if level==25:
            extra,left=strengthen_group(22,0,500);reinvested+=extra
            extra,left=strengthen_group(25,0,1500);reinvested+=extra
        else:
            reserve=min(24,cash);extra,cash=strengthen_group(phase,insertion,cash-reserve);reinvested+=extra;cash+=reserve
        # One-time late conversion remains an independent bounded alternative.
        finalpath=path_for(board);start=round(r['metrics']['waves'][-1]['combatStartSeconds']*1000)
        timing=math.ceil((max([e['combatMs']-start for e in r['enemyOutcomes']if e['waveOrdinal']==25 and e['isFlying']]or[0])+2000)/1000)*1000
        for convert in [False,True]:
            candidate=list(ops);late=[]
            if convert:
                choices=sorted([(coverage(p,finalpath,5),p,tid)for p,tid in board.items()if tc[tid]['type']==1 and tc[tid]['level']>=2],reverse=True)[:6]
                for _,p,tid in choices:late.append(dict(waveOrdinal=25,timeMs=timing,action='sell',row=p[1],col=p[0],towerId=tid))
                for _,p,tid in choices:late.append(dict(waveOrdinal=25,timeMs=timing,action='build',row=p[1],col=p[0],towerId=4))
                for _,p,tid in choices:
                    if tc[tid]['level']==3:late.append(dict(waveOrdinal=25,timeMs=timing,action='upgrade',row=p[1],col=p[0],towerId=5))
            candidate+=late;candidate.sort(key=lambda o:(o['waveOrdinal'],o['timeMs']));variant=name+('-late6'if convert else'-retain-air');f=out/f'{variant}.json';f.write_text(json.dumps(candidate,ensure_ascii=False,indent=2),encoding='utf-8')
            runs.append(dict(profileId='D04',levelId=level,strategy=f'{tag}-{variant}',speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
            notes.append(dict(level=level,name=variant,sourceRunId=r['metrics']['runId'],changedFromWave=phase,removed=removed,added=added,reinvested=reinvested,late=late,observedOriginalRouteEdges=len(r['finalPathCells'])-1,predictedRouteEdges=len(finalpath)-1,preparationBudget=budget,predictedPreparationCash=cash,predictionOnly=True,scope='Earlier waves unchanged. Formal data unchanged. BFS route is a placement prediction; actual Unity AStar and real transactions determine outcome.'))
request=dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs)
(REPORT/f'requests/{tag}.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(maxRuns=len(runs),termination='One real run per listed candidate; no assertion of global strategy exhaustion',decisions=notes),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'unexecuted route-extension candidates')
