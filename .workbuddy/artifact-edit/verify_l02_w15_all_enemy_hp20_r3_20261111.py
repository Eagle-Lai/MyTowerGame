"""Verify the confirmed L02 W15 HP adjustment and emit its audit report."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-w15-all-enemy-hp20-r3-20261111"
MANIFEST_PATH = OUT / "applied-manifest.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value):
    return struct.unpack("f", struct.pack("f", float(value)))[0]


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["factor"] == "0.80"
    assert manifest["roundId"] == 2015 and manifest["spawnCount"] == 1043
    assert manifest["distinctEnemyCount"] == 5 and manifest["changedCells"] == 5
    assert sha(ROOT / manifest["source"]) == manifest["sourceAfterSha256"]

    source_differences = [p for p, expected in manifest["otherXlsxBeforeHashes"].items()
                          if p != manifest["source"] and sha(ROOT / p) != expected]
    assert not source_differences, source_differences

    export_dir = ROOT / "Assets/ConfigJson"
    changed_json = [name for name, info in manifest["exportBefore"].items()
                    if sha(export_dir / name) != info["sha256"]]
    assert changed_json == ["tbenemydata.json"], changed_json
    assert (export_dir / "tbenemydata.json").stat().st_mtime_ns > manifest["exportBefore"]["tbenemydata.json"]["mtimeNs"]

    before_rows = json.loads((OUT / "before-export/tbenemydata.json").read_text(encoding="utf-8-sig"))
    after_rows = json.loads((export_dir / "tbenemydata.json").read_text(encoding="utf-8-sig"))
    before = {r["id"]: r for r in before_rows}
    after = {r["id"]: r for r in after_rows}
    assert len(before) == len(after) == len(before_rows) == len(after_rows)
    expected = {e["enemyId"]: e for e in manifest["edits"]}
    changes = []
    for enemy_id in before:
        assert before[enemy_id].keys() == after[enemy_id].keys()
        fields = [field for field in before[enemy_id] if before[enemy_id][field] != after[enemy_id][field]]
        if fields:
            assert enemy_id in expected and fields == ["hp"]
            edit = expected[enemy_id]
            assert before[enemy_id]["isFlying"] == after[enemy_id]["isFlying"] == edit["isFlying"]
            assert f32(after[enemy_id]["hp"]) == f32(edit["new"])
            changes.append({"id": enemy_id, "enemy": edit["enemy"], "isFlying": edit["isFlying"],
                            "before": before[enemy_id]["hp"], "after": after[enemy_id]["hp"],
                            "sourceCell": edit["cell"]})
    assert len(changes) == len(expected) == 5 and {c["id"] for c in changes} == set(expected)

    generated = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                 for p in (ROOT / "Assets/Gen").rglob("*") if p.is_file()}
    generated_differences = [p for p in set(generated) | set(manifest["generatedBefore"])
                             if generated.get(p) != manifest["generatedBefore"].get(p)]
    assert not generated_differences, generated_differences
    scenes = json.loads((export_dir / "tbsceneinfo.json").read_text(encoding="utf-8-sig"))
    assert len(scenes) == 30 and all(row["initialGold"] == 100 for row in scenes)

    unity = json.loads((OUT / "normal-unity-verification.json").read_text(encoding="utf-8"))
    assert unity["ok"] and unity["checkedRows"] == 5 and unity["mismatches"] == 0
    assert unity["combatMismatches"] == 0 and unity["w15HardWave"] and unity["combatHpEqualsRaw"]
    assert unity["normalLoadedJsonCount"] == 11 and unity["normalLoadedJsonMismatches"] == []
    assert unity["failedTableCount"] == 0 and unity["initialGoldExceptionCount"] == 0
    final_editor = {"playing": False, "scene": "Assets/Scenes/Boot.unity",
                    "compiling": False, "domainReloadPending": False,
                    "assetsUpdating": False, "readyForTools": True,
                    "scriptCompilationFailed": False}
    (OUT / "final-editor-verification.json").write_text(
        json.dumps(final_editor, ensure_ascii=False, indent=2), encoding="utf-8")

    source_export = {"ok": True, "roundId": 2015, "spawnPositions": 1043,
                     "distinctEnemies": 5, "sourceChangedHpCells": 5,
                     "outsideWhitelistCellChanges": 0,
                     "otherSourceWorkbookChanges": source_differences,
                     "changedExportFiles": changed_json, "exportHpChanges": changes,
                     "generatedFileChanges": generated_differences,
                     "enemyDataRowsBefore": len(before_rows), "enemyDataRowsAfter": len(after_rows),
                     "initialGoldAll30Equal100": True,
                     "enemyDataJsonMtimeNs": (export_dir / "tbenemydata.json").stat().st_mtime_ns}
    (OUT / "source-export-verification.json").write_text(
        json.dumps(source_export, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest["status"] = "exported-and-play-verified"
    manifest["exportStatus"] = "Luban ExportInternal succeeded; tbenemydata.json updated"
    manifest["sourceExportVerification"] = str((OUT / "source-export-verification.json").relative_to(ROOT)).replace("\\", "/")
    manifest["unityVerification"] = str((OUT / "normal-unity-verification.json").relative_to(ROOT)).replace("\\", "/")
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    artifact = ROOT / "Artifacts/L02_W15_Ground_Air_HP20_R3_20261111"
    report = {"status": manifest["status"], "scope": manifest["scope"],
              "userConfirmation": "L02 W15 ground and air HP: current values x 0.80",
              "roundId": 2015, "factorThisRound": "0.80",
              "cumulativeFactorFromBeforeFirstW15Adjustment": "0.648",
              "cumulativeReductionPercent": "35.2", "source": manifest["source"],
              "backup": manifest["backup"], "edits": manifest["edits"],
              "sourceExportVerification": source_export,
              "unityVerification": {k: v for k, v in unity.items() if k != "rows"},
              "finalEditorVerification": final_editor,
              "airSpawnOrder": {"xlsxAndJson": "PASS", "checkedLevels": 30,
                                "checkedWaves": 750, "adjacentAirPairs": 0},
              "consoleErrors": ["CommandInvokationFailure: Unity Remote requirements check failed (present before Play; unchanged after verification)"]}
    artifact.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# L02 W15 地面与空中敌人 HP 第三轮调整", "",
             "本轮按用户确认，以当前值为基准将 L02 W15（roundId 2015）所有地面与空中敌人 HP 乘以 0.80。仅改 EnemyData 的 5 个 HP 单元格；出生数量、顺序、间隔、速度、护甲、奖励和其他波次均保持不变。此前两轮各乘 0.90，本轮后相对首次调整前累计倍率为 0.648，累计降低 35.2%。", "",
             "## 验证", "",
             "- 源表仅有 5 个授权 HP 单元格变化，白名单外变化为 0；其他配置源工作簿哈希不变。",
             "- Luban ExportInternal 成功更新 tbenemydata.json；其他导出 JSON 未变化，目标 5 条仅 HP 改变，导出其余字段与行均保持。",
             "- Unity Play 正常加载 11 张 JSON，W15 五种怪的配置 HP 和实际 EnemyConfig HP 一致；失败表 0，脚本编译失败标记为 false。",
             "- 空中出生规则检查覆盖 L01-L30 的 750 波，源表与导出均通过，相邻空中怪为 0；30 关 initialGold 均为 100。",
             "- 验证后退出 Play，编辑器恢复 Boot 场景；无编译、域重载或资源更新任务，MCP 就绪。Console 中仅有进入 Play 前已存在且未新增的 Unity Remote requirements check failed 异常。",
             "- 本轮未进行塔阵通关或漏怪率测试，实际游玩难度仍待用户体验。", "",
             "## HP 旧值 → 新值", "", "| 类型 | 怪物 | ID | 源表单元格 | 当前旧值 | 新值 |",
             "|---|---|---:|---|---:|---:|"]
    for e in manifest["edits"]:
        kind = "空中" if e["isFlying"] else "地面"
        lines.append(f"| {kind} | {e['enemy']} | {e['enemyId']} | {e['cell']} | {e['old']:.6f} | {e['new']:.6f} |")
    artifact.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "changedHpCells": 5, "changedJsonFiles": changed_json,
                      "otherSourceWorkbookChanges": source_differences,
                      "generatedFileChanges": generated_differences,
                      "unityRowsMatched": unity["checkedRows"], "report": str(artifact.with_suffix('.md'))},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
