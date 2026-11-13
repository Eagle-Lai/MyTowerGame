"""Read current L02 source tables; write diagnostics outside source/export directories."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import struct
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Library/BalanceStage" / ("l02-w11-review-" + datetime.now().strftime("%Y%m%d-%H%M%S"))


def read_table(name):
    path = ROOT / "Luban/Config/Datas/Levels/L02" / (name + ".xlsx")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
    sheet = wb.worksheets[0]
    rows = list(sheet.values)
    records = {}
    locations = {}
    for rownum, row in enumerate(rows[3:], 4):
        if len(row) < 2 or not isinstance(row[1], int):
            continue
        record = {h: row[k] for k, h in enumerate(rows[0]) if h and h != "##"}
        assert record["id"] not in records
        records[record["id"]] = record
        locations[record["id"]] = {
            h: {"file": str(path.relative_to(ROOT)).replace("\\", "/"), "sheet": sheet.title,
                "cell": openpyxl.utils.get_column_letter(k + 1) + str(rownum)}
            for k, h in enumerate(rows[0]) if h and h != "##"
        }
    wb.close()
    return records, locations


def ids(value):
    return [int(x) for x in str(value).split(",")]


def f32(value):
    return struct.unpack("f", struct.pack("f", value))[0]


def rolling(timeline, enemies, flying, window=10):
    best = total = 0.0
    left = 0
    for right, (time, enemy_id, _) in enumerate(timeline):
        e = enemies[enemy_id]
        if bool(e["isFlying"]) == flying:
            total += e["hp"] / (1 - e["armor"])
        # Half-open window [t, t+window), avoiding double-counting exact boundaries.
        while timeline[left][0] <= time - window + 1e-9:
            old = enemies[timeline[left][1]]
            if bool(old["isFlying"]) == flying:
                total -= old["hp"] / (1 - old["armor"])
            left += 1
        best = max(best, total)
    return best / window


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    source_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (ROOT / "Luban/Config/Datas").rglob("*.xlsx")}
    tables, cells = {}, {}
    for name in ("EnemyData", "EnemyList", "RoundData", "SceneInfo", "TowerInfo", "BulletData", "LevelRules"):
        tables[name], cells[name] = read_table(name)
    scene = tables["SceneInfo"][2]
    assert scene["initialGold"] == 100
    enemies = tables["EnemyData"]
    exported = {name: {r["id"]: r for r in json.loads((ROOT / "Assets/ConfigJson" / ("tb" + name.lower() + ".json")).read_text(encoding="utf-8-sig"))}
                for name in tables}
    mismatches = []
    for name, rows in tables.items():
        for record_id, row in rows.items():
            output = exported[name].get(record_id)
            if output is None:
                mismatches.append([name, record_id, "missing"])
                continue
            for field, value in row.items():
                if field not in output or field in ("desc", "name"):
                    continue
                actual = output[field]
                if isinstance(actual, dict) and set(actual) == {"x", "y", "z"} and isinstance(value, str):
                    expected = dict(zip(("x", "y", "z"), (float(v) for v in value.split(","))))
                elif isinstance(actual, str) and value is None:
                    expected = ""
                elif isinstance(actual, list) and isinstance(value, str):
                    expected = ids(value)
                else:
                    expected = value
                if isinstance(expected, float) and isinstance(actual, (float, int)):
                    equal = math.isclose(f32(expected), actual, rel_tol=1e-7, abs_tol=1e-7)
                else:
                    equal = expected == actual
                if not equal:
                    mismatches.append([name, record_id, field, expected, actual])
    cumulative = float(scene["initialGold"])
    waves = []
    all_births = []
    for wave, rid in enumerate(ids(scene["RoundList"]), 1):
        r = tables["RoundData"][rid]
        timeline = []
        offset = max(0, r["interval"]) / 1000
        for gid in ids(r["EnemyIndexs"]):
            g = tables["EnemyList"][gid]
            seq = ids(g["EnemyIndexs"])
            gap = (g["enemyInterval"] if g["enemyInterval"] > 0 else 200) / 1000
            start = offset + g["interval"] / 1000
            timeline.extend((start + k * gap, eid, gid) for k, eid in enumerate(seq))
            offset = max(offset, start + gap * max(1, len(seq) - 1) + gap)
        timeline.sort()
        span = timeline[-1][0] - timeline[0][0]
        count = Counter(t[1] for t in timeline)
        roster = [{**enemies[eid], "count": n, "hpSource": cells["EnemyData"][eid]["hp"]} for eid, n in count.items()]
        channels = {}
        for flying, channel in ((False, "ground"), (True, "air")):
            selected = [e for e in roster if bool(e["isFlying"]) == flying]
            ehp = sum(e["count"] * e["hp"] / (1 - e["armor"]) for e in selected)
            channels[channel] = {"count": sum(e["count"] for e in selected), "ehp": ehp,
                                 "meanEhpPerSecond": ehp / span, "peak10sEhpPerSecond": rolling(timeline, enemies, flying),
                                 "totalPotentialLeakDamage": sum(e["count"] * max(1, e["damageToPlayer"]) for e in selected)}
        income = sum(e["count"] * e["reward"] for e in roster)
        waves.append({"wave": wave, "roundId": rid, "waveType": r["waveType"], "spawnSpanSeconds": span,
                      "groupIntervalsMs": [tables["EnemyList"][gid]["enemyInterval"] for gid in ids(r["EnemyIndexs"])],
                      "total": len(timeline), "prewaveTheoreticalEarned": cumulative,
                      "killIncome": income, "roundReward": r["rewardGold"], "channels": channels, "roster": roster})
        all_births.extend({"wave": wave, "roundId": rid, "group": gid, "position": pos + 1, "enemyId": eid}
                          for pos, (_, eid, gid) in enumerate(timeline))
        cumulative += income + r["rewardGold"]
    violations = [[a, b] for a, b in zip(all_births, all_births[1:]) if enemies[a["enemyId"]]["isFlying"] and enemies[b["enemyId"]]["isFlying"]]
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in source_hashes.items())
    result = {"capturedAtUtc": datetime.now(timezone.utc).isoformat(), "scope": "L02 W11-W25 analysis only",
              "sourceWrites": 0, "exportWrites": 0, "sourceHashes": source_hashes,
              "exportMismatches": mismatches, "airAdjacentViolations": violations,
              "fullKillTheoreticalEarned": cumulative, "tables": tables, "waves": waves,
              "limitations": "Arrival pressure only. No measured tower capacity, path contention or combat outcome inferred."}
    (OUT / "current-baseline.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OUTPUT", str(OUT))
    print("SOURCE_EXPORT_MISMATCHES", json.dumps(mismatches[:20], ensure_ascii=False), "TOTAL", len(mismatches))
    print("AIR_ADJACENCIES", len(violations))
    print("wave round total interval span groundEhpRate airEhpRate ground10sPeak air10sPeak prewaveEarned")
    for w in waves[8:]:
        g, a = w["channels"]["ground"], w["channels"]["air"]
        print(w["wave"], w["roundId"], w["total"], w["groupIntervalsMs"], round(w["spawnSpanSeconds"], 2),
              *[round(v, 2) for v in (g["meanEhpPerSecond"], a["meanEhpPerSecond"], g["peak10sEhpPerSecond"], a["peak10sEhpPerSecond"], w["prewaveTheoreticalEarned"])])
    w10, w11 = waves[9:11]
    print("W11_VS_W10", json.dumps({c: {"meanRatio": w11["channels"][c]["meanEhpPerSecond"] / w10["channels"][c]["meanEhpPerSecond"],
                                           "peakRatio": w11["channels"][c]["peak10sEhpPerSecond"] / w10["channels"][c]["peak10sEhpPerSecond"]}
                                     for c in ("ground", "air")}))
    print("W11_ROSTER", json.dumps(w11["roster"], ensure_ascii=False))


if __name__ == "__main__":
    main()
