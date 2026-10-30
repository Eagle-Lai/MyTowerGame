from pathlib import Path
import json,sys
r=Path(__file__).resolve().parent
name,prior,current=sys.argv[1:4]
a=json.loads((r/prior).read_text(encoding="utf-8"));b=json.loads((r/current).read_text(encoding="utf-8"))
old={x["path"]:x for x in a["unexpected"]}
report={"prior":prior,"current":current,"prior_unexpected":len(a["unexpected"]),"current_unexpected":len(b["unexpected"]),"new_unexpected":[x for x in b["unexpected"] if x!=old.get(x["path"])],"semantic_failures":{n:s["unexpected"] for n,s in b["semantics"].items() if not s["pass"]}}
(r/name/"scope_delta.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
