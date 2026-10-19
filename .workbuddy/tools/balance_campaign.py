"""Shared campaign dimensions, persistent identifiers and legal capacity accounting."""
import collections
import copy
import math
import heapq
import json
import pathlib
import functools

def runtime_path_for(cells,blocked=()):
    return list(_runtime_path(tuple(cells),frozenset(map(tuple,blocked))))

@functools.lru_cache(maxsize=4096)
def _runtime_path(cells,blocked):
    """Mirror shipped AStarWrapper: up/down/left/right, first-open equal F.

    The game stops when E enters the open list, rather than when E is popped.
    Heap ties retain each node's original insertion ordinal, including decreases.
    """
    start=next((x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c=='S')
    end=next((x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c=='E')
    opened={start:0};queue=[(0,0,start)];g={start:0};parent={start:None};closed=set();sequence=0
    while queue:
        f,order,cell=heapq.heappop(queue)
        if cell in closed or f!=g[cell]+(0 if cell==start else abs(end[0]-cell[0])+abs(end[1]-cell[1])):continue
        opened.pop(cell,None);closed.add(cell)
        for dx,dy in [(0,1),(0,-1),(-1,0),(1,0)]:
            other=(cell[0]+dx,cell[1]+dy)
            if not (0<=other[1]<len(cells) and 0<=other[0]<len(cells[0])) or cells[other[1]][other[0]] in '#X' or other in blocked or other in closed:continue
            candidate=g[cell]+1
            if other in opened and candidate>=g[other]:continue
            if other not in opened:sequence+=1;opened[other]=sequence
            g[other]=candidate;parent[other]=cell
            heapq.heappush(queue,(candidate+abs(end[0]-other[0])+abs(end[1]-other[1]),opened[other],other))
        if end in opened:
            result=[];cell=end
            while cell is not None:result.append(cell);cell=parent[cell]
            return tuple(reversed(result))
    return ()


def dimensions(recipe):
    levels = int(recipe.get('campaignLevelCount', 20))
    waves = int(recipe.get('wavesPerLevel', 20))
    per_tier = int(recipe.get('levelsPerTier', 4))
    if min(levels, waves, per_tier) <= 0:
        raise ValueError('Campaign dimensions must be positive')
    return levels, waves, per_tier


def prepare_manifest(manifest, baseline):
    """Seed every legacy profile before allocating any new key, regardless of switch order."""
    manifest = copy.deepcopy(manifest)
    manifest['schemaVersion'] = 2
    variants = manifest.setdefault('variants', {})
    manifest.setdefault('rounds', {f'{level}|{wave}': (level-1)*20+wave
        for level in range(1,21) for wave in range(1,21)})
    manifest.setdefault('enemyLists', dict(manifest['rounds']))
    manifest.setdefault('nextIds', {'rounds': 401, 'enemyLists': 401, 'variants': 10000000})
    for category in ['rounds','enemyLists','variants']:
        values = list(manifest[category].values())
        if len(values) != len(set(values)):
            raise ValueError('Persistent manifest contains duplicate ' + category + ' identifiers')
        if any(not isinstance(v,int) or v <= 0 for v in values):
            raise ValueError('Persistent identifiers must be positive integers')
        manifest['nextIds'][category] = max(manifest['nextIds'].get(category,1),max(values,default=0)+1)
    return manifest


def allocate(manifest, category, key, legacy_id=None):
    existing = manifest[category].get(key)
    if existing is not None:
        return existing
    if legacy_id is not None:
        value = legacy_id
        if value in manifest[category].values():
            raise ValueError('Legacy identifier collision: ' + key)
    else:
        value = manifest['nextIds'][category]
        # nextIds is persisted and advances monotonically; validate it once on load.
        manifest['nextIds'][category] = value + 1
    manifest[category][key] = value
    return value


def capacity(cells):
    """0-1 shortest path: minimize reserved buildable cells, not geometric distance."""
    start = next(((x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c == 'S'), None)
    end = next(((x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c == 'E'), None)
    if start is None or end is None or sum(row.count('S') for row in cells)!=1 or sum(row.count('E') for row in cells)!=1:
        raise ValueError('Capacity requires exactly one spawn and exit')
    # Primary weight is still exactly 0/1 buildable cost. Among equal-capacity
    # routes, prefer the ground corridor nearest the straight air corridor. A
    # geometric shortest-path tie that hugs an edge needlessly loses one side
    # of the firing line; the secondary cost does not change q or C.
    queue = [(0,0,start)]; costs = {start: (0,0)}; parents = {start: None}
    axis=(end[0]-start[0],end[1]-start[1]);length=max(1,math.hypot(*axis))
    while queue:
        primary,secondary,current = heapq.heappop(queue)
        if costs[current] != (primary,secondary):continue
        for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
            other = current[0]+dx, current[1]+dy
            if not (0 <= other[1] < len(cells) and 0 <= other[0] < len(cells[0])):
                continue
            char = cells[other[1]][other[0]]
            if char in '#X':
                continue
            weight = int(char == '.')
            offset=abs((other[0]-start[0])*axis[1]-(other[1]-start[1])*axis[0])/length
            new = (primary+weight,secondary+1+offset)
            if new < costs.get(other, (math.inf,math.inf)):
                costs[other] = new; parents[other] = current
                heapq.heappush(queue,(*new,other))
    if end not in costs:
        raise ValueError('Map has no legal ground route')
    route = []; current = end
    while current is not None:
        route.append(current); current = parents[current]
    route.reverse()
    buildable = sum(row.count('.') for row in cells)
    reserved = set(route)
    positions = [(x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c == '.' and (x,y) not in reserved]
    return {'buildableCells': buildable, 'reservedBuildableCells': costs[end][0],
        'capacity': buildable-costs[end][0], 'reservedPath': route, 'maximumLayoutCells': positions}


def economy(plan):
    rows = []
    towers = {tower['id']: tower for tower in plan['tables']['tbtowerinfo']}
    for level in plan['tables']['tbsceneinfo']:
        board = next(m for m in plan['tables']['tblevelmap'] if m['id'] == level['mapId'])
        audit = capacity(board['cells']); total = audit['capacity']
        counts = [math.floor(total*.5), math.floor(total*.3), 0]
        counts[2] = total-sum(counts)
        full_cost = sum(count*towers[tid]['prices'] for count,tid in zip(counts,[1,4,7]))
        income = level['initialGold']; checkpoints = []
        for wave in [w for w in plan['waves'] if w['levelId'] == level['id']]:
            income += wave['killGold'] + wave['rewardGold']
            checkpoints.append({'waveOrdinal': wave['waveOrdinal'], 'perfectCumulativeIncome': income,
                'killGold': wave['killGold'], 'clearGold': wave['rewardGold']})
        reference=plan['recipe'].get('referencePolicy',{})
        maze_root=pathlib.Path(__file__).resolve().parents[2]/reference.get('mazeDirectory','Library/BalanceWorkbench/no-maze')
        maze_path=maze_root/f'L{level["id"]:02}.json'
        maze=json.loads(maze_path.read_text(encoding='utf-8-sig')) if maze_path.is_file() else None
        if maze and maze.get('mapCells')!=board['cells']:maze=None
        maze_audit={}
        if maze:
            pattern=[1,1,4,1,7,1,4,1,7,4]
            maze_cost=sum(towers[pattern[i%len(pattern)]]['prices'] for i in range(maze['towerCount']))
            maze_audit={'mazeTowerCount':maze['towerCount'],'mazeLevelOneCost':maze_cost,
                'mazePathLength':maze['pathLength'],'mazeRepeatedCoverageTowers':maze['repeatedCoverageTowers'],
                'mazeOccupancy':maze['occupancy'],'mazePerfectUpgradeBudgetBeforeFinalWave':checkpoints[-2]['perfectCumulativeIncome']-maze_cost,
                'mazeSearchKind':maze['searchKind']}
        rows.append({'levelId': level['id'], **audit, **maze_audit, 'mixedLevelOneCounts': dict(zip(['normal','power','slow'],counts)),
            'mixedLevelOneCost': full_cost, 'initialGold': level['initialGold'],
            'perfectIncomeBeforeFinalWave': checkpoints[-2]['perfectCumulativeIncome'],
            'upgradeBudgetBeforeFinalWave': checkpoints[-2]['perfectCumulativeIncome']-full_cost,
            'legacyOccupancyComparisonTowers': math.ceil(total*.85), 'incomeCurve': checkpoints,
            'layoutObjective':reference.get('layoutObjective','legacy maximum occupancy'),
            'occupancyEnforced':reference.get('occupancyEnforced',True),
            'coverage': 'static_capacity_and_perfect_income_only; route completion, U and actual reuse require legal replay'})
    return rows
