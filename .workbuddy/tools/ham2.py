"""逐关求 S→E 的 Hamilton 路径（遍历全部可走格）。找到即最长解 = n−1。

只保留两类剪枝：剩余图连通性、当前点邻居的度数 0/1 判定。
Warnsdorff 排序。带时间上限。
"""
import sys, time
from collections import deque


def solve(cells, time_limit=60.0):
    H, W = len(cells), len(cells[0])
    free, fidx = [], {}
    for y in range(H):
        for x in range(W):
            if cells[y][x] != '#':
                fidx[(x, y)] = len(free)
                free.append((x, y))
    n = len(free)
    adj = [tuple(fidx[(x+dx, y+dy)] for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))
                 if (x+dx, y+dy) in fidx) for (x, y) in free]
    S = next(i for i, (x, y) in enumerate(free) if cells[y][x] == 'S')
    E = next(i for i, (x, y) in enumerate(free) if cells[y][x] == 'E')

    t0 = time.time()
    visited = bytearray(n)
    path = [S]
    visited[S] = 1
    done = [False]
    nodes = [0]
    sys.setrecursionlimit(20000)

    def dfs(cur, depth):
        if done[0]:
            return
        nodes[0] += 1
        if (nodes[0] & 1023) == 0 and time.time() - t0 > time_limit:
            return
        if depth == n - 1:
            if cur == E:
                done[0] = True
            return
        if cur == E:
            return
        # 连通性：未访问部分必须仍连通，且能连到 E
        seen = bytearray(n)
        seen[cur] = 1
        dq = deque([cur])
        cnt = 0
        hit = False
        while dq:
            u = dq.popleft()
            for v in adj[u]:
                if not visited[v] and not seen[v]:
                    seen[v] = 1
                    cnt += 1
                    if v == E:
                        hit = True
                    dq.append(v)
        if not hit or depth + cnt + 1 < n:
            return
        cand = [v for v in adj[cur] if not visited[v]]
        cand.sort(key=lambda v: sum(1 for w in adj[v] if not visited[w]))
        for v in cand:
            visited[v] = 1
            path.append(v)
            dfs(v, depth + 1)
            if done[0]:
                return
            path.pop()
            visited[v] = 0

    dfs(S, 0)
    return {'n': n, 'found': done[0], 'path': [free[i] for i in path] if done[0] else None,
            'bestLen': len(path) - 1 if done[0] else None,
            'nodes': nodes[0], 'elapsed': time.time() - t0}


if __name__ == '__main__':
    import json, io
    lm = {m['levelId']: m for m in json.load(io.open(
        'E:/MyTowerGame/Assets/ConfigJson/tblevelmap.json', encoding='utf-8'))}
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    r = solve(lm[L]['cells'], time_limit=tl)
    print('L%d 可走=%d Hamilton=%s 长度=%s 节点=%d 用时=%.1fs'
          % (L, r['n'], r['found'], r['bestLen'], r['nodes'], r['elapsed']))
