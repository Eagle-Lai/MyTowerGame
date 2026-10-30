"""Seal the reviewed final WinterOgre only; preserve failed requests and historical media."""
from session_winterogre import *
from PIL import Image
import ast, re
import numpy as np

owner()
phase = sys.argv[1]
assert phase in ['audit','seal']
REV='art_r01'
RUNS=['runtime_r01','runtime_updeath_r01']
V=D/'visual_review_art_r01_20261029'
baseline=read(D/'incremental_before_20261029.json')
before=baseline['files']; current=snapshot(); target=baseline['target']
assert len(before)==5545 and len(current)==5565
snapshot_before_play=read(D/'production_before_play_20261029.json')
installed=snapshot_before_play['final_files']
manifest=read(D/'installed_manifest.json')
assert snapshot_before_play['revision']==REV and snapshot_before_play['manifest_sha256']==sha(D/'installed_manifest.json')
assert len(installed)==21 and all(current.get(p)==s for p,s in installed.items())
assert len(manifest['changes'])==20 and manifest['verification']['data']['result']['pass']
assert all(current[r['path']]==r['after'] and before.get(r['path'])==r['before'] for r in manifest['changes'])
verify=(D/'installed_verify.txt').read_text(encoding='utf-8-sig').strip()
assert verify==manifest['verification']['data']['result']['report'].strip()
assert all(s.startswith('PASS ') for s in verify.splitlines())
changes=[{'path':p,'before':before.get(p),'after':current.get(p)} for p in sorted(set(before)|set(current)) if before.get(p)!=current.get(p)]
folder_meta=target['art_dir']+'.meta'
meta_text=(ROOT/folder_meta).read_text(encoding='utf-8-sig')
guid=re.search(r'^guid: ([0-9a-f]{32})$',meta_text,re.M)[1]
assert before.get(folder_meta) is None and 'folderAsset: yes' in meta_text
assert len([p for p in (ROOT/'Assets').rglob('*.meta') if re.search(r'^guid: '+guid+r'$',p.read_text(encoding='utf-8-sig'),re.M)])==1
folder_meta_report={'path':folder_meta,'sha256':current[folder_meta],'guid':guid,'folderAsset':True,
    'classification':'New WinterOgre Directions root folder meta; installer/prePlay scan omitted parent-level meta.',
    'not_present_in_initial_baseline':True,'unique_guid_in_Assets':True}
side=[]
for row in changes:
    if row['path']=='Assets/StreamingAssets/build_info':
        assert current['Assets/Reporter/Editor/ReporterEditor.cs']==before['Assets/Reporter/Editor/ReporterEditor.cs']
        assert re.fullmatch(r'Build from .+ at .+', (ROOT/row['path']).read_text(encoding='utf-8'))
        side.append(dict(row,origin='Unmodified ReporterEditor automatic Play timestamp'))
unexpected=[r for r in changes if r['path'] not in set(installed)|{folder_meta}|{r['path'] for r in side}]
assert not unexpected
assert (len(changes),sum(r['before'] is None for r in changes),sum(r['after'] is None for r in changes))==(22,20,0)
protected=baseline['protected_six']
assert all(current[p]==s for p,s in protected.items() if p!=target['battle'])
assert all(sha(D/'reference'/Path(p).name)==s for p,s in protected.items())
cs_drift=[p for p in set(before)|set(current) if p.endswith('.cs') and before.get(p)!=current.get(p)]
assert not cs_drift
audit_source=H.parent/'Batch01_10/audit_scope.py'
tree=ast.parse(audit_source.read_text(encoding='utf-8-sig'))
definitions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
ns={'re':re,'hashlib':hashlib,'HERE':H,'ROOT':ROOT,'targets':{NAME:target}}
exec(compile(definitions,str(audit_source),'exec'),ns)
semantic=ns['semantic'](NAME)
assert semantic['pass'],semantic
offline=read(D/'offline_review_final_20261029.json')
assert offline['offline_visual_pass'] and offline['revision']==REV
assert all(sha(D/'staged_art'/p)==s for p,s in offline['stage_files'].items())
assert all(sha(D/'staged_art'/p)==current[target['art_dir']+'/'+p] for p in ['WinterOgre_Directions.png','WinterOgre_Directions.sprites.json','WinterOgre_Directions.layout.json'])
spec=read(D/'staged_art/WinterOgre_Directions.sprites.json')
atlas=Image.open(D/'staged_art/WinterOgre_Directions.png').convert('RGBA')
assert atlas.size==(2048,2048) and spec['ppu']==100 and len(spec['sprites'])==14
parts={}
for s in spec['sprites']:
    p=D/'staged_art'/(s['name']+'.png'); im=Image.open(p).convert('RGBA')
    assert im.size==(s['w'],s['h']) and im.getchannel('A').getbbox()
    a=np.array(im); b=np.array(atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y'])))
    assert np.array_equal(a[:,:,3],b[:,:,3]) and np.array_equal(a[a[:,:,3]>0],b[a[:,:,3]>0])
    parts[s['name']]={'sha256':sha(p),'size':list(im.size),'pivot':[s['pivotX'],s['pivotY']]}
pixels=np.array(atlas).astype(np.int16)
assert not np.any((np.minimum(pixels[:,:,0],pixels[:,:,2])-pixels[:,:,1]>18)&(pixels[:,:,3]>30))
assert len({parts['Up_Head'+p]['sha256'] for p in ['Normal','Angry','Dead']})==1
runtime=read(D/'runtime_summary.json')
assert (runtime['passes'],runtime['failures'],runtime['actual_frames'])==(168,0,716)
assert [r['revision'] for r in runtime['runtime']]==RUNS
frames={}
for run in runtime['runtime']:
    folder=D/run['revision']
    records=[json.loads(l) for l in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l]
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8-sig').splitlines()
    assert run['pass']==84 and run['fail']==0 and len(records)==run['frames']
    assert sum(s.startswith('PASS ') for s in checks)==84 and not any(s.startswith('FAIL ') for s in checks)
    assert sha(folder/'actual_frames.jsonl')==run['records_sha256']
    assert all(b['frame']>a['frame'] and b['realtime']>a['realtime'] for a,b in zip(records,records[1:]))
    assert not any(r['shadow'] for r in records)
    frames[run['revision']]={r['file']:sha(folder/r['file']) for r in records}
    assert len(frames[run['revision']])==len(list((folder/'frames').glob('*.png')))
    start=D/(run['revision']+'_start.json')
    assert read(start)['project']['projectRoot']=='E:/MyTowerGame' and start.stat().st_mtime>(D/'production_before_play_20261029.json').stat().st_mtime
    assert read(D/(run['revision']+'_returned.json'))['state']=={'playing':False,'review':False,'scene':'Assets/Scenes/Boot.unity','dirty':False}
assert read(D/'runtime_updeath_r01_start.json')['death_up'] is True
board=read(V/'sources.json')['sources']; positions=len(board)
unique=len({(r['revision'],r['source']) for r in board})
assert positions==281 and all(frames[r['revision']][r['source']]==r['source_sha256'] for r in board)
samples=read(V/'gif_samples.json')['samples']
assert len(samples)==60 and len({(r['revision'],r['file']) for r in samples})==12
for r in samples:
    p=D/r['revision']/r['file']; assert sha(p)==r['gif_sha256']
    with Image.open(p) as gif:
        assert gif.n_frames==r['frame_count'];gif.seek(r['frame_index_zero_based'])
        im=gif.convert('RGB').crop(r['stable_crop']);im.thumbnail((300,215),Image.Resampling.LANCZOS)
        assert hashlib.sha256(im.tobytes()).hexdigest().upper()==r['sample_sha256']
full=read(V/'uncropped_gif_sources.json')
assert len(full)==4
for r in full:
    assert sha(D/r['source'])==r['source_sha256'] and sha(D/r['output'])==r['output_sha256']
    with Image.open(D/r['source']) as gif:
        gif.seek(r['frame']);assert gif.convert('RGB').tobytes()==Image.open(D/r['output']).convert('RGB').tobytes()
originals=read(D/'original_png_selection_20261029.json')
assert len(originals)==8 and all(p.split('/',1)[1] in frames[p.split('/',1)[0]] for p in originals)
fix=read(D/'native_walk_media_fix_20261029.json')
assert fix['encoded_cycle_ms']==670 and abs(fix['native_clip_seconds']-2/3)<1e-5 and len(fix['changes'])==6
for r in fix['changes']:
    assert sha(D/r['revision']/r['file'])==r['after_sha256']
    assert sha(D/'media_before_native_loop_fix_20261029'/r['revision']/r['file'])==r['before_sha256']
uncertain=sorted((D/'generation').rglob('uncertain_result.json'))
successful=sorted((D/'generation').rglob('result.json'))
assert len(uncertain)==5 and len(successful)==2 and all(read(p)['status']==200 for p in successful)
probe=read(D/'unity_release_final_20261029.json')
assert probe['success'] and probe['transport']=='http://127.0.0.1:8088/mcp'
assert probe['errors']['data']==[] and probe['compile_errors']['data']==[]
idle(probe['final_probe']);imports=probe['installed_data']
assert imports['spriteCount']==14 and imports['spriteMode']=='Multiple' and imports['ppu']==100
assert imports['alphaIsTransparency'] and not imports['mipmaps'] and imports['weaponEnabled'] is False
for s in spec['sprites']:
    actual=next(x for x in imports['sprites'] if x['name']==s['name'])
    assert all(abs(actual[k]-s[k])<1e-4 for k in ['x','y','w','h'])
    assert abs(actual['pivotX']-s['pivotX']*s['w'])<1e-3 and abs(actual['pivotY']-s['pivotY']*s['h'])<1e-3
contract=read(D/'source_contract_20261029.json')['contract']
for live in imports['clips']:
    old=next(c for c in contract['clips'] if c['name']==live['name'])
    assert (live['length'],live['rate'],live['loop'])==(old['length'],old['rate'],old['loop'])
    assert live['floatBindings']==len(old['floatCurves']) and live['objectBindings']==0
    assert live['events']==[{k:e[k] for k in ['time','functionName','intParameter','stringParameter']} for e in old['events']]
assert target['art_dir']+'/WinterOgre_Directions.png' in imports['dependencies']
assert target['art_dir']+'/WinterOgre_Directions.asset' in imports['dependencies']
assert 'PASS YooAsset prefab and artwork collectors present' in verify

note=f'最终art_r01实际审过两轮four_directions和runtime strip、12张时序/步态板（{positions}采样位、{unique}张不同真实PNG）、8张768像素完整原PNG、12个最终GIF各5个编码帧共60帧、另4张未裁切GIF整帧；最终离线图和两个成功raw的实审记录保留。金赭斑点、秃顶尖耳、矮壮双足、白毛裙和大型棕白护腕保留，两手为空拳；原Weapon renderer禁用、不把图集未用手杖装到角色上。Up纯后脑无脸、光滑后跟，Down正常/愤怒/死亡表情与脚趾正确。原侧面保持，轴向正背面比原侧面窄；头身/肩髋连接、错相短腿行走、连续转向和拳击蓄力/展开在抽样中正常，无地面阴影。受击白闪结束、Down及Up全身死亡旋转缩小淡出、自动回收和同实例Down正常复用、暂停冻结/恢复及1x/2x/3x相位推进正常。淡出时既有逐renderer alpha会透出重叠分件。GIF通用脚本误用0.5秒，已仅在本角色使用实际记录相位和原Walk0.6666667秒修正为GIF670毫秒，原6个错误时长GIF作为历史保留；没有合成姿态或修改共享脚本/原动画。GIF采用编码帧和原PNG时序抽样，未实时播放或逐帧全审，固定裁图可能截断极端展开，已另看完整帧。224个残余品红RGB边像素本地清理且alpha/形状不变，原件/初版布局/清理前暂存保留。旧5次Up传输结果及费用仍不明；服务新证据后Up05和首次Down均HTTP200，两个raw原件保留；没有把usage聚合或空batch当作退款/失败证明。两轮各84PASS/0FAIL，共716张真实PNG。内部技术视觉通过，仍待用户美术验收。'
reviewed=['runtime_visual_strip.png']+[run+'/four_directions.png' for run in RUNS]
reviewed += [p.relative_to(D).as_posix() for p in V.glob('*.png')]
visual={'reviewed_at':now(),'character':NAME,'owner_thread_id':OWNER,'dispatch_token':TOKEN,'final_revision':REV,
    'reviewed_images':{p:sha(D/p) for p in reviewed},'selected_original_pngs':{p:sha(D/p) for p in originals},
    'sample_positions':positions,'unique_board_source_pngs':unique,'encoded_gif_samples':60,'gif_count':12,
    'additional_uncropped_encoded_frames':4,'observations':note,'technical_visual_pass':True,'user_approved':False,
    'limitations':['Chronological PNG and encoded GIF sampling, no realtime playback or exhaustive every-frame review.',
                   'Existing per-renderer death alpha exposes overlapping parts during fade.',
                   'Axial views narrower than original side view; fixed crop can omit fully spread arms, full frames also inspected.'],
    'offline_review_file':'offline_review_final_20261029.json','native_walk_media_fix':'native_walk_media_fix_20261029.json'}
scope={'observed_at':now(),'baseline':'incremental_before_20261029.json','baseline_sha256':sha(D/'incremental_before_20261029.json'),
    'comparison':'Full path union Assets/Packages/ProjectSettings/Luban vs current disk initial baseline, not Git HEAD.',
    'baseline_files':len(before),'current_files':len(current),'changes':changes,'added_count':20,'deleted_count':0,
    'unexpected_incremental':unexpected,'automatic_editor_side_effects':side,'directions_root_meta':folder_meta_report,
    'protected_six':protected,'protected_drift':[],'shared_CSharp_drift':cs_drift,'installed_files':installed,
    'prePlay_production_drift':[],'prefab_semantics':semantic,'stage_parts':parts,
    'legacy_global_note':'Historical global scope failures preserved and not re-audited; only WinterOgre incremental PASS.'}
archive_path=H.parent/'AllGIF/manifest.json'
if phase=='audit':
    write(D/'scope_incremental_final_20261029.json',scope,fresh=True)
    write(V/'review.json',visual,fresh=True)
    assert not (D/'record_note_utf8.txt').exists()
    (D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
    archive=read(archive_path)
    assert not any(r['source'].startswith('Remaining_20261024/WinterOgre/') for r in archive['files'])
    write(D/'archive_before_record_20261029.json',{'count':archive['count'],'sources':[r['source'] for r in archive['files']],
        'manifest_sha256':sha(archive_path)},fresh=True)
    print(json.dumps({'phase':'audit','changes':len(changes),'unexpected':0,'semantic_pass':True,'positions':positions,'unique_pngs':unique}))
    raise SystemExit(0)

assert read(D/'scope_incremental_final_20261029.json')['changes']==changes
assert read(V/'review.json')['observations']==note and not (D/'final_validation_20261029.json').exists()
progress=read(H/'progress.json');item=next(i for i in progress['items'] if i['name']==NAME)
assert progress['completed_count']==99 and item['status']!='completed_pending_user_art_review'
runtime.update(final_revision=REV,visual_reviewed=True,visual_review_file='visual_review_art_r01_20261029/review.json',
    visual_note=note,user_approved=False,status='completed_pending_user_art_review')
write(D/'runtime_summary.json',runtime)
record=subprocess.run([sys.executable,str(H/'record_review.py'),NAME,note],capture_output=True,text=True,encoding='utf-8',check=True)
archive=read(archive_path);rows=[r for r in archive['files'] if r['source'].startswith('Remaining_20261024/WinterOgre/')]
actual_sources={p.relative_to(H.parent).as_posix() for p in D.rglob('*.gif')}
assert len(rows)==len(actual_sources)==18
assert {r['source'] for r in rows}==actual_sources
for r in rows:
    assert sha(H.parent/r['source'])==r['sha256']==sha(H.parent/'AllGIF'/r['file'])
assert sum(r['status']=='当前审核版本' for r in rows)==12
old=read(D/'archive_before_record_20261029.json')
assert archive['count']==old['count']+len(rows)
assert set(r['source'] for r in archive['files'])-set(old['sources'])==actual_sources
archive_report={'verified_at':now(),'source_gif_count':len(rows),'final_review_gifs':12,'historical_gifs':6,
    'global_archive_count_before':old['count'],'global_archive_count':archive['count'],
    'all_source_and_archive_sha256_match':True,'files':rows,'manifest_sha256':sha(archive_path)}
write(D/'gif_archive_verification_20261029.json',archive_report,fresh=True)
progress=read(H/'progress.json');item=next(i for i in progress['items'] if i['name']==NAME)
assert progress['completed_count']==100 and item['status']=='completed_pending_user_art_review' and item['user_approved'] is False
remaining=[i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[i for i in remaining if i['status'] not in ['not_started','blocked']]
selected=min(recoverable or [i for i in remaining if i['status']!='blocked'],key=lambda i:i['index'])
assert selected['name']=='WinterWarg' and selected['index']==112
item.update(stage='recorded_pending_user_art_review',final_revision=REV,recovery_stage='Up05_Down_installed_both_runtime_visual_record_complete',
    generation_outcome='Up05 and first Down HTTP200/raw reviewed; previous five Up uncertain and unknown charges retained',
    unity_release_file='Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/unity_release_final_20261029.json',
    final_validation_file='WinterOgre/final_validation_20261029.json',version_binding_file='WinterOgre/version_binding_final_20261029.json',
    scope_file='WinterOgre/scope_incremental_final_20261029.json',visual_review_file='WinterOgre/visual_review_art_r01_20261029/review.json',
    gif_archive_file='WinterOgre/gif_archive_verification_20261029.json')
progress.update(current=selected['name'],updated_at=now());write(H/'progress.json',progress)
evidence={p.relative_to(D).as_posix():sha(p) for p in sorted(D.rglob('*')) if p.is_file() and 'frames' not in p.relative_to(D).parts
    and p.name not in ['version_binding_final_20261029.json','final_validation_20261029.json']}
binding={'observed_at':now(),'final_revision':REV,'manifest':'installed_manifest.json','manifest_sha256':sha(D/'installed_manifest.json'),
    'prePlay_snapshot_sha256':sha(D/'production_before_play_20261029.json'),'installed_files':installed,
    'additional_directions_root_meta':folder_meta_report,'production_scope_files':{r['path']:r['after'] for r in changes},
    'files':evidence,'actual_png_frames':frames,'frame_total':716,
    'note':'21 prePlay fingerprints unchanged; additional new folder meta explicitly audited; art_r01 installed before both Play rounds.'}
write(D/'version_binding_final_20261029.json',binding,fresh=True)
final={'observed_at':now(),'character':NAME,'owner_thread_id':OWNER,'dispatch_token':TOKEN,'status':item['status'],'user_approved':False,
    'final_revision':REV,'passes':168,'failures':0,'actual_png_frames':716,'runtime':runtime['runtime'],'installer_verify_pass':True,
    'manifest_sha256':sha(D/'installed_manifest.json'),'incremental_scope_file':'scope_incremental_final_20261029.json',
    'incremental_scope_sha256':sha(D/'scope_incremental_final_20261029.json'),'incremental_changes':22,'incremental_unexpected':0,
    'prefab_semantic_pass':True,'version_binding_file':'version_binding_final_20261029.json',
    'version_binding_sha256':sha(D/'version_binding_final_20261029.json'),'visual_review_file':'visual_review_art_r01_20261029/review.json',
    'visual_review_sha256':sha(V/'review.json'),'gif_archive_file':'gif_archive_verification_20261029.json',
    'gif_archive_sha256':sha(D/'gif_archive_verification_20261029.json'),'archived_character_gifs':18,'final_review_gifs':12,
    'historical_gifs':6,'global_archive_count':archive['count'],
    'unity':{'transport':probe['transport'],'project':probe['project'],'live_probe':probe['final_probe'],'ready_for_tools':True,
             'current_console_errors':0,'current_error_CS':0,'earlier_errors_retained_in_evidence':True,'evidence':'unity_release_final_20261029.json'},
    'progress':{'completed_count':100,'authorized_count':108,'next_candidate':selected['name']},
    'generation':{'successful_http200':2,'old_uncertain_requests':5,'old_unknown_charges_retained':True,
                  'uncertain_evidence':{p.relative_to(D).as_posix():sha(p) for p in uncertain},
                  'successful_evidence':{p.relative_to(D).as_posix():sha(p) for p in successful},'usage_is_not_bill':True},
    'record_review_output':record.stdout.strip(),'legacy_global_scope_warning':scope['legacy_global_note']}
write(D/'final_validation_20261029.json',final,fresh=True)
stage('recorded_pending_user_art_review','Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/final_validation_20261029.json')
print(json.dumps({'phase':'sealed','completed_count':100,'passes':168,'failures':0,'frames':716,'archived_gifs':18,
                  'archive_count':archive['count'],'next':selected['name']},ensure_ascii=False))
