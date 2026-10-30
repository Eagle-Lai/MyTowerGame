"""精确求 S→E 最长简单路径（= 最大诱导路径布局下的敌人最短路）。

网格四连通，'#' 不可走。求一条不重复经过格子的 S→E 路径，使长度最大；
其余可走格全部建塔。路径长度即敌人实际最短路径格数。

DFS + 三项剪枝：可达格数上界、E 可达性、Warnsdorff 邻居排序。
带时间限制；搜索空间耗尽即证明最优，否则报"时间上限内最好"。
"""
import sys, time
from collections import deque


def solve(cells, time_limit=60.0, verbose=False):
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

    color = [(free[i][0] + free[i][1]) & 1 for i in range(n)]
    remB = sum(1 for i in range(n) if color[i] == 0)
    remW = n - remB
    cE = color[E]

    t0 = time.time()
    visited = [False] * n
    path = []
    best = []
    done = [False]
    nodes = [0]

    def reachable(cur, budget):
        seen = {cur}
        dq = deque([cur])
        cnt = 0
        hit_e = False
        while dq and cnt <= budget:
            u = dq.popleft()
            for v in adj[u]:
                if v not in seen and not visited[v]:
                    seen.add(v)
                    cnt += 1
                    if v == E:
                        hit_e = True
                    dq.append(v)
            if cnt > budget:
                break
        return cnt, hit_e

    # 贪心初始解：Warnsdorff + 远离 E 优先，尽量绕远
    def greedy():
        vis = [False] * n
        p = [S]
        vis[S] = True
        cur = S
        while cur != E:
            cand = [v for v in adj[cur] if not vis[v]]
            if not cand:
                break
            def key(v):
                deg = sum(1 for w in adj[v] if not vis[w])
                ex, ey = free[E]; vx, vy = free[v]
                return (deg, -abs(vx - ex) - abs(vy - ey))
            cand.sort(key=key)
            cur = cand[0]
            vis[cur] = True
            p.append(cur)
        return p

    g = greedy()
    if g and g[-1] == E:
        best.extend(g)

    sys.setrecursionlimit(10000)

    def parity_bound(cur):
        # 棋盘染色：从 cur 出发，后续格必须黑白交替。
        # 剩余可走步数受 min(剩余黑, 剩余白) 与 E 的颜色奇偶双重限制。
        if color[cur] == 0:
            cap = 2 * min(remW, remB) + (1 if remW > remB else 0)
        else:
            cap = 2 * min(remB, remW) + (1 if remB > remW else 0)
        # 走到 E 的步数奇偶必须匹配
        need = (cE ^ color[cur]) & 1
        if cap > 0 and (cap & 1) != need:
            cap -= 1
        return cap

    def dfs(cur, depth, budget_cap):
        nonlocal remB, remW
        if done[0]:
            return
        nodes[0] += 1
        if nodes[0] % 2048 == 0:
            if time.time() - t0 > time_limit:
                done[0] = True
                return
        if cur == E:
            if depth > len(best):
                best[:] = path[:]
            return
        if depth >= budget_cap:
            return
        cap = parity_bound(cur)
        if depth + cap + 1 <= len(best):
            return
        cnt, hit_e = reachable(cur, min(budget_cap - depth, cap))
        if not hit_e or depth + cnt + 1 <= len(best):
            return
        cand = [v for v in adj[cur] if not visited[v]]
        cand.sort(key=lambda v: sum(1 for w in adj[v] if not visited[w]))
        for v in cand:
            visited[v] = True
            path.append(v)
            if color[v] == 0:
                remB -= 1
            else:
                remW -= 1
            dfs(v, depth + 1, budget_cap)
            if color[v] == 0:
                remB += 1
            else:
                remW += 1
            path.pop()
            visited[v] = False
            if done[0]:
                return

    visited[S] = True
    path.append(S)
    dfs(S, 0, n - 1)

    return {
        'S': free[S], 'E': free[E],
        'nFree': n,
        'bestLen': len(best) - 1,
        'path': [free[i] for i in best],
        'proven': not done[0],
        'upperBound': n - 1,
        'nodes': nodes[0],
        'elapsed': time.time() - t0,
    }


if __name__ == '__main__':
    import json, io, pathlib
    lm = {m['levelId']: m for m in json.load(io.open(
        'E:/MyTowerGame/Assets/ConfigJson/tblevelmap.json', encoding='utf-8'))}
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    cells = lm[L]['cells']
    r = solve(cells, time_limit=tl)
    print('L%d  可走格=%d  最优路径=%d  上界=%d  证明最优=%s  节点=%d  用时=%.1fs'
          % (L, r['nFree'], r['bestLen'], r['upperBound'], r['proven'], r['nodes'], r['elapsed']))
