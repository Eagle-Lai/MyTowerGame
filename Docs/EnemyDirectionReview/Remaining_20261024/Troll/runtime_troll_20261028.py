from session_troll import *
import time
owner();manifest=read(D/'installed_manifest.json');assert manifest['verification']['data']['result']['pass']
installed={x['path']:x['after'].upper() for x in manifest['changes']}
def binding():
    for p,s in installed.items():assert sha(R/p)==s,p
    return dict(installed=installed,installed_manifest_sha256=sha(D/'installed_manifest.json'),staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},source_and_dependencies={p:sha(R/p) for p in ['Assets/Scripts/Enemy/BaseEnemy.cs','Assets/Scripts/Enemy/EnemyDirectionalVisual.cs','Assets/Scripts/Enemy/EnemyDirectionalProfile.cs','Assets/Scripts/Enemy/MonsterAnimEventReceiver.cs','Assets/Editor/EnemyDirectionalRigBuilder.cs','Assets/Editor/EnemyDirectionRemainingMotion.cs','Assets/Editor/EnemyDirectionBatchReview.cs','Assets/_UIAssets/Monsters/_Common/Animations/Giant/Controller.controller']})
for revision,up in [('runtime_r01',False),('runtime_updeath_r01',True)]:
    owner();folder=D/revision;assert not folder.exists(),'Existing runtime must be inspected, not blindly rerun'
    c=Client();project=c.identity();errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));state=c.resource('mcpforunity://editor/state');live=probe(c)
    assert not any(v for k,v in live.items() if k!='scene') and errors['data']==[],live
    before=binding();write(D/(revision+'_version_binding_before.json'),dict(observed_at=now(),revision=revision,project=project,errors=errors,state=state,live=live,binding=before,protocol_history=c.history))
    subprocess.run([sys.executable,str(H/'start_runtime.py'),NAME,revision]+(['up'] if up else []),check=True)
    deadline=time.monotonic()+180
    while not (folder/'actual_runtime_checks.txt').exists():
        if (folder/'exception.txt').exists():raise ValueError((folder/'exception.txt').read_text(encoding='utf-8'))
        if time.monotonic()>deadline:raise TimeoutError('Runtime unfinished; no forced Play exit')
        time.sleep(2)
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8');assert checks.count('PASS ')==84 and 'FAIL ' not in checks
    deadline=time.monotonic()+45
    while True:
        c=Client();project=c.identity();live=probe(c)
        if not live['playing'] and not live['review']:break
        if time.monotonic()>deadline:raise TimeoutError('Natural scene return incomplete')
        time.sleep(2)
    assert live['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in live.items() if k!='scene'),live
    assert binding()==before,'Final installation or directly used C# drifted during Play'
    write(D/(revision+'_returned.json'),dict(observed_at=now(),project=project,live=live,binding_matched=True,protocol_history=c.history))
    print(json.dumps(dict(revision=revision,passes=84,failures=0,natural_return=live,version_bound_before=True)),flush=True)
subprocess.run([sys.executable,str(H/'finish_runtime.py'),NAME],check=True)
p=read(H/'progress.json');item=next(x for x in p['items'] if x['name']==NAME);item.update(status='runtime_complete_pending_visual_check',user_approved=False);p.update(current=NAME,updated_at=now());write(H/'progress.json',p)
c=owner();c.update(current_stage='runtime_complete_pending_visual_check',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Troll/runtime_summary.json',updated_at=now());write(H/'conversation_chain.json',c)
