from session_current import *
import subprocess

owner()
assert not (HERE/'installed_manifest.json').exists()
revision='Up_local03_Down_local03_alpha03_layout01'
views=['offline_four_directions_final_20261029.png','parts_clean.png']
stage={p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
save(HERE/'staged_visual_review_final_20261029.json',{
    'observed_at':now(),'art_revision':revision,
    'viewed_full_images':{p:sha(HERE/p) for p in views},
    'findings':'Full four-direction board and all fourteen parts inspected. Original gray-brown/olive, slate fur, ochre circles, pointed ears, ivory eyes, broad nose, cream fangs/mouth, small chest tuft, four short canine legs and broad long tail retained. Up has a faceless rear head and smooth heels. Down has frontal normal/angry/dead face variants and forward toe marks. Full ear/paw/tail extents visible; roots overlap the body in the offline assembly. No added equipment, ground shadow, duplicate head, floating part or rectangular fill seam observed in the reviewed stage. Runtime must establish the motion and occlusion result.',
    'stage_files':stage,
    'local_derivations':['generation/Up/local_revision_03/processing.json','generation/Down/local_revision_03/processing.json','staged_alpha_cleanup_r03_20261029.json'],
    'internal_stage_accepted_for_install':True,'user_approved':False})
c=Client();project=c.identity();errors={}
for key,args in [('errors',{}),('compile_errors',{'filter_text':'error CS'})]:
    v=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json',**args})
    errors[key]=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    assert errors[key]['data']==[],errors[key]
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
assert state['data']['advice']['ready_for_tools'] and not state['data']['tests']['is_running']
assert not state['data']['compilation']['is_domain_reload_pending']
files=snapshot();scope=audit(files)
assert files==read(HERE/'production_paths_before_20261029.json')
assert not scope['changes'] and not scope['unexpected']
assert all(v['matches'] for v in scope['protected_six'].values())
save(HERE/'preinstall_final_20261029.json',{
    'observed_at':now(),'project':project,'probe':p,'state':state,'errors':errors,
    'production_fingerprints':files,'all_startup_paths_match':True,'scope_diagnostic':scope,
    'diagnostic_note':'The semantic validator requires installed Directions and is diagnostic only before installation. The pre-install gate is complete path/SHA equality and all six protected files.',
    'protocol_history':c.history})
owner()
subprocess.run([sys.executable,str(RUN/'install_character.py'),NAME],check=True)
owner();c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
v=errors.get('structuredContent') or json.loads(errors['content'][0]['text']);assert v['data']==[],v
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
assert state['data']['advice']['ready_for_tools'] and not state['data']['tests']['is_running']
files=snapshot();scope=audit(files);assert scope['pass'],scope
save(HERE/'scope_incremental_preplay_20261029.json',scope)
assert stage=={p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
save(HERE/'preplay_version_binding_20261029.json',{
    'observed_at':now(),'owner_thread_id':owner()['owner_thread_id'],'dispatch_token':owner()['dispatch_token'],
    'art_revision':revision,'project':project,'production_fingerprints':bound(files),'all_production_fingerprints':files,
    'staged_fingerprints':stage,'manifest_sha256':sha(HERE/'installed_manifest.json'),'verify_sha256':sha(HERE/'installed_verify.txt'),
    'scope':'scope_incremental_preplay_20261029.json','probe':p,'editor_state':state,'errors':errors,'protocol_history':c.history})
print(json.dumps({'installed':True,'scope_pass':scope['pass'],'bound_files':len(bound(files)),'all_paths':len(files),'staged_files':len(stage),'ready_for_two_real_Play_rounds':True}))
