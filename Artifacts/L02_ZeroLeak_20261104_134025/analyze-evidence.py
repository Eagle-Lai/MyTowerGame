"""Read-only configuration/evidence analysis; writes reports only beside this file."""
import collections
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def current(name):
    return json.loads((ROOT / f"Assets/ConfigJson/{name}.json").read_text(encoding="utf-8-sig"))


def head(name):
    return json.loads(subprocess.check_output(["git", "show", f"HEAD:Assets/ConfigJson/{name}.json"], cwd=ROOT))


def mapped(rows):
    return {row["id"]: row for row in rows}


scene = next(row for row in current("tbsceneinfo") if row["id"] == 2)
enemies, old_enemies = mapped(current("tbenemydata")), mapped(head("tbenemydata"))
lists, old_lists = mapped(current("tbenemylist")), mapped(head("tbenemylist"))
rounds, old_rounds = mapped(current("tbrounddata")), mapped(head("tbrounddata"))
wave_rows, hp_rows = [], []
for wave, round_id in enumerate(scene["RoundList"], 1):
    row, old = rounds[round_id], old_rounds[round_id]
    ids = [eid for list_id in row["EnemyIndexs"] for eid in lists[list_id]["EnemyIndexs"]]
    old_ids = [eid for list_id in old["EnemyIndexs"] for eid in old_lists[list_id]["EnemyIndexs"]]
    counts = collections.Counter(eid % 10 for eid in ids)
    intervals = [lists[list_id]["enemyInterval"] for list_id in row["EnemyIndexs"]]
    wave_rows.append(dict(wave=wave, roundId=round_id,
        status="retained W1-W4" if wave <= 4 else "this request W5-W25",
        oldCountAtHEAD=len(old_ids), count=len(ids), crawler=counts[0], runner=counts[1],
        tank=counts[2], shield=counts[3], boss=counts[4], flyer=counts[5],
        enemyIntervalMs=intervals[0] if len(set(intervals)) == 1 else intervals,
        oldClearGoldAtHEAD=old["rewardGold"], clearGold=row["rewardGold"], waveType=row["waveType"],
        theoreticalKillGold=round(sum(enemies[eid]["reward"] for eid in ids), 6)))
    for eid in sorted(set(ids)):
        enemy, old_enemy = enemies[eid], old_enemies[eid]
        hp_rows.append(dict(wave=wave, enemyId=eid, name=enemy["name"], isFlying=enemy["isFlying"],
            oldHpAtHEAD=old_enemy["hp"], hp=enemy["hp"], armor=enemy["armor"],
            speed=enemy["speed"], killGold=enemy["reward"], levelId=enemy["levelId"]))

for name, rows in [("wave-values.csv", wave_rows), ("enemy-values.csv", hp_rows)]:
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

summary = dict(enemyCount=sum(row["count"] for row in wave_rows),
    enemyCountW05W25=sum(row["count"] for row in wave_rows[4:]),
    clearGold=sum(row["clearGold"] for row in wave_rows),
    clearGoldW05W25=sum(row["clearGold"] for row in wave_rows[4:]),
    theoreticalKillGold=round(sum(row["theoreticalKillGold"] for row in wave_rows), 6),
    initialGold=scene["initialGold"], rows=wave_rows)
save("configuration-summary.json", summary)

scope, diffs = {}, {}
for name in ["tbenemydata", "tbenemylist", "tbrounddata"]:
    old, new = head(name), current(name)
    old_map, new_map = mapped(old), mapped(new)
    changes = []
    for row_id in sorted(old_map.keys() | new_map.keys()):
        a, b = old_map.get(row_id, {}), new_map.get(row_id, {})
        if a != b:
            changes.append(dict(id=row_id, fields={key: dict(old=a.get(key), new=b.get(key))
                for key in sorted(a.keys() | b.keys()) if a.get(key) != b.get(key)}))
    allowed = set(scene["RoundList"]) if name != "tbenemydata" else {eid for eid in enemies if 6000000 <= eid < 7000000}
    diffs[name] = dict(oldRows=len(old), newRows=len(new), changedRows=len(changes),
        changedFields=dict(collections.Counter(key for row in changes for key in row["fields"])), changes=changes)
    scope[name] = dict(oldRows=len(old), newRows=len(new), changedRows=len(changes),
        changedFields=diffs[name]["changedFields"], outsideL02ChangedIds=[row["id"] for row in changes if row["id"] not in allowed])
source_changes = subprocess.check_output(["git", "diff", "--name-only", "--", "Luban/Config/Datas/Levels"], cwd=ROOT, text=True).splitlines()
scope["sourceTablesChangedVsHEAD"] = source_changes
scope["otherLevelSourceChanges"] = [path for path in source_changes if not path.startswith("Luban/Config/Datas/Levels/L02/")]
scope["comparisonNote"] = "HEAD also includes the previously approved W1-W4 edits; this request retained them."
save("config-diff.json", diffs)
save("scope-check.json", scope)

baseline = json.loads((OUT / "protected-baseline.json").read_text(encoding="utf-8-sig"))
mismatches = []
for item in baseline:
    path = ROOT / item["path"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.exists() else "MISSING"
    if actual != item["sha256"]:
        mismatches.append(dict(path=item["path"], expected=item["sha256"], actual=actual))
frozen = dict(checkedUtc=datetime.now(timezone.utc).isoformat(), fileCount=len(baseline),
    mismatches=mismatches, baselineNote="414-file baseline was created during attempt02, not before attempt01; the three L02 source hashes were also recorded separately before testing.")
save("protected-check.json", frozen)

attempt_summaries = []
for directory in [OUT] + sorted(OUT.glob("attempt*")):
    if not directory.is_dir() or not (directory / "test-context.json").exists():
        continue
    state_path = directory / "final-layout.json"
    if not state_path.exists():
        state_path = directory / "first-leak-state.json"
    record = dict(attempt="attempt01" if directory == OUT else directory.name)
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        record.update({key: state.get(key) for key in ["state", "wave", "hp", "killed", "leaked", "gold", "gameSeconds", "combatSeconds", "elapsedSeconds", "manualSimulation"]})
        record["towerCount"] = len(state["towers"])
        record["pathNodes"] = len(state["path"])
    result_path = directory / "result.json"
    if result_path.exists():
        record["result"] = json.loads(result_path.read_text(encoding="utf-8-sig"))
    attempt_summaries.append(record)
save("attempt-summary.json", attempt_summaries)
print(json.dumps(dict(configuration={key: value for key, value in summary.items() if key != "rows"},
    scope=scope, frozen=frozen, attempts=attempt_summaries), ensure_ascii=False, indent=2))
