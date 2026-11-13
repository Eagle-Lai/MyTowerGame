"""Verify and document the explicitly confirmed fourth HP reduction."""
from pathlib import Path
import json
from verify_l02_ground15_20261110 import verify_exports

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-ground8-r4-20261110"


def main():
    report, manifest = verify_exports(OUT)
    normal = json.loads((OUT / "normal-unity-verification.json").read_text(encoding="utf-8"))
    assert normal["ok"] and normal["checkedGroundRows"] == 61 and normal["normalLoadedJsonCount"] == 11
    assert normal["groundMismatches"] == 0 and normal["normalLoadedJsonMismatches"] == []
    final = json.loads((OUT / "final-editor-verification.json").read_text(encoding="utf-8"))
    assert not final["playing"] and not final["dirty"] and not final["compilationFailed"]
    assert final["scene"] == "Assets/Scenes/Boot.unity"
    artifact = ROOT / "Artifacts/L02_W11_W25_Ground_HP8_R4_20261110"
    record = {"status": "applied-exported-normal-Unity-verified-awaiting-user-playtest",
              "userConfirmation": "继续改为下调8%", "scope": manifest["scope"],
              "thisRoundFactor": "0.92", "previousCumulativeFactor": "0.719440",
              "nominalCumulativeFactor": "0.6618848", "nominalCumulativeReductionPct": "33.81152",
              "basis": "Current source values exactly matching completed round 3; explicit stacking confirmation",
              "source": manifest["source"], "backup": manifest["backup"],
              "sourceBeforeSha256": manifest["sourceBeforeSha256"], "sourceAfterSha256": manifest["sourceAfterSha256"],
              "edits": manifest["edits"], "sourceExportVerification": report,
              "unityVerification": {k: v for k, v in normal.items() if k != "rows"},
              "finalEditorVerification": final}
    artifact.with_suffix(".json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    other_count = len(manifest["otherXlsxBeforeHashes"]) - 1
    lines = ["# L02 W11–W25 地面血量第四轮：再降低 8%，已落表并导出", "",
             "用户本轮将原先提出的 4% 改为「继续改为下调8%」，以此作为本轮最终口径，只执行一次 ×0.92。仅修改 L02 W11–W25 中 isFlying=0 的地面敌人 HP，以已完成的第三轮源表现值为基准乘 0.92，保留 6 位小数。", "",
             "四轮名义累计倍率为 0.85×0.92×0.92×0.92=0.6618848，即相对第一轮修改前降低约 33.81152%。本轮为试测数值调整，不声称实际塔阵已稳定通过 W11–W25。", "",
             "源表：`" + manifest["source"] + "`，工作表 `Sheet`。备份：`" + manifest["backup"] + "`。", "",
             "## 实际验收", "",
             f"- 源表逐格回读：61 个目标 HP 单元格变化，白名单外零变化；其他 {other_count} 份源表 SHA256 未变。",
             "- OOXML 仅指定 HP 数字变化，其他 ZIP 条目内容一致；表结构、公式、格式保持。",
             "- 当前实体工程 D:/FreedomTower_1，Unity 2022.3.62f3c1，unityMCP stdio 6400，实例 FreedomTower_1@520e2c6d；连接和 Play 域重载后重新核对身份。",
             "- 通过本工程现有 Luban ExportInternal 真实导出成功，11 张表；tbenemydata.json 的 mtime 更新且 git status 为 M。",
             f"- 与本轮导出前快照相比，仅 tbenemydata.json 内容变化：{report['afterEnemyRowCount']:,} 条记录、{report['afterEnemyJsonLines']:,} 行，只有目标 61 条 HP 变化；其他 JSON 和 Assets/Gen 内容均未变。",
             "- git status 中原有 tbenemylist.json、tbrounddata.json 修改保留；本轮哈希比对证明未再次改变其内容。",
             "- 正常 Play 启动实际加载：全部 11 张 JSON 与导出逐字匹配，61 条地面 HP 与预期 float32 值全部一致，失败表 0，scriptCompilationFailed=false。",
             "- 修改前、导出后 L02 XLSX 与 JSON 空中出生顺序检查均通过：25 波、1,923 只空中怪、0 相邻空中对、0 输入错误。",
             "- 空中敌人、数量、出生顺序、间隔、速度、护甲、奖励、W1–W10 和其他关卡保持现值；30 关 initialGold 全部仍为 100。",
             "- Console 仅有本轮修改前已存在的 Unity Remote requirements check failed，未新增配置加载或编译错误，未手动清空日志。",
             "- 验证后已停止 Play，恢复干净的 Boot 场景，未启动关卡战斗。", "",
             "## 完整旧值→新值", "", "| 波次 | roundId | 敌人 ID | 怪物 | 单元格 | 本轮修改前 HP | 本轮修改后 HP |",
             "|---|---:|---:|---|---|---:|---:|"]
    for e in manifest["edits"]:
        lines.append(f"| W{e['wave']} | {e['roundId']} | {e['enemyId']} | {e['enemy']} | {e['cell']} | {e['old']:.6f} | {e['new']:.6f} |")
    artifact.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "changedHpCells": len(manifest["edits"]), "cumulativeFactor": "0.6618848",
                      "report": str(artifact.with_suffix('.md'))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
