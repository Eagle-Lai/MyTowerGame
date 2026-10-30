"""Close Mounted only after the two real Play rounds and actual PNG review."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,re,subprocess,sys,time
D=Path(__file__).resolve().parent;HERE=D.parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v): return v.get('structuredContent') or json.loads(v['content'][0]['text'])
chain=read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='ScarabMounted' and chain['dispatch_token']=='scarab-to-scarabmounted-dd3da45145854f44998a5b6bdc48d12e'
assert not (D/'final_validation_20261028.json').exists(),'Inspect existing finalization before retry'
intent=read(D/'generation/Down/revision_03/recovery_intent.json')
assert sha(D/'authorized_resume_20261028.json').lower()==intent['authorization_sha256'].lower()
result=read(D/'generation/Down/revision_03/result.json')
assert result['status']==200 and result['bytes']==(D/'generation/Down/revision_03/raw.png').stat().st_size
old_requests={}
for direction,revisions in [('Up',['revision_01','revision_02']),('Down',['initial','revision_01','revision_02'])]:
    for rev in revisions:
        folder=D/'generation'/direction
        if rev!='initial':folder=folder/rev
        assert (folder/'uncertain_result.json').is_file() and not (folder/'raw.png').exists() and not (folder/'result.json').exists()
        old_requests[folder.relative_to(D).as_posix()]={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
base_path=D/'incremental_before_resumed_20261028.json';baseline=read(base_path)
base={p:s.upper() for p,s in baseline['files'].items()}
current={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changes=[dict(path=p,before=base.get(p),after=current.get(p)) for p in sorted(set(base)|set(current)) if base.get(p)!=current.get(p)]
battle='Assets/Prefabs/Enemy/Enemy_ScarabMounted.prefab';art='Assets/_UIAssets/Monsters/Mounts/ScarabMounted/Directions'
unexpected=[];side_effects=[]
for x in changes:
    p=x['path']
    if p==battle or p.startswith(art+'/') or p==art+'.meta':continue
    if p=='Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs']==base['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+',(ROOT/p).read_text(encoding='utf-8')):
        side_effects.append(dict(x,origin='Unmodified ReporterEditor InitializeOnLoad Play timestamp'))
    else:unexpected.append(x)
assert not unexpected,unexpected
protected=baseline['protected_six'];drift=[p for p,s in protected.items() if p!=battle and sha(ROOT/p)!=s.upper()]
assert not drift,drift
legacy_before=read(HERE/'scope_ScarabMounted_recovery_blocked_20261028_124451.json')
legacy=read(HERE/'scope_ScarabMounted_20261028_r02_final.json')
prior_unexpected={x['path']:x.get('after') for x in legacy_before['unexpected']}
new_unexpected=[x for x in legacy['unexpected'] if prior_unexpected.get(x['path'])!=x.get('after')]
new_semantics={n:s['unexpected'] for n,s in legacy['semantics'].items() if not s['pass'] and s['unexpected']!=legacy_before['semantics'].get(n,{}).get('unexpected')}
assert not new_unexpected and not new_semantics,(new_unexpected,new_semantics)
assert legacy['semantics']['ScarabMounted']['pass']
manifest=read(D/'installed_manifest.json')
assert all(sha(ROOT/x['path'])==x['after'].upper() for x in manifest['changes'])
verify=manifest['verification']['data']['result'];assert verify['pass']
assert (D/'installed_verify.txt').read_text(encoding='utf-8')==verify['report']
preplay=read(D/'preplay_version_binding_r02_20261028.json')
assert sha(D/'installed_manifest.json')==preplay['installed_manifest_sha256']
assert all(sha(ROOT/p)==s for p,s in preplay['installed_files'].items())
staged=read(D/'offline_review_resumed_20261028.json')['staging_files']
assert all(sha(D/'staged_art'/p)==s for p,s in staged.items())
assert all(sha(D/'staged_art'/n)==sha(ROOT/art/n) for n in ['ScarabMounted_Directions.png','ScarabMounted_Directions.layout.json','ScarabMounted_Directions.sprites.json'])
scope=dict(observed_at=now(),baseline=base_path.name,baseline_sha256=sha(base_path),baseline_files=len(base),current_files=len(current),comparison='Union of before/current paths, including additions and deletions',changes=changes,unexpected_incremental=unexpected,automatic_editor_side_effects=side_effects,protected_six=protected,protected_drift=drift,prefab_semantics=legacy['semantics']['ScarabMounted'],installed_asset_drift=[],staged_production_drift=[],legacy_before='scope_ScarabMounted_recovery_blocked_20261028_124451.json',legacy_after='scope_ScarabMounted_20261028_r02_final.json',legacy_pass=legacy['pass'],legacy_unexpected_count=len(legacy['unexpected']),legacy_semantic_failure_count=sum(not s['pass'] for s in legacy['semantics'].values()),legacy_semantic_failures=[n for n,s in legacy['semantics'].items() if not s['pass']],new_unexpected_vs_preexisting_legacy=new_unexpected,new_semantic_failures=new_semantics,note='Historical global differences preserved; no global PASS claim')
write(D/'scope_incremental_final_20261028.json',scope)
runtime=read(D/'runtime_summary.json')
assert runtime['passes']==168 and runtime['failures']==0 and [r['revision'] for r in runtime['runtime']]==['runtime_r02','runtime_updeath_r02']
frames={}
for r in runtime['runtime']:
    f=D/r['revision'];records=f/'actual_frames.jsonl';assert sha(records)==r['records_sha256']
    rows=[json.loads(line) for line in records.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(rows)==r['frames'] and all(a['frame']<b['frame'] for a,b in zip(rows,rows[1:]))
    assert len({x['file'] for x in rows})==len(rows)
    checks=(f/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks)==84 and not any(x.startswith('FAIL ') for x in checks)
    frames[r['revision']]={x['file']:sha(f/x['file']) for x in rows};assert all(frames[r['revision']].values())
assert sum(len(x) for x in frames.values())==runtime['actual_frames']
note='Up选revision_04定向返修原图，后脑无眼口且保留双带纹触角；Down选当前续做中curl单次成功HTTP200的revision_03，经local_raster_revision_01只用本图完好中腿根修补前腿根底色污染。原图、Up01/02及Down初次/01/02全部uncertain、旧Up402和被否决Up03均保留，不推定费用。安装后side_reuse_repair_r01仅给Mounted自有Walk副本新增Body三轴Euler常量0，147条原float曲线/PPtr/事件/时长/loop通过保留检查，未改Scarab或共享源动画/C#。最终runtime_r01与runtime_updeath_r01各84 PASS/0 FAIL，共691张真实Unity帧。实际查看四方向、strip与10张时序/步态/愤怒细节板：橄榄赭色斑壳、唯一鞍、双触角、六足与象牙口器；Up无眼口，Down正常橙眼、攻击斜眼与死亡叉眼清楚。腿根藏在壳下，三对腿错相，部分中足与壳边重叠；抽样未见漂浮连接、轮廓断开或地面阴影，连续转向和死亡复用后的左右侧身直立。受击及致死白闪结束，死亡倾斜淡出，自动回收与同实例复用恢复，暂停帧保持，恢复及2x/3x有推进。正背造型比原侧图更接近轴向俯视，鞍的视角与中足遮挡密度保留给用户最终美术判断。审阅为真实PNG时序抽样，未播放GIF全片，也未逐张审完691帧；仅内部技术与视觉完成，user_approved=false。'
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
note=note.replace('最终runtime_r01与runtime_updeath_r01各84 PASS/0 FAIL，共691张真实Unity帧。','初轮168/0后，范围审计发现Builder预览把侧头初始Sprite改为接收器同Atlas图，source_head_repair_r02已只恢复原共享Scarab Sprite PPtr，接收器表情数组与源动画不动，旧r01/审阅/审计完整保留。最终runtime_r02与runtime_updeath_r02各84 PASS/0 FAIL，共'+str(runtime['actual_frames'])+'张真实Unity帧。').replace('逐张审完691帧','逐张审完'+str(runtime['actual_frames'])+'帧')
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
visual=D/'visual_review_final_r02_20261028';sources=read(visual/'sources.json');sheets=sorted({x['sheet'] for x in sources['sources']})
assert len(sheets)==10 and len(sources['sources'])==256
assert {x['revision'] for x in sources['runtime_summary']}=={'runtime_r02','runtime_updeath_r02'}
unique=len({(x['revision'],x['source']) for x in sources['sources']})
write(visual/'review.json',dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,note=note,viewed_sheets=sheets,sample_slots=len(sources['sources']),distinct_actual_frame_samples=unique,source_manifest='sources.json',additional_viewed=['runtime_r02/four_directions.png','runtime_visual_strip.png'],method='Chronological actual PNG samples, walk cycle and angry detail. No live GIF playback; not every frame reviewed',rejected_previous='source_head_repair_r02/rejection.json',final_install_manifest='installed_manifest.json',sources_sha256=sha(visual/'sources.json'),viewed_sheet_sha256={p:sha(visual/p) for p in sheets},final_version_binding='version_binding_final_20261028.json'))
runtime.update(status='runtime_and_internal_visual_review_complete_pending_user_art_review',visual_review_file='visual_review_final_r02_20261028/review.json');write(D/'runtime_summary.json',runtime)
files=[D/p for p in ['installed_manifest.json','installed_verify.txt','art_selection.json','layout_adjustments.json','processing.json','generation/Up/revision_04/raw.png','generation/Up/revision_04/result.json','generation/Down/revision_03/raw.png','generation/Down/revision_03/result.json','generation/Down/revision_03/recovery_intent.json','authorized_resume_20261028.json','network_assessment_resume_20261028.json','local_raster_revision_01/Down_sheet.png','local_raster_revision_01/processing.json','repair_root_20261028.py','runtime_summary.json','runtime_visual_strip.png','side_reuse_repair_r01/repair.json','side_reuse_repair_r01/repair_mcp.json','repair_side_reuse_20261028.py','preplay_version_binding_r02_20261028.json','source_head_repair_r02/repair.json','source_head_repair_r02/repair_mcp.json','repair_source_head_20261028.py','record_note_utf8.txt','visual_review_final_r02_20261028/sources.json','visual_review_final_r02_20261028/review.json']]
for r in runtime['runtime']:
    f=D/r['revision'];files += [f/'actual_frames.jsonl',f/'actual_runtime_checks.txt',f/'media_manifest.json',f/'four_directions.png',D/(r['revision']+'_start.json'),D/(r['revision']+'_returned.json')]+list(f.glob('*.gif'))
files += [p for p in (D/'staged_art').iterdir() if p.is_file()]+list(visual.glob('*.png'))
assert all(p.is_file() for p in files),[str(p) for p in files if not p.is_file()]
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest='installed_manifest.json',files={p.relative_to(D).as_posix():sha(p) for p in files},installed_files={x['path']:x['after'] for x in manifest['changes']},actual_png_frames=frames,frame_total=runtime['actual_frames'],preserved_uncertain_requests=old_requests,note='Own copied Walk reset preceded both actual Play rounds. Original shared Head restored and own Walk reset preceded both r02 rounds. Original generated sheets/source animations unchanged; previous failures remain preserved'))
c=Client();project=c.identity();refresh=c.tool('refresh_unity',dict(mode='force',scope='assets',compile='none',wait_for_ready=True));c.identity();cache_refresh=None
for attempt in range(4):
    state=c.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if attempt==0 and s.get('advice',{}).get('blocking_reasons')==['stale_status']:
        cache_refresh=unwrap(c.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"ScarabMounted_final_live_state_read"});return true;')))
        assert cache_refresh['success'] and cache_refresh['data']['result'] is True
    time.sleep(1)
else:raise RuntimeError('Editor not ready; do not record')
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
probe=unwrap(c.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success'];observed=probe['data']['result'];assert not any(v for k,v in observed.items() if k!='scene') and observed['scene']=='Assets/Scenes/Boot.unity'
assert errors['success'] and errors['data']==[]
assert all(sha(ROOT/x['path'])==x['after'].upper() for x in manifest['changes'])
write(D/'final_validation_20261028.json',dict(observed_at=now(),project=project,refresh=refresh,cache_refresh=cache_refresh,state=state,errors=errors,probe=probe,final_install_manifest='installed_manifest.json',installed_asset_drift=[],runtime_summary_sha256=sha(D/'runtime_summary.json'),protocol_history=c.history))
before=read(HERE/'progress.json');before_count=before['completed_count'];assert before_count==82
subprocess.run([sys.executable,str(HERE/'record_review.py'),'ScarabMounted',note],check=True)
p=read(HERE/'progress.json');item=next(i for i in p['items'] if i['name']=='ScarabMounted')
historical={k:item[k] for k in ['blocked_reason','blocked_record','blocked_at','final_unity_release'] if k in item}
item.setdefault('historical_blocked_records',[]).append(dict(historical,closed_at=now(),resolution='Down03 single curl resume returned; both real Play rounds and actual PNG review complete. Original uncertain outcomes preserved'))
for k in ['blocked_reason','blocked_at','blocked_record','final_unity_release']:item.pop(k,None)
item.update(current_blocked=False,recovery_in_progress=False,recovery_completed_at=now(),recovery_stage='recorded_pending_user_art_review',current_stage='recorded_pending_user_art_review',generation_revisions=dict(Up='revision_04',Down='revision_03'),down_outcomes=dict(initial='uncertain_preserved',revision_01='uncertain_preserved',revision_02='uncertain_preserved',revision_03='HTTP200'),final_animation_repair='ScarabMounted/side_reuse_repair_r01/repair.json',final_install_manifest='ScarabMounted/installed_manifest.json',final_visual_review='ScarabMounted/visual_review_final_r02_20261028/review.json',final_validation='ScarabMounted/final_validation_20261028.json',final_scope='ScarabMounted/scope_incremental_final_20261028.json',current_turn_resume_requests=1)
assert p['completed_count']==before_count+1 and item['status']=='completed_pending_user_art_review' and not item['user_approved'];write(HERE/'progress.json',p)
gifs=read(HERE.parent/'AllGIF/manifest.json');own=[x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/ScarabMounted/')];active=[x for x in own if x['status']=='当前审核版本']
assert len(own)==24 and len(active)==12
assert all(sha(HERE.parent/x['source'])==x['sha256'] and sha(HERE.parent/'AllGIF'/x['file'])==x['sha256'] for x in own)
write(D/'gif_archive_verification_20261028.json',dict(observed_at=now(),total=gifs['count'],character_count=len(own),current_count=len(active),files=own,sha256_match=True))
chain.update(character_status_at_handoff=item['status'],completed_count_snapshot=p['completed_count'],current_stage='recorded_pending_user_art_review',resume_stage='Mounted own Walk reset and original Head restored, 168/0, '+str(runtime['actual_frames'])+' actual frames, actual PNG review, record and GIF archive complete',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/ScarabMounted/final_validation_20261028.json',updated_at=now(),current_blocked=False);write(HERE/'conversation_chain.json',chain)
print(json.dumps(dict(completed=p['completed_count'],changes=len(changes),added=sum(x['before'] is None for x in changes),unexpected=len(unexpected),legacy_unexpected=len(legacy['unexpected']),new_legacy=len(new_unexpected),samples=unique,probe=observed,gifs_total=gifs['count'],character_gifs=len(own)),ensure_ascii=False))
