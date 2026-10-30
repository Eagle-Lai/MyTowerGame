from session_current import *
c0=owner();c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
assert state['data']['advice']['ready_for_tools']
files=snapshot();scope=audit(files);assert scope['pass'],scope
save(HERE/'scope_incremental_preplay_20261029.json',scope)
save(HERE/'preplay_version_binding_20261029.json',{
    'observed_at':now(),'owner_thread_id':c0['owner_thread_id'],'dispatch_token':c0['dispatch_token'],
    'art_revision':'Up_local03_Down03_alpha_r01_layout_r01','project':project,
    'production_fingerprints':bound(files),'all_production_fingerprints':files,
    'staged_fingerprints':{p.name:sha(p) for p in (HERE/'staged_art').iterdir() if p.is_file()},
    'manifest_sha256':sha(HERE/'installed_manifest.json'),'verify_sha256':sha(HERE/'installed_verify.txt'),
    'scope':'scope_incremental_preplay_20261029.json','probe':p,'editor_state':state,'errors':errors,
    'protocol_history':c.history})
print(json.dumps({'verify':True,'scope_pass':scope['pass'],'bound_files':len(bound(files)),'ready':True,'all_paths':len(files)}))
