"""求 S→E 的 Hamilton 路径（遍历所有可走格）。找到即证明最长路径最优。

若存在一条经过全部可走格的简单路径，则最长路径长度 = 可走格数 − 1，无需再搜索。
剪枝：剩余图连通性、度数 0/1 判定、Warnsdorff 邻居排序。
"""
import sys, time
from collections import deque


def solve(cells, time_limit=30.0):
    H, W = len(cells), len(cells[0])
    free, fidx = [], {}
    for y in range(H):
        for x in range(W):
            if cells[y][x] != '#':
                fidx[(x, y)] = len(free)
                free.append((x, y))
    n = len(free)
    adj = [[] for _ in range(n)]
    for i, (x, y) in enumerate(free):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            j = fidx.get((x + dx, y + dy))
            if j is not None:
                adj[i].append(j)
    S = next(i for i, (x, y) in enumerate(free) if cells[y][x] == 'S')
    E = next(i for i, (x, y) in enumerate(free) if cells[y][x] == 'E')

    t0 = time.time()
    visited = [False] * n
    path = []
    done = [False]
    nodes = [0]
    sys.setrecursionlimit(10000)

    def degrees_left(cur):
        """返回 (剩余度数分布, 连通性, 是否可行)。"""
        d1 = []
        cnt = 0
        seen = {cur}
        dq = deque([cur])
        while dq:
            u = dq.popleft()
            for v in adj[u]:
                if not visited[v]:
                    cnt += 1
                    if v not in seen:
                        seen.add(v)
                        dq.append(v)
        # 检查每个未访问格的剩余度数
        reach = len(seen) - 1
        for i in range(n):
            if visited[i]:
                continue
            d = sum(1 for w in adj[i] if not visited[w])
            if d == 0 and i != E:
                return None, reach, False
            if d == 1 and i != E:
                d1.append(i)
        if len(d1) > 2:
            return None, reach, False
        return d1, reach, True

    def dfs(cur, depth):
        if done[0]:
            return
        nodes[0] += 1
        if nodes[0] % 512 == 0 and time.time() - t0 > time_limit:
            return
        if depth == n - 1:
            if cur == E:
                done[0] = True
            return
        if cur == E:
            return
        d1, reach, ok = degrees_left(cur)
        if not ok or depth + reach + 1 < n:
            return
        cand = [v for v in adj[cur] if not visited[v]]
        cand.sort(key=lambda v: sum(1 for w in adj[v] if not visited[w]))
        for v in cand:
            visited[v] = True
            path.append(v)
            dfs(v, depth + 1)
            if done[0]:
                return
            path.pop()
            visited[v] = False

    visited[S] = True
    path.append(S)
    dfs(S, 0)
    return {
        'n': n, 'path': [free[i] for i in path] if done[0] else None,
        'found': done[0], 'bestLen': len(path) - 1 if done[0] else None,
        'nodes': nodes[0], 'elapsed': time.time() - t0,
    }


if __name__ == '__main__':
    import json, io
    lm = {m['levelId']: m for m in json.load(io.open(
        'E:/MyTowerGame/Assets/ConfigJson/tblevelmap.json', encoding='utf-8'))}
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    r = solve(lm[L]['cells'], time_limit=float(sys.argv[2]) if len(sys.argv) > 2 else 30)
    print('L%d 可走=%d 找到Hamilton=%s 路径=%s 节点=%d 用时=%.2fs'
          % (L, r['n'], r['found'], r['bestLen'], r['nodes'], r['elapsed']))
