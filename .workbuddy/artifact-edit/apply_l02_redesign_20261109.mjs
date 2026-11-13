import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const LEVEL = path.join(ROOT, "Luban", "Config", "Datas", "Levels", "L02");
const ARTIFACT = path.join(ROOT, "Artifacts", "L01_ZeroLeak_20261103_1823", "runtime-config.json");
const OUT = path.join(ROOT, ".workbuddy", "artifact-edit", "out-20261109");

const DESIGN = {
  groundOutputRatio: 13178.54 / 14500.54,
  airOutputRatio: 6905.8536585365855 / 6865.721308375875,
  groundPathL01: 41,
  groundPathL02: 70,
  airPathL01: 12,
  airPathL02: 15,
  groundCountRatio: 1.5,
  airCountRatio: 1.25,
  economy: 7335,
  initialGold: 100,
};

// Solve the reward multiplier against the actual mixed target counts
// (ground x1.5, air x1.25), so kill gold plus fixed wave rewards reaches the
// approved 7,335 total economy exactly after rounding.
const targetKillGold = DESIGN.economy - DESIGN.initialGold - 2338;
const l01TargetRewardBase = l01Waves(JSON.parse(await fs.readFile(ARTIFACT, "utf8")))
  .reduce((sum, wave) => sum + wave.enemies.reduce((s, e) => {
    const count = Math.round(e.count * (e.IsFlying ? DESIGN.airCountRatio : DESIGN.groundCountRatio));
    return s + count * e.Reward;
  }, 0), 0);
const REWARD_FACTOR = targetKillGold / l01TargetRewardBase;
const UNIT_REWARD_FACTOR = REWARD_FACTOR;
const ROUND_REWARDS = [
  64, 64, 64, 64,
  151, 77, 77, 77, 77,
  156, 81, 81, 81, 81,
  161, 84, 84, 84, 84,
  167, 88, 88, 88, 88,
  127,
];

function round(value, digits = 6) {
  const p = 10 ** digits;
  return Math.round(value * p) / p;
}

function asRows(sheet) {
  return sheet.getUsedRange().values;
}

function headerMap(rows) {
  return Object.fromEntries(rows[0].map((v, i) => [String(v), i]));
}

async function openBook(file) {
  return SpreadsheetFile.importXlsx(await FileBlob.load(file));
}

function l01Waves(runtime) {
  return runtime.rounds.map((rd) => {
    const enemies = rd.groups.flatMap((g) => g.enemies);
    const ground = enemies.filter((e) => !e.IsFlying);
    const air = enemies.filter((e) => e.IsFlying);
    const vg = ground.reduce((s, e) => s + e.count * e.Speed, 0) / ground.reduce((s, e) => s + e.count, 0);
    const va = air.length ? air.reduce((s, e) => s + e.count * e.Speed, 0) / air.reduce((s, e) => s + e.count, 0) : 1;
    return {
      id: rd.Id,
      interval: rd.groups[0].SpawnIntervalMs,
      enemies,
      ground,
      air,
      vg,
      va,
      totalCount: enemies.reduce((s, e) => s + e.count, 0),
      groundEhp: ground.reduce((s, e) => s + e.count * e.Hp, 0),
      airEhp: air.reduce((s, e) => s + e.count * e.Hp, 0),
    };
  });
}

function resample(sequence, targets) {
  const positions = new Map();
  sequence.forEach((id, i) => {
    if (!positions.has(id)) positions.set(id, []);
    positions.get(id).push(i);
  });
  const emitted = new Map(sequence.map((_, i) => [i, 0]));
  for (const [id, target] of Object.entries(targets)) {
    const pos = positions.get(Number(id));
    if (!pos) throw new Error(`Missing source enemy id ${id} while resampling`);
    const sourceCount = pos.length;
    for (let k = 1; k <= target; k += 1) {
      const occ = Math.min(sourceCount, Math.max(1, Math.ceil((k * sourceCount) / target)));
      const at = pos[occ - 1];
      emitted.set(at, emitted.get(at) + 1);
    }
  }
  const result = [];
  sequence.forEach((id, i) => {
    for (let k = 0; k < emitted.get(i); k += 1) result.push(id);
  });
  return result;
}

function buildSequence(source, targetGround, targetAir, enemyById) {
  const groundTemplate = source.filter((id) => !enemyById.get(id).isFlying);
  const ground = resample(groundTemplate, targetGround);
  const airTotal = Object.values(targetAir).reduce((s, n) => s + n, 0);
  const air = Object.entries(targetAir).flatMap(([id, n]) => Array.from({ length: n }, () => Number(id)));
  if (!airTotal) return ground;
  const total = ground.length + airTotal;
  if (total / airTotal < 2) throw new Error(`Air slots would be adjacent: total=${total}, air=${airTotal}`);
  const slots = new Set(Array.from({ length: airTotal }, (_, k) => Math.floor(((k + 0.5) * total) / airTotal)));
  const result = [];
  let gi = 0;
  let ai = 0;
  for (let p = 0; p < total; p += 1) {
    if (slots.has(p)) result.push(air[ai++]);
    else result.push(ground[gi++]);
  }
  if (result.some((id, i) => i > 0 && enemyById.get(id).isFlying && enemyById.get(result[i - 1]).isFlying)) {
    throw new Error("Air spawn adjacency detected after sequence construction");
  }
  return result;
}

function setCell(sheet, row, col, value, changes, label) {
  const old = sheet.getCell(row, col).values[0][0];
  if (old !== value) {
    sheet.getCell(row, col).values = [[value]];
    changes.push({ label, row: row + 1, col: col + 1, old, new: value });
  }
}

const runtime = JSON.parse(await fs.readFile(ARTIFACT, "utf8"));
const l01 = l01Waves(runtime);

const enemyBook = await openBook(path.join(LEVEL, "EnemyData.xlsx"));
const listBook = await openBook(path.join(LEVEL, "EnemyList.xlsx"));
const roundBook = await openBook(path.join(LEVEL, "RoundData.xlsx"));
const sceneBook = await openBook(path.join(LEVEL, "SceneInfo.xlsx"));

const enemySheet = enemyBook.worksheets.getItemAt(0);
const listSheet = listBook.worksheets.getItemAt(0);
const roundSheet = roundBook.worksheets.getItemAt(0);
const sceneSheet = sceneBook.worksheets.getItemAt(0);
const enemyRows = asRows(enemySheet);
const listRows = asRows(listSheet);
const roundRows = asRows(roundSheet);
const sceneRows = asRows(sceneSheet);
const eh = headerMap(enemyRows);
const lh = headerMap(listRows);
const rh = headerMap(roundRows);
const sh = headerMap(sceneRows);

if (sceneRows[3][sh.initialGold] !== DESIGN.initialGold) {
  throw new Error(`SceneInfo.initialGold must remain 100, got ${sceneRows[3][sh.initialGold]}`);
}

const enemyById = new Map();
for (let r = 3; r < enemyRows.length; r += 1) {
  const id = Number(enemyRows[r][eh.id]);
  if (!Number.isFinite(id)) continue;
  enemyById.set(id, {
    row: r,
    id,
    name: String(enemyRows[r][eh.name]),
    isFlying: Number(enemyRows[r][eh.isFlying] || 0) !== 0,
    hp: Number(enemyRows[r][eh.hp]),
    reward: Number(enemyRows[r][eh.reward]),
    speed: Number(enemyRows[r][eh.speed]),
    armor: Number(enemyRows[r][eh.armor]),
  });
}

const listByRound = new Map();
for (let r = 3; r < listRows.length; r += 1) {
  const id = Number(listRows[r][lh.id]);
  if (!Number.isFinite(id)) continue;
  const ids = String(listRows[r][lh.EnemyIndexs] || "").split(",").filter(Boolean).map(Number);
  listByRound.set(id, { row: r, ids });
}

const changes = { enemyData: [], enemyList: [], roundData: [], sceneInfo: [] };
const waveReports = [];
const intervalFactor = (DESIGN.groundPathL02 / DESIGN.groundPathL01) / DESIGN.groundCountRatio;
const groundOutput = 1437 * DESIGN.groundOutputRatio;
const airOutput = 2997 * DESIGN.airOutputRatio;

for (let i = 0; i < l01.length; i += 1) {
  const base = l01[i];
  const roundId = i < 20 ? 2001 + i : 2401 + (i - 20);
  const list = listByRound.get(roundId);
  if (!list) throw new Error(`Missing EnemyList round ${roundId}`);

  const targetGroundByName = Object.fromEntries(base.ground.map((e) => [e.Name, Math.round(e.count * DESIGN.groundCountRatio)]));
  const targetAirByName = Object.fromEntries(base.air.map((e) => [e.Name, Math.round(e.count * DESIGN.airCountRatio)]));
  const targetGroundIds = {};
  const targetAirIds = {};
  for (const [name, count] of Object.entries(targetGroundByName)) {
    const id = list.ids.find((candidate) => enemyById.get(candidate)?.name === name && !enemyById.get(candidate).isFlying);
    if (!id) throw new Error(`Missing ground id for ${name} in round ${roundId}`);
    targetGroundIds[id] = count;
  }
  for (const [name, count] of Object.entries(targetAirByName)) {
    const id = list.ids.find((candidate) => enemyById.get(candidate)?.name === name && enemyById.get(candidate).isFlying);
    if (!id) throw new Error(`Missing air id for ${name} in round ${roundId}`);
    targetAirIds[id] = count;
  }
  const sequence = buildSequence(list.ids, targetGroundIds, targetAirIds, enemyById);
  const interval = round(base.interval * intervalFactor, 1);
  setCell(listSheet, list.row, lh.EnemyIndexs, sequence.join(","), changes.enemyList, `EnemyList.${roundId}.EnemyIndexs`);
  setCell(listSheet, list.row, lh.enemyInterval, interval, changes.enemyList, `EnemyList.${roundId}.enemyInterval`);

  const groundCount = Object.values(targetGroundIds).reduce((s, n) => s + n, 0);
  const airCount = Object.values(targetAirIds).reduce((s, n) => s + n, 0);
  const totalCount = groundCount + airCount;
  const t1 = base.totalCount * base.interval / 1000 + DESIGN.groundPathL01 / base.vg;
  const t2 = totalCount * interval / 1000 + DESIGN.groundPathL02 / base.vg;
  const lambdaGround = 1437 * t1 / base.groundEhp;
  const targetGroundEhp = groundOutput * t2 / lambdaGround;
  const targetAirEhp = base.airEhp * (airOutput / 2997) * (DESIGN.airPathL02 / DESIGN.airPathL01);
  const baseGroundHp = base.ground.reduce((s, e) => s + (targetGroundByName[e.Name] || 0) * e.Hp, 0);
  const groundMultiplier = targetGroundEhp / baseGroundHp;
  const airPerUnit = airCount ? targetAirEhp / airCount : 0;
  const baseByName = new Map(base.enemies.map((e) => [e.Name, e]));

  for (const id of Object.keys(targetGroundIds).map(Number)) {
    const info = enemyById.get(id);
    const baseUnit = baseByName.get(info.name);
    if (!baseUnit) throw new Error(`Missing L01 base enemy ${info.name} in wave ${i + 1}`);
    const hp = round(baseUnit.Hp * groundMultiplier, 6);
    const reward = round(baseUnit.Reward * UNIT_REWARD_FACTOR, 6);
    setCell(enemySheet, info.row, eh.hp, hp, changes.enemyData, `EnemyData.${id}.hp`);
    setCell(enemySheet, info.row, eh.reward, reward, changes.enemyData, `EnemyData.${id}.reward`);
  }
  for (const id of Object.keys(targetAirIds).map(Number)) {
    const info = enemyById.get(id);
    const baseUnit = baseByName.get(info.name);
    if (!baseUnit) throw new Error(`Missing L01 base air enemy ${info.name} in wave ${i + 1}`);
    const reward = round(baseUnit.Reward * UNIT_REWARD_FACTOR, 6);
    setCell(enemySheet, info.row, eh.hp, round(airPerUnit, 6), changes.enemyData, `EnemyData.${id}.hp`);
    setCell(enemySheet, info.row, eh.reward, reward, changes.enemyData, `EnemyData.${id}.reward`);
  }

  waveReports.push({
    wave: i + 1,
    roundId,
    ground: groundCount,
    air: airCount,
    total: totalCount,
    intervalMs: interval,
    targetGroundEhp: round(targetGroundEhp, 2),
    targetAirEhp: round(targetAirEhp, 2),
    targetEhp: round(targetGroundEhp + targetAirEhp, 2),
    groundMultiplier: round(groundMultiplier, 6),
    airHp: round(airPerUnit, 6),
  });
}

for (let i = 0; i < l01.length; i += 1) {
  const roundId = i < 20 ? 2001 + i : 2401 + (i - 20);
  const row = roundRows.findIndex((values, r) => r >= 3 && Number(values[rh.id]) === roundId);
  if (row < 0) throw new Error(`Missing RoundData row ${roundId}`);
  setCell(roundSheet, row, rh.rewardGold, ROUND_REWARDS[i], changes.roundData, `RoundData.${roundId}.rewardGold`);
}

for (const [name, book] of [["EnemyData", enemyBook], ["EnemyList", listBook], ["RoundData", roundBook], ["SceneInfo", sceneBook]]) {
  await fs.mkdir(OUT, { recursive: true });
  const source = path.join(LEVEL, `${name}.xlsx`);
  const backup = path.join(LEVEL, `${name}.xlsx.bak_20261109_before_redesign`);
  try { await fs.access(backup); } catch { await fs.copyFile(source, backup); }
  book.recalculate();
  const output = await SpreadsheetFile.exportXlsx(book);
  const temp = path.join(OUT, `${name}.xlsx`);
  await output.save(temp);
  await fs.copyFile(temp, source);
}

const manifest = {
  generatedAt: new Date().toISOString(),
  design: { ...DESIGN, intervalFactor: round(intervalFactor, 8), groundOutput, airOutput, rewardFactor: round(REWARD_FACTOR, 8), unitRewardFactor: round(UNIT_REWARD_FACTOR, 8) },
  changed: changes,
  waveReports,
  totals: {
    enemies: waveReports.reduce((s, w) => s + w.total, 0),
    ground: waveReports.reduce((s, w) => s + w.ground, 0),
    air: waveReports.reduce((s, w) => s + w.air, 0),
    targetEhp: round(waveReports.reduce((s, w) => s + w.targetEhp, 0), 2),
    roundReward: ROUND_REWARDS.reduce((s, n) => s + n, 0),
  },
};
await fs.writeFile(path.join(ROOT, "Artifacts", "L02_Redesign_20261109_change_manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
console.log(JSON.stringify({
  totals: manifest.totals,
  changedCells: Object.fromEntries(Object.entries(changes).map(([k, v]) => [k, v.length])),
  firstWaves: waveReports.slice(0, 4),
  lastWave: waveReports.at(-1),
}, null, 2));
