"""Record the sealed review and verify all target GIF archive revisions."""
from session_treasurechest import *
owner();progress=read(H/'progress.json');assert progress['completed_count']==87
binding=read(D/'version_binding_final_20261028.json')
assert all(sha(D/p)==s for p,s in binding['files'].items())
assert all(sha(R/p)==s for p,s in binding['installed_files'].items())
assert all(sha(R/p)==s for p,s in binding['production_scope_files'].items())
assert all(sha(R/p)==s for p,s in binding['external_evidence'].items())
review=read(D/'visual_review_final_20261028/review.json');assert review['user_approved'] is False and review['distinct_actual_frame_samples']==288
note=(D/'record_note_utf8.txt').read_text(encoding='utf-8').strip();assert note==review['note'] and '\ufffd' not in note
subprocess.run([sys.executable,str(H/'character_step.py'),'record',NAME,note],check=True)
progress=read(H/'progress.json');item=next(x for x in progress['items'] if x['name']==NAME)
assert progress['completed_count']==88 and item['status']=='completed_pending_user_art_review' and item['user_approved'] is False and item['visual_note']==note
item.update(current_stage='recorded_pending_user_art_review',final_install_manifest='TreasureChest/installed_manifest_r02.json',final_visual_review='TreasureChest/visual_review_final_20261028/review.json',final_validation='TreasureChest/final_validation_20261028.json',final_scope='TreasureChest/scope_incremental_final_20261028.json',final_version_binding='TreasureChest/version_binding_final_20261028.json',initial_up_outcome='uncertain_preserved',up_extra_network_requests=2,final_runtime_revisions=['runtime_r02','runtime_updeath_r02'],historical_runtime_revisions=['runtime_r01','runtime_updeath_r01'])
write(H/'progress.json',progress)
gifs=read(H.parent/'AllGIF/manifest.json');own=[x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/TreasureChest/')];active=[x for x in own if x['status']=='当前审核版本']
assert {x['source'] for x in own}=={p.relative_to(H.parent).as_posix() for p in D.rglob('*.gif')}
assert len(own)==24 and len(active)==12 and {x['source'].split('/')[2] for x in active}=={'runtime_r02','runtime_updeath_r02'}
assert all(sha(H.parent/x['source'])==x['sha256'] and sha(H.parent/'AllGIF'/x['file'])==x['sha256'] for x in own)
write(D/'gif_archive_verification_20261028.json',dict(observed_at=now(),total=gifs['count'],character_count=len(own),current_count=len(active),historical_count=len(own)-len(active),files=own,sha256_match=True,all_available_character_gifs_archived=True))
chain=owner();chain.update(character_status_at_handoff=item['status'],completed_count_snapshot=88,current_stage='recorded_pending_user_art_review',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/TreasureChest/final_validation_20261028.json',updated_at=now());write(H/'conversation_chain.json',chain)
print(json.dumps(dict(completed=88,current_gifs=len(active),historical_gifs=len(own)-len(active),archive_total=gifs['count'],user_approved=False),ensure_ascii=False))
