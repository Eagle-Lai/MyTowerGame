"""Compare immutable production audits, preserving unrelated prior differences."""
from pathlib import Path
import json,sys
here=Path(__file__).resolve().parent
name,prior_name,current_name=sys.argv[1:4]
prior=json.loads((here/prior_name).read_text(encoding='utf-8'))
current=json.loads((here/current_name).read_text(encoding='utf-8'))
old={x['path']:x for x in prior['unexpected']}
new={x['path']:x for x in current['unexpected']}
delta={'prior':prior_name,'current':current_name,'prior_unexpected':len(old),'current_unexpected':len(new),'new_unexpected':[v for p,v in new.items() if p not in old],'changed_prior_unexpected':[{'path':p,'prior':old[p],'current':v} for p,v in new.items() if p in old and v!=old[p]],'removed_prior_unexpected':[v for p,v in old.items() if p not in new],'semantic_failures':[{'name':n,'details':s['unexpected']} for n,s in current['semantics'].items() if not s['pass']]}
out=here/name/'scope_delta.json'
if out.exists():raise ValueError('Existing scope delta must not be replaced')
out.write_text(json.dumps(delta,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
print(json.dumps(delta,ensure_ascii=False))
