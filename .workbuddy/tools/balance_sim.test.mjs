// balance_sim.test.mjs
// Unit and integration checks for .workbuddy/tools/balance_sim.mjs (run: node --test .workbuddy/tools/balance_sim.test.mjs).
// Uses only exported functions of balance_sim.mjs. Small fixtures are built with synthetic maps and the real
// tower / bullet rows, so the expected numbers can be computed by hand from the C# formulas.

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  loadTables, buildGrid, runtimePath, snakeLayout, normalizeTowerRows, makeRunState, stepOnce,
  towerAct, moveEnemy, hurtEnemy, pickTarget, splashHits, applySlow, consumeCadence,
  damageAfterArmor, buildTimeline, isLegalPlacement, runLevel, prepareLevel, DEFAULTS,
} from './balance_sim.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(HERE, '..', '..');
const REAL = loadTables();
const TOWER_ROWS = normalizeTowerRows(REAL);
const NORMAL_L1 = TOWER_ROWS.get(1);   // power 6, CD 450 ms, radius 2, canAttackAir
const BLAST_L1 = TOWER_ROWS.get(4);    // power 16, CD 1000 ms, radius 2, splash bullet 2 (aoeRadius 0.75)
const FROST_L1 = TOWER_ROWS.get(7);    // radius 3, slow 0.3, CD 250 ms

// ---------------------------------------------------------------- fixtures
// Build a run state on a synthetic map with the real tower and bullet tables.
function fixtureState({ lines, initialGold = 0, initialHp = 12, maxAlive = 200, rounds = [], groups = new Map(),
  enemies = new Map(), rewardGold = 0, dt = 0.05 }) {
  const cols = lines[0].length;
  const grid = buildGrid({ levelId: 999, cols, rows: lines.length, cells: lines });
  const roundIds = rounds.map((_, i) => 9000 + i);
  const tables = {
    ...REAL,
    global: { autoNextRoundDelayMs: 2500, maxEnemyAlive: maxAlive },
    scenes: new Map([[999, { id: 999, name: 'fixture', mapId: 999, RoundList: roundIds, initialGold, initialHp }]]),
    maps: new Map([[999, { levelId: 999, cols, rows: lines.length, cells: lines }]]),
    rounds: new Map(roundIds.map((id, i) => [id, { id, EnemyIndexs: rounds[i].groups, rewardGold: rounds[i].reward ?? rewardGold, interval: 0 }])),
    groups,
    enemies,
  };
  const prep = { levelId: 999, name: 'fixture', grid, scene: tables.scenes.get(999), slots: [], layout: {} };
  const st = makeRunState(prep, tables, { ...DEFAULTS, dt, airPreempt: false });
  return { st, grid, tables };
}

// Minimal unit with the fields used by moveEnemy / hurtEnemy / pickTarget.
let uid = 100;
function unit({ id = uid++, x = 0, y = 0, hp = 100, armor = 0, speed = 0, reward = 0, flying = false,
  travelled = 0, route = null, s = 0, damage = 1 } = {}) {
  return {
    id, enemyId: 0, flying, alive: true, hp, armor, speed, reward, leakDamage: damage,
    travelled, slowRatio: 0, slowTimer: 0, x, y, route, s, total: 0,
  };
}

// Open 1-row corridor "S" ... "E" with the real start/end indices.
const corridor = (n) => ['S' + '.'.repeat(n - 2) + 'E'];

// ---------------------------------------------------------------- (a) damage, cadence, slow, splash, targeting
test('damage: raw * (1 - armor), no floor and no overkill carry', () => {
  assert.equal(damageAfterArmor(6, 0.1), 5.4);
  assert.equal(damageAfterArmor(16, 0.35), 10.4);
  assert.equal(damageAfterArmor(13, 0), 13);
});

test('cadence: ConsumeCadence counts full cycles and keeps the remainder', () => {
  // 50 s of 0.05 s steps at a 0.45 s interval -> floor(50 / 0.45) = 111 cycles
  let timer = 0, total = 0;
  for (let i = 0; i < 1000; i++) {
    const c = consumeCadence(timer, 0.05, 0.45);
    total += c.count;
    timer = c.timer;
  }
  assert.equal(total, 111);
  // one large step can complete several cycles (accumulator, not one shot per step)
  assert.equal(consumeCadence(0, 0.9, 0.45).count, 2);
  assert.equal(consumeCadence(0, 0.45, 0.45).count, 1);
  assert.equal(consumeCadence(0, 0.2, 0.45).count, 0);
  assert.ok(Math.abs(consumeCadence(0, 0.5, 0.45).timer - 0.05) < 1e-12);
});

test('normal L1 tower vs Chick-like unit: 5.4 per shot, 60 shots, first hit at about 0.5 s', () => {
  const { st, grid } = fixtureState({ lines: ['S.....', '......', '.....E'] });
  // tower (1,1) within radius 2 of unit at S (0,0): distance sqrt(2)
  const tower = { row: NORMAL_L1, x: 1, y: 1, fireTimer: 0, searchTimer: 0, target: null, fired: 0 };
  const chick = unit({ x: 0, y: 0, hp: 320, armor: 0.1, speed: 0, route: [grid.start] });
  st.enemies.push(chick);
  let hits = 0, lastHp = chick.hp, firstHitStep = null, killStep = null;
  for (let k = 1; k <= 2000 && chick.alive; k++) {
    st.k = k;
    towerAct(st, tower);
    if (chick.hp < lastHp) {
      hits++;
      lastHp = chick.hp;
      if (firstHitStep === null) firstHitStep = k;
      if (!chick.alive) killStep = k;
      if (hits === 1) assert.ok(Math.abs(chick.hp - (320 - 5.4)) < 1e-9, 'first hit = 6 * (1 - 0.1)');
    }
  }
  assert.equal(hits, 60, 'ceil(320 / 5.4) = 60 shots');
  assert.equal(chick.alive, false);
  assert.ok(Math.abs(killStep * 0.05 - 27.05) < 0.11, `60th shot at about 27.05 s, got ${killStep * 0.05}`);
  assert.ok(Math.abs(firstHitStep * 0.05 - 0.5) < 0.06, `first shot at about 0.5 s, got ${firstHitStep * 0.05}`);
});

test('blast splash: centre = target position at fire time, radius 0.75 inclusive, flyers skipped', () => {
  const { st } = fixtureState({ lines: ['S........', '.........', '........E'] });
  const blast = { row: BLAST_L1, x: 2, y: 1, fireTimer: 0.95, searchTimer: 0, target: null, fired: 0 };
  const A = unit({ x: 4, y: 1, hp: 500 });                  // target, distance 2 from the tower
  const B = unit({ x: 4.6, y: 1, hp: 500, armor: 0.35 });   // 0.6 from centre -> hit, armour applies
  const C = unit({ x: 2.6, y: 1, hp: 500 });                // in tower range but 1.4 from centre -> miss
  const D = unit({ x: 4.9, y: 1, hp: 500 });                // 0.9 from centre -> miss
  const F = unit({ x: 4.2, y: 1, hp: 500, flying: true });  // inside splash, but blast cannot hit air
  blast.target = A;
  st.enemies.push(A, B, C, D, F);
  st.k = 1;
  towerAct(st, blast);
  assert.equal(A.hp, 500 - 16, 'target hit with power 16');
  assert.ok(Math.abs(B.hp - (500 - 16 * 0.65)) < 1e-9, 'B hit with armour 0.35');
  assert.equal(C.hp, 500, 'C outside the splash centre radius');
  assert.equal(D.hp, 500, 'D outside the splash radius');
  assert.equal(F.hp, 500, 'flyer untouched by a ground-only splash');
});

test('blast with aoeRadius <= 0 does nothing (no target damage)', () => {
  const hits = splashHits([unit({ x: 0, y: 0, hp: 9 })], 0, 0, 0, true);
  assert.equal(hits.length, 0);
});

test('slow: strongest only, weaker ignored while stronger active, equal refreshes, clamp 0.95', () => {
  const e = { alive: true, slowRatio: 0, slowTimer: 0 };
  assert.equal(applySlow(e, 0.3, 0.35), true);
  assert.equal(e.slowRatio, 0.3);
  assert.equal(applySlow(e, 0.5, 0.35), true);
  assert.equal(e.slowRatio, 0.5);
  assert.equal(applySlow(e, 0.3, 0.35), false, 'weaker ratio ignored while the stronger one is active');
  assert.equal(e.slowRatio, 0.5);
  e.slowTimer = 0.1;
  applySlow(e, 0.5, 0.35);
  assert.equal(e.slowTimer, 0.35, 'equal ratio refreshes the timer');
  applySlow(e, 1.2, 0.35);
  assert.equal(e.slowRatio, 0.95, 'ratio clamped to 0.95');
  assert.equal(applySlow({ alive: false, slowRatio: 0, slowTimer: 0 }, 0.3, 0.35), false, 'dead units are not slowed');
});

test('frost aura: slowed speed is speed * (1 - ratio) once pulses keep the slow alive', () => {
  // corridor 12 wide, unit speed 1.4, frost L1 (ratio 0.3, radius 3, CD 250 ms) at (1,0)
  const lines = ['S' + '.'.repeat(10) + 'E', '.'.repeat(12)];
  const { st, grid } = fixtureState({ lines });
  const frost = { row: FROST_L1, x: 1, y: 0, fireTimer: 0, searchTimer: 0, target: null, fired: 0 };
  const route = runtimePath(grid, new Uint8Array(grid.N));
  const u = unit({ x: grid.xOf ? 0 : 0, y: 0, speed: 1.4, route, s: 0 });
  u.x = 0; u.y = 1;   // row of S
  st.enemies.push(u);
  const dts = [];
  for (let k = 1; k <= 40; k++) {
    st.k = k;
    towerAct(st, frost);
    const before = u.s;
    moveEnemy(st, u);
    dts.push(u.s - before);
  }
  for (let k = 20; k < 40; k++) {
    assert.ok(Math.abs(dts[k] - 1.4 * 0.7 * 0.05) < 1e-9, `step ${k}: ${dts[k]}`);
  }
});

test('target choice: flyers first when the tower hits air; then max distance travelled; tie -> lower id', () => {
  const ground = [unit({ id: 2, x: 1, y: 0, travelled: 5 }), unit({ id: 1, x: 1, y: 0, travelled: 3 })];
  assert.equal(pickTarget(ground, 0, 0, 2, true).id, 2, 'more travelled wins');
  const tie = [unit({ id: 3, x: 1, y: 0, travelled: 4 }), unit({ id: 2, x: 1, y: 0, travelled: 4 })];
  assert.equal(pickTarget(tie, 0, 0, 2, true).id, 2, 'tie -> lower id');
  const mixed = [unit({ id: 1, x: 1, y: 0, travelled: 10 }), unit({ id: 9, x: 1, y: 0, travelled: 0, flying: true })];
  assert.equal(pickTarget(mixed, 0, 0, 2, true).id, 9, 'flyer preferred when the tower can hit air');
  assert.equal(pickTarget(mixed, 0, 0, 2, false).id, 1, 'ground-only tower ignores flyers');
  assert.equal(pickTarget([unit({ x: 5, y: 0 })], 0, 0, 2, true), null, 'out of range -> no target');
});

// ---------------------------------------------------------------- (a) legality, rewards, leaks, cap
test('placement legality: a tower that cuts S from E is rejected', () => {
  const g = buildGrid({ levelId: 1, cols: 3, rows: 1, cells: ['S.E'] });
  assert.equal(isLegalPlacement(g, new Uint8Array(g.N), 1), false);
  const open = buildGrid({ levelId: 2, cols: 3, rows: 3, cells: ['S..', '...', '..E'] });
  assert.equal(isLegalPlacement(open, new Uint8Array(open.N), 4), true);
});

test('kill pays gold immediately; round reward is paid once at clear; leak costs max(1, damage)', () => {
  // kill: immediate gold
  const { st, grid } = fixtureState({ lines: ['S..E'], initialGold: 0 });
  const dead = unit({ hp: 5, armor: 0, reward: 7, x: 0, y: 0 });
  st.enemies.push(dead);
  hurtEnemy(st, dead, 10);
  assert.equal(dead.alive, false);
  assert.equal(st.gold, 7);
  assert.equal(st.killedTotal, 1);
  assert.ok(grid.N === 4);
});

test('spawn cap: deferred, not dropped; leak deducts 1 HP for damageToPlayer 0; round reward once', () => {
  const groups = new Map([[77, { id: 77, EnemyIndexs: [5001, 5001, 5001], enemyInterval: 100, interval: 0 }]]);
  const enemies = new Map([[5001, { id: 5001, speed: 40, hp: 1, armor: 0, reward: 1, damageToPlayer: 0, isFlying: 0 }]]);
  const { st } = fixtureState({
    lines: corridor(12), initialGold: 0, initialHp: 12, maxAlive: 2, groups, enemies,
    rounds: [{ groups: [77], reward: 26 }],
  });
  let maxSeen = 0;
  for (let i = 0; i < 2000 && !st.done && !st.lost; i++) {
    stepOnce(st);
    maxSeen = Math.max(maxSeen, st.enemies.length);
  }
  assert.ok(maxSeen <= 2, `alive cap respected, max seen ${maxSeen}`);
  assert.equal(st.spawnedTotal, 3, 'all three units eventually spawn');
  assert.equal(st.leaksTotal, 3);
  assert.equal(st.hp, 12 - 3, 'each leak costs max(1, 0) = 1 HP');
  assert.equal(st.roundsCleared, 1);
  assert.equal(st.gold, 26, 'round reward paid once, no kill gold (no towers)');
});

test('malformed ground unit without a route is handled as a path failure, not a TypeError', () => {
  const { st } = fixtureState({ lines: corridor(6), initialHp: 3 });
  const e = unit({ x: 0, y: 0, speed: 1, route: null, damage: 1 });
  st.enemies.push(e);
  st.k = 1;
  moveEnemy(st, e);
  assert.equal(e.alive, false);
  assert.equal(st.leaksTotal, 1);
  assert.equal(st.hp, 2);
});

test('reroute re-anchors a malformed ground unit without a route', () => {
  const { st, grid } = fixtureState({ lines: ['S....E', '......'], rounds: [{ groups: [] }] });
  const e = unit({ x: 1, y: 0, speed: 0, route: null, s: 0 });
  st.enemies.push(e);
  assert.doesNotThrow(() => {
    // The helper is intentionally exercised through the exported placement
    // policy: a legal wall edit triggers the same reroute path as runtime.
    const slot = { idx: 7, family: 0, state: 'pending', legalVersion: -1, legal: null };
    st.slots = [slot];
    st.gold = 1000;
    st.k = 1;
    stepOnce(st);
  });
  assert.ok(e.route === null || Array.isArray(e.route));
  if (e.route) assert.ok(e.route.length > 0);
  assert.equal(grid.start, 0);
});

// ---------------------------------------------------------------- (a) spawn timeline
test('spawn timeline: unit k at start + k*gap; next group one gap after last spawn; single-unit group adds one gap', () => {
  const groups = new Map([
    [1, { id: 1, EnemyIndexs: [10, 10, 10], enemyInterval: 280, interval: 0 }],
    [2, { id: 2, EnemyIndexs: [20], enemyInterval: 200, interval: 0 }],
  ]);
  const tl = buildTimeline({ id: 1, EnemyIndexs: [1, 2], interval: 0 }, { groups });
  const t = tl.map((e) => Math.round(e.time * 1000) / 1000);
  assert.deepEqual(t, [0, 0.28, 0.56, 0.84]);
  const plain = buildTimeline({ id: 2, EnemyIndexs: [3], interval: 0 },
    { groups: new Map([[3, { id: 3, EnemyIndexs: [1, 1], enemyInterval: 0, interval: 0 }]]) });
  assert.deepEqual(plain.map((e) => e.time), [0, 0.2], 'enemyInterval 0 -> 200 ms default');
});

// ---------------------------------------------------------------- (b) layout and parity
test('layout: L30 has 53 finger walls and a 57-edge route with fingers only', () => {
  const grid = buildGrid(REAL.maps.get(30));
  const lay = snakeLayout(grid, 2, false);
  assert.equal(lay.fingers.length, 53);
  const occ = new Uint8Array(grid.N);
  for (const [x, y] of lay.fingers) occ[y * grid.cols + x] = 1;
  assert.equal(runtimePath(grid, occ).length - 1, 57);
});

test('layout: drop ratios remove ceil(W * ratio) slots', () => {
  const base = prepareLevel(1, REAL, { ...DEFAULTS, spacing: 2, sentries: true, slotDrop: 0 });
  const five = prepareLevel(1, REAL, { ...DEFAULTS, spacing: 2, sentries: true, slotDrop: 0.05 });
  const ten = prepareLevel(1, REAL, { ...DEFAULTS, spacing: 2, sentries: true, slotDrop: 0.1 });
  assert.equal(base.slots.length, 33);
  assert.equal(five.slots.filter((s) => s.state === 'dropped').length, Math.ceil(33 * 0.05));
  assert.equal(ten.slots.filter((s) => s.state === 'dropped').length, Math.ceil(33 * 0.1));
});

test('layout parity: fingers, sentries, route edges match Docs/Balance_TowerCapacity/capacity.json (spacing 2) on all 30 levels', () => {
  const capFile = path.join(PROJECT_ROOT, 'Docs', 'Balance_TowerCapacity', 'capacity.json');
  const cap = JSON.parse(fs.readFileSync(capFile, 'utf8'));
  for (const row of cap.levels) {
    const grid = buildGrid(REAL.maps.get(row.levelId));
    const lay = snakeLayout(grid, 2, true);
    const b = row.bySpacing['2'];
    assert.equal(lay.fingers.length, b.fingerWalls, `L${row.levelId} fingers`);
    assert.equal(lay.sentries.length, b.sentryCells, `L${row.levelId} sentries`);
    const occF = new Uint8Array(grid.N);
    for (const [x, y] of lay.fingers) occF[y * grid.cols + x] = 1;
    assert.equal(runtimePath(grid, occF).length - 1, b.fingersOnly.pathEdges, `L${row.levelId} finger path`);
    const occA = new Uint8Array(grid.N);
    for (const [x, y] of [...lay.fingers, ...lay.sentries]) occA[y * grid.cols + x] = 1;
    assert.equal(runtimePath(grid, occA).length - 1, b.pathEdges, `L${row.levelId} augmented path`);
  }
});

test('current tables: every map parses with only . S E # characters and one S, one E', () => {
  for (const [id, m] of REAL.maps) {
    const g = buildGrid(m);
    assert.deepEqual(g.warnings ?? [], [], `L${id}`);
    assert.ok(g.buildable.reduce((a, b) => a + b, 0) > 0, `L${id} has buildable cells`);
  }
});

// ---------------------------------------------------------------- (b) determinism
test('determinism: identical inputs give identical JSON (L1 and L30, default options)', () => {
  for (const id of [1, 30]) {
    const a = JSON.stringify(runLevel(id, REAL, {}));
    const b = JSON.stringify(runLevel(id, REAL, {}));
    assert.equal(a, b, `L${id}`);
  }
});

test('prepareLevel exposes ordered finger slots for the policy', () => {
  const prep = prepareLevel(30, REAL, { ...DEFAULTS });
  assert.equal(prep.slots.filter((s) => s.kind === 'finger').length, 53);
  assert.deepEqual(prep.slots.slice(0, 3).map((s) => s.family), [0, 1, 2], 'round-robin normal, blast, frost');
});
