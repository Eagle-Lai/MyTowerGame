from session_current import *
import subprocess

owner()
binding=read(HERE/'preplay_version_binding_20261029.json')
assert not any((HERE/r).exists() for r in ['runtime_r01','runtime_updeath_r01'])
assert bound(snapshot())==binding['production_fingerprints']
assert {p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}==binding['staged_fingerprints']
assert sha(HERE/'installed_manifest.json')==binding['manifest_sha256']
assert sha(HERE/'installed_verify.txt')==binding['verify_sha256']
for key,value in binding.items():
    if 'native' in key: print(key,value,flush=True)
assert binding['native_attack_manifest_sha256']==sha(HERE/'native_attack_timing01_manifest_20261029.json')
assert binding['native_attack_verify_sha256']==sha(HERE/'native_attack_timing01_verify.txt')
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
v=errors.get('structuredContent') or json.loads(errors['content'][0]['text']);assert v['data']==[],v
state=fresh_state(c,'Zombie pre-runtime continuation gate');p=probe(c);idle(p)
save(HERE/'runtime_start_gate_20261029.json',{'observed_at':now(),'project':project,'probe':p,'state':state,'errors':errors,'art_revision':binding['art_revision'],'preplay_binding_sha256':sha(HERE/'preplay_version_binding_20261029.json'),'protocol_history':c.history})
owner()
subprocess.run([sys.executable,str(RUN/'runtime_runner.py'),NAME],check=True)
c=Client();project=c.identity();state=fresh_state(c,'Zombie both real rounds returned');p=probe(c);idle(p)
assert bound(snapshot())==binding['production_fingerprints']
summary=read(HERE/'runtime_summary.json')
assert summary['passes']==168 and summary['failures']==0
assert all(r['pass']==84 and r['fail']==0 for r in summary['runtime'])
save(HERE/'runtime_rounds_returned_20261029.json',{'observed_at':now(),'project':project,'probe':p,'state':state,'summary':summary,'production_matches_preplay':True,'protocol_history':c.history})
print(json.dumps({'passes':summary['passes'],'failures':summary['failures'],'actual_frames':summary['actual_frames'],'clean_Boot':True}),flush=True)
