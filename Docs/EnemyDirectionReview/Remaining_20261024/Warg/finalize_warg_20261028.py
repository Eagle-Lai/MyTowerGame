"""Seal only the actually reviewed Warg R02 and its two actual Play runs."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from PIL import Image,ImageDraw
import ast,hashlib,json,re,subprocess,sys
import numpy as np
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
NAME='Warg';OWNER='01a1830c-598a-7473-8ee1-01bccdd1f9be'
TOKEN='volcanoparasite-to-warg-20261028-7f2313bf-967a-440d-94c4-79bf845d2b6f'
RUNS=['runtime_r02','runtime_updeath_r02']
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now=lambda:datetime.now(timezone(timedelta(hours=8))).isoformat()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def data(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
chain=read(H/'conversation_chain.json');progress=read(H/'progress.json')
assert chain['state']=='active' and chain['owner_thread_id']==OWNER and chain['dispatch_token']==TOKEN and chain['current_character']==NAME
item=next(r for r in progress['items'] if r['name']==NAME)
assert item['status']=='staged_pending_visual_check' and not item.get('user_approved',False) and progress['completed_count']==91
assert not (D/'final_validation_20261028.json').exists()
baseline=read(D/'incremental_before_20261028.json');before={p:v.upper() for p,v in baseline['files'].items()}
current={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
t=baseline['target'];battle=t['battle'];art=t['art_dir']
manifest=read(D/'repair_proportions_r02/manifest.json');installed=manifest['final_files']
assert manifest['verification']['pass'] and len(installed)==21
assert all(current.get(p)==digest for p,digest in installed.items()),'Final installed manifest drift'
verify=(D/'repair_proportions_r02/verify.txt').read_text(encoding='utf-8-sig')
assert verify.strip()==manifest['verification']['report'].strip() and all(s.startswith('PASS ') for s in verify.splitlines())
assert 'PASS YooAsset prefab and artwork collectors present' in verify
assert all(p in [battle,battle+'.meta'] or p.startswith(art+'/') for p in installed)
changes=[{'path':p,'before':before.get(p),'after':current.get(p)} for p in sorted(set(before)|set(current)) if before.get(p)!=current.get(p)]
side_effects=[]
for r in changes:
    if r['path']=='Assets/StreamingAssets/build_info':
        assert current['Assets/Reporter/Editor/ReporterEditor.cs']==before['Assets/Reporter/Editor/ReporterEditor.cs']
        assert re.fullmatch(r'Build from .+ at .+',(ROOT/r['path']).read_text(encoding='utf-8'))
        side_effects.append(dict(r,origin='Unmodified ReporterEditor Play timestamp'))
allowed=set(installed)|{art+'.meta'}|{r['path'] for r in side_effects}
unexpected=[r for r in changes if r['path'] not in allowed];assert not unexpected,unexpected
protected={p:v.upper() for p,v in baseline['protected_six'].items()}
protected_drift=[p for p,v in protected.items() if p!=battle and current.get(p)!=v];assert not protected_drift
assert all(sha(D/'reference'/Path(p).name)==v for p,v in protected.items())
cs_drift=[p for p in set(before)|set(current) if p.endswith('.cs') and before.get(p)!=current.get(p)];assert not cs_drift
audit_source=H.parent/'Batch01_10/audit_scope.py'
tree=ast.parse(audit_source.read_text(encoding='utf-8-sig'));definitions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
ns={'re':re,'hashlib':hashlib,'HERE':H,'ROOT':ROOT,'targets':{NAME:t}}
exec(compile(definitions,str(audit_source),'exec'),ns);semantic=ns['semantic'](NAME);assert semantic['pass'],semantic
staged={f:sha(D/'staged_art'/f) for f in [NAME+'_Directions.png',NAME+'_Directions.sprites.json',NAME+'_Directions.layout.json']}
assert all(current[art+'/'+f]==v for f,v in staged.items())
parts={}
for s in read(D/'staged_art/Warg_Directions.sprites.json')['sprites']:
    path=D/'staged_art'/(s['name']+'.png');im=Image.open(path).convert('RGBA');a=np.asarray(im)
    opaque=a[:,:,3]>0
    pad=Image.new('L',(im.width+2,im.height+2),255);pad.paste(Image.fromarray(np.where(opaque,0,255).astype('uint8')),(1,1));ImageDraw.floodfill(pad,(0,0),127)
    holes=int((np.asarray(pad)[1:-1,1:-1]==255).sum())
    magenta=int(((a[:,:,0]>180)&(a[:,:,2]>180)&(a[:,:,1]<100)&opaque).sum())
    assert holes==0 and magenta==0 and opaque.any(),s['name']
    parts[s['name']]={'sha256':sha(path),'size':list(im.size),'enclosed_alpha_holes':holes,'opaque_magenta_pixels':magenta,'pivot':[s['pivotX'],s['pivotY']]}
assert len(parts)==14
runtime=read(D/'runtime_summary.json');assert (runtime['passes'],runtime['failures'],runtime['actual_frames'])==(168,0,601)
assert [r['revision'] for r in runtime['runtime']]==RUNS
frames={}
for run in runtime['runtime']:
    rev=run['revision'];folder=D/rev
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8-sig').splitlines()
    records=[json.loads(l) for l in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l]
    assert (run['pass'],run['fail'])==(84,0) and len(records)==run['frames']
    assert sum(s.startswith('PASS ') for s in checks)==84 and not any(s.startswith('FAIL ') for s in checks)
    assert all(b['frame']>a['frame'] and b['realtime']>a['realtime'] for a,b in zip(records,records[1:]))
    assert all(not r['shadow'] for r in records)
    assert sha(folder/'actual_frames.jsonl')==run['records_sha256']
    frames[rev]={r['file']:sha(folder/r['file']) for r in records}
    assert all(frames[rev].values()) and len(frames[rev])==len(list((folder/'frames').glob('*.png')))==run['frames']
    start=read(D/(rev+'_start.json'));assert start['project']['projectRoot'].lower()=='e:/mytowergame' and start['revision']==rev and data(start['response'])['data']['result'] is True
    assert read(D/(rev+'_returned.json'))['state']=={'playing':False,'review':False,'scene':'Assets/Scenes/Boot.unity','dirty':False}
assert read(D/'runtime_updeath_r02_start.json')['death_up'] is True
sample=read(D/'gif_samples_r02_20261028/samples.json');assert len(sample['samples'])==60
assert len({(r['revision'],r['file']) for r in sample['samples']})==12
assert all(sha(D/r['revision']/r['file'])==r['gif_sha256'] for r in sample['samples'])
source_board=read(D/'visual_review_r02_20261028/sources.json')
assert len(source_board['sources'])==256 and len({(r['revision'],r['source']) for r in source_board['sources']})==228
probe_path=D/'unity_release_probe_20261028_response.json';probe=read(probe_path)
assert probe['success'] and probe['transport']=='http://127.0.0.1:8088/mcp' and probe['project']['projectRoot'].lower()=='e:/mytowergame'
state=probe['results'][1]['data'];errors=data(probe['results'][2]);live=data(probe['results'][3])['data']['result']
assert state['advice']['ready_for_tools'] and state['activity']['phase']=='idle' and not state['staleness']['is_stale']
assert not state['tests']['is_running'] and not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending'] and not state['assets']['is_updating']
assert errors['data']==[] and live['scene']=='Assets/Scenes/Boot.unity' and live['sceneCount']==1
assert all(live[k] is False for k in ['playing','compiling','failed','updating','sceneDirty','balance','recording','review','manual'])
reviewed=['offline_rig_proof_r02.png','runtime_visual_strip.png']+[r+'/four_directions.png' for r in RUNS]
reviewed += ['visual_review_r02_20261028/'+r+'_'+suffix+'.png' for r in RUNS for suffix in ['sequence_0','sequence_1','sequence_2','walk_cycle','angry_detail']]
reviewed += ['gif_samples_r02_20261028/'+r+'_samples.png' for r in RUNS]
originals=['runtime_r02/frames/'+p for p in ['Attack_00124.png','Hurt_00141.png','ContinuousTurns_00253.png','UpWalk_00009.png','DeathAutoRecycle_00148.png']]+['runtime_updeath_r02/frames/DeathAutoRecycle_00144.png']
note='R02实际查看两轮四方向图、runtime strip、10张时序/步态/愤怒细节板（256采样位、228张不同真实PNG）、6张原尺寸PNG及12个最终GIF各5个编码帧，共60帧。Up为无脸无牙的后脑、斑点背毛及后跟，Down为双金眼、奶油色獠牙，攻击切换张口尖牙，死亡有垂舌表情。四足根部保持连接，头颈及长尾根重叠固定；短幅交错步态、尾部摆动，攻击有前压与回收。受击白闪恢复，Down/Up两向死亡侧倾、全身缩小淡出后回收，同实例复用正常，连续左右转向无倒置，暂停后恢复及倍速有时序证据。R01正背头身偏小已否决；R02仅正背布局围绕地面基线等比放大1.6。原HP位置保留，在部分正背姿态覆盖耳/背头或尾尖。时序板的顶部裁剪不是生产裁切，已用原PNG核对。GIF为编码帧抽样，非实时播放或逐GIF全帧审核；用户美术验收待进行。'
visual={'reviewed_at':now(),'character':NAME,'owner_thread_id':OWNER,'dispatch_token':TOKEN,'final_revision':'R02','runs':RUNS,'reviewed_images':{p:sha(D/p) for p in reviewed},'selected_original_pngs':{p:sha(D/p) for p in originals},'sample_positions':256,'unique_board_source_pngs':228,'gif_count':12,'encoded_gif_samples':60,'gif_sample_manifest':'gif_samples_r02_20261028/samples.json','observations':note,'limitations':['Encoded-frame sampling, not real-time playback or exhaustive GIF review.','Sequence board crop truncates upper portions; original PNGs and offline proof inspected.','Original HP position overlaps upper rear head / far tail in some poses; original UI semantics preserved.'],'rejected_revision':{'R01':'Axial head/body undersized despite 168/0 technical checks; retained.'},'technical_visual_pass':True,'user_approved':False}
assert all(visual['reviewed_images'].values()) and all(visual['selected_original_pngs'].values())
write(D/'visual_review_r02_20261028/review.json',visual);(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
scope={'observed_at':now(),'baseline':'incremental_before_20261028.json','baseline_sha256':sha(D/'incremental_before_20261028.json'),'baseline_files':len(before),'current_files':len(current),'comparison':'Full path union across Assets/Packages/ProjectSettings/Luban; current disk baseline, never Git HEAD.','changes':changes,'unexpected_incremental':unexpected,'automatic_editor_side_effects':side_effects,'protected_six':protected,'protected_drift':protected_drift,'shared_CSharp_drift':cs_drift,'installed_manifest_paths':installed,'installed_manifest_drift':[],'staged_to_installed_hashes':staged,'prefab_semantics':semantic,'stage_parts':parts,'legacy_global_note':'Prior historical global audit had 291 unexpected paths and six other-character semantic failures. This is a Warg-only incremental audit, not a global PASS or a new full historical re-audit.'}
write(D/'scope_incremental_final_20261028.json',scope)
runtime.update(final_revision='R02',visual_reviewed=True,visual_review_file='visual_review_r02_20261028/review.json',visual_note=note,user_approved=False,status='completed_pending_user_art_review');write(D/'runtime_summary.json',runtime)
archive_path=H.parent/'AllGIF/manifest.json';archive_before=read(archive_path)['count']
record=subprocess.run([sys.executable,str(H/'record_review.py'),NAME,note],capture_output=True,text=True,encoding='utf-8',check=True)
progress=read(H/'progress.json');item=next(r for r in progress['items'] if r['name']==NAME)
assert progress['completed_count']==92 and item['status']=='completed_pending_user_art_review' and not item['user_approved'] and item['actual_frames']==601
archive=read(archive_path);by_source={r['source']:r for r in archive['files']};pairs=[]
for run in ['runtime_r01','runtime_updeath_r01',*RUNS]:
    files=list((D/run).glob('*.gif'));assert len(files)==6
    for p in files:
        source='Remaining_20261024/Warg/'+run+'/'+p.name;r=by_source[source];digest=sha(p)
        assert r['sha256']==digest==sha(H.parent/'AllGIF'/r['file'])
        assert r['status']==('当前审核版本' if run in RUNS else '历史或准备材料')
        pairs.append({'source':source,'archive':r['file'],'sha256':digest,'status':r['status']})
archive_report={'verified_at':now(),'source_gif_count':24,'matching_archive_count':24,'final_review_gifs':12,'historical_gifs':12,'global_archive_count_before':archive_before,'global_archive_count':archive['count'],'all_source_and_archive_sha256_match':True,'files':pairs,'manifest_sha256':sha(archive_path)}
write(D/'gif_archive_verification_20261028.json',archive_report)
remaining=[r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[r for r in remaining if r['status'] not in ['not_started','blocked']]
selected=min(recoverable or [r for r in remaining if r['status']!='blocked'],key=lambda r:r['index']);assert selected['name']=='Wasp'
item.update(stage='recorded_pending_user_art_review',final_revision='R02',final_validation_file='Warg/final_validation_20261028.json',version_binding_file='Warg/version_binding_final_20261028.json',scope_file='Warg/scope_incremental_final_20261028.json',visual_review_file='Warg/visual_review_r02_20261028/review.json',gif_archive_file='Warg/gif_archive_verification_20261028.json')
progress.update(current='Wasp',updated_at=now());write(H/'progress.json',progress)
evidence={p.relative_to(D).as_posix():sha(p) for p in sorted(D.rglob('*')) if p.is_file() and 'frames' not in p.relative_to(D).parts and p.name not in ['version_binding_final_20261028.json','final_validation_20261028.json']}
binding={'observed_at':now(),'final_revision':'R02','manifest':'repair_proportions_r02/manifest.json','manifest_sha256':sha(D/'repair_proportions_r02/manifest.json'),'installed_files':installed,'production_scope_files':{r['path']:r['after'] for r in changes},'files':evidence,'actual_png_frames':frames,'frame_total':601,'note':'Final full 21-path production snapshot, 601 final actual PNG frames, 12 current /12 historical GIFs, technical logs and actual visual sampling are bound. R01 is rejected for size.'}
write(D/'version_binding_final_20261028.json',binding)
final={'observed_at':now(),'character':NAME,'owner_thread_id':OWNER,'dispatch_token':TOKEN,'status':'completed_pending_user_art_review','user_approved':False,'final_revision':'R02','passes':168,'failures':0,'actual_png_frames':601,'runtime':runtime['runtime'],'installer_verify_pass':True,'manifest':'repair_proportions_r02/manifest.json','manifest_sha256':sha(D/'repair_proportions_r02/manifest.json'),'incremental_scope_file':'scope_incremental_final_20261028.json','incremental_scope_sha256':sha(D/'scope_incremental_final_20261028.json'),'incremental_changes':len(changes),'incremental_unexpected':0,'prefab_semantic_pass':True,'version_binding_file':'version_binding_final_20261028.json','version_binding_sha256':sha(D/'version_binding_final_20261028.json'),'visual_review_file':'visual_review_r02_20261028/review.json','visual_review_sha256':sha(D/'visual_review_r02_20261028/review.json'),'gif_archive_file':'gif_archive_verification_20261028.json','gif_archive_sha256':sha(D/'gif_archive_verification_20261028.json'),'archived_character_gifs':24,'final_review_gifs':12,'global_archive_count':archive['count'],'unity':{'transport':probe['transport'],'project':probe['project'],'instance_id':state['unity']['instance_id'],'live_probe':live,'ready_for_tools':True,'console_errors':0,'external_changes_dirty':state['assets']['external_changes_dirty'],'evidence':probe_path.name,'cache_note':'Existing ForceUpdate rebuilt a factual snapshot after idle timestamp staleness; no plugin source edited.'},'progress':{'completed_count':92,'authorized_count':108,'next_candidate':'Wasp'},'record_review_output':record.stdout.strip(),'legacy_global_scope_warning':scope['legacy_global_note']}
write(D/'final_validation_20261028.json',final)
chain=read(H/'conversation_chain.json');assert chain['state']=='active' and chain['owner_thread_id']==OWNER and chain['dispatch_token']==TOKEN
chain.update(current_stage='recorded_pending_user_art_review',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Warg/final_validation_20261028.json',updated_at=now());write(H/'conversation_chain.json',chain)
print(json.dumps({'character':NAME,'status':final['status'],'completed_count':92,'baseline_files':len(before),'current_files':len(current),'scope_changes':len(changes),'incremental_unexpected':0,'semantic_pass':True,'passes':168,'failures':0,'frames':601,'character_gifs':24,'archive_count':archive['count'],'next':'Wasp'},ensure_ascii=False))
