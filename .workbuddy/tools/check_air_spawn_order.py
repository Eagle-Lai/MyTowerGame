#!/usr/bin/env python3
"""Read-only check for adjacent flying enemies in current Luban XLSX/JSON.

No source table, exported asset, or Unity state is ever written. Exit 0 means
both the references and the selected data satisfy the rule; exit 1 means a
violation or malformed/missing input. Report JSON goes to stdout only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
TABLES = {"SceneInfo": "tbsceneinfo", "RoundData": "tbrounddata",
          "EnemyList": "tbenemylist", "EnemyData": "tbenemydata"}
FIELDS = {"SceneInfo": ("id", "RoundList"),
          "RoundData": ("id", "EnemyIndexs", "interval"),
          "EnemyList": ("id", "EnemyIndexs", "interval", "enemyInterval"),
          "EnemyData": ("id", "isFlying")}
LISTS = {"RoundList", "EnemyIndexs"}


@dataclass
class Record:
    values: dict
    source: dict


def integer(value, label):
    if isinstance(value, bool):
        raise ValueError(f"{label}: boolean is not an integer")
    number = Decimal(str(value))
    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError(f"{label}: invalid integer {value!r}")
    return int(number)


def sequence(value, label):
    if value is None or value == "":
        return []
    items = value if isinstance(value, list) else str(value).split(",")
    return [integer(item, label) for item in items]


def read_xlsx(path):
    """Read physical cells, preserving source addresses, without an Excel writer."""
    with ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(n.itertext()) for n in
                       ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {r.attrib["Id"]: r.attrib["Target"] for r in relationships}
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        for sheet in workbook.findall("s:sheets/s:sheet", NS):
            target = targets[sheet.attrib[f"{{{REL_NS}}}id"]]
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            sheet_xml = ET.fromstring(archive.read(target))
            headers = None
            for row in sheet_xml.findall("s:sheetData/s:row", NS):
                cells = {}
                formulas = set()
                for cell in row.findall("s:c", NS):
                    address = cell.attrib["r"]
                    column = "".join(c for c in address if c.isalpha())
                    node = cell.find("s:v", NS)
                    raw = node.text if node is not None else None
                    kind = cell.attrib.get("t")
                    if kind == "s":
                        value = strings[int(raw)] if raw is not None else None
                    elif kind == "inlineStr":
                        inline = cell.find("s:is", NS)
                        value = "".join(inline.itertext()) if inline is not None else None
                    else:
                        value = raw
                    cells[column] = value
                    if cell.find("s:f", NS) is not None:
                        formulas.add(column)
                if headers is None:
                    if not any(v in ("id", "full_name") for v in cells.values()):
                        continue
                    headers = cells
                    continue
                if str(cells.get("A", "")).startswith("##"):
                    continue
                values = {name: cells.get(col) for col, name in headers.items()
                          if name and not name.startswith("##")}
                if not any(v is not None for v in values.values()):
                    continue
                active_formulas = [headers[c] for c in formulas if c in headers]
                if active_formulas:
                    raise ValueError(f"{path}: {sheet.attrib['name']}!{row.attrib['r']}: "
                                     f"formula requires manual review: {active_formulas}")
                yield Record(values, {"path": str(path), "sheet": sheet.attrib["name"],
                                      "row": int(row.attrib["r"]),
                                      "columns": {v: k for k, v in headers.items() if v}})


def normalize(record, table):
    values = record.values
    for field in FIELDS[table]:
        if field not in values or values[field] is None:
            raise ValueError(f"{record.source}: missing {field}")
        if field in LISTS:
            values[field] = sequence(values[field], field)
        elif field == "enemyInterval":
            number = Decimal(str(values[field]))
            if not number.is_finite():
                raise ValueError(f"{record.source}: invalid {field}")
            values[field] = number
        else:
            values[field] = integer(values[field], field)
    if values["id"] <= 0:
        raise ValueError(f"{record.source}: id must be positive")
    if table in ("RoundData", "EnemyList") and values["interval"] < 0:
        raise ValueError(f"{record.source}: negative interval")
    if table == "EnemyList" and values["enemyInterval"] <= 0:
        raise ValueError(f"{record.source}: enemyInterval must be positive")
    return record


def load_data(root, kind):
    errors = []
    db = {t: {} for t in TABLES}
    data_dir = root / "Luban/Config/Datas"
    if kind == "xlsx":
        registry_path = data_dir / "__tables__.xlsx"
        try:
            registry = {r.values.get("full_name"): r.values for r in read_xlsx(registry_path)}
            for table in TABLES:
                expected = {f"Levels/L{n:02d}/{table}.xlsx" for n in range(1, 31)}
                registered = {s.strip().replace("\\", "/") for s in
                              str(registry.get("TB" + table, {}).get("input", "")).split(",")}
                if registered != expected:
                    errors.append(f"{registry_path}: unexpected inputs for TB{table}")
        except (OSError, ValueError, KeyError, ET.ParseError, BadZipFile) as exc:
            errors.append(f"{registry_path}: {exc}")
    for table, exported in TABLES.items():
        paths = ([data_dir / f"Levels/L{n:02d}/{table}.xlsx" for n in range(1, 31)]
                 if kind == "xlsx" else [root / "Assets/ConfigJson" / (exported + ".json")])
        for path in paths:
            try:
                if kind == "xlsx":
                    records = list(read_xlsx(path))
                else:
                    values = json.loads(path.read_text(encoding="utf-8-sig"))
                    if not isinstance(values, list):
                        raise ValueError("expected a JSON array")
                    records = [Record(v, {"path": str(path), "index": i}) for i, v in enumerate(values)]
                if not records:
                    raise ValueError("no data rows")
                for record in records:
                    record = normalize(record, table)
                    key = record.values["id"]
                    if key in db[table]:
                        errors.append(f"{path}: duplicate {table} id={key}")
                    else:
                        db[table][key] = record
            except (OSError, ValueError, KeyError, TypeError, InvalidOperation, ET.ParseError, BadZipFile) as exc:
                errors.append(f"{path}: {exc}")
    missing_levels = set(range(1, 31)) - db["SceneInfo"].keys()
    if missing_levels:
        errors.append(f"missing levels: {sorted(missing_levels)}")
    return db, errors


def inspect_data(db, levels):
    errors, pairs = [], []
    air_count = 0
    checked_waves = 0
    affected_waves = set()
    air_by_name = Counter()
    for level in levels:
        scene = db["SceneInfo"].get(level)
        if scene is None:
            errors.append(f"L{level:02d}: missing SceneInfo")
            continue
        previous = None
        round_ids = scene.values["RoundList"]
        if not round_ids:
            errors.append(f"L{level:02d}: empty RoundList")
        if len(round_ids) != len(set(round_ids)):
            errors.append(f"L{level:02d}: repeated round reference")
        for wave, round_id in enumerate(round_ids, 1):
            round_row = db["RoundData"].get(round_id)
            if round_row is None:
                errors.append(f"L{level:02d} W{wave}: missing roundId={round_id}")
                previous = None
                continue
            checked_waves += 1
            offset = Decimal(round_row.values["interval"])
            entries = []
            group_ids = round_row.values["EnemyIndexs"]
            if not group_ids:
                errors.append(f"L{level:02d} W{wave}: empty group list")
                previous = None
            if len(group_ids) != len(set(group_ids)):
                errors.append(f"L{level:02d} W{wave}: repeated group reference")
            for group_id in group_ids:
                group = db["EnemyList"].get(group_id)
                if group is None:
                    errors.append(f"L{level:02d} W{wave}: missing groupId={group_id}")
                    entries.append(None)
                    continue
                ids = group.values["EnemyIndexs"]
                if not ids:
                    errors.append(f"L{level:02d} W{wave}: groupId={group_id} is empty")
                    entries.append(None)
                    continue
                gap = Decimal(group.values["enemyInterval"])
                if gap <= 0:
                    errors.append(f"L{level:02d} W{wave}: groupId={group_id} has invalid interval")
                    entries.append(None)
                    continue
                start = offset + group.values["interval"]
                for index, enemy_id in enumerate(ids, 1):
                    enemy = db["EnemyData"].get(enemy_id)
                    if enemy is None:
                        errors.append(f"L{level:02d} W{wave}: groupId={group_id}, "
                                      f"position={index}, missing enemyId={enemy_id}")
                    entries.append({"level": level, "wave": wave, "roundId": round_id,
                                    "groupId": group_id, "positionInGroup": index,
                                    "enemyId": enemy_id, "air": enemy.values["isFlying"] != 0 if enemy else None,
                                    "name": enemy.values.get("name", "") if enemy else "",
                                    "timeMs": start + gap * (index - 1), "source": group.source})
                offset = max(offset, start + gap * max(1, len(ids) - 1) + gap)
            # Positive gaps and serialized groups match WaveManager.BeginRound's order.
            # Missing inputs break adjacency and remain errors rather than a false pass.
            for position, entry in enumerate(entries, 1):
                if entry is None or entry["air"] is None:
                    previous = None
                    continue
                entry["positionInWave"] = position
                if entry["air"]:
                    air_count += 1
                    air_by_name[entry["name"]] += 1
                    if previous is not None and previous["air"]:
                        boundary = ("round" if previous["roundId"] != entry["roundId"] else
                                    "group" if previous["groupId"] != entry["groupId"] else "within_group")
                        pairs.append({"level": level, "wave": wave, "boundary": boundary,
                                      "first": previous.copy(), "second": entry.copy(),
                                      "gapMs": None if boundary == "round" else entry["timeMs"] - previous["timeMs"]})
                        affected_waves.add((level, wave))
                previous = entry
    return {"errors": errors, "airCount": air_count, "airByName": dict(air_by_name),
            "checkedWaves": checked_waves, "affectedWaveCount": len(affected_waves),
            "pairCount": len(pairs), "pairs": pairs}


def compare_data(first, second, levels):
    errors = []
    # Global IDs/references must match as well: a stale export is never a pass.
    for table in TABLES:
        if first[table].keys() != second[table].keys():
            errors.append(f"source/export ID sets differ: {table}")
        for key in first[table].keys() & second[table].keys():
            for field in FIELDS[table]:
                if first[table][key].values.get(field) != second[table][key].values.get(field):
                    errors.append(f"source/export differ: {table} id={key} field={field}")
    return errors


def source_cell(entry):
    source = entry["source"]
    if "row" in source:
        column = source["columns"]["EnemyIndexs"]
        return f"{source['path']} [{source['sheet']}!{column}{source['row']}]"
    return f"{source['path']} [index={source['index']}]"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source", choices=("xlsx", "json", "both"), default="both")
    parser.add_argument("--levels", nargs="+", type=int, default=list(range(1, 31)))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--max-details", type=int, default=20,
                        help="text detail limit; JSON always includes every violation")
    args = parser.parse_args(argv)
    if any(level not in range(1, 31) for level in args.levels):
        parser.error("levels must be in 1..30")
    selected = sorted(set(args.levels))
    kinds = ("xlsx", "json") if args.source == "both" else (args.source,)
    datasets, reports = {}, {}
    for kind in kinds:
        data, load_errors = load_data(args.root.resolve(), kind)
        datasets[kind] = data
        report = inspect_data(data, selected)
        report["errors"][:0] = load_errors
        reports[kind] = report
    differences = compare_data(datasets["xlsx"], datasets["json"], selected) if len(kinds) == 2 else []
    valid = not differences and all(not r["errors"] and not r["pairCount"] for r in reports.values())
    result = {"ok": valid, "root": str(args.root.resolve()), "levels": selected,
              "sourceExportDifferences": differences, "reports": reports}
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2,
                         default=lambda value: float(value) if isinstance(value, Decimal) else str(value)))
    else:
        for kind, report in reports.items():
            print(f"[{kind}] waves={report['checkedWaves']}, air={report['airCount']}, "
                  f"adjacent_air_pairs={report['pairCount']}, affected_waves={report['affectedWaveCount']}, "
                  f"input_errors={len(report['errors'])}")
            for error in report["errors"][:max(0, args.max_details)]:
                print("  ERROR: " + error)
            for pair in report["pairs"][:max(0, args.max_details)]:
                a, b = pair["first"], pair["second"]
                print(f"  L{pair['level']:02d} W{pair['wave']} roundId={b['roundId']} "
                      f"{pair['boundary']}: {a['groupId']}:{a['positionInGroup']} "
                      f"id={a['enemyId']} -> {b['groupId']}:{b['positionInGroup']} "
                      f"id={b['enemyId']}, gapMs={pair['gapMs']}")
                print("    " + source_cell(a))
                if a["source"] != b["source"]:
                    print("    " + source_cell(b))
        for difference in differences[:max(0, args.max_details)]:
            print("  ERROR: " + difference)
        print("PASS" if valid else "FAIL: adjacent flying enemies or invalid/stale input")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
