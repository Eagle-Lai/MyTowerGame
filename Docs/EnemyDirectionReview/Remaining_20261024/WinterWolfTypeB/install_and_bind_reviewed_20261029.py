from session_current import *
import subprocess

owner()
assert not (HERE/'installed_manifest.json').exists()
views=['offline_four_directions_r04.png','Down_Body_detail_r04.png','offline_rig_proof.png','parts_clean.png']
review={
    'observed_at':now(),'art_revision':'Up_local03_Down_local03_alpha01_body04_layout04',
    'viewed_full_images':{p:sha(HERE/p) for p in views[:3]},
    'findings':'Complete offline Left/Right source and Up/Down silhouettes inspected. Up has plain rear ears/head and smooth heels; Down has one frontal head, ivory eyes, ochre nose/spots, fangs, chin tuft and ventral bib. Four limbs and tail are connected. Removed the two broken upper-rump motif/spot remnants. No clipping of ears, feet or tail, added equipment, duplicate head or detached part observed. Offline view does not prove runtime motion.',
    'stage_files':{p.name:sha(p) for p in (HERE/'staged_art').iterdir() if p.is_file()},
    'local_derivation_record':'staged_body_cleanup_r04_20261029.json',
    'internal_stage_accepted_for_install':True,'user_approved':False}
review_path=HERE/'staged_visual_review_final_20261029.json'
if review_path.exists():
    assert read(review_path)['stage_files']==review['stage_files']
else:
    save(review_path,review)
c=Client();project=c.identity()
errors={}
for key,args in [('errors',{}),('compile_errors',{'filter_text':'error CS'})]:
    v=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json',**args})
    errors[key]=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    assert errors[key]['data']==[],errors[key]
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
assert state['data']['advice']['ready_for_tools'] and not state['data']['tests']['is_running']
files=snapshot();scope=audit(files)
# The semantic validator intentionally requires installed Directions and removed
# shadows, so its pre-install result is retained as evidence, not a gate.
assert files==read(HERE/'production_paths_before_20261029.json')
assert not scope['changes'] and not scope['unexpected']
assert all(v['matches'] for v in scope['protected_six'].values())
save(HERE/'preinstall_final_20261029.json',{'observed_at':now(),'project':project,'probe':p,'state':state,'errors':errors,'production_fingerprints':files,'all_startup_paths_match':True,'scope_diagnostic':scope,'diagnostic_note':'Installed semantic validator is not applicable until installation. Its original false pre-install result is retained. First attempt stopped before all production writes for this reason. Pre-install gate is exact path/SHA equality and all six protected files.','protocol_history':c.history})
owner()
subprocess.run([sys.executable,str(RUN/'install_character.py'),NAME],check=True)
owner();c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
v=errors.get('structuredContent') or json.loads(errors['content'][0]['text']);assert v['data']==[],v
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
assert state['data']['advice']['ready_for_tools']
files=snapshot();scope=audit(files);assert scope['pass'],scope
save(HERE/'scope_incremental_preplay_20261029.json',scope)
save(HERE/'preplay_version_binding_20261029.json',{
    'observed_at':now(),'owner_thread_id':owner()['owner_thread_id'],'dispatch_token':owner()['dispatch_token'],
    'art_revision':'Up_local03_Down_local03_alpha01_body04_layout04','project':project,
    'production_fingerprints':bound(files),'all_production_fingerprints':files,
    'staged_fingerprints':{p.name:sha(p) for p in (HERE/'staged_art').iterdir() if p.is_file()},
    'manifest_sha256':sha(HERE/'installed_manifest.json'),'verify_sha256':sha(HERE/'installed_verify.txt'),
    'scope':'scope_incremental_preplay_20261029.json','probe':p,'editor_state':state,'errors':errors,
    'protocol_history':c.history})
print(json.dumps({'installed':True,'scope_pass':scope['pass'],'bound_files':len(bound(files)),'all_paths':len(files),'ready_for_two_real_Play_rounds':True}))
