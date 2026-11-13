"""Verify the exact L02 W15 ground/air HP adjustment and normal Unity load."""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-w15-all-enemy-hp10-r2-20261110"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value):
    return struct.unpack("f", struct.pack("f", value))[0]


def compact_manifest(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for edit in manifest["edits"]:
        if "references" in edit:
            refs = edit.pop("references")
            edit["referenceLocations"] = sorted({(r["levelId"], r["wave"], r["roundId"], r["groupId"]) for r in refs})
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main():
    manifest = compact_manifest(OUT / "applied-manifest.json")
    compact_manifest(OUT / "prepared-manifest.json")
    assert manifest["scope"] == "L02 W15 ground and air HP only"
    assert manifest["roundId"] == 2015 and manifest["spawnCount"] == 1043
    assert sha(ROOT / manifest["source"]) == manifest["sourceAfterSha256"]
    other_source_changes = [p for p, expected in manifest["otherXlsxBeforeHashes"].items()
                            if p != manifest["source"] and sha(ROOT / p) != expected]
    assert not other_source_changes, other_source_changes
    changed_json = [name for name, info in manifest["exportBefore"].items()
                    if sha(ROOT / "Assets/ConfigJson" / name) != info["sha256"]]
    assert changed_json == ["tbenemydata.json"], changed_json
    before_path = OUT / "before-export/tbenemydata.json"
    after_path = ROOT / "Assets/ConfigJson/tbenemydata.json"
    before_rows = json.loads(before_path.read_text(encoding="utf-8-sig"))
    after_rows = json.loads(after_path.read_text(encoding="utf-8-sig"))
    before = {r["id"]: r for r in before_rows}
    after = {r["id"]: r for r in after_rows}
    assert len(before) == len(after) == len(before_rows) == len(after_rows) and before.keys() == after.keys()
    expected = {e["enemyId"]: e for e in manifest["edits"]}
    changes = []
    for eid in before:
        assert before[eid].keys() == after[eid].keys()
        changed_fields = [field for field in before[eid] if before[eid][field] != after[eid][field]]
        if changed_fields:
            assert eid in expected and changed_fields == ["hp"]
            edit = expected[eid]
            assert before[eid]["isFlying"] == edit["isFlying"] == after[eid]["isFlying"]
            assert f32(after[eid]["hp"]) == f32(edit["new"])
            changes.append({"id": eid, "field": "hp", "isFlying": edit["isFlying"],
                            "before": before[eid]["hp"], "after": after[eid]["hp"]})
    assert {c["id"] for c in changes} == set(expected) and len(changes) == 5
    assert {e["isFlying"] for e in manifest["edits"]} == {0, 1}
    generated = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                 for p in (ROOT / "Assets/Gen").rglob("*") if p.is_file()}
    generated_changes = [p for p in set(generated) | set(manifest["generatedBefore"])
                         if generated.get(p) != manifest["generatedBefore"].get(p)]
    assert not generated_changes, generated_changes
    scenes = json.loads((ROOT / "Assets/ConfigJson/tbsceneinfo.json").read_text(encoding="utf-8-sig"))
    assert len(scenes) == 30 and all(row["initialGold"] == 100 for row in scenes)
    assert after_path.stat().st_mtime_ns > manifest["exportBefore"][after_path.name]["mtimeNs"]
    source_export = {"ok": True, "roundId": 2015, "spawnPositions": manifest["spawnCount"],
                     "distinctEnemies": len(expected), "sourceChangedHpCells": len(expected),
                     "outsideWhitelistCellChanges": 0, "otherSourceWorkbookChanges": other_source_changes,
                     "changedExportFiles": changed_json, "exportHpChanges": changes,
                     "generatedFileChanges": generated_changes, "beforeEnemyRows": len(before_rows),
                     "afterEnemyRows": len(after_rows), "initialGoldAll30Equal100": True,
                     "airAndGroundTargetsPresent": True, "enemyJsonMtimeNs": after_path.stat().st_mtime_ns}
    (OUT / "source-export-verification.json").write_text(json.dumps(source_export, ensure_ascii=False, indent=2), encoding="utf-8")

    if "--source-only" in sys.argv:
        print(json.dumps({k: v for k, v in source_export.items() if k != "exportHpChanges"}, ensure_ascii=False))
        return
    normal = json.loads((OUT / "normal-unity-verification.json").read_text(encoding="utf-8"))
    assert normal["ok"] and normal["checkedRows"] == 5 and normal["mismatches"] == 0
    assert normal["combatMismatches"] == 0 and normal["w15HardWave"] and normal["combatHpEqualsRaw"]
    assert normal["normalLoadedJsonCount"] == 11 and normal["normalLoadedJsonMismatches"] == []
    assert normal["failedTableCount"] == 0 and normal["initialGoldExceptionCount"] == 0
    final = json.loads((OUT / "final-editor-verification.json").read_text(encoding="utf-8"))
    assert final == {"playing": False, "scene": "Assets/Scenes/Boot.unity", "dirty": False, "compilationFailed": False}

    artifact = ROOT / "Artifacts/L02_W15_Ground_Air_HP10_R2_20261110"
    report = {"status": "applied-exported-normal-Unity-verified",
              "userConfirmation": "叠加，再乘 0.90", "w15CumulativeFactor": "0.81", "w15CumulativeReductionPct": "19", "scope": manifest["scope"],
              "roundId": 2015, "factor": "0.90", "source": manifest["source"],
              "backup": manifest["backup"], "edits": manifest["edits"],
              "sourceExportVerification": source_export,
              "unityVerification": {k: v for k, v in normal.items() if k != "rows"},
              "finalEditorVerification": final}
    artifact.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# L02 W15 地面与空中敌人第二轮：再下调 10%", "",
             "用户确认仅调整 L02 W15（roundId 2015）全部地面与空中敌人的 HP，按上一轮已下调后的当前配置值再 ×0.90。两轮累计 ×0.81，较两轮前降低约 19%。本波共有 1,043 个出生位置、5 种敌人记录（4 种地面、1 种空中）；仅改 5 个 EnemyData HP 单元格。数量、出生次序、间隔及其他字段未改。", "",
             f"## 验证", "",
             f"- 源表只改 5 个白名单 HP 单元格，其他 {len(manifest['otherXlsxBeforeHashes']) - 1} 份源表哈希不变，OOXML 结构和格式保持。",
             "- Luban ExportInternal 返回成功，导出 11 张表；只有 tbenemydata.json 内容变化，目标五条 HP 精确匹配，其余记录和字段不变。",
             "- 正常 Play 加载的 11 张 JSON 与导出逐字一致，五条 HP 全匹配；额外按 L02 W15 困难波倍率构造战斗配置，HP 与新表值相同，未额外放大；失败表 0，scriptCompilationFailed=false。",
             "- W15 引用链核验五种敌人仅被 L02 W15 使用；空中出生顺序检查通过，30 关 initialGold 均为 100。",
             "- Console 仅有改动前已有的 Unity Remote requirements check failed；未新增配置/编译错误。验证后已停止 Play，恢复干净 Boot 场景。实际战斗体验待用户试测。", "",
             "## 单元格旧值→新值", "", "| 类型 | 波次 | roundId | 敌人 ID | 敌人 | 单元格 | HP 修改前 | HP 修改后 |",
             "|---|---:|---:|---:|---|---|---:|---:|"]
    for e in manifest["edits"]:
        kind = "空中" if e["isFlying"] else "地面"
        lines.append(f"| {kind} | W15 | 2015 | {e['enemyId']} | {e['enemy']} | {e['cell']} | {e['old']:.6f} | {e['new']:.6f} |")
    artifact.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "changedHpCells": len(expected), "groundEnemyTypes": 4,
                      "airEnemyTypes": 1, "report": str(artifact.with_suffix('.md'))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
