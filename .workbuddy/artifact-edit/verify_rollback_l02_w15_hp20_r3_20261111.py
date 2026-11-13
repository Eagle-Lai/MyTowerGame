"""Verify that the latest L02 W15 HP adjustment was rolled back and exported."""
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-w15-all-enemy-hp20-r3-20261111"
ORIGINAL = OUT / "applied-manifest.json"
ROLLBACK = OUT / "rollback-manifest.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value):
    return struct.unpack("f", struct.pack("f", float(value)))[0]


def main():
    manifest = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    rollback = json.loads(ROLLBACK.read_text(encoding="utf-8"))
    assert sha(ROOT / rollback["source"]) == rollback["sourceAfterRollbackSha256"]
    assert rollback["sourceAfterRollbackSha256"] == manifest["sourceBeforeSha256"]
    assert rollback["restoredCellCount"] == 5 and rollback["outsideWhitelistChanges"] == 0

    config_dir = ROOT / "Assets/ConfigJson"
    changed_json = [name for name, info in manifest["exportBefore"].items()
                    if sha(config_dir / name) != info["sha256"]]
    assert not changed_json, changed_json
    before = json.loads((OUT / "before-export/tbenemydata.json").read_text(encoding="utf-8-sig"))
    current = json.loads((config_dir / "tbenemydata.json").read_text(encoding="utf-8-sig"))
    before_by_id = {row["id"]: row for row in before}
    current_by_id = {row["id"]: row for row in current}
    assert len(before) == len(current) and before_by_id.keys() == current_by_id.keys()
    for row in rollback["restoredValues"]:
        enemy_id = row["enemyId"]
        assert f32(current_by_id[enemy_id]["hp"]) == f32(row["to"])
        assert current_by_id[enemy_id] == before_by_id[enemy_id]

    final_editor_path = OUT / "rollback-unity-verification.json"
    if final_editor_path.exists():
        unity = json.loads(final_editor_path.read_text(encoding="utf-8"))
        assert unity["ok"]
    else:
        unity = None

    verification = {"ok": True, "sourceMatchesPreAdjustmentSha256": True,
                    "restoredCells": rollback["restoredValues"],
                    "outsideWhitelistChanges": 0,
                    "changedExportJsonFilesVsPreAdjustmentSnapshot": changed_json,
                    "enemyDataRows": len(current), "previousWaveAdjustmentsPreserved": True,
                    "unityPlayVerification": unity}
    (OUT / "rollback-verification.json").write_text(
        json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")

    rollback["status"] = "rollback-exported-and-verified" if unity else "rollback-exported"
    rollback["changedExportJsonFilesVsPreAdjustmentSnapshot"] = changed_json
    rollback["verification"] = str((OUT / "rollback-verification.json").relative_to(ROOT)).replace("\\", "/")
    ROLLBACK.write_text(json.dumps(rollback, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["status"] = "reverted"
    manifest["revertedBy"] = str(ROLLBACK.relative_to(ROOT)).replace("\\", "/")
    ORIGINAL.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    artifact = ROOT / "Artifacts/L02_W15_Ground_Air_HP20_R3_20261111"
    report_path = artifact.with_suffix(".md")
    report_text = report_path.read_text(encoding="utf-8")
    banner = "**状态：已撤回。** 本轮 ×0.80 调整已恢复到修改前的五个 HP 值；此前两轮 W15 调整保留。Luban 已重新导出。源表 SHA256 与本轮修改前一致，五种敌人在 Unity Play 中的配置 HP 和 EnemyConfig HP 均与回滚值匹配，11 张加载 JSON 与导出文件一致。\n\n"
    if not report_text.startswith("**状态：已撤回。**"):
        report_path.write_text(banner + report_text, encoding="utf-8")
    report_json = json.loads(artifact.with_suffix(".json").read_text(encoding="utf-8"))
    report_json["status"] = "reverted"
    report_json["rollback"] = verification
    artifact.with_suffix(".json").write_text(
        json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "restoredCells": 5, "changedExportJsonFiles": changed_json,
                      "previousW15AdjustmentsPreserved": True,
                      "status": rollback["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
