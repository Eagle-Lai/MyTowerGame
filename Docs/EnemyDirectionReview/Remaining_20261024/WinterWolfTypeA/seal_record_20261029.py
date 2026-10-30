from session_current import *

owner();assert not (HERE/'gif_archive_verification_20261029.json').exists()
manifest=read(RUN.parent/'AllGIF/manifest.json');old=read(HERE/'docs_before_final_record_20261029/manifest.json')
assert old['count']==1642 and manifest['count']==1660
assert {(x['source'],x['sha256']) for x in old['files']}<={(x['source'],x['sha256']) for x in manifest['files']}
sources={p.relative_to(RUN.parent).as_posix():p for p in HERE.rglob('*.gif')}
entries=[r for r in manifest['files'] if r['source'].startswith('Remaining_20261024/WinterWolfTypeA/')]
assert len(sources)==len(entries)==18 and set(sources)=={r['source'] for r in entries}
verified=[]
for r in entries:
    source=sources[r['source']];copy=RUN.parent/'AllGIF'/r['file'];ok=sha(source)==sha(copy)==r['sha256'];assert ok
    verified.append({**r,'source_copy_sha256_match':True})
assert sum(r['status']=='当前审核版本' for r in entries)==12
save(HERE/'gif_archive_verification_20261029.json',{'observed_at':now(),'before':old['count'],'after':manifest['count'],'current_character_sources':18,'final':12,'historical_timing_originals':6,'all_old_source_hashes_retained':True,'all_current_source_copy_matches':True,'entries':verified,'user_approved':False})
progress=read(RUN/'progress.json');item=next(r for r in progress['items'] if r['name']==NAME)
assert item['status']=='completed_pending_user_art_review' and progress['completed_count']==102
history={k:item[k] for k in ['blocked_at','blocked_reason','blocked_record'] if k in item}
item.setdefault('historical_blocks',[]).append({**history,'resolved_at':now(),'resolution':'Down03 HTTP200 after user generator edge fix; original three outcomes and charges remain unknown; standing2/2 not reset.'})
item.update(blocked_at=None,blocked_reason=None,current_stage='recorded_pending_user_art_review',completed_at=now(),production_modified=True,staging='Up_local03_Down03_alpha_r01_layout_r01',install_verify='PASS',record='completed',new_gifs=18,final_gifs=12,historical_gifs=6,scope_record='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/scope_incremental_final_20261029.json',unity_release='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/unity_release_final_20261029.json',final_validation='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/final_validation_20261029.json',version_binding='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/final_version_binding_20261029.json',visual_review='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/visual_review_final_20261029/review.json',gif_archive='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/gif_archive_verification_20261029.json',user_approved=False)
remaining=[r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']]
material=[]
for r in remaining:
    folder=RUN/r['name'];paths=sorted(p for p in folder.rglob('*') if p.is_file())
    material.append({'index':r['index'],'name':r['name'],'status':r['status'],'files':{p.relative_to(folder).as_posix():sha(p) for p in paths},'has_install':(folder/'installed_manifest.json').exists(),'has_stage':(folder/'staged_art').exists(),'has_runtime':(folder/'runtime_summary.json').exists(),'successful_raws':[p.relative_to(folder).as_posix() for p in folder.rglob('raw.png')]})
assert [r['name'] for r in remaining]==['PossessedWarg','WinterWolfTypeB','Wolf','WolfHound','WolfMounfed','Zombie']
warg=material[0];assert warg['successful_raws']==['generation/Up/raw.png'] and not any(warg[k] for k in ['has_install','has_stage','has_runtime'])
old_assessment=read(HERE/'successor_assessment_blocked_20261029_180355.json')
save(HERE/'successor_assessment_final_20261029.json',{'observed_at':now(),'completed':102,'authorized':108,'remaining':material,'selected':'WinterWolfTypeB','selected_index':114,'selection_reason':'No independently recoverable started character; PossessedWarg Down still unknown. Fresh WinterWolfTypeB can proceed through the user-fixed direct pinned Curl route now proven by WinterWolfTypeA Down03 production HTTP200. No diagnostic paid probe.','PossessedWarg_inference':'No saved new image/result or provider query ID; external claim unsent rejected; original unknown request remains preserved.','previous_assessment_sha256':sha(HERE/'successor_assessment_blocked_20261029_180355.json'),'standing_recovery_used_current_character':2,'standing_recovery_limit_current_character':2,'reset_counters':False})
progress.update(current='WinterWolfTypeB',updated_at=now())
(RUN/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
final=read(HERE/'final_validation_20261029.json');final.update(record_completed=True,completed_count=102,authorized_count=108,gif_archive_count=1660,character_gifs=18,final_gifs=12,historical_gifs=6,gif_archive_verification_sha256=sha(HERE/'gif_archive_verification_20261029.json'),progress_sha256_after_record=sha(RUN/'progress.json'))
(HERE/'final_validation_20261029.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'completed':102,'authorized':108,'allGIF':1660,'character_gifs':18,'final':12,'history':6,'all_sha_match':True,'next':'WinterWolfTypeB','remaining_count':len(remaining)},ensure_ascii=False))
