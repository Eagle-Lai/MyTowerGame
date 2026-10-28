// 只读：逐关倒推锚点（F 章，逐关锚定版）。不含仿真，全部为推导量。
//
// 链（每关独立，锚点为本关金币，由本关第 25 波承载）：
//   1. W(L)            墙体塔数（capacity.json, spacing 2, fingersOnly）
//   2. E_max(L)       = W(L) × 平均三级累计价（配比 1:1:1，三族累计价 100/139/130 的均值）
//   3. G(L)           = r × E_max(L)   ← 本关金币锚点（r 为参数，默认 1.25，待确认）
//   4. F(L)           = W(L) × 平均一级建造价（新建段与升级段的折点）
//   5. P(L)           = G(L) × ρ，ρ = 每金 DPS（三族 L3 均值 DPS ÷ 三族平均累计价）
//   6. v̄(L)           本关全部单位速度中位数（格/秒，CellSize=1）
//   7. T_pass(L)      = L_path(L) ÷ v̄(L)，L_path 取 spacing-2 墙体塔布局的路径边数
//   8. π25(L)         = 1 − 2/L_path（F.3 环节 5：末波击杀位置在末 2 格内）
//   9. H25_target(L)  = P(L) × π25 × T_pass（F.2 关系 ΣH = P_eff·π·L_path/v）
//  10. H25_actual(L)  本关第 25 波实测 EHP（monster_stats.json）；比值 actual/target 为偏差
//
// 同时列出现行收入 cur(L) = 开局金 + 全部清场金 + 全部击杀金，以及 G(L)/cur(L)，说明收入机制要改多少。
// 不做的事：不做覆盖率折算、不做溢出折算、不做仿真（这些是 G 章的工作）。
//
// 用法：node .workbuddy/tools/balance_anchor.mjs [--r 1.25] [--out <dir>]
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "../..");
const args = process.argv.slice(2);
const arg = (k, d) => (args.indexOf(k) >= 0 ? args[args.indexOf(k) + 1] : d);
const r = Number(arg("--r", "1.25"));
const outDir = path.resolve(arg("--out", path.join(root, "Docs/Balance_TowerSystem")));
const cfg = (f) => JSON.parse(fs.readFileSync(path.join(root, "Assets/ConfigJson", f), "utf8"));
const cap = JSON.parse(fs.readFileSync(path.join(root, "Docs/Balance_TowerCapacity/capacity.json"), "utf8"));
const mon = JSON.parse(fs.readFileSync(path.join(outDir, "monster_stats.json"), "utf8")).levels;

const scenes = cfg("tbsceneinfo.json").sort((a, b) => a.id - b.id);
const rounds = new Map(cfg("tbrounddata.json").map((x) => [x.id, x]));
const lists = new Map(cfg("tbenemylist.json").map((x) => [x.id, x]));
const enemies = new Map(cfg("tbenemydata.json").map((x) => [x.id, x]));
const towers = cfg("tbtowerinfo.json");

// 三族：累计价与 L3 DPS（配比 1:1:1）
const families = [...new Set(towers.map((t) => t.type))].map((type) => {
  const fam = towers.filter((t) => t.type === type).sort((a, b) => a.level - b.level);
  const cum = fam.reduce((s, t) => s + t.prices, 0);
  const l3 = fam[fam.length - 1];
  const dps = l3.CD > 0 ? l3.power / (l3.CD / 1000) : 0;
  return { name: fam[0].name, type, cum, dps };
});
const avgCum = families.reduce((s, f) => s + f.cum, 0) / families.length;
const avgDps = families.reduce((s, f) => s + f.dps, 0) / families.length;
const rho = avgDps / avgCum;
const L1 = towers.filter((t) => t.level === 1);
const avgL1 = L1.reduce((s, t) => s + t.prices, 0) / L1.length;

const median = (a) => { const s = [...a].sort((x, y) => x - y); return s[Math.floor((s.length - 1) / 2)]; };

const rows = [];
for (const sc of scenes) {
  const L = sc.id;
  const capL = cap.levels.find((x) => x.levelId === L);
  const s2 = capL.bySpacing["2"].fingersOnly;
  const W = s2.towers;
  const Lpath = s2.pathEdges;

  let kill = 0, rnd = 0;
  const speeds = [];
  let spanW25 = 0;
  sc.RoundList.forEach((rid, idx) => {
    const rd = rounds.get(rid);
    rnd += rd.rewardGold;
    for (const lid of rd.EnemyIndexs) {
      const el = lists.get(lid);
      if (idx === 24) spanW25 += (el.EnemyIndexs.length * (el.enemyInterval || 200)) / 1000;
      for (const v of el.EnemyIndexs) {
        const e = enemies.get(v);
        kill += e.reward;
        speeds.push(e.speed);
      }
    }
  });
  const cur = sc.initialGold + rnd + kill;
  const E = W * avgCum;
  const G = r * E;
  const F = W * avgL1;
  const P = G * rho;
  const vbar = median(speeds);
  const Tpass = Lpath / vbar;
  const pi25 = 1 - 2 / Lpath;
  // 两种时间窗：仅转场（F.2 字面关系）与完整时间窗（D.2：首只出生到末只抵达 = 刷怪跨度 + 转场）
  const Twin = spanW25 + Tpass;
  const H25target = P * pi25 * Tpass;
  const H25target_win = P * pi25 * Twin;
  const m = mon.find((x) => x.levelId === L);
  const H25actual = m.waves[24].ehp;
  rows.push({ L, W, Lpath, E_max: Math.round(E), G: Math.round(G), cur: cur, G_over_cur: +(G / cur).toFixed(3),
    F: Math.round(F), G_over_F: +(G / F).toFixed(2), P: +P.toFixed(1), vbar: +vbar.toFixed(3), Tpass: +Tpass.toFixed(1),
    span: +spanW25.toFixed(1), Twin: +Twin.toFixed(1), pi25: +pi25.toFixed(3),
    H25target: Math.round(H25target), H25target_win: Math.round(H25target_win), H25actual: Math.round(H25actual),
    ratio: +(H25actual / H25target).toFixed(3), ratio_win: +(H25actual / H25target_win).toFixed(3) });
}

const ratios = rows.map((x) => x.ratio);
const ratiosWin = rows.map((x) => x.ratio_win);
const sorted = [...ratios].sort((a, b) => a - b);
const sortedWin = [...ratiosWin].sort((a, b) => a - b);

fs.mkdirSync(outDir, { recursive: true });
const md = [];
md.push("# 倒推锚点诊断（逐关锚定，推导量，非仿真）\n");
md.push(`参数：r = ${r}（G(L) = r × E_max(L)，待确认）。配比 1:1:1。`);
md.push(`三族平均累计价 = ${avgCum.toFixed(2)}（${families.map((f) => `${f.name} ${f.cum}`).join(" / ")}）；`
  + `三族 L3 平均 DPS = ${avgDps.toFixed(2)}；每金 DPS ρ = ${rho.toFixed(4)}；平均一级建造价 = ${avgL1.toFixed(2)}。`);
md.push("");
md.push("链：W → E_max = W×累计均价 → G(L) = r×E_max（本关金币，由第 25 波承载）→ F = W×一级均价 → P = G×ρ → π25 = 1−2/L_path → H25 目标 = P×π25×时间窗。");
md.push("时间窗两种：T_pass = L_path/v̄（F.2 字面关系）；T_win = 刷怪跨度 + T_pass（D.2 定义：首只出生到末只抵达）。T_win 为主口径，T_pass 仅作对照。");
md.push("");
md.push("| L | W | L_path | E_max | G(L) | 现行收入 cur | G/cur | F | G/F | P(DPS) | v̄ | 刷怪跨度 s | T_pass s | T_win s | π25 | H25 目标(T_win) | H25 实测 | 实测/目标(T_win) | 实测/目标(T_pass) |");
md.push("|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|");
for (const x of rows) md.push(`| ${x.L} | ${x.W} | ${x.Lpath} | ${x.E_max} | ${x.G} | ${x.cur} | ${x.G_over_cur} | ${x.F} | ${x.G_over_F} | ${x.P} | ${x.vbar} | ${x.span} | ${x.Tpass} | ${x.Twin} | ${x.pi25} | ${x.H25target_win} | ${x.H25actual} | ${x.ratio_win} | ${x.ratio} |`);
md.push("");
md.push(`实测/目标(T_win)：最小 ${sortedWin[0]}，中位 ${median(ratiosWin)}，最大 ${sortedWin[sortedWin.length - 1]}。`);
md.push(`实测/目标(T_pass)：最小 ${sorted[0]}，中位 ${median(ratios)}，最大 ${sorted[sorted.length - 1]}。`);
fs.writeFileSync(path.join(outDir, "anchor_diagnostic.md"), md.join("\n") + "\n");
fs.writeFileSync(path.join(outDir, "anchor_diagnostic.json"), JSON.stringify({ r, avgCum, avgDps, rho, avgL1, rows }, null, 2));
console.log(`r=${r} rho=${rho.toFixed(4)} avgCum=${avgCum} avgDps=${avgDps.toFixed(2)}`);
console.log(rows.map((x) => `L${String(x.L).padStart(2, "0")} W=${x.W} G=${x.G} cur=${x.cur} G/cur=${x.G_over_cur} P=${x.P} Twin=${x.Twin} H25tgt=${x.H25target_win} H25act=${x.H25actual} ratio_win=${x.ratio_win} ratio_pass=${x.ratio}`).join("\n"));
