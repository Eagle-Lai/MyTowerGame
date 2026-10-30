from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
a=json.loads((r/"scope_Chicken_repair01_20261024.json").read_text(encoding="utf-8"))
b=json.loads((r/"scope_Cow_20261024.json").read_text(encoding="utf-8"))
old={x["path"]:x for x in a["unexpected"]}
new=[x for x in b["unexpected"] if x!=old.get(x["path"])]
report={"prior":"scope_Chicken_repair01_20261024.json","current":"scope_Cow_20261024.json","prior_unexpected":len(a["unexpected"]),"current_unexpected":len(b["unexpected"]),"new_unexpected":new,"semantic_failures":{n:s["unexpected"] for n,s in b["semantics"].items() if not s["pass"]},"note":"Global baseline contains unrelated existing sound-removal differences. No unrelated changes reverted."}
(r/"Cow/scope_delta.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
