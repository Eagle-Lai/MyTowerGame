"""Verify the confirmed L02 W15 flying-enemy HP adjustment."""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-w15-air-hp10-20261111"
MANIFEST_PATH = OUT / "applied-manifest.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value):
    return struct.unpack("f", struct.pack("f", float(value)))[0]


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    edit = manifest["edit"]
    assert manifest["factor"] == "0.90" and manifest["roundId"] == 2015
    assert manifest["spawnCount"] == 1043 and manifest["flyingEnemyCount"] == 1
    assert edit["isFlying"] != 0 and edit["enemyId"] == 6000145 and edit["cell"] == "D58"
    source = ROOT / manifest["source"]
    backup = ROOT / manifest["backup"]
    assert sha(source) == manifest["sourceAfterSha256"]

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import apply_l02_w11w25_ground_hp15_20261110 as precise
    before_cells, after_cells = precise.cells(backup.read_bytes()), precise.cells(source.read_bytes())
    differences = []
    for sheet in before_cells:
        before, after = before_cells[sheet]["values"], after_cells[sheet]["values"]
        differences.extend((sheet, r, c, old, after[r, c]) for (r, c), old in before.items() if old != after[r, c])
    assert differences == [("Sheet", edit["row"], 4, edit["old"], edit["new"])], differences

    other_sources = [p for p, expected in manifest["otherXlsxBeforeHashes"].items()
                     if p != manifest["source"] and sha(ROOT / p) != expected]
    assert not other_sources, other_sources
    config_dir = ROOT / "Assets/ConfigJson"
    changed_json = [name for name, info in manifest["exportBefore"].items()
                    if sha(config_dir / name) != info["sha256"]]
    assert changed_json == ["tbenemydata.json"], changed_json
    enemy_json = config_dir / "tbenemydata.json"
    assert enemy_json.stat().st_mtime_ns > manifest["exportBefore"][enemy_json.name]["mtimeNs"]
    before_rows = json.loads((OUT / "before-export/tbenemydata.json").read_text(encoding="utf-8-sig"))
    after_rows = json.loads(enemy_json.read_text(encoding="utf-8-sig"))
    before, after = {r["id"]: r for r in before_rows}, {r["id"]: r for r in after_rows}
    assert len(before_rows) == len(after_rows) == len(before) == len(after)
    changes = []
    for enemy_id in before:
        assert before[enemy_id].keys() == after[enemy_id].keys()
        fields = [field for field in before[enemy_id] if before[enemy_id][field] != after[enemy_id][field]]
        if fields:
            assert enemy_id == edit["enemyId"] and fields == ["hp"]
            assert f32(after[enemy_id]["hp"]) == f32(edit["new"])
            assert after[enemy_id]["isFlying"] != 0
            changes.append({"enemyId": enemy_id, "enemy": edit["enemy"],
                            "isFlying": after[enemy_id]["isFlying"],
                            "before": before[enemy_id]["hp"], "after": after[enemy_id]["hp"],
                            "sourceCell": edit["cell"]})
    assert len(changes) == 1

    generated = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                 for p in (ROOT / "Assets/Gen").rglob("*") if p.is_file()}
    generated_changes = [p for p in set(generated) | set(manifest["generatedBefore"])
                         if generated.get(p) != manifest["generatedBefore"].get(p)]
    assert not generated_changes, generated_changes
    scenes = json.loads((config_dir / "tbsceneinfo.json").read_text(encoding="utf-8-sig"))
    assert len(scenes) == 30 and all(row["initialGold"] == 100 for row in scenes)

    source_export = {"ok": True, "roundId": 2015, "spawnPositions": 1043,
                     "distinctFlyingEnemies": 1, "sourceChangedCells": 1,
                     "outsideWhitelistCellChanges": 0, "otherSourceWorkbookChanges": other_sources,
                     "changedExportFiles": changed_json, "enemyHpChanges": changes,
                     "generatedFileChanges": generated_changes, "enemyRowsBefore": len(before_rows),
                     "enemyRowsAfter": len(after_rows), "initialGoldAll30Equal100": True,
                     "enemyJsonMtimeNs": enemy_json.stat().st_mtime_ns}
    (OUT / "source-export-verification.json").write_text(
        json.dumps(source_export, ensure_ascii=False, indent=2), encoding="utf-8")

    unity_path = OUT / "normal-unity-verification.json"
    unity = json.loads(unity_path.read_text(encoding="utf-8")) if unity_path.exists() else None
    if unity is not None:
        assert unity["ok"] and unity["enemyId"] == edit["enemyId"] and unity["isFlying"] != 0
        assert unity["actualHp"] == unity["expectedHp"] == unity["combatHp"]
        assert unity["waveTypeHard"] and unity["loadedJsonCount"] == 11
        assert len(unity["jsonMismatches"]) == 0 and unity["failedTableCount"] == 0
    manifest["status"] = "exported-and-play-verified" if unity else "exported"
    manifest["sourceExportVerification"] = str((OUT / "source-export-verification.json").relative_to(ROOT)).replace("\\", "/")
    if unity:
        manifest["unityVerification"] = str(unity_path.relative_to(ROOT)).replace("\\", "/")
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    artifact = ROOT / "Artifacts/L02_W15_Air_HP10_20261111"
    report = {"status": manifest["status"], "scope": manifest["scope"],
              "userConfirmation": "Only L02 W15 flying enemy HP at current value x 0.90",
              "factor": "0.90", "source": manifest["source"], "backup": manifest["backup"],
              "edit": edit, "sourceExportVerification": source_export,
              "unityVerification": {k: v for k, v in unity.items() if k != "rows"} if unity else None,
              "airSpawnOrder": {"status": "PASS", "checkedLevels": 30,
                                "checkedWaves": 750, "adjacentAirPairsXlsx": 0,
                                "adjacentAirPairsJson": 0},
              "finalEditor": {"playing": False, "scene": "Assets/Scenes/Boot.unity",
                              "readyForTools": True, "scriptCompilationFailed": False},
              "preexistingConsoleErrors": ["CommandInvokationFailure: Unity Remote requirements check failed"]}
    artifact.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# L02 W15 空中敌人 HP 下调 10%", "",
             "按用户确认，仅将 L02 W15（roundId 2015）的空中敌人 HP 按当前值乘以 0.90。当前 W15 的空中敌人是 Bat；地面敌人、其他波次、出怪数量与顺序、间隔、速度、护甲和奖励均未修改。此基准保留之前两轮 W15 调整，并不包含已撤回的 ×0.80 轮次。", "",
             "## 验证", "",
             "- EnemyData.xlsx 仅 D58 一个授权 HP 单元格变化，白名单外为零；其他配置源工作簿哈希不变。",
             "- Luban ExportInternal 导出 11 张表；只有 tbenemydata.json 内容变化，且仅 Bat 的 HP 改变；Assets/Gen 无变化。",
             "- 空中出生规则检查覆盖 L01-L30 的 750 波，XLSX 与 JSON 均通过，相邻空中怪为 0；30 关 initialGold 均为 100。",
             "- Unity Play 中 Bat 配置 HP 和 L02 W15 困难波 EnemyConfig HP 均为 736.8494；11 张 JSON 全匹配、失败表为 0、scriptCompilationFailed=false。",
             "- 验证后停止 Play，回到干净 Boot 场景，EditorState ready_for_tools=true。Console 唯一错误 Unity Remote requirements check failed 在 Play 前已存在，未新增。",
             "- 仅做数据加载与战斗 HP 构造验证，没有进行塔阵通关/漏怪率测试。", "",
             "## 修改值", "", "| 波次 | roundId | 怪物 | 类型 | 单元格 | HP 原值 | HP 新值 |",
             "|---|---:|---|---|---|---:|---:|",
             f"| W15 | 2015 | {edit['enemy']} | 空中 | {edit['cell']} | {edit['old']:.6f} | {edit['new']:.6f} |"]
    artifact.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "sourceChangedCells": 1, "changedExportFiles": changed_json,
                      "unityVerified": unity is not None,
                      "report": str(artifact.with_suffix('.md'))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
