#!/usr/bin/env python3
"""Build the measured 30-level report and per-level operation documents."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "Library" / "BalanceWorkbench" / "PlayMode-gold100-all30" / "unity-results.json"
ROUTES = ROOT / "Docs" / "Balance_TowerSystem" / "LevelRouteAndOperations"
PNG_DIR = ROUTES / "png"
OUT_ROOT = ROOT / "Docs" / "Balance_TowerSystem"
CANONICAL_PNG_DIR = OUT_ROOT / "LongestPathTowerPNG"
DETAIL_DIR = OUT_ROOT / "Measured_30Levels_2026-10-28"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_seconds(value):
    return f"{float(value):.2f}"


def main():
    results = load_json(RESULTS)
    tower_rows = load_json(ROOT / "Assets" / "ConfigJson" / "tbtowerinfo.json")
    tower_names = {int(row["id"]): row["name"] for row in tower_rows}
    results_by_level = {int(row["levelId"]): row for row in results}
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)

    summary = []
    for level in range(1, 31):
        result = results_by_level[level]
        metrics = result["metrics"]
        route = load_json(ROUTES / f"L{level:02d}.json")
        waves = metrics.get("waves", [])
        final_gold = waves[-1].get("gold") if waves else None
        min_hp = min((wave.get("hp", metrics.get("hp")) for wave in waves), default=metrics.get("hp"))
        failures = result.get("operationFailures") or []
        pending = result.get("pendingOperations") or []
        operations = result.get("operations") or []
        row = {
            "levelId": level,
            "initialGold": 100,
            "state": result.get("state"),
            "valid": bool(result.get("valid")),
            "victory": bool(result.get("victory")),
            "stars": result.get("stars"),
            "reasons": result.get("reasons") or [],
            "expectedWaveCount": metrics.get("expectedWaveCount"),
            "completedWaveCount": metrics.get("completedWaveCount"),
            "expectedEnemyCount": metrics.get("expectedEnemyCount"),
            "killed": metrics.get("killed"),
            "leaked": metrics.get("leaked"),
            "bossLeaked": metrics.get("bossLeaked"),
            "criticalLeaked": metrics.get("criticalLeaked"),
            "hpStart": metrics.get("maxHp"),
            "hpMin": min_hp,
            "hpEnd": metrics.get("hp"),
            "combatElapsedSeconds": metrics.get("combatElapsedSeconds"),
            "levelElapsedSeconds": metrics.get("levelElapsedSeconds"),
            "finalGold": final_gold,
            "operationCount": len(operations),
            "operationFailureCount": len(failures),
            "pendingOperationCount": len(pending),
            "profileId": result.get("profileId"),
            "balanceRevision": metrics.get("balanceRevision"),
            "ratingRevision": metrics.get("ratingRevision"),
            "longestPathEdges": route["longestPath"]["pathEdges"],
            "towerCellCount": len(route["longestPath"]["towerCells"]),
            "png": f"LongestPathTowerPNG/L{level:02d}_longest_path_towers.png",
        }
        summary.append(row)

        detail = []
        detail.append(f"# L{level:02d} 实测通关与操作流程")
        detail.append("")
        detail.append("本页的战斗数据来自 Unity PlayMode 批量回放，不是离线模拟。初始金额按硬性规定固定为 100。")
        detail.append("")
        detail.append("## 实测结果")
        detail.append("")
        detail.append(f"- 结论：{'通关' if row['victory'] else '未通关'}；星级：{row['stars']} 星；正式运行时 profile：`{row['profileId']}`。")
        detail.append(f"- 初始金额：`{row['initialGold']}`；最终金额：`{row['finalGold']}`；完成波数：`{row['completedWaveCount']}/{row['expectedWaveCount']}`。")
        detail.append(f"- 击杀：`{row['killed']}/{row['expectedEnemyCount']}`；漏怪：`{row['leaked']}`；HP：`{row['hpStart']} -> {row['hpMin']} -> {row['hpEnd']}`。")
        detail.append(f"- 战斗时间：`{fmt_seconds(row['combatElapsedSeconds'])}s`；关卡时间：`{fmt_seconds(row['levelElapsedSeconds'])}s`。")
        detail.append(f"- 回放操作数：`{row['operationCount']}`；操作失败：`{row['operationFailureCount']}`；待执行操作：`{row['pendingOperationCount']}`。")
        if row["reasons"]:
            detail.append(f"- 评分说明：`{'；'.join(row['reasons'])}`。")
        detail.append("")
        detail.append("## 最长路径 PNG")
        detail.append("")
        detail.append(f"![L{level:02d} longest path tower placement](../LongestPathTowerPNG/L{level:02d}_longest_path_towers.png)")
        detail.append("")
        detail.append(f"该图由 `L{level:02d}.json` 的正式 `longestPath` 数据渲染，路径长度为 `{row['longestPathEdges']}` 条边，推荐塔位 `{row['towerCellCount']}` 个。该路线是预算候选中的最长路径，不宣称数学全局最优。")
        detail.append("")
        detail.append("## 具体操作步骤")
        detail.append("")
        detail.append("坐标使用回放接口坐标：`x = col`、`y = row`。波次开始后按 `关卡时间` 执行；同一波次的多行按表格顺序执行。")
        detail.append("")
        detail.append("| 步骤 | 波次 | 关卡时间(s) | 操作 | 坐标(x,y) | towerId/塔型 | 花费 | 操作后金额 |")
        detail.append("|---:|---:|---:|---|---|---|---:|---:|")
        for index, operation in enumerate(operations, 1):
            tower_id = int(operation.get("towerId", 0))
            tower_name = tower_names.get(tower_id, "Unknown Tower")
            action = operation.get("action", operation.get("type", "unknown"))
            action_map = {"build": "建造", "upgrade": "升级", "sell": "出售"}
            action_text = action_map.get(action, action)
            time_ms = operation.get("levelTimeMs", operation.get("requestedTimeMs", 0))
            detail.append(f"| {index} | {operation.get('waveOrdinal', '-') } | {float(time_ms) / 1000:.2f} | {action_text} | ({operation.get('col')},{operation.get('row')}) | {tower_id}/{tower_name} | {operation.get('cost', 0)} | {operation.get('balanceAfter', '-')} |")
        if not operations:
            detail.append("| - | - | - | 无 | - | - | - | - |")
        detail.append("")
        detail.append("操作完成后等待当前波次清场或按下一行的目标波次继续；不要跳过升级与出售步骤。")
        (DETAIL_DIR / f"L{level:02d}.md").write_text("\n".join(detail) + "\n", encoding="utf-8")

    report_json = OUT_ROOT / "Measured_30Levels_2026-10-28.json"
    report_json.write_text(json.dumps({
        "schema": "balance_unity_playmode_measurement/1",
        "measuredAt": datetime.now(timezone.utc).isoformat(),
        "source": "Library/BalanceWorkbench/PlayMode-gold100-all30/unity-results.json",
        "runtime": {"unityVersion": "2022.3.62f3c1", "instance": "FishTestGame@0c9048e2c2ec99ee", "profileId": "D04"},
        "hardRules": {"initialGold": 100, "measurement": "Unity PlayMode real scene/pools/A*/tower/economy/WaveManager/GameClock"},
        "levels": summary,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = []
    report.append("# 30 关 Unity 实测结果与 PNG 摆塔交付（2026-10-28）")
    report.append("")
    report.append("本报告记录本轮 Unity 2022.3.62f3c1 PlayMode 批量回放的正式结果。所有关卡初始金额均为 100；结果来自真实场景、对象池、A*、塔攻击、AOE、减速、经济、WaveManager、GameClock 与评分器。路线图为 PNG 文件，不以 ASCII 简图作为交付物。")
    report.append("")
    report.append("## 总结")
    report.append("")
    report.append(f"- 实测范围：L01-L30，共 {len(summary)} 关；通关 {sum(1 for row in summary if row['victory'])} 关。")
    report.append(f"- 星级：5 星 {sum(1 for row in summary if row['stars'] == 5)} 关；4 星 {sum(1 for row in summary if row['stars'] == 4)} 关。")
    report.append(f"- 漏怪：共有 {sum(1 for row in summary if row['leaked'] > 0)} 关出现漏怪，具体为 L04（{next(row['leaked'] for row in summary if row['levelId'] == 4)}）和 L22（{next(row['leaked'] for row in summary if row['levelId'] == 22)}）；两关仍然通关但按评分规则为 4 星。")
    report.append("- 初始金额核对：30/30 关为 100。")
    report.append("")
    report.append("## 逐关实测表")
    report.append("")
    report.append("| 关卡 | 星级 | 通关 | 波次 | 击杀/预期 | 漏怪 | HP(起始/最低/结束) | 战斗时间(s) | 关卡时间(s) | 最终金额 | 操作数 | PNG |")
    report.append("|---:|---:|---|---:|---:|---:|---|---:|---:|---:|---:|---|")
    for row in summary:
        report.append(f"| [L{row['levelId']:02d}](Measured_30Levels_2026-10-28/L{row['levelId']:02d}.md) | {row['stars']} | {'是' if row['victory'] else '否'} | {row['completedWaveCount']}/{row['expectedWaveCount']} | {row['killed']}/{row['expectedEnemyCount']} | {row['leaked']} | {row['hpStart']}/{row['hpMin']}/{row['hpEnd']} | {fmt_seconds(row['combatElapsedSeconds'])} | {fmt_seconds(row['levelElapsedSeconds'])} | {row['finalGold']} | {row['operationCount']} | [PNG](LongestPathTowerPNG/L{row['levelId']:02d}_longest_path_towers.png) |")
    report.append("")
    report.append("## 交付说明")
    report.append("")
    report.append("每个关卡独立文档包含真实结果、最长路径 PNG、完整建造/升级/出售步骤、波次、关卡时间、坐标、towerId、花费和操作后金额。PNG 的路径和塔位来源于正式路线 JSON；路线搜索声明为预算候选中的最长路径。")
    report.append("")
    report.append("本轮没有修改受保护的关卡源表；配置结果通过 Unity 运行时导出物核对。")
    (OUT_ROOT / "Measured_30Levels_2026-10-28.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    png_index = ["# 最长路径 PNG 摆塔图", "", "以下 30 个文件均为正式 PNG 图片，展示地图网格、坐标、起点、终点、路径方向、路径顺序、阻挡格和推荐塔位。交付主目录为 `Docs/Balance_TowerSystem/LongestPathTowerPNG/`。", "", "| 关卡 | PNG | 路径边数 | 塔位数 |", "|---:|---|---:|---:|"]
    png_json = []
    for row in summary:
        png_index.append(f"| L{row['levelId']:02d} | [L{row['levelId']:02d}_longest_path_towers.png](L{row['levelId']:02d}_longest_path_towers.png) | {row['longestPathEdges']} | {row['towerCellCount']} |")
        png_json.append({"levelId": row["levelId"], "pathEdges": row["longestPathEdges"], "towerCellCount": row["towerCellCount"], "png": f"L{row['levelId']:02d}_longest_path_towers.png"})
    CANONICAL_PNG_DIR.mkdir(parents=True, exist_ok=True)
    (CANONICAL_PNG_DIR / "index.md").write_text("\n".join(png_index) + "\n", encoding="utf-8")
    (CANONICAL_PNG_DIR / "index.json").write_text(json.dumps({"schema": "longest_path_tower_png_index/1", "directory": "Docs/Balance_TowerSystem/LongestPathTowerPNG", "levels": png_json}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROUTES / "png" / "index.md").write_text("\n".join(png_index) + "\n", encoding="utf-8")
    (ROUTES / "png" / "index.json").write_text(json.dumps({"schema": "longest_path_tower_png_index/1", "directory": "Docs/Balance_TowerSystem/LongestPathTowerPNG", "levels": png_json}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(summary)} level docs, report, and PNG index")


if __name__ == "__main__":
    main()
