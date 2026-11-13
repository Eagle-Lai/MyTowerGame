"""Read-only HP proposal. Does not edit source workbooks or exported config."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "Library/BalanceStage/l02-w11-review-20261110-135842/current-baseline.json"
OUT = ROOT / "Library/BalanceStage/l02-ground-hp-proposal-20261110"


def read_export(name):
    return json.loads((ROOT / "Assets/ConfigJson" / (name + ".json")).read_text(encoding="utf-8-sig"))


def main():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in base["sourceHashes"].items()), "Source changed; refresh baseline first"
    edits = []
    factor = Decimal("0.80")
    for wave in base["waves"]:
        if not 11 <= wave["wave"] <= 25:
            continue
        for enemy in wave["roster"]:
            if enemy["isFlying"] != 0:
                continue
            new = (Decimal(str(enemy["hp"])) * factor).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
            edits.append({"wave": wave["wave"], "roundId": wave["roundId"], "enemyId": enemy["id"],
                          "enemy": enemy["resName"], "isFlying": enemy["isFlying"], "field": "hp",
                          "old": enemy["hp"], "new": float(new), "factor": str(factor), **enemy["hpSource"]})
    target_ids = {e["enemyId"] for e in edits}
    assert len(target_ids) == len(edits) == 61, "Repeated IDs or changed target roster"
    rounds = {r["id"]: r for r in read_export("tbrounddata")}
    groups = {g["id"]: g for g in read_export("tbenemylist")}
    references = defaultdict(list)
    scenes = read_export("tbsceneinfo")
    assert len(scenes) == 30 and all(s["initialGold"] == 100 for s in scenes)
    for scene in scenes:
        for wave, rid in enumerate(scene["RoundList"], 1):
            for gid in rounds[rid]["EnemyIndexs"]:
                for eid in set(groups[gid]["EnemyIndexs"]):
                    if eid in target_ids:
                        references[eid].append([scene["id"], wave, rid, gid])
    for edit in edits:
        refs = references[edit["enemyId"]]
        assert refs and all(r[:3] == [2, edit["wave"], edit["roundId"]] for r in refs), (edit, refs)
    scenarios = []
    for value in ("0.85", "0.80", "0.75"):
        f = float(value)
        w10, w11 = base["waves"][9:11]
        scenarios.append({"groundHpFactor": value, "groundHpReductionPct": (1-f)*100,
                          "w11GroundMeanEhpPerSecond": w11["channels"]["ground"]["meanEhpPerSecond"]*f,
                          "w11GroundPeak10sEhpPerSecond": w11["channels"]["ground"]["peak10sEhpPerSecond"]*f,
                          "w11MeanRelativeToW10": w11["channels"]["ground"]["meanEhpPerSecond"]*f/w10["channels"]["ground"]["meanEhpPerSecond"],
                          "w11PeakRelativeToW10": w11["channels"]["ground"]["peak10sEhpPerSecond"]*f/w10["channels"]["ground"]["peak10sEhpPerSecond"]})
    result = {"status": "proposal-awaiting-user-value-confirmation", "scope": "L02 W11-W25 ground HP only",
              "baseline": str(BASE.relative_to(ROOT)), "sourceWrites": 0, "exportWrites": 0,
              "edits": edits, "referenceProof": dict(references), "scenarios": scenarios,
              "unchanged": ["all air HP/counts/order/timing", "ground counts/order/timing", "speed", "armor", "rewards", "initialGold", "W1-W10", "all other levels"],
              "knownTradeoff": "New ground composition means W11 common-species HP may fall below W10; no monotonic HP-floor is imposed on this unapproved candidate.",
              "limitation": "Static arrival-pressure comparison. No actual user W11 tower snapshot or Unity combat validation yet."}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "proposal.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# L02 W11–W25 地面血量候选（待用户确认）", "",
             "仅预览：源表和导出产物均未改动。建议首轮只把 61 条地面记录 HP 乘 0.80，数量和间隔保持当前值。", "",
             "空中分类只按 isFlying != 0；空中 HP、数量、位置与出生时间均不改。全关卡引用核查确认这 61 个 ID 仅被 L02 对应目标波次使用。", "",
             "这不是已完成的算法校准或实战结论。当前没有取得用户实际 W11 开波塔阵。该方案是供选择的首轮削弱幅度。", "",
             "## W11 静态压力敏感性", "", "| 地面血量削弱 | 平均地面 EHP/秒 | 10 秒峰值 EHP/秒 | 平均压力相对 W10 |", "|---|---:|---:|---:|"]
    for s in scenarios:
        lines.append(f"| {s['groundHpReductionPct']:.0f}% | {s['w11GroundMeanEhpPerSecond']:.2f} | {s['w11GroundPeak10sEhpPerSecond']:.2f} | {s['w11MeanRelativeToW10']:.1%} |")
    lines += ["", "注意：统一 HP 削弱 20% 会使 W11 Chicken/Larva/Crawler 单只 HP 低于 W10 同类当前值；W11 仍保留新增重甲组成和更高总地面压力。此方案不沿用旧算法的同类 HP 单调下限。", "",
              "HP 改变不会改变理论全击杀奖励，但真实击杀率和收入仍会随战斗结果变化。地面难度下降也可能改变普通塔对地/空的实际射击分配，因此空中实际通过情况仍需复测。", "",
              "## 完整单元格候选", "", "源文件：Luban/Config/Datas/Levels/L02/EnemyData.xlsx；工作表 Sheet；只拟修改下列 hp 单元格。", "",
              "| 波次 | roundId | 敌人 ID | 资源名 | 单元格 | 当前 HP | 候选 HP |", "|---|---:|---:|---|---|---:|---:|"]
    for e in edits:
        lines.append(f"| W{e['wave']} | {e['roundId']} | {e['enemyId']} | {e['enemy']} | {e['cell']} | {e['old']:.6f} | {e['new']:.6f} |")
    (OUT / "proposal.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in base["sourceHashes"].items())
    print(json.dumps({"proposal": str(OUT / "proposal.md"), "groundHpCells": len(edits), "sourceWrites": 0,
                      "outsideTargetReferences": 0, "scenarios": scenarios, "W11": [e for e in edits if e["wave"] == 11]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
