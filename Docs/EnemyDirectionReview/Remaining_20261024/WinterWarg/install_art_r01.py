from session_winterwarg import *
from audit_current import audit
owner()
checkpoint=read(D/'preinstall_checkpoint_20261029_alpha_r02.json')
assert all(v['enclosed_transparent_pixels']==0 and v['magenta_opaque_pixels']==0 for v in checkpoint['pixel_metrics'])
assert checkpoint['staged_files']=={f.relative_to(D).as_posix():sha(f) for f in (D/'staged_art').iterdir() if f.is_file()}
write(D/'offline_art_review_20261029.json',{'recorded_at':now(),'art_revision':'art_r01','viewed':['original paid Up revision02 full image','first Down raw full image','local Up revisions03/04 full images and rejected artifacts','layout_r01 offline proof and parts sheet','layout_r02 offline proof','final alpha-cleaned 1600x700 parts sheet'],'observations':['Final rear head is face-free with round outer ears and a short crown tuft; repeated identically for rear head states.','Rear feet show smooth heels; forward feet preserve long canine claws and toe lines.','Both directions have four diagonal-phase legs with shoulder/hip roots buried in torso.','One original-type long white/ochre tail is rooted in rump using measured per-view pivot; no duplicate head/limbs or ground shadows.','Tiny chroma-mask holes were filled from adjacent foreground; all14 selected slices now contain no enclosed transparent pixels or opaque magenta.'],'retained_rejected':'local03/local04 and layout_r01 evidence kept under generation and stage_history','status':'internal offline visual review complete; user approval pending'},True)
c=Client();project=c.identity();p=probe(c);idle(p)
assert audit()['pass']
run('install_character.py',NAME)
c=Client();project=c.identity();state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
cs=c.tool('read_console',{'action':'get','types':['error'],'filter_text':'error CS','count':'50','format':'json'})
report=audit();assert report['pass'],report
write(D/'scope_postinstall_20261029.json',report,True)
files=snapshot();baseline=read(D/'incremental_before_20261029.json');t=baseline['target']
fingerprints={p:s for p,s in files.items() if p==t['battle'] or p==t['battle']+'.meta' or p==t['art_dir']+'.meta' or p.startswith(t['art_dir']+'/')}
write(D/'preplay_version_binding_art_r01_20261029.json',{'recorded_at':now(),'art_revision':'art_r01','layout_revision':'layout_r02','project':project,'production_fingerprints':fingerprints,'all_production_fingerprints':files,'staged_fingerprints':checkpoint['staged_files'],'selected_art':read(D/'art_selection.json'),'installed_manifest_sha256':sha(D/'installed_manifest.json'),'state':state,'probe':p,'errors':errors,'error_cs':cs,'scope_pass':True,'protocol_history':c.history},True)
stage('art_r01_installed_verified_preplay_bound',D/'preplay_version_binding_art_r01_20261029.json')
print(json.dumps({'installed':True,'scope_pass':True,'production_files':len(fingerprints),'probe':p,'errors':errors,'error_cs':cs},ensure_ascii=False))
