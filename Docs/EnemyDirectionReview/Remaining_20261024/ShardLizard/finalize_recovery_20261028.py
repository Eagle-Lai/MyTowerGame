"""Finalize the actually reviewed r03 repair; keep all historical failures intact."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from mcp_call import Client

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(r): return r.get('structuredContent') or json.loads(r['content'][0]['text'])

chain = read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='ShardLizard'
assert chain['dispatch_token']=='scarabmounted-to-shardlizard-e066b2f9cbb54a5ca5b215b2e08ea8d2'
assert not (D/'final_validation_20261028.json').exists(), 'Inspect existing final evidence before retry'
baseline_path = D/'incremental_before_recovery_20261028_085812.json'
baseline = read(baseline_path)
base = {p:s.upper() for p,s in baseline['files'].items()}
current = {p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changes = [{'path':p,'before':base.get(p),'after':current.get(p)} for p in sorted(set(base)|set(current)) if base.get(p)!=current.get(p)]
battle = 'Assets/Prefabs/Enemy/Enemy_ShardLizard.prefab'
art = 'Assets/_UIAssets/Monsters/Rats/ShardLizard/Directions'
side_effects, unexpected = [], []
for x in changes:
    p=x['path']
    if p==battle or p.startswith(art+'/') or p==art+'.meta': continue
    if p=='Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs']==base['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+', (ROOT/p).read_text(encoding='utf-8')):
        side_effects.append(dict(x, origin='Unmodified ReporterEditor.cs InitializeOnLoad BuildInfo.Update; startup/compilation timestamp, also observed around Play.'))
    else: unexpected.append(x)
assert not unexpected, unexpected
protected_drift = [{'path':p,'expected':s,'actual':sha(ROOT/p)} for p,s in baseline['protected_shardlizard'].items() if p!=battle and sha(ROOT/p)!=s.upper()]
assert not protected_drift, protected_drift

targets = {t['name']:t for t in read(HERE/'local_baseline.json')['targets']}
definitions = (HERE.parent/'Batch01_10/audit_scope.py').read_text(encoding='utf-8')
exec(definitions[definitions.index('def sha('):definitions.index('changed=[];unexpected=[]')])
sem = semantic('ShardLizard')
assert sem['pass'], sem
manifest_path = D/'repair_proportions_r03/manifest.json'
manifest = read(manifest_path)
drift = [x['path'] for x in manifest['changes'] if sha(ROOT/x['path'])!=x['after'].upper()]
assert not drift, drift
packed_names = ['ShardLizard_Directions.png','ShardLizard_Directions.layout.json','ShardLizard_Directions.sprites.json']
staged_drift = [n for n in packed_names if sha(D/'staged_art'/n)!=sha(ROOT/art/n)]
assert not staged_drift, staged_drift
verify = manifest['verification']['data']['result']
assert verify['pass'] and 'PASS YooAsset prefab and artwork collectors present' in verify['report']
assert (D/'repair_proportions_r03/verify.txt').read_text(encoding='utf-8')==verify['report']
legacy_before = read(HERE/'scope_ShardLizard_20261028_092018.json')
legacy_name = 'scope_ShardLizard_20261028_final.json'
assert not (HERE/legacy_name).exists()
process = subprocess.run([sys.executable,str(HERE/'audit_scope.py'),legacy_name],capture_output=True,text=True,encoding='utf-8')
if process.returncode: raise RuntimeError(process.stderr)
legacy = read(HERE/legacy_name)
prior_unexpected = {x['path']:x.get('after') for x in legacy_before['unexpected']}
new_unexpected = [x for x in legacy['unexpected'] if prior_unexpected.get(x['path'])!=x.get('after')]
new_semantic_failures = {n:s['unexpected'] for n,s in legacy['semantics'].items() if not s['pass'] and s['unexpected']!=legacy_before['semantics'].get(n,{}).get('unexpected')}
assert not new_unexpected and not new_semantic_failures, (new_unexpected,new_semantic_failures)
scope = dict(observed_at=now(),baseline=baseline_path.name,baseline_files=len(base),incremental_changes=changes,
    unexpected_incremental=unexpected,allowed_incremental_side_effects=side_effects,protected_drift=protected_drift,
    prefab_semantics=sem,installed_asset_drift=drift,staged_production_drift=staged_drift,
    legacy_before='scope_ShardLizard_20261028_092018.json',legacy_after=legacy_name,
    legacy_pass=legacy['pass'],legacy_unexpected_count=len(legacy['unexpected']),
    new_unexpected_vs_preexisting_legacy=new_unexpected,new_semantic_failures=new_semantic_failures,
    note='File union includes additions and deletions; hash case normalized. Historical 291 unexpected entries and existing semantic failures preserved; no baseline reset/global PASS.')
write(D/'scope_incremental_recovery_20261028.json',scope)

runtime = read(D/'runtime_summary.json')
assert runtime['passes']==168 and runtime['failures']==0 and runtime['actual_frames']==679
version_files = [manifest_path,D/'installed_manifest.json',D/'art_selection.json',D/'layout_adjustments.json',
    D/'generation/Up/revision_02/raw.png',D/'generation/Down/raw.png',D/'runtime_summary.json']
frames = {}
for r in runtime['runtime']:
    folder = D/r['revision']
    records = folder/'actual_frames.jsonl'
    assert sha(records)==r['records_sha256'].upper()
    rows = [json.loads(line) for line in records.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(rows)==r['frames'] and all(a['frame']<b['frame'] for a,b in zip(rows,rows[1:]))
    assert len({x['file'] for x in rows})==len(rows)
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks)==84 and not any(x.startswith('FAIL ') for x in checks)
    frames[r['revision']]={x['file']:sha(folder/x['file']) for x in rows}
    assert all(frames[r['revision']].values())
    version_files += [records,folder/'actual_runtime_checks.txt',folder/'media_manifest.json',D/(r['revision']+'_start.json'),D/(r['revision']+'_returned.json')]
    version_files += list(folder.glob('*.gif'))
version_files += [p for p in (D/'staged_art').iterdir() if p.is_file()]
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest=manifest_path.relative_to(D).as_posix(),
    files={p.relative_to(D).as_posix():sha(p) for p in version_files},installed_files={x['path']:x['after'] for x in manifest['changes']},
    actual_png_frames=frames,frame_total=sum(len(x) for x in frames.values()),
    note='Final r03 repair precedes both new real Play rounds. This is a final binding; original initial runtime evidence is retained and superseded.'))

c=Client()
project=c.identity()
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
state=c.resource('mcpforunity://editor/state')
code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'
probe=unwrap(c.tool('execute_code',dict(action='execute',code=code)))
assert probe['success'],probe
observed=probe['data']['result']
assert not any(v for k,v in observed.items() if k!='scene'),observed
assert observed['scene']=='Assets/Scenes/Boot.unity',observed
s=state['data']
assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']
assert errors['success'] and errors['data']==[],errors
write(D/'final_validation_20261028.json',dict(observed_at=now(),project=project,state=state,errors=errors,probe=probe,
    final_install_manifest=manifest_path.relative_to(D).as_posix(),installed_asset_drift=drift,runtime_summary_sha256=sha(D/'runtime_summary.json'),protocol_history=c.history))

note='最终采用local_raster_revision_02与repair_proportions_r03。初版两轮虽168/0，但Up/Down体量过小已视觉否决；revision03将轴向部件与关节间距放大1.6并保留专用尾根pivot。新两轮真实Play为84/0+84/0，共679帧。实际查看四方向图、runtime_visual_strip及10张整身时序/步态/愤怒细节板，共256采样位、230张不同真实帧，并查看Down攻击及死亡原PNG。Up后脑无五官，四肢/颈尾根连续、单条分节尾；Down保留宽脸、小额晶片和单块宽顶背晶，攻击张嘴、死亡眼舌状态可辨；侧向保持原低伏长体。上下步态脚部压缩/摆动与尾摆可见，连续转向、白闪后恢复、死亡整身倾倒淡出及回收后不透明状态正常；暂停姿态及时间不变，恢复和2x/3x继续推进。抽样中尾尖完整且未碰血条，未见地面阴影。审阅为按时间排序的真实PNG抽样，未实时播放GIF、未逐张审完679帧。仅内部技术与视觉检查完成，用户美术未批准。'
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
visual_folder=D/'visual_review_final_20261028'
sources=read(visual_folder/'sources.json')
sheets=sorted({x['sheet'] for x in sources['sources']})
assert len(sheets)==10 and len(sources['sources'])==256
review=dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,note=note,
    viewed_sheets=sheets,source_manifest='sources.json',sample_slots=256,distinct_actual_frame_samples=230,
    additional_viewed=['runtime_final_r02/four_directions.png','runtime_visual_strip.png','offline_proportions_revision_03/full_rig_proof.png',
        'runtime_final_r02/frames/Attack_00139.png','runtime_final_r02/frames/DeathAutoRecycle_00165.png'],
    method='Chronological actual PNG samples, walk cycles and angry details. No live GIF playback; not every frame reviewed.',
    final_install_manifest='repair_proportions_r03/manifest.json',sources_sha256=sha(visual_folder/'sources.json'),
    viewed_sheet_sha256={p:sha(visual_folder/p) for p in sheets},final_version_binding='version_binding_final_20261028.json',
    superseded_runtime=['runtime_r01','runtime_updeath_r01'],superseded_reason='Up/Down too small despite technical PASS')
write(visual_folder/'review.json',review)
subprocess.run([sys.executable,str(HERE/'record_review.py'),'ShardLizard',note],check=True)
p=read(HERE/'progress.json')
i=next(x for x in p['items'] if x['name']=='ShardLizard')
i.update(recovery_in_progress=False,recovery_completed_at=now(),current_blocked=False,
    historical_blocked_records_preserved=True,final_install_manifest='ShardLizard/repair_proportions_r03/manifest.json',
    final_visual_review='ShardLizard/visual_review_final_20261028/review.json',final_validation='ShardLizard/final_validation_20261028.json',
    final_scope='ShardLizard/scope_incremental_recovery_20261028.json',selected_rig_revision='repair_proportions_r03')
assert p['completed_count']==80 and i['status']=='completed_pending_user_art_review' and not i['user_approved']
write(HERE/'progress.json',p)
chain.update(character_status_at_handoff=i['status'],completed_count_snapshot=80,current_stage='recorded_pending_user_art_review',
    resume_stage='final r03 repaired, 168/0, 679 frames, actual visual review and record complete',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/ShardLizard/final_validation_20261028.json',updated_at=now())
write(HERE/'conversation_chain.json',chain)
gifs=read(HERE.parent/'AllGIF/manifest.json')
own=[x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/ShardLizard/')]
print(json.dumps(dict(completed=p['completed_count'],incremental_changes=len(changes),added=sum(x['before'] is None for x in changes),
    unexpected=len(unexpected),legacy_unexpected=len(legacy['unexpected']),new_legacy=len(new_unexpected),prefab_semantics=sem['pass'],
    probe=observed,gifs_total=gifs['count'],character_gifs=len(own),character_current_gifs=sum(x['status']=='当前审核版本' for x in own)),ensure_ascii=False))
