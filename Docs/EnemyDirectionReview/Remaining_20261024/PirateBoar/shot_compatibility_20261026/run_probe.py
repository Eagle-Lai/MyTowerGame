from pathlib import Path
import sys,json,time
HERE=Path(__file__).resolve().parent
RUN=HERE.parents[1]
sys.path.insert(0,str(RUN))
from mcp_call import Client
c=Client();identity=c.identity()
state=c.resource('mcpforunity://editor/state')['data']
assert not state['editor']['play_mode']['is_playing']
r=c.tool('execute_code',{'action':'execute','code':'FTProject.EditorTools.EnemyDirectionBatchReview.Start("PirateBoar","runtime_shot_r02",false);return true;'})
for i in range(12):
    time.sleep(1)
    try:
        c=Client();c.identity()
        state=c.resource('mcpforunity://editor/state')['data']
        if state['editor']['play_mode']['is_playing'] and not state['compilation']['is_compiling']:
            break
    except Exception:
        continue
time.sleep(1)
code=(HERE/'shot_probe.cs.txt').read_text().replace('runtime_shot_r01','runtime_shot_r02')
r=c.tool('execute_code',{'action':'execute','code':code})
print(json.dumps(r),flush=True)
(HERE/'hook_r02.json').write_text(json.dumps({'project':identity,'result':r,'history':c.history},indent=2)+chr(10),encoding='utf-8')
