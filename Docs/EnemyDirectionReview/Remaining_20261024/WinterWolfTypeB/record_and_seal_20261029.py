from session_current import *
import subprocess,shutil

owner()
assert not (HERE/'gif_archive_verification_20261029.json').exists()
final=read(HERE/'final_validation_20261029.json')
assert final['passes']==168 and final['failures']==0 and final['scope_pass']
progress=read(RUN/'progress.json')
assert progress['completed_count']==102
item=next(r for r in progress['items'] if r['name']==NAME)
assert not item.get('user_approved')
backup=HERE/'docs_before_final_record_20261029';assert not backup.exists();backup.mkdir()
shutil.copy2(RUN/'progress.json',backup/'progress.json')
for n in ['manifest.json','README.md','index.html']:
    shutil.copy2(RUN.parent/'AllGIF'/n,backup/n)
note=(HERE/'record_note_utf8.txt').read_text(encoding='utf-8').strip()
subprocess.run([sys.executable,str(RUN/'character_step.py'),'record',NAME,note],check=True)
owner()
manifest=read(RUN.parent/'AllGIF/manifest.json');old=read(backup/'manifest.json')
assert {(r['source'],r['sha256']) for r in old['files']}<={(r['source'],r['sha256']) for r in manifest['files']}
sources={p.relative_to(RUN.parent).as_posix():p for p in HERE.rglob('*.gif')}
entries=[r for r in manifest['files'] if r['source'].startswith('Remaining_20261024/'+NAME+'/')]
assert len(sources)==len(entries) and set(sources)=={r['source'] for r in entries}
assert manifest['count']==old['count']+len(entries)
verified=[]
for r in entries:
    source=sources[r['source']];copy=RUN.parent/'AllGIF'/r['file']
    assert sha(source)==sha(copy)==r['sha256']
    verified.append({**r,'source_copy_sha256_match':True})
final_gifs=sum(r['status']=='当前审核版本' for r in entries)
historical_gifs=len(entries)-final_gifs
assert final_gifs==12 and historical_gifs==6
save(HERE/'gif_archive_verification_20261029.json',{
    'observed_at':now(),'before':old['count'],'after':manifest['count'],
    'current_character_sources':len(sources),'final':final_gifs,'historical_timing_originals':historical_gifs,
    'all_old_source_hashes_retained':True,'all_current_source_copy_matches':True,'entries':verified,'user_approved':False})
progress=read(RUN/'progress.json');item=next(r for r in progress['items'] if r['name']==NAME)
assert progress['completed_count']==103 and item['status']=='completed_pending_user_art_review'
item.update(current_stage='recorded_pending_user_art_review',completed_at=now(),production_modified=True,
    staging=final['art_revision'],install_verify='PASS',record='completed',new_gifs=len(entries),
    final_gifs=final_gifs,historical_gifs=historical_gifs,
    scope_record=(HERE/'scope_incremental_final_20261029.json').relative_to(ROOT).as_posix(),
    unity_release=(HERE/'unity_release_final_20261029.json').relative_to(ROOT).as_posix(),
    final_validation=(HERE/'final_validation_20261029.json').relative_to(ROOT).as_posix(),
    version_binding=(HERE/'final_version_binding_20261029.json').relative_to(ROOT).as_posix(),
    visual_review=(HERE/'visual_review_final_20261029/review.json').relative_to(ROOT).as_posix(),
    gif_archive=(HERE/'gif_archive_verification_20261029.json').relative_to(ROOT).as_posix(),user_approved=False)
remaining=sorted([r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']],key=lambda r:r['index'])
assert [r['name'] for r in remaining]==['PossessedWarg','Wolf','WolfHound','WolfMounfed','Zombie']
material=[]
for r in remaining:
    folder=RUN/r['name'];paths=sorted(p for p in folder.rglob('*') if p.is_file())
    material.append({'index':r['index'],'name':r['name'],'status':r['status'],
        'files':{p.relative_to(folder).as_posix():sha(p) for p in paths},
        'has_install':(folder/'installed_manifest.json').exists(),'has_stage':(folder/'staged_art').exists(),
        'has_runtime':(folder/'runtime_summary.json').exists(),
        'successful_raws':[p.relative_to(folder).as_posix() for p in folder.rglob('raw.png')]})
assert material[0]['successful_raws']==['generation/Up/raw.png']
assert not any(r[k] for r in material for k in ['has_install','has_stage','has_runtime'])
wolf=next(r for r in material if r['name']=='Wolf')
assert wolf['index']==115 and len(wolf['files'])==8 and not wolf['successful_raws']
save(HERE/'successor_assessment_final_20261029.json',{
    'observed_at':now(),'completed':103,'authorized':108,'remaining':material,
    'selected':'Wolf','selected_index':115,
    'selection_reason':'No independently recoverable started character. PossessedWarg Down remains unknown. Wolf is the next reference-only uncompleted index; use proven direct pinned domain route for actual work, not paid diagnostics.',
    'PossessedWarg_inference':'Original unknown request outcome/charge unchanged. No reissue or claim of uncharged/unsent.',
    'current_character_network_recovery_used':1,'current_character_network_recovery_limit':2,'reset_counters':False})
progress.update(current='Wolf',updated_at=now())
(RUN/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
final.update(record_completed=True,completed_count=103,authorized_count=108,gif_archive_count=manifest['count'],
             character_gifs=len(entries),final_gifs=final_gifs,historical_gifs=historical_gifs,
             gif_archive_verification_sha256=sha(HERE/'gif_archive_verification_20261029.json'),
             progress_sha256_after_record=sha(RUN/'progress.json'))
(HERE/'final_validation_20261029.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'completed':103,'authorized':108,'allGIF_before':old['count'],'allGIF_after':manifest['count'],
    'character_gifs':len(entries),'final':final_gifs,'history':historical_gifs,'all_sha_match':True,
    'next':'Wolf','next_reference_files':len(wolf['files']),'remaining_count':len(remaining)},ensure_ascii=False))
