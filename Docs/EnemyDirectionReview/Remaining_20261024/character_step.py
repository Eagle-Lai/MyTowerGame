"""One-character checkpoints; visual review between steps remains mandatory."""
from pathlib import Path
from datetime import datetime
import json,sys,subprocess
HERE=Path(__file__).resolve().parent
action,name=sys.argv[1:3]
def run(script,*args):subprocess.run([sys.executable,str(HERE/script),*args],check=True)
if action=='prepare':
    run('prepare_character.py',name)
    run('render_source_reference.py','--battle','--name',name)
elif action=='stage':
    run('pack_character.py',name)
    if (HERE/name/'layout_adjustments.json').exists():run('adjust_layout.py',name)
    if (HERE/name/'retouch_heels.py').exists():subprocess.run([sys.executable,str(HERE/name/'retouch_heels.py')],check=True)
    run('render_staged_rig.py',name)
elif action=='install-and-review':
    run('install_character.py',name)
    run('runtime_runner.py',name)
    run('audit_scope.py','scope_'+name+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
elif action=='record':
    run('record_review.py',name,sys.argv[3])
else:raise ValueError(action)
if action!='record':
    path=HERE/'progress.json';progress=json.loads(path.read_text(encoding='utf-8'))
    item=next(x for x in progress['items'] if x['name']==name)
    if item.get('user_approved'):raise ValueError('Never alter approved status')
    item.update(status={'prepare':'reference_prepared','stage':'staged_pending_visual_check','install-and-review':'runtime_complete_pending_visual_check'}[action])
    progress['current']=name
    path.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
