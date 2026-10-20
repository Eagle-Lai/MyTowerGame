"""Occupancy-ladder gate runner for the FreedomTower balance campaign.

Why the ladder is a fraction of a maze blueprint
------------------------------------------------
The campaign keeps the "build towers to reroute the monsters" mechanic, so the
maximum useful garrison is NOT every buildable cell: cells that never touch the
corridor cannot shoot, and cells dropped into the corridor cut it short. The
reference garrison is therefore an explicit serpentine wall blueprint, and the
ladder asks how much of that maze must exist:

  G1  50% of the maze must fail          G2  70% of the maze must fail
  G3  85% of the maze must not five-star
  G4  100% of the maze + upgrades must five-star inside the Par band
  G5  100% of the maze without upgrades must not five-star

The blueprint is generated deterministically and never published to the game; it
is only the yardstick used to compare tower counts.

  python balance_fill_gate.py run --levels 1,6,10,15,24,30 --out <dir> [--workers 6]
  python balance_fill_gate.py report --run <dir> [--markdown <file>]
  python balance_fill_gate.py preflight --recipe <json> --out <dir>
"""
import argparse, concurrent.futures as cf, copy, json, pathlib, sys, time

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import balance_pipeline as bp
import balance_simulator as sim
from balance_campaign import capacity, runtime_path_for

DEFAULT_RECIPE = str(bp.DEFAULT_RECIPE)
DEFAULT_LADDER = [0.5, 0.7, 0.85, 1.0]
MODE_FILL, MODE_NOUP = 'fill', 'no_upgrade'
AIR_POSTS = 8


# ---------------------------------------------------------------- layout
def _positions(cells, char):
    for r, row in enumerate(cells):
        for c, ch in enumerate(row):
            if ch == char:
                return (c, r)
    return None


def _straight(a, b, step=0.5):
    n = max(1, int((abs(a[0] - b[0]) ** 2 + abs(a[1] - b[1]) ** 2) ** 0.5 / step))
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def _cover(cell, points, radius):
    r2 = radius * radius
    return sum((cell[0] - p[0]) ** 2 + (cell[1] - p[1]) ** 2 <= r2 for p in points)


def augment_layout(cells, walls, radius=2.0):
    """Blind-spot repair for the reference garrison.

    The finger walls cover the ground corridor but leave the straight air lane and
    the finger gaps uncovered, which no amount of extra HP can fix. Greedily add
    legal cells that hit the most still-uncovered corridor / air-lane points. These
    are exactly the "sentry" towers a human builds, so the reference stays honest.
    """
    path = runtime_path_for(cells, walls)
    if not path:
        return walls
    ground = list(path)
    air = _straight(path[0], path[-1])
    chosen = list(walls)
    blocked = set(chosen) | {tuple(path[0]), tuple(path[-1])}
    free = [(c, r) for r, row in enumerate(cells) for c, ch in enumerate(row)
            if ch == '.' and (c, r) not in blocked]
    for _ in range(len(free)):
        uncovered_g = [p for p in ground if not any(
            (t[0] - p[0]) ** 2 + (t[1] - p[1]) ** 2 <= radius * radius for t in chosen)]
        uncovered_a = [p for p in air if not any(
            (t[0] - p[0]) ** 2 + (t[1] - p[1]) ** 2 <= radius * radius for t in chosen)]
        if not uncovered_g and not uncovered_a:
            break
        best, best_key = None, None
        for cell in free:
            if cell in blocked:
                continue
            if not runtime_path_for(cells, chosen + [cell]):
                continue
            key = (_cover(cell, uncovered_g, radius) + 2 * _cover(cell, uncovered_a, radius),
                   -abs(cell[0] - len(cells[0]) / 2) - abs(cell[1] - len(cells) / 2))
            if best_key is None or key > best_key:
                best, best_key = cell, key
        if best is None or best_key[0] <= 0:
            break
        chosen.append(best)
        blocked.add(best)
    # Air sentries: the flying lane is a straight S->E line, so a wall-based maze
    # can leave it almost uncovered. Plant posts along the lane every ~2 cells,
    # exactly like a player would build a second, anti-air line.
    posts = []
    for point in air[::2]:
        if any((q[0] - point[0]) ** 2 + (q[1] - point[1]) ** 2 <= 4.0 for q in posts):
            continue
        best, best_key = None, None
        for cell in free:
            if cell in blocked:
                continue
            dist = (cell[0] - point[0]) ** 2 + (cell[1] - point[1]) ** 2
            if dist > radius * radius:
                continue
            if not runtime_path_for(cells, chosen + [cell]):
                continue
            key = (-dist, -len([q for q in air
                                if (cell[0] - q[0]) ** 2 + (cell[1] - q[1]) ** 2 <= radius * radius]))
            if best_key is None or key > best_key:
                best, best_key = cell, key
        if best is not None:
            chosen.append(best)
            blocked.add(best)
            posts.append(best)
    return chosen


def snake_walls(cells, spacing=2, augment=True):
    """Deterministic serpentine wall blueprint for a single-entry open grid.

    Vertical fingers alternate a top gap and a bottom gap, then a repair pass
    refuses any cell that would sever the corridor. With `augment`, sentry cells
    are appended to cover the air lane and the finger gaps.
    """
    rows, cols = len(cells), len(cells[0])
    spawn, end = _positions(cells, 'S'), _positions(cells, 'E')
    candidates, flip = [], 0
    if abs(end[0] - spawn[0]) >= abs(end[1] - spawn[1]):
        # Horizontal corridor: vertical fingers, gap alternating bottom / top.
        step = spacing if end[0] > spawn[0] else -spacing
        column = spawn[0] + step
        while (column < end[0]) if step > 0 else (column > end[0]):
            rng = range(0, rows - 1) if flip == 0 else range(1, rows)
            for r in rng:
                if cells[r][column] == '.':
                    candidates.append((column, r))
            flip ^= 1
            column += step
    else:
        # Vertical corridor: horizontal fingers, gap alternating right / left.
        step = spacing if end[1] > spawn[1] else -spacing
        row = spawn[1] + step
        while (row < end[1]) if step > 0 else (row > end[1]):
            rng = range(0, cols - 1) if flip == 0 else range(1, cols)
            for c in rng:
                if cells[row][c] == '.':
                    candidates.append((c, row))
            flip ^= 1
            row += step
    walls = []
    for cell in candidates:
        if runtime_path_for(cells, walls + [cell]):
            walls.append(cell)
    if not augment:
        return walls
    fingers = list(walls)
    full = augment_layout(cells, fingers)
    sentries = full[len(fingers):]
    # Interleave sentries with fingers so a partially built maze still covers the
    # air lane and the finger gaps; otherwise the ladder is non-monotonic.
    mixed = []
    for i in range(max(len(fingers), len(sentries))):
        if i < len(fingers):
            mixed.append(fingers[i])
        if i < len(sentries):
            mixed.append(sentries[i])
    return mixed


def level_map(plan, level):
    scene = next(s for s in plan['tables']['tbsceneinfo'] if s['id'] == level)
    return next(m for m in plan['tables']['tblevelmap'] if m['id'] == scene['mapId'])


def unit_price(plan):
    table = {t['id']: t for t in plan['tables']['tbtowerinfo']}
    return 0.5 * table[1]['prices'] + 0.3 * table[4]['prices'] + 0.2 * table[7]['prices']


_MAZE_CACHE = {}


def maze_for(plan, level):
    key = (id(plan), level)
    if key not in _MAZE_CACHE:
        cells = level_map(plan, level)['cells']
        _MAZE_CACHE[key] = (cells, snake_walls(cells))
    return _MAZE_CACHE[key]


def make_policy(plan, level, fraction, mode, upgrade_budget=None):
    cells, walls = maze_for(plan, level)
    target = max(1, min(len(walls), int(round(len(walls) * fraction))))
    policy = {
        'capacity': capacity(cells)['capacity'],
        'targetCount': target,
        'maxTowers': target,
        'blueprintCells': [list(c) for c in walls[:target]],
        'types': [1, 1, 4, 1, 7, 1, 4, 1, 7, 4],
        'upgradeShare': 0.0,
        'preferUpgrade': False,
        'midwaveUpgrades': False,
        'upgradeAfter': target,
        'maxWallSeconds': 900,
        'trackReentry': True,
    }
    if mode == MODE_NOUP:
        policy['forbidUpgrades'] = True
    elif upgrade_budget is not None:
        policy['upgradeBudgetGold'] = int(upgrade_budget)
    return policy, target, len(walls)


# ---------------------------------------------------------------- worker
_WORKER = {}


def _init_worker(recipe_path, step_ms, out_root, resume=False):
    recipe = bp.read_json(recipe_path)
    _WORKER['plan'] = bp.generate(recipe, recipe.get('selectedProfileId', 'D04'))
    _WORKER['step_ms'] = step_ms
    _WORKER['out'] = out_root
    _WORKER['resume'] = resume


def _run_one(task):
    plan = _WORKER['plan']
    level, fraction, mode, seed, budget = task
    hash_now = plan['levels'][level - 1].get('combatBasisHash')
    out = pathlib.Path(_WORKER['out']) / 'runs' / ('L%02d' % level) / ('%s@%.2f' % (mode, fraction)) / ('seed%d' % seed)
    sidecar = out / 'gate-row.json'
    if _WORKER.get('resume') and sidecar.exists():
        previous = bp.read_json(sidecar, {})
        if previous.get('combatBasisHash') == hash_now:
            previous['reused'] = True
            return previous
    policy, target, maze_size = make_policy(plan, level, fraction, mode, budget)
    sim.POLICY = copy.deepcopy(policy)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    try:
        res = sim.simulate_level(plan, level, 'mixed', _WORKER['step_ms'], out, seed=seed)
    finally:
        sim.POLICY = {}
    last = res['waves'][-1] if res['waves'] else {}
    row = {
        'runKey': '%d|%.2f|%s|%d' % (level, fraction, mode, seed),
        'levelId': level, 'mazeFraction': fraction, 'mode': mode, 'seed': seed,
        'mazeSize': maze_size, 'targetTowers': target, 'builtCount': last.get('towerCount', 0),
        'pathLength': last.get('pathLength', 0), 'capacity': policy['capacity'],
        'victory': res['metrics']['victory'], 'completedWave': res['metrics']['completedWaveCount'],
        'leaked': res['leaked'], 'hp': res['metrics']['hp'], 'maxHp': res['metrics']['maxHp'],
        'killed': res['metrics']['killed'], 'expectedEnemyCount': res['metrics']['expectedEnemyCount'],
        'combatMs': res['metrics']['combatElapsedMs'], 'parMs': res['ratingProfile']['parCombatTimeMs'],
        'combatToParRatio': res['combatToParRatio'], 'balance': res['balance'],
        'spentBuild': sum(op['cost'] for op in res['operations'] if op['action'] == 'build'),
        'spentUpgrade': sum(op['cost'] for op in res['operations'] if op['action'] == 'upgrade'),
        'upgradeBudget': budget,
        'fullMazeCost': round(len(policy['blueprintCells']) * unit_price(plan), 1),
        'spawnDeferred': sum(w.get('spawnDeferredCount', 0) for w in res['waves']),
        'alivePeak': res['alivePeak'], 'overkill': res['overkillDamage'],
        'leakWaves': [w['waveOrdinal'] for w in res['waves'] if w.get('leaked')],
        'leakRoles': {k: sum(w['leakedByRole'].get(k, 0) for w in res['waves'])
                      for k in {r for w in res['waves'] for r in w['leakedByRole']}},
        'combatBasisHash': hash_now,
        'fiveStar': five_star(res), 'elapsedSec': round(time.time() - started, 2),
    }
    sidecar.write_text(json.dumps(row, ensure_ascii=False), encoding='utf-8')
    return row


# ---------------------------------------------------------------- gates
def five_star(res):
    m = res['metrics']
    return (m['victory'] and res['leaked'] == 0 and m['hp'] >= m['maxHp']
            and m['killed'] == m['expectedEnemyCount']
            and m['combatElapsedMs'] <= res['ratingProfile']['parCombatTimeMs'])


def _pick(rows, fraction, mode=MODE_FILL):
    hits = [r for r in rows if abs(r['mazeFraction'] - fraction) < 1e-6 and r['mode'] == mode]
    return hits[0] if hits else None


def structural_clear(row):
    """Five-star predicate without the Par condition, used before Par calibration."""
    return (row['victory'] and row['leaked'] == 0 and row['hp'] >= row['maxHp']
            and row['killed'] == row['expectedEnemyCount'])


def evaluate_level(level, rows):
    gates, notes, detail = {}, {}, {}
    half = _pick(rows, 0.5)
    if half is not None:
        gates['G1'] = bool(half['leaked'] >= 6 or half['hp'] <= 10)
        notes['G1'] = '50%% maze (%d towers): leaked=%d hp=%d' % (half['builtCount'], half['leaked'], half['hp'])
    seven = _pick(rows, 0.7)
    if seven is not None:
        gates['G2'] = bool(seven['leaked'] >= 4 or seven['hp'] <= 16)
        notes['G2'] = '70%% maze (%d towers): leaked=%d hp=%d' % (seven['builtCount'], seven['leaked'], seven['hp'])
    most = _pick(rows, 0.85)
    if most is not None:
        gates['G3'] = not structural_clear(most)
        notes['G3'] = '85%% maze (%d towers): structural_clear=%s leaked=%d' % (
            most['builtCount'], structural_clear(most), most['leaked'])
    full = [r for r in rows if abs(r['mazeFraction'] - 1.0) < 1e-6 and r['mode'] == MODE_FILL]
    if full:
        row = full[0]
        clear_ok = structural_clear(row)
        policy_ok = row['builtCount'] >= row['targetTowers'] - 1
        budget_ok = row['spentUpgrade'] >= 0.25 * row['fullMazeCost']
        time_ok = 0.90 <= row['combatToParRatio'] <= 1.05
        gates['G4'] = bool(clear_ok and policy_ok and budget_ok and time_ok)
        detail['G4'] = {'clear': clear_ok, 'policy': policy_ok, 'budget': budget_ok, 'time': time_ok,
                        'leaked': row['leaked'], 'hp': row['hp'], 'ratio': round(row['combatToParRatio'], 4),
                        'built': row['builtCount'], 'target': row['targetTowers'],
                        'upgrade': row['spentUpgrade'], 'upgradeFloor': round(0.25 * row['fullMazeCost']),
                        'leakWaves': row.get('leakWaves', []), 'leakRoles': row.get('leakRoles', {})}
        notes['G4'] = ('full maze (%d/%d): clear=%s policy=%s budget=%s time=%s ratio=%.3f leaked=%d'
                       % (row['builtCount'], row['targetTowers'], clear_ok, policy_ok, budget_ok,
                          time_ok, row['combatToParRatio'], row['leaked']))
    noup = _pick(rows, 1.0, MODE_NOUP)
    if noup is not None:
        gates['G5'] = not structural_clear(noup)
        notes['G5'] = 'full maze, no upgrades: structural_clear=%s leaked=%d' % (
            structural_clear(noup), noup['leaked'])
    return gates, notes, detail


def next_action(gates, detail):
    g4 = detail.get('G4')
    if not g4:
        return 'measure'
    if g4['clear'] and not g4['time']:
        return 'par'
    if g4['clear']:
        return 'ok'
    if g4['leaked'] <= 2 and g4['leakRoles'] and set(g4['leakRoles']) <= {'boss'}:
        return 'boss_weight'
    if g4['leaked'] <= 2:
        return 'lower_x_small'
    if g4['leaked'] <= 6:
        return 'lower_x'
    return 'lower_x_large'


def summarize(rows):
    by_level = {}
    for row in rows:
        by_level.setdefault(row['levelId'], []).append(row)
    summary = {}
    for level, items in sorted(by_level.items()):
        gates, notes, detail = evaluate_level(level, items)
        if level < 6:
            for key in ('G1', 'G2'):
                gates.pop(key, None)
        if level < 15:
            gates.pop('G5', None)
        summary[level] = {'gates': gates, 'notes': notes, 'detail': detail,
                          'action': next_action(gates, detail),
                          'passed': (all(gates.values()) if gates else None),
                          'failures': [k for k, v in gates.items() if not v]}
    ordered = sorted(summary)
    return {'levels': summary,
            'passed': all(summary[l]['passed'] for l in ordered if summary[l]['passed'] is not None),
            'failingLevels': [l for l in ordered if summary[l]['passed'] is False],
            'actions': {l: summary[l]['action'] for l in ordered if summary[l]['passed'] is False}}


# ---------------------------------------------------------------- commands
LADDERS = {
    'quick': [0.5, 0.85, 1.0],
    'gate': [0.5, 0.7, 0.85, 1.0],
    'curve': [round(0.1 * i, 1) for i in range(1, 11)],
    'full': [round(0.1 * i, 1) for i in range(1, 11)] + [0.5, 0.7, 0.85],
}


def parse_ladder(text):
    if text in LADDERS:
        return sorted(set(LADDERS[text] + [1.0]))
    return [float(x) for x in text.split(',') if x.strip()]


def _run_batch(args, out, tasks, resume):
    rows = []
    if not tasks:
        return rows
    if args.workers <= 1:
        _init_worker(args.recipe, args.step_ms, out, resume)
        for task in tasks:
            rows.append(_run_one(task))
            print(json.dumps({'event': 'run', 'level': task[0], 'fraction': task[1], 'mode': task[2],
                              'towers': rows[-1]['builtCount'], 'leaked': rows[-1]['leaked']}), flush=True)
        return rows
    with cf.ProcessPoolExecutor(max_workers=args.workers, initializer=_init_worker,
                                initargs=(args.recipe, args.step_ms, out, resume)) as pool:
        for row in pool.map(_run_one, tasks):
            rows.append(row)
            print(json.dumps({'event': 'run', 'level': row['levelId'], 'fraction': row['mazeFraction'],
                              'mode': row['mode'], 'towers': row['builtCount'],
                              'leaked': row['leaked'], 'ratio': round(row['combatToParRatio'], 3)}), flush=True)
    return rows


def cmd_run(args):
    recipe = bp.read_json(args.recipe)
    level_count = bp.dimensions(recipe)[0]
    levels = list(range(1, level_count + 1)) if args.levels == 'all' else [int(x) for x in args.levels.split(',') if x.strip()]
    fractions = parse_ladder(args.ladder)
    seeds = [int(s) for s in args.seeds.split(',')]
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.only_failing:
        previous = json.loads((pathlib.Path(args.only_failing) / 'gate-summary.json').read_text(encoding='utf-8'))
        levels = sorted(int(k) for k, v in previous['levels'].items() if v['passed'] is False)
        print(json.dumps({'event': 'subset', 'levels': levels}), flush=True)

    # Phase 1: the full-maze row decides how much upgrade money is legitimate;
    # lower tiers inherit that ceiling so a small garrison cannot convert the
    # saved build budget into an unlimited upgrade budget.
    phase1 = [(L, 1.0, MODE_FILL, s, None) for L in levels for s in seeds]
    print(json.dumps({'event': 'phase1', 'runs': len(phase1)}), flush=True)
    rows = _run_batch(args, out, phase1, args.resume)
    spent_full = {}
    for row in rows:
        if abs(row['mazeFraction'] - 1.0) < 1e-9 and row['mode'] == MODE_FILL:
            spent_full[row['levelId']] = row['spentUpgrade']

    phase2 = []
    for L in levels:
        for fraction in fractions:
            if abs(fraction - 1.0) < 1e-9:
                if args.control:
                    phase2 += [(L, fraction, MODE_NOUP, s, 0) for s in seeds]
                continue
            budget = None
            if args.upgrade_budget == 'uniform':
                budget = spent_full.get(L)
            elif args.upgrade_budget.startswith('fixed:'):
                budget = int(args.upgrade_budget.split(':', 1)[1])
            phase2 += [(L, fraction, MODE_FILL, s, budget) for s in seeds]
    print(json.dumps({'event': 'phase2', 'runs': len(phase2),
                      'budget': args.upgrade_budget}), flush=True)
    rows += _run_batch(args, out, phase2, args.resume)

    write_outputs(out, rows, args)
    summary = json.loads((out / 'gate-summary.json').read_text(encoding='utf-8'))
    print(json.dumps({'event': 'done', 'passed': summary['passed'],
                      'failing': summary['failingLevels'], 'actions': summary['actions']}), flush=True)
    return 0 if summary['passed'] else 2


def write_outputs(out, rows, args):
    (out / 'gate-matrix.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = summarize(rows)
    summary.update({'schemaVersion': 1, 'recipe': str(args.recipe), 'stepMs': args.step_ms,
                    'generatedUtc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    (out / 'gate-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'gate-report.md').write_text(render_markdown(rows, summary), encoding='utf-8')
    csv_lines = ['level,fraction,mode,built,target,path,leaked,hp,maxHp,ratio,upgrade,fiveStar']
    for r in sorted(rows, key=lambda x: (x['levelId'], x['mazeFraction'], x['mode'])):
        csv_lines.append('%d,%.2f,%s,%d,%d,%d,%d,%d,%d,%.4f,%d,%s' % (
            r['levelId'], r['mazeFraction'], r['mode'], r['builtCount'], r['targetTowers'],
            r['pathLength'], r['leaked'], r['hp'], r['maxHp'], r['combatToParRatio'],
            r['spentUpgrade'], r['fiveStar']))
    (out / 'gate-matrix.csv').write_text('\n'.join(csv_lines) + '\n', encoding='utf-8')


def render_markdown(rows, summary):
    lines = ['# 占用阶梯闸门报告', '',
             '> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。',
             '> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。', '',
             '| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |',
             '|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|']
    for row in sorted(rows, key=lambda r: (r['levelId'], r['mazeFraction'], r['mode'])):
        lines.append('| %d | %.0f%% | %s | %d | %d | %d | %d | %d/%d | %.3f | %d | %s |' % (
            row['levelId'], row['mazeFraction'] * 100, row['mode'], row['targetTowers'], row['builtCount'],
            row['pathLength'], row['leaked'], row['hp'], row['maxHp'], row['combatToParRatio'],
            row['spentUpgrade'], '★' if row['fiveStar'] else '—'))
    lines += ['', '## 闸门汇总', '',
              '| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |',
              '|---|:--:|:--:|:--:|:--:|:--:|---|']
    for level, item in summary['levels'].items():
        state = 'PASS' if item['passed'] else ('FAIL' if item['passed'] is False else 'N/A')
        cell = lambda k: ('—' if k not in item['gates'] else ('✓' if item['gates'][k] else '✗'))
        lines.append('| %s | %s | %s | %s | %s | %s | %s %s |' % (
            level, cell('G1'), cell('G2'), cell('G3'), cell('G4'), cell('G5'), state, ','.join(item['failures'])))
    lines += ['', '## 明细', '']
    for level, item in summary['levels'].items():
        for key, note in item['notes'].items():
            lines.append('- L%s %s: %s' % (level, key, note))
    return '\n'.join(lines) + '\n'


def cmd_rescore(args):
    out = pathlib.Path(args.run)
    rows = json.loads((out / 'gate-matrix.json').read_text(encoding='utf-8'))
    recipe = bp.read_json(args.recipe)
    plan = bp.generate(recipe, recipe.get('selectedProfileId', 'D04'))
    par = {l['levelId']: l['parCombatTimeMs'] for l in plan['levels']}
    hashes = {l['levelId']: l['combatBasisHash'] for l in plan['levels']}
    skipped = set()
    for row in rows:
        level = row['levelId']
        if row.get('combatBasisHash') and row['combatBasisHash'] != hashes.get(level):
            skipped.add(level)
            continue
        row['parMs'] = par[level]
        row['combatToParRatio'] = row['combatMs'] / par[level]
        row['fiveStar'] = bool(row['victory'] and row['leaked'] == 0 and row['hp'] >= row['maxHp']
                               and row['killed'] == row['expectedEnemyCount']
                               and row['combatMs'] <= par[level])
    args.step_ms = args.step_ms
    write_outputs(out, rows, args)
    print(json.dumps({'event': 'rescore', 'skippedStaleLevels': sorted(skipped)}))
    return 0


def cmd_report(args):
    out = pathlib.Path(args.run)
    rows = json.loads((out / 'gate-matrix.json').read_text(encoding='utf-8'))
    summary = summarize(rows)
    text = render_markdown(rows, summary)
    (out / 'gate-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'gate-report.md').write_text(text, encoding='utf-8')
    if args.markdown:
        pathlib.Path(args.markdown).write_text(text, encoding='utf-8')
    print(json.dumps({'event': 'report', 'passed': summary['passed'], 'failing': summary['failingLevels']}))
    return 0 if summary['passed'] else 2


def cmd_preflight(args):
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    recipe = bp.read_json(args.recipe)
    plan = bp.generate(recipe, recipe.get('selectedProfileId', 'D04'))
    plain = bp.validate(plan)
    if args.skip_export:
        exported = {'passed': None, 'errors': []}
    else:
        exported = bp.validate(plan, str(bp.ROOT / 'Assets/ConfigJson'))
    report = {'recipe': args.recipe, 'balanceRevision': plan['recipe']['balanceRevision'],
              'validate': plain['passed'], 'validateExport': exported['passed'],
              'errors': plain['errors'][:20], 'exportErrors': exported['errors'][:20], 'levels': []}
    for level in range(1, plan['levelCount'] + 1):
        cells, walls = maze_for(plan, level)
        audit = capacity(cells)
        report['levels'].append({'levelId': level, 'B': audit['buildableCells'], 'q': audit['reservedBuildableCells'],
                                 'C': audit['capacity'], 'mazeWalls': len(walls),
                                 'mazePath': len(runtime_path_for(cells, walls)) - 1,
                                 'mazeCost': round(len(walls) * unit_price(plan))})
    (out / 'preflight.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'event': 'preflight', 'validate': plain['passed'], 'export': exported['passed']}))
    ok = plain['passed'] and exported['passed'] is not False
    return 0 if ok else 3


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)

    def common(p):
        p.add_argument('--recipe', default=DEFAULT_RECIPE)
        p.add_argument('--out', default=None)

    p = sub.add_parser('run')
    common(p)
    p.add_argument('--levels', default='1,6,10,15,24,30')
    p.add_argument('--ladder', default='gate')
    p.add_argument('--seeds', default='42')
    p.add_argument('--step-ms', type=int, default=100)
    p.add_argument('--workers', type=int, default=7)
    p.add_argument('--upgrade-budget', default='uniform')
    p.add_argument('--only-failing', default=None)
    p.add_argument('--control', dest='control', action='store_true', default=True,
                   help='also run the no-upgrade control at 1.0')
    p.add_argument('--no-control', dest='control', action='store_false')
    p.add_argument('--resume', dest='resume', action='store_true', default=True)
    p.add_argument('--fresh', dest='resume', action='store_false')

    p = sub.add_parser('report')
    p.add_argument('--run', required=True)
    p.add_argument('--markdown', default=None)

    p = sub.add_parser('rescore')
    p.add_argument('--run', required=True)
    p.add_argument('--recipe', default=DEFAULT_RECIPE)
    p.add_argument('--step-ms', type=int, default=100)

    p = sub.add_parser('preflight')
    common(p)
    p.add_argument('--skip-export', action='store_true', default=False)

    args = parser.parse_args(argv)
    if args.command == 'run':
        args.out = args.out or str(bp.ROOT / 'Luban/BalanceDesign/FillGate' / ('run-' + time.strftime('%Y%m%d-%H%M%S')))
        return cmd_run(args)
    if args.command == 'report':
        return cmd_report(args)
    if args.command == 'rescore':
        return cmd_rescore(args)
    args.out = args.out or str(bp.ROOT / 'Luban/BalanceDesign/FillGate/preflight')
    return cmd_preflight(args)


if __name__ == '__main__':
    raise SystemExit(main())
