"""Strict final RatKing version and new-file audit, then the established record flow."""
from pathlib import Path
import json,os,hashlib,subprocess,sys
from datetime import datetime,timezone,timedelta
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='RatKing' and c['dispatch_token']=='rat-to-ratking-5222dbfeb5d146d7ad666975e4e8d90e'
manifest=read(D/'repair_tail_r06/manifest.json');assert all(sha(ROOT/x['path'])==x['after'] for x in manifest['changes'])
base=read(D/'incremental_before_20261026.json')['files']
current={p.relative_to(ROOT).as_posix():p for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
added=[dict(path=p,sha256=sha(current[p])) for p in sorted(set(current)-set(base))]
prefix='Assets/_UIAssets/Monsters/Rats/RatKing/Directions'
unexpected_new=[x for x in added if not (x['path'].startswith(prefix+'/') or x['path']==prefix+'.meta')]
assert not unexpected_new,unexpected_new
for path,digest in read(D/'incremental_before_20261026.json')['protected_ratking'].items():
    if path=='Assets/Prefabs/Enemy/Enemy_RatKing.prefab':continue
    assert sha(ROOT/path)==digest,path
summary=read(D/'runtime_summary.json');assert summary['passes']==168 and summary['failures']==0 and summary['actual_frames']==680
assert [r['revision'] for r in summary['runtime']]==['runtime_final_r03','runtime_final_updeath_r03']
source=read(D/'visual_review_final_serial_20261026/sources.json')
unique={(r['revision'],r['source']) for r in source['sources']}
frames={}
for item in summary['runtime']:
    rev=item['revision'];assert sha(D/rev/'actual_frames.jsonl')==item['records_sha256']
    index=[json.loads(x) for x in (D/rev/'actual_frames.jsonl').read_text().splitlines() if x]
    assert len(index)==item['frames']
    frames[rev]={r['file']:sha(D/rev/r['file']) for r in index}
binding=dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),final_manifest='repair_tail_r06/manifest.json',manifest_sha256=sha(D/'repair_tail_r06/manifest.json'),runtime_summary_sha256=sha(D/'runtime_summary.json'),raw_sources={k:{p.name:sha(p) for p in (D/'generation'/k).iterdir() if p.is_file()} for k in ['Up','Down']},staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},actual_png_sha256=frames,review_sampling=dict(sheets=10,sample_slots=len(source['sources']),unique_actual_frames=len(unique),method='Chronological real PNG samples; GIFs not played; not all saved frames viewed'),added_files=added,unexpected_added=unexpected_new)
write(D/'version_binding_final_20261026.json',binding)
subprocess.run([sys.executable,str(H/'finalize_serial_character.py'),'RatKing','repair_tail_r06/manifest.json','visual_review_final_serial_20261026'],check=True)
p=D/'scope_incremental_20261026.json';scope=read(p);scope.update(added_files=added,unexpected_added=unexpected_new);write(p,scope)
v=read(D/'final_validation_20261026.json');errors=v['errors'].get('structuredContent') or json.loads(v['errors']['content'][0]['text']);assert errors['success'] and errors['data']==[],errors
progress=read(H/'progress.json');i=next(x for x in progress['items'] if x['name']=='RatKing');assert i['status']=='completed_pending_user_art_review' and i['user_approved'] is False
note=(D/'record_note_utf8.txt').read_text(encoding='utf-8').strip();assert i['visual_note']==note and '\ufffd' not in note and '?'*3 not in note
print(json.dumps(dict(completed_count=progress['completed_count'],new_files=len(added),sampling=binding['review_sampling'],frames=summary['actual_frames'],console_errors=0,allgif=read(H.parent/'AllGIF/manifest.json')['count']),ensure_ascii=False))
