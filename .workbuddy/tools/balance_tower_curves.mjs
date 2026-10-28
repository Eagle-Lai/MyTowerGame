// 只读：塔数值曲线与 A 章验收（表驱动断言）。
// 默认读取 Assets/ConfigJson/tbtowerinfo.json；可用 --table <json> 指定候选表（同结构数组）。
// 输出派生量（累计投入、卖价复算、每金 DPS、升级/新建效率比 τ）并断言单调性与公式一致性。
// 用法：node .workbuddy/tools/balance_tower_curves.mjs [--table <path>] [--out <dir>]
// 只写 --out（默认 Docs/Balance_TowerSystem），不写 Luban/、Assets/。
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "../..");
const args = process.argv.slice(2);
const arg = (k, d) => (args.indexOf(k) >= 0 ? args[args.indexOf(k) + 1] : d);
const tablePath = path.resolve(arg("--table", path.join(root, "Assets/ConfigJson/tbtowerinfo.json")));
const outDir = path.resolve(arg("--out", path.join(root, "Docs/Balance_TowerSystem")));
const rows = JSON.parse(fs.readFileSync(tablePath, "utf8"));

// 塔族：按 type 分组，按 level 排序；upgradeTo 链须与 level 一致
const families = {};
for (const r of rows) (families[r.type] ||= []).push(r);
for (const k of Object.keys(families)) families[k].sort((a, b) => a.level - b.level);

const failures = [];
const check = (cond, msg) => { if (!cond) failures.push(msg); };
const report = [];

for (const [type, fam] of Object.entries(families)) {
  let cum = 0;
  const name = fam[0].name;
  report.push(`## ${name}（type=${type}）\n`);
  report.push("| 级 | 建造/升级价(增量) | 累计投入 | 卖价(表) | 卖价(公式 floor(0.7×累计)) | 半径 | 伤害 | CD(ms) | DPS(单体) | 减速 | 对空 |");
  report.push("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|");
  fam.forEach((r, i) => {
    cum += r.prices;
    const dps = r.CD > 0 ? (r.power / (r.CD / 1000)) : 0;
    const sellFormula = Math.floor(0.7 * cum);
    check(r.sellPrice === sellFormula, `${name} L${r.level} sellPrice ${r.sellPrice} != floor(0.7*${cum})=${sellFormula}`);
    check(r.upgradeTo === (i + 1 < fam.length ? fam[i + 1].id : 0), `${name} L${r.level} upgradeTo 链断裂`);
    check(r.level === i + 1, `${name} 等级不连续`);
    if (i > 0) {
      const p = fam[i - 1];
      check(r.radius > p.radius, `${name} 半径未递增 L${r.level}`);
      check(r.CD < p.CD, `${name} CD 未递减 L${r.level}`);
      check(r.power >= p.power, `${name} 伤害递减 L${r.level}`);
      if (type === "3") check(r.effectValue > p.effectValue, `${name} 减速强度未递增 L${r.level}`);
    }
    report.push(`| ${r.level} | ${r.prices} | ${cum} | ${r.sellPrice} | ${sellFormula} | ${r.radius} | ${r.power} | ${r.CD} | ${dps.toFixed(2)} | ${type === "3" ? r.effectValue : "—"} | ${r.canAttackAir ? "是" : "否"} |`);
  });
  report.push("");
}

// 升级/新建效率：同族 L1 的每金 DPS 与各级升级的每金 DPS 增量
report.push("## 升级 vs 新建效率（仅火力项，不含路径收益）\n");
report.push("τ = 升级每金产出 ÷ 建造 L1 每金产出（同族）。τ>1 表示铺设优先；τ 不得等于 1。\n");
report.push("| 族 | 段 | 花费 | DPS 增量 | 每金 DPS | τ（相对 L1 新建） |");
report.push("|---|---|---:|---:|---:|---:|");
for (const [type, fam] of Object.entries(families)) {
  if (type === "3") continue; // 减速塔无直接 DPS，效率在报告中单独论述
  const base = fam[0].power / (fam[0].CD / 1000);
  const newPerGold = base / fam[0].prices;
  for (let i = 1; i < fam.length; i++) {
    const prev = fam[i - 1].power / (fam[i - 1].CD / 1000);
    const cur = fam[i].power / (fam[i].CD / 1000);
    const up = fam[i].prices;
    const perGold = (cur - prev) / up;
    report.push(`| ${fam[0].name} | L${i}→L${i + 1} | ${up} | ${(cur - prev).toFixed(2)} | ${perGold.toFixed(3)} | ${(perGold / newPerGold).toFixed(2)} |`);
  }
}

fs.mkdirSync(outDir, { recursive: true });
const tag = path.basename(tablePath, ".json");
fs.writeFileSync(path.join(outDir, `tower_curves_${tag}.md`), `# 塔曲线（${tag}）\n\n${report.join("\n")}\n`);
console.log(`table: ${tablePath}`);
console.log(failures.length ? `FAIL ${failures.length}:\n- ${failures.join("\n- ")}` : "PASS: 单调性、升级链、累计卖价公式全部断言通过");
process.exitCode = failures.length ? 1 : 0;
