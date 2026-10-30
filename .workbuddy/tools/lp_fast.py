"""逐关求最长诱导路径：度数剪枝版 DFS。

核心剪枝：任何未访问、剩余度数=1 且不是终点的格子，路径进去就出不来 → 立即失败。
维护 ones 集合与 deg 增量，避免每次全图扫描。
"""
import sys, time
from collections import deque


def peel(cells):
    """剥离死胡同：度数 1 的非端点格必须放弃。返回保留集合。"""
    H, W = len(cells), len(cells[0])
    free = {(x, y) for y in range(H) for x in range(W) if cells[y][x] != '#'}
    S = next(c for c in free if cells[c[1]][c[0]] == 'S')
    E = next(c for c in free if cells[c[1]][c[0]] == 'E')
    keep = set(free)
    changed = True
    while changed:
        changed = False
        for c in list(keep):
            if c == S or c == E:
                continue
            d = sum(1 for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)) if (c[0]+dx, c[1]+dy) in keep)
            if d <= 1:
                keep.discard(c)
                changed = True
    return keep, S, E


def solve(cells, time_limit=60.0, max_len=None):
    keep, S, E = peel(cells)
    idx = {c: i for i, c in enumerate(sorted(keep))}
    free = sorted(keep)
    n = len(free)
    adj = [tuple(idx[(x+dx, y+dy)] for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))
                 if (x+dx, y+dy) in idx) for (x, y) in free]
    s, e = idx[S], idx[E]
    deg = [len(a) for a in adj]
    vis = bytearray(n)
    vis[s] = 1
    for v in adj[s]:
        deg[v] -= 1
    path = [s]
    best = [s]
    t0 = time.time()
    nodes = 0
    stop = False

    def dfs(cur, depth):
        nonlocal nodes, stop
        if stop:
            return
        nodes += 1
        if (nodes & 63) == 0 and (time.time() - t0 > time_limit or nodes > 6000000):
            stop = True
            return
        if depth > len(best):
            best[:] = path[:]
        if depth == n - 1:
            return
        if max_len is not None and depth + 1 >= max_len:
            return
        # 死格判定：deg==0 的未访问格（非 E）永远进不去；
        # deg==1 的未访问格若不在当前点的邻居里，也进不去（进去无出口）。
        nb = set(adj[cur])
        ones = 0
        for v in range(n):
            if vis[v] or v == e:
                continue
            if deg[v] == 0:
                return
            if deg[v] == 1:
                if v not in nb:
                    return
                ones += 1
        if ones > 1:
            return
        cand = [v for v in adj[cur] if not vis[v]]
        cand.sort(key=lambda v: deg[v])
        for v in cand:
            vis[v] = 1
            path.append(v)
            for w in adj[v]:
                if not vis[w]:
                    deg[w] -= 1
            dfs(v, depth + 1)
            for w in adj[v]:
                if not vis[w]:
                    deg[w] += 1
            path.pop()
            vis[v] = 0
            if stop:
                return

    dfs(s, 0)
    return {'n': n, 'peeled': len(cells[0]) and None, 'bestLen': len(best) - 1,
            'path': [free[i] for i in best], 'nodes': nodes,
            'elapsed': time.time() - t0, 'timedout': stop}


if __name__ == '__main__':
    import json, io
    lm = {m['levelId']: m for m in json.load(io.open(
        'E:/MyTowerGame/Assets/ConfigJson/tblevelmap.json', encoding='utf-8'))}
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    cells = lm[L]['cells']
    keep, S, E = peel(cells)
    r = solve(cells, time_limit=tl)
    print('L%d 原始可走=%d 剥离后=%d 当前最优=%d 节点=%d 用时=%.1fs 超时=%s'
          % (L, sum(1 for row in cells for c in row if c != '#'), r['n'], r['bestLen'], r['nodes'], r['elapsed'], r['timedout']))
