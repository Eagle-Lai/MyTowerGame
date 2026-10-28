#!/usr/bin/env python3
"""Rollback the authorized semantic TowerInfo.xlsx cell edits.

The script refuses to write if any current cell differs from the recorded
after-value. It is intentionally delivered without being executed here.
Requires openpyxl in the caller's Python environment.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError as exc:
    raise SystemExit("rollback.py requires openpyxl: %s" % (exc,))

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "Luban" / "Config" / "Datas" / "TowerInfo.xlsx"
CHANGES = Path(__file__).with_name("changes.json")

def equal(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-12)
    return a == b

payload = json.loads(CHANGES.read_text(encoding="utf-8"))
changes = payload["changes"]
book = openpyxl.load_workbook(TARGET)
errors = []
for row in changes:
    ws = book[row["sheet"]]
    actual = ws[row["cell"]].value
    if not equal(actual, row["newValue"]):
        errors.append(f'{row["sheet"]}!{row["cell"]}: expected current {row["newValue"]!r}, found {actual!r}')
if errors:
    raise SystemExit("Refusing rollback; current values do not match after.xlsx:
" + "
".join(errors))
for row in changes:
    book[row["sheet"]][row["cell"]] = row["oldValue"]
book.save(TARGET)
print(f"Rolled back {len(changes)} semantic cells in {TARGET}")
