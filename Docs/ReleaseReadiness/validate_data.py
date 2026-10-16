"""Read-only source/export comparison and current content metrics."""
import json
import pathlib
import re
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=pathlib.Path(__file__).resolve().parent/"evidence"
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def write(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")

sheets=load(OUT/"source_tables.json")
active=next(x for x in sheets if x["file"].endswith("/__tables__.xlsx"))["rows"]
results=[]
for definition in active[3:]:
    if not definition[1] or not definition[4] or str(definition[0]).startswith("##"): continue
    table=definition[1].lower()
    src=next(x for x in sheets if x["file"].endswith("/"+definition[4]) and x["rows"])
    headers,types=src["rows"][:2]
    source={}
    for rn,row in enumerate(src["rows"][3:],4):
        if not row or str(row[0]).startswith("##") or row[1] is None: continue
        record={}
        for col,header in enumerate(headers):
            if col==0 or not header or str(header).startswith("##"): continue
            typ=str(types[col]).strip()
            v=row[col] if col<len(row) else None
            if typ.startswith("(list"):
                sep=re.search(r"sep=(.)",typ)[1]
                parts=str(v).split(sep) if v is not None else []
                v=[int(float(p)) for p in parts] if typ.endswith("int") else parts
            elif typ in {"int","float","double","long"}: v=float(v or 0)
            elif typ=="vector3": v=dict(zip("xyz",map(float,str(v or "0,0,0").split(","))))
            else: v=str(v) if v is not None else ""
            record[str(header).strip()]=v
        key = str(int(record["id"])) if isinstance(record["id"], (int,float)) else str(record["id"])
        source[key]=(rn,record)
    exported=load(ROOT/"Assets/ConfigJson"/(table+".json"))
    differences=[]
    exported_by_id={str(r["id"]):r for r in exported}
    for key,(rn,record) in source.items():
        other=exported_by_id.get(key)
        if other is None: differences.append({"row":rn,"id":key,"error":"source record absent from JSON"});continue
        for field,v in record.items():
            if v!=other.get(field): differences.append({"row":rn,"id":key,"field":field,"source":v,"exported":other.get(field)})
    for key in exported_by_id.keys()-source.keys(): differences.append({"id":key,"error":"JSON record absent from source"})
    results.append({"table":table,"file":src["file"],"sheet":src["sheet"],"source_rows":len(source),"exported_rows":len(exported),"differences":differences})

tables={p.stem:load(p) for p in (ROOT/"Assets/ConfigJson").glob("*.json")}
enemies={r["id"]:r for r in tables["tbenemydata"]}
metrics=[]
for w in tables["tbenemylist"]:
    ids=w["EnemyIndexs"]
    metrics.append({"wave":w["id"],"count":len(ids),"hp":round(sum(enemies[i]["hp"] for i in ids),2),"effective_hp":round(sum(enemies[i]["hp"]/(1-enemies[i]["armor"]) for i in ids),2),"gold":sum(enemies[i]["reward"] for i in ids),"flying":sum(enemies[i]["isFlying"] for i in ids),"high_pressure_armor_or_boss":sum(enemies[i]["armor"]>=0.25 or enemies[i]["type"]==3 for i in ids),"interval_ms":w["enemyInterval"]})
write("data_validation.json",{"source_export":results,"wave_metrics":metrics,"note":"Comparison follows active __tables__ definitions and declared scalar/list/vector types. Empty auxiliary sheets and unreferenced backup workbooks are excluded. Difficulty metrics are static, not playtest outcomes."})
checks=["check_code.py","check_events.py","check_usings.py","check_native_symbols.py","verify_save_roundtrip.py","check_ui_contract.py"]
check_results=[]
for name in checks:
    run=subprocess.run([sys.executable,"-X","utf8",str(ROOT/".workbuddy/tools"/name)],cwd=ROOT,capture_output=True,encoding="utf-8",errors="replace",timeout=60)
    (OUT/(name+".log")).write_text(run.stdout+"\nSTDERR:\n"+run.stderr,encoding="utf-8")
    check_results.append({"script":name,"exit_code":run.returncode,"log":name+".log","tail":run.stdout.splitlines()[-6:]})
write("existing_checks.json",check_results)
print(json.dumps({"source_export":[{"table":r["table"],"source_rows":r["source_rows"],"differences":len(r["differences"])} for r in results],"checks":check_results},ensure_ascii=False,indent=2))
