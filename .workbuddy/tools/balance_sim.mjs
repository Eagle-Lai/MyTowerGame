#!/usr/bin/env node
// balance_sim.mjs
// Deterministic continuous-time tower-defence balance simulator (policy P1 "build-first").
// Node.js ESM, no npm dependencies. Reads Assets/ConfigJson/*.json only (read-only).
// Writes only under Library/BalanceStage/sim/ (per-level JSON, summary.json, summary.md).
//
// Usage:
//   node .workbuddy/tools/balance_sim.mjs [--levels 1-30] [--dt 0.05] [--spacing 2]
//     [--slotDrop 0] [--ehpScale 1] [--sentries] [--noAirPreempt] [--strictBuildFirst]
//     [--operationScriptDir <base-sim-dir>] [--maxSimSec 3600] [--out <sim-dir>]
//     [--summary D:/FishTestGame/Library/BalanceStage/sim/current_baseline.md]
//
// Rule sources (C# runtime under Assets/Scripts; "C#:" comments mark each port):
//   BaseTower.cs         TickAttack, ConsumeCadence, TickSlowAura, PickBestTarget, Fire, DetonateAt
//   BaseEnemy.cs         Hurt, Die, ApplySlow, TickEffects, MoveAlongPath, MoveStraight, OnReachEnd
//   WaveManager.cs       BeginRound (timeline), Tick (spawn, capacity deferral), IsRoundFinished
//   GameFlowManager.cs   FinishRound (clear reward), TickAutoNextRound (delay)
//   TowerManager.cs      TryBuildInternal (legality), TryUpgrade (new instance => fresh timers)
//   CombatSystem.cs      OnUpdate order: enemies, towers (reverse list order), then flow
//   balance_capacity.mjs runtimePath (A*), snakeWalls, augmentLayout (copied, file not modified)
//
// Known C#-vs-spec choices (see report): C# re-targets a ground-locked tower to an air unit in
// range at each search tick (kept by default, --noAirPreempt disables it). Upgrades reset the
// tower's timers and target. Kill order and tie-break use lower unit id.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(SCRIPT_DIR, '..', '..');
const CONFIG_DIR = path.join(PROJECT_ROOT, 'Assets', 'ConfigJson');
const SIM_ROOT = path.join(PROJECT_ROOT, 'Library', 'BalanceStage', 'sim');
const DEFAULT_OUT = path.join(SIM_ROOT, 'run');

export const DEFAULTS = Object.freeze({
  dt: 0.05,
  spacing: 2,
  slotDrop: 0,
  ehpScale: 1,
  sentries: false,
  airPreempt: true,         // C#: BaseTower.TickAttack re-checks a ground lock for air units each search tick
  strictBuildFirst: false,  // false: literal gate (upgrades once no slot is buildable-and-affordable)
    towerPowerScale: 1,
    forbidUpgrades: false,
  maxSimSec: 3600,
});

const SEARCH_INTERVAL_DEFAULT_SEC = 0.1; // BaseTower searchIntervalMs default
const SLOW_LINGER_SEC = 0.1;             // C#: BaseTower.SlowAuraLingerSec
const SLOW_MAX = 0.95;                   // C#: BaseEnemy.ApplySlow clamp
const DEFAULT_GAP_MS = 200;              // spec: enemyInterval 0 -> 200 (C#: WaveConfig.SpawnIntervalSec)
const MIN_LEAK_DAMAGE = 1;               // spec: lose damageToPlayer HP, min 1
const FAMILY_NAMES = ['normal', 'blast', 'frost']; // tower type 1, 2, 3; round-robin order
const ASTAR_DIRS = [[0, 1], [0, -1], [-1, 0], [1, 0]];   // balance_capacity ASTAR_DIRS
const BFS_DIRS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
const KEY_SHIFT = 1048576;               // balance_capacity: packs (f, first-open ordinal)
const EPS = 1e-9;

// ---------------------------------------------------------------- tables
export function loadTables(configDir = CONFIG_DIR) {
  configDir = path.resolve(configDir);
  const read = (name) => {
    const data = JSON.parse(fs.readFileSync(path.join(configDir, name), 'utf8').replace(/^\uFEFF/, ''));
    if (!Array.isArray(data)) throw new Error(`${name} must be a JSON array`);
    return data;
  };
  const byId = (rows) => new Map(rows.map((r) => [r.id, r]));
  const glob = read('tbglobal.json')[0];
  return {
    global: {
      autoNextRoundDelayMs: glob.autoNextRoundDelayMs ?? 2500,
      maxEnemyAlive: glob.maxEnemyAlive ?? 200,
    },
    scenes: new Map(read('tbsceneinfo.json').map((s) => [s.id, s])),
    rounds: byId(read('tbrounddata.json')),
    groups: byId(read('tbenemylist.json')),
    enemies: byId(read('tbenemydata.json')),
    towers: byId(read('tbtowerinfo.json')),
    bullets: byId(read('tbbulletdata.json')),
    maps: new Map(read('tblevelmap.json').map((m) => [m.levelId, m])),
  };
}

// Normalised tower rows: seconds instead of ms, family index, splash radius from the bullet table.
export function normalizeTowerRows(tables) {
  const rows = new Map();
  for (const r of tables.towers.values()) {
    const bullet = tables.bullets.get(r.bulletId);
    const effectType = r.effectType;
    rows.set(r.id, {
      id: r.id,
      family: r.type - 1,
      level: r.level,
      radius: r.radius,
      power: r.power,
      cdSec: r.CD / 1000,
      searchSec: (r.searchIntervalMs > 0 ? r.searchIntervalMs : SEARCH_INTERVAL_DEFAULT_SEC * 1000) / 1000,
      prices: r.prices,            // L1 = build cost; L2/L3 = incremental upgrade cost
      upgradeTo: r.upgradeTo,
      canAttackAir: r.canAttackAir === 1,
      effectType,                  // 0 single target, 3 splash, 1 slow aura
      effectValue: r.effectValue,  // slow ratio for frost
      aoeRadius: effectType === 3 && bullet ? bullet.aoeRadius : 0,
    });
  }
  return rows;
}

function l1Rows(towerRows) {
  return FAMILY_NAMES.map((_, family) => {
    for (const row of towerRows.values()) if (row.family === family && row.level === 1) return row;
    throw new Error(`no level-1 tower row for family ${family}`);
  });
}

// ---------------------------------------------------------------- grid
// '.' buildable, 'S' start, 'E' end (both walkable, not buildable), '#' terrain.
// Any other character is treated as blocked and reported in `unexpected`.
export function buildGrid(entry) {
  const cells = entry.cells;
  const rows = cells.length;
  const cols = cells[0].length;
  if (rows !== entry.rows || cols !== entry.cols) {
    throw new Error(`level ${entry.levelId}: declared ${entry.cols}x${entry.rows}, data ${cols}x${rows}`);
  }
  const N = rows * cols;
  const ch = new Array(N);
  const terrain = new Uint8Array(N);   // blocks enemies and towers
  const buildable = new Uint8Array(N);
  const unexpected = {};
  const starts = [];
  const ends = [];
  for (let y = 0; y < rows; y++) {
    if (cells[y].length !== cols) throw new Error(`level ${entry.levelId}: ragged row ${y}`);
    for (let x = 0; x < cols; x++) {
      const c = cells[y][x];
      const i = y * cols + x;
      ch[i] = c;
      if (c === '.') buildable[i] = 1;
      else if (c === 'S') starts.push(i);
      else if (c === 'E') ends.push(i);
      else {
        terrain[i] = 1;
        if (c !== '#') unexpected[c] = (unexpected[c] || 0) + 1;
      }
    }
  }
  if (starts.length === 0 || ends.length === 0) throw new Error(`level ${entry.levelId}: missing S or E`);
  const xOf = new Int32Array(N);
  const yOf = new Int32Array(N);
  for (let i = 0; i < N; i++) { xOf[i] = i % cols; yOf[i] = (i - xOf[i]) / cols; }
  return {
    levelId: entry.levelId, cols, rows, N, ch, terrain, buildable, xOf, yOf,
    start: starts[0], end: ends[0],
    extraStarts: starts.length - 1, extraEnds: ends.length - 1,
    unexpected,
  };
}

// balance_capacity.mjs PairHeap (copied)
class PairHeap {
  constructor() { this.k = []; this.v = []; }
  get size() { return this.k.length; }
  push(key, val) {
    const k = this.k, v = this.v;
    let i = k.length;
    k.push(key); v.push(val);
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (k[p] <= key) break;
      k[i] = k[p]; v[i] = v[p];
      i = p;
    }
    k[i] = key; v[i] = val;
  }
  pop() {
    const k = this.k, v = this.v;
    const lastK = k.pop(), lastV = v.pop();
    const n = k.length;
    if (n === 0) return;
    let i = 0;
    for (;;) {
      let c = 2 * i + 1;
      if (c >= n) break;
      if (c + 1 < n && k[c + 1] < k[c]) c++;
      if (k[c] >= lastK) break;
      k[i] = k[c]; v[i] = v[c];
      i = c;
    }
    k[i] = lastK; v[i] = lastV;
  }
}

// balance_capacity.mjs runtimePath (copied; `from` generalised from S so enemies can re-path).
// 4-direction A*, F = G + Manhattan, ties by first-open ordinal, stops once E enters the open list.
// Returns cell indices from..end, or [] when E is unreachable. `towers` is a Uint8Array overlay.
export function runtimePath(g, towers, from = g.start) {
  if (from === g.end) return [from];
  const { cols, rows, N, terrain, end } = g;
  const ex = end % cols;
  const ey = (end - ex) / cols;
  const state = new Uint8Array(N);
  const seq = new Int32Array(N);
  const gc = new Int32Array(N);
  const parent = new Int32Array(N).fill(-1);
  const heap = new PairHeap();
  let sequence = 0;

  state[from] = 1;
  seq[from] = 0;
  heap.push(0, from);
  while (heap.size > 0) {
    const key = heap.k[0];
    const cell = heap.v[0];
    heap.pop();
    const f = Math.floor(key / KEY_SHIFT);
    const cx = cell % cols;
    const cy = (cell - cx) / cols;
    const h = cell === from ? 0 : Math.abs(ex - cx) + Math.abs(ey - cy);
    if (state[cell] === 2 || f !== gc[cell] + h) continue;
    state[cell] = 2;
    for (const [dx, dy] of ASTAR_DIRS) {
      const ox = cx + dx;
      const oy = cy + dy;
      if (ox < 0 || oy < 0 || ox >= cols || oy >= rows) continue;
      const o = oy * cols + ox;
      if (terrain[o] || towers[o] || state[o] === 2) continue;
      const candidate = gc[cell] + 1;
      if (state[o] === 1 && candidate >= gc[o]) continue;
      if (state[o] !== 1) {
        sequence += 1;
        state[o] = 1;
        seq[o] = sequence;
      }
      gc[o] = candidate;
      parent[o] = cell;
      heap.push((candidate + Math.abs(ex - ox) + Math.abs(ey - oy)) * KEY_SHIFT + seq[o], o);
    }
    if (state[end] === 1) {
      const out = [];
      let c = end;
      while (c !== -1) { out.push(c); c = parent[c]; }
      return out.reverse();
    }
  }
  return [];
}

// BFS walk distance from `from` over walkable cells (used for slot ordering).
function bfsDistance(g, from) {
  const dist = new Int32Array(g.N).fill(-1);
  const queue = [from];
  dist[from] = 0;
  for (let qi = 0; qi < queue.length; qi++) {
    const c = queue[qi];
    const cx = c % g.cols;
    const cy = (c - cx) / g.cols;
    for (const [dx, dy] of BFS_DIRS) {
      const ox = cx + dx;
      const oy = cy + dy;
      if (ox < 0 || oy < 0 || ox >= g.cols || oy >= g.rows) continue;
      const o = oy * g.cols + ox;
      if (g.terrain[o] || dist[o] >= 0) continue;
      dist[o] = dist[c] + 1;
      queue.push(o);
    }
  }
  return dist;
}

// ---------------------------------------------------------------- S-shape fingers (balance_capacity.mjs, copied)
function pyRange(a, b) {
  const out = [];
  for (let i = a; i < b; i++) out.push(i);
  return out;
}

function straight(a, b, step = 0.5) {
  const dx = Math.abs(a[0] - b[0]);
  const dy = Math.abs(a[1] - b[1]);
  const n = Math.max(1, Math.trunc(Math.sqrt(dx * dx + dy * dy) / step));
  const out = [];
  for (let i = 0; i <= n; i++) out.push([a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]);
  return out;
}

function sq2(a, b) {
  const dx = a[0] - b[0];
  const dy = a[1] - b[1];
  return dx * dx + dy * dy;
}

function coverCount(cell, points, r2) {
  let n = 0;
  for (const p of points) if (sq2(cell, p) <= r2) n++;
  return n;
}

function keyGreater(a, b) {
  if (a[0] !== b[0]) return a[0] > b[0];
  return a[1] > b[1];
}

// Port of balance_fill_gate.augment_layout(cells, walls, radius=2.0); returns walls + sentries.
function augmentLayout(g, walls, radius = 2.0) {
  const { cols, rows, N } = g;
  const r2 = radius * radius;
  const towers = new Uint8Array(N);
  const blocked = new Uint8Array(N);
  for (const [x, y] of walls) { towers[y * cols + x] = 1; blocked[y * cols + x] = 1; }
  const pathIdx = runtimePath(g, towers);
  if (pathIdx.length === 0) return walls.map(([x, y]) => [x, y]);
  const toXY = (i) => [i % cols, (i - (i % cols)) / cols];
  const ground = pathIdx.map(toXY);
  const sPt = ground[0];
  const ePt = ground[ground.length - 1];
  const air = straight(sPt, ePt);
  const chosen = walls.map(([x, y]) => [x, y]);
  blocked[sPt[1] * cols + sPt[0]] = 1;
  blocked[ePt[1] * cols + ePt[0]] = 1;
  const free = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      if (g.ch[i] === '.' && !blocked[i]) free.push([c, r]);
    }
  }
  for (let iter = 0; iter < free.length; iter++) {
    const uncoveredG = ground.filter((p) => !chosen.some((t) => sq2(t, p) <= r2));
    const uncoveredA = air.filter((p) => !chosen.some((t) => sq2(t, p) <= r2));
    if (uncoveredG.length === 0 && uncoveredA.length === 0) break;
    let best = null;
    let bestKey = null;
    for (const cell of free) {
      const idx = cell[1] * cols + cell[0];
      if (blocked[idx]) continue;
      towers[idx] = 1;
      const legal = runtimePath(g, towers).length > 0;
      towers[idx] = 0;
      if (!legal) continue;
      const key = [
        coverCount(cell, uncoveredG, r2) + 2 * coverCount(cell, uncoveredA, r2),
        -Math.abs(cell[0] - cols / 2) - Math.abs(cell[1] - rows / 2),
      ];
      if (bestKey === null || keyGreater(key, bestKey)) { best = cell; bestKey = key; }
    }
    if (best === null || bestKey[0] <= 0) break;
    const bi = best[1] * cols + best[0];
    chosen.push(best);
    blocked[bi] = 1;
    towers[bi] = 1;
  }
  const posts = [];
  for (let k = 0; k < air.length; k += 2) {
    const point = air[k];
    if (posts.some((q) => sq2(q, point) <= 4.0)) continue;
    let best = null;
    let bestKey = null;
    for (const cell of free) {
      const idx = cell[1] * cols + cell[0];
      if (blocked[idx]) continue;
      const dist = sq2(cell, point);
      if (dist > r2) continue;
      towers[idx] = 1;
      const legal = runtimePath(g, towers).length > 0;
      towers[idx] = 0;
      if (!legal) continue;
      const key = [-dist, -air.filter((q) => sq2(cell, q) <= r2).length];
      if (bestKey === null || keyGreater(key, bestKey)) { best = cell; bestKey = key; }
    }
    if (best !== null) {
      const bi = best[1] * cols + best[0];
      chosen.push(best);
      blocked[bi] = 1;
      towers[bi] = 1;
      posts.push(best);
    }
  }
  return chosen;
}

// Port of balance_fill_gate.snake_walls(cells, spacing, augment). Returns fingers and (optionally) sentries.
export function snakeLayout(g, spacing, augment = false) {
  const { cols, rows } = g;
  const sx = g.start % cols, sy = (g.start - sx) / cols;
  const ex = g.end % cols, ey = (g.end - ex) / cols;
  const isDot = (x, y) => g.ch[y * cols + x] === '.';
  const candidates = [];
  let flip = 0;
  if (Math.abs(ex - sx) >= Math.abs(ey - sy)) {
    const step = ex > sx ? spacing : -spacing;
    let column = sx + step;
    while (step > 0 ? column < ex : column > ex) {
      const rng = flip === 0 ? pyRange(0, rows - 1) : pyRange(1, rows);
      for (const r of rng) if (isDot(column, r)) candidates.push([column, r]);
      flip ^= 1;
      column += step;
    }
  } else {
    const step = ey > sy ? spacing : -spacing;
    let row = sy + step;
    while (step > 0 ? row < ey : row > ey) {
      const rng = flip === 0 ? pyRange(0, cols - 1) : pyRange(1, cols);
      for (const c of rng) if (isDot(c, row)) candidates.push([c, row]);
      flip ^= 1;
      row += step;
    }
  }
  const towers = new Uint8Array(g.N);
  const fingers = [];
  for (const [x, y] of candidates) {
    const i = y * cols + x;
    towers[i] = 1;
    if (runtimePath(g, towers).length > 0) fingers.push([x, y]);
    else towers[i] = 0;
  }
  if (!augment) return { fingers, sentries: [] };
  const full = augmentLayout(g, fingers);
  return { fingers, sentries: full.slice(fingers.length) };
}

// ---------------------------------------------------------------- slots (policy P1 order)
// Slots = finger walls (+ sentries when enabled). Order: BFS distance from S on the empty map,
// then row, then column. Family round-robin normal, blast, frost over the finger order.
// Sentries (if any) are normal towers appended after the walls. --slotDrop removes the last slots.
export function buildSlots(g, opts) {
  const layout = snakeLayout(g, opts.spacing, opts.sentries);
  const dist = bfsDistance(g, g.start);
  const fingerSlots = layout.fingers.map(([x, y]) => {
    const idx = y * g.cols + x;
    return { x, y, idx, dist: dist[idx], kind: 'finger' };
  });
  fingerSlots.sort((a, b) => (a.dist - b.dist) || (a.y - b.y) || (a.x - b.x));
  const pattern = Array.isArray(opts.familyPattern) && opts.familyPattern.length
    ? opts.familyPattern
    : [0, 1, 2];
  const wallSlots = fingerSlots.map((s, i) => ({ ...s, family: pattern[i % pattern.length] }));
  const sentrySlots = [];
  for (const [x, y] of layout.sentries) {
    const idx = y * g.cols + x;
    sentrySlots.push({ x, y, idx, dist: dist[idx], kind: 'sentry', family: pattern[0] ?? 0 });
  }
  const slots = opts.sentryFirst ? [...sentrySlots, ...wallSlots] : [...wallSlots, ...sentrySlots];
  for (const s of slots) { s.state = 'pending'; s.tower = null; s.legalVersion = -1; s.legal = false; }
  const nDrop = Math.ceil(opts.slotDrop * slots.length - EPS);
  for (let i = slots.length - nDrop; i < slots.length; i++) slots[i].state = 'dropped';
  const occFingers = new Uint8Array(g.N);
  for (const s of slots) if (s.kind === 'finger') occFingers[s.idx] = 1;
  const emptyEdges = runtimePath(g, new Uint8Array(g.N)).length;
  const fingerEdges = runtimePath(g, occFingers).length;
  return {
    slots,
    layout: {
      fingerWalls: layout.fingers.length,
      sentries: layout.sentries.length,
      slotsTotal: slots.length,
      droppedSlots: nDrop,
      emptyPathEdges: emptyEdges > 0 ? emptyEdges - 1 : null,
      pathEdgesWithAllFingers: fingerEdges > 0 ? fingerEdges - 1 : null,
    },
  };
}

// ---------------------------------------------------------------- timeline (WaveManager.BeginRound)
// Spawn list relative to round start, in seconds. Unit j of a group spawns at groupStart + j*gap.
// The next group starts one gap after the last spawn of this group; a single-unit group adds one extra gap.
export function buildTimeline(round, tables) {
  const out = [];
  let offset = (round.interval || 0) / 1000;
  round.EnemyIndexs.forEach((groupId, groupIndex) => {
    const group = tables.groups.get(groupId);
    if (!group) throw new Error(`round ${round.id}: missing enemy group ${groupId}`);
    const gap = (group.enemyInterval > 0 ? group.enemyInterval : DEFAULT_GAP_MS) / 1000;
    const groupStart = offset + (group.interval || 0) / 1000;
    const n = group.EnemyIndexs.length;
    for (let j = 0; j < n; j++) {
      out.push({ time: groupStart + gap * j, enemyId: group.EnemyIndexs[j], group: groupIndex });
    }
    const groupEnd = groupStart + gap * Math.max(1, n - 1);
    offset = Math.max(offset, groupEnd + gap);
  });
  return out;
}

// ---------------------------------------------------------------- pure combat rules
// C#: BaseEnemy.Hurt: real = damage * (1 - armor). No floor, no overkill carry.
export function damageAfterArmor(raw, armor) {
  return raw * (1 - armor);
}

// C#: BaseTower.ConsumeCadence. Returns the number of full cycles completed and the leftover timer.
export function consumeCadence(timer, dt, interval) {
  if (dt <= 0) return { count: 0, timer };
  const elapsed = timer + dt;
  const count = Math.floor((elapsed + 1e-6) / interval);
  return { count, timer: Math.max(0, elapsed - count * interval) };
}

// C#: BaseEnemy.ApplySlow. Strongest only; weaker ignored while a stronger one is active;
// equal ratio refreshes; ratio clamped to 0.95.
export function applySlow(e, ratio, durationSec) {
  if (!e.alive || ratio <= 0 || durationSec <= 0) return false;
  const r = Math.min(Math.max(ratio, 0), SLOW_MAX);
  if (r < e.slowRatio && e.slowTimer > 0) return false;
  e.slowTimer = r > e.slowRatio ? durationSec : Math.max(e.slowTimer, durationSec);
  e.slowRatio = r;
  return true;
}

// C#: BaseTower.DetonateAt. The splash centre is fixed at the target position at fire time.
// Every live unit within radius of that centre is hit; flyers are skipped when the tower cannot hit air.
export function splashHits(enemies, cx, cy, radius, canAttackAir) {
  if (!(radius > 0)) return [];
  const r2 = radius * radius;
  const out = [];
  for (const e of enemies) {
    if (!e.alive) continue;
    if (e.flying && !canAttackAir) continue;
    const dx = e.x - cx;
    const dy = e.y - cy;
    if (dx * dx + dy * dy <= r2) out.push(e);
  }
  return out;
}

// C#: BaseTower.PickBestTarget. Air layer first when the tower can hit air; inside a layer the
// unit with the largest distance travelled wins; ties go to the lower unit id.
export function pickTarget(enemies, x, y, radius, canAttackAir, airOnly = false) {
  const r2 = radius * radius;
  let bestAir = null;
  let bestGround = null;
  for (const e of enemies) {
    if (!e.alive) continue;
    if (e.flying) { if (!canAttackAir) continue; } else if (airOnly) continue;
    const dx = e.x - x;
    const dy = e.y - y;
    if (dx * dx + dy * dy > r2) continue;
    if (e.flying) {
      if (bestAir === null || better(e, bestAir)) bestAir = e;
    } else if (bestGround === null || better(e, bestGround)) {
      bestGround = e;
    }
  }
  return bestAir !== null ? bestAir : bestGround;
}

function better(e, cur) {
  return e.travelled > cur.travelled || (e.travelled === cur.travelled && e.id < cur.id);
}

// Legal only if S still reaches E after the tower occupies idx (TowerManager.TryBuildInternal).
export function isLegalPlacement(g, occ, idx) {
  if (!g.buildable[idx] || occ[idx]) return false;
  occ[idx] = 1;
  const ok = runtimePath(g, occ, g.start).length > 0;
  occ[idx] = 0;
  return ok;
}

// ---------------------------------------------------------------- run state
export function prepareLevel(levelId, tables, opts) {
  const scene = tables.scenes.get(levelId);
  if (!scene) throw new Error(`level ${levelId}: no tbsceneinfo row`);
  const map = tables.maps.get(levelId);
  if (!map) throw new Error(`level ${levelId}: no tblevelmap row`);
  const grid = buildGrid(map);
  const { slots, layout } = buildSlots(grid, opts);
  return { levelId, name: scene.name, grid, scene, slots, layout };
}

export function makeRunState(prep, tables, opts) {
  const towerRows = normalizeTowerRows(tables);
  if (opts.towerPowerScale !== 1) {
    for (const row of towerRows.values()) row.power *= opts.towerPowerScale;
  }
  const g = prep.grid;
  return {
    levelId: prep.levelId,
    grid: g,
    opts,
    tables,
    scene: prep.scene,
    slots: prep.slots,
    layout: prep.layout,
    towerRows,
    l1Rows: l1Rows(towerRows),
    dt: opts.dt,
    k: 0,
    delaySteps: Math.max(0, Math.round(tables.global.autoNextRoundDelayMs / 1000 / opts.dt)),
    maxAlive: tables.global.maxEnemyAlive,
    gold: prep.scene.initialGold,
    hp: prep.scene.initialHp,
    occ: new Uint8Array(g.N),
    wallVersion: 0,
    routeCache: new Map(),
    towers: [],        // C# _towers order: append on build/upgrade, iterated in reverse
    builtOrder: [],    // slots in build order (upgrade queue)
    enemies: [],       // alive units in creation (id) order
    nextEnemyId: 1,
    nRounds: prep.scene.RoundList.length,
    roundIdx: 0,
    roundActive: false,
    nextStartStep: 1,  // round 1 starts at t = 0
    roundStep: 0,
    roundReward: 0,
    timeline: [],
    cursor: 0,
    rounds: [],
    kills: [],
    ledger: [],
    operations: [],
    scriptOperationIndex: 0,
    scriptFailures: [],
    deathSeq: 0,
    leaksTotal: 0,
    killedTotal: 0,
    spawnedTotal: 0,
    roundsCleared: 0,
    lost: null,
    done: false,
  };
}

function roundRec(st, idx) {
  while (st.rounds.length <= idx) {
    const i = st.rounds.length;
    st.rounds.push({
      index: i + 1, roundId: st.scene.RoundList[i], startSec: null, clearSec: null, cleared: false,
      goldStart: null, goldEnd: null, rewardGold: null,
      planned: 0, plannedGround: 0, plannedAir: 0,
      spawned: 0, spawnedGround: 0, spawnedAir: 0,
      killed: 0, leaked: 0, hpLost: 0, built: 0, upgraded: 0, spawnDeferredSteps: 0, delayedSpawns: 0,
    });
  }
  return st.rounds[idx];
}

const r4 = (v) => (v === null || v === undefined ? null : Math.round(v * 1e4) / 1e4);

function getRoute(st, from) {
  let route = st.routeCache.get(from);
  if (!route) {
    route = runtimePath(st.grid, st.occ, from);
    if (route.length === 0) throw new Error(`no ground route from cell ${from} (legality breached)`);
    st.routeCache.set(from, route);
  }
  return route;
}

function newTower(st, slot, row) {
  return { slot, row, x: st.grid.xOf[slot.idx], y: st.grid.yOf[slot.idx], fireTimer: 0, searchTimer: 0, target: null };
}

// Build a tower on a slot (caller checked price and legality).
export function placeTower(st, slot) {
  const row = st.l1Rows[slot.family];
  const before = st.gold;
  st.gold -= row.prices;
  st.occ[slot.idx] = 1;
  st.wallVersion += 1;
  st.routeCache.clear();
  const t = newTower(st, slot, row);
  st.towers.push(t);
  slot.tower = t;
  slot.state = 'built';
  st.builtOrder.push(slot);
  roundRec(st, st.roundIdx).built += 1;
  const op = { type: 'build', round: st.roundIdx + 1, timeSec: r4(st.k * st.dt),
    towerId: row.id, family: slot.family, level: row.level, x: slot.x, y: slot.y,
    price: row.prices, goldBefore: before, goldAfter: st.gold };
  st.operations.push(op);
  st.ledger.push({ type: 'spend', source: 'build', round: st.roundIdx + 1,
    timeSec: op.timeSec, amount: -row.prices, goldBefore: before, goldAfter: st.gold });
  return t;
}

// C#: TryUpgrade builds a new instance (fresh timers, no target) and retires the old one.
function upgradeSlot(st, slot, nextRow) {
  const before = st.gold;
  st.gold -= nextRow.prices;
  const i = st.towers.indexOf(slot.tower);
  if (i >= 0) st.towers.splice(i, 1);
  const t = newTower(st, slot, nextRow);
  st.towers.push(t);
  slot.tower = t;
  roundRec(st, st.roundIdx).upgraded += 1;
  const op = { type: 'upgrade', round: st.roundIdx + 1, timeSec: r4(st.k * st.dt),
    towerId: nextRow.id, family: slot.family, level: nextRow.level, x: slot.x, y: slot.y,
    price: nextRow.prices, goldBefore: before, goldAfter: st.gold };
  st.operations.push(op);
  st.ledger.push({ type: 'spend', source: 'upgrade', round: st.roundIdx + 1,
    timeSec: op.timeSec, amount: -nextRow.prices, goldBefore: before, goldAfter: st.gold });
}

export function makeEnemy(st, enemyId) {
  const cfg = st.tables.enemies.get(enemyId);
  if (!cfg) throw new Error(`missing enemy row ${enemyId}`);
  const g = st.grid;
  const flying = cfg.isFlying === 1;
  const e = {
    id: st.nextEnemyId++,
    birthId: `${st.levelId}-R${String(st.roundIdx + 1).padStart(2, '0')}-B${String(st.nextEnemyId - 1).padStart(6, '0')}`,
    eventSeq: null,
    enemyId,
    flying,
    alive: true,
    hp: st.roundIdx + 1 === st.nRounds ? Math.round(cfg.hp * st.opts.ehpScale) : cfg.hp,
    armor: cfg.armor,
    speed: cfg.speed,
    reward: cfg.reward,
    leakDamage: Math.max(MIN_LEAK_DAMAGE, cfg.damageToPlayer),
    travelled: 0,        // distance walked (cells), cumulative: the "path progress" for targeting
    slowRatio: 0,
    slowTimer: 0,
    x: g.xOf[g.start],
    y: g.yOf[g.start],
    route: null,         // ground: cell indices, current route
    s: 0,                // ground: arc length along current route (cells)
    total: 0,            // flyer: straight-line length S -> E
  };
  if (flying) {
    e.total = Math.hypot(g.xOf[g.end] - g.xOf[g.start], g.yOf[g.end] - g.yOf[g.start]);
  } else {
    e.route = getRoute(st, g.start);
  }
  return e;
}

function setGroundPos(st, e) {
  const r = e.route;
  const L = r.length - 1;
  const { xOf, yOf } = st.grid;
  if (e.s >= L) { e.x = xOf[r[L]]; e.y = yOf[r[L]]; return; }
  const i = Math.floor(e.s);
  const f = e.s - i;
  const a = r[i];
  const b = r[i + 1];
  e.x = xOf[a] + (xOf[b] - xOf[a]) * f;
  e.y = yOf[a] + (yOf[b] - yOf[a]) * f;
}

function leak(st, e) {
  e.alive = false;
  st.leaksTotal += 1;
  const rec = roundRec(st, st.roundIdx);
  rec.leaked += 1;
  rec.hpLost += e.leakDamage;
  st.hp = Math.max(0, st.hp - e.leakDamage);
  if (st.hp <= 0) {
    st.lost = { roundIndex: st.roundIdx + 1, roundId: st.scene.RoundList[st.roundIdx], timeSec: r4(st.k * st.dt) };
  }
}

// C#: BaseEnemy.Tick -> TickEffects (slow expiry), then MoveAlongPath / MoveStraight.
export function moveEnemy(st, e) {
  if (e.slowTimer > 0) {
    e.slowTimer -= st.dt;
    if (e.slowTimer <= 0) { e.slowTimer = 0; e.slowRatio = 0; }
  }
  const step = e.speed * (1 - e.slowRatio) * st.dt;
  if (e.flying) {
    e.travelled = Math.min(e.total, e.travelled + step);
    const f = e.total > 0 ? e.travelled / e.total : 1;
    const g = st.grid;
    e.x = g.xOf[g.start] + (g.xOf[g.end] - g.xOf[g.start]) * f;
    e.y = g.yOf[g.start] + (g.yOf[g.end] - g.yOf[g.start]) * f;
    if (e.travelled >= e.total) leak(st, e);
    return;
  }
  // A ground unit should always receive a route at spawn time. Keep the
  // simulator total when a malformed fixture or an invalid reroute leaves it
  // without one: the runtime treats an unreachable ground unit as a path
  // failure, and continuing with `route.length` would turn that data issue
  // into an opaque TypeError.
  if (!e.route || e.route.length === 0) {
    leak(st, e);
    return;
  }
  const L = e.route.length - 1;
  e.s += step;
  e.travelled += step;
  if (e.s >= L) {
    e.s = L;
    setGroundPos(st, e);
    leak(st, e);
    return;
  }
  setGroundPos(st, e);
}

// C#: BaseEnemy.Hurt + Die. Gold is paid immediately; the unit is untargetable from this moment.
export function hurtEnemy(st, e, raw) {
  if (!e.alive) return;
  e.hp -= damageAfterArmor(raw, e.armor);
  if (e.hp <= 0) kill(st, e);
}

function kill(st, e) {
  e.alive = false;
  st.gold += e.reward;
  st.killedTotal += 1;
  roundRec(st, st.roundIdx).killed += 1;
  st.deathSeq = (st.deathSeq || 0) + 1;
  e.eventSeq = st.deathSeq;
  const g = st.grid;
  const remaining = e.flying
    ? Math.hypot(g.xOf[g.end] - e.x, g.yOf[g.end] - e.y)  // flyers: Euclidean to E
    : (e.route ? e.route.length - 1 - e.s : null);        // ground: remaining path cells from E
  st.kills.push({
    birthId: e.birthId,
    enemyId: e.enemyId,
    round: st.roundIdx + 1,
    kind: e.flying ? 'air' : 'ground',
    remaining,
    x: r4(e.x),
    y: r4(e.y),
    eventSeq: e.eventSeq,
    timeSec: r4(st.k * st.dt),
  });
  st.ledger.push({ type: 'income', source: 'kill', round: st.roundIdx + 1,
    timeSec: r4(st.k * st.dt), amount: e.reward, birthId: e.birthId, goldAfter: st.gold });
}

function inRange(t, e) {
  const dx = e.x - t.x;
  const dy = e.y - t.y;
  return dx * dx + dy * dy <= t.row.radius * t.row.radius;
}

function fire(st, t, target) {
  const row = t.row;
  if (row.effectType === 3) {
    // C#: DetonateAt. Centre = target position at fire time; power applies to every hit unit.
    for (const e of splashHits(st.enemies, target.x, target.y, row.aoeRadius, row.canAttackAir)) {
      hurtEnemy(st, e, row.power);
    }
  } else {
    hurtEnemy(st, target, row.power);
  }
}

// C#: BaseTower.TickSlowAura. Pulse every CD, independent of any target; one pulse per step.
function pulse(st, t) {
  const row = t.row;
  const r2 = row.radius * row.radius;
  for (const e of st.enemies) {
    if (!e.alive) continue;
    if (e.flying && !row.canAttackAir) continue;
    const dx = e.x - t.x;
    const dy = e.y - t.y;
    if (dx * dx + dy * dy > r2) continue;
    applySlow(e, row.effectValue, row.cdSec + SLOW_LINGER_SEC);
  }
}

// C#: BaseTower.TickAttack for single-target and splash towers.
export function towerAct(st, t) {
  const row = t.row;
  const dt = st.dt;
  if (row.effectType === 1) {
    const c = consumeCadence(t.fireTimer, dt, row.cdSec);
    t.fireTimer = c.timer;
    if (c.count > 0) pulse(st, t);
    return;
  }
  if (t.target && (!t.target.alive || !inRange(t, t.target))) t.target = null;
  const s = consumeCadence(t.searchTimer, dt, row.searchSec);
  t.searchTimer = s.timer;
  if (s.count > 0) {
    if (!t.target) {
      t.target = pickTarget(st.enemies, t.x, t.y, row.radius, row.canAttackAir, false);
    } else if (st.opts.airPreempt && row.canAttackAir && !t.target.flying) {
      const air = pickTarget(st.enemies, t.x, t.y, row.radius, true, true);
      if (air) t.target = air;
    }
  }
  if (!t.target) return;   // no target: the cooldown does not accumulate
  const f = consumeCadence(t.fireTimer, dt, row.cdSec);
  t.fireTimer = f.timer;
  for (let i = 0; i < f.count; i++) {
    if (!t.target || !t.target.alive || !inRange(t, t.target)) {
      t.target = pickTarget(st.enemies, t.x, t.y, row.radius, row.canAttackAir, false);
    }
    if (!t.target) break;
    fire(st, t, t.target);
  }
}

// Re-path every living ground unit after the wall set changed. Each unit restarts from the cell
// nearest its position (C#: WorldToCell + UpdatePathByEnemyPoint). Travelled distance is kept.
function rerouteGround(st) {
  for (const e of st.enemies) {
    if (!e.alive || e.flying) continue;
    // A route can be absent only for malformed synthetic fixtures or after a
    // failed path update. Re-anchor such a unit at its nearest grid cell so a
    // later wall edit cannot crash the deterministic replay.
    let node;
    if (!e.route || e.route.length === 0) {
      let best = st.grid.start;
      let bestD = Infinity;
      for (let i = 0; i < st.grid.N; i++) {
        if (st.grid.terrain[i]) continue;
        const dx = st.grid.xOf[i] - e.x;
        const dy = st.grid.yOf[i] - e.y;
        const d = dx * dx + dy * dy;
        if (d < bestD || (d === bestD && i < best)) { best = i; bestD = d; }
      }
      node = best;
    } else {
      const L = e.route.length - 1;
      node = e.route[Math.min(L, Math.round(e.s))];
    }
    e.route = getRoute(st, node);
    e.s = 0;
    e.x = st.grid.xOf[node];
    e.y = st.grid.yOf[node];
  }
}

function legalCached(st, slot) {
  if (slot.legalVersion !== st.wallVersion) {
    slot.legal = isLegalPlacement(st.grid, st.occ, slot.idx);
    slot.legalVersion = st.wallVersion;
  }
  return slot.legal;
}

function upgradesOpen(st) {
  if (!st.opts.strictBuildFirst) return true;
  return !st.slots.some((s) => s.state === 'pending' && legalCached(st, s));
}

// P1 policy. Walls: any slot that is affordable and legal is built, scanning in slot order.
// Upgrades: head of the build-order queue, all to L2 first, then all to L3; wait for gold.
export function policy(st) {
  if (Array.isArray(st.opts.operationScript)) {
    let wallsChanged = false;
    const now = st.k * st.dt;
    while (st.scriptOperationIndex < st.opts.operationScript.length) {
      const op = st.opts.operationScript[st.scriptOperationIndex];
      if (Number(op.timeSec) > now + EPS) break;
      st.scriptOperationIndex += 1;
      const slot = st.slots.find((s) => s.x === op.x && s.y === op.y);
      let reason = null;
      if (!slot) reason = 'slot_missing';
      else if (slot.family !== op.family) reason = 'tower_family_mismatch';
      else if (op.type === 'build') {
        if (slot.state !== 'pending') reason = 'slot_not_pending';
        else if (st.gold < st.l1Rows[slot.family].prices) reason = 'insufficient_gold';
        else if (!isLegalPlacement(st.grid, st.occ, slot.idx)) reason = 'illegal_placement';
        else { placeTower(st, slot); wallsChanged = true; }
      } else if (op.type === 'upgrade') {
        if (!slot.tower || slot.state !== 'built') reason = 'tower_missing';
        else {
          const next = st.towerRows.get(slot.tower.row.upgradeTo);
          if (!next || next.level !== op.level) reason = 'upgrade_chain_mismatch';
          else if (st.gold < next.prices) reason = 'insufficient_gold';
          else upgradeSlot(st, slot, next);
        }
      } else reason = 'unsupported_operation';
      if (reason) st.scriptFailures.push({ source: op, atSec: r4(now), reason, gold: st.gold });
    }
    if (wallsChanged) rerouteGround(st);
    return;
  }
  let wallsChanged = false;
  for (const slot of st.slots) {
    if (slot.state !== 'pending') continue;
    const price = st.l1Rows[slot.family].prices;
    if (st.gold < price) continue;
    if (!isLegalPlacement(st.grid, st.occ, slot.idx)) { slot.state = 'illegal'; continue; }
    placeTower(st, slot);
    wallsChanged = true;
  }
  if (wallsChanged) rerouteGround(st);
  if (st.opts.forbidUpgrades) return;
  if (!upgradesOpen(st)) return;
  for (;;) {
    const needL2 = st.builtOrder.some((s) => s.tower.row.level < 2);
    const target = needL2 ? 2 : 3;
    const cand = st.builtOrder.find((s) => s.tower.row.level < target);
    if (!cand) return;
    const next = st.towerRows.get(cand.tower.row.upgradeTo);
    if (!next || next.level !== target) throw new Error('upgrade chain broken for tower row ' + cand.tower.row.id);
    if (st.gold < next.prices) return;
    upgradeSlot(st, cand, next);
  }
}

function startRound(st) {
  const k = st.k;
  const roundId = st.scene.RoundList[st.roundIdx];
  const round = st.tables.rounds.get(roundId);
  if (!round) throw new Error(`missing round row ${roundId}`);
  st.timeline = buildTimeline(round, st.tables);
  st.cursor = 0;
  st.roundActive = true;
  st.roundStep = k;
  st.roundReward = round.rewardGold;
  const rec = roundRec(st, st.roundIdx);
  rec.startSec = r4((k - 1) * st.dt);
  rec.goldStart = st.gold;
  rec.rewardGold = round.rewardGold;
  rec.planned = st.timeline.length;
  for (const entry of st.timeline) {
    const cfg = st.tables.enemies.get(entry.enemyId);
    if (cfg && cfg.isFlying === 1) rec.plannedAir += 1;
    else rec.plannedGround += 1;
  }
}

// C#: WaveManager.Tick. Spawns are deferred (not dropped) while the alive cap is reached.
function spawnDue(st) {
  const tl = (st.k - st.roundStep + 1) * st.dt;
  let deferred = false;
  while (st.cursor < st.timeline.length && st.timeline[st.cursor].time <= tl + EPS) {
    if (st.enemies.length >= st.maxAlive) { deferred = true; break; }
    const entry = st.timeline[st.cursor];
    st.cursor += 1;
    st.enemies.push(makeEnemy(st, entry.enemyId));
    st.spawnedTotal += 1;
    const rec = roundRec(st, st.roundIdx);
    rec.spawned += 1;
    const cfg = st.tables.enemies.get(entry.enemyId);
    if (cfg && cfg.isFlying === 1) rec.spawnedAir += 1;
    else rec.spawnedGround += 1;
  }
  if (deferred) {
    const rec = roundRec(st, st.roundIdx);
    rec.spawnDeferredSteps += 1;
    rec.delayedSpawns = Math.max(rec.delayedSpawns, st.timeline.length - st.cursor);
  }
}

// C#: GameFlowManager.FinishRound (reward once) and TickAutoNextRound (delay before next round).
function clearRound(st) {
  const rec = roundRec(st, st.roundIdx);
  const before = st.gold;
  st.gold += st.roundReward;
  st.ledger.push({ type: 'income', source: 'clearReward', round: st.roundIdx + 1,
    timeSec: r4(st.k * st.dt), amount: st.roundReward, goldBefore: before, goldAfter: st.gold });
  rec.goldEnd = st.gold;
  rec.clearSec = r4(st.k * st.dt);
  rec.cleared = true;
  st.roundActive = false;
  st.roundsCleared += 1;
  st.roundIdx += 1;
  if (st.roundIdx >= st.nRounds) { st.done = true; return; }
  // Round start time is (step-1)*dt, so the next round begins at clear + delay (delay steps after the clear step).
  st.nextStartStep = st.k + st.delaySteps + 1;
}

// One fixed step. Order follows CombatSystem.OnUpdate (enemies, towers) and then the wave flow.
export function stepOnce(st) {
  st.k += 1;
  if (!st.roundActive && !st.done && !st.lost && st.k >= st.nextStartStep) startRound(st);
  policy(st);
  for (const e of st.enemies) {
    if (!e.alive) continue;
    moveEnemy(st, e);
    if (st.lost) return;
  }
  for (let i = st.towers.length - 1; i >= 0; i--) towerAct(st, st.towers[i]);
  st.enemies = st.enemies.filter((e) => e.alive);
  if (st.roundActive) spawnDue(st);
  if (st.roundActive && st.cursor >= st.timeline.length && st.enemies.length === 0) clearRound(st);
}

// ---------------------------------------------------------------- level run and output
export function runLevel(levelId, tables, opts = {}) {
  const o = { ...DEFAULTS, ...opts };
  if (o.operationScriptDir && !Array.isArray(o.operationScript)) {
    const scriptPath = path.join(o.operationScriptDir, `L${String(levelId).padStart(2, '0')}.json`);
    const script = JSON.parse(fs.readFileSync(scriptPath, 'utf8').replace(/^\uFEFF/, ''));
    o.operationScript = Array.isArray(script) ? script : script.operations;
    if (!Array.isArray(o.operationScript)) throw new Error(`operation script has no operations: ${scriptPath}`);
  }
  const prep = prepareLevel(levelId, tables, o);
  const st = makeRunState(prep, tables, o);
  const maxSteps = Math.round(o.maxSimSec / o.dt);
  while (st.k < maxSteps && !st.lost && !st.done) stepOnce(st);
  const verdict = st.lost ? 'lost' : st.done ? (st.hp > 0 ? 'pass' : 'lost') : 'timeout';
  return buildOutput(st, prep, verdict);
}

export function quantile(sorted, q) {
  if (sorted.length === 0) return null;
  const pos = (sorted.length - 1) * q;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

function distStats(values) {
  const s = values.slice().sort((a, b) => a - b);
  if (s.length === 0) return { count: 0, min: null, q1: null, median: null, q3: null, max: null };
  return {
    count: s.length,
    min: r4(s[0]),
    q1: r4(quantile(s, 0.25)),
    median: r4(quantile(s, 0.5)),
    q3: r4(quantile(s, 0.75)),
    max: r4(s[s.length - 1]),
  };
}

function buildOutput(st, prep, verdict) {
  const rounds = st.rounds
    .filter((r) => r.startSec !== null)
    .map((r) => ({
      ...r,
      goldStart: r.goldStart, goldEnd: r.goldEnd,
      clearSec: r.clearSec,
    }));
  const finalKills = st.kills.filter((k) => k.round === st.nRounds);
  const groundKills = finalKills.filter((k) => k.kind === 'ground');
  const airKills = finalKills.filter((k) => k.kind === 'air');
  const lastOf = (list) => (list.length ? { ...list[list.length - 1], remaining: r4(list[list.length - 1].remaining) } : null);
  const lastAny = lastOf(finalKills);
  const finalRoundNumber = st.nRounds;
  const towerCounts = { L1: 0, L2: 0, L3: 0 };
  for (const s of st.builtOrder) towerCounts[`L${s.tower.row.level}`] += 1;
  const slotState = (name) => st.slots.filter((s) => s.state === name).length;
  return {
    schema: 'balance_sim/1',
    levelId: st.levelId,
    name: prep.name,
    map: { cols: prep.grid.cols, rows: prep.grid.rows, unexpectedChars: prep.grid.unexpected, extraStarts: prep.grid.extraStarts, extraEnds: prep.grid.extraEnds },
    options: {
      dt: st.opts.dt, spacing: st.opts.spacing, slotDrop: st.opts.slotDrop, ehpScale: st.opts.ehpScale,
      sentries: st.opts.sentries, airPreempt: st.opts.airPreempt, strictBuildFirst: st.opts.strictBuildFirst,
      fixedOperations: Array.isArray(st.opts.operationScript), operationCount: st.opts.operationScript?.length ?? null,
      operationScriptDir: st.opts.operationScriptDir || null,
      towerPowerScale: st.opts.towerPowerScale,
      forbidUpgrades: st.opts.forbidUpgrades,
      ehpScaleScope: 'final wave only; integer HP via Math.round',
      policy: Array.isArray(st.opts.operationScript) ? 'fixed operation replay' : 'P1 build-first',
      maxSimSec: st.opts.maxSimSec, configDir: st.opts.configDir || null,
    },
    layout: prep.layout,
    verdict,
    lost: st.lost,
    roundsCleared: st.roundsCleared,
    roundsTotal: st.nRounds,
    leaks: st.leaksTotal,
    killed: st.killedTotal,
    spawned: st.spawnedTotal,
    hpStart: st.scene.initialHp,
    hpMin: st.hp,
    goldFinal: st.gold,
    simSec: r4(st.k * st.dt),
    simSteps: st.k,
    towers: {
      built: st.builtOrder.length,
      byLevel: towerCounts,
      slotsIllegal: slotState('illegal'),
      slotsPending: slotState('pending'),
      slotsDropped: slotState('dropped'),
    },
    finalRound: {
      index: finalRoundNumber,
      reached: st.rounds.length >= finalRoundNumber && st.rounds[finalRoundNumber - 1].startSec !== null,
      ground: distStats(groundKills.map((k) => k.remaining)),
      air: distStats(airKills.map((k) => k.remaining)),
      lastKill: lastAny,
      lastGroundKill: lastOf(groundKills),
      lastAirKill: lastOf(airKills),
    },
    rounds,
    kills: st.kills,
    ledger: st.ledger,
    operations: st.operations,
    operationReplay: Array.isArray(st.opts.operationScript) ? {
      expected: st.opts.operationScript.length,
      executed: st.scriptOperationIndex - st.scriptFailures.length,
      failures: st.scriptFailures,
      remaining: Math.max(0, st.opts.operationScript.length - st.scriptOperationIndex),
    } : null,
  };
}

// ---------------------------------------------------------------- CLI
function parseArgs(argv) {
  const args = {};
  const flags = new Set(['sentries', 'sentryFirst', 'noAirPreempt', 'strictBuildFirst', 'forbidUpgrades']);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) throw new Error('unexpected argument: ' + a);
    const eq = a.indexOf('=');
    if (eq > 0) { args[a.slice(2, eq)] = a.slice(eq + 1); continue; }
    const name = a.slice(2);
    if (flags.has(name)) { args[name] = true; continue; }
    const val = argv[i + 1];
    if (val === undefined || val.startsWith('--')) throw new Error('missing value for ' + a);
    args[name] = val;
    i++;
  }
  return args;
}

function parseIntList(text) {
  const out = new Set();
  for (const part of String(text).split(',')) {
    const t = part.trim();
    if (!t) continue;
    const m = /^(\d+)(?:-(\d+))?$/.exec(t);
    if (!m) throw new Error(`bad level token: "${t}"`);
    const lo = Number(m[1]);
    const hi = m[2] === undefined ? lo : Number(m[2]);
    if (lo < 1 || hi < lo) throw new Error(`bad level range: "${t}"`);
    for (let v = lo; v <= hi; v++) out.add(v);
  }
  return [...out].sort((a, b) => a - b);
}

function assertUnderSimRoot(p, label) {
  const rel = path.relative(SIM_ROOT, p);
  if (rel === '' || rel.startsWith('..') || path.isAbsolute(rel)) {
    throw new Error(`${label} must be inside ${SIM_ROOT}: ${p}`);
  }
}

function optNumber(value, fallback, name, check) {
  if (value === undefined) return fallback;
  const v = Number(value);
  if (!Number.isFinite(v) || !check(v)) throw new Error(`bad --${name}: ${value}`);
  return v;
}

function parseFamilyPattern(value) {
  if (value === undefined) return [0, 1, 2];
  const aliases = new Map([['normal', 0], ['blast', 1], ['frost', 2], ['0', 0], ['1', 1], ['2', 2]]);
  const out = String(value).split(',').map((token) => {
    const key = token.trim().toLowerCase();
    if (!aliases.has(key)) throw new Error(`bad --familyPattern token: ${token}`);
    return aliases.get(key);
  }).filter((v) => Number.isInteger(v));
  if (!out.length) throw new Error('--familyPattern requires at least one tower family');
  return out;
}

function compactRow(o) {
  return {
    levelId: o.levelId,
    verdict: o.verdict,
    roundsCleared: o.roundsCleared,
    leaks: o.leaks,
    killed: o.killed,
    hpEnd: o.hpMin,
    lost: o.lost,
    towersBuilt: o.towers.built,
    byLevel: o.towers.byLevel,
    slotsIllegal: o.towers.slotsIllegal,
    clearSecLastRound: o.rounds.length ? o.rounds[o.rounds.length - 1].clearSec : null,
    finalRoundGround: o.finalRound.ground,
    finalRoundAir: o.finalRound.air,
    lastGroundKill: o.finalRound.lastGroundKill,
    lastAirKill: o.finalRound.lastAirKill,
    lastKill: o.finalRound.lastKill,
    simSec: o.simSec,
  };
}

function fmt(v) {
  if (v === null || v === undefined) return '-';
  return typeof v === 'number' ? String(Math.round(v * 100) / 100) : String(v);
}

function markdown(results, opts, command) {
  const out = [];
  out.push('# Balance simulator: current tables baseline');
  out.push('');
  out.push(`Command: \`${command}\``);
  out.push('Tables: \`Assets/ConfigJson/\` (read-only). Policy P1 build-first; spawning, combat and round flow ported from the C# runtime (see \`balance_sim.mjs\` header).');
  out.push(`Options: dt=${opts.dt}, spacing=${opts.spacing}, slotDrop=${opts.slotDrop}, ehpScale=${opts.ehpScale}, familyPattern=${opts.familyPattern.join(',')}, sentries=${opts.sentries}, airPreempt=${opts.airPreempt}, strictBuildFirst=${opts.strictBuildFirst}.`);
  const passed = results.filter((r) => r.verdict === 'pass').length;
  out.push(`Result: ${passed}/${results.length} levels pass; ${results.length - passed} lost or timed out.`);
  out.push('');
  out.push('"Last kill" distances are measured in the final round (round 25): ground = remaining path cells from E; air = Euclidean distance to E. "min HP" is the HP at the end of the run (HP only falls).');
  out.push('');
  out.push('| Lv | Verdict | Rounds cleared | Leaks | Killed | Min HP | Lost at (round, s) | Towers W/L1/L2/L3 | R25 ground last kill | R25 air last kill | R25 ground min/med/max | R25 air min/med/max |');
  out.push('|---|---|---|---|---|---|---|---|---|---|---|---|');
  for (const r of results) {
    const c = compactRow(r);
    const lost = c.lost ? `R${c.lost.roundIndex} @${fmt(c.lost.timeSec)}` : '-';
    const bl = c.byLevel;
    const g = c.finalRoundGround;
    const a = c.finalRoundAir;
    const gm = g.count ? `${fmt(g.min)}/${fmt(g.median)}/${fmt(g.max)} (n=${g.count})` : '-';
    const am = a.count ? `${fmt(a.min)}/${fmt(a.median)}/${fmt(a.max)} (n=${a.count})` : '-';
    out.push(`| ${String(c.levelId).padStart(2, '0')} | ${c.verdict} | ${c.roundsCleared} | ${c.leaks} | ${c.killed} | ${fmt(c.hpEnd)} | ${lost} | ${c.towersBuilt} (${bl.L1}/${bl.L2}/${bl.L3}) | ${c.lastGroundKill ? fmt(c.lastGroundKill.remaining) : '-'} | ${c.lastAirKill ? fmt(c.lastAirKill.remaining) : '-'} | ${gm} | ${am} |`);
  }
  out.push('');
  out.push('Per-level detail (per-round start/clear times, gold, kills, leaks, builds): `L<nn>.json` in the same folder.');
  out.push('');
  return out.join('\n') + '\n';
}

function main(argv) {
  const args = parseArgs(argv);
  const opts = {
    ...DEFAULTS,
    dt: optNumber(args.dt, DEFAULTS.dt, 'dt', (v) => v > 0 && v <= 0.5),
    spacing: optNumber(args.spacing, DEFAULTS.spacing, 'spacing', (v) => Number.isInteger(v) && v >= 1),
    slotDrop: optNumber(args.slotDrop, DEFAULTS.slotDrop, 'slotDrop', (v) => v >= 0 && v < 1),
    ehpScale: optNumber(args.ehpScale, DEFAULTS.ehpScale, 'ehpScale', (v) => v > 0),
    maxSimSec: optNumber(args.maxSimSec, DEFAULTS.maxSimSec, 'maxSimSec', (v) => v > 0),
    sentries: args.sentries === true,
    sentryFirst: args.sentryFirst === true,
    airPreempt: args.noAirPreempt !== true,
    strictBuildFirst: args.strictBuildFirst === true,
    towerPowerScale: optNumber(args.towerPowerScale, DEFAULTS.towerPowerScale, 'towerPowerScale', (v) => v >= 0),
    forbidUpgrades: args.forbidUpgrades === true,
    familyPattern: parseFamilyPattern(args.familyPattern),
    configDir: path.resolve(args.configDir || CONFIG_DIR),
    operationScriptDir: args.operationScriptDir ? path.resolve(args.operationScriptDir) : null,
  };
  const outDir = path.resolve(args.out || DEFAULT_OUT);
  assertUnderSimRoot(outDir, '--out');
  const summaryPath = path.resolve(args.summary || path.join(outDir, 'summary.md'));
  assertUnderSimRoot(summaryPath, '--summary');
  const levels = parseIntList(args.levels || '1-30');
  const configDir = path.resolve(args.configDir || CONFIG_DIR);
  if (opts.operationScriptDir) assertUnderSimRoot(opts.operationScriptDir, '--operationScriptDir');
  const tables = loadTables(configDir);
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];
  for (const id of levels) {
    const res = runLevel(id, tables, opts);
    fs.writeFileSync(path.join(outDir, `L${String(id).padStart(2, '0')}.json`), JSON.stringify(res, null, 2) + '\n', 'utf8');
    results.push(res);
    const c = compactRow(res);
    console.log([
      `L${String(id).padStart(2, '0')}`, c.verdict, `cleared=${c.roundsCleared}/${res.roundsTotal}`,
      `leaks=${c.leaks}`, `hp=${fmt(c.hpEnd)}`, `towers=${c.towersBuilt}`, `simSec=${fmt(c.simSec)}`,
      `R25 ground last=${fmt(c.lastGroundKill && c.lastGroundKill.remaining)}`,
      `R25 air last=${fmt(c.lastAirKill && c.lastAirKill.remaining)}`,
    ].join('\t'));
  }
  const command = `node .workbuddy/tools/balance_sim.mjs --levels ${args.levels || '1-30'} --dt ${opts.dt} --spacing ${opts.spacing} --slotDrop ${opts.slotDrop} --ehpScale ${opts.ehpScale} --towerPowerScale ${opts.towerPowerScale} --familyPattern ${opts.familyPattern.join(',')} --configDir "${configDir}"${opts.operationScriptDir ? ` --operationScriptDir "${opts.operationScriptDir}"` : ''}${opts.sentries ? ' --sentries' : ''}${opts.sentryFirst ? ' --sentryFirst' : ''}${opts.airPreempt ? '' : ' --noAirPreempt'}${opts.strictBuildFirst ? ' --strictBuildFirst' : ''}${opts.forbidUpgrades ? ' --forbidUpgrades' : ''}`;
  fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify({ command, options: opts, levels: results.map(compactRow) }, null, 2) + '\n', 'utf8');
  fs.mkdirSync(path.dirname(summaryPath), { recursive: true });
  fs.writeFileSync(summaryPath, markdown(results, opts, command), 'utf8');
  console.log(`wrote ${results.length} level files to ${outDir}`);
  console.log(`wrote ${summaryPath}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    main(process.argv.slice(2));
  } catch (err) {
    console.error('balance_sim: ' + (err && err.message ? err.message : err));
    process.exitCode = 1;
  }
}
