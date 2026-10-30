from pathlib import Path
import json,hashlib
out=Path(__file__).resolve().parent
d=out.parent
here=d.parent
p=here/'progress.json'
progress=json.loads(p.read_text(encoding='utf-8'))
item=next(x for x in progress['items'] if x['name']=='Porcupine')
note=(out/'visual_note_utf8.txt').read_text(encoding='utf-8').strip()
assert item['visual_note'].strip()==note and '??' not in note and chr(65533) not in note
assert item['status']=='completed_pending_user_art_review' and progress['completed_count']==63
(out/'progress_after_record_before_metadata.json').write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
resolved={k:item.pop(k) for k in list(item) if k.startswith('blocked_')}
item.update(visual_pass=True,visual_reviewed=True,viewed_image_count=6,visual_evidence='Porcupine/repair_pose_r01/final_review.json',repair_revision='repair_pose_r01',resolved_blocked_evidence='Porcupine/blocked_visual_20261026.json')
(out/'resolved_blocked_metadata.json').write_text(json.dumps(resolved,ensure_ascii=False,indent=2),encoding='utf-8')
p.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
readback=json.loads(p.read_text(encoding='utf-8'))
readitem=next(x for x in readback['items'] if x['name']=='Porcupine')
assert readitem['visual_note'].strip()==note and readitem['visual_pass'] is True
m=json.loads((here.parent/'AllGIF/manifest.json').read_text(encoding='utf-8'))
files=[x for x in m['files'] if x['source'].startswith('Remaining_20261024/Porcupine/')]
assert len(files)==24
for f in files:
 source=here.parent/f['source']
 dest=here.parent/'AllGIF'/f['file']
 expected=f['sha256']
 assert hashlib.sha256(source.read_bytes()).hexdigest().upper()==expected==hashlib.sha256(dest.read_bytes()).hexdigest().upper()
 expected_status='当前审核版本' if '/runtime_r02/' in f['source'] or '/runtime_updeath_r02/' in f['source'] else '历史或准备材料'
 assert f['status']==expected_status
result={'name':'Porcupine','status':readitem['status'],'completed_count':readback['completed_count'],'current':readback['current'],'visual_note_encoding':'UTF-8 exact match; no replacement characters','visual_pass':readitem['visual_pass'],'runtime':readitem['runtime'],'actual_frames':readitem['actual_frames'],'new_gifs':12,'allgif_newly_archived_including_old_r01':24,'allgif_total':m['count'],'archive_hashes':'24 source/copy pairs match','index_exists':(here.parent/'AllGIF/index.html').is_file(),'sprites_reused':12,'production_changes_this_run':2,'rebuild_requirement':'Reapply Porcupine/repair_pose_r01/patch.cs.txt after a future full Builder rebuild.'}
(out/'record_integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
print(readitem['visual_note'])
