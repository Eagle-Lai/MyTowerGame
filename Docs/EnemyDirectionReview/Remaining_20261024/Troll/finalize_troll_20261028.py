"""Seal the actually reviewed Troll installation; do not rebuild or repeat Play."""
from session_troll import *
import time
from PIL import Image

chain=owner();assert URL=='http://127.0.0.1:8088/mcp'
assert not (D/'final_validation_20261028.json').exists(), 'Inspect existing final evidence before resuming'
progress=read(H/'progress.json');assert progress['completed_count']==88
item=next(x for x in progress['items'] if x['name']==NAME)
assert item['status']=='runtime_complete_pending_visual_check' and item.get('user_approved') is False
baseline=read(D/'incremental_before_20261028.json');before={p:s.upper() for p,s in baseline['files'].items()};current=inventory()
battle='Assets/Prefabs/Enemy/Enemy_Troll.prefab';art='Assets/_UIAssets/Monsters/Giants/Troll/Directions'
changes=[dict(path=p,before=before.get(p),after=current.get(p)) for p in sorted(set(before)|set(current)) if before.get(p)!=current.get(p)]
unexpected=[];side_effects=[]
for x in changes:
    p=x['path']
    if p==battle or p==art+'.meta' or p.startswith(art+'/'):continue
    if p=='Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs']==before['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+',(R/p).read_text(encoding='utf-8')):
        side_effects.append(dict(x,origin='Unmodified ReporterEditor Play timestamp'))
    else:unexpected.append(x)
assert not unexpected,unexpected
protected_drift=[p for p,s in baseline['protected_six'].items() if p!=battle and sha(R/p)!=s.upper()]
assert not protected_drift,protected_drift
assert all(sha(D/'reference'/Path(p).name)==s.upper() for p,s in baseline['protected_six'].items())
shared_cs_drift=[p for p in set(before)|set(current) if p.endswith('.cs') and current.get(p)!=before.get(p)]
assert not shared_cs_drift,shared_cs_drift
legacy_before=read(H/'scope_Troll_before_20261028.json');legacy_after=read(H/'scope_Troll_final_20261028.json')
old_unexpected={x['path']:x.get('after') for x in legacy_before['unexpected']}
assert {x['path']:x.get('after') for x in legacy_after['unexpected']}==old_unexpected
old_fail={n:s['unexpected'] for n,s in legacy_before['semantics'].items() if not s['pass']}
new_fail={n:s['unexpected'] for n,s in legacy_after['semantics'].items() if not s['pass']}
assert old_fail==new_fail and legacy_after['semantics'][NAME]['pass']
manifest=read(D/'installed_manifest.json');installed={x['path']:x['after'].upper() for x in manifest['changes']}
assert all(sha(R/p)==s for p,s in installed.items())
verify=manifest['verification']['data']['result'];assert verify['pass'] and (D/'installed_verify.txt').read_text(encoding='utf-8')==verify['report']
intended={x['path']:x['after'] for x in changes if x['path'] not in {s['path'] for s in side_effects}}
assert {p:s for p,s in intended.items() if p!=art+'.meta'}==installed

def sprite_contract(path):
    text=path.read_text(encoding='utf-8-sig');blocks=list(re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',text,re.M|re.S))
    objects={m[2]:re.search(r'^  m_Name: (.+)$',m[3],re.M)[1] for m in blocks if m[1]=='1'};result={}
    for m in blocks:
        if m[1]!='212':continue
        go=re.search(r'^  m_GameObject: \{fileID: (-?\d+)\}',m[3],re.M)[1]
        result[m[2]]=dict(name=objects[go],game_object=go,sprite=re.search(r'^  m_Sprite: (.+)$',m[3],re.M)[1])
    return result
original=sprite_contract(D/'before'/battle);after=sprite_contract(R/battle)
assert len(original)==11 and sum(x['name']!='Shadow' for x in original.values())==10
assert {x['name'] for x in original.values()}=={'Body','Head','ArmL','ArmR','FistR','Weapon','LegL','LegR','Shadow','Bg','Fill'}
for fid,value in original.items():
    if value['name']=='Shadow':assert fid not in after
    else:assert after[fid]==value
preinstall=read(D/'preinstall_review_20261028.json')
staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()};assert staged==preinstall['staged']
for suffix in ['.png','.sprites.json','.layout.json']:
    assert sha(D/'staged_art'/('Troll_Directions'+suffix))==sha(R/art/('Troll_Directions'+suffix))
assert len(preinstall['alpha'])==14 and all(x['internal_transparent_holes']==0 for x in preinstall['alpha'].values())
quality=read(D/'chroma_pinhole_repair_20261028.json');assert quality['total']==148 and quality['max_component_pixels']==12
assert sha(D/'staged_art/Troll_Directions.png')==quality['staged_atlas_sha256']
for part,repair in quality['parts'].items():
    src=D/'staged_before_pinhole_repair'/(part+'.png');dst=D/'staged_art'/(part+'.png')
    assert sha(src)==repair['before_sha256'] and sha(dst)==repair['after_sha256']
    a=Image.open(src).convert('RGBA');b=Image.open(dst).convert('RGBA');assert a.size==b.size
    changed=[(x,y) for x,y in zip(a.getdata(),b.getdata()) if x!=y]
    assert len(changed)==repair['filled_pixels'] and all(x[3]==0 and y[3]>0 for x,y in changed)
selection=read(D/'art_selection.json');assert selection['Up']=='generation/Up/raw.png' and selection['Down']=='local_raster_revision_05/Down_sheet.png'
for direction in ['Up','Down']:
    folder=D/'generation'/direction;v=read(folder/'result.json');assert v['status']==200 and v['bytes']==(folder/'raw.png').stat().st_size
uncertain=D/'generation/Down/revision_01';assert (uncertain/'uncertain_result.json').is_file() and not (uncertain/'raw.png').exists() and not (uncertain/'result.json').exists()
assert len(list((D/'generation').glob('**/request.json')))==3
for rev in ['02','05']:
    folder=D/('local_raster_revision_'+rev);v=read(folder/'derivation.json')
    assert sha(D/v['parent'])==v['parent_sha256'] and sha(folder/'Down_sheet.png')==v['output_sha256']

runtime=read(D/'runtime_summary.json');assert runtime['passes']==168 and runtime['failures']==0 and runtime['actual_frames']==722
assert [x['revision'] for x in runtime['runtime']]==['runtime_r01','runtime_updeath_r01']
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
    bound=read(D/(rev+'_version_binding_before.json'))['binding']
    assert bound['installed']==installed and bound['installed_manifest_sha256']==sha(D/'installed_manifest.json') and bound['staged']==staged
    assert all(sha(R/p)==s for p,s in bound['source_and_dependencies'].items())
    returned=read(D/(rev+'_returned.json'));assert returned['binding_matched']
    assert returned['live']['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in returned['live'].items() if k!='scene')
    assert all(not x['shadow'] for x in rows)
    dead=[x for x in rows if x['stage']=='DeathAutoRecycle' and x['state']=='Death'];reuse=[x for x in rows if x['stage']=='Reuse'];pause=[x for x in rows if x['stage']=='Pause']
    assert dead and all(x['expression']==2 for x in dead) and dead[0]['alpha']>dead[-1]['alpha']
    assert len(reuse)==9 and all(x['alive'] and not x['recycled'] and x['expression']==0 and x['alpha']==1 and x['flash']==0 and x['speed']==1 for x in reuse)
    assert len(pause)==12 and all(x['paused'] and x['simulationDelta']==0 for x in pause)
    lifecycle[rev]=dict(death_frames=dead,reuse_frames=reuse,pause_frames=pause,all_frames_shadow_false=True,version_binding_before=rev+'_version_binding_before.json')
visual=D/'visual_review_final_20261028';sources=read(visual/'sources.json');sheets=sorted(sources['boards'])
assert len(sheets)==12 and len(sources['sources'])==288 and len({(x['revision'],x['source']) for x in sources['sources']})==288
assert all(sha(visual/p)==s for p,s in sources['boards'].items())
for x in sources['sources']:
    assert frames[x['revision']][x['source']]==x['source_sha256'] and rows_by_rev[x['revision']][x['source']]['frame']==x['frame']
additional=['runtime_r01/four_directions.png','runtime_visual_strip.png']+[x['revision']+'/'+x['file'] for x in read(visual/'full_size_candidates.json')]
assert len(additional)==8 and all((D/p).is_file() for p in additional)

client=Client();project=client.identity();errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));assert errors['data']==[]
cache_refresh=None
for attempt in range(5):
    state=client.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if attempt==0 and s['advice'].get('blocking_reasons')==['stale_status']:
        cache_refresh=unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Troll_final_live_state_read"});return true;')))
    time.sleep(1)
else:raise RuntimeError('Unity not ready; do not record')
live=probe(client);assert live['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in live.items() if k!='scene')
scenes=unwrap(client.tool('execute_code',dict(action='execute',code='return System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>new{path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}));')))['data']['result']
assert scenes and all(not x['dirty'] for x in scenes)
assert inventory()==current

write(D/'original_sprite_contracts_20261028.json',dict(observed_at=now(),before=original,original_count=11,retained_non_shadow_count=10,included_hp_sprites=True,only_removed_original_sprite='Shadow',all_retained_pptr_unchanged=True,baseline_prefab_sha256=sha(D/'before'/battle),current_prefab_sha256=sha(R/battle)))
write(D/'lifecycle_contract_final_20261028.json',dict(observed_at=now(),source_horizontal_contract_verify=verify,actual_lifecycle=lifecycle,note='Native Giant SetHead0/1/2 and Event Attack preserved. True Up rear heads remain faceless; original ArmR/FistR/Weapon hierarchy retained horizontally. Whole generated right arm/hammer is one vertical sprite.'))
write(D/'scope_incremental_final_20261028.json',dict(observed_at=now(),baseline='incremental_before_20261028.json',baseline_sha256=sha(D/'incremental_before_20261028.json'),baseline_files=len(before),current_files=len(current),comparison='Union of before/current paths including additions/deletions',changes=changes,unexpected_incremental=unexpected,automatic_editor_side_effects=side_effects,protected_six=baseline['protected_six'],protected_drift=protected_drift,shared_CSharp_drift=shared_cs_drift,retained_non_shadow_sprite_count=10,prefab_semantics=legacy_after['semantics'][NAME],installed_asset_drift=[],staged_production_drift=[],legacy_unexpected_count=len(old_unexpected),legacy_semantic_failures=list(new_fail),new_unexpected_vs_preexisting_legacy=[],new_semantic_failures={},note='Target battle/Directions/rootmeta plus automatic Reporter timestamp only. Historical global differences remain; no global PASS claim.'))
note=('源Troll为金赭斑点双足巨人，秃头尖耳，解剖左耳单灰环、琥珀眼、正常锯齿嘴/攻击张嘴小牙/死亡空圆眼，三牙项链、椭圆螺旋扣、破边围布、腕带、正面三趾甲，解剖右手一把木柄灰白石锤，未增加毛发/角/尾。Up和Down初次各HTTP200；Down定点躯干纠偏revision_01遇Curl55 Send reset，结果及可能计费未知，原请求/输出保留，没有网络重试。复用成功Down原图的头/臂/腿，仅对新生成正面躯干作本地轴向纠偏：最终local_raster_revision_05沿用r02，把生成躯干右半对称并保留同图完整三牙项链和椭圆扣；r01横纹/r03底色掩码/r04硬接缝等拒绝稿保留，不使用原侧图伪造正背图。肩臂pivot按真实根部测量，Up手臂置后、Down置前，腿缩至原巨人比例，14透明切片。仅148个全封闭零alpha微孔用最近原不透明像素补齐，最大组件12；原有不透明及AA像素不变，最终14片内部透明孔0。原11 SpriteRenderer保留10个非Shadow含HP原PPtr，仅移除Shadow；源prefab/atlas、Giant原动画及所有共享C#未改。安装Verify通过原Ready/Walk/Attack/Death水平曲线、原事件、时长/loop和重复重建；原上下表情事件保留，背面三状态均无脸。普通362帧、Up死亡360帧，两轮各84/0，共168/0、722真实PNG，安装/暂存/直接代码依赖在两轮前后hash一致，均自然回Boot。实际审阅四向、strip、12板288个不同实帧，另6张原尺寸上下攻击/双向死亡PNG。涵盖四向双腿错相步行、Idle/Ready/Walk/Run、上下蓄力挥锤和复位、受击闪白、双向死亡旋转淡出及18张复用、暂停/恢复/2x/3x、连续转向和飞行。Down挥锤根部连接完整；Up挥锤峰值臂柄被背/围布遮住，锤头短暂显于双腿间，未见独立漂浮或切片断口；这一后向打击可读性连同较原侧面更窄更直立的正背比例、对称躯干斑点和局部柔化仍待用户美术判断。采样未见紫底/地面阴影或死亡部件脱落；白闪结束、淡出及复用alpha/表情恢复还由实际记录支持。仅PNG时序抽样，未实时全播GIF或逐张审完722帧。内部实现和审阅完成，completed_pending_user_art_review，user_approved=false。')
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
write(visual/'review.json',dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,note=note,viewed_sheets=sheets,sample_slots=288,distinct_actual_frame_samples=288,source_manifest='sources.json',sources_sha256=sha(visual/'sources.json'),viewed_sheet_sha256=sources['boards'],additional_viewed=additional,additional_viewed_sha256={p:sha(D/p) for p in additional},method='Actual chronological PNG sampling, full768 frames scaled without crop, plus six native attack/death images; no GIF playback or exhaustive all-frame review',final_version_binding='version_binding_final_20261028.json'))
runtime.update(status='runtime_and_internal_visual_review_complete_pending_user_art_review',visual_review_file='visual_review_final_20261028/review.json');write(D/'runtime_summary.json',runtime)
excluded={'version_binding_final_20261028.json','final_validation_20261028.json','gif_archive_verification_20261028.json'}
files={p.relative_to(D).as_posix():sha(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts}
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest='installed_manifest.json',files=files,installed_files=installed,production_scope_files=intended,external_evidence={p.relative_to(R).as_posix():sha(p) for p in [H/'standing_network_recovery_authorization_20261028.json',H/'generate.mjs',H/'scope_Troll_final_20261028.json']},actual_png_frames=frames,frame_total=722,note='Original references, successful and uncertain requests, local derivations and rejected drafts, pinhole repair, staging/installation, both pre/post Play bindings, all722 actual PNG hashes and viewed boards sealed. No charge inference for uncertain Down correction.'))
write(D/'final_validation_20261028.json',dict(observed_at=now(),transport=URL,project=project,state=state,cache_refresh=cache_refresh,errors=errors,live=live,all_scenes=scenes,final_install_manifest='installed_manifest.json',runtime_summary_sha256=sha(D/'runtime_summary.json'),version_binding_sha256=sha(D/'version_binding_final_20261028.json'),scope_sha256=sha(D/'scope_incremental_final_20261028.json'),protocol_history=client.history))
print(json.dumps(dict(ready_for_record=True,production_changes=len(changes),baseline_files=len(before),production_additions=sum(x['before'] is None for x in changes),unexpected_incremental=0,legacy_unexpected=len(old_unexpected),legacy_semantic_failures=list(new_fail),frames=722,actual_visual_samples=288,live=live),ensure_ascii=False))
