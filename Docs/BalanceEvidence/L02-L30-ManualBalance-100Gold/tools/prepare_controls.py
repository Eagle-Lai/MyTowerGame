"""Prepare three declared real player controls on the currently sealed campaign."""
from formal_tools import *
import sys
tag=sys.argv[1]
out=REPORT/f'requests/{tag}.json';assert not out.exists()
runs=[dict(profileId='D04',levelId=level,strategy=strategy,speed=1,waitForFunds=False,screenshots=False,captureStages=False)for level in range(2,31)for strategy in ['normal','power','mistake']]
request=dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs)
out.write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
bounds=dict(runtimeHashAtPreparation=runtime_hash(),candidateCount=87,levels=list(range(2,31)),strategies=dict(normal='Existing preparation-only ordinary-tower buying heuristic, cap8towers, with actual upgrades; no slow/group allocation',power='Existing preparation-only cap8heuristic: first two ordinary towers, then group towers, with actual upgrades',mistake='Existing intentionally incomplete investment control: only one ordinary tower; must be reported as underinvestment, not representative of all beginners'),funding='Real100-gold initial state, actual costs and balances, no injected currency',termination='Exactly29levels times3declared controls; early defense failures are real failures and not complete25-wave runs',status='unexecuted')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(bounds,ensure_ascii=False,indent=2),encoding='utf-8')
print('87 unexecuted controls')
