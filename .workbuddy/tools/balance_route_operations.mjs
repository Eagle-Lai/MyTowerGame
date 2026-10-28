#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { DEFAULTS, buildGrid, loadTables, runLevel, runtimePath, snakeLayout } from './balance_sim.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), '../..');
const CFG = path.join(ROOT, 'Assets', 'ConfigJson');
const CAPACITY = path.join(ROOT, 'Docs', 'Balance_TowerCapacity', 'capacity.json');
const SIM = path.join(ROOT, 'Library', 'BalanceStage', 'sim');
const OUT = path.join(ROOT, 'Docs', 'Balance_TowerSystem', 'LevelRouteAndOperations');
const pad = (n) => String(n).padStart(2, '0');
const read = (file) => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const writeJson = (file, value) => fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
const writeText = (file, value) => fs.writeFileSync(file, value.endsWith('\n') ? value : `${value}\n`, 'utf8');
const rel = (file) => path.relative(ROOT, file).replaceAll('\\', '/');
const scenarioNames = ['base', 'ehp95', 'ehp105', 'drop05', 'drop10', 'power70', 'power50', 'noUpgrade'];
const profiles = Array.from({ length: 8 }, (_, i) => `D${pad(i + 1)}`);
const operationProfile = 'D01';
const guideRoot = path.join(SIM, `gold100_guides_${operationProfile}`);
const replayRoot = path.join(SIM, 'gold100_guide_replays');
const patterns = [[0, 1], [0, 0, 1], [0, 0, 0, 1], [0, 1, 2], [0, 1, 0, 2]];
const familyNames = new Map([[1, 'Normal'], [2, 'Blast'], [3, 'Frost']]);
const scenarioLabels = { base: '100% 基准', ehp95: 'EHP -5%', ehp105: 'EHP +5%', drop05: '减塔 5%', drop10: '减塔 10%', power70: '70% 火力', power50: '50% 火力', noUpgrade: '不升级' };

const maps = read(path.join(CFG, 'tblevelmap.json'));
const capacity = read(CAPACITY);
const cellSize = Number(read(path.join(CFG, 'tbglobal.json'))[0].cellSize);
const towerRows = read(path.join(CFG, 'tbtowerinfo.json'));
const towerById = new Map(towerRows.map((row) => [row.id, row]));
const sha256 = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const configNames = ['tbglobal.json', 'tbsceneinfo.json', 'tbrounddata.json', 'tbenemylist.json', 'tbenemydata.json', 'tbtowerinfo.json', 'tbbulletdata.json', 'tblevelmap.json'];
const inputHashes = Object.fromEntries(configNames.map((name) => [path.join('Assets', 'ConfigJson', name).replaceAll('\\', '/'), sha256(path.join(CFG, name))]));
const stagingHashes = Object.fromEntries(profiles.map((profile) => [profile, Object.fromEntries(configNames.map((name) => [name, sha256(path.join(ROOT, 'Library', 'BalanceStage', 'initial_gold_100', profile, name))]))]));
const simulatorHash = sha256(path.join(ROOT, '.workbuddy', 'tools', 'balance_sim.mjs'));

function selectRoute(levelId) {
  const entry = maps.find((row) => row.levelId === levelId);
  const cap = capacity.levels.find((row) => row.levelId === levelId);
  if (!entry || !cap) throw new Error(`missing map/capacity for L${pad(levelId)}`);
  const grid = buildGrid(entry);
  const candidates = Object.entries(cap.bySpacing).map(([spacing, value]) => {
    const towers = new Uint8Array(grid.N);
    for (const [x, y] of value.towerCells || []) towers[y * grid.cols + x] = 1;
    const route = runtimePath(grid, towers);
    return {
      spacing: Number(spacing),
      towerCount: (value.towerCells || []).length,
      fingerWalls: value.fingerWalls ?? null,
      sentries: value.sentryCells ?? null,
      pathEdges: Math.max(0, route.length - 1),
      path: route.map((cell) => [cell % grid.cols, Math.floor(cell / grid.cols)]),
      towerCells: value.towerCells || [],
      pathConnected: route.length > 0,
    };
  }).sort((a, b) => (b.pathEdges - a.pathEdges) || (a.towerCount - b.towerCount) || (a.spacing - b.spacing));
  const chosen = candidates[0];
  const routeSet = new Set(chosen.path.map(([x, y]) => `${x},${y}`));
  const towerSet = new Set(chosen.towerCells.map(([x, y]) => `${x},${y}`));
  const ascii = [];
  for (let y = 0; y < grid.rows; y++) {
    let row = '';
    for (let x = 0; x < grid.cols; x++) {
      const source = entry.cells[y][x];
      const key = `${x},${y}`;
      if (source === 'S' || source === 'E') row += source;
      else if (towerSet.has(key)) row += '#';
      else if (routeSet.has(key)) row += '*';
      else if (source === '#') row += 'X';
      else row += '.';
    }
    ascii.push(row);
  }
  return {
    levelId,
    map: { cols: grid.cols, rows: grid.rows, cellSize, start: [grid.start % grid.cols, Math.floor(grid.start / grid.cols)], end: [grid.end % grid.cols, Math.floor(grid.end / grid.cols)] },
    search: { seed: 0, iterations: candidates.length, candidateCount: candidates.length, candidates: candidates.map(({ spacing, towerCount, fingerWalls, sentries, pathEdges, pathConnected }) => ({ spacing, towerCount, fingerWalls, sentries, pathEdges, pathConnected })), objective: ['max pathEdges', 'min towerCount', 'min spacing'], guarantee: 'budgeted best among spacing 1/2/3 candidates; not a mathematical global optimum' },
    longestPath: { spacing: chosen.spacing, pathEdges: chosen.pathEdges, cells: chosen.path, towerCells: chosen.towerCells, fingerWalls: chosen.fingerWalls, sentries: chosen.sentries, pathConnected: chosen.pathConnected, ascii },
  };
}

function makeAscii(mapEntry, pathCells, towerCells) {
  const routeSet = new Set(pathCells.map(([x, y]) => `${x},${y}`));
  const towerSet = new Set(towerCells.map(([x, y]) => `${x},${y}`));
  return mapEntry.cells.map((sourceRow, y) => [...sourceRow].map((source, x) => {
    const key = `${x},${y}`;
    if (source === 'S' || source === 'E') return source;
    if (towerSet.has(key)) return '#';
    if (routeSet.has(key)) return '*';
    return source === '#' ? 'X' : '.';
  }).join(''));
}

function searchOperationPlan(levelId, tablesByProfile) {
  const rows = [];
  const tables = tablesByProfile.get(operationProfile);
  for (const spacing of [1, 2, 3]) for (const sentries of [false, true]) for (const familyPattern of patterns) {
    try {
      const sim = runLevel(levelId, tables, { ...DEFAULTS, spacing, sentries, familyPattern });
      rows.push({ spacing, sentries, familyPattern, sim, verdict: sim.verdict, roundsCleared: sim.roundsCleared, leaks: sim.leaks, hpMin: sim.hpMin, towersBuilt: sim.towers.built, pathEdges: sim.layout.pathEdgesWithAllFingers, error: null });
    } catch (error) {
      rows.push({ spacing, sentries, familyPattern, sim: null, verdict: 'error', roundsCleared: 0, leaks: null, hpMin: null, towersBuilt: null, pathEdges: null, error: error.message });
    }
  }
  const rank = (a, b) => (a.leaks - b.leaks) || (b.hpMin - a.hpMin) || (b.pathEdges - a.pathEdges) || (a.towersBuilt - b.towersBuilt) || (a.spacing - b.spacing);
  const passing = rows.filter((row) => row.verdict === 'pass').sort(rank);
  const viable = rows.filter((row) => row.sim).sort((a, b) => (b.roundsCleared - a.roundsCleared) || (a.leaks - b.leaks) || (b.hpMin - a.hpMin));
  const selected = passing[0] || viable[0];
  if (!selected) throw new Error(`no valid operation candidate for L${pad(levelId)}`);
  const mapEntry = maps.find((row) => row.levelId === levelId);
  const grid = buildGrid(mapEntry);
  const layout = snakeLayout(grid, selected.spacing, selected.sentries);
  const placedSet = new Set(selected.sim.operations.filter((op) => op.type === 'build').map((op) => `${op.x},${op.y}`));
  const towerCells = [...layout.fingers, ...layout.sentries].filter(([x, y]) => placedSet.has(`${x},${y}`));
  const towers = new Uint8Array(grid.N);
  for (const [x, y] of towerCells) towers[y * grid.cols + x] = 1;
  const pathCells = runtimePath(grid, towers).map((cell) => [cell % grid.cols, Math.floor(cell / grid.cols)]);
  const output = path.join(guideRoot, `L${pad(levelId)}.json`);
  fs.mkdirSync(guideRoot, { recursive: true });
  selected.sim.operationStrategy = { spacing: selected.spacing, sentries: selected.sentries, familyPattern: selected.familyPattern, candidateCount: rows.length };
  writeJson(output, selected.sim);
  const guideReplays = [];
  for (const profile of profiles) {
    const replay = runLevel(levelId, tablesByProfile.get(profile), {
      ...DEFAULTS, spacing: selected.spacing, sentries: selected.sentries, familyPattern: selected.familyPattern,
      operationScript: selected.sim.operations,
    });
    const replayFile = path.join(replayRoot, profile, `L${pad(levelId)}.json`);
    fs.mkdirSync(path.dirname(replayFile), { recursive: true });
    writeJson(replayFile, replay);
    guideReplays.push({ profileId: profile, verdict: replay.verdict, roundsCleared: replay.roundsCleared, roundsTotal: replay.roundsTotal, leaks: replay.leaks, hpStart: replay.hpStart, hpMin: replay.hpMin, goldFinal: replay.goldFinal, towersBuilt: replay.towers.built, operationFailures: replay.operationReplay?.failures?.length ?? 0, remainingOperations: replay.operationReplay?.remaining ?? 0, source: rel(replayFile) });
  }
  return {
    profileId: operationProfile,
    config: { spacing: selected.spacing, sentries: selected.sentries, familyPattern: selected.familyPattern },
    search: { seed: 0, iterations: rows.length, candidateCount: rows.length, passingCandidates: passing.length, objective: ['pass', 'min leaks', 'max remaining HP', 'max route pathEdges', 'min towersBuilt'], candidates: rows.map(({ spacing: candidateSpacing, sentries: candidateSentries, familyPattern, verdict, roundsCleared, leaks, hpMin, towersBuilt, pathEdges, error }) => ({ spacing: candidateSpacing, sentries: candidateSentries, familyPattern, verdict, roundsCleared, leaks, hpMin, towersBuilt, pathEdges, error })) },
    verdict: selected.verdict, roundsCleared: selected.roundsCleared, roundsTotal: selected.sim.roundsTotal, leaks: selected.leaks, hpMin: selected.hpMin,
    source: rel(output), operations: selected.sim.operations, guideReplays,
    layout: { candidateFingerWalls: layout.fingers.length, candidateSentries: layout.sentries.length, builtWalls: towerCells.filter(([x, y]) => layout.fingers.some(([fx, fy]) => fx === x && fy === y)).length, builtSentries: towerCells.filter(([x, y]) => layout.sentries.some(([sx, sy]) => sx === x && sy === y)).length, towerCells, pathEdges: Math.max(0, pathCells.length - 1), path: pathCells, ascii: makeAscii(mapEntry, pathCells, towerCells) },
  };
}

function readSim(scenario, profile, levelId) {
  const file = path.join(SIM, `gold100_${scenario}_${profile}`, `L${pad(levelId)}.json`);
  if (!fs.existsSync(file)) return null;
  const value = read(file);
  return {
    scenario, profileId: profile, verdict: value.verdict, roundsCleared: value.roundsCleared, roundsTotal: value.roundsTotal,
    leaks: value.leaks, killed: value.killed, spawned: value.spawned, hpStart: value.hpStart, hpMin: value.hpMin,
    goldFinal: value.goldFinal, towersBuilt: value.towers?.built ?? null, towersByLevel: value.towers?.byLevel ?? null,
    simSec: value.simSec, operationFailures: value.operationReplay?.failures?.length ?? 0,
    firstFailure: value.operationReplay?.failures?.[0] ?? null, source: rel(file), initialGold: 100,
  };
}

function readGuideReplay(profile, levelId) {
  const file = path.join(replayRoot, profile, `L${pad(levelId)}.json`);
  if (!fs.existsSync(file)) return null;
  const value = read(file);
  return {
    scenario: 'guide_replay', profileId: profile, verdict: value.verdict, roundsCleared: value.roundsCleared, roundsTotal: value.roundsTotal,
    leaks: value.leaks, killed: value.killed, spawned: value.spawned, hpStart: value.hpStart, hpMin: value.hpMin,
    goldFinal: value.goldFinal, towersBuilt: value.towers?.built ?? null, towersByLevel: value.towers?.byLevel ?? null,
    simSec: value.simSec, operationFailures: value.operationReplay?.failures?.length ?? 0,
    firstFailure: value.operationReplay?.failures?.[0] ?? null, remainingOperations: value.operationReplay?.remaining ?? 0,
    source: rel(file), initialGold: 100, artifactHash: sha256(file),
  };
}

function pickProfile(results) {
  const pass = profiles.filter((profile) => results.find((row) => row.profileId === profile && row.scenario === 'base')?.verdict === 'pass');
  return { recommendedProfile: pass[0] || 'D01', passProfiles: pass };
}

function operationPlan(profile, levelId, guided = null) {
  const file = guided ? path.join(ROOT, guided.source) : path.join(SIM, `gold100_base_${profile}`, `L${pad(levelId)}.json`);
  const value = read(file);
  const operations = (guided?.operations || value.operations || []).map((op, index) => {
    const row = towerById.get(op.towerId);
    return {
      index: index + 1, type: op.type, round: op.round, timeSec: op.timeSec, x: op.x, y: op.y,
      family: familyNames.get(op.family + 1) || `Family${op.family + 1}`, familyId: op.family,
      level: op.level, towerId: op.towerId, towerName: row?.name ?? null, price: op.price,
      goldBefore: op.goldBefore, goldAfter: op.goldAfter,
    };
  });
  const placements = new Map();
  for (const op of operations) {
    const key = `${op.x},${op.y}`;
    const item = placements.get(key) || { x: op.x, y: op.y, family: op.family, familyId: op.familyId, finalLevel: 0, build: null, upgrades: [] };
    if (op.type === 'build') item.build = op;
    if (op.type === 'upgrade') { item.upgrades.push(op); item.finalLevel = Math.max(item.finalLevel, op.level); }
    if (op.type === 'build') item.finalLevel = Math.max(item.finalLevel, 1);
    placements.set(key, item);
  }
  return {
    source: rel(file), policy: value.options?.policy ?? 'P1 build-first', verdict: value.verdict,
    roundsCleared: value.roundsCleared, roundsTotal: value.roundsTotal, leaks: value.leaks, hpMin: value.hpMin,
    operations, placements: [...placements.values()].sort((a, b) => (a.build?.timeSec ?? 0) - (b.build?.timeSec ?? 0)),
  };
}

function markdown(doc) {
  const route = doc.longestPath;
  const summary = doc.diagnostics.find((row) => row.scenario === 'base' && row.profileId === doc.operationProfile);
  const lines = [];
  lines.push(`# L${pad(doc.levelId)} 路线与防御塔操作流程`);
  lines.push('');
  lines.push('本页是 `initialGold=100` 的离线复现资料。路线和操作策略都是有限候选中的预算内最佳，不代表数学全局最优；失败证据仍按 `lost` 保留。');
  lines.push('');
  lines.push(`- 地图：${doc.map.cols}×${doc.map.rows}；cellSize=${doc.map.cellSize}；起点：(${doc.map.start[0]},${doc.map.start[1]})；终点：(${doc.map.end[0]},${doc.map.end[1]})`);
  lines.push(`- 最长路线搜索：seed=${doc.search.seed}，iterations=${doc.search.iterations}，candidateCount=${doc.search.candidateCount}，候选 spacing=1/2/3`);
  lines.push(`- 选中 spacing=${route.spacing}，最长路径=${route.pathEdges} 条边（${Number((route.pathEdges * doc.map.cellSize).toFixed(3))} 世界单位），布局候选塔位=${route.towerCells.length}（fingerWalls=${route.fingerWalls}，sentries=${route.sentries}）`);
  lines.push(`- 通关策略搜索：seed=${doc.operation.search.seed}，iterations=${doc.operation.search.iterations}，passingCandidates=${doc.operation.search.passingCandidates}/${doc.operation.search.candidateCount}；操作 spacing=${doc.operation.config.spacing}，familyPattern=${doc.operation.config.familyPattern.join(',')}，sentries=${doc.operation.config.sentries}`);
  lines.push(`- 操作 profile：${doc.operationProfile}；策略结果=${doc.operation.verdict}，通关波次=${doc.operation.roundsCleared}/${doc.operation.roundsTotal}，漏怪=${doc.operation.leaks}，剩余 HP=${doc.operation.hpMin}`);
  lines.push('- 操作方法：点击塔按钮进入预览后点击棋盘格放置；或长按/按住移动拖到格子并松手放置。点击已建塔后用塔旁升级按钮；资源不足时等待击杀金/清场金到账后再升级。');
  lines.push('');
  lines.push('## 最长路径图');
  lines.push('');
  lines.push('图例：`#` 塔/墙，`*` 路径，`S` 起点，`E` 终点，`X` 地形障碍，`.` 空地。');
  lines.push('');
  lines.push('```text');
  lines.push(`   ${Array.from({ length: doc.map.cols }, (_, i) => i % 10).join('')}`);
  route.ascii.forEach((row, index) => lines.push(`${String(index).padStart(2, '0')} ${row}`));
  lines.push('```');
  lines.push('');
  lines.push(`路径坐标（${route.cells.length} 个节点）：`);
  lines.push('');
  lines.push(route.cells.map(([x, y]) => `(${x},${y})`).join(' → '));
  lines.push('');
  lines.push('## 通关阵型路径');
  lines.push('');
  lines.push(`下图只标出操作序列实际建成的塔：墙塔 ${doc.operation.layout.builtWalls} 个、哨位 ${doc.operation.layout.builtSentries} 个；候选布局容量为墙塔 ${doc.operation.layout.candidateFingerWalls} 个、哨位 ${doc.operation.layout.candidateSentries} 个；spacing=${doc.operation.config.spacing}，实际路径 ${doc.operation.layout.pathEdges} 条边。`);
  lines.push('');
  lines.push('```text');
  lines.push(`   ${Array.from({ length: doc.map.cols }, (_, i) => i % 10).join('')}`);
  doc.operation.layout.ascii.forEach((row, index) => lines.push(`${String(index).padStart(2, '0')} ${row}`));
  lines.push('```');
  lines.push('');
  lines.push(`通关阵型路径坐标：${doc.operation.layout.path.map(([x, y]) => `(${x},${y})`).join(' → ')}`);
  lines.push('');
  lines.push('## 塔位与操作顺序');
  lines.push('');
  lines.push(`操作来源：\`${doc.operation.source}\`；策略：P1 build-first，塔型轮换 ${doc.operation.config.familyPattern.join(',')}（0=普通、1=火力、2=减速）。时点为仿真时间，逐项照表建造/升级；购买时以当前可用金币为准。`);
  lines.push('');
  lines.push('| 塔位 | 类型 | 最终等级 | 首次建造(s) | 升级次数 |');
  lines.push('|---|---|---:|---:|---:|');
  for (const item of doc.operation.placements) {
    lines.push(`| (${item.x},${item.y}) | ${item.family} | ${item.finalLevel} | ${item.build?.timeSec ?? '-'} | ${item.upgrades.length} |`);
  }
  lines.push('');
  lines.push('| # | 时间(s) | 波次 | 动作 | 类型 | 等级 | 坐标 | 花费 | 金币前→后 |');
  lines.push('|---:|---:|---:|---|---|---:|---|---:|---|');
  for (const op of doc.operation.operations) {
    lines.push(`| ${op.index} | ${op.timeSec} | ${op.round} | ${op.type} | ${op.family} | ${op.level} | (${op.x},${op.y}) | ${op.price} | ${op.goldBefore}→${op.goldAfter} |`);
  }
  lines.push('');
  lines.push('## 八档仿真结果');
  lines.push('');
  lines.push('| 场景 | Profile | 结果 | 波次 | 漏怪 | HP | 塔数 | 操作失败 |');
  lines.push('|---|---|---|---:|---:|---:|---:|---:|');
  for (const row of doc.simulations) {
    lines.push(`| 固定流程回放 | ${row.profileId} | ${row.verdict} | ${row.roundsCleared}/${row.roundsTotal} | ${row.leaks} | ${row.hpMin}/${row.hpStart} | ${row.towersBuilt ?? '-'} | ${row.operationFailures} |`);
  }
  lines.push('');
  lines.push('## 鲁棒性诊断汇总');
  lines.push('');
  lines.push('| 场景 | Profile 数 | 通关 | 零漏怪 | 满HP |');
  lines.push('|---|---:|---:|---:|---:|');
  for (const scenario of scenarioNames) {
    const rows = doc.diagnostics.filter((row) => row.scenario === scenario);
    lines.push(`| ${scenarioLabels[scenario] || scenario} | ${rows.length} | ${rows.filter((row) => row.verdict === 'pass').length} | ${rows.filter((row) => row.leaks === 0).length} | ${rows.filter((row) => row.hpMin === row.hpStart).length} |`);
  }
  lines.push('');
  if (summary?.verdict !== 'pass') lines.push(`注意：D01 默认策略基准为 ${summary?.verdict ?? 'missing'}；本页通关流程来自单独策略搜索，默认基准失败仍保留在表中。`, '');
  lines.push('JSON 文件包含完整路径节点、塔位、逐步操作、资金和每档仿真来源。');
  return lines.join('\n');
}

function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const tablesByProfile = new Map(profiles.map((profile) => [profile, loadTables(path.join(ROOT, 'Library', 'BalanceStage', 'initial_gold_100', profile))]));
  const index = [];
  for (let levelId = 1; levelId <= 30; levelId++) {
    const route = selectRoute(levelId);
    const diagnostics = profiles.flatMap((profile) => scenarioNames.map((scenario) => readSim(scenario, profile, levelId))).filter(Boolean);
    const guided = searchOperationPlan(levelId, tablesByProfile);
    const simulations = guided.guideReplays.map((row) => readGuideReplay(row.profileId, levelId)).filter(Boolean);
    const profileChoice = { recommendedProfile: operationProfile, passProfiles: guided.verdict === 'pass' ? [operationProfile] : [] };
    const operation = operationPlan(profileChoice.recommendedProfile, levelId, guided);
    operation.config = guided.config;
    operation.search = guided.search;
    operation.layout = guided.layout;
    operation.verdict = guided.verdict;
    operation.roundsCleared = guided.roundsCleared;
    operation.roundsTotal = guided.roundsTotal;
    operation.leaks = guided.leaks;
    operation.hpMin = guided.hpMin;
    const doc = {
      schema: 'balance_route_operations/1', generatedAt: new Date().toISOString(), initialGold: 100,
      levelId, map: route.map, search: route.search, longestPath: route.longestPath,
      operationProfile: profileChoice.recommendedProfile, passProfiles: profileChoice.passProfiles,
      operation, simulations, diagnostics,
      sources: { map: 'Assets/ConfigJson/tblevelmap.json', capacity: rel(CAPACITY), operation: operation.source, simulator: '.workbuddy/tools/balance_sim.mjs' },
      evidence: { status: 'simulated', inputHashes, stagingHashes, capacityHash: sha256(CAPACITY), simulatorHash, selectedOperationHash: sha256(path.join(ROOT, operation.source)), operationReplayArtifactHashes: Object.fromEntries(simulations.map((row) => [row.profileId, row.artifactHash])) },
    };
    writeJson(path.join(OUT, `L${pad(levelId)}.json`), doc);
    writeText(path.join(OUT, `L${pad(levelId)}.md`), markdown(doc));
    const d01 = simulations.find((row) => row.profileId === 'D01');
    index.push({ levelId, markdown: `L${pad(levelId)}.md`, json: `L${pad(levelId)}.json`, spacing: route.longestPath.spacing, pathEdges: route.longestPath.pathEdges, towerCount: route.longestPath.towerCells.length, operationProfile: profileChoice.recommendedProfile, operationSpacing: guided.config.spacing, operationFamilyPattern: guided.config.familyPattern, operationSentries: guided.config.sentries, operationVerdict: guided.verdict, operationLeaks: guided.leaks, operationHpMin: guided.hpMin, passProfiles: profileChoice.passProfiles, d01: d01 ? { verdict: d01.verdict, roundsCleared: d01.roundsCleared, leaks: d01.leaks, hpMin: d01.hpMin, operationCount: operation.operations.length, operationFailures: d01.operationFailures } : null });
  }
  const manifest = { schema: 'balance_route_operations_index/1', generatedAt: new Date().toISOString(), initialGold: 100, search: { seed: 0, routeCandidateCount: 3, routeCandidates: [1, 2, 3], routeObjective: ['max pathEdges', 'min towerCount', 'min spacing'], operationCandidateCount: 30, operationCandidates: { spacing: [1, 2, 3], sentries: [false, true], familyPatterns: patterns }, operationObjective: ['pass', 'min leaks', 'max remaining HP', 'max route pathEdges', 'min towersBuilt'], guarantee: 'budgeted best among candidates' }, levels: index, outputRoot: rel(OUT) };
  writeJson(path.join(OUT, 'index.json'), manifest);
  const lines = ['# 30 关路线与防御塔操作索引', '', '所有资料按 `initialGold=100` 生成。每关路线枚举 spacing 1/2/3 的合法候选，取路径边数最多且塔位最少者；这是当前候选预算内的最长路线，不保证数学全局最优。通关操作从 30 个确定性策略候选中搜索，并将同一操作序列固定回放到 D01–D08。玩家快速点击塔按钮进入放置预览后点格子建造，也可按住塔按钮拖到棋盘并松手放置；点选已建造塔后从塔旁升级按钮升级。', '', '| 关卡 | 最长路 spacing | 路径边数 | 塔位 | 操作 spacing | 塔型轮换 | D01 操作回放 | 漏怪 | 剩余 HP | 文档 |', '|---|---:|---:|---:|---:|---|---|---:|---:|---|'];
  for (const row of index) lines.push(`| L${pad(row.levelId)} | ${row.spacing} | ${row.pathEdges} | ${row.towerCount} | ${row.operationSpacing} | ${row.operationFamilyPattern.join(',')} | ${row.operationVerdict} | ${row.operationLeaks} | ${row.operationHpMin} | [Markdown](L${pad(row.levelId)}.md) / [JSON](L${pad(row.levelId)}.json) |`);
  lines.push('', '复现：', '', '```powershell', 'Set-Location D:\\FishTestGame', 'node .workbuddy/tools/balance_route_operations.mjs', '```', '', '路线图是离线 staging 产物，Unity 放置与玩家手感仍需单独验收。');
  writeText(path.join(OUT, 'index.md'), lines.join('\n'));
  console.log(JSON.stringify({ output: rel(OUT), levels: index.length, initialGold: 100 }, null, 2));
}

main();
