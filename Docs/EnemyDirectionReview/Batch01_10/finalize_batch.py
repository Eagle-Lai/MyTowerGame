"""Freeze the completed authorized batch and produce the review index. Docs output only."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,datetime,difflib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
b=read('local_baseline.json');boundary=read('handoff_boundary.json');progress=read('progress.json')
audit=read('scope_final.json');handoff=read('handoff_boundary_audit.json')
assert not audit['unexpected_prefab_changes'] and not audit['original_sources_or_GUID_drift'] and not audit['shared_animation_drift']
assert all(v['pass'] for v in audit['prefab_semantics'].values()) and handoff['frozen_inputs_unchanged']
assert audit['untouched_prefabs']==109
assert len(progress['items'])==10 and all(i['runtime_verified'] and i['visual_reviewed'] for i in progress['items'])
assert progress['approved_example_regression']['runtime_verified'] and progress['approved_example_regression']['visual_reviewed']
for item in progress['items']+[dict(progress['approved_example_regression'],name='AdvancedHen')]:
    inputs=read(item['name']+'/'+item['runtime_revision']+'/observed_input_fingerprints.json')['files']
    drift=[relative for relative,value in inputs.items() if sha(ROOT/relative)!=value]
    assert not drift, (item['name'],drift)
paths=set()
for t in b['targets']:
    paths.add(ROOT/t['battle']);paths.add(ROOT/(t['battle']+'.meta'))
    art=ROOT/t['art_dir'];paths.add(art.with_suffix('.meta'))
    paths|={p for p in art.rglob('*') if p.is_file()}
for relative in ['Assets/Scripts/Enemy/EnemyDirectionalProfile.cs','Assets/Scripts/Enemy/EnemyDirectionalVisual.cs','Assets/Editor/EnemyDirectionPrefabBuilder.cs','Assets/Editor/EnemyDirectionalRigBuilder.cs','Assets/Editor/EnemyDirectionBatchReview.cs']:
    paths.add(ROOT/relative);paths.add(ROOT/(relative+'.meta'))
entries=[]
baseline_hashes=dict(boundary['files'])
for target in b['targets']:baseline_hashes.update(target['files'])
original_code={s['path'] for s in read('source_snapshot.json')}
for p in sorted(paths):
    if not p.is_file():continue
    relative=p.relative_to(ROOT).as_posix()
    inventory_only=relative.endswith('.cs.meta') and relative[:-5] in original_code
    entries.append({'path':relative,'before_sha256':baseline_hashes.get(relative),'after_sha256':sha(p),'bytes':p.stat().st_size,'baseline_status':'unchanged_metadata_inventory_only_no_before_hash' if inventory_only else 'recorded' if relative in baseline_hashes else 'new_file'})
manifest={'observed_at':datetime.datetime.now().astimezone().isoformat(),'baseline':'handoff_boundary.json plus local_baseline.json; existing user edits preserved','files':entries,'note':'All modified existing files have exact before/after hashes. Existing code .meta files were not written by this task; their initial hashes were not collected and they are explicitly inventory-only. Before=null otherwise denotes new files.'}
(HERE/'implementation_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
snapshot={s['path']:s for s in read('source_snapshot.json')}
patch=[]
for p in sorted(paths):
    if p.suffix!='.cs':continue
    relative=p.relative_to(ROOT).as_posix()
    prior=snapshot.get(relative,{})
    # Existing source snapshot stores the exact initial local file, including user edits.
    initial=prior.get('content',prior.get('text',''))
    if prior and not initial:raise ValueError('Missing baseline source content: '+relative)
    patch.extend(difflib.unified_diff(initial.splitlines(keepends=True),p.read_text(encoding='utf-8-sig').splitlines(keepends=True),fromfile='before/'+relative,tofile='after/'+relative))
(HERE/'final_code_changes.patch').write_text(''.join(patch),encoding='utf-8')
frozen={relative:sha(ROOT/relative) for relative in boundary['files']}
frozen.update({e['path']:e['after_sha256'] for e in entries})
for t in b['targets']:
    for relative in t['files']:frozen[relative]=sha(ROOT/relative)
for relative in read('shared_animation_baseline.json')['files']:frozen[relative]=sha(ROOT/relative)
freeze={'observed_at':manifest['observed_at'],'purpose':'Final artwork/code/config freeze for the numerical task strict rerun after explicit return.','files':dict(sorted(frozen.items()))}
(HERE/'final_frozen_fingerprints.json').write_text(json.dumps(freeze,indent=2),encoding='utf-8')
lines=['# 后续 10 个敌人审核材料','',
'已按文件名顺序接入 Bat 至 BoarMounted，并完成逐个真实 Play 验收与画面检查。AdvancedHen 的共享代码回归也已完成。本批之后是 `Enemy_BugQueen.prefab`，未接入。','',
'每项 84 PASS：四向实际位移、首段/重复节点、滞回、镜像、原生攻击表情事件、Idle/Ready/Walk/Run、受击白闪、致死闪白消退、全身淡出收缩、自动入池并取回同实例、跨帧暂停、1/2/3 倍速、连续转弯和飞行直线。测试使用临时未保存场景及内存配置，媒体来自真实 Unity 帧；无手动 Animator.Update 采样媒体。','',
'|角色|四向|上下行走|转向|攻击/死亡/复用|实测|','|---|---|---|---|---|---|']
overview=Image.new('RGB',(1536,420*10),(40,48,37))
for index,item in enumerate(progress['items']):
    name=item['name'];base=name+'/'+item['runtime_revision']
    lines.append(f'|{name}|[PNG]({base}/four_directions.png)|[GIF]({base}/up_down_walk.gif)|[GIF]({base}/walk_turn.gif)|[GIF]({base}/attack_death_reuse.gif)|[84 PASS]({base}/actual_runtime_checks.txt)|')
    overview.paste(Image.open(HERE/base/'four_directions.png').convert('RGB').resize((1536,420),Image.Resampling.LANCZOS),(0,index*420))
overview.save(HERE/'batch_overview.png')
reg=progress['approved_example_regression'];regbase='AdvancedHen/'+reg['runtime_revision']
lines+=['',f'AdvancedHen 回归：[四向]({regbase}/four_directions.png)、[行走]({regbase}/up_down_walk.gif)、[84 PASS]({regbase}/actual_runtime_checks.txt)。原 R3 证据完整保留。','',
'## 范围与实现','',
'仅改动本批 10 个战斗 prefab，其他 109 个（含 AdvancedHen 和 BugQueen）与修改前本地基线逐字节相同。原图、源 prefab、共享动作与现有 GUID 无漂移；逐组件 YAML 审计确认根变换、原碰撞/战斗组件、血条、锚点及事件接收引用保持。删除仅限当前战斗 prefab 的 Shadow。','',
'公共扩展仅修改 EnemyDirectionalProfile、EnemyDirectionalVisual、EnemyDirectionPrefabBuilder，新增 EnemyDirectionalRigBuilder 与 EnemyDirectionBatchReview。角色使用独立正背分件、专用控制器和动作副本；原侧面曲线/事件/时长保留。复用既有闪白材质，不实例化材质；Bat 用 forceRenderingOff 门控保留原 enabled 翼姿动画。旧 AdvancedHen 分支维持原逻辑。','',
'单例接入入口：选中一个已授权的战斗 prefab，执行 `Tools/塔防/敌人方向批次/接入选中的单个战斗预制体`；或 `EnemyDirectionalRigBuilder.Build("Bat")`（替换成表中单个名称）。缺真实图集/切片/解剖部件即失败，不支持全目录批量重建。各角色 `installed_verify_r01.txt` 记录两次克隆重建钩子、依赖、Missing 脚本、原曲线事件和现 YooAsset 收集覆盖；真实重复导入的 `.meta` 稳定性另有记录。','',
'## 指纹和异常','',
'- [前后 SHA256 与精确实现清单](implementation_manifest.json)','- [最终冻结指纹](final_frozen_fingerprints.json)','- [119 个 prefab 范围及语义审计](scope_final.json)','- [移交时 9304 文件边界审计](handoff_boundary_audit.json)','- [进度与逐角色画面记录](progress.json)','',
'Bat runtime_r01 的旧式重复节点回归断言只 Tick 一次，尚未越过重复点，出现一项 FAIL。审核工具改为四次 Tick，未改 BaseEnemy；runtime_r02 为最终 84 PASS。原失败记录保留。后续使用修正后的工具。','',
'所有角色目录保留 reference、原始生成返回、提示词/请求/结果、去底切片过程及 staged_art。`offline_*`、CPU 拼装图只供草稿检查，不是运行证据。最终运行目录包含原始 768px PNG、严格递增 Unity 帧号日志、状态/相位/时间/血量和全部衍生媒体来源。','',
'BlueScorpion 沿用原图的金黄色身份与透镜眼，六步足/双钳/分节尾；BearMounted、BoarMounted 沿用只有鞍具没有骑手的设计。野猪为短腿圆胖体型。所有最终角色四向、死亡及复用后均无地面阴影。','',
'未执行 APK/真机、发布包构建回读、完整关卡或长期战斗。本批只完成资源依赖/现有收集覆盖，数值任务最终严格复跑由其原任务在交回后执行。Unity 编译与结束状态详见 [editor_validation.json](editor_validation.json)。','']
(HERE/'README.md').write_text('\n'.join(lines),encoding='utf-8')
progress['status']='completed_pending_user_art_review';progress['current_index']=11
progress['frozen_fingerprints']='final_frozen_fingerprints.json'
(HERE/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'implementation_files':len(entries),'frozen_files':len(frozen),'runtime_passes':sum(i['runtime_pass_count'] for i in progress['items'])+reg['runtime_pass_count'],'next':'Enemy_BugQueen.prefab'}))
