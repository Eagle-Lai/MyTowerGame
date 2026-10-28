#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "../..");
const rel = "Luban/Config/Datas/TowerInfo.xlsx";
const current = path.join(ROOT, rel);
const out = path.join(ROOT, "Docs", "Balance_TowerSystem", "authorized_tower_patch_20261027");
const before = path.join(out, "before.xlsx");
const after = path.join(out, "after.xlsx");
fs.mkdirSync(out, { recursive: true });

function xmlText(file, entry) {
  return execFileSync("tar", ["-xOf", file, entry], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024, stdio: ["ignore", "pipe", "ignore"] });
}
function xmlTextBuffer(file, entry) {
  return execFileSync("tar", ["-xOf", file, entry], { maxBuffer: 64 * 1024 * 1024, stdio: ["ignore", "pipe", "ignore"] });
}
function decode(s) {
  if (s == null) return null;
  return s.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, "&");
}
function attrs(s) {
  const a = {};
  for (const m of s.matchAll(/([A-Za-z_:][\w:.-]*)=(?:"([^"]*)"|'([^']*)')/g)) a[m[1]] = m[2] ?? m[3] ?? "";
  return a;
}
function sharedStrings(file) {
  let xml;
  try { xml = xmlText(file, "xl/sharedStrings.xml"); } catch { return []; }
  const out = [];
  for (const m of xml.matchAll(/<si(?:\s[^>]*)?>([\s\S]*?)<\/si>/g)) {
    const parts = [...m[1].matchAll(/<t(?:\s[^>]*)?>([\s\S]*?)<\/t>/g)].map(x => decode(x[1]) ?? "");
    out.push(parts.join(""));
  }
  return out;
}
function cells(file, entry, shared) {
  const xml = xmlText(file, entry), map = new Map();
  for (const m of xml.matchAll(/<c\b([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g)) {
    const a = attrs(m[1]), body = m[2] ?? "", ref = a.r;
    if (!ref) continue;
    const vm = body.match(/<v(?:\s[^>]*)?>([\s\S]*?)<\/v>/), fm = body.match(/<f(?:\s[^>]*)?>([\s\S]*?)<\/f>/), tm = body.match(/<t(?:\s[^>]*)?>([\s\S]*?)<\/t>/);
    const raw = vm ? decode(vm[1]) : (tm ? decode(tm[1]) : null);
    let value = raw;
    if (a.t === "s" && raw != null) value = shared[Number(raw)] ?? raw;
    const type = a.t === "s" || a.t === "inlineStr" ? "string" : "number";
    if (type === "number" && value != null && value !== "" && /^[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?$/.test(String(value))) value = Number(value);
    map.set(ref, { ref, type, style: a.s ?? null, value, formula: fm ? decode(fm[1]) : null, raw });
  }
  return map;
}
function workbook(file) {
  const shared = sharedStrings(file), sheets = {};
  for (let i = 1; i <= 20; i++) {
    const entry = `xl/worksheets/sheet${i}.xml`;
    try { sheets[`Sheet${i}`] = cells(file, entry, shared); } catch { break; }
  }
  return sheets;
}
function semantic(c) {
  return c ? JSON.stringify({ type: c.type, value: c.value, formula: c.formula }) : "<missing>";
}
function sha(file) {
  const b = fs.readFileSync(file);
  return crypto.createHash("sha256").update(b).digest("hex");
}
function csvCell(v) {
  const s = v == null ? "" : String(v);
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}

const beforeBuffer = execFileSync("git", ["show", `HEAD:${rel}`], { maxBuffer: 64 * 1024 * 1024 });
fs.writeFileSync(before, beforeBuffer);
fs.copyFileSync(current, after);
const oldBook = workbook(before), newBook = workbook(after), rows = [];
for (const sheet of new Set([...Object.keys(oldBook), ...Object.keys(newBook)])) {
  const oldCells = oldBook[sheet] ?? new Map(), newCells = newBook[sheet] ?? new Map();
  for (const ref of new Set([...oldCells.keys(), ...newCells.keys()])) {
    const o = oldCells.get(ref), n = newCells.get(ref);
    if (semantic(o) === semantic(n)) continue;
    rows.push({ sheet, cell: ref, oldValue: o?.value ?? null, newValue: n?.value ?? null, oldType: o?.type ?? null, newType: n?.type ?? null, oldFormula: o?.formula ?? null, newFormula: n?.formula ?? null, oldStyle: o?.style ?? null, newStyle: n?.style ?? null });
  }
}
rows.sort((a, b) => a.sheet.localeCompare(b.sheet) || a.cell.localeCompare(b.cell, undefined, { numeric: true }));
const metadata = {
  generatedAt: new Date().toISOString(),
  source: rel,
  baseRef: "HEAD",
  beforeSha256: sha(before), afterSha256: sha(after),
  changedCellCount: rows.length,
  authorization: "User authorized code-assisted point edits to TowerInfo.xlsx only; protected level/enemy/source-export restrictions remain in force.",
  lubanExportExecuted: false,
  protectedFilesUntouchedByThisPatch: ["Luban/Config/Datas/Levels/**", "Luban/Config/Datas/EnemyData.xlsx", "Luban/Config/Datas/__tables__.xlsx", "Assets/ConfigJson/**", "Assets/Gen/**"]
};
fs.writeFileSync(path.join(out, "changes.json"), JSON.stringify({ metadata, changes: rows }, null, 2) + "\n", "utf8");
const headers = ["sheet", "cell", "oldValue", "newValue", "oldType", "newType", "oldFormula", "newFormula", "oldStyle", "newStyle"];
fs.writeFileSync(path.join(out, "changes.csv"), [headers.join(","), ...rows.map(r => headers.map(h => csvCell(r[h])).join(","))].join("\n") + "\n", "utf8");
const rollback = `#!/usr/bin/env python3
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
    raise SystemExit("Refusing rollback; current values do not match after.xlsx:\n" + "\n".join(errors))
for row in changes:
    book[row["sheet"]][row["cell"]] = row["oldValue"]
book.save(TARGET)
print(f"Rolled back {len(changes)} semantic cells in {TARGET}")
`;
fs.writeFileSync(path.join(out, "rollback.py"), rollback, "utf8");
const mdRows = rows.map(r => `| ${r.sheet}!${r.cell} | ${String(r.oldValue ?? "").replaceAll("|", "/")} | ${String(r.newValue ?? "").replaceAll("|", "/")} |`);
const readme = `# Authorized TowerInfo point patch — 2026-10-27

This package records the code-assisted, point edits already present in the workspace copy of \`Luban/Config/Datas/TowerInfo.xlsx\`. The user authorized these TowerInfo edits while keeping the project rule against bulk rewriting level tables, \`EnemyData.xlsx\`, \`__tables__.xlsx\`, and generated Luban outputs.

## Contents

- \`before.xlsx\`: exact \`git show HEAD:${rel}\` bytes.
- \`after.xlsx\`: exact current workspace bytes.
- \`changes.json\` / \`changes.csv\`: ${rows.length} semantic value changes, compared by sheet/cell/value/formula. Presentation-only XLSX style/serialization differences are not treated as balance edits.
- \`rollback.py\`: optional rollback. It first verifies every current cell equals its recorded \`newValue\`; any mismatch aborts without writing. It was not executed because no usable Python runtime is installed in this environment.

## Integrity and scope

- before SHA-256: \`${metadata.beforeSha256}\`
- after SHA-256: \`${metadata.afterSha256}\`
- Luban export: **not executed**.
- This package does not modify \`Assets/ConfigJson/**\` or \`Assets/Gen/**\`; it does not modify level tables, \`EnemyData.xlsx\`, or \`__tables__.xlsx\`.
- The formal balance reports remain offline derived/simulated evidence. The current formal tower table still fails compactness in the offline simulation.

## Semantic cell changes

| Cell | Before | After |
|---|---:|---:|
${mdRows.join("\n")}

To use the rollback script from the project root, run \`python Docs/Balance_TowerSystem/authorized_tower_patch_20261027/rollback.py\` only after reviewing the package and ensuring the current cells still match the recorded after-values.
`;
fs.writeFileSync(path.join(out, "README.md"), readme, "utf8");
console.log(JSON.stringify({ out, changedCellCount: rows.length, beforeSha256: metadata.beforeSha256, afterSha256: metadata.afterSha256, changes: rows }, null, 2));
