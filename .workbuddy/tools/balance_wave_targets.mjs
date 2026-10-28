// 只读：逐波倒推目标 EHP（F 章，逐波版）。推导量，不含仿真。
//
// 每关每波 w：
//   c_{w-1}  = 波 w 开始前已累计收入 ÷ G(L)           （来自 income_plan_A.json，开局金计入）
//   P(L)     = 整关满建满级的 DPS 预算（anchor_diagnostic.json）
//   π_w      = π25 × (A0 + (1 − A0) × (w−1)/24)        单调上升，末波 = π25，首波 = A0 × π25（A0 默认 0.6）
//   T_win_w  = 本波刷怪跨度 + 转场时间 L_path/v̄         （D.2 时间窗）
//   H_w      = P(L) × c_{w-1} × π_w × T_win_w           本波目标 EHP
//   f_w      = H_w ÷ 现行本波 EHP                        本波所有变体 hp 的倍率（只改 hp，不改数量、速度、护甲、奖励）
//
// 用法：node .workbuddy/tools/balance_wave_targets.mjs [--a0 0.6] [--out <dir>]
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "../..");
const args = process.argv.slice(2);
const arg = (k, d) => (args.indexOf(k) >= 0 ? args[args.indexOf(k) + 1] : d);
const A0 = Number(arg("--a0", "0.6"));
const outDir = path.resolve(arg("--out", path.join(root, "Docs/Balance_TowerSystem")));
const cfg = (f) => JSON.parse(fs.readFileSync(path.join(root, "Assets/ConfigJson", f), "utf8"));
const anchor = JSON.parse(fs.readFileSync(path.join(outDir, "anchor_diagnostic.json"), "utf8"));
const income = JSON.parse(fs.readFileSync(path.join(outDir, "income_plan_A.json"), "utf8")).plan;
const mon = JSON.parse(fs.readFileSync(path.join(outDir, "monster_stats.json"), "utf8")).levels;

const scenes = cfg("tbsceneinfo.json").sort((a, b) => a.id - b.id);
const rounds = new Map(cfg("tbrounddata.json").map((x) => [x.id, x]));
const lists = new Map(cfg("tbenemylist.json").map((x) => [x.id, x]));

const out = [];
for (const sc of scenes) {
  const L = sc.id;
  const anc = anchor.rows.find((x) => x.L === L);
  const pl = income.find((x) => x.L === L);
  const m = mon.find((x) => x.levelId === L);
  const G = pl.G;
  const tPass = anc.Lpath / anc.vbar;
  const cum = [pl.initialGold];
  for (const w of pl.waves) cum.push(cum[cum.length - 1] + w.kill + w.reward);
  const waves = sc.RoundList.map((rid, idx) => {
    const w = idx + 1;
    const rd = rounds.get(rid);
    let span = 0;
    for (const lid of rd.EnemyIndexs) {
      const el = lists.get(lid);
      span += (el.EnemyIndexs.length * (el.enemyInterval || 200)) / 1000;
    }
    const piW = anc.pi25 * (A0 + (1 - A0) * (w - 1) / 24);
    const Twin = span + tPass;
    const cPrev = cum[w - 1] / G;
    const H = anc.P * cPrev * piW * Twin;
    const cur = m.waves[idx].ehp;
    return { wave: w, n: m.waves[idx].n, span: +span.toFixed(2), Twin: +Twin.toFixed(2), pi: +piW.toFixed(4),
      cPrev: +cPrev.toFixed(4), H: Math.round(H), EHPcur: Math.round(cur), f: +(H / cur).toFixed(3) };
  });
  out.push({ L, G, P: anc.P, Lpath: anc.Lpath, vbar: anc.vbar, tPass: +tPass.toFixed(2), A0, waves });
}

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, "wave_targets.json"), JSON.stringify({ A0, levels: out }, null, 2));

const md = ["# 逐波目标 EHP（推导量，非仿真）\n",
  `参数：A0 = ${A0}（首波 π = A0 × π25）；H_w = P × c_{w-1} × π_w × T_win_w；f_w = H_w ÷ 现行本波 EHP。\n`,
  "| L | 波 | 数量 n | π_w | 刷怪跨度 s | T_win s | c_{w-1} | H_w 目标 | 现行 EHP | f_w |", "|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"];
for (const l of out) for (const w of l.waves) md.push(`| ${l.L} | ${w.wave} | ${w.n} | ${w.pi} | ${w.span} | ${w.Twin} | ${w.cPrev} | ${w.H} | ${w.EHPcur} | ${w.f} |`);
fs.writeFileSync(path.join(outDir, "wave_targets.md"), md.join("\n") + "\n");

const fs_ = out.flatMap((l) => l.waves.map((w) => w.f));
console.log(`A0=${A0}; f 范围 ${Math.min(...fs_)} – ${Math.max(...fs_)}`);
for (const l of out) {
  const w25 = l.waves[24];
  console.log(`L${String(l.L).padStart(2, "0")} H1=${l.waves[0].H} (cur ${l.waves[0].EHPcur}) H25=${w25.H} (cur ${w25.EHPcur}) f25=${w25.f} f1=${l.waves[0].f}`);
}
