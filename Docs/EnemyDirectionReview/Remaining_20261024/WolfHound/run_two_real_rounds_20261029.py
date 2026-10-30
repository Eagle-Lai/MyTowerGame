from session_current import *
import subprocess

owner()
binding=read(HERE/'preplay_version_binding_20261029.json')
assert not any((HERE/r).exists() for r in ['runtime_r01','runtime_updeath_r01'])
assert bound(snapshot())==binding['production_fingerprints']
assert {p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}==binding['staged_fingerprints']
assert sha(HERE/'installed_manifest.json')==binding['manifest_sha256']
assert sha(HERE/'installed_verify.txt')==binding['verify_sha256']
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
v=errors.get('structuredContent') or json.loads(errors['content'][0]['text']);assert v['data']==[],v
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
assert state['data']['advice']['ready_for_tools'] and not state['data']['tests']['is_running'] and not state['data']['compilation']['is_domain_reload_pending']
save(HERE/'runtime_start_gate_20261029.json',{'observed_at':now(),'project':project,'probe':p,'state':state,'errors':errors,'art_revision':binding['art_revision'],'preplay_binding_sha256':sha(HERE/'preplay_version_binding_20261029.json'),'protocol_history':c.history})
owner()
subprocess.run([sys.executable,str(RUN/'runtime_runner.py'),NAME],check=True)
