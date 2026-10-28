// 只读：金币承载方案 A 的逐关收入计划（推导量，不改任何配置表）。
//
// 方案 A（用户确认）：
//   - 每关整关收入合计 = G(L)（来自 balance_anchor.mjs，G(L) = r × E_max(L)）。
//   - 开局金（initialGold）不参与压缩。
//   - 击杀金与各波清场金（rewardGold）按同一比例 s(L) 调整，使其余收入合计 = G(L) − 开局金。
//     s(L) = (G(L) − initialGold) ÷ (全部击杀金 + 全部清场金)。s < 1 为压缩，s > 1 为放大。
//   - 第 25 波 rewardGold 为「承载值」：吸收整数取整的余量，使整关收入精确等于 G(L)。
//     注意：第 25 波 rewardGold 不等于 G(L)。若字段要直接等于 G(L)，击杀金与前 24 波清场金只能为 0，与方案 A 冲突。
//
// 输出：每关 s(L)、各波调整后的击杀金与清场金、第 25 波承载值、整关合计校验、前期现金流（第 1–5 波结束时的累计收入）。
// 用法：node .workbuddy/tools/balance_income_plan.mjs [--out <dir>]
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "../..");
const args = process.argv.slice(2);
const outDir = path.resolve(args.indexOf("--out") >= 0 ? args[args.indexOf("--out") + 1] : path.join(root, "Docs/Balance_TowerSystem"));
const cfg = (f) => JSON.parse(fs.readFileSync(path.join(root, "Assets/ConfigJson", f), "utf8"));
const anchor = JSON.parse(fs.readFileSync(path.join(outDir, "anchor_diagnostic.json"), "utf8"));

const scenes = cfg("tbsceneinfo.json").sort((a, b) => a.id - b.id);
const rounds = new Map(cfg("tbrounddata.json").map((x) => [x.id, x]));
const lists = new Map(cfg("tbenemylist.json").map((x) => [x.id, x]));
const enemies = new Map(cfg("tbenemydata.json").map((x) => [x.id, x]));

const plan = [];
for (const sc of scenes) {
  const L = sc.id;
  const anc = anchor.rows.find((x) => x.L === L);
  const G = anc.G;
  const I = sc.initialGold;
  // 每波原始击杀金与清场金
  const waves = sc.RoundList.map((rid, idx) => {
    const rd = rounds.get(rid);
    let kill = 0;
    for (const lid of rd.EnemyIndexs) for (const v of lists.get(lid).EnemyIndexs) kill += enemies.get(v).reward;
    return { wave: idx + 1, killRaw: kill, rewardRaw: rd.rewardGold };
  });
  const sumRaw = waves.reduce((s, w) => s + w.killRaw + w.rewardRaw, 0);
  const s = (G - I) / sumRaw;

  // 第 1–24 波：按 s 取整；第 25 波：承载余量
  let acc = 0;
  const out = waves.map((w) => {
    if (w.wave < 25) {
      const k = Math.round(w.killRaw * s);
      const r = Math.round(w.rewardRaw * s);
      acc += k + r;
      return { wave: w.wave, kill: k, reward: r };
    }
    const k25 = Math.round(w.killRaw * s);
    acc += k25;
    return { wave: w.wave, kill: k25, reward: null }; // reward 在下面按余量填
  });
  const carrier = G - I - acc;
  out[24].reward = carrier;
  const total = I + out.reduce((t, w) => t + w.kill + w.reward, 0);

  // 前期现金流：第 1–5 波结束时累计收入（含开局金）
  const cum = [];
  let c = I;
  for (const w of out) { c += w.kill + w.reward; cum.push(c); }

  plan.push({ L, G, initialGold: I, s: +s.toFixed(4), sumRaw, killTotal: out.reduce((t, w) => t + w.kill, 0),
    roundTotal: out.reduce((t, w) => t + w.reward, 0), finalCarrier: carrier, total, check: total === G,
    rawFinal: waves[24].rewardRaw, cumAfterW1: cum[0], cumAfterW5: cum[4], waves: out });
}

fs.mkdirSync(outDir, { recursive: true });
const md = [];
md.push("# 金币承载方案 A：逐关收入计划（推导量，未落表）\n");
md.push("规则：开局金不变；击杀金与清场金按同一比例 s(L) 调整，使其余收入 = G(L) − 开局金；第 25 波 rewardGold 吸收取整余量，使整关收入精确等于 G(L)。");
md.push("注意：第 25 波 rewardGold 是承载余量，不是 G(L) 本身。s > 1 的关是放大而非压缩。\n");
md.push("| L | G(L) | 开局金 | s | 击杀金合计 | 清场金合计(含第25波) | 第25波承载值 | 原第25波清场金 | 整关合计 | 校验 | 第1波后累计 | 第5波后累计 |");
md.push("|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--:|--:|--:|");
for (const p of plan) md.push(`| ${p.L} | ${p.G} | ${p.initialGold} | ${p.s} | ${p.killTotal} | ${p.roundTotal} | ${p.finalCarrier} | ${p.rawFinal} | ${p.total} | ${p.check ? "通过" : "不符"} | ${p.cumAfterW1} | ${p.cumAfterW5} |`);
const ss = plan.map((p) => p.s);
md.push("");
md.push(`s 的范围：最小 ${Math.min(...ss)}（L${plan[ss.indexOf(Math.min(...ss))].L}），最大 ${Math.max(...ss)}（L${plan[ss.indexOf(Math.max(...ss))].L}）。`);
md.push(`s > 1 的关：${plan.filter((p) => p.s > 1).map((p) => "L" + p.L).join("、")}（现行收入低于 G(L)，需放大）。`);
fs.writeFileSync(path.join(outDir, "income_plan_A.md"), md.join("\n") + "\n");
fs.writeFileSync(path.join(outDir, "income_plan_A.json"), JSON.stringify({ rule: "A", plan }, null, 2));

console.log(plan.map((p) => `L${String(p.L).padStart(2, "0")} G=${p.G} s=${p.s} carrier25=${p.finalCarrier} raw25=${p.rawFinal} total=${p.total} ${p.check ? "OK" : "MISMATCH"} cumW5=${p.cumAfterW5}`).join("\n"));
const bad = plan.filter((p) => !p.check || p.finalCarrier < 0);
console.log(bad.length ? `FAIL: ${bad.map((p) => p.L).join(",")}` : "PASS: 30 关整关合计精确等于 G(L)，第 25 波承载值均非负");
process.exitCode = bad.length ? 1 : 0;
