from session_current import *
import subprocess
owner();c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json','include_stacktrace':True})
observed=errors.get('structuredContent') or json.loads(errors['content'][0]['text'])
expected=(read(HERE/'runtime_r01_detailed_errors_20261029.json')['errors'].get('structuredContent'))
assert observed['data']==expected['data'],observed
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
assert state['data']['advice']['ready_for_tools'] and not state['data']['tests']['is_running'] and not state['data']['compilation']['is_domain_reload_pending']
files=snapshot();scope=audit(files);assert scope['pass'],scope
save(HERE/'scope_incremental_preplay_r02_20261029.json',scope)
old=read(HERE/'preplay_version_binding_20261029.json')
assert old['staged_fingerprints']=={p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
binding={**old,'observed_at':now(),'asset_revision':old['art_revision']+'_headbindings02',
 'production_fingerprints':bound(files),'all_production_fingerprints':files,
 'verify_file':'installed_verify_repair_r02.txt','verify_sha256':sha(HERE/'installed_verify_repair_r02.txt'),
 'repair_manifest':'head_binding_repair_r02_20261029.json','repair_manifest_sha256':sha(HERE/'head_binding_repair_r02_20261029.json'),
 'original_install_manifest_preserved':True,'scope':'scope_incremental_preplay_r02_20261029.json',
 'historical_errors_retained':observed,'probe':p,'editor_state':state,'protocol_history':c.history}
save(HERE/'preplay_version_binding_r02_20261029.json',binding)
save(HERE/'runtime_start_gate_r02_20261029.json',{'observed_at':now(),'project':project,'probe':p,'state':state,'historical_errors':observed,'preplay_binding_sha256':sha(HERE/'preplay_version_binding_r02_20261029.json'),'protocol_history':c.history})
assert not any((HERE/r).exists() for r in ['runtime_r02','runtime_updeath_r02'])
owner()
subprocess.run([sys.executable,str(RUN/'runtime_runner_revision.py'),NAME,'runtime_r02','runtime_updeath_r02'],check=True)
