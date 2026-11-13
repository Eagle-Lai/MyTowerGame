import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const LEVEL = path.join(ROOT, "Luban", "Config", "Datas", "Levels", "L02");
const OUT = path.join(ROOT, ".workbuddy", "artifact-edit", "out-20261109-strengthen");
const L01_RUNTIME = path.join(ROOT, "Artifacts", "L01_ZeroLeak_20261103_1823", "runtime-config.json");
const L01_METRICS = path.join(ROOT, "Artifacts", "L01_ZeroLeak_20261103_1823", "final-metrics.json");
const JSON_DIR = path.join(ROOT, "Assets", "ConfigJson");
const MANIFEST = path.join(ROOT, "Artifacts", "L02_Strengthen_20261109_change_manifest.json");
const REVIEW_JSON = path.join(ROOT, "Artifacts", "L02_Strengthen_20261109_review.json");
const REVIEW_CSV = path.join(ROOT, "Artifacts", "L02_Strengthen_20261109_review.csv");
const DRY_RUN = process.argv.includes("--dry-run");

const GROUND_PATH_L01 = 41;
const GROUND_PATH_L02 = 70;
const AIR_PATH_L01 = 12;
const AIR_PATH_L02 = 15;
const GROUND_COUNT_RATIO = 1.5;
const AIR_COUNT_RATIO = 1.25;
const INITIAL_GOLD = 100;
const TARGET_FINAL_COST_L01 = 3919;
const TARGET_FINAL_COST_L02 = 7116;
const TARGET_FINAL_GROUND_DPS_L01 = 1437;
const TARGET_FINAL_GROUND_DPS_L02 = 2603;
const TARGET_FINAL_AIR_DPS_L01 = 2997;
const TARGET_FINAL_AIR_DPS_L02 = 3520;

function round(v, digits = 6) {
  const p = 10 ** digits;
  return Math.round(v * p) / p;
}

function rowsOf(sheet) {
  return sheet.getUsedRange().values;
}

function headers(rows) {
  return Object.fromEntries(rows[0].map((v, i) => [String(v), i]));
}

async function openBook(file) {
  return SpreadsheetFile.importXlsx(await FileBlob.load(file));
}

function l01Waves(runtime) {
  return runtime.rounds.map((roundData) => {
    const enemies = roundData.groups.flatMap((g) => g.enemies);
    const ground = enemies.filter((e) => !e.IsFlying);
    const air = enemies.filter((e) => e.IsFlying);
    const groundCount = ground.reduce((s, e) => s + e.count, 0);
    const airCount = air.reduce((s, e) => s + e.count, 0);
    const vg = groundCount
      ? ground.reduce((s, e) => s + e.count * e.Speed, 0) / groundCount
      : 1;
    const va = airCount
      ? air.reduce((s, e) => s + e.count * e.Speed, 0) / airCount
      : 1;
    return {
      id: roundData.Id,
      interval: Number(roundData.groups[0].SpawnIntervalMs),
      enemies,
      ground,
      air,
      groundCount,
      airCount,
      totalCount: enemies.reduce((s, e) => s + e.count, 0),
      groundEhp: ground.reduce((s, e) => s + e.count * e.Hp, 0),
      airEhp: air.reduce((s, e) => s + e.count * e.Hp, 0),
      vg,
      va,
    };
  });
}

function csvLine(values) {
  return values.map((v) => {
    const s = String(v ?? "");
    return /[",\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
  }).join(",");
}

const runtime = JSON.parse(await fs.readFile(L01_RUNTIME, "utf8"));
const l01Metrics = JSON.parse(await fs.readFile(L01_METRICS, "utf8"));
const l01 = l01Waves(runtime);
const currentEnemyData = JSON.parse(await fs.readFile(path.join(JSON_DIR, "tbenemydata.json"), "utf8"));
const currentEnemyList = JSON.parse(await fs.readFile(path.join(JSON_DIR, "tbenemylist.json"), "utf8"));
const currentRoundData = JSON.parse(await fs.readFile(path.join(JSON_DIR, "tbrounddata.json"), "utf8"));
const enemyById = new Map(currentEnemyData.map((e) => [Number(e.id), e]));
const listByRound = new Map(currentEnemyList.filter((e) => e.id >= 2001 && e.id <= 2025 || e.id >= 2401 && e.id <= 2405).map((e) => [Number(e.id), e]));
const roundById = new Map(currentRoundData.map((e) => [Number(e.id), e]));

// Reconstruct the economy that is available at each wave start. This includes
// all previous kill gold and clear rewards, so remaining unspent gold is part
// of the modeled defense budget. W5 therefore includes the screenshot's
// approximately 196 remaining gold: 897.9 total available - 701.9 spent.
let l01Economy = INITIAL_GOLD;
let l02Economy = INITIAL_GOLD;
const economyAtStart = [];
for (let i = 0; i < 25; i += 1) {
  economyAtStart.push({ l01: l01Economy, l02: l02Economy });
  const l01Wave = l01Metrics.waves[i];
  l01Economy += Number(l01Wave.killGold || 0) + Number(l01Wave.clearGold || 0);
  const roundId = i < 20 ? 2001 + i : 2401 + (i - 20);
  const list = listByRound.get(roundId);
  const roundData = roundById.get(roundId);
  const killGold = list.EnemyIndexs.reduce((s, id) => s + Number(enemyById.get(Number(id)).reward), 0);
  l02Economy += killGold + Number(roundData.rewardGold || 0);
}

const enemyBook = await openBook(path.join(LEVEL, "EnemyData.xlsx"));
const listBook = await openBook(path.join(LEVEL, "EnemyList.xlsx"));
const enemySheet = enemyBook.worksheets.getItemAt(0);
const listSheet = listBook.worksheets.getItemAt(0);
const enemyRows = rowsOf(enemySheet);
const listRows = rowsOf(listSheet);
const eh = headers(enemyRows);
const lh = headers(listRows);

const enemyRowsById = new Map();
for (let r = 3; r < enemyRows.length; r += 1) {
  const id = Number(enemyRows[r][eh.id]);
  if (Number.isFinite(id)) enemyRowsById.set(id, { row: r, values: enemyRows[r] });
}
const listRowsById = new Map();
for (let r = 3; r < listRows.length; r += 1) {
  const id = Number(listRows[r][lh.id]);
  if (Number.isFinite(id)) listRowsById.set(id, { row: r, values: listRows[r] });
}

const changed = [];
const waveReports = [];
const modifiedIds = new Set();

for (let i = 4; i < 25; i += 1) {
  const l01Wave = l01[i];
  const roundId = i < 20 ? 2001 + i : 2401 + (i - 20);
  const list = listByRound.get(roundId);
  const listSource = listRowsById.get(roundId);
  if (!list || !listSource) throw new Error(`Missing L02 EnemyList round ${roundId}`);

  const ids = [...new Set(list.EnemyIndexs.map(Number))];
  const l02Enemies = list.EnemyIndexs.map((id) => enemyById.get(Number(id)));
  const ground = l02Enemies.filter((e) => !e.isFlying);
  const air = l02Enemies.filter((e) => e.isFlying);
  const groundCount = ground.length;
  const airCount = air.length;
  const vg2 = groundCount ? ground.reduce((s, e) => s + Number(e.speed), 0) / groundCount : 1;
  const va2 = airCount ? air.reduce((s, e) => s + Number(e.speed), 0) / airCount : 1;
  const totalCount = groundCount + airCount;
  const spawnTime1 = l01Wave.totalCount * l01Wave.interval / 1000;
  const spawnTime2 = totalCount * Number(list.enemyInterval) / 1000;
  const t1Ground = spawnTime1 + GROUND_PATH_L01 / l01Wave.vg;
  const t2Ground = spawnTime2 + GROUND_PATH_L02 / vg2;
  const t1Air = spawnTime1 + AIR_PATH_L01 / l01Wave.va;
  const t2Air = spawnTime2 + AIR_PATH_L02 / va2;
  const economicRatio = economyAtStart[i].l02 / economyAtStart[i].l01;

  // The final layouts have nearly equal effective DPS per invested gold after
  // slow exposure is counted. Keeping the ratios explicit makes the economy
  // conversion auditable and prevents the final 64-tower layout from being
  // incorrectly treated as active during W5.
  const groundDpsPerGoldRatio = (TARGET_FINAL_GROUND_DPS_L02 / TARGET_FINAL_COST_L02)
    / (TARGET_FINAL_GROUND_DPS_L01 / TARGET_FINAL_COST_L01);
  const airDpsPerGoldRatio = (TARGET_FINAL_AIR_DPS_L02 / TARGET_FINAL_COST_L02)
    / (TARGET_FINAL_AIR_DPS_L01 / TARGET_FINAL_COST_L01);
  const groundTargetEhp = l01Wave.groundEhp * economicRatio * groundDpsPerGoldRatio * (t2Ground / t1Ground);
  const airTargetEhp = l01Wave.airEhp * economicRatio * airDpsPerGoldRatio * (t2Air / t1Air);

  const l01GroundByName = new Map(l01Wave.ground.map((e) => [e.Name, e]));
  const l01AirByName = new Map(l01Wave.air.map((e) => [e.Name, e]));
  let baseGroundEhp = 0;
  let baseAirEhp = 0;
  const targetById = new Map();
  for (const id of ids) {
    const source = enemyById.get(id);
    const base = source.isFlying ? l01AirByName.get(source.name) : l01GroundByName.get(source.name);
    if (!base) throw new Error(`Missing L01 ${source.isFlying ? "air" : "ground"} type ${source.name} in W${i + 1}`);
    const count = list.EnemyIndexs.filter((candidate) => Number(candidate) === id).length;
    if (source.isFlying) baseAirEhp += count * base.Hp;
    else baseGroundEhp += count * base.Hp;
  }
  const groundMultiplier = groundCount ? groundTargetEhp / baseGroundEhp : 1;
  const airMultiplier = airCount ? airTargetEhp / baseAirEhp : 1;

  for (const id of ids) {
    const source = enemyById.get(id);
    const base = source.isFlying ? l01AirByName.get(source.name) : l01GroundByName.get(source.name);
    const multiplier = source.isFlying ? airMultiplier : groundMultiplier;
    const newHp = round(Number(base.Hp) * multiplier, 6);
    const sourceRow = enemyRowsById.get(id);
    if (!sourceRow) throw new Error(`Missing EnemyData source row ${id}`);
    const oldHp = Number(sourceRow.values[eh.hp]);
    if (!Number.isFinite(oldHp)) throw new Error(`EnemyData.${id}.hp is not numeric: ${sourceRow.values[eh.hp]}`);
    if (oldHp !== newHp && !DRY_RUN) enemySheet.getCell(sourceRow.row, eh.hp).values = [[newHp]];
    if (oldHp !== newHp) {
      changed.push({ id, wave: i + 1, roundId, field: "hp", old: oldHp, new: newHp, flying: source.isFlying ? 1 : 0 });
      modifiedIds.add(id);
    }
  }

  waveReports.push({
    wave: i + 1,
    roundId,
    groundCount,
    airCount,
    l01EconomyAtStart: round(economyAtStart[i].l01, 3),
    l02EconomyAtStart: round(economyAtStart[i].l02, 3),
    screenshotW5RemainingGold: i === 4 ? 196 : null,
    economicRatio: round(economicRatio, 6),
    groundTimeRatio: round(t2Ground / t1Ground, 6),
    airTimeRatio: round(t2Air / t1Air, 6),
    targetGroundEhp: round(groundTargetEhp, 2),
    targetAirEhp: round(airTargetEhp, 2),
    groundHpMultiplier: round(groundMultiplier, 6),
    airHpMultiplier: round(airMultiplier, 6),
    currentGroundEhp: round(ground.reduce((s, e) => s + Number(e.hp), 0), 2),
    currentAirEhp: round(air.reduce((s, e) => s + Number(e.hp), 0), 2),
    intervalMs: Number(list.enemyInterval),
  });
}

if (!DRY_RUN) {
  await fs.mkdir(OUT, { recursive: true });
  const source = path.join(LEVEL, "EnemyData.xlsx");
  const backup = path.join(LEVEL, "EnemyData.xlsx.bak_20261109_before_strengthen");
  try { await fs.access(backup); } catch { await fs.copyFile(source, backup); }
  enemyBook.recalculate();
  const output = await SpreadsheetFile.exportXlsx(enemyBook);
  const temp = path.join(OUT, "EnemyData.xlsx");
  await output.save(temp);
  await fs.copyFile(temp, source);
}

const manifest = {
  generatedAt: new Date().toISOString(),
  mode: DRY_RUN ? "dry-run" : "write",
  scope: "L02 EnemyData.xlsx W5-W25 hp only",
  assumptions: {
    initialGold: INITIAL_GOLD,
    groundPathL01: GROUND_PATH_L01,
    groundPathL02: GROUND_PATH_L02,
    airPathL01: AIR_PATH_L01,
    airPathL02: AIR_PATH_L02,
    groundCountRatio: GROUND_COUNT_RATIO,
    airCountRatio: AIR_COUNT_RATIO,
    targetFinalCostL01: TARGET_FINAL_COST_L01,
    targetFinalCostL02: TARGET_FINAL_COST_L02,
    targetFinalGroundDpsL01: TARGET_FINAL_GROUND_DPS_L01,
    targetFinalGroundDpsL02: TARGET_FINAL_GROUND_DPS_L02,
    targetFinalAirDpsL01: TARGET_FINAL_AIR_DPS_L01,
    targetFinalAirDpsL02: TARGET_FINAL_AIR_DPS_L02,
    economyConversion: "D_eff = finalDps / finalCost * (built spend + remaining gold); the ratio is applied to L01 measured wave EHP.",
  },
  changedCells: changed,
  waveReports,
  totals: {
    waves: waveReports.length,
    changedRows: modifiedIds.size,
    oldTargetEhp: round(waveReports.reduce((s, w) => s + w.currentGroundEhp + w.currentAirEhp, 0), 2),
    newTargetEhp: round(waveReports.reduce((s, w) => s + w.targetGroundEhp + w.targetAirEhp, 0), 2),
  },
};

await fs.writeFile(MANIFEST, JSON.stringify(manifest, null, 2), "utf8");
await fs.writeFile(REVIEW_JSON, JSON.stringify({ assumptions: manifest.assumptions, waveReports }, null, 2), "utf8");
const columns = ["wave", "roundId", "groundCount", "airCount", "l01EconomyAtStart", "l02EconomyAtStart", "economicRatio", "groundTimeRatio", "airTimeRatio", "groundHpMultiplier", "airHpMultiplier", "currentGroundEhp", "currentAirEhp", "targetGroundEhp", "targetAirEhp", "intervalMs"];
await fs.writeFile(REVIEW_CSV, [columns.join(","), ...waveReports.map((w) => csvLine(columns.map((c) => w[c])))].join("\n") + "\n", "utf8");
console.log(JSON.stringify({ mode: manifest.mode, changedRows: modifiedIds.size, changedCells: changed.length, waveReports }, null, 2));
