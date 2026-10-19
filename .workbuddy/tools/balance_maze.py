"""Deterministic legal maze search, maximizing the enemy's actual shortest route.

Finite search reports its budget and an upper bound; it never claims a proof of
the globally longest induced grid path. B/C remain the unmodified map capacity.
"""
import argparse,math,pathlib,random,time,concurrent.futures
from balance_pipeline import path_for,read_json,write_json,generate,DEFAULT_RECIPE
from balance_campaign import capacity

def intervals(cell,path,radius=2):
    inside=[(cell[0]-p[0])**2+(cell[1]-p[1])**2<=radius*radius for p in path]
    return sum(v and (i==0 or not inside[i-1]) for i,v in enumerate(inside))

def search(cells,seed=42,iterations=400,min_towers=0):
    started=time.perf_counter();rng=random.Random(seed)
    free={(x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c=='.'}
    best=None;seen=0;trace=[]
    def evaluate(blocked,label):
        nonlocal best,seen
        seen+=1;p=path_for(cells,blocked)
        if not p:return None
        blocked=set(blocked)
        if len(blocked)<min_towers:
            extras=sorted(free-blocked-set(p))
            if len(blocked)+len(extras)<min_towers:return None
            # Only fill off-route cells after preserving the candidate route.
            blocked.update(extras[:min_towers-len(blocked)])
        reuse=sum(max(0,intervals(c,p)-1) for c in blocked)
        active=sum(intervals(c,p)>0 for c in blocked)
        # Actual route length dominates; tie-break by reusable firing zones and
        # fewer non-participating walls. No tower count enters game ratings.
        key=(len(p),reuse,active,-len(blocked))
        result=(key,blocked,p)
        if best is None or key>best[0]:
            best=result;trace.append({'trial':seen,'source':label,'pathLength':len(p)-1,'towers':len(blocked),'reuse':reuse})
        return result
    evaluate(set(),'empty')
    height=len(cells);width=len(cells[0])
    for vertical in [False,True]:
        across=width if vertical else height;along=height if vertical else width
        for spacing in [2,3,4]:
            for offset in range(1,spacing+1):
                for flip in [0,1]:
                    for gap in [1,2]:
                        blocked=set()
                        for index,line in enumerate(range(offset,across-1,spacing)):
                            opening=range(gap) if (index+flip)%2 else range(along-gap,along)
                            for pos in range(along):
                                cell=(line,pos) if vertical else (pos,line)
                                if pos not in opening and cell in free:blocked.add(cell)
                        evaluate(blocked,'alternating-wall-seed')
    # Best-first mutations include complete wall relocations through pair swaps;
    # single-cell greedy placement alone gets trapped on zero-gain plateaus.
    current=best;temperature=5.;failures=0
    for i in range(iterations):
        if current is None:break
        blocked=set(current[1]);path=current[2]
        removable=sorted(blocked)
        if removable:
            for _ in range(rng.choice([1,1,2,3])):
                if blocked:blocked.remove(rng.choice(sorted(blocked)))
        candidates=[c for c in path if c in free and c not in blocked]
        candidates+=list(sorted(free-blocked))
        for _ in range(rng.choice([1,2,2,3])):
            if candidates:blocked.add(rng.choice(candidates))
        result=evaluate(blocked,'local-rewire')
        if result and (result[0]>current[0] or rng.random()<math.exp(min(0,(result[0][0]-current[0][0])/temperature))):current=result
        else:failures+=1
        if i%40==39:current=best;temperature=max(.5,temperature*.85)
    key,blocked,path=best;rows=[]
    for cell in sorted(blocked):
        without=path_for(cells,blocked-{cell})
        rows.append({'row':cell[1],'col':cell[0],'coveragePasses':intervals(cell,path),
            'coveredPathCells':sum((cell[0]-p[0])**2+(cell[1]-p[1])**2<=4 for p in path),
            'shortcutPreventedSteps':len(path)-len(without) if without else 0})
    audit=capacity(cells)
    return {'seed':seed,'iterations':iterations,'evaluatedLayouts':seen,'elapsedSec':time.perf_counter()-started,
        'searchKind':'Alternating wall seeds plus seeded local rewiring; best found, global optimality unproven',
        'capacity':audit['capacity'],'buildableCells':audit['buildableCells'],'reservedPath':path,
        'pathLength':len(path)-1,'towerCount':len(blocked),'occupancy':len(blocked)/audit['capacity'],
        'simplePathUpperBound':sum(c not in '#X' for row in cells for c in row)-len(blocked)-1,
        'repeatedCoverageTowers':sum(r['coveragePasses']>1 for r in rows),'layout':rows,'improvements':trace,
        'displayCells':[''.join('T' if (x,y) in blocked else '*' if (x,y) in path and c=='.' else c for x,c in enumerate(row)) for y,row in enumerate(cells)]}

def search_board(payload):
    board,iterations,seeds,out=payload
    trials=[search(board['cells'],42+board['id']+i*1009,iterations) for i in range(seeds)]
    row=max(trials,key=lambda r:(r['pathLength'],r['repeatedCoverageTowers'],-r['towerCount']))
    row['levelId']=board['id'];row['mapCells']=board['cells']
    row['searchTrials']=[{k:r[k] for k in ['seed','iterations','evaluatedLayouts','pathLength','towerCount','elapsedSec']} for r in trials]
    add_air_service(board['cells'],row)
    write_json(pathlib.Path(out)/f'L{board["id"]:02}.json',row)
    return row

def add_air_service(cells,row):
    """Reserve effective anti-air positions on short unbendable flying lanes.

    Off-route service towers preserve the best found ground route exactly. A
    radius-2 tangent alone has zero shooting duration, so it does not qualify.
    """
    start,end=row['reservedPath'][0],row['reservedPath'][-1]
    distance=math.dist(start,end)
    if distance>10:return
    samples=[(start[0]+(end[0]-start[0])*i/80,start[1]+(end[1]-start[1])*i/80) for i in range(81)]
    def cov(c):return sum(math.dist(c,p)<1.9 for p in samples)
    blocked={(r['col'],r['row']) for r in row['layout']};path=set(map(tuple,row['reservedPath']))
    useful=[c for c in blocked if cov(c)>8]
    candidates=sorted(((x,y) for y,line in enumerate(cells) for x,c in enumerate(line) if c=='.' and (x,y) not in path|blocked),key=lambda c:(-cov(c),c))
    added=[]
    for c in candidates:
        if len(useful)>=8 or cov(c)<=8:break
        useful.append(c);blocked.add(c);added.append(c)
        row['layout'].append({'row':c[1],'col':c[0],'coveragePasses':intervals(c,row['reservedPath']),
            'coveredPathCells':sum(math.dist(c,p)<=2 for p in row['reservedPath']),
            'shortcutPreventedSteps':0,'purpose':'short-flight-lane interception; ground route unchanged'})
    hints=[{'col':c[0],'row':c[1],'towerId':1} for c in useful]
    if added:
        slow=max(added,key=cov)
        next(h for h in hints if (h['col'],h['row'])==slow)['towerId']=7
    row['towerTypeHints']=hints;row['airServiceAddedCells']=added
    row['towerCount']=len(blocked);row['occupancy']=len(blocked)/row['capacity']
    row['repeatedCoverageTowers']=sum(r['coveragePasses']>1 for r in row['layout'])
    row['simplePathUpperBound']=sum(c not in '#X' for line in cells for c in line)-len(blocked)-1
    row['displayCells']=[''.join('T' if (x,y) in blocked else '*' if (x,y) in path and c=='.' else c for x,c in enumerate(line)) for y,line in enumerate(cells)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',default=str(DEFAULT_RECIPE));ap.add_argument('--out',required=True)
    ap.add_argument('--iterations',type=int,default=400);ap.add_argument('--levels',default='all')
    ap.add_argument('--seeds',type=int,default=1);ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    plan=generate(read_json(args.recipe),'D04');levels=None if args.levels=='all' else set(map(int,args.levels.split(',')))
    rows=[]
    jobs=[(board,args.iterations,args.seeds,args.out) for board in plan['tables']['tblevelmap'] if levels is None or board['id'] in levels]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        for row in executor.map(search_board,jobs):
            rows.append(row);print(row['levelId'],row['pathLength'],row['towerCount'],row['repeatedCoverageTowers'],flush=True)
    write_json(pathlib.Path(args.out)/'index.json',rows)

if __name__=='__main__':main()
