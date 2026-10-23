"""Preserve the exact production SHA256 success line observed in the live Unity log."""
from formal_tools import *
import sys,datetime,shutil
tag=sys.argv[1];assert tag in ['r2','r3','r4','final']
h=runtime_hash();path=pathlib.Path('C:/Users/Administrator/AppData/Local/Unity/Editor/Editor.log')
lines=path.read_text(encoding='utf-8',errors='replace').split('\n')
matches=[i for i,line in enumerate(lines)if '[Rating] Runtime configuration SHA256 verified: '+h in line]
assert matches,'No observed production load verification for current hash'
i=matches[-1]
record=dict(capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtimeContentHash=h,source=str(path),sourceLine=i+1,productionLogLine=lines[i],nearbyContext=lines[max(0,i-4):i+10],method='Read-only capture of actual Unity Editor.log emitted by Configs; MCP console may be busy during fixed-step batch',mcpConsoleConfirmation='pending_after_batch')
out=REPORT/f'audit/runtime-load-{tag}.json'
if out.exists():
 history=REPORT/'audit/runtime-load-history';history.mkdir(exist_ok=True)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
 shutil.copy2(out,history/f'{tag}-before-{stamp}.json')
out.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(lines[i])
