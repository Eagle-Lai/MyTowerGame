"""Apply only the confirmed L02 W15 flying-enemy HP adjustment."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import re
import struct
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_l02_w11w25_ground_hp15_20261110 as precise

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-w15-air-hp10-20261111"
SRC = precise.SRC
SHEET_XML = "xl/worksheets/sheet1.xml"
FACTOR = Decimal("0.90")
PRIOR = ROOT / "Library/BalanceStage/l02-w15-all-enemy-hp20-r3-20261111"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def f32(value):
    return struct.unpack("f", struct.pack("f", float(value)))[0]


def main():
    assert not OUT.exists(), "Audit directory already exists; inspect before continuing"
    prior = json.loads((PRIOR / "applied-manifest.json").read_text(encoding="utf-8"))
    rollback = json.loads((PRIOR / "rollback-manifest.json").read_text(encoding="utf-8"))
    original = SRC.read_bytes()
    assert sha(original) == rollback["sourceAfterRollbackSha256"] == prior["sourceBeforeSha256"], \
        "EnemyData changed since rollback; refusing to apply"
    for path, expected in prior["otherXlsxBeforeHashes"].items():
        if path != prior["source"]:
            assert sha((ROOT / path).read_bytes()) == expected, f"Another source workbook changed: {path}"

    def load(name):
        return json.loads((ROOT / "Assets/ConfigJson" / f"{name}.json").read_text(encoding="utf-8-sig"))

    scenes = load("tbsceneinfo")
    assert len(scenes) == 30 and all(row["initialGold"] == 100 for row in scenes)
    scene = next(row for row in scenes if row["id"] == 2)
    round_id = scene["RoundList"][14]
    assert round_id == 2015
    rounds = {row["id"]: row for row in load("tbrounddata")}
    groups = {row["id"]: row for row in load("tbenemylist")}
    enemies = {row["id"]: row for row in load("tbenemydata")}
    spawn_ids = [eid for gid in rounds[round_id]["EnemyIndexs"] for eid in groups[gid]["EnemyIndexs"]]
    flying_ids = {eid for eid in set(spawn_ids) if enemies[eid]["isFlying"] != 0}
    assert len(spawn_ids) == 1043 and len(flying_ids) == 1
    target_id = next(iter(flying_ids))

    refs = defaultdict(list)
    for level in scenes:
        for wave, rid in enumerate(level["RoundList"], start=1):
            for group_id in rounds[rid]["EnemyIndexs"]:
                for enemy_id in groups[group_id]["EnemyIndexs"]:
                    if enemy_id == target_id:
                        refs[enemy_id].append({"levelId": level["id"], "wave": wave,
                                               "roundId": rid, "groupId": group_id})
    assert refs[target_id] and all(r == {"levelId": 2, "wave": 15, "roundId": 2015, "groupId": r["groupId"]}
                                   for r in refs[target_id])

    source_cells = precise.cells(original)
    values = source_cells["Sheet"]["values"]
    id_to_row = {values[r, 2]: r for r in range(1, source_cells["Sheet"]["shape"][0] + 1)
                 if values.get((r, 2)) is not None}
    row = id_to_row[target_id]
    enemy = enemies[target_id]
    assert enemy["isFlying"] != 0 and values[row, 14] == enemy["isFlying"]
    assert f32(values[row, 4]) == f32(enemy["hp"])
    edit = {"wave": 15, "roundId": 2015, "enemyId": target_id,
            "enemy": enemy["resName"], "isFlying": enemy["isFlying"], "field": "hp",
            "old": values[row, 4],
            "new": float((Decimal(str(values[row, 4])) * FACTOR).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)),
            "newText": format((Decimal(str(values[row, 4])) * FACTOR).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP), ".6f"),
            "row": row, "col": 4, "cell": f"D{row}",
            "referenceCount": len(refs[target_id]), "references": refs[target_id]}
    assert Decimal(0) < Decimal(edit["newText"]) < Decimal(str(edit["old"]))

    with zipfile.ZipFile(BytesIO(original)) as archive:
        old_xml = archive.read(SHEET_XML).decode("utf-8")
        pattern = re.compile(r'(<(?:\w+:)?c\b[^>]*\br="' + edit["cell"] + r'"[^>]*>)(.*?)(</(?:\w+:)?c>)', re.S)
        matches = list(pattern.finditer(old_xml))
        assert len(matches) == 1
        match = matches[0]
        inner = match.group(2)
        assert not re.search(r"<(?:\w+:)?f\b", inner)
        value = re.search(r'(<(?:\w+:)?v>)([^<]+)(</(?:\w+:)?v>)', inner)
        assert value and Decimal(value.group(2)) == Decimal(str(edit["old"]))
        edit["oldXmlNumber"] = value.group(2)
        inner = inner[:value.start(2)] + edit["newText"] + inner[value.end(2):]
        new_xml = old_xml[:match.start(2)] + inner + old_xml[match.end(2):]
        mask = lambda xml: re.sub(r'(<(?:\w+:)?c\b[^>]*\br="' + edit["cell"] + r'"[^>]*>.*?<(?:\w+:)?v>)[^<]+(</(?:\w+:)?v>)',
                                  r'\1AUTHORIZED_HP\2', xml, count=1, flags=re.S)
        assert mask(old_xml) == mask(new_xml)
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as result:
            result.comment = archive.comment
            for entry in archive.infolist():
                result.writestr(entry, new_xml.encode("utf-8") if entry.filename == SHEET_XML else archive.read(entry.filename))
        payload = buffer.getvalue()

    before_cells, after_cells = precise.cells(original), precise.cells(payload)
    differences = []
    for sheet in before_cells:
        before, after = before_cells[sheet]["values"], after_cells[sheet]["values"]
        differences.extend((sheet, r, c, old, after[r, c]) for (r, c), old in before.items() if old != after[r, c])
    assert differences == [("Sheet", row, 4, edit["old"], edit["new"])], differences

    OUT.mkdir(parents=True)
    backup = SRC.with_name("EnemyData.xlsx.bak_20261111_before_l02w15_air_hp10")
    assert not backup.exists()
    backup.write_bytes(original)
    (OUT / "before-export").mkdir()
    export_before = {}
    for path in (ROOT / "Assets/ConfigJson").glob("*.json"):
        data = path.read_bytes()
        (OUT / "before-export" / path.name).write_bytes(data)
        export_before[path.name] = {"sha256": sha(data), "mtimeNs": path.stat().st_mtime_ns}
    generated = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p.read_bytes())
                 for p in (ROOT / "Assets/Gen").rglob("*") if p.is_file()}
    manifest = {"status": "prepared", "factor": str(FACTOR),
                "scope": "L02 W15 flying enemies HP only; current config baseline",
                "source": str(SRC.relative_to(ROOT)).replace("\\", "/"),
                "sourceBeforeSha256": sha(original), "sourceAfterSha256": sha(payload),
                "backup": str(backup.relative_to(ROOT)).replace("\\", "/"),
                "roundId": round_id, "spawnCount": len(spawn_ids), "flyingEnemyCount": len(flying_ids),
                "changedCells": 1, "outsideWhitelistCellChanges": 0,
                "edit": {k: v for k, v in edit.items() if k != "references"},
                "referenceGroups": refs[target_id],
                "otherXlsxBeforeHashes": prior["otherXlsxBeforeHashes"],
                "exportBefore": export_before, "generatedBefore": generated}
    (OUT / "prepared-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    candidate = OUT / "validated-candidate.xlsx"
    candidate.write_bytes(payload)
    os.replace(candidate, SRC)
    assert sha(SRC.read_bytes()) == manifest["sourceAfterSha256"]
    manifest["status"] = "source-applied-awaiting-Luban-export"
    (OUT / "applied-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "edit": manifest["edit"],
                      "outsideWhitelistCellChanges": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
