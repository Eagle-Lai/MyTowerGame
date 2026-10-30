"""Validate the reviewed r02 without rebuilding; seal evidence before record."""
from session_treasurechest import *
import time

chain=owner();assert URL=='http://127.0.0.1:8088/mcp'
assert not (D/'final_validation_20261028.json').exists(), 'Inspect existing finalization before resuming'
progress=read(H/'progress.json');assert progress['completed_count']==87
item=next(x for x in progress['items'] if x['name']==NAME)
assert item['status']!='completed_pending_user_art_review' and item.get('user_approved') is False
baseline=read(D/'incremental_before_20261028.json');before={p:s.upper() for p,s in baseline['files'].items()};current=inventory()
battle='Assets/Prefabs/Enemy/Enemy_TreasureChest.prefab';art='Assets/_UIAssets/Monsters/Inanimate/TreasureChest/Directions'
changes=[dict(path=p,before=before.get(p),after=current.get(p)) for p in sorted(set(before)|set(current)) if before.get(p)!=current.get(p)]
unexpected=[];side_effects=[]
for x in changes:
    p=x['path']
    if p==battle or p==art+'.meta' or p.startswith(art+'/'):continue
    if p=='Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs']==before['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+',(R/p).read_text(encoding='utf-8')):
        side_effects.append(dict(x,origin='Unmodified ReporterEditor InitializeOnLoad Play timestamp'))
    else:unexpected.append(x)
assert not unexpected,unexpected
protected_drift=[p for p,s in baseline['protected_six'].items() if p!=battle and sha(R/p)!=s.upper()]
assert not protected_drift,protected_drift
assert all(sha(D/'reference'/Path(p).name)==s.upper() for p,s in baseline['protected_six'].items())
shared_cs_drift=[p for p,s in before.items() if p.endswith('.cs') and current.get(p)!=s]
assert not shared_cs_drift,shared_cs_drift
legacy_before=read(H/'scope_TreasureChest_before_20261028.json');legacy_after=read(H/'scope_TreasureChest_final_20261028.json')
old_unexpected={x['path']:x.get('after') for x in legacy_before['unexpected']}
assert {x['path']:x.get('after') for x in legacy_after['unexpected']}==old_unexpected
old_fail={n:s['unexpected'] for n,s in legacy_before['semantics'].items() if not s['pass']}
new_fail={n:s['unexpected'] for n,s in legacy_after['semantics'].items() if not s['pass']}
assert old_fail==new_fail and legacy_after['semantics'][NAME]['pass']
manifest=read(D/'installed_manifest_r02.json');assert all(sha(R/x['path'])==x['after'].upper() for x in manifest['changes'])
verify=manifest['verification']['data']['result'];assert verify['pass'] and (D/'installed_verify_r02.txt').read_text(encoding='utf-8')==verify['report']
intended={x['path']:x['after'] for x in changes if x['path'] not in {s['path'] for s in side_effects}}
assert intended=={x['path']:x['after'] for x in manifest['changes']}

def sprite_contract(path):
    text=path.read_text(encoding='utf-8-sig');blocks=list(re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',text,re.M|re.S))
    objects={m[2]:re.search(r'^  m_Name: (.+)$',m[3],re.M)[1] for m in blocks if m[1]=='1'};result={}
    for m in blocks:
        if m[1]!='212':continue
        go=re.search(r'^  m_GameObject: \{fileID: (-?\d+)\}',m[3],re.M)[1]
        result[m[2]]=dict(name=objects[go],game_object=go,sprite=re.search(r'^  m_Sprite: (.+)$',m[3],re.M)[1])
    return result
original=sprite_contract(D/'before'/battle);installed=sprite_contract(R/battle)
assert len(original)==5 and sum(x['name']!='Shadow' for x in original.values())==4
assert {x['name'] for x in original.values()}=={'Normal','Broken','Shadow','Bg','Fill'}
for fid,value in original.items():
    if value['name']=='Shadow':assert fid not in installed
    else:assert installed[fid]==value
write(D/'original_sprite_contracts_20261028.json',dict(observed_at=now(),before=original,original_count=5,retained_non_shadow_count=4,included_hp_sprites=True,only_removed_original_sprite='Shadow',all_retained_pptr_unchanged=True,baseline_prefab_sha256=sha(D/'before'/battle),current_prefab_sha256=sha(R/battle)))
preinstall=read(D/'preinstall_review_20261028.json')
assert {p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()}==preinstall['staged']
for suffix in ['.png','.sprites.json','.layout.json']:
    assert sha(D/'staged_art'/('TreasureChest_Directions'+suffix))==sha(R/art/('TreasureChest_Directions'+suffix))
quality=read(D/'chroma_quality_20261028.json');assert quality['total_fringe_pixels_removed']==6905 and quality['actual_interior_pixels_filled']==0
assert all(x.get('intentional_transparent_carrier') or x['interior_holes_after']==0 for x in quality['parts'].values())
assert sha(D/'staged_art/TreasureChest_Directions.png')==quality['atlas_sha256']
assert sha(D/'TreasureChestDirectionAdapter.cs.txt')==sha(R/art/'Editor/TreasureChestDirectionAdapter.cs')
assert sha(D/'TreasureChestDirectionReview.cs.txt')==sha(R/art/'Editor/TreasureChestDirectionReview.cs')
selection=read(D/'art_selection.json');assert selection['Up']=='local_raster_revision_01/Up_sheet.png' and selection['Down']=='generation/Down/raw.png'
for p in ['generation/Up','generation/Up/revision_01']:
    assert (D/p/'uncertain_result.json').is_file() and not (D/p/'raw.png').exists() and not (D/p/'result.json').exists()
for p in ['generation/Up/revision_02','generation/Down']:
    result=read(D/p/'result.json');assert result['status']==200 and result['bytes']==(D/p/'raw.png').stat().st_size
application=read(D/'standing_recovery_application_20261028.json')
assert application['owner_thread_id']==chain['owner_thread_id'] and application['dispatch_token']==TOKEN
assert sha(H/'standing_network_recovery_authorization_20261028.json')==application['authorization_sha256'].upper()
assert all(sha(D/x['path'])==x['sha256'].upper() for x in application['preserved_evidence'])
assert len(list((D/'generation/Up').glob('revision_*/request.json')))==2
derivation=read(D/'local_raster_revision_01/derivation.json')
assert sha(D/derivation['parent'])==derivation['parent_sha256'] and sha(D/derivation['output'])==derivation['output_sha256']

runtime=read(D/'runtime_summary.json');assert runtime['passes']==168 and runtime['failures']==0 and runtime['actual_frames']==697
assert [x['revision'] for x in runtime['runtime']]==['runtime_r02','runtime_updeath_r02']
frames={};rows_by_rev={};lifecycle={}
for run in runtime['runtime']:
    rev=run['revision'];folder=D/rev
    assert sha(folder/'actual_frames.jsonl')==run['records_sha256']
    rows=[json.loads(x) for x in (folder/'actual_frames.jsonl').read_text(encoding='utf-8-sig').splitlines() if x]
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks)==84 and not any(x.startswith('FAIL ') for x in checks)
    assert len(rows)==run['frames'] and all(a['frame']<b['frame'] and a['realtime']<b['realtime'] for a,b in zip(rows,rows[1:]))
    frames[rev]={x['file']:sha(folder/x['file']) for x in rows};rows_by_rev[rev]={x['file']:x for x in rows}
    assert len(frames[rev])==len(rows) and all(frames[rev].values()) and len(list(folder.glob('*.gif')))==6
    bound=read(D/(rev+'_version_binding_before.json'))
    assert bound['installed_manifest']=='installed_manifest_r02.json' and bound['installed_manifest_sha256']==sha(D/'installed_manifest_r02.json')
    assert all(sha(R/p)==s for p,s in bound['production'].items())
    assert all(sha(D/p)==s for p,s in bound['staged'].items())
    returned=read(D/(rev+'_returned.json'));assert returned['version_unchanged'] and returned['own_review'] is False
    assert returned['state']['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in returned['state'].items() if k!='scene')
    dead=[x for x in rows if x['stage']=='DeathAutoRecycle' and x['state']=='Death'];reuse=[x for x in rows if x['stage']=='Reuse']
    assert len(dead)>0 and len(reuse)==9
    assert all(not x['originalNormalActive'] and x['originalBrokenActive'] and x['shownSprite']==x['facing']+'_HeadDead' for x in dead)
    assert all(x['originalNormalActive'] and not x['originalBrokenActive'] and x['state']!='Death' and x['expression']==0 and x['shownSprite']==x['facing']+'_HeadNormal' and all(v==0 for v in x['originalBodyPosition'].values()) and all(v==0 for v in x['originalBodyEuler'].values()) for x in reuse)
    lifecycle[rev]=dict(death_frames=dead,reuse_frames=reuse,original_activation_pass=True,reuse_closed_and_body_reset_pass=True,version_binding_before=rev+'_version_binding_before.json')
visual=D/'visual_review_final_20261028';sources=read(visual/'sources.json');sheets=sorted(sources['boards'])
assert len(sheets)==12 and len(sources['sources'])==288 and len({(x['revision'],x['source']) for x in sources['sources']})==288
assert all(sha(visual/p)==s for p,s in sources['boards'].items())
for x in sources['sources']:
    assert frames[x['revision']][x['source']]==x['source_sha256'] and rows_by_rev[x['revision']][x['source']]['frame']==x['frame']
additional=['runtime_r02/four_directions.png','runtime_visual_strip.png','runtime_r02/frames/DeathAutoRecycle_00181.png','runtime_updeath_r02/frames/DeathAutoRecycle_00181.png']
assert all((D/p).is_file() for p in additional)

client=Client();project=client.identity();errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));assert errors['data']==[]
cache_refresh=None
for attempt in range(5):
    state=client.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if attempt==0 and s['advice'].get('blocking_reasons')==['stale_status']:
        cache_refresh=unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"TreasureChest_final_live_state_read"});return true;')))
    time.sleep(1)
else:raise RuntimeError('Unity not ready; do not record')
live=probe(client);assert live['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in live.items() if k!='scene')
code='''var p=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Prefabs/Enemy/Enemy_TreasureChest.prefab");var r=p.GetComponent<FTProject.MonsterAnimEventReceiver>();var src=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/_Common/Animations/Container/Death.anim");var dst=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/Inanimate/TreasureChest/Directions/Animations/Death_Directions.anim");var sourceY=UnityEditor.AnimationUtility.GetEditorCurve(src,UnityEditor.EditorCurveBinding.FloatCurve("Body",typeof(UnityEngine.Transform),"m_LocalPosition.y"));return new{ownReview=FTProject.EditorTools.TreasureChestDirectionReview.Running,headRendererNull=r.HeadRenderer==null,headSprites=r.HeadSprites.Length,sourceY=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(sourceY.keys,k=>new{time=k.time,value=k.value,inTangent=k.inTangent,outTangent=k.outTangent})),vertical=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(new[]{"Up","Down"},d=>new{direction=d,keys=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetEditorCurve(dst,UnityEditor.EditorCurveBinding.FloatCurve("DirectionVisual/"+d+"/Motion",typeof(UnityEngine.Transform),"m_LocalPosition.y")).keys,k=>new{time=k.time,value=k.value,inTangent=k.inTangent,outTangent=k.outTangent}))})),scenes=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>new{path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}))};'''
contract=unwrap(client.tool('execute_code',dict(action='execute',code=code)))['data']['result']
assert contract['ownReview'] is False and contract['headRendererNull'] and contract['headSprites']==0 and all(not x['dirty'] for x in contract['scenes'])
layout=read(D/'staged_art/TreasureChest_Directions.layout.json');offset=layout['referenceBottom']+layout['referenceHeight']*.5
for view in contract['vertical']:
    assert len(view['keys'])==len(contract['sourceY'])
    for src,dst in zip(contract['sourceY'],view['keys']):
        assert abs(src['time']-dst['time'])<1e-6 and abs(dst['value']-(src['value']*.4+offset))<1e-5
        assert abs(dst['inTangent']-src['inTangent']*.4)<1e-4 and abs(dst['outTangent']-src['outTangent']*.4)<1e-4
assert all(sha(R/x['path'])==x['after'] for x in manifest['changes'])
write(D/'death_reuse_contract_final_20261028.json',dict(observed_at=now(),read_only_editor_contract=contract,vertical_source_lift_ratio=.4,offset=offset,source_horizontal_contract_verify=verify,actual_lifecycle=lifecycle,note='Container whole Normal/Broken states. Original Death float keys/events/duration/loop preserved; compatibility events added to dedicated clips. Nondeath Body/Normal/Broken reset confirmed in all18 final Reuse captures.'))
write(D/'scope_incremental_final_20261028.json',dict(observed_at=now(),baseline='incremental_before_20261028.json',baseline_sha256=sha(D/'incremental_before_20261028.json'),baseline_files=len(before),current_files=len(current),comparison='Union of before/current paths including additions/deletions',changes=changes,unexpected_incremental=unexpected,automatic_editor_side_effects=side_effects,protected_six=baseline['protected_six'],protected_drift=protected_drift,shared_CSharp_drift=shared_cs_drift,target_only_CSharp=[p for p in intended if p.endswith('.cs')],retained_non_shadow_sprite_count=4,prefab_semantics=legacy_after['semantics'][NAME],installed_asset_drift=[],staged_production_drift=[],legacy_unexpected_count=len(old_unexpected),legacy_semantic_failures=list(new_fail),new_unexpected_vs_preexisting_legacy=[],new_semantic_failures={},note='Only target battle/Directions/rootmeta plus automatic Reporter timestamp. Historical global differences remain; no global PASS claim.'))
note=('源宝箱为金赭木板、宽灰铁箍、正面方形锁孔、背面成对铰链，无脸/眼/牙/舌/肢体。按Container整物Normal闭合/Broken开箱状态制作；HeadNormal与兼容HeadAngry同闭合图，HeadDead为完整开箱，Body为透明1px载体，不伪造动物解剖。Up初次Curl56、额外revision_01 Curl55均结果/可能计费不明，原证据保留；已核验常设静默有界恢复授权，额外两次上限已用尽，revision_02 HTTP200成功。Down初次HTTP200。Up只对新生成真实后视图做轴向半面镜像纠正轻微三分之四偏斜，Down用原raw。只去除6905个alpha1至23外缘重采样像素，未填内部/改不透明色；实际内部透明孔0。原5个SpriteRenderer中4个非Shadow含HP PPtr保持，仅移除原Shadow。共享C#、源prefab/图集、原Container动画未改；本角色Directions/Editor适配器与真实Play审阅器及asmref已编译通过。原Idle/Death水平曲线、原事件保留、时长/loop Verify通过；兼容Walk/Attack和SetHead事件只在本角色副本，非原生事件。原Idle无复位曲线，副本补Body位置/欧拉零及Normal开/Broken关，最终18张Reuse捕获全通过。初版r01两轮168/0、719帧留作历史；实看Up死亡盖碰血条后，仅新竖向Death Motion.y键与切线降为源0.4倍，HP与原Body曲线不改。最终r02普通339帧、Up死亡358帧，两轮各84/0，共168/0、697真实PNG，均自然回Boot。实际看最终四向、strip、12板288个不同实际帧与Up/Down死亡峰值2张原尺寸PNG，覆盖四向移动、Idle/Ready/Walk/Run、上下攻击倾斜、受击白闪、双向开箱摆动淡出回收、复用闭合、暂停/恢复/2x/3x、连续转向和飞行。采样未见背景紫边、部件脱落或地面阴影；死亡峰值开盖与血条有间隔，复用恢复闭箱且Body位置/旋转为零。无腿宝箱只有整物轻微摆动，不声称足摆或表情变化；暂停与倍速推进还由真实运行记录支持。Down较原侧面更亮更平滑、开箱锁扣/后铰链造型仍待用户美术判断。仅PNG时序抽样，未实时全播GIF或逐张审完697帧。内部实现与审阅完成，user_approved=false。')
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
write(visual/'review.json',dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,note=note,viewed_sheets=sheets,sample_slots=288,distinct_actual_frame_samples=288,source_manifest='sources.json',sources_sha256=sha(visual/'sources.json'),viewed_sheet_sha256=sources['boards'],additional_viewed=additional,additional_viewed_sha256={p:sha(D/p) for p in additional},method='Actual PNG chronological sampling, full768x768 frames scaled without crop, plus two native death peak images; no GIF playback or exhaustive all-frame review',final_version_binding='version_binding_final_20261028.json'))
runtime.update(status='runtime_and_internal_visual_review_complete_pending_user_art_review',visual_review_file='visual_review_final_20261028/review.json');write(D/'runtime_summary.json',runtime)
excluded={'version_binding_final_20261028.json','final_validation_20261028.json','gif_archive_verification_20261028.json'}
files={p.relative_to(D).as_posix():sha(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts}
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest='installed_manifest_r02.json',files=files,installed_files={x['path']:x['after'] for x in manifest['changes']},production_scope_files=intended,external_evidence={p.relative_to(R).as_posix():sha(p) for p in [H/'standing_network_recovery_authorization_20261028.json',H/'generate.mjs',H/'scope_TreasureChest_final_20261028.json']},actual_png_frames=frames,frame_total=697,historical_runtime_revisions=['runtime_r01','runtime_updeath_r01'],note='Original references and uncertain/successful requests, authorization application, local derivation, staging/installation including target Editor/asmref, repair history, preplay bindings, all final697 actual PNG hashes and viewed boards sealed. Historical r01 evidence retained separately.'))
write(D/'final_validation_20261028.json',dict(observed_at=now(),transport=URL,project=project,state=state,cache_refresh=cache_refresh,errors=errors,live=live,own_review=contract['ownReview'],all_scenes=contract['scenes'],final_install_manifest='installed_manifest_r02.json',runtime_summary_sha256=sha(D/'runtime_summary.json'),version_binding_sha256=sha(D/'version_binding_final_20261028.json'),scope_sha256=sha(D/'scope_incremental_final_20261028.json'),protocol_history=client.history))
print(json.dumps(dict(ready_for_record=True,production_changes=len(changes),baseline_files=len(before),production_additions=sum(x['before'] is None for x in changes),unexpected_incremental=0,legacy_unexpected=len(old_unexpected),legacy_semantic_failures=list(new_fail),frames=697,actual_visual_samples=288,live=live),ensure_ascii=False))
