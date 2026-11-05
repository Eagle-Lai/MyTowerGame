#!/usr/bin/env python3
"""Apply an explicitly reviewed, old-value-guarded list of XLSX cell updates."""

from __future__ import annotations

import argparse
import collections
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}
EXPECTED_LEVELS = set(range(3, 31))
EXPECTED_CELLS = 296
EXPECTED_WORKBOOKS = 28


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def worksheet_member(book: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(book.read("xl/workbook.xml"))
    rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
    targets = {node.attrib["Id"]: node.attrib["Target"]
               for node in rels.findall("pkg:Relationship", NS)}
    for sheet in workbook.findall("main:sheets/main:sheet", NS):
        if sheet.attrib.get("name") != sheet_name:
            continue
        target = targets[sheet.attrib[f"{{{NS['rel']}}}id"]]
        if target.startswith("/"):
            member = PurePosixPath(target.lstrip("/"))
        else:
            member = PurePosixPath("xl") / target
        member = PurePosixPath(os.path.normpath(str(member)).replace("\\", "/"))
        if member.is_absolute() or ".." in member.parts:
            raise ValueError(f"Unsafe worksheet relationship target: {target}")
        return str(member)
    raise ValueError(f"Worksheet not found: {sheet_name}")


def get_cell(xml: bytes, address: str) -> tuple[re.Match[bytes], str, re.Match[bytes]]:
    address_bytes = address.encode("ascii")
    cell_pattern = re.compile(rb"<(?:[A-Za-z_][\w.-]*:)?c\b[^>]*>.*?</(?:[A-Za-z_][\w.-]*:)?c>", re.S)
    matches = []
    for match in cell_pattern.finditer(xml):
        opening = match.group(0).split(b">", 1)[0]
        ref = re.search(rb"\br\s*=\s*([\"'])" + re.escape(address_bytes) + rb"\1", opening)
        if ref:
            matches.append(match)
    if len(matches) != 1:
        raise ValueError(f"Expected one cell {address}, found {len(matches)}")
    cell = matches[0]
    fragment = cell.group(0)
    root = ET.fromstring(fragment)
    if root.tag.split("}")[-1] != "c" or root.attrib.get("r") != address:
        raise ValueError(f"Malformed cell {address}")
    if root.attrib.get("t") != "inlineStr":
        raise ValueError(f"Cell {address} is not an inline string")
    texts = [node for node in root.iter() if node.tag.split("}")[-1] == "t"]
    if len(texts) != 1:
        raise ValueError(f"Cell {address} must contain exactly one text node")
    text_nodes = list(re.finditer(rb"<(?:[A-Za-z_][\w.-]*:)?t\b[^>]*>.*?</(?:[A-Za-z_][\w.-]*:)?t>", fragment, re.S))
    if len(text_nodes) != 1:
        raise ValueError(f"Cell {address} text node is not uniquely locatable")
    return cell, texts[0].text or "", text_nodes[0]


def replace_cell_text(xml: bytes, address: str, expected: str, replacement: str) -> bytes:
    cell, current, text_node = get_cell(xml, address)
    if current != expected:
        raise ValueError(f"Cell {address}: expected old value differs from current data")
    fragment = cell.group(0)
    start, end = text_node.span()
    opening_end = fragment.index(b">", start) + 1
    closing_start = fragment.rindex(b"</", opening_end, end)
    escaped = html.escape(replacement, quote=False).encode("utf-8")
    updated = fragment[:opening_end] + escaped + fragment[closing_start:]
    return xml[:cell.start()] + updated + xml[cell.end():]


def load_air_ids(project_root: Path) -> set[int]:
    checker_path = project_root / ".workbuddy/tools/check_air_spawn_order.py"
    spec = __import__("importlib.util", fromlist=["spec_from_file_location"])
    module_spec = spec.spec_from_file_location("air_spawn_checker", checker_path)
    checker = spec.module_from_spec(module_spec)
    sys.modules[module_spec.name] = checker
    module_spec.loader.exec_module(checker)
    flying_by_id = {}
    for level in range(1, 31):
        path = project_root / f"Luban/Config/Datas/Levels/L{level:02d}/EnemyData.xlsx"
        for record in checker.read_xlsx(path):
            enemy_id = int(record.values["id"])
            is_flying = int(record.values["isFlying"]) != 0
            if enemy_id in flying_by_id and flying_by_id[enemy_id] != is_flying:
                raise ValueError(f"Conflicting isFlying for enemy id={enemy_id} in {path}")
            flying_by_id[enemy_id] = is_flying
    air = {enemy_id for enemy_id, is_flying in flying_by_id.items() if is_flying}
    if not air:
        raise ValueError("No flying enemies found in the current EnemyData source")
    return air


def read_proposal_cell(record: dict, project_root: Path) -> tuple[Path, str, str, str]:
    source = record["source"]
    source_path = str(source["path"]).replace("\\\\", "\\")
    path = Path(source_path)
    if not path.is_absolute():
        path = project_root / path
    path = path.resolve()
    if not path.is_relative_to(project_root.resolve()):
        raise ValueError(f"Cell source escapes project root: {path}")
    address = f"{source['columns']['EnemyIndexs']}{source['row']}"
    return path, source["sheet"], address, str(record["oldValue"])


def inspect_update_set(cells: list[dict], project_root: Path) -> tuple[dict, dict]:
    updates_by_book: dict[Path, dict[str, dict[str, tuple[str, str]]]] = {}
    records_by_key = {}
    levels = set()
    for record in cells:
        level = int(record["level"])
        levels.add(level)
        path, sheet, address, old_value = read_proposal_cell(record, project_root)
        new_value = str(record["proposedValue"])
        key = (path, sheet, address)
        if key in records_by_key:
            raise ValueError(f"Duplicate cell update: {key}")
        old_ids = old_value.split(",")
        new_ids = new_value.split(",")
        if not old_ids or any(not item.isdigit() for item in old_ids + new_ids):
            raise ValueError(f"Invalid enemy ID sequence at {path}:{sheet}!{address}")
        if collections.Counter(old_ids) != collections.Counter(new_ids):
            raise ValueError(f"Enemy ID multiset changes at {path}:{sheet}!{address}")
        records_by_key[key] = record
        updates_by_book.setdefault(path, {}).setdefault(sheet, {})[address] = (old_value, new_value)
    if len(cells) != EXPECTED_CELLS or len(updates_by_book) != EXPECTED_WORKBOOKS or levels != EXPECTED_LEVELS:
        raise ValueError(f"Unexpected proposal scope: cells={len(cells)}, workbooks={len(updates_by_book)}, levels={sorted(levels)}")
    return updates_by_book, records_by_key


def stage_workbook(path: Path, sheets: dict[str, dict[str, tuple[str, str]]], records: dict,
                   stage_root: Path, project_root: Path, air_ids: set[int]) -> tuple[Path, dict[str, bytes]]:
    relative = path.relative_to(project_root.resolve())
    staged = stage_root / relative
    staged.parent.mkdir(parents=True, exist_ok=True)
    changed_members: dict[str, bytes] = {}
    with zipfile.ZipFile(path, "r") as source:
        modifications = {}
        for sheet_name, cell_updates in sheets.items():
            member = worksheet_member(source, sheet_name)
            original_xml = source.read(member)
            changed_xml = original_xml
            for address, (old_value, new_value) in cell_updates.items():
                changed_xml = replace_cell_text(changed_xml, address, old_value, new_value)
                ids = [int(value) for value in new_value.split(",")]
                if any(left in air_ids and right in air_ids for left, right in zip(ids, ids[1:])):
                    raise ValueError(f"Proposed cell still has adjacent air enemies: {path}:{sheet_name}!{address}")
                record = records[(path, sheet_name, address)]
                swaps = record.get("swaps", [])
                if ids and swaps:
                    old_ids = [int(value) for value in old_value.split(",")]
                    if ids[0] != old_ids[0] or ids[-1] != old_ids[-1]:
                        raise ValueError(f"Proposal changes end positions: {path}:{sheet_name}!{address}")
            modifications[member] = changed_xml
            changed_members[member] = changed_xml
        with zipfile.ZipFile(staged, "w") as output:
            for info in source.infolist():
                output.writestr(info, modifications.get(info.filename, source.read(info.filename)))
    with zipfile.ZipFile(path, "r") as original, zipfile.ZipFile(staged, "r") as check:
        if check.testzip() is not None or original.namelist() != check.namelist():
            raise ValueError(f"Staged workbook package is invalid: {path}")
        for name in original.namelist():
            expected = changed_members.get(name, original.read(name))
            if check.read(name) != expected:
                raise ValueError(f"Unexpected workbook content change: {path}:{name}")
    return staged, changed_members


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="commit staged cell changes after full preflight")
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    if proposal.get("applied") is not False:
        raise ValueError("Proposal must be an unapplied review artifact")
    updates, records = inspect_update_set(proposal["cells"], project_root)
    for path in updates:
        expected_hashes = {record["sourceSha256"] for (book, _, _), record in records.items() if book == path}
        if len(expected_hashes) != 1 or sha256(path) not in expected_hashes:
            raise ValueError(f"Workbook hash does not match approved pre-edit baseline: {path}")
    air_ids = load_air_ids(project_root)
    stage_root = args.stage_root.resolve()
    stage_root.mkdir(parents=True, exist_ok=False)
    staged_files = {}
    for path, sheets in sorted(updates.items()):
        staged, _ = stage_workbook(path, sheets, records, stage_root, project_root, air_ids)
        staged_files[path] = staged
    if not args.apply:
        print(json.dumps({"staged": len(staged_files), "cells": len(records), "stageRoot": str(stage_root), "applied": False}, ensure_ascii=False))
        return 0

    rollback = stage_root / "rollback"
    rollback.mkdir()
    committed = []
    try:
        for original, staged in staged_files.items():
            saved = rollback / original.relative_to(project_root)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, saved)
            temporary = original.with_name(original.name + ".air-order.tmp")
            shutil.copy2(staged, temporary)
            os.replace(temporary, original)
            committed.append((original, saved))
    except Exception:
        for original, saved in reversed(committed):
            os.replace(saved, original)
        raise
    for original in staged_files:
        with zipfile.ZipFile(original, "r") as check:
            if check.testzip() is not None:
                raise ValueError(f"Committed workbook failed ZIP validation: {original}")
    print(json.dumps({"staged": len(staged_files), "cells": len(records), "stageRoot": str(stage_root), "applied": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
