from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib
REV=Path(__file__).resolve().parent;CHAR=REV.parent;HERE=CHAR.parent;ROOT=HERE.parents[2]
path=HERE/'progress.json'
progress=json.loads(path.read_text(encoding='utf-8'))
item=next(x for x in progress['items'] if x['name']=='IceParasite')
note=(REV/'visual_note_utf8.txt').read_text(encoding='utf-8').strip()
assert item['status']=='completed_pending_user_art_review'
assert item['visual_note'].strip()==note and '??' not in item['visual_note'] and chr(0xfffd) not in item['visual_note']
assert progress['completed_count']==38 and progress['current']=='InfectedRat'
previous_block={k:item[k] for k in ['blocked_reason','blocked_category','blocked_at','blocked_evidence','resume_from'] if k in item}
for key in previous_block:item.pop(key)
item.update(visual_passed=True,repair_revision='repair_pool_rotation_r02',visual_evidence='IceParasite/repair_pool_rotation_r02/final_review.json',block_resolved_at=datetime.now(timezone(timedelta(hours=8))).isoformat())
path.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
readback=json.loads(path.read_text(encoding='utf-8'))
entry=next(x for x in readback['items'] if x['name']=='IceParasite')
assert entry['visual_note'].strip()==note and entry['visual_passed'] and '??' not in entry['visual_note'] and chr(0xfffd) not in entry['visual_note']
archive=ROOT/'Docs/EnemyDirectionReview/AllGIF'
manifest=json.loads((archive/'manifest.json').read_text(encoding='utf-8'))
final=[x for x in manifest['files'] if x['source'].startswith('Remaining_20261024/IceParasite/runtime_r02/') or x['source'].startswith('Remaining_20261024/IceParasite/runtime_updeath_r02/')]
assert len(final)==12 and all(x['status']=='当前审核版本' for x in final)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
assert all(sha(archive/x['file'])==x['sha256']==sha(ROOT/'Docs/EnemyDirectionReview'/x['source']) for x in final)
assert manifest['count']==len(manifest['files'])==585
report={'record_success':True,'visual_note_utf8_readback':entry['visual_note'],'previous_block_resolved':previous_block,'status':entry['status'],'runtime':entry['runtime'],'actual_frames':entry['actual_frames'],'completed_count_before':37,'completed_count_after':readback['completed_count'],'current':readback['current'],'gif_new':len(final),'gif_total':manifest['count'],'sprites_reused':12,'production_changes_this_session':['Ready_Directions.anim','Walk_Directions.anim'],'automatic_editor_side_effect':'Assets/StreamingAssets/build_info','image_count':6,'shared_code_changed':False,'prefab_changed_this_session':False,'user_approved':False}
(REV/'completion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
