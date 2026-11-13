"""Apply the explicitly confirmed L02 W15 HP reduction."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import re
import struct
import zipfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_l02_w11w25_ground_hp15_20261110 as precise

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-w15-all-enemy-hp20-r3-20261111"
SRC = precise.SRC
SHEET_XML = "xl/worksheets/sheet1.xml"
FACTOR = Decimal("0.80")
PREVIOUS = ROOT / "Library/BalanceStage/l02-w15-all-enemy-hp10-r2-20261110/applied-manifest.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def float32(value):
    return struct.unpack("f", struct.pack("f", value))[0]


def main():
    assert not (OUT / "applied-manifest.json").exists(), "This W15 reduction was already applied"
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    original = SRC.read_bytes()
    assert sha(original) == previous["sourceAfterSha256"], "EnemyData changed since the previous verified round"
    for path, expected in previous["otherXlsxBeforeHashes"].items():
        if path == previous["source"]:
            continue
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
    target_ids = set(spawn_ids)
    assert len(spawn_ids) == 1043 and len(target_ids) == 5

    references = defaultdict(list)
    for level in scenes:
        for wave_number, rid in enumerate(level["RoundList"], start=1):
            for gid in rounds[rid]["EnemyIndexs"]:
                for eid in groups[gid]["EnemyIndexs"]:
                    if eid in target_ids:
                        references[eid].append({"levelId": level["id"], "wave": wave_number, "roundId": rid, "groupId": gid})
    assert all(references[eid] and all(ref["levelId"] == 2 and ref["wave"] == 15 and ref["roundId"] == round_id
                                       for ref in references[eid]) for eid in target_ids)

    source_cells = precise.cells(original)
    values = source_cells["Sheet"]["values"]
    id_to_row = {values[r, 2]: r for r in range(1, source_cells["Sheet"]["shape"][0] + 1) if values.get((r, 2)) is not None}
    assert len(id_to_row) == len([r for r in range(1, source_cells["Sheet"]["shape"][0] + 1) if values.get((r, 2)) is not None])
    edits = []
    for eid in sorted(target_ids):
        assert eid in enemies and eid in id_to_row
        enemy = enemies[eid]
        row = id_to_row[eid]
        assert values[row, 14] == enemy["isFlying"] and enemy["isFlying"] in (0, 1)
        assert float32(values[row, 4]) == float32(enemy["hp"])
        assert float32(values[row, 3]) == float32(enemy["speed"])
        new_hp = (Decimal(str(values[row, 4])) * FACTOR).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
        assert Decimal(0) < new_hp < Decimal(str(values[row, 4]))
        edits.append({"wave": 15, "roundId": round_id, "enemyId": eid, "enemy": enemy["resName"],
                      "isFlying": enemy["isFlying"], "field": "hp", "old": values[row, 4], "new": float(new_hp),
                      "newText": format(new_hp, ".6f"), "row": row, "col": 4,
                      "file": str(SRC.relative_to(ROOT)).replace("\\", "/"), "sheet": "Sheet",
                      "cell": f"D{row}", "referenceCount": len(references[eid]), "references": references[eid]})
    assert len(edits) == 5 and {e["isFlying"] for e in edits} == {0, 1}

    with zipfile.ZipFile(BytesIO(original)) as zin:
        old_xml = zin.read(SHEET_XML).decode("utf-8")
        new_xml = old_xml
        for edit in edits:
            pattern = re.compile(r'(<(?:\w+:)?c\b[^>]*\br="' + edit["cell"] + r'"[^>]*>)(.*?)(</(?:\w+:)?c>)', re.S)
            matches = list(pattern.finditer(new_xml))
            assert len(matches) == 1, (edit["cell"], len(matches))
            match = matches[0]
            inner = match.group(2)
            assert not re.search(r"<(?:\w+:)?f\b", inner), "Refusing to overwrite a formula"
            value = re.search(r'(<(?:\w+:)?v>)([^<]+)(</(?:\w+:)?v>)', inner)
            assert value and Decimal(value.group(2)) == Decimal(str(edit["old"]))
            edit["oldXmlNumber"] = value.group(2)
            replacement = inner[:value.start(2)] + edit["newText"] + inner[value.end(2):]
            new_xml = new_xml[:match.start(2)] + replacement + new_xml[match.end(2):]

        def stripped(xml):
            for edit in edits:
                pattern = re.compile(r'(<(?:\w+:)?c\b[^>]*\br="' + edit["cell"] + r'"[^>]*>.*?<(?:\w+:)?v>)[^<]+(</(?:\w+:)?v>)', re.S)
                xml, count = pattern.subn(lambda m: m.group(1) + "AUTHORIZED_HP" + m.group(2), xml)
                assert count == 1
            return xml

        assert stripped(old_xml) == stripped(new_xml), "Unexpected worksheet XML changes"
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as zout:
            zout.comment = zin.comment
            for entry in zin.infolist():
                zout.writestr(entry, new_xml.encode("utf-8") if entry.filename == SHEET_XML else zin.read(entry.filename))
        payload = buffer.getvalue()

    after_cells = precise.cells(payload)
    assert source_cells.keys() == after_cells.keys()
    differences = []
    for sheet in source_cells:
        assert source_cells[sheet]["shape"] == after_cells[sheet]["shape"]
        before, after = source_cells[sheet]["values"], after_cells[sheet]["values"]
        differences.extend((sheet, r, c, old, after[r, c]) for (r, c), old in before.items() if old != after[r, c])
    allowed = {("Sheet", e["row"], 4): (e["old"], e["new"]) for e in edits}
    assert len(differences) == 5 and all(allowed[s, r, c] == (old, new) for s, r, c, old, new in differences)
    with zipfile.ZipFile(BytesIO(original)) as a, zipfile.ZipFile(BytesIO(payload)) as b:
        assert a.namelist() == b.namelist()
        assert [entry for entry in a.namelist() if a.read(entry) != b.read(entry)] == [SHEET_XML]

    OUT.mkdir(parents=True, exist_ok=True)
    backup = SRC.with_name("EnemyData.xlsx.bak_20261111_before_l02w15_all_enemy_hp20_r3")
    assert not backup.exists(), "Unexpected pre-existing backup; inspect before proceeding"
    with backup.open("xb") as stream:
        stream.write(original)
    (OUT / "before-export").mkdir()
    export_before = {}
    for path in (ROOT / "Assets/ConfigJson").glob("*.json"):
        content = path.read_bytes()
        (OUT / "before-export" / path.name).write_bytes(content)
        export_before[path.name] = {"sha256": sha(content), "mtimeNs": path.stat().st_mtime_ns}
    generated_before = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path.read_bytes())
                        for path in (ROOT / "Assets/Gen").rglob("*") if path.is_file()}
    manifest = {"status": "prepared", "factor": str(FACTOR), "scope": "L02 W15 ground and air HP only; third cumulative W15 adjustment",
                "source": str(SRC.relative_to(ROOT)).replace("\\", "/"), "sourceBeforeSha256": sha(original),
                "sourceAfterSha256": sha(payload), "backup": str(backup.relative_to(ROOT)).replace("\\", "/"),
                "roundId": round_id, "spawnCount": len(spawn_ids), "distinctEnemyCount": len(target_ids),
                "changedCells": len(differences), "outsideWhitelistCellChanges": 0, "edits": [{k: v for k, v in e.items() if k != "references"} for e in edits],
                "otherXlsxBeforeHashes": previous["otherXlsxBeforeHashes"], "exportBefore": export_before,
                "generatedBefore": generated_before}
    (OUT / "prepared-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    assert SRC.read_bytes() == original
    staged = OUT / "validated-candidate.xlsx"
    staged.write_bytes(payload)
    os.replace(staged, SRC)
    assert SRC.read_bytes() == payload and precise.cells(SRC.read_bytes()) == after_cells
    other_changes = [path for path, expected in previous["otherXlsxBeforeHashes"].items()
                     if path != manifest["source"] and sha((ROOT / path).read_bytes()) != expected]
    assert not other_changes, other_changes
    manifest["status"] = "source-applied-awaiting-Luban-export"
    manifest["otherSourceWorkbookChanges"] = other_changes
    (OUT / "applied-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "changedCells": len(edits), "outsideWhitelistCellChanges": 0,
                      "otherSourceWorkbookChanges": other_changes, "edits": [{k: v for k, v in e.items() if k != "references"} for e in edits]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
