"""Restore only the five L02 W15 HP cells changed by the latest adjustment."""
from pathlib import Path
from decimal import Decimal
from io import BytesIO
import hashlib
import json
import os
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-w15-all-enemy-hp20-r3-20261111"
MANIFEST_PATH = OUT / "applied-manifest.json"
SHEET_XML = "xl/worksheets/sheet1.xml"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    source = ROOT / manifest["source"]
    current = source.read_bytes()
    assert sha(current) == manifest["sourceAfterSha256"], "Source changed since the last verified adjustment"
    assert len(manifest["edits"]) == 5 and all("oldXmlNumber" in e for e in manifest["edits"])

    backup = ROOT / (manifest["source"] + ".bak_20261111_before_undo_l02w15_all_enemy_hp20_r3")
    assert not backup.exists(), "Rollback backup already exists; inspect before continuing"

    with zipfile.ZipFile(BytesIO(current)) as archive:
        xml = archive.read(SHEET_XML).decode("utf-8")
        restored_xml = xml
        for edit in manifest["edits"]:
            pattern = re.compile(r'(<(?:\w+:)?c\b[^>]*\br="' + edit["cell"] + r'"[^>]*>)(.*?)(</(?:\w+:)?c>)', re.S)
            matches = list(pattern.finditer(restored_xml))
            assert len(matches) == 1, (edit["cell"], len(matches))
            match = matches[0]
            inner = match.group(2)
            assert not re.search(r"<(?:\w+:)?f\b", inner), "Refusing to modify a formula cell"
            value = re.search(r'(<(?:\w+:)?v>)([^<]+)(</(?:\w+:)?v>)', inner)
            assert value and Decimal(value.group(2)) == Decimal(edit["newText"])
            replacement = inner[:value.start(2)] + edit["oldXmlNumber"] + inner[value.end(2):]
            restored_xml = restored_xml[:match.start(2)] + replacement + restored_xml[match.end(2):]

        def masked(payload):
            for edit in manifest["edits"]:
                pattern = re.compile(r'(<(?:\w+:)?c\b[^>]*\br="' + edit["cell"] + r'"[^>]*>.*?<(?:\w+:)?v>)[^<]+(</(?:\w+:)?v>)', re.S)
                payload, count = pattern.subn(lambda m: m.group(1) + "WHITELIST_HP" + m.group(2), payload)
                assert count == 1
            return payload

        assert masked(xml) == masked(restored_xml), "Rollback changed data outside the five approved HP cells"
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as result:
            result.comment = archive.comment
            for entry in archive.infolist():
                result.writestr(entry, restored_xml.encode("utf-8") if entry.filename == SHEET_XML else archive.read(entry.filename))
        payload = buffer.getvalue()

    backup.write_bytes(current)
    staged = OUT / "rollback-candidate.xlsx"
    staged.write_bytes(payload)
    os.replace(staged, source)
    assert sha(source.read_bytes()) != manifest["sourceAfterSha256"]
    record = {"status": "source-restored-awaiting-Luban-export",
              "reverses": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
              "source": manifest["source"], "sourceBeforeRollbackSha256": sha(current),
              "sourceAfterRollbackSha256": sha(payload),
              "rollbackBackup": str(backup.relative_to(ROOT)).replace("\\", "/"),
              "restoredCellCount": len(manifest["edits"]),
              "restoredValues": [{"enemyId": e["enemyId"], "enemy": e["enemy"],
                                  "cell": e["cell"], "from": e["newText"],
                                  "to": e["oldXmlNumber"]} for e in manifest["edits"]],
              "outsideWhitelistChanges": 0}
    (OUT / "rollback-manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
