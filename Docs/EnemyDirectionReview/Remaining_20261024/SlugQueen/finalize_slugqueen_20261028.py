"""Bind actually reviewed SlugQueen r02 evidence, release Unity, record and archive."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,re,subprocess,sys,time
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client,URL
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
chain=read(H/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='SlugQueen' and chain['dispatch_token']=='sheep-to-slugqueen-5dd11f24cb8646d0ac5a622d232ec22d'
assert not (D/'final_validation_20261028.json').exists(),'Inspect prior finalization'
progress=read(H/'progress.json');assert progress['completed_count']==84
assert next(x for x in progress['items'] if x['name']=='SlugQueen')['status']!='completed_pending_user_art_review'
baseline=read(D/'incremental_before_20261028.json');before={p:s.upper() for p,s in baseline['files'].items()}
current={p.relative_to(R).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (R/folder).rglob('*') if p.is_file()}
changes=[dict(path=p,before=before.get(p),after=current.get(p)) for p in sorted(set(before)|set(current)) if before.get(p)!=current.get(p)]
battle='Assets/Prefabs/Enemy/Enemy_SlugQueen.prefab';art='Assets/_UIAssets/Monsters/Insects/SlugQueen/Directions'
unexpected=[];side_effects=[]
for x in changes:
    p=x['path']
    if p==battle or p.startswith(art+'/') or p==art+'.meta':continue
    if p=='Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs']==before['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+',(R/p).read_text(encoding='utf-8')):
        side_effects.append(dict(x,origin='Unmodified ReporterEditor InitializeOnLoad Play timestamp'))
    else:unexpected.append(x)
assert not unexpected,unexpected
protected_drift=[p for p,s in baseline['protected_six'].items() if p!=battle and sha(R/p)!=s.upper()]
assert not protected_drift,protected_drift
legacy_before=read(H/'scope_SlugQueen_before_20261028.json');legacy_after=read(H/'scope_SlugQueen_r02_final_20261028.json')
old_unexpected={x['path']:x.get('after') for x in legacy_before['unexpected']}
assert {x['path']:x.get('after') for x in legacy_after['unexpected']}==old_unexpected
old_failures={n:s['unexpected'] for n,s in legacy_before['semantics'].items() if not s['pass']}
new_failures={n:s['unexpected'] for n,s in legacy_after['semantics'].items() if not s['pass']}
assert old_failures==new_failures and legacy_after['semantics']['SlugQueen']['pass']
manifest=read(D/'installed_manifest.json')
assert all(sha(R/x['path'])==x['after'].upper() for x in manifest['changes'])
verify=manifest['verification']['data']['result'];assert verify['pass']
assert (D/'installed_verify.txt').read_text(encoding='utf-8')==verify['report']
preplay=read(D/'preplay_version_binding_r02_20261028.json')
assert preplay['transport']=='http://127.0.0.1:8088/mcp' and sha(D/'installed_manifest.json')==preplay['installed_manifest_sha256']
assert all(sha(R/p)==s for p,s in preplay['installed_files'].items())
original=read(D/'original_sprite_contracts_20261028.json');prefab=(R/battle).read_text(encoding='utf-8-sig')
for fid,value in original.items():
    block=re.search(r'^--- !u!212 &'+fid+r'\s*\n(.*?)(?=^--- !u!|\Z)',prefab,re.M|re.S)
    assert block and re.search(r'^  m_Sprite: .+$',block[1],re.M)[0]==value,fid
offline=read(D/'offline_review_20261028.json')
assert all(sha(D/'staged_art'/p)==s for p,s in offline['staging_files'].items())
for p in ['SlugQueen_Directions.png','SlugQueen_Directions.layout.json','SlugQueen_Directions.sprites.json']:
    assert sha(D/'staged_art'/p)==sha(R/art/p)
for direction in ['Up','Down']:
    result=read(D/'generation'/direction/'result.json')
    assert result['status']==200 and result['bytes']==(D/'generation'/direction/'raw.png').stat().st_size
    assert sha(D/'generation'/direction/'raw.png')==offline['raw_sha256'][direction]
selection=read(D/'art_selection.json');assert selection['Up']=='local_raster_revision_02/Up_sheet.png' and selection['Down']=='generation/Down/raw.png'
local=read(D/'local_raster_revision_02/processing.json')
assert sha(D/selection['Up'])==local['output_sha256'] and local['paid_request'] is False
assert read(D/'local_raster_revision_02/review.json')['accepted_for_install']
repair=read(D/'side_reuse_repair_r01/repair.json');preserve=repair['preservation_checks']
assert preserve['originalCurvesEventsTimingPreserved'] and preserve['originalFloatBindings']==70 and preserve['afterFloatBindings']==73
assert sha(R/repair['path'])==repair['after']
pose=read(D/'reuse_live_inspection_runtime_r01_20261028.json')
assert pose['initial_horizontal_body_z']==[0.0] and pose['after_reuse_horizontal_body_z']==[0.0]
scope=dict(observed_at=now(),baseline='incremental_before_20261028.json',baseline_sha256=sha(D/'incremental_before_20261028.json'),baseline_files=len(before),current_files=len(current),comparison='Union of before/current paths including additions and deletions',changes=changes,unexpected_incremental=unexpected,automatic_editor_side_effects=side_effects,protected_six=baseline['protected_six'],protected_drift=protected_drift,original_sprite_contracts=original,prefab_semantics=legacy_after['semantics']['SlugQueen'],installed_asset_drift=[],staged_production_drift=[],legacy_before='scope_SlugQueen_before_20261028.json',legacy_after='scope_SlugQueen_r02_final_20261028.json',legacy_pass=legacy_after['pass'],legacy_unexpected_count=len(old_unexpected),legacy_semantic_failures=list(new_failures),new_unexpected_vs_preexisting_legacy=[],new_semantic_failures={},note='Historical global differences remain; no global PASS claim')
write(D/'scope_incremental_final_20261028.json',scope)
runtime=read(D/'runtime_summary.json')
assert runtime['passes']==168 and runtime['failures']==0 and runtime['actual_frames']==674
assert [x['revision'] for x in runtime['runtime']]==['runtime_r02','runtime_updeath_r02']
frames={}
for item in runtime['runtime']:
    folder=D/item['revision'];assert sha(folder/'actual_frames.jsonl')==item['records_sha256']
    rows=[json.loads(line) for line in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks)==84 and not any(x.startswith('FAIL ') for x in checks)
    assert len(rows)==item['frames'] and all(a['frame']<b['frame'] for a,b in zip(rows,rows[1:]))
    frames[item['revision']]={x['file']:sha(folder/x['file']) for x in rows}
    assert len(frames[item['revision']])==len(rows) and all(frames[item['revision']].values())
assert sum(map(len,frames.values()))==674
visual=D/'visual_review_final_r02_20261028';sources=read(visual/'sources.json')
sheets=sorted({x['sheet'] for x in sources['sources']});unique=len({(x['revision'],x['source']) for x in sources['sources']})
assert len(sheets)==10 and len(sources['sources'])==256 and unique==226
assert {x['revision'] for x in sources['runtime_summary']}=={'runtime_r02','runtime_updeath_r02'}
additional=['runtime_r02/four_directions.png','runtime_visual_strip.png','runtime_r02/frames/DeathAutoRecycle_00162.png','runtime_r02/frames/ContinuousTurns_00322.png','runtime_updeath_r02/frames/DeathAutoRecycle_00162.png']
note=('Up/Down初次正式生成各一次HTTP200，未重试或付费返修。Up选local_raster_revision_02/Up_sheet.png：把同张原图Body赭斑下移130px避开颈圈遮挡，旧位置同排褐色插值填充，内缩1px并轻柔羽化遮罩去除本地r01浅色边；Down选原始HTTP200返回。源图、两张付费raw、本地r01、首版过露Down颈圈布局、被否决的旧运行和旧审阅范围全部保留。保留橄榄褐色无足软体、三段圆拱躯干、短尾端、唯一头冠；无新增腿/触角/独立尾。原侧面含HP的4个存活Sprite PPtr及非美术语义保持。源Larva Death把Body旋转至-180度而Walk未复位，只给SlugQueen自有Walk副本新增Body Euler三轴常量0；70条原float绑定、PPtr/事件/时长/loop保留，未改共享源或C#。此前runtime_r01现场复用前后Body.z均0度；最终返修仅替换本角色图集，该修复动画SHA不变。最终runtime_r02/runtime_updeath_r02各84 PASS/0 FAIL，共674张真实Unity帧。实际查看最终四方向和strip、两轮全部10张时序/步态/愤怒板（256采样位/226张不同实际帧），另看Down死亡、复用后Left和Up死亡3张原尺寸PNG。Up后脑无眼口且赭斑清晰可见；Down斜金眼、攻击张口小牙、死亡圆金眼可辨。无足软体多节错相蠕动并有轻摇，连续转向后原侧面恢复，抽样未见部件断开、重复冠、底色污染或地面阴影。受击和致死白闪结束、双向死亡倾斜淡出、回收复用恢复，暂停姿态与时间保持，恢复与2x/3x推进。上下轴向视图相对原侧图更窄、质感更平滑，留给用户最终美术判断。审阅为真实PNG时序抽样，未实时播放GIF全片、未逐张审完674帧。内部实现与审阅完成，user_approved=false。')
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
write(visual/'review.json',dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,note=note,viewed_sheets=sheets,sample_slots=256,distinct_actual_frame_samples=unique,source_manifest='sources.json',sources_sha256=sha(visual/'sources.json'),viewed_sheet_sha256={p:sha(visual/p) for p in sheets},additional_viewed=additional,additional_viewed_sha256={p:sha(D/p) for p in additional},method='Actual chronological PNG samples, gait cycle and angry sheets, plus three full frames; no live GIF playback or exhaustive all-frame review',rejected_previous='local_raster_revision_01/rejected_previous.json',final_version_binding='version_binding_final_20261028.json'))
runtime.update(status='runtime_and_internal_visual_review_complete_pending_user_art_review',visual_review_file='visual_review_final_r02_20261028/review.json');write(D/'runtime_summary.json',runtime)
files=[D/p for p in ['installed_manifest.json','installed_verify.txt','art_selection.json','anatomy_plan.json','layout_adjustments.json','processing.json','offline_review_20261028.json','reference_review_20261028.json','original_sprite_contracts_20261028.json','local_raster_revision_01/processing.json','local_raster_revision_01/rejected_previous.json','local_raster_revision_02/Up_sheet.png','local_raster_revision_02/processing.json','local_raster_revision_02/review.json','local_raster_revision_02/installation.json','side_reuse_repair_r01/repair.json','side_reuse_repair_r01/repair_mcp.json','preplay_version_binding_20261028.json','preplay_version_binding_r02_20261028.json','source_animation_contracts_20261028.json','source_animation_contracts_detail_20261028.json','source_death_reuse_contract_20261028.json','source_death_reuse_probe_20261028.json','reuse_live_inspection_runtime_r01_20261028.json','runtime_summary.json','runtime_visual_strip.png','record_note_utf8.txt','visual_review_final_r02_20261028/sources.json','visual_review_final_r02_20261028/review.json','scope_incremental_final_20261028.json']]
for direction in ['Up','Down']:
    files += [D/'generation'/direction/p for p in ['raw.png','result.json','generation_intent.json','request.json','prompt.txt','review_20261028.json']]
for item in runtime['runtime']:
    folder=D/item['revision'];files += [folder/p for p in ['actual_frames.jsonl','actual_runtime_checks.txt','media_manifest.json','four_directions.png']]
    files+=list(folder.glob('*.gif'))+[D/(item['revision']+p) for p in ['_start.json','_returned.json']]
files += [p for p in (D/'staged_art').iterdir() if p.is_file()]+list(visual.glob('*.png'))
assert all(p.is_file() for p in files),[str(p) for p in files if not p.is_file()]
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest='installed_manifest.json',files={p.relative_to(D).as_posix():sha(p) for p in files},installed_files={x['path']:x['after'] for x in manifest['changes']},actual_png_frames=frames,frame_total=674,note='Selected image, local patch derivation, staging, installation, preserved own Walk reset and historical live pose evidence, final two real-Play rounds, actual reviewed sheets and all 674 final PNG frames bound by SHA256. R01 runtime remains historical; final r02 atlas-only repair retains the exact Walk hash.'))
client=Client();project=client.identity()
refresh=client.tool('refresh_unity',dict(mode='force',scope='assets',compile='none',wait_for_ready=True));client.identity();cache_refresh=None
for attempt in range(4):
    state=client.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if attempt==0 and s['advice'].get('blocking_reasons')==['stale_status']:
        cache_refresh=unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"SlugQueen_final_live_state_read"});return true;')))
    time.sleep(1)
else:raise RuntimeError('Unity not ready; do not record')
errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
probe=unwrap(client.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success'] and errors['success'] and errors['data']==[]
released=probe['data']['result'];assert released['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in released.items() if k!='scene')
assert all(sha(R/x['path'])==x['after'].upper() for x in manifest['changes'])
write(D/'final_validation_20261028.json',dict(observed_at=now(),transport=URL,project=project,refresh=refresh,cache_refresh=cache_refresh,state=state,errors=errors,probe=probe,installed_asset_drift=[],final_install_manifest='installed_manifest.json',runtime_summary_sha256=sha(D/'runtime_summary.json'),version_binding_sha256=sha(D/'version_binding_final_20261028.json'),scope_sha256=sha(D/'scope_incremental_final_20261028.json'),protocol_history=client.history))
subprocess.run([sys.executable,str(H/'character_step.py'),'record','SlugQueen',note],check=True)
progress=read(H/'progress.json');item=next(x for x in progress['items'] if x['name']=='SlugQueen')
assert progress['completed_count']==85 and item['status']=='completed_pending_user_art_review' and item['user_approved'] is False
item.update(current_stage='recorded_pending_user_art_review',final_install_manifest='SlugQueen/installed_manifest.json',final_animation_repair='SlugQueen/side_reuse_repair_r01/repair.json',final_visual_review='SlugQueen/visual_review_final_r02_20261028/review.json',final_validation='SlugQueen/final_validation_20261028.json',final_scope='SlugQueen/scope_incremental_final_20261028.json',final_version_binding='SlugQueen/version_binding_final_20261028.json');write(H/'progress.json',progress)
gifs=read(H.parent/'AllGIF/manifest.json');own=[x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/SlugQueen/')];active=[x for x in own if x['status']=='当前审核版本']
assert {x['source'] for x in own}=={p.relative_to(H.parent).as_posix() for p in D.rglob('*.gif')}
assert len(active)==12 and {x['source'].split('/')[2] for x in active}=={'runtime_r02','runtime_updeath_r02'}
assert all(sha(H.parent/x['source'])==x['sha256'] and sha(H.parent/'AllGIF'/x['file'])==x['sha256'] for x in own)
write(D/'gif_archive_verification_20261028.json',dict(observed_at=now(),total=gifs['count'],character_count=len(own),current_count=len(active),files=own,sha256_match=True,all_available_character_gifs_archived=True))
chain.update(character_status_at_handoff=item['status'],completed_count_snapshot=85,current_stage='recorded_pending_user_art_review',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/SlugQueen/final_validation_20261028.json',updated_at=now());write(H/'conversation_chain.json',chain)
print(json.dumps(dict(completed=85,production_changes=len(changes),production_additions=sum(x['before'] is None for x in changes),unexpected_incremental=len(unexpected),legacy_unexpected=len(old_unexpected),legacy_semantic_failures=list(new_failures),sample_slots=256,distinct_actual_samples=unique,frames=674,probe=released,gifs_total=gifs['count'],slugqueen_gifs=len(own),current_gifs=len(active)),ensure_ascii=False))
