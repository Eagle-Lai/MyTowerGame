"""Read-only post-export checks and application record for the second HP reduction."""
from pathlib import Path
import json
from verify_l02_ground15_20261110 import verify_exports

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-ground8-r2-20261110"


def main():
    report, manifest = verify_exports(OUT)
    normal = json.loads((OUT / "normal-unity-verification.json").read_text(encoding="utf-8"))
    assert normal["ok"] and normal["checkedGroundRows"] == 61 and normal["normalLoadedJsonCount"] == 11
    assert normal["groundMismatches"] == 0 and normal["normalLoadedJsonMismatches"] == []
    artifact = ROOT / "Artifacts/L02_W11_W25_Ground_HP8_R2_20261110"
    record = {"status": "applied-exported-normal-Unity-verified-awaiting-user-playtest",
              "scope": manifest["scope"], "thisRoundFactor": "0.92", "previousRoundFactor": "0.85",
              "nominalCumulativeFactor": "0.782", "nominalCumulativeReductionPct": "21.8",
              "basis": "Current values after the approved 15% reduction, verified from source cells",
              "source": manifest["source"], "backup": manifest["backup"],
              "sourceBeforeSha256": manifest["sourceBeforeSha256"], "sourceAfterSha256": manifest["sourceAfterSha256"],
              "edits": manifest["edits"], "sourceExportVerification": report,
              "unityVerification": {k: v for k, v in normal.items() if k != "rows"}}
    artifact.with_suffix(".json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# L02 W11–W25 地面血量再降低 8%：第二轮已落表并导出", "",
             "用户在 15% 版本试测后继续反馈地面仍强，要求再整体降低 8%。沿用本轮上下文的最小范围：L02 W11–W25 地面 HP，不扩到其他波次或关卡。", "",
             "本轮用上一轮落表后的当前 HP ×0.92，逐格核对旧值，保留 6 位小数。两轮名义累计倍率为 0.85×0.92=0.782，即相对第一轮前约降低 21.8%。", "",
             "源表：`" + manifest["source"] + "`，工作表 `Sheet`。备份：`" + manifest["backup"] + "`。", "",
             "## 已完成验收", "",
             "- 61 个地面 HP 单元格变化，源表白名单外零变化，其他 249 份源表 SHA256 未变。",
             "- 表结构、公式和样式保持；只有 sheet1.xml 内指定数字变化，其余 ZIP 条目内容一致。",
             "- 当前工程 unityMCP / stdio / 6400，核对实例 FreedomTower_1@520e2c6d、工程 D:/FreedomTower_1、Unity 2022.3.62f3c1 后调用现有 Luban ExportInternal，真实返回 true，11 张表导出成功。",
             "- 导出只改变 tbenemydata.json，mtime 已更新；前后均为 12,296 条敌人记录、221,330 行，仅目标 61 条 HP 变化。其余 JSON 和 Assets/Gen 内容未变。",
             "- 正常 Play 启动：[Config] 失败表 0；加载的全部 11 张 JSON 与导出逐字匹配，61 条新 HP 回读零差异，scriptCompilationFailed=false。",
             "- L02 XLSX/JSON 在修改前和导出后均通过空中出生顺序检查：25 波、1,923 只空中怪、0 相邻空中怪、0 输入错误。",
             "- 所有空中记录、数量、顺序、间隔、速度、护甲和奖励保持，W1–W10 和其他关卡未改；30 关 initialGold 全部仍为 100。",
             "- 未修改 C# 战斗逻辑；当前 Console 仅有改动前原有的 Unity Remote requirements check failed，未新增编译或配置加载错误，未手动清空日志。",
             "- 正常启动验证已结束，未启动任何关卡战斗；实际 W11–W25 体验仍待用户试测。", "",
             "## 完整旧值→新值", "", "| 波次 | roundId | 敌人 ID | 怪物 | 单元格 | 本轮修改前 HP | 本轮修改后 HP |",
             "|---|---:|---:|---|---|---:|---:|"]
    for e in manifest["edits"]:
        lines.append(f"| W{e['wave']} | {e['roundId']} | {e['enemyId']} | {e['enemy']} | {e['cell']} | {e['old']:.6f} | {e['new']:.6f} |")
    artifact.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "changedHpCells": len(manifest["edits"]), "cumulativeFactor": "0.782",
                      "report": str(artifact.with_suffix('.md'))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
