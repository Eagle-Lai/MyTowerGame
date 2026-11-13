"""Confirmed third round: L02 W11-W25 ground HP, current post-round-2 values x0.92."""
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import apply_l02_w11w25_ground_hp15_20261110 as precise

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage/l02-ground8-r3-20261110"
PREVIOUS = ROOT / "Library/BalanceStage/l02-ground8-r2-20261110/applied-manifest.json"


def main():
    assert not (OUT / "applied-manifest.json").exists(), "This round has already been applied"
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    original = precise.SRC.read_bytes()
    assert hashlib.sha256(original).hexdigest() == previous["sourceAfterSha256"], "Current source differs from the previous applied version"
    source_hashes = dict(previous["otherXlsxBeforeHashes"])
    source_hashes[previous["source"]] = previous["sourceAfterSha256"]
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in source_hashes.items()), "Another source changed; refresh the baseline before continuing"
    current = precise.cells(original)
    waves = {}
    for entry in previous["edits"]:
        values = current[entry["sheet"]]["values"]
        row = entry["row"]
        assert values[row, 2] == entry["enemyId"] and values[row, 14] == 0
        assert Decimal(str(values[row, 4])) == Decimal(str(entry["new"]))
        wave = waves.setdefault(entry["wave"], {"wave": entry["wave"], "roundId": entry["roundId"], "roster": []})
        wave["roster"].append({"id": entry["enemyId"], "hp": values[row, 4], "isFlying": 0,
                               "resName": entry["enemy"], "hpSource": {k: entry[k] for k in ("file", "sheet", "cell")}})
    assert len(waves) == 15 and sum(len(w["roster"]) for w in waves.values()) == 61
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = {"basis": "User explicitly confirmed another stacked 8%; fresh source cells matching completed round 2",
                "sourceHashes": source_hashes, "waves": [waves[n] for n in sorted(waves)]}
    baseline_path = OUT / "current-baseline.json"
    baseline_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    precise.BASE = baseline_path
    precise.OUT = OUT
    precise.BACKUP = precise.SRC.with_name("EnemyData.xlsx.bak_20261110_before_w11w25_ground_hp8_r3")
    precise.FACTOR = Decimal("0.92")
    precise.main()


if __name__ == "__main__":
    main()
