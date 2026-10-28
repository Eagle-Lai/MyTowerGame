// 只读：统计 30 关 × 25 波的怪物构成（C 章）。
// 数据链：tbsceneinfo.RoundList -> tbrounddata.EnemyIndexs -> tbenemylist.EnemyIndexs -> tbenemydata
// 口径：
//   - 怪数 = 配置计划数（每个变体 id 在 tbenemylist 中出现一次记一只）
//   - 防空 = tbenemydata.isFlying === 1（与变体 desc 的 role=air 一致，脚本会交叉核对）
//   - 对地 = 总数 - 防空；本数据集中不存在既非空中也非地面的单位
//   - EHP = hp（护甲在伤害侧折算，不并入 EHP）
//   - 种类去重键 = canonical（desc 中 canonical=）；变体 id 不计种类
//   - 角色 = desc 中 role=（normal/medium/heavy/air/...）
// 用法：node .workbuddy/tools/balance_monster_stats.mjs [--out <dir>]
// 只写 --out 目录（默认 Docs/Balance_TowerSystem），不写 Luban/、Assets/。
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "../..");
const args = process.argv.slice(2);
const outArg = args.indexOf("--out") >= 0 ? args[args.indexOf("--out") + 1] : path.join(root, "Docs/Balance_TowerSystem");
const cfg = (f) => JSON.parse(fs.readFileSync(path.join(root, "Assets/ConfigJson", f), "utf8"));

const scenes = cfg("tbsceneinfo.json").sort((a, b) => a.id - b.id);
const rounds = new Map(cfg("tbrounddata.json").map((r) => [r.id, r]));
const lists = new Map(cfg("tbenemylist.json").map((r) => [r.id, r]));
const enemies = new Map(cfg("tbenemydata.json").map((r) => [r.id, r]));

const parseDesc = (d) => {
  const m = {};
  for (const part of (d || "").split(";")) {
    const kv = part.trim().split("=");
    if (kv.length === 2) m[kv[0].trim()] = kv[1].trim();
  }
  return m;
};

const levels = [];
for (const sc of scenes) {
  const L = sc.id;
  const waves = [];
  const roleTotals = {};
  const kinds = new Set();
  const firstRole = {};
  let totalN = 0, airN = 0, totalEhp = 0, airEhp = 0, mismatch = 0;
  sc.RoundList.forEach((roundId, idx) => {
    const w = idx + 1;
    const rd = rounds.get(roundId);
    if (!rd) throw new Error(`missing round ${roundId} in level ${L}`);
    let n = 0, air = 0, ehp = 0, aEhp = 0;
    const roleCount = {};
    for (const listId of rd.EnemyIndexs) {
      const el = lists.get(listId);
      if (!el) throw new Error(`missing enemylist ${listId}`);
      for (const vid of el.EnemyIndexs) {
        const e = enemies.get(vid);
        if (!e) throw new Error(`missing variant ${vid}`);
        const d = parseDesc(e.desc);
        n++;
        totalN++;
        ehp += e.hp;
        totalEhp += e.hp;
        const role = d.role || "unknown";
        roleCount[role] = (roleCount[role] || 0) + 1;
        roleTotals[role] = roleTotals[role] || { n: 0, ehp: 0 };
        roleTotals[role].n++;
        roleTotals[role].ehp += e.hp;
        if (!firstRole[role]) firstRole[role] = { level: L, wave: w };
        if (d.canonical) kinds.add(d.canonical);
        const isAir = e.isFlying === 1;
        if (isAir !== (role === "air")) mismatch++;
        if (isAir) { air++; airN++; aEhp += e.hp; airEhp += e.hp; }
      }
    }
    waves.push({ wave: w, roundId, rewardGold: rd.rewardGold, n, air, ground: n - air,
      airShare: n ? +(air / n).toFixed(3) : 0, ehp: +ehp.toFixed(2), airEhp: +aEhp.toFixed(2),
      airEhpShare: ehp ? +(aEhp / ehp).toFixed(3) : 0, roles: roleCount });
  });
  levels.push({ levelId: L, name: sc.name, waves, totalN, airN, groundN: totalN - airN,
    airShare: +(airN / totalN).toFixed(3), totalEhp: +totalEhp.toFixed(2), airEhp: +airEhp.toFixed(2),
    airEhpShare: +(airEhp / totalEhp).toFixed(3), kindCount: kinds.size, roleTotals, firstRole, roleMismatch: mismatch });
}

fs.mkdirSync(outArg, { recursive: true });
fs.writeFileSync(path.join(outArg, "monster_stats.json"), JSON.stringify({ levels }, null, 2));

// 按关汇总（C.2 第一张表）
const md = [];
md.push("# 怪物构成统计（只读，脚本生成）\n");
md.push("口径：怪数=配置计划数；防空=isFlying===1（与 role=air 交叉核对，见 roleMismatch）；EHP=hp；种类=canonical 去重。\n");
md.push("## 按关汇总\n");
md.push("| 关 | 总怪 | 防空 | 对地 | 防空占比(数量) | 种类 | 全关 EHP | 空中 EHP | 空中 EHP 占比 | role 不一致 |");
md.push("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|");
for (const l of levels) {
  md.push(`| ${l.levelId} | ${l.totalN} | ${l.airN} | ${l.groundN} | ${l.airShare} | ${l.kindCount} | ${l.totalEhp.toFixed(0)} | ${l.airEhp.toFixed(0)} | ${l.airEhpShare} | ${l.roleMismatch} |`);
}
md.push("\n## 角色首次出场（关 / 波）\n");
md.push("| 关 | " + ["normal", "medium", "heavy", "air", "elite", "boss", "swarm", "quick"].join(" | ") + " |");
md.push("|---:|" + "---:|".repeat(8));
for (const l of levels) {
  const cells = ["normal", "medium", "heavy", "air", "elite", "boss", "swarm", "quick"].map((r) => {
    const f = l.firstRole[r];
    return f ? `${f.level}-W${f.wave}` : "—";
  });
  md.push(`| ${l.levelId} | ${cells.join(" | ")} |`);
}
fs.writeFileSync(path.join(outArg, "monster_stats.md"), md.join("\n") + "\n");

const summary = levels.map((l) => `L${String(l.levelId).padStart(2, "0")} N=${l.totalN} air=${l.airN}(${l.airShare}) EHP=${l.totalEhp.toFixed(0)} airEHP=${l.airEhpShare} kinds=${l.kindCount} roles=${Object.keys(l.roleTotals).join("/")} mismatch=${l.roleMismatch}`);
console.log(summary.join("\n"));
console.log(`written: ${outArg}`);
