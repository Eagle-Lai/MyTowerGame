"""Apply the user's approved L02 W11-W25 ground HP x0.85 via precise OOXML edits."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import re
import zipfile
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "Library/BalanceStage/l02-w11-review-20261110-135842/current-baseline.json"
OUT = ROOT / "Library/BalanceStage/l02-ground15-20261110"
SRC = ROOT / "Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
BACKUP = SRC.with_name("EnemyData.xlsx.bak_20261110_before_w11w25_ground_hp15")
SHEET = "xl/worksheets/sheet1.xml"
FACTOR = Decimal("0.85")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def cells(payload):
    wb = openpyxl.load_workbook(BytesIO(payload), read_only=False, data_only=False)
    result = {s.title: {"shape": [s.max_row, s.max_column],
                        "values": {(r, c): s.cell(r, c).value for r in range(1, s.max_row + 1)
                                   for c in range(1, s.max_column + 1)}} for s in wb.worksheets}
    wb.close()
    return result


def main():
    assert not (OUT / "applied-manifest.json").exists(), "Application manifest exists; do not apply twice"
    base = json.loads(BASE.read_text(encoding="utf-8"))
    for p, expected in base["sourceHashes"].items():
        assert digest((ROOT / p).read_bytes()) == expected, f"Baseline changed: {p}"
    original = SRC.read_bytes()
    if BACKUP.exists():
        assert BACKUP.read_bytes() == original, "Existing backup differs from current source; investigate before resuming"
    before_cells = cells(original)
    edits = []
    for wave in base["waves"]:
        if 11 <= wave["wave"] <= 25:
            for enemy in wave["roster"]:
                if enemy["isFlying"] != 0:
                    continue
                source = enemy["hpSource"]
                assert source["file"] == str(SRC.relative_to(ROOT)).replace("\\", "/")
                row = int(re.search(r"\d+$", source["cell"])[0])
                current = before_cells[source["sheet"]]["values"]
                assert current[row, 2] == enemy["id"] and current[row, 14] == 0
                assert Decimal(str(current[row, 4])) == Decimal(str(enemy["hp"]))
                new = (Decimal(str(enemy["hp"])) * FACTOR).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
                assert Decimal(0) < new < Decimal(str(enemy["hp"]))
                edits.append({"wave": wave["wave"], "roundId": wave["roundId"], "enemyId": enemy["id"],
                              "enemy": enemy["resName"], "field": "hp", "old": enemy["hp"], "new": float(new),
                              "newText": format(new, ".6f"), "row": row, "col": 4, **source})
    target_ids = {e["enemyId"] for e in edits}
    assert len(edits) == len(target_ids) == 61
    # Prove that changing the selected rows cannot affect another level/wave.
    def exported(name):
        return json.loads((ROOT / "Assets/ConfigJson" / (name + ".json")).read_text(encoding="utf-8-sig"))
    rounds = {r["id"]: r for r in exported("tbrounddata")}
    groups = {g["id"]: g for g in exported("tbenemylist")}
    refs = defaultdict(list)
    for scene in exported("tbsceneinfo"):
        assert scene["initialGold"] == 100
        for wave, rid in enumerate(scene["RoundList"], 1):
            for gid in rounds[rid]["EnemyIndexs"]:
                for eid in set(groups[gid]["EnemyIndexs"]):
                    if eid in target_ids:
                        refs[eid].append([scene["id"], wave, rid, gid])
    assert all(refs[e["enemyId"]] and all(r[:3] == [2, e["wave"], e["roundId"]] for r in refs[e["enemyId"]]) for e in edits)
    with zipfile.ZipFile(BytesIO(original)) as zin:
        old_xml = zin.read(SHEET).decode("utf-8")
        new_xml = old_xml
        for edit in edits:
            pattern = re.compile(r'(<(?:\w+:)?c\b[^>]*\br="' + edit["cell"] + r'"[^>]*>)(.*?)(</(?:\w+:)?c>)', re.S)
            matches = list(pattern.finditer(new_xml))
            assert len(matches) == 1, (edit["cell"], len(matches))
            m = matches[0]
            inside = m.group(2)
            assert not re.search(r"<(?:\w+:)?f\b", inside), "Do not replace a formula"
            value = re.search(r'(<(?:\w+:)?v>)([^<]+)(</(?:\w+:)?v>)', inside)
            assert value is not None and Decimal(value.group(2)) == Decimal(str(edit["old"]))
            edit["oldXmlNumber"] = value.group(2)
            replacement = inside[:value.start(2)] + edit["newText"] + inside[value.end(2):]
            new_xml = new_xml[:m.start(2)] + replacement + new_xml[m.end(2):]
        # Removing only authorized numeric values must leave identical XML.
        def stripped(xml):
            for e in edits:
                pattern = re.compile(r'(<(?:\w+:)?c\b[^>]*\br="' + e["cell"] + r'"[^>]*>.*?<(?:\w+:)?v>)[^<]+(</(?:\w+:)?v>)', re.S)
                xml, n = pattern.subn(lambda m: m.group(1) + "AUTHORIZED_HP" + m.group(2), xml)
                assert n == 1
            return xml
        assert stripped(old_xml) == stripped(new_xml), "Unexpected XML changes"
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as zout:
            zout.comment = zin.comment
            for entry in zin.infolist():
                zout.writestr(entry, new_xml.encode("utf-8") if entry.filename == SHEET else zin.read(entry.filename))
        payload = buffer.getvalue()
    after_cells = cells(payload)
    assert before_cells.keys() == after_cells.keys()
    differences = []
    for sheet in before_cells:
        assert before_cells[sheet]["shape"] == after_cells[sheet]["shape"]
        before, after = before_cells[sheet]["values"], after_cells[sheet]["values"]
        differences.extend((sheet, r, c, v, after[r, c]) for (r, c), v in before.items() if v != after[r, c])
    allowed = {(e["sheet"], e["row"], 4): (e["old"], e["new"]) for e in edits}
    assert len(differences) == 61 and all(allowed[s, r, c] == (old, new) for s, r, c, old, new in differences)
    with zipfile.ZipFile(BytesIO(original)) as a, zipfile.ZipFile(BytesIO(payload)) as b:
        assert a.namelist() == b.namelist()
        assert [n for n in a.namelist() if a.read(n) != b.read(n)] == [SHEET]
    OUT.mkdir(parents=True, exist_ok=True)
    # Preserve the actual pre-edit source and all export bytes for post-export checks.
    if not BACKUP.exists():
        with BACKUP.open("xb") as stream:
            stream.write(original)
    (OUT / "before-export").mkdir(exist_ok=True)
    export_state = {}
    for p in (ROOT / "Assets/ConfigJson").glob("*.json"):
        data = p.read_bytes()
        (OUT / "before-export" / p.name).write_bytes(data)
        export_state[p.name] = {"sha256": digest(data), "mtimeNs": p.stat().st_mtime_ns}
    generated_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p.read_bytes()) for p in (ROOT / "Assets/Gen").rglob("*") if p.is_file()}
    manifest = {"status": "prepared", "factor": str(FACTOR), "scope": "L02 W11-W25 ground HP only",
                "source": str(SRC.relative_to(ROOT)).replace("\\", "/"), "sourceBeforeSha256": digest(original),
                "sourceAfterSha256": digest(payload), "backup": str(BACKUP.relative_to(ROOT)).replace("\\", "/"),
                "edits": edits, "changedCells": len(differences), "outsideWhitelistCellChanges": 0,
                "otherXlsxBeforeHashes": base["sourceHashes"], "exportBefore": export_state, "generatedBefore": generated_hashes,
                "referenceProof": dict(refs)}
    (OUT / "prepared-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    assert SRC.read_bytes() == original, "Source changed during preparation"
    staged = OUT / "validated-candidate.xlsx"
    with staged.open("wb") as stream:
        stream.write(payload)
    # Atomic same-volume replacement avoids truncating an OS-mapped original.
    # If the OS denies replacement, the complete original remains untouched.
    os.replace(staged, SRC)
    assert SRC.read_bytes() == payload and cells(SRC.read_bytes()) == after_cells
    other_changes = [p for p, expected in base["sourceHashes"].items() if p != manifest["source"] and digest((ROOT / p).read_bytes()) != expected]
    assert not other_changes, other_changes
    manifest["status"] = "source-applied-awaiting-Luban-export"
    manifest["otherSourceWorkbookChanges"] = other_changes
    (OUT / "applied-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "changedCells": len(edits), "outsideWhitelistCellChanges": 0,
                      "otherSourceWorkbookChanges": other_changes, "W11": [e for e in edits if e["wave"] == 11]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
