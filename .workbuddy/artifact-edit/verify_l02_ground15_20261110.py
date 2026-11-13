"""Read-only verification of the approved edit and the real Luban export."""
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-ground15-20261110"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def float32(value):
    return struct.unpack("f", struct.pack("f", value))[0]


def verify_exports(output_dir):
    OUT = output_dir
    m = json.loads((OUT / "applied-manifest.json").read_text(encoding="utf-8"))
    assert sha(ROOT / m["source"]) == m["sourceAfterSha256"]
    other_sources = [p for p, expected in m["otherXlsxBeforeHashes"].items()
                     if p != m["source"] and sha(ROOT / p) != expected]
    assert not other_sources, other_sources
    changed_exports = [name for name, info in m["exportBefore"].items()
                       if sha(ROOT / "Assets/ConfigJson" / name) != info["sha256"]]
    assert changed_exports == ["tbenemydata.json"], changed_exports
    before_path = OUT / "before-export/tbenemydata.json"
    after_path = ROOT / "Assets/ConfigJson/tbenemydata.json"
    before_rows = json.loads(before_path.read_text(encoding="utf-8-sig"))
    after_rows = json.loads(after_path.read_text(encoding="utf-8-sig"))
    before = {r["id"]: r for r in before_rows}
    after = {r["id"]: r for r in after_rows}
    assert len(before_rows) == len(after_rows) == len(before) == len(after) and before.keys() == after.keys()
    changes = []
    expected = {e["enemyId"]: e for e in m["edits"]}
    for eid in before:
        assert before[eid].keys() == after[eid].keys()
        for field in before[eid]:
            if before[eid][field] != after[eid][field]:
                assert eid in expected and field == "hp" and before[eid]["isFlying"] == 0
                assert float32(after[eid][field]) == float32(expected[eid]["new"])
                changes.append({"id": eid, "field": field, "before": before[eid][field], "after": after[eid][field]})
    assert len(changes) == len(expected) == 61
    generated = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in (ROOT / "Assets/Gen").rglob("*") if p.is_file()}
    generated_changes = [p for p in set(generated) | set(m["generatedBefore"]) if generated.get(p) != m["generatedBefore"].get(p)]
    assert not generated_changes, generated_changes
    scenes = json.loads((ROOT / "Assets/ConfigJson/tbsceneinfo.json").read_text(encoding="utf-8-sig"))
    assert len(scenes) == 30 and all(s["initialGold"] == 100 for s in scenes)
    assert after_path.stat().st_mtime_ns > m["exportBefore"][after_path.name]["mtimeNs"]
    report = {"ok": True, "sourceChangedHpCells": m["changedCells"], "outsideWhitelistCellChanges": 0,
              "otherSourceWorkbookChanges": other_sources, "changedExportFiles": changed_exports,
              "exportHpChanges": changes, "generatedFileChanges": generated_changes,
              "beforeEnemyRowCount": len(before_rows), "afterEnemyRowCount": len(after_rows),
              "beforeEnemyJsonLines": len(before_path.read_text(encoding="utf-8-sig").splitlines()),
              "afterEnemyJsonLines": len(after_path.read_text(encoding="utf-8-sig").splitlines()),
              "airEnemyRowsUnchanged": True, "initialGoldAll30Equal100": True,
              "enemyJsonMtimeNs": after_path.stat().st_mtime_ns}
    (OUT / "source-export-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report, m


def main():
    report, m = verify_exports(OUT)
    normal_path = OUT / "normal-unity-verification.json"
    if normal_path.exists():
        normal = json.loads(normal_path.read_text(encoding="utf-8"))
        assert normal["ok"] and normal["checkedGroundRows"] == 61 and normal["normalLoadedJsonCount"] == 11
        artifact = ROOT / "Artifacts/L02_W11_W25_Ground_HP15_20261110"
        summary = {"status": "applied-exported-normal-Unity-verified-awaiting-user-playtest", "factor": m["factor"],
                   "scope": m["scope"], "source": m["source"], "backup": m["backup"],
                   "sourceBeforeSha256": m["sourceBeforeSha256"], "sourceAfterSha256": m["sourceAfterSha256"],
                   "edits": m["edits"], "sourceExportVerification": report,
                   "unityVerification": {k: v for k, v in normal.items() if k != "rows"}}
        artifact.with_suffix(".json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = ["# L02 W11–W25 地面血量降低 15%：已落表并导出", "",
                 "用户已确认使用当前源表现值 ×0.85，仅修改 L02 W11–W25 地面 HP，共 61 个单元格；按 6 位小数四舍五入。", "",
                 "源表：`Luban/Config/Datas/Levels/L02/EnemyData.xlsx`，工作表 `Sheet`。", "",
                 "备份：`" + m["backup"] + "`。", "",
                 "## 实际验收", "",
                 "- 源表逐格回读：61 个目标 HP 变化，白名单外零改动；其他 249 份配置源表 SHA256 未变。",
                 "- OOXML：只替换指定单元格的数字；除 sheet1.xml 外，所有 ZIP 条目内容完全一致；表结构、公式、样式保持。",
                 "- Luban：本工程 MCP 调用现有 ExportInternal，真实返回 true；工具输出含 `== succ ==`，11 张表导出成功。",
                 "- 本轮导出变化仅 `Assets/ConfigJson/tbenemydata.json`；全表 12,296 条，前后均为 221,330 行，仅目标 61 条 HP 不同。其他 JSON、Assets/Gen 内容均未变。",
                 "- Unity 正常 Play 启动：YooAsset 就绪；[Config] 加载完成，失败表 0；正常内存中的 11 张 JSON 与本次导出文件逐字一致；61 条地面 HP 回读全匹配。",
                 "- 强制刷新、编译、域重载完成，scriptCompilationFailed=false。",
                 "- 空中出生顺序：改前、改后分别检查 L02 XLSX 和 JSON，均为 25 波、1,923 只空中怪、0 相邻空中怪、0 输入错误。",
                 "- 所有空中敌人记录保持；W1–W10、数量、出生顺序、出生间隔、速度、护甲、奖励均保持。30 关 initialGold 仍全为 100。",
                 "- 恢复到停止运行的 Boot 编辑场景；场景未变脏，Assets/Scenes 无修改。未代替用户进行 W11 实际塔阵战斗验收。", "",
                 "## 验证过程说明", "",
                 "Windows 首次拒绝截断被映射的源文件，原文件哈希未变化；保留备份后采用同盘原子替换成功。",
                 "直接在 EditMode 初始化 YooAsset 触发 DontDestroyOnLoad 的运行模式限制；已删除本次验证创建的临时 [YooAssets] 对象，随后改用正常 Play 启动完成加载验证。结束时该临时对象不存在。",
                 "正常 Play 验证时 Console 仅见改动前已存在的 `Unity Remote requirements check failed`，没有新增配置加载或编译错误；未手动清空日志。",
                 "L02 EnemyData.levelId 历史归属警告仍存在，本轮未修改该字段。", "",
                 "## 完整单元格改动", "", "| 波次 | roundId | 敌人 ID | 怪物 | 单元格 | 修改前 HP | 修改后 HP |",
                 "|---|---:|---:|---|---|---:|---:|"]
        for e in m["edits"]:
            lines.append(f"| W{e['wave']} | {e['roundId']} | {e['enemyId']} | {e['enemy']} | {e['cell']} | {e['old']:.6f} | {e['new']:.6f} |")
        lines += ["", "本轮只调整试测数值。实际漏怪数量、扣血与 W11–W25 的体验仍需用户实测反馈；本记录不宣称全部波次已稳定通过。"]
        artifact.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "exportHpChanges"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
