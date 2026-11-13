import fs from 'node:fs';
// REJECTED: This diagnostic used a historical CSV layout and unaudited exports.
// It must not be used to design or apply L02 configuration.
throw new Error('Rejected diagnostic: rebuild from current L01 source XLSX and user-confirmed screenshots.');
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  loadTables,
  prepareLevel,
  makeRunState,
  normalizeTowerRows,
  isLegalPlacement,
  runtimePath,
  stepOnce,
  DEFAULTS,
} from '../../.workbuddy/tools/balance_sim.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const SOURCE = path.join(ROOT, 'Assets', 'ConfigJson');
const OUT = path.join(ROOT, 'Library', 'BalanceStage', `l02-terminal-recalc-${Date.now()}`);
const L01_COST = 3919;
const L02_COST = 6887;
const L02_TOTAL_ECONOMY = 7106;
const TERMINAL_CELLS = 3;
const DT = 0.05;

const towerCosts = { 1: { 1: 32, 2: 28, 3: 40 }, 2: { 1: 44, 2: 40, 3: 55 }, 3: { 1: 30, 2: 40, 3: 60 } };

function read(name) { return JSON.parse(fs.readFileSync(path.join(SOURCE, name), 'utf8')); }
function write(dir, name, value) { fs.writeFileSync(path.join(dir, name), JSON.stringify(value, null, 2) + '\n'); }
function clone(v) { return JSON.parse(JSON.stringify(v)); }
function l02GroupId(i) { return i < 20 ? 2001 + i : 2401 + (i - 20); }
function l01GroupId(i) { return i < 20 ? i + 1 : 401 + (i - 20); }
function l02EnemyId(id) { return Number(id) + 1000000; }

// The supplied final L02 image: P=retard, N=normal, F=blast.
const L02_LAYOUT = [
  [3, 0, 3, 1], [7, 0, 3, 1], [11, 0, 3, 1], [15, 0, 3, 3],
  [1, 1, 3, 1], [3, 1, 3, 3], [5, 1, 3, 3], [7, 1, 3, 3], [9, 1, 3, 3], [11, 1, 3, 3], [13, 1, 3, 3], [15, 1, 3, 3],
  [1, 2, 3, 3], [3, 2, 3, 3], [5, 2, 3, 3], [7, 2, 3, 3], [9, 2, 3, 3], [11, 2, 3, 3], [13, 2, 3, 3], [15, 2, 3, 3],
  [1, 3, 1, 3], [3, 3, 1, 3], [5, 3, 1, 3], [7, 3, 1, 3], [9, 3, 1, 3], [11, 3, 1, 3], [13, 3, 1, 3], [15, 3, 3, 3],
  [1, 4, 1, 3], [3, 4, 2, 3], [5, 4, 1, 3], [7, 4, 2, 3], [9, 4, 1, 3], [11, 4, 2, 3], [13, 4, 1, 3],
  [1, 5, 1, 3], [3, 5, 1, 3], [5, 5, 1, 3], [7, 5, 1, 3], [9, 5, 1, 3], [11, 5, 1, 3], [13, 5, 1, 3], [14, 5, 1, 3], [15, 5, 1, 3],
  [1, 6, 3, 3], [3, 6, 3, 3], [5, 6, 3, 3], [7, 6, 3, 3], [9, 6, 3, 3], [11, 6, 3, 3], [13, 6, 3, 3], [14, 6, 1, 3], [15, 6, 1, 3],
  [1, 7, 3, 3], [3, 7, 3, 3], [5, 7, 3, 3], [7, 7, 3, 3], [9, 7, 3, 3], [11, 7, 3, 3], [13, 7, 3, 3],
  [1, 8, 3, 1], [5, 8, 3, 1], [9, 8, 3, 1], [13, 8, 3, 1],
];

function staticOperations(layout, cost) {
  const ops = [];
  for (const [x, y, family, level] of layout) {
    ops.push({ type: 'build', x, y, family: family - 1, level: 1, timeSec: 0 });
    for (let l = 2; l <= level; l += 1) ops.push({ type: 'upgrade', x, y, family: family - 1, level: l, timeSec: 0 });
  }
  const actual = layout.reduce((sum, [, , family, level]) => {
    let s = 0; for (let l = 1; l <= level; l += 1) s += towerCosts[family][l]; return sum + s;
  }, 0);
  if (actual !== cost) throw new Error(`layout cost mismatch: expected ${cost}, got ${actual}`);
  return ops;
}

function buildCandidate(multiplier, intervalScale = 1, speedScale = 1, armorBonus = 0) {
  fs.mkdirSync(OUT, { recursive: true });
  for (const name of fs.readdirSync(SOURCE)) if (name.endsWith('.json')) fs.copyFileSync(path.join(SOURCE, name), path.join(OUT, name));

  const enemy = read('tbenemydata.json');
  const l01Enemy = enemy.filter((r) => r.levelId === 1);
  const nonLevels = enemy.filter((r) => r.levelId !== 1 && r.levelId !== 2);
  const l02Enemy = l01Enemy.map((r) => ({ ...clone(r), id: l02EnemyId(r.id), levelId: 2,
    hp: r.hp * (r.isFlying ? multiplier.air : multiplier.ground),
    speed: r.speed * speedScale,
    armor: Math.min(0.95, r.armor + armorBonus),
    reward: r.reward,
  }));
  write(OUT, 'tbenemydata.json', [...nonLevels, ...l01Enemy, ...l02Enemy]);

  const lists = read('tbenemylist.json');
  const l01Lists = lists.filter((r) => (r.id >= 1 && r.id <= 20) || (r.id >= 401 && r.id <= 405));
  const l02ListIds = new Set(Array.from({ length: 20 }, (_, i) => 2001 + i).concat([2401, 2402, 2403, 2404, 2405]));
  const newLists = l01Lists.map((r, i) => ({ ...clone(r), id: l02GroupId(i),
    EnemyIndexs: r.EnemyIndexs.map(l02EnemyId), enemyInterval: r.enemyInterval * intervalScale }));
  write(OUT, 'tbenemylist.json', [...lists.filter((r) => !l02ListIds.has(r.id) && !l01Lists.some((l) => l.id === r.id)), ...l01Lists, ...newLists]);

  const rounds = read('tbrounddata.json');
  const l01Rounds = rounds.filter((r) => (r.id >= 1 && r.id <= 20) || (r.id >= 401 && r.id <= 405));
  const newRounds = l01Rounds.map((r, i) => ({ ...clone(r), id: l02GroupId(i), EnemyIndexs: [l02GroupId(i)], rewardGold: r.rewardGold }));
  const roundIds = new Set(newRounds.map((r) => r.id));
  write(OUT, 'tbrounddata.json', [...rounds.filter((r) => !roundIds.has(r.id)), ...newRounds]);

  const scenes = read('tbsceneinfo.json').map((r) => ({ ...r }));
  const s1 = scenes.find((r) => r.id === 1); const s2 = scenes.find((r) => r.id === 2);
  s1.initialGold = 100; s2.initialGold = 100;
  s1.initialHp = 1000000; s2.initialHp = 1000000;
  s1.RoundList = [405]; s2.RoundList = [2405];
  write(OUT, 'tbsceneinfo.json', scenes);
  return { tables: loadTables(OUT), l01Layout: readL01Layout(), l02Layout: L02_LAYOUT };
}

function readL01Layout() {
  const rows = fs.readFileSync(path.join(ROOT, 'Artifacts', 'L01_ZeroLeak_20261103_1823', 'final-towers.csv'), 'utf8').trim().split(/\r?\n/).slice(1).map((line) => line.replaceAll('"', '').split(','));
  return rows.map((r) => [Number(r[1]), Number(r[0]), Number(r[2]), Number(r[3])]);
}

function installStaticTowers(st, layout, levelId) {
  const rows = normalizeTowerRows(st.tables);
  const selected = layout.map(([x, y, family, level]) => {
    const row = [...rows.values()].find((r) => r.levelId === undefined && r.family === family - 1 && r.level === level);
    if (!row) throw new Error(`tower row missing family=${family} level=${level}`);
    return { x, y, family: family - 1, row };
  });
  for (const tower of selected) {
    const idx = tower.y * st.grid.cols + tower.x;
    if (!isLegalPlacement(st.grid, st.occ, idx)) throw new Error(`illegal static placement at ${tower.x},${tower.y}`);
    st.occ[idx] = 1;
    st.towers.push({ slot: null, row: tower.row, x: tower.x, y: tower.y, fireTimer: 0, searchTimer: 0, target: null });
    st.builtOrder.push({ idx, x: tower.x, y: tower.y, family: tower.family, state: 'built', tower: st.towers[st.towers.length - 1] });
  }
  if (runtimePath(st.grid, st.occ).length === 0) throw new Error(`static layout disconnects L${levelId}`);
  st.wallVersion += 1;
  st.routeCache.clear();
}

function terminalMetrics(st, levelId) {
  const final = st.nRounds;
  let maxAlive = 0; let maxEhp = 0; let minKillMargin = Infinity; let leaks = 0;
  const kills = [];
  const isTerminal = (e) => {
    if (e.flying) {
      const dx = st.grid.xOf[st.grid.end] - e.x; const dy = st.grid.yOf[st.grid.end] - e.y;
      return Math.hypot(dx, dy) <= TERMINAL_CELLS;
    }
    return e.route && e.route.length - 1 - e.s <= TERMINAL_CELLS;
  };
  const run = () => {
    const maxSteps = Math.round(3600 / DT);
    while (st.k < maxSteps && !st.lost && !st.done) {
      stepOnce(st);
      if (st.roundIdx + (st.roundActive ? 1 : 0) === final || (st.roundIdx === final - 1 && st.roundActive)) {
        const near = st.enemies.filter((e) => e.alive && isTerminal(e));
        maxAlive = Math.max(maxAlive, near.length);
        maxEhp = Math.max(maxEhp, near.reduce((sum, e) => sum + Math.max(0, e.hp), 0));
      }
    }
  };
  run();
  for (const k of st.kills.filter((x) => x.round === final)) {
    if (k.remaining !== null && k.remaining <= TERMINAL_CELLS) minKillMargin = Math.min(minKillMargin, k.remaining);
  }
  leaks = st.leaksTotal;
  return { levelId, verdict: st.lost ? 'lost' : st.done ? 'pass' : 'timeout', leaks, roundsCleared: st.roundsCleared,
    maxAliveTerminal3: maxAlive, maxEhpTerminal3: Number(maxEhp.toFixed(4)), minKillMargin: minKillMargin === Infinity ? null : Number(minKillMargin.toFixed(4)),
    spawned: st.spawnedTotal, killed: st.killedTotal, towers: st.towers.length, firstKill: st.kills[0] || null,
    goldFinal: Number(st.gold.toFixed(4)), simSec: Number((st.k * DT).toFixed(4)) };
}

function simulate(levelId, tables, layout) {
  const opts = { ...DEFAULTS, dt: DT, spacing: 2, operationScript: [], airPreempt: true, towerPowerScale: 1, forbidUpgrades: false, configDir: OUT };
  const prep = prepareLevel(levelId, tables, opts);
  const st = makeRunState(prep, tables, opts);
  installStaticTowers(st, layout, levelId);
  st.roundIdx = st.nRounds - 1;
  st.nextStartStep = 1;
  st.gold = 100;
  return terminalMetrics(st, levelId);
}

const multipliers = [1];
const results = [];
for (const g of multipliers) {
  for (const a of multipliers) {
    const candidate = buildCandidate({ ground: g, air: a });
    const l01 = simulate(1, candidate.tables, candidate.l01Layout);
    const l02 = simulate(2, candidate.tables, candidate.l02Layout);
    results.push({ groundMultiplier: g, airMultiplier: a, l01, l02 });
  }
}
fs.writeFileSync(path.join(OUT, 'search-results.json'), JSON.stringify({ baseline: results[0].l01, results }, null, 2) + '\n');
console.log(JSON.stringify({ baseline: results[0].l01, samples: results.filter((r) => [1.5, 2, 3, 4, 6, 10].includes(r.groundMultiplier) && r.groundMultiplier === r.airMultiplier) }, null, 2));
