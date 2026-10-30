from session_current import *
import subprocess,shutil

owner();assert not (HERE/'gif_archive_verification_20261029.json').exists()
final=read(HERE/'final_validation_20261029.json')
assert final['passes']==168 and final['failures']==0 and final['scope_pass'] and final['original_semantics_pass']
pre=read(HERE/'final_version_binding_20261029.json');assert snapshot()==pre['all_production_fingerprints']
progress=read(RUN/'progress.json');assert progress['completed_count']==106
item=next(r for r in progress['items'] if r['name']==NAME);assert not item.get('user_approved')
backup=HERE/'docs_before_final_record_20261029';assert not backup.exists();backup.mkdir()
shutil.copy2(RUN/'progress.json',backup/'progress.json')
for n in ['manifest.json','README.md','index.html']:shutil.copy2(RUN.parent/'AllGIF'/n,backup/n)
assert sha(backup/'manifest.json')==read(HERE/'sync_start_20261029.json')['read_full_json_sha256']['Docs\\EnemyDirectionReview\\AllGIF\\manifest.json']
note=(HERE/'record_note_utf8.txt').read_text(encoding='utf-8').strip()
assert 'Zombie' in note and '639' in note and '用户美术' in note and '?' not in note
subprocess.run([sys.executable,str(RUN/'character_step.py'),'record',NAME,note],check=True)
owner();manifest=read(RUN.parent/'AllGIF/manifest.json');old=read(backup/'manifest.json')
assert {(r['source'],r['sha256']) for r in old['files']}<={(r['source'],r['sha256']) for r in manifest['files']}
old_verified=0
for r in old['files']:
    assert sha(RUN.parent/r['source'])==sha(RUN.parent/'AllGIF'/r['file'])==r['sha256']
    old_verified+=1
sources={p.relative_to(RUN.parent).as_posix():p for p in HERE.rglob('*.gif')}
entries=[r for r in manifest['files'] if r['source'].startswith('Remaining_20261024/'+NAME+'/')]
assert len(sources)==len(entries)==18 and set(sources)=={r['source'] for r in entries}
assert old['count']==1726 and manifest['count']==old['count']+len(entries)==1744
verified=[]
for r in entries:
    assert sha(sources[r['source']])==sha(RUN.parent/'AllGIF'/r['file'])==r['sha256']
    verified.append({**r,'source_copy_sha256_match':True})
final_gifs=sum(r['status']=='当前审核版本' for r in entries)
historical_gifs=len(entries)-final_gifs
assert final_gifs==12 and historical_gifs==len(list((HERE/'media_before_gif_quantization_fix_20261029').rglob('*.gif')))==6
save(HERE/'gif_archive_verification_20261029.json',{'observed_at':now(),'before':old['count'],'after':manifest['count'],'current_character_sources':len(sources),'final':final_gifs,'historical_timing_originals':historical_gifs,'all_old_source_hashes_retained':True,'old_sources_and_copies_verified':old_verified,'all_current_source_copy_matches':True,'entries':verified,'user_approved':False})
progress=read(RUN/'progress.json');item=next(r for r in progress['items'] if r['name']==NAME)
assert progress['completed_count']==107 and item['status']=='completed_pending_user_art_review' and item['visual_note']==note
rel=lambda p:p.relative_to(ROOT).as_posix()
item.update(current_stage='recorded_pending_user_art_review',completed_at=now(),production_modified=True,staging=final['art_revision'],install_verify='PASS',record='completed',new_gifs=len(entries),final_gifs=final_gifs,historical_gifs=historical_gifs,scope_record=rel(HERE/'scope_incremental_final_20261029.json'),unity_release=rel(HERE/'unity_release_final_20261029.json'),final_validation=rel(HERE/'final_validation_20261029.json'),version_binding=rel(HERE/'final_version_binding_20261029.json'),visual_review=rel(HERE/'visual_review_final_20261029/review.json'),gif_archive=rel(HERE/'gif_archive_verification_20261029.json'),user_approved=False)
remaining=sorted([r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']],key=lambda r:r['index'])
assert [r['name'] for r in remaining]==['PossessedWarg'] and remaining[0]['status']=='blocked'
material=[]
for r in remaining:
    folder=RUN/r['name'];paths=sorted(p for p in folder.rglob('*') if p.is_file())
    material.append({'index':r['index'],'name':r['name'],'status':r['status'],'files':{p.relative_to(folder).as_posix():sha(p) for p in paths},'has_install':(folder/'installed_manifest.json').exists(),'has_stage':(folder/'staged_art').exists(),'has_runtime':(folder/'runtime_summary.json').exists(),'successful_raws':[p.relative_to(folder).as_posix() for p in folder.rglob('raw.png')]})
assert material[0]['successful_raws']==['generation/Up/raw.png'] and not any(material[0][k] for k in ['has_install','has_stage','has_runtime'])
oldblock=read(RUN/'PossessedWarg/blocked_20261026_125634_639300.json')
assert sha(RUN/'PossessedWarg/generation/Down/request.json')==oldblock['request_sha256']
assert not any((RUN/'PossessedWarg/generation/Down'/name).exists() for name in ['raw.png','result.json','uncertain_result.json'])
save(HERE/'successor_assessment_final_20261029.json',{'observed_at':now(),'completed':107,'authorized':108,'remaining':material,'selected':None,'independently_recoverable_count':0,'selection_reason':'Only PossessedWarg79 remains. Its original paid Down outcome and charge are unknown, with no image, saved response or provider query ID. No independent production phase can continue. Stop chain without a successor or paid probe.','PossessedWarg_inference':'No reissue, no unsent/uncharged inference; old request and all files preserved.','current_character_network_recovery_used':0,'reset_counters':False})
progress.update(current='PossessedWarg',updated_at=now())
(RUN/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
final.update(record_completed=True,completed_count=107,authorized_count=108,gif_archive_count=manifest['count'],character_gifs=len(entries),final_gifs=final_gifs,historical_gifs=historical_gifs,gif_archive_verification_sha256=sha(HERE/'gif_archive_verification_20261029.json'),progress_sha256_after_record=sha(RUN/'progress.json'))
(HERE/'final_validation_20261029.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'completed':107,'authorized':108,'allGIF_before':old['count'],'allGIF_after':manifest['count'],'character_gifs':len(entries),'final':final_gifs,'history':historical_gifs,'old_sources_and_copies_verified':old_verified,'all_sha_match':True,'next':None,'remaining':'PossessedWarg79 blocked'},ensure_ascii=False))
