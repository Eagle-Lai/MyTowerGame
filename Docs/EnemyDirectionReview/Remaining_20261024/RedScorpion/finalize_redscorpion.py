from serial_common import *
import subprocess
owner();manifest=read(D/'installed_manifest.json');assert all(sha(ROOT/x['path'])==x['after'] for x in manifest['changes'])
base=read(D/'incremental_before_20261026.json')['files']
current={p.relative_to(ROOT).as_posix():p for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
added=[dict(path=p,sha256=sha(current[p])) for p in sorted(set(current)-set(base))]
prefix='Assets/_UIAssets/Monsters/Scorpions/RedScorpion/Directions'
unexpected=[x for x in added if not (x['path'].startswith(prefix+'/') or x['path']==prefix+'.meta')]
assert not unexpected,unexpected
for path,digest in read(D/'incremental_before_20261026.json')['protected_redscorpion'].items():
    if path!='Assets/Prefabs/Enemy/Enemy_RedScorpion.prefab':assert sha(ROOT/path)==digest,path
summary=read(D/'runtime_summary.json');assert summary['passes']==168 and summary['failures']==0 and summary['actual_frames']==684
assert [r['revision'] for r in summary['runtime']]==['runtime_r01','runtime_updeath_r01']
source=read(D/'visual_review_serial_full_20261026/sources.json');unique={(r['revision'],r['source']) for r in source['sources']}
assert len(unique)==225 and len(source['sources'])==256
frames={}
for item in summary['runtime']:
    rev=item['revision'];assert sha(D/rev/'actual_frames.jsonl')==item['records_sha256']
    rows=[json.loads(x) for x in (D/rev/'actual_frames.jsonl').read_text().splitlines() if x]
    assert len(rows)==item['frames'];frames[rev]={r['file']:sha(D/rev/r['file']) for r in rows}
binding=dict(observed_at=now(),final_manifest='installed_manifest.json',manifest_sha256=sha(D/'installed_manifest.json'),runtime_summary_sha256=sha(D/'runtime_summary.json'),raw_sources={str(p.relative_to(D)):sha(p) for p in (D/'generation').rglob('*') if p.is_file()},staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},actual_png_sha256=frames,review_sampling=dict(sheets=10,sample_slots=256,unique_actual_frames=225,method='Chronological full-body actual PNG samples; GIFs not played; not all frames individually viewed',extra_detail='attack_up_connection_detail.png'),added_files=added,unexpected_added=unexpected)
write(D/'version_binding_final_20261026.json',binding)
subprocess.run([sys.executable,str(H/'finalize_serial_character.py'),NAME,'installed_manifest.json','visual_review_serial_full_20261026'],check=True)
scope=read(D/'scope_incremental_20261026.json');scope.update(added_files=added,unexpected_added=unexpected);write(D/'scope_incremental_20261026.json',scope)
v=read(D/'final_validation_20261026.json');errors=unwrap(v['errors']);assert errors['success'] and errors['data']==[],errors
progress=read(H/'progress.json');i=next(x for x in progress['items'] if x['name']==NAME);assert i['status']=='completed_pending_user_art_review' and i['user_approved'] is False
note=(D/'record_note_utf8.txt').read_text(encoding='utf-8').strip();assert note==i['visual_note'] and '\ufffd' not in note
print(json.dumps(dict(completed_count=progress['completed_count'],new_files=len(added),sampling=binding['review_sampling'],frames=summary['actual_frames'],console_errors=0,allgif=read(H.parent/'AllGIF/manifest.json')['count']),ensure_ascii=False))
