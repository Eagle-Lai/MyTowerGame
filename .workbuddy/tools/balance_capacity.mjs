#!/usr/bin/env node
// balance_capacity.mjs
// Node.js port of the S-shape wall layout and runtime path rules from the Python balance tooling.
// No npm dependencies. Read-only over project data; writes only capacity.json, capacity.md and
// grids_spacing2.txt into the --out directory.
//
// Ported from .workbuddy/tools:
//   balance_fill_gate.py  snake_walls(cells, spacing, augment=True), augment_layout(cells, walls, radius=2.0),
//                         _positions, _straight, _cover
//   balance_campaign.py   _runtime_path: 4-direction A*, heap ordered by (f, first-open ordinal),
//                         stops as soon as E enters the open list; capacity(): 0-1 reserved-route cost.
//
// Usage:
//   node .workbuddy/tools/balance_capacity.mjs --levels 1-30 --spacing 1,2,3 --out D:/FishTestGame/Docs/Balance_TowerCapacity
// Options:
//   --map <file>          default Assets/ConfigJson/tblevelmap.json (read only)
//   --grid-spacing <n>    spacing whose ASCII grids are written (default 2)

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(SCRIPT_DIR, '..', '..');
const DEFAULT_MAP = path.join(PROJECT_ROOT, 'Assets', 'ConfigJson', 'tblevelmap.json');
const DEFAULT_OUT = path.join(PROJECT_ROOT, 'Docs', 'Balance_TowerCapacity');
const DEFAULT_RADIUS = 2.0;

// balance_campaign._runtime_path neighbour order: (0,1),(0,-1),(-1,0),(1,0)
const ASTAR_DIRS = [[0, 1], [0, -1], [-1, 0], [1, 0]];
// balance_campaign.capacity neighbour order: (1,0),(0,1),(-1,0),(0,-1)
const CAP_DIRS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
// Packs (f, first-open ordinal) into one exact double key; ordinals stay far below 2^20 for these maps.
const KEY_SHIFT = 1048576;
const ALLOWED_CHARS = new Set(['.', 'S', 'E', 'P', '#', 'X']);

// ---------------------------------------------------------------- CLI
function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) throw new Error('unexpected argument: ' + a);
    const eq = a.indexOf('=');
    if (eq > 0) {
      args[a.slice(2, eq)] = a.slice(eq + 1);
    } else {
      const val = argv[i + 1];
      if (val === undefined || val.startsWith('--')) throw new Error('missing value for ' + a);
      args[a.slice(2)] = val;
      i++;
    }
  }
  return args;
}

// "1-3,7,10-12" -> [1,2,3,7,10,11,12]
function parseIntList(text, name) {
  const out = new Set();
  for (const part of String(text).split(',')) {
    const t = part.trim();
    if (!t) continue;
    const m = /^(\d+)(?:-(\d+))?$/.exec(t);
    if (!m) throw new Error(`bad ${name} token: "${t}"`);
    const lo = Number(m[1]);
    const hi = m[2] === undefined ? lo : Number(m[2]);
    if (lo < 1 || hi < lo) throw new Error(`bad ${name} range: "${t}"`);
    for (let v = lo; v <= hi; v++) out.add(v);
  }
  return [...out].sort((a, b) => a - b);
}

// ---------------------------------------------------------------- map
function loadMaps(file) {
  const text = fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '');
  const data = JSON.parse(text);
  if (!Array.isArray(data)) throw new Error('map file must be a JSON array: ' + file);
  return data;
}

// Grid of flat indices i = y * cols + x (x = column, y = row).
function buildGrid(entry) {
  const cells = entry.cells;
  const rows = cells.length;
  const cols = cells[0].length;
  if (rows !== entry.rows || cols !== entry.cols) {
    throw new Error(`level ${entry.levelId}: declared ${entry.cols}x${entry.rows}, data ${cols}x${rows}`);
  }
  for (const line of cells) {
    if (line.length !== cols) throw new Error(`level ${entry.levelId}: ragged row`);
  }
  const N = rows * cols;
  const ch = new Array(N);
  const terrain = new Uint8Array(N); // '#' or 'X': blocks enemies (Python '#X', C# IsWalkable false)
  let buildable = 0;
  let start = -1;
  let end = -1;
  let nS = 0;
  let nE = 0;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const c = cells[y][x];
      if (!ALLOWED_CHARS.has(c)) {
        throw new Error(`level ${entry.levelId}: unexpected cell char "${c}" at (${x},${y})`);
      }
      const i = y * cols + x;
      ch[i] = c;
      if (c === '#' || c === 'X') terrain[i] = 1;
      if (c === '.') buildable++;
      if (c === 'S') { nS++; if (start < 0) start = i; }
      if (c === 'E') { nE++; if (end < 0) end = i; }
    }
  }
  if (start < 0 || end < 0) throw new Error(`level ${entry.levelId}: missing S or E`);
  return { levelId: entry.levelId, cols, rows, N, ch, terrain, buildable, start, end, nS, nE };
}

// ---------------------------------------------------------------- heap
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

// ---------------------------------------------------------------- runtime path
// Port of balance_campaign._runtime_path (mirrors AStarWrapper.FindPath + AStarManager.GetAStarPath).
//  - 4-direction moves; '#', 'X' and overlay towers are impassable.
//  - F = G + Manhattan(H); G = steps; ties broken by first-open ordinal (C# open-list order).
//  - Stops as soon as E enters the open list, then follows parents from E.
// `towers` is a Uint8Array overlay (1 = tower/wall). Returns indices start..end, or [] if unreachable.
function runtimePath(g, towers) {
  const { cols, rows, N, terrain, start, end } = g;
  const ex = end % cols;
  const ey = (end - ex) / cols;
  const state = new Uint8Array(N); // 0 unseen, 1 open, 2 closed
  const seq = new Int32Array(N);   // first-open ordinal
  const gc = new Int32Array(N);
  const parent = new Int32Array(N).fill(-1);
  const heap = new PairHeap();
  let sequence = 0;

  state[start] = 1;
  seq[start] = 0;
  heap.push(0 * KEY_SHIFT + 0, start);
  while (heap.size > 0) {
    const key = heap.k[0];
    const cell = heap.v[0];
    heap.pop();
    const f = Math.floor(key / KEY_SHIFT);
    const cx = cell % cols;
    const cy = (cell - cx) / cols;
    const h = cell === start ? 0 : Math.abs(ex - cx) + Math.abs(ey - cy);
    if (state[cell] === 2 || f !== gc[cell] + h) continue; // stale entry
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

// Port of balance_campaign.capacity: 0-1 shortest route (primary = buildable cells entered, which is
// what capacity uses; secondary = geometric offset from the S->E axis, used only for route choice).
// Dijkstra on lexicographic cost; N is a few hundred so an O(N^2) selection is used.
function capacityOf(g) {
  const { cols, rows, N, ch, start, end } = g;
  const sx = start % cols, sy = (start - sx) / cols;
  const ex = end % cols, ey = (end - ex) / cols;
  const ax = ex - sx, ay = ey - sy;
  const length = Math.max(1, Math.hypot(ax, ay));
  const prim = new Float64Array(N).fill(Infinity);
  const sec = new Float64Array(N).fill(Infinity);
  const done = new Uint8Array(N);
  prim[start] = 0;
  sec[start] = 0;
  for (;;) {
    let cur = -1;
    for (let i = 0; i < N; i++) {
      if (done[i] || prim[i] === Infinity) continue;
      if (cur < 0 || prim[i] < prim[cur] || (prim[i] === prim[cur] && sec[i] < sec[cur])) cur = i;
    }
    if (cur < 0) break;
    done[cur] = 1;
    const cx = cur % cols, cy = (cur - cx) / cols;
    for (const [dx, dy] of CAP_DIRS) {
      const ox = cx + dx, oy = cy + dy;
      if (ox < 0 || oy < 0 || ox >= cols || oy >= rows) continue;
      const o = oy * cols + ox;
      const c = ch[o];
      if (c === '#' || c === 'X') continue;
      const weight = c === '.' ? 1 : 0;
      const offset = Math.abs((ox - sx) * ay - (oy - sy) * ax) / length;
      const np = prim[cur] + weight;
      const ns = sec[cur] + 1 + offset;
      if (np < prim[o] || (np === prim[o] && ns < sec[o])) {
        prim[o] = np;
        sec[o] = ns;
      }
    }
  }
  if (!Number.isFinite(prim[end])) {
    return { capacity: null, reserved: null, error: 'map has no legal ground route' };
  }
  return { capacity: g.buildable - prim[end], reserved: prim[end], error: null };
}

// ---------------------------------------------------------------- S-shape layout
function pyRange(a, b) { // Python range(a, b)
  const out = [];
  for (let i = a; i < b; i++) out.push(i);
  return out;
}

// Port of balance_fill_gate._straight(a, b, step=0.5)
function straight(a, b, step = 0.5) {
  const dx = Math.abs(a[0] - b[0]);
  const dy = Math.abs(a[1] - b[1]);
  const n = Math.max(1, Math.trunc(Math.sqrt(dx * dx + dy * dy) / step));
  const out = [];
  for (let i = 0; i <= n; i++) {
    out.push([a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]);
  }
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

// Lexicographic '>' on [primary, secondary] keys, same as Python tuple comparison.
function keyGreater(a, b) {
  if (a[0] !== b[0]) return a[0] > b[0];
  return a[1] > b[1];
}

function toXY(g, i) {
  const x = i % g.cols;
  return [x, (i - x) / g.cols];
}

// Port of balance_fill_gate.augment_layout(cells, walls, radius=2.0).
// Returns walls followed by the greedily added sentry cells.
function augmentLayout(g, walls, radius = DEFAULT_RADIUS) {
  const { cols, rows, N } = g;
  const r2 = radius * radius;
  const towers = new Uint8Array(N); // overlay mirrors `chosen`
  const blocked = new Uint8Array(N);
  for (const [x, y] of walls) {
    towers[y * cols + x] = 1;
    blocked[y * cols + x] = 1;
  }
  const pathIdx = runtimePath(g, towers);
  if (pathIdx.length === 0) return walls.map(([x, y]) => [x, y]);

  const ground = pathIdx.map((i) => toXY(g, i));
  const sPt = ground[0];
  const ePt = ground[ground.length - 1];
  const air = straight(sPt, ePt);
  const chosen = walls.map(([x, y]) => [x, y]);
  blocked[sPt[1] * cols + sPt[0]] = 1;
  blocked[ePt[1] * cols + ePt[0]] = 1;

  // free = '.' cells not yet blocked, row-major (r outer, c inner), as in the Python list comprehension
  const free = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      if (g.ch[i] === '.' && !blocked[i]) free.push([c, r]);
    }
  }

  // Ground / air coverage greedy
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
      if (bestKey === null || keyGreater(key, bestKey)) {
        best = cell;
        bestKey = key;
      }
    }
    if (best === null || bestKey[0] <= 0) break;
    const bi = best[1] * cols + best[0];
    chosen.push(best);
    blocked[bi] = 1;
    towers[bi] = 1;
  }

  // Air sentries: posts every second air point, within radius, legal only.
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
      if (bestKey === null || keyGreater(key, bestKey)) {
        best = cell;
        bestKey = key;
      }
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

// Port of balance_fill_gate.snake_walls(cells, spacing, augment=True).
function snakeWalls(g, spacing, augment = true) {
  const { cols, rows } = g;
  const sx = g.start % cols, sy = (g.start - sx) / cols;
  const ex = g.end % cols, ey = (g.end - ex) / cols;
  const isDot = (x, y) => g.ch[y * cols + x] === '.';
  const candidates = [];
  let flip = 0;
  if (Math.abs(ex - sx) >= Math.abs(ey - sy)) {
    // Horizontal corridor: vertical fingers, gap alternating bottom / top.
    const step = ex > sx ? spacing : -spacing;
    let column = sx + step;
    while (step > 0 ? column < ex : column > ex) {
      const rng = flip === 0 ? pyRange(0, rows - 1) : pyRange(1, rows);
      for (const r of rng) if (isDot(column, r)) candidates.push([column, r]);
      flip ^= 1;
      column += step;
    }
  } else {
    // Vertical corridor: horizontal fingers, gap alternating right / left.
    const step = ey > sy ? spacing : -spacing;
    let row = sy + step;
    while (step > 0 ? row < ey : row > ey) {
      const rng = flip === 0 ? pyRange(0, cols - 1) : pyRange(1, cols);
      for (const c of rng) if (isDot(c, row)) candidates.push([c, row]);
      flip ^= 1;
      row += step;
    }
  }

  // Greedy legality: keep a candidate only if S->E stays connected.
  const towers = new Uint8Array(g.N);
  const fingers = [];
  for (const [x, y] of candidates) {
    const i = y * cols + x;
    towers[i] = 1;
    if (runtimePath(g, towers).length > 0) fingers.push([x, y]);
    else towers[i] = 0;
  }
  if (!augment) return { towers: fingers, fingerCells: fingers, fingers: fingers.length, sentries: 0 };

  const full = augmentLayout(g, fingers);
  const sentries = full.slice(fingers.length);
  // Interleave sentries with fingers (balance_fill_gate.snake_walls "mixed" order).
  const mixed = [];
  const n = Math.max(fingers.length, sentries.length);
  for (let i = 0; i < n; i++) {
    if (i < fingers.length) mixed.push(fingers[i]);
    if (i < sentries.length) mixed.push(sentries[i]);
  }
  return { towers: mixed, fingerCells: fingers, fingers: fingers.length, sentries: sentries.length };
}

// Checks that a route is a real S->E walk over open, tower-free cells.
function checkPath(g, pathIdx, towers) {
  if (pathIdx.length === 0) return { connected: false, reason: 'no S->E route' };
  if (pathIdx[0] !== g.start || pathIdx[pathIdx.length - 1] !== g.end) {
    return { connected: false, reason: 'route does not run from S to E' };
  }
  const seen = new Set();
  for (let k = 0; k < pathIdx.length; k++) {
    const i = pathIdx[k];
    if (seen.has(i)) return { connected: false, reason: 'route repeats a cell' };
    seen.add(i);
    if (g.terrain[i] || towers[i]) return { connected: false, reason: 'route crosses a blocked cell' };
    if (k > 0) {
      const [ax, ay] = toXY(g, pathIdx[k - 1]);
      const [bx, by] = toXY(g, i);
      if (Math.abs(ax - bx) + Math.abs(ay - by) !== 1) return { connected: false, reason: 'non-adjacent step' };
    }
  }
  return { connected: true, reason: '' };
}

function asciiGrid(g, towers, pathIdx) {
  const onPath = new Uint8Array(g.N);
  for (const i of pathIdx) onPath[i] = 1;
  const digits = [];
  for (let x = 0; x < g.cols; x++) digits.push(String(x % 10));
  const lines = ['   ' + digits.join('')];
  for (let y = 0; y < g.rows; y++) {
    let line = '';
    for (let x = 0; x < g.cols; x++) {
      const i = y * g.cols + x;
      const c = g.ch[i];
      let out;
      if (towers[i]) out = '#';
      else if (c === 'S' || c === 'E') out = c;
      else if (onPath[i] && c === '.') out = '*';
      else out = c === '.' ? '.' : c; // terrain '#', 'X', 'P' kept as-is
      line += out;
    }
    lines.push(String(y).padStart(2, '0') + ' ' + line);
  }
  return lines.join('\n');
}

const round = (v, d = 4) => Math.round(v * 10 ** d) / 10 ** d;

function analyzeLevel(entry, spacings, gridSpacing, gridBlocks) {
  const g = buildGrid(entry);
  const issues = [];
  const sx = g.start % g.cols, sy = (g.start - sx) / g.cols;
  const ex = g.end % g.cols, ey = (g.end - ex) / g.cols;

  const empty = runtimePath(g, new Uint8Array(g.N));
  const emptyCheck = checkPath(g, empty, new Uint8Array(g.N));
  const cap = capacityOf(g);
  if (cap.error) issues.push('capacity: ' + cap.error);
  if (!emptyCheck.connected) issues.push('empty map: ' + emptyCheck.reason);

  const row = {
    levelId: g.levelId,
    cols: g.cols,
    rows: g.rows,
    buildableCells: g.buildable,
    start: [sx, sy],
    end: [ex, ey],
    euclideanStartEnd: round(Math.hypot(ex - sx, ey - sy)),
    capacity: cap.capacity,
    reservedBuildableCells: cap.reserved,
    emptyPathEdges: empty.length ? empty.length - 1 : null,
    bySpacing: {},
  };

  for (const s of spacings) {
    try {
      const layout = snakeWalls(g, s, true);
      const towers = new Uint8Array(g.N);
      for (const [x, y] of layout.towers) towers[y * g.cols + x] = 1;
      const pathIdx = runtimePath(g, towers);
      const check = checkPath(g, pathIdx, towers);

      // Fingers-only variant (snake_walls augment=False): same S-shape fingers, no sentries.
      const fingerTowers = new Uint8Array(g.N);
      for (const [x, y] of layout.fingerCells) fingerTowers[y * g.cols + x] = 1;
      const fingerPath = runtimePath(g, fingerTowers);
      const fingerCheck = checkPath(g, fingerPath, fingerTowers);

      const cellIssues = [];
      if (layout.towers.length === 0) cellIssues.push('zero towers');
      if (!check.connected) cellIssues.push('path not connected (' + check.reason + ')');
      row.bySpacing[String(s)] = {
        towers: layout.towers.length,
        fingerWalls: layout.fingers,
        sentryCells: layout.sentries,
        pathEdges: pathIdx.length ? pathIdx.length - 1 : null,
        pathConnected: check.connected,
        fingersOnly: {
          towers: layout.fingerCells.length,
          pathEdges: fingerPath.length ? fingerPath.length - 1 : null,
          pathConnected: fingerCheck.connected,
        },
        towerCells: layout.towers,
      };
      for (const m of cellIssues) issues.push(`s${s}: ${m}`);
      if (s === gridSpacing) {
        gridBlocks.push(`L${String(g.levelId).padStart(2, '0')}  ${g.cols}x${g.rows}  spacing=${s}  towers=${layout.towers.length}  pathEdges=${pathIdx.length ? pathIdx.length - 1 : 'none'}  (# tower/wall, * route, S start, E end, . open)\n` + asciiGrid(g, towers, pathIdx));
      }
    } catch (err) {
      const msg = err && err.message ? err.message : String(err);
      row.bySpacing[String(s)] = { error: msg };
      issues.push(`s${s}: exception: ${msg}`);
    }
  }
  row.issues = issues;
  return row;
}

// ---------------------------------------------------------------- output
// Compact pretty JSON: arrays of numbers / number pairs stay on one line.
function jsonPretty(v, indent = '') {
  if (Array.isArray(v)) {
    const inline = v.every((x) => typeof x !== 'object' || x === null
      || (Array.isArray(x) && x.every((y) => typeof y === 'number')));
    if (inline) return '[' + v.map((x) => JSON.stringify(x)).join(', ') + ']';
    const inner = indent + '  ';
    return '[\n' + v.map((x) => inner + jsonPretty(x, inner)).join(',\n') + '\n' + indent + ']';
  }
  if (v && typeof v === 'object') {
    const keys = Object.keys(v);
    if (keys.length === 0) return '{}';
    const inner = indent + '  ';
    return '{\n' + keys.map((k) => inner + JSON.stringify(k) + ': ' + jsonPretty(v[k], inner)).join(',\n') + '\n' + indent + '}';
  }
  return JSON.stringify(v);
}

function fmt(v) { return v === null || v === undefined ? '-' : String(v); }

function buildMarkdown(meta, rows, spacings) {
  const out = [];
  out.push('# Balance tower capacity: S-shape wall layout');
  out.push('');
  out.push(`Source: \`${meta.map}\` (${rows.length} maps). Generated by \`.workbuddy/tools/balance_capacity.mjs\` (no timestamp; identical input gives identical output).`);
  out.push(`Command: \`${meta.command}\``);
  out.push('');
  out.push('Rules (ported, see JSON `port`):');
  out.push('- Movement: 4-direction (AStarWrapper.cs GetSurroundPoints). Blocked: `#`, `X`, and tower cells. `S`/`E` are walkable.');
  out.push('- Route length: A* that stops when E enters the open list (balance_campaign._runtime_path). Edges = cells - 1.');
  out.push('- W = towers placed by snake_walls(augment=True): fingers + sentries. Each tower must keep S->E connected (BaseTower.cs TryBuildInternal).');
  out.push('- Capacity = buildable `.` cells minus the fewest `.` cells on any S->E route (balance_campaign.capacity).');
  out.push('- Euclid = straight-line start-end distance in cells.');
  out.push('');
  const head = ['Lv', 'cols x rows', 'buildable', 'capacity', 'empty path', 'euclid'];
  for (const s of spacings) head.push(`s${s} W`, `s${s} path`);
  head.push('issues');
  out.push('| ' + head.join(' | ') + ' |');
  out.push('|' + head.map(() => '---').join('|') + '|');
  for (const r of rows) {
    const cells = [
      String(r.levelId).padStart(2, '0'),
      `${r.cols} x ${r.rows}`,
      fmt(r.buildableCells),
      fmt(r.capacity),
      fmt(r.emptyPathEdges),
      fmt(r.euclideanStartEnd),
    ];
    for (const s of spacings) {
      const b = r.bySpacing[String(s)];
      if (!b || b.error) cells.push('ERR', 'ERR');
      else cells.push(fmt(b.towers), fmt(b.pathEdges));
    }
    cells.push(r.issues.length ? r.issues.join('; ') : '-');
    out.push('| ' + cells.join(' | ') + ' |');
  }
  out.push('');
  out.push('### Fingers only (snake_walls augment=False)');
  out.push('');
  out.push('Same serpentine fingers without the augment_layout sentries. Shown because the augmented layout (default above) adds sentry cells on top of the fingers.');
  out.push('');
  const head2 = ['Lv'];
  for (const s of spacings) head2.push(`s${s} W`, `s${s} path`);
  out.push('| ' + head2.join(' | ') + ' |');
  out.push('|' + head2.map(() => '---').join('|') + '|');
  for (const r of rows) {
    const cells = [String(r.levelId).padStart(2, '0')];
    for (const s of spacings) {
      const b = r.bySpacing[String(s)];
      if (!b || b.error) cells.push('ERR', 'ERR');
      else cells.push(fmt(b.fingersOnly.towers), fmt(b.fingersOnly.pathEdges));
    }
    out.push('| ' + cells.join(' | ') + ' |');
  }
  out.push('');
  out.push(`ASCII grids for spacing ${meta.gridSpacing}: \`grids_spacing${meta.gridSpacing}.txt\` in this directory (augmented layout).`);
  out.push('');
  return out.join('\n') + '\n';
}

// ---------------------------------------------------------------- main
function main() {
  const args = parseArgs(process.argv.slice(2));
  const mapFile = path.resolve(args.map || DEFAULT_MAP);
  const outDir = path.resolve(args.out || DEFAULT_OUT);
  const spacings = parseIntList(args.spacing || '2', 'spacing');
  const gridSpacing = Number(args['grid-spacing'] || 2);

  // Safety: never write into project data folders.
  const forbidden = ['Assets', 'Luban', path.join('.workbuddy', 'memory')].map((p) => path.join(PROJECT_ROOT, p));
  for (const f of forbidden) {
    const rel = path.relative(f, outDir);
    if (rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel))) {
      throw new Error('refusing to write into protected folder: ' + outDir);
    }
  }

  const maps = loadMaps(mapFile);
  let selected;
  if (args.levels) {
    const wanted = parseIntList(args.levels, 'levels');
    selected = wanted.map((id) => {
      const m = maps.find((e) => e.levelId === id);
      if (!m) throw new Error(`level ${id} not in ${mapFile}`);
      return m;
    });
  } else {
    selected = maps.slice().sort((a, b) => a.levelId - b.levelId);
  }

  const gridBlocks = [];
  const rows = selected.map((entry) => analyzeLevel(entry, spacings, gridSpacing, gridBlocks));

  const command = `node .workbuddy/tools/balance_capacity.mjs --levels ${args.levels || 'all'} --spacing ${spacings.join(',')} --out ${outDir}`;
  const meta = { map: path.relative(PROJECT_ROOT, mapFile).split(path.sep).join('/'), command, gridSpacing };
  const doc = {
    schema: 'balance_capacity/1',
    map: meta.map,
    spacings,
    gridSpacing,
    port: {
      runtimePath: 'balance_campaign.py _runtime_path (4-dir A*, stop when E enters open list, heap by (f, first-open ordinal))',
      snakeWalls: 'balance_fill_gate.py snake_walls(cells, spacing, augment=True) with augment_layout(radius=2.0)',
      capacity: 'balance_campaign.py capacity (0-1 reserved-route cost; primary count only)',
      csharp: 'AStarWrapper.cs FindPath / AStarManager.cs GetAStarPath; Board.cs ParseCell/IsWalkable/IsBuildable; BaseTower.cs TryBuildInternal',
    },
    command,
    levels: rows,
  };

  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'capacity.json'), jsonPretty(doc) + '\n', 'utf8');
  fs.writeFileSync(path.join(outDir, 'capacity.md'), buildMarkdown(meta, rows, spacings), 'utf8');
  fs.writeFileSync(path.join(outDir, `grids_spacing${gridSpacing}.txt`), gridBlocks.join('\n\n') + '\n', 'utf8');

  // Console summary (one line per level)
  const header = ['Lv', 'size', 'buildable', 'cap', 'empty'];
  for (const s of spacings) header.push(`s${s}:W/P`);
  console.log(header.join('\t'));
  for (const r of rows) {
    const cols = [String(r.levelId), `${r.cols}x${r.rows}`, r.buildableCells, fmt(r.capacity), fmt(r.emptyPathEdges)];
    for (const s of spacings) {
      const b = r.bySpacing[String(s)];
      cols.push(!b || b.error ? 'ERR' : `${b.towers}/${fmt(b.pathEdges)}`);
    }
    console.log(cols.join('\t') + (r.issues.length ? '\t!! ' + r.issues.join('; ') : ''));
  }
  console.log(`wrote ${path.join(outDir, 'capacity.json')}`);
  console.log(`wrote ${path.join(outDir, 'capacity.md')}`);
  console.log(`wrote ${path.join(outDir, `grids_spacing${gridSpacing}.txt`)}`);
}

try {
  main();
} catch (err) {
  console.error('balance_capacity: ' + (err && err.message ? err.message : err));
  process.exitCode = 1;
}
