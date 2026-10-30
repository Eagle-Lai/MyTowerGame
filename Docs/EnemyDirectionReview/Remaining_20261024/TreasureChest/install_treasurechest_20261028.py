from session_treasurechest import *
import shutil,time
owner();action=sys.argv[1]
t=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']==NAME);art=R/t['art_dir']
if action=='editor':
    assert inventory()==read(D/'incremental_before_20261028.json')['files']
    assert read(D/'preinstall_review_20261028.json')['accepted_for_install']
    client=Client();project=client.identity();errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));live=probe(client)
    assert errors['data']==[] and not any(v for k,v in live.items() if k!='scene')
    dest=art/'Editor';assert not dest.exists();dest.mkdir(parents=True)
    for name in ['TreasureChestDirectionAdapter','TreasureChestDirectionReview']:
        shutil.copy2(D/(name+'.cs.txt'),dest/(name+'.cs'))
    write(D/'editor_import_intent_20261028.json',dict(observed_at=now(),project=project,live=live,errors=errors,history=client.history,source={p.name:sha(p) for p in dest.iterdir()}))
    refresh=unwrap(client.tool('refresh_unity',dict(mode='force',scope='all',compile='request',wait_for_ready=True)))
    write(D/'editor_compile_request_20261028.json',dict(observed_at=now(),response=refresh,history=client.history))
    print(json.dumps(dict(requested=True,source_files=2)))
elif action=='compile':
    client=Client();project=client.identity();history=[]
    for attempt in range(40):
        state=client.resource('mcpforunity://editor/state');s=state['data'];history.append(state)
        if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
        if s['advice'].get('blocking_reasons')==['stale_status']:
            unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"TreasureChest_compile_live_state_read"});return true;')))
        time.sleep(1)
    else:raise RuntimeError('Not ready')
    errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));live=probe(client)
    write(D/'editor_compile_result_20261028.json',dict(observed_at=now(),project=project,states=history,errors=errors,live=live,history=client.history))
    assert errors['data']==[] and not any(v for k,v in live.items() if k!='scene')
    print(json.dumps(dict(compilation_failed=live['failed'],errors=0,scene=live['scene'])))
elif action=='install':
    assert not (D/'installed_manifest.json').exists();assert read(D/'editor_compile_result_20261028.json')['live']['failed'] is False
    original=read(D/'incremental_before_20261028.json')['protected_six'];assert all(sha(R/p)==s for p,s in original.items())
    expected=read(D/'preinstall_review_20261028.json')['staged'];assert all(sha(D/'staged_art'/p)==s for p,s in expected.items())
    before={p.relative_to(R).as_posix():sha(p) for p in [R/t['battle'],R/(t['battle']+'.meta'),*art.rglob('*')] if p.is_file()}
    for p in before:
        dest=D/'before'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,dest)
    for suffix in ['.png','.sprites.json','.layout.json']:shutil.copy2(D/'staged_art'/('TreasureChest_Directions'+suffix),art/('TreasureChest_Directions'+suffix))
    client=Client();project=client.identity();assert not any(v for k,v in probe(client).items() if k!='scene')
    unwrap(client.tool('refresh_unity',dict(mode='force',scope='assets',compile='none',wait_for_ready=True)));client.identity()
    code='FTProject.EditorTools.TreasureChestDirectionAdapter.Build();FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionalRigBuilder.TryGetSpec("TreasureChest",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);System.IO.File.WriteAllText("Docs/EnemyDirectionReview/Remaining_20261024/TreasureChest/installed_verify.txt",report);return new{pass=pass,report=report};'
    result=unwrap(client.tool('execute_code',dict(action='execute',code=code)))
    after={p.relative_to(R).as_posix():sha(p) for p in [R/t['battle'],R/(t['battle']+'.meta'),*art.rglob('*')] if p.is_file()}
    changes=[dict(path=p,before=before.get(p),after=after.get(p)) for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
    write(D/'installed_manifest.json',dict(name=NAME,installed_at=now(),project=project,verification=result,changes=changes,protocol_history=client.history,adapter='Editor/TreasureChestDirectionAdapter.cs',scope_note='Target-only Editor source imported before atlas installation; included in preplay binding and final scope'))
    assert result['data']['result']['pass']
    print(json.dumps(dict(installed=True,verify=True,changes=len(changes))))
