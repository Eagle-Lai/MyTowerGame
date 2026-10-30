from session_treasurechest import *
import time
owner();manifest_path=D/(sys.argv[1] if len(sys.argv)>1 else 'installed_manifest.json');manifest=read(manifest_path);assert manifest['verification']['data']['result']['pass']
assert all(sha(R/x['path'])==x['after'] for x in manifest['changes'])
t=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']==NAME);art=R/t['art_dir']
revisions=sys.argv[2:4] or ['runtime_r01','runtime_updeath_r01'];assert len(revisions)==2
for revision,up in [(revisions[0],False),(revisions[1],True)]:
    owner();folder=D/revision;assert not folder.exists(),'Inspect prior round, do not overwrite'
    client=Client();project=client.identity();errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));live=probe(client)
    assert errors['data']==[] and not any(v for k,v in live.items() if k!='scene')
    code='return FTProject.EditorTools.TreasureChestDirectionReview.Running;'
    assert unwrap(client.tool('execute_code',dict(action='execute',code=code)))['data']['result'] is False
    files={p.relative_to(R).as_posix():sha(p) for p in [R/t['battle'],R/(t['battle']+'.meta'),*art.rglob('*')] if p.is_file()}
    staged={p.relative_to(D).as_posix():sha(p) for p in (D/'staged_art').iterdir() if p.is_file()}
    write(D/(revision+'_version_binding_before.json'),dict(observed_at=now(),installed_manifest=manifest_path.name,installed_manifest_sha256=sha(manifest_path),production=files,staged=staged,shared_CSharp={p:s for p,s in read(D/'incremental_before_20261028.json')['files'].items() if p.endswith('.cs')},target_harness='Editor/TreasureChestDirectionReview.cs',harness_derivation_sha256=sha(D/'editor_adapter_derivation_20261028.json')))
    response=unwrap(client.tool('execute_code',dict(action='execute',code='FTProject.EditorTools.TreasureChestDirectionReview.Start("TreasureChest",'+json.dumps(revision)+','+str(up).lower()+');return true;')))
    write(D/(revision+'_start.json'),dict(project=project,name=NAME,revision=revision,death_up=up,response=response,protocol_history=client.history))
    deadline=time.monotonic()+180
    while not (folder/'actual_runtime_checks.txt').exists():
        if (folder/'exception.txt').exists():raise RuntimeError((folder/'exception.txt').read_text())
        if time.monotonic()>deadline:raise TimeoutError('Real Play unfinished; do not force exit')
        time.sleep(2)
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8');assert checks.count('PASS ')==84 and 'FAIL ' not in checks,checks
    deadline=time.monotonic()+30
    while True:
        client=Client();client.identity();live=probe(client)
        own_review=unwrap(client.tool('execute_code',dict(action='execute',code=code)))['data']['result']
        if not live['playing'] and not own_review:break
        assert time.monotonic()<deadline,'Waiting for natural scene return';time.sleep(1)
    assert live['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in live.items() if k!='scene')
    assert all(sha(R/p)==s for p,s in files.items()),'Installed asset drift during actual round'
    write(D/(revision+'_returned.json'),dict(observed_at=now(),state=live,own_review=own_review,protocol_history=client.history,version_unchanged=True))
    print(json.dumps(dict(revision=revision,checks=84,failures=0,returned=live)),flush=True)
subprocess.run([sys.executable,str(H/'finish_runtime_revision.py'),NAME,*revisions],check=True)
c=owner();c.update(current_stage='runtime_complete_pending_actual_visual_review',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/TreasureChest/runtime_summary.json',updated_at=now());write(H/'conversation_chain.json',c)
