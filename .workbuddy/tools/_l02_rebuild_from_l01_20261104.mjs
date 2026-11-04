import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const levelsRoot = "E:/MyTowerGame/Luban/Config/Datas/Levels";
const temp = "E:/MyTowerGame/.workbuddy/tools/_temp_l02_xlsx";
const files = ["EnemyList.xlsx", "RoundData.xlsx", "EnemyData.xlsx"];
const areaScale = 144 / 91;
const groundHpScale = 71 / 42;
const airHpScale = 15 / 12;
const typeSuffixes = [0, 1, 2, 3, 4, 5];
const waves = [
  { wave: 5, counts: [187, 100, 66, 0, 0, 13], interval: 252, reward: 133, type: 2 },
  { wave: 6, counts: [199, 114, 73, 0, 0, 19], interval: 245, reward: 68, type: 1 },
  { wave: 7, counts: [220, 120, 79, 0, 0, 25], interval: 238, reward: 68, type: 1 },
  { wave: 8, counts: [233, 133, 87, 0, 0, 32], interval: 231, reward: 68, type: 1 },
  { wave: 9, counts: [253, 139, 93, 0, 0, 38], interval: 224, reward: 68, type: 1 },
  { wave: 10, counts: [266, 153, 100, 0, 0, 44], interval: 217, reward: 138, type: 2 },
  { wave: 11, counts: [260, 146, 87, 60, 0, 51], interval: 210, reward: 71, type: 1 },
  { wave: 12, counts: [272, 153, 93, 66, 0, 57], interval: 203, reward: 71, type: 1 },
  { wave: 13, counts: [286, 166, 93, 73, 0, 63], interval: 196, reward: 71, type: 1 },
  { wave: 14, counts: [307, 172, 100, 73, 0, 70], interval: 189, reward: 71, type: 1 },
  { wave: 15, counts: [320, 180, 106, 79, 0, 76], interval: 182, reward: 142, type: 2 },
  { wave: 16, counts: [332, 193, 114, 79, 0, 82], interval: 175, reward: 74, type: 1 },
  { wave: 17, counts: [345, 199, 120, 87, 0, 89], interval: 168, reward: 74, type: 1 },
  { wave: 18, counts: [366, 206, 120, 93, 0, 95], interval: 161, reward: 74, type: 1 },
  { wave: 19, counts: [378, 220, 127, 93, 0, 101], interval: 154, reward: 74, type: 1 },
  { wave: 20, counts: [392, 226, 133, 100, 0, 108], interval: 150.15, reward: 147, type: 2 },
  { wave: 21, counts: [413, 233, 139, 100, 0, 106], interval: 140, reward: 78, type: 1 },
  { wave: 22, counts: [419, 247, 146, 106, 0, 112], interval: 133, reward: 78, type: 1 },
  { wave: 23, counts: [438, 253, 147, 112, 0, 119], interval: 126, reward: 78, type: 1 },
  { wave: 24, counts: [459, 260, 153, 112, 0, 125], interval: 128, reward: 78, type: 1 },
  { wave: 25, counts: [438, 260, 160, 139, 21, 131], interval: 236.5, reward: 112, type: 2 },
];

async function importWorkbook(level, file) {
  return await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(levelsRoot, level, file)));
}

function usedValues(workbook, sheetIndex = 0) {
  const sheet = workbook.worksheets.getItemAt(sheetIndex);
  return { sheet, values: sheet.getUsedRange().values };
}

function rowIndexById(values, id) {
  const index = values.findIndex(row => Number(row?.[1]) === id);
  assert.notEqual(index, -1, `Missing row id ${id}`);
  return index;
}

function waveTableId(level, wave) {
  if (wave <= 20) return (level === "L01" ? 0 : 2000) + wave;
  return (level === "L01" ? 400 : 2400) + wave - 20;
}

function countsFromSequence(value) {
  const counts = new Map();
  for (const id of String(value).split(",").map(Number)) {
    const suffix = id % 10;
    counts.set(suffix, (counts.get(suffix) ?? 0) + 1);
  }
  return counts;
}

function expandedSequence(sourceValue, targetCounts, wave) {
  const sourceIds = String(sourceValue).split(",").map(Number);
  const sourceSuffixes = sourceIds.map(id => id % 10);
  const total = targetCounts.reduce((sum, count) => sum + count, 0);
  const sequence = Array.from({ length: total }, (_, index) => sourceSuffixes[Math.floor(index * sourceSuffixes.length / total)]);
  const actual = new Map(typeSuffixes.map(type => [type, 0]));
  for (const type of sequence) actual.set(type, (actual.get(type) ?? 0) + 1);

  const surplusPositions = [];
  const deficitTypes = [];
  for (let typeIndex = 0; typeIndex < typeSuffixes.length; typeIndex++) {
    const type = typeSuffixes[typeIndex];
    const target = targetCounts[typeIndex];
    const current = actual.get(type) ?? 0;
    if (current > target) {
      const positions = sequence.map((value, index) => value === type ? index : -1).filter(index => index >= 0);
      const surplus = current - target;
      for (let i = 0; i < surplus; i++) surplusPositions.push(positions[Math.floor((i + 0.5) * positions.length / surplus)]);
    } else {
      for (let i = 0; i < target - current; i++) deficitTypes.push(type);
    }
  }
  assert.equal(surplusPositions.length, deficitTypes.length, `Unbalanced sampled sequence for W${wave}`);
  for (let i = 0; i < surplusPositions.length; i++) sequence[surplusPositions[i]] = deficitTypes[i];
  const finalCounts = new Map(typeSuffixes.map(type => [type, 0]));
  for (const type of sequence) finalCounts.set(type, (finalCounts.get(type) ?? 0) + 1);
  assert.deepEqual(typeSuffixes.map(type => finalCounts.get(type)), targetCounts, `Composition mismatch for W${wave}`);
  return sequence.map(type => 6000000 + (wave - 1) * 10 + type).join(",");
}

function assertValuesPreservedExcept(before, after, allowedCells, label) {
  assert.equal(after.length, before.length, `${label}: row count changed`);
  let changed = 0;
  for (let row = 0; row < before.length; row++) {
    assert.equal(after[row]?.length ?? 0, before[row]?.length ?? 0, `${label}: column count changed at row ${row + 1}`);
    for (let col = 0; col < (before[row]?.length ?? 0); col++) {
      const a = before[row][col];
      const b = after[row][col];
      const same = a == null && b == null || Object.is(a, b) || typeof a === "number" && typeof b === "number" && Math.abs(a - b) < 1e-9;
      if (!same && !allowedCells.has(`${row},${col}`)) throw new Error(`${label}: unexpected value change at row ${row + 1}, column ${col + 1}: ${JSON.stringify(a)} -> ${JSON.stringify(b)}`);
      if (!same) changed++;
    }
  }
  return changed;
}

function allowedCells(rows, columns) {
  return new Set(rows.flatMap(row => columns.map(column => `${row},${column}`)));
}

function setCell(sheet, rowIndex, colIndex, value) {
  sheet.getRangeByIndexes(rowIndex, colIndex, 1, 1).values = [[value]];
}

function roundTo(value, places) {
  const scale = 10 ** places;
  return Math.round((value + Number.EPSILON) * scale) / scale;
}

async function loadPlan() {
  const [l1EnemyList, l1RoundData, l1EnemyData, l2EnemyList, l2RoundData, l2EnemyData, l2SceneInfo] = await Promise.all([
    importWorkbook("L01", "EnemyList.xlsx"), importWorkbook("L01", "RoundData.xlsx"), importWorkbook("L01", "EnemyData.xlsx"),
    importWorkbook("L02", "EnemyList.xlsx"), importWorkbook("L02", "RoundData.xlsx"), importWorkbook("L02", "EnemyData.xlsx"), importWorkbook("L02", "SceneInfo.xlsx"),
  ]);
  const l1Lists = usedValues(l1EnemyList).values;
  const l1Rounds = usedValues(l1RoundData).values;
  const l1Enemies = usedValues(l1EnemyData).values;
  const l2Lists = usedValues(l2EnemyList).values;
  const l2Rounds = usedValues(l2RoundData).values;
  const l2Enemies = usedValues(l2EnemyData).values;
  const sceneValues = usedValues(l2SceneInfo).values;
  const enemyById = values => new Map(values.filter(row => Number.isFinite(Number(row?.[1]))).map(row => [Number(row[1]), row]));
  const l1EnemyMap = enemyById(l1Enemies);
  const l2EnemyMap = enemyById(l2Enemies);
  const result = [];
  const nonHpMismatches = [];
  const copiedColumns = [[2, "speed"], [4, "name"], [5, "type"], [6, "enemyInterval"], [7, "resName"], [8, "armor"], [9, "killGold"], [10, "damageToPlayer"], [11, "scale"], [12, "bodyRadius"], [13, "isFlying"], [14, "animController"]];

  const scene = sceneValues.find(row => Number(row?.[1]) === 2);
  assert(scene, "L02 SceneInfo row id=2 is missing");
  assert.equal(Number(scene[11]), 100, "L02 initial gold must remain 100");

  for (const target of waves) {
    const l1List = l1Lists[rowIndexById(l1Lists, waveTableId("L01", target.wave))];
    const l2ListIndex = rowIndexById(l2Lists, waveTableId("L02", target.wave));
    const baseCounts = countsFromSequence(l1List[2]);
    const scaledCounts = typeSuffixes.map(type => Math.round((baseCounts.get(type) ?? 0) * areaScale));
    assert.deepEqual(scaledCounts, target.counts, `Approved count table no longer matches L01 area scaling at W${target.wave}`);
    assert.equal(Number(l1List[4]), target.interval, `L01 interval changed from approved value at W${target.wave}`);

    const l1Round = l1Rounds[rowIndexById(l1Rounds, waveTableId("L01", target.wave))];
    const l2RoundIndex = rowIndexById(l2Rounds, waveTableId("L02", target.wave));
    const scaledReward = Math.round(Number(l1Round[5]) * areaScale);
    assert.equal(scaledReward, target.reward, `Clear reward no longer matches approved scale at W${target.wave}`);
    assert.equal(Number(l1Round[6]), target.type, `Wave type differs from the approved L01 pattern at W${target.wave}`);

    const hpRows = [];
    for (let typeIndex = 0; typeIndex < typeSuffixes.length; typeIndex++) {
      if (target.counts[typeIndex] === 0) continue;
      const suffix = typeSuffixes[typeIndex];
      const sourceId = 5000000 + (target.wave - 1) * 10 + suffix;
      const targetId = 6000000 + (target.wave - 1) * 10 + suffix;
      const source = l1EnemyMap.get(sourceId);
      const current = l2EnemyMap.get(targetId);
      assert(source && current, `Missing EnemyData id ${sourceId} or ${targetId}`);
      const hpScale = Number(source[13]) === 1 ? airHpScale : groundHpScale;
      const hp = roundTo(Number(source[3]) * hpScale, 2);
      hpRows.push({ suffix, id: targetId, hp, baseHp: Number(source[3]), scale: hpScale, killGold: Number(source[9]) });
      for (const [column, name] of copiedColumns) {
        const a = source[column];
        const b = current[column];
        const same = typeof a === "number" && typeof b === "number" ? Math.abs(a - b) < 1e-9 : a === b;
        if (!same) nonHpMismatches.push({ wave: target.wave, id: targetId, field: name, l01: a, l02: b });
      }
    }
    result.push({ wave: target.wave, total: target.counts.reduce((a, b) => a + b, 0), counts: target.counts, interval: target.interval, clearGold: target.reward, waveType: target.type, hpRows, currentEnemyRow: l2ListIndex + 1, currentRoundRow: l2RoundIndex + 1, currentEnemyIds: countsFromSequence(l2Lists[l2ListIndex][2]) });
  }
  return { l2EnemyList, l2RoundData, l2EnemyData, l1Lists, l1Enemies, l2Lists, l2Rounds, l2Enemies, plan: result, nonHpMismatches };
}

async function inspect() {
  for (const file of files) {
    const workbook = await importWorkbook("L02", file);
    const sheetInfo = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 1500 });
    console.log(JSON.stringify({ file, sheets: sheetInfo.ndjson }));
    for (let i = 0; i < workbook.worksheets.items.length; i++) {
      const sheet = workbook.worksheets.getItemAt(i);
      const used = sheet.getUsedRange();
      const values = used?.values ?? [];
      console.log(JSON.stringify({ file, sheet: sheet.name, rows: values.length, columns: values[0]?.length ?? 0, preview: values.slice(0, 6).map(row => row.slice(0, Math.min(row.length, 8))) }));
      if (i === 0) {
        const address = file === "EnemyList.xlsx" ? "A1:F8" : file === "RoundData.xlsx" ? "A1:G10" : "A1:Q12";
        const preview = await workbook.render({ sheetName: sheet.name, range: address, scale: 1, format: "png" });
        await fs.mkdir(temp, { recursive: true });
        await fs.writeFile(path.join(temp, file.replace(".xlsx", ".png")), new Uint8Array(await preview.arrayBuffer()));
      }
    }
  }
}

async function plan() {
  const data = await loadPlan();
  const l2EnemyMap = new Map(data.l2Enemies.filter(row => Number.isFinite(Number(row?.[1]))).map(row => [Number(row[1]), row]));
  for (const target of waves) {
    const listRow = data.l2Lists[rowIndexById(data.l2Lists, waveTableId("L02", target.wave))];
    assert.deepEqual(typeSuffixes.map(type => countsFromSequence(listRow[2]).get(type) ?? 0), target.counts, `L02 EnemyList mismatch at W${target.wave}`);
    assert.equal(Number(listRow[4]), target.interval, `L02 EnemyList interval mismatch at W${target.wave}`);
    const roundRow = data.l2Rounds[rowIndexById(data.l2Rounds, waveTableId("L02", target.wave))];
    assert.equal(Number(roundRow[5]), target.reward, `L02 clear reward mismatch at W${target.wave}`);
    assert.equal(Number(roundRow[6]), target.type, `L02 wave type mismatch at W${target.wave}`);
    for (let i = 0; i < typeSuffixes.length; i++) if (target.counts[i] > 0) {
      const id = 6000000 + (target.wave - 1) * 10 + typeSuffixes[i];
      const actual = l2EnemyMap.get(id);
      const source = data.plan.find(wave => wave.wave === target.wave).hpRows.find(enemy => enemy.suffix === typeSuffixes[i]);
      assert(actual && source, `L02 EnemyData row missing at W${target.wave}, suffix ${typeSuffixes[i]}`);
      assert.equal(Number(actual[3]), source.hp, `L02 EnemyData HP mismatch for id ${id}`);
    }
  }
  const totalEnemies = data.plan.reduce((sum, wave) => sum + wave.total, 0);
  const clearGold = data.plan.reduce((sum, wave) => sum + wave.clearGold, 0);
  const killGold = data.plan.reduce((sum, wave) => sum + wave.hpRows.reduce((waveSum, enemy) => waveSum + wave.counts[enemy.suffix] * enemy.killGold, 0), 0);
  console.log(JSON.stringify({ validatedWaves: "W5-W25", totalEnemiesW05W25: totalEnemies, clearGoldW05W25: clearGold, killGoldW05W25: roundTo(killGold, 2), enemyDataRows: data.plan.reduce((sum, wave) => sum + wave.hpRows.length, 0), initialGold: 100, nonHpMismatches: data.nonHpMismatches.length, intervals: data.plan.map(wave => wave.interval), waveCounts: data.plan.map(wave => wave.total) }, null, 2));
}

async function apply() {
  const data = await loadPlan();
  assert.deepEqual(data.nonHpMismatches, [], "L02 non-HP EnemyData fields differ from the approved L01 carry-over values; stop for review");
  const listOriginal = JSON.parse(JSON.stringify(data.l2EnemyList.worksheets.getItemAt(0).getUsedRange().values));
  const roundOriginal = JSON.parse(JSON.stringify(data.l2RoundData.worksheets.getItemAt(0).getUsedRange().values));
  const enemyOriginal = JSON.parse(JSON.stringify(data.l2EnemyData.worksheets.getItemAt(0).getUsedRange().values));
  const listSheet = data.l2EnemyList.worksheets.getItemAt(0);
  const roundSheet = data.l2RoundData.worksheets.getItemAt(0);
  const enemySheet = data.l2EnemyData.worksheets.getItemAt(0);
  const enemyRows = usedValues(data.l2EnemyData).values;
  const enemyIds = new Map(enemyRows.map((row, index) => [Number(row?.[1]), index]));

  for (const target of waves) {
    const rowIndex = rowIndexById(usedValues(data.l2EnemyList).values, waveTableId("L02", target.wave));
    const sourceList = data.l1Lists[rowIndexById(data.l1Lists, waveTableId("L01", target.wave))][2];
    setCell(listSheet, rowIndex, 2, expandedSequence(sourceList, target.counts, target.wave));
    setCell(listSheet, rowIndex, 4, target.interval);

    const roundIndex = rowIndexById(usedValues(data.l2RoundData).values, waveTableId("L02", target.wave));
    setCell(roundSheet, roundIndex, 5, target.reward);
    setCell(roundSheet, roundIndex, 6, target.type);

    const l1EnemyMap = new Map(data.l1Enemies.filter(row => Number.isFinite(Number(row?.[1]))).map(row => [Number(row[1]), row]));
    for (let typeIndex = 0; typeIndex < typeSuffixes.length; typeIndex++) {
      if (target.counts[typeIndex] === 0) continue;
      const suffix = typeSuffixes[typeIndex];
      const sourceId = 5000000 + (target.wave - 1) * 10 + suffix;
      const targetId = 6000000 + (target.wave - 1) * 10 + suffix;
      const source = l1EnemyMap.get(sourceId);
      const targetIndex = enemyIds.get(targetId);
      assert(source && targetIndex != null, `Missing EnemyData id ${sourceId} or ${targetId}`);
      const hpScale = Number(source[13]) === 1 ? airHpScale : groundHpScale;
      setCell(enemySheet, targetIndex, 3, roundTo(Number(source[3]) * hpScale, 2));
    }
  }

  for (const workbook of [data.l2EnemyList, data.l2RoundData, data.l2EnemyData]) workbook.recalculate();
  await fs.rm(temp, { recursive: true, force: true });
  await fs.mkdir(temp, { recursive: true });
  const listRows = waves.map(target => rowIndexById(usedValues(data.l2EnemyList).values, waveTableId("L02", target.wave)));
  const roundRows = waves.map(target => rowIndexById(usedValues(data.l2RoundData).values, waveTableId("L02", target.wave)));
  const allowedByFile = new Map([
    ["EnemyList.xlsx", allowedCells(listRows, [2, 4])],
    ["RoundData.xlsx", allowedCells(roundRows, [5, 6])],
  ]);
  const enemyRowsAllowed = [];
  for (const target of waves) for (let i = 0; i < typeSuffixes.length; i++) if (target.counts[i] > 0) {
    enemyRowsAllowed.push(enemyIds.get(6000000 + (target.wave - 1) * 10 + typeSuffixes[i]));
  }
  allowedByFile.set("EnemyData.xlsx", allowedCells(enemyRowsAllowed, [3]));
  const workbooks = new Map([["EnemyList.xlsx", data.l2EnemyList], ["RoundData.xlsx", data.l2RoundData], ["EnemyData.xlsx", data.l2EnemyData]]);
  const originals = new Map([["EnemyList.xlsx", listOriginal], ["RoundData.xlsx", roundOriginal], ["EnemyData.xlsx", enemyOriginal]]);

  for (const file of files) {
    const output = await SpreadsheetFile.exportXlsx(workbooks.get(file));
    await output.save(path.join(temp, file));
    const check = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(temp, file)));
    const checkValues = check.worksheets.getItemAt(0).getUsedRange().values;
    const changed = assertValuesPreservedExcept(originals.get(file), checkValues, allowedByFile.get(file), file);
    console.log(JSON.stringify({ staged: file, changedTargetCells: changed, rows: checkValues.length, columns: checkValues[0]?.length ?? 0 }));
  }

  for (const file of files) await fs.copyFile(path.join(temp, file), path.join(levelsRoot, "L02", file));
  console.log(JSON.stringify({ committed: files, enemyCountW05W25: data.plan.reduce((sum, wave) => sum + wave.total, 0) }));
}

const mode = process.argv[2] ?? "inspect";
if (mode === "inspect") await inspect();
else if (mode === "plan") await plan();
else if (mode === "apply") await apply();
else throw new Error(`Unknown mode: ${mode}`);
