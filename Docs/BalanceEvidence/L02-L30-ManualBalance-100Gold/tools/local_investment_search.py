"""Reallocate final-wave purchases and enumerate new legal tower positions, read-only."""
from formal_tools import *
import collections,math,sys
levels=list(map(int,sys.argv[1:]));t=tables();tc={x['id']:x for x in t['tbtowerinfo']};sc={x['id']:x for x in t['tbsceneinfo']};maps={x['id']:x for x in t['tblevelmap']};runs=[];decisions=[]
for level in levels:
    source=ROOT/'Library/BalanceWorkbench'/('manual-campaign-r1-L04'if level==4 else 'campaign-r1-L05-L12')/'unity-results.json'
    choices=[r for r in json.loads(source.read_text(encoding='utf-8'))if r['levelId']==level and r['metrics']['completedWaveCount']>=24 and not r['pendingOperations']]
    if not choices:continue
    r=min(choices,key=lambda x:(x['metrics']['leaked'],-x['metrics']['killed']));base=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    assert not any(o['waveOrdinal']==25 and o['timeMs']>0 for o in base)
    mp=maps[sc[level]['mapId']];cells=mp['cells'];points={ch:(c,row)for row,line in enumerate(cells)for c,ch in enumerate(line)if ch in 'SE'};S=points['S'];E=points['E']
    def path_for(board):
        queue=collections.deque([S]);previous={S:None}
        while queue:
            p=queue.popleft()
            if p==E:
                result=[]
                while p is not None:result.append(p);p=previous[p]
                return result[::-1]
            for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
                q=(p[0]+dx,p[1]+dy)
                if 0<=q[0]<mp['cols']and 0<=q[1]<mp['rows']and cells[q[1]][q[0]]in'.SE'and q not in board and q not in previous:previous[q]=p;queue.append(q)
        return []
    def aircoverage(cell,radius):return sum((S[0]+(E[0]-S[0])*k/80-cell[0])**2+(S[1]+(E[1]-S[1])*k/80-cell[1])**2<=radius**2 for k in range(81))
    def pick(board,tid,airweight):
        best=None
        for row,line in enumerate(cells):
            for col,ch in enumerate(line):
                cell=(col,row)
                if ch!='.'or cell in board:continue
                board[cell]=tid;path=path_for(board);del board[cell]
                if not path:continue
                cfg=tc[tid];ground=sum((c-col)**2+(rr-row)**2<=cfg['radius']**2 for c,rr in path)
                air=aircoverage(cell,cfg['radius'])if cfg['canAttackAir']else 0
                slow_penalty=sum(20 for (c,rr),i in board.items()if tc[i]['type']==3 and(c-col)**2+(rr-row)**2<3.5**2)if cfg['type']==3 else 0
                # Price-independent placement choice; payment still uses actual runtime prices.
                score=ground+len(path)*.8+air*airweight-slow_penalty+((col-S[0])*(E[0]-S[0])+(row-S[1])*(E[1]-S[1]))*.002
                value=(score,col,row)
                if best is None or value>best:best=value
        return None if best is None else(best[1],best[2])
    out=REPORT/f'L{level:02}/search-investment-r3';out.mkdir(parents=True,exist_ok=False)
    variants=[('extra-air',False,0,[1],1.2),('redirect-aoe',True,2,[1],1.0),('redirect-build',True,0,[1,4,1,7,1,4],.7),('extra-group',False,0,[4,1],.4)]
    if level==4:variants=[('air-pair-a',False,0,[(4,2),(4,4)],0),('air-pair-b',False,0,[(3,2),(5,2)],0),('air-pair-c',False,0,[(4,10),(4,12)],0),('air-pair-greedy',False,0,[1],1.2)]
    for name,redirect,upgrade_count,builds,weight in variants:
        removed=[o for o in r['operations']if redirect and o['waveOrdinal']==25 and o['action']=='upgrade']
        ops=[o for o in base if not(redirect and o['waveOrdinal']==25 and o['action']=='upgrade')];board={}
        for o in ops:
            key=(o['col'],o['row'])
            if o['action']=='sell':del board[key]
            else:board[key]=o['towerId']
        budget=r['waveBoundaries'][-1]['cash']+sum(o['cost']for o in removed);extra=[]
        def add(action,cell,tid,time=0):
            extra.append(dict(waveOrdinal=25,timeMs=time,action=action,row=cell[1],col=cell[0],towerId=tid))
        if upgrade_count:
            path=path_for(board);choices=[]
            for cell,tid in board.items():
                if tc[tid]['type']!=2 or not tc[tid]['upgradeTo']:continue
                new=tc[tc[tid]['upgradeTo']];cover=sum((c-cell[0])**2+(rr-cell[1])**2<=new['radius']**2 for c,rr in path)
                choices.append((cover*(new['power']/new['CD']-tc[tid]['power']/tc[tid]['CD'])/new['prices'],cell,new['id']))
            for _,cell,tid in sorted(choices,reverse=True)[:upgrade_count]:
                if budget>=tc[tid]['prices']:add('upgrade',cell,tid);budget-=tc[tid]['prices'];board[cell]=tid
        if level==4 and isinstance(builds[0],tuple):
            for row,col in builds:
                cell=(col,row);assert cell not in board and budget>=32;board[cell]=1
                add('build',cell,1);budget-=32
        else:
            for i in range(12):
                tid=builds[i%len(builds)]
                if budget<tc[tid]['prices']:break
                cell=pick(board,tid,weight)
                if cell is None:break
                add('build',cell,tid);board[cell]=tid;budget-=tc[tid]['prices']
        if level==4:
            late=[(6,1,3),(5,1,3),(1,3,2),(3,1,3),(4,7,3),(5,9,3)]
            for row,col,tid in late:add('sell',(col,row),tid,40000)
            for row,col,tid in late:add('build',(col,row),4,40000)
            for row,col,tid in late:
                if tid==3:add('upgrade',(col,row),5,40000)
        ops+=extra;ops.sort(key=lambda o:(o['waveOrdinal'],o['timeMs']));path=out/f'{name}.json';path.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
        runs.append(dict(profileId='D04',levelId=level,strategy=f'investment-r3-{name}',speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True,captureStages=True))
        decisions.append(dict(level=level,variant=name,sourceRunId=r['metrics']['runId'],removed=removed,extra=extra,predictedUnspentAtBoundary=budget))
request=REPORT/'requests/investment-r3.json';request.write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench/investment-r3'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8');(REPORT/'audit/investment-r3-decisions.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8');print(len(runs),'bounded investment trials')
