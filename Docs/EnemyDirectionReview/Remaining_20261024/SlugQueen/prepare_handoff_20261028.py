"""Persist final evidence and release unique ownership for one fresh Swine chat."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,re,sys,time,uuid
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client,URL
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
rel=lambda p:p.relative_to(R).as_posix()
chain=read(H/'conversation_chain.json');parent=os.environ['CODEX_THREAD_ID']
assert chain['state']=='active' and chain['owner_thread_id']==parent and chain['current_character']=='SlugQueen'
assert chain['dispatch_token']=='sheep-to-slugqueen-5dd11f24cb8646d0ac5a622d232ec22d'
progress=read(H/'progress.json');assert progress['completed_count']==85
item=next(x for x in progress['items'] if x['name']=='SlugQueen')
assert item['status']=='completed_pending_user_art_review' and item['user_approved'] is False
binding=read(D/'version_binding_final_20261028.json')
assert all(sha(D/p)==s for p,s in binding['files'].items())
assert all(sha(R/p)==s for p,s in binding['installed_files'].items())
assessment=[]
for x in sorted((x for x in progress['items'] if x['status'] not in ['completed_pending_user_art_review','user_approved']),key=lambda x:x['index']):
    folder=H/x['name'];files=sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
    assessment.append(dict(index=x['index'],name=x['name'],status=x['status'],files=files,checkpoints=[p for p in ['anatomy_plan.json','installed_manifest.json','runtime_summary.json'] if (folder/p).is_file()],raw=[p for p in files if p.endswith('/raw.png')],runtime_directories=[p.name for p in folder.glob('runtime*') if p.is_dir()],blocked_reason=x.get('blocked_reason')))
blocked=[x for x in assessment if x['status']=='blocked'];available=[x for x in assessment if x['status']!='blocked']
assert len(blocked)==1 and blocked[0]['name']=='PossessedWarg'
assert len(available)==22 and all(x['status']=='not_started' and not x['checkpoints'] and not x['raw'] and not x['runtime_directories'] and all(p.startswith('reference/') for p in x['files']) for x in available)
successor=available[0];assert successor['name']=='Swine' and successor['index']==97
target=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']=='Swine')
paths=[target['battle'],target['battle']+'.meta',target['source'],target['source']+'.meta',target['atlas'],target['atlas']+'.meta']
original=read(H/'production_fingerprints_before.json');six={p:sha(R/p) for p in paths}
assert all(six[p]==original[p] and sha(H/'Swine/reference'/Path(p).name)==six[p] for p in paths)
client=Client();project=client.identity();cache_refresh=None
for attempt in range(4):
    state=client.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if attempt==0 and s['advice'].get('blocking_reasons')==['stale_status']:
        cache_refresh=unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"SlugQueen_handoff_live_state_read"});return true;')))
    time.sleep(1)
else:raise RuntimeError('Unity not ready to release')
errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
probe=unwrap(client.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert errors['success'] and errors['data']==[] and probe['success']
released=probe['data']['result'];assert released['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in released.items() if k!='scene')
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S');token='slugqueen-to-swine-'+uuid.uuid4().hex
handoff=H/'conversation_handoffs'/(stamp+'_SlugQueen_completed.md')
assessment_path=D/('successor_assessment_'+stamp+'.json');release_path=D/('handoff_release_'+stamp+'.json');dispatch_path=D/('successor_dispatch_'+stamp+'.json')
assert not any(p.exists() for p in [handoff,assessment_path,release_path,dispatch_path])
scope=read(D/'scope_incremental_final_20261028.json');gifs=read(D/'gif_archive_verification_20261028.json')
live=(f'2026-10-28 SlugQueen96完成，85/108，待用户美术审核user_approved=false。Up/Down各一次HTTP200，无付费返修；Up本地revision02将同图赭斑下移130px并清理浅边，Down原raw。只在自有Walk补Body Euler三轴0，70原绑定/事件/时序保留；旧r01现场复用前后z=0，最终仅换图集且动画SHA不变。最终runtime_r02/runtime_updeath_r02各84/0共674真实帧，实际审四方向/strip、10板(256采样位/226不同帧)及3张原尺寸PNG，未播放GIF全片或逐帧全审。AllGIF{gifs["total"]}，SlugQueen{gifs["character_count"]}含{gifs["current_count"]}当前版。5238基线并集22变化20新增，增量unexpected0；原Sprite/六保护/语义/安装绑定通过。全局历史291unexpected及6其他角色语义失败保留新增0。Unity安全释放Boot非Play、全场景非dirty、空闲、编译失败false、error0。用户已将MyTowerGame连接改为HTTP Local8088，已动态身份核对；8082现场是D:/FishTestGame，禁止误操作。下一唯一Swine97，仅reference/not_started。PossessedWarg旧Down仍uncertain不重发。完整交接：{rel(handoff)}。所有权以实时chain为准，桌面控制仍须先对话确认。')
handoff_text=f'''# SlugQueen(index96) 完成与下一唯一角色交接

时间：{now()}。工程E:/MyTowerGame，Unity2022.3.62f3c1，unityMCP兼容HTTP协议直连{URL}。
父聊天：{parent}。旧令牌：{chain['dispatch_token']}。
状态completed_pending_user_art_review，user_approved=false。实时85/108；剩余23项，其中PossessedWarg阻断1项、未开始22项。

## 实际修改与返修

仅修改Assets/Prefabs/Enemy/Enemy_SlugQueen.prefab与Assets/_UIAssets/Monsters/Insects/SlugQueen/Directions。源prefab/图集、共享Larva动画、共享C#、配置表、Assets/ConfigJson/Gen、声音和其他角色均未修改；未Git同步/提交、构建或部署。生产22变化20新增，另Reporter原代码在Play自动更新时间戳单列。
Up与Down各一次正式生成HTTP200，原图1310726/1373297 bytes，原意图/request/result/raw均保留，没有重复收费请求或付费修图。最终Up选local_raster_revision_02/Up_sheet.png，Down选generation/Down/raw.png。Up同图赭斑下移130px避免被颈圈遮完；原位置用同行褐色插值填充。local_raster_revision_01有浅边被否决，r02用内缩1px加0.45px羽化遮罩去浅边；原付费图和本地r01保留。首版Down颈圈外露布局保留于offline_layout_revision_01，最终布局收颈圈并增大头。
保留无足橄榄褐色软体、三段大圆拱躯干、小尾端、唯一小金冠、短圆吻；没有腿/翼/触角/独立尾巴。Up后脑无脸，Down正常斜金眼、攻击张嘴小牙、死亡圆金眼。12 RGBA部件无opaque magenta；源含HP的4个Sprite PPtr保持。正背面较原侧面更窄、质感更平滑，最终美术判断交用户。

## 动画与实际运行

源Larva Death把Body转至-180度，Walk未复位。side_reuse_repair_r01只给本角色Walk_Directions.anim添加Body/localEulerAnglesRaw.x/y/z常量0；70条原float绑定、PPtr/事件/时长/loop保留，改后73条，不改共享动画/C#。runtime_r01现场读取复用前后Body.z均0。最终返修只替换图集，动画SHA保持DA04815C8B80A4DB97FD6FCF7FBAFB69695FC82B970FCEF393B023626ADD632A。不要全Build覆盖这个自有修复。
旧runtime_r01/runtime_updeath_r01合计670帧，虽168/0但因Up斑被遮挡而否决。旧10板只实际查看2板；准确范围见local_raster_revision_01/rejected_previous.json，不能当最终证据。
最终runtime_r02/runtime_updeath_r02各84 PASS/0 FAIL、337帧，共168/0、674张真实Unity帧。实际查看四方向/strip与visual_review_final_r02_20261028全部10板(256采样位/226不同实际帧)，另看runtime_r02/frames/DeathAutoRecycle_00162.png、ContinuousTurns_00322.png及runtime_updeath_r02/frames/DeathAutoRecycle_00162.png原尺寸。
抽样可见多节错相蠕动和轻摇、连续转向、攻击张口、白闪结束、双向倾斜淡出/回收、复用和暂停/1x/2x/3x。未见断开/重复冠/地面阴影/底色污染，复用后原侧面没有倒置。未实时播放GIF全片、未逐张审完674帧，不把PNG抽样说成全片审核。
AllGIF总{gifs['total']}，SlugQueen共{gifs['character_count']}，{gifs['current_count']}当前审核版，其余历史；来源/归档SHA256一致。入口Docs/EnemyDirectionReview/AllGIF/index.html。

## 范围、版本绑定与释放

5238文件基线按前后路径并集检查含新增/删除：22变化20新增、增量unexpected=[]；除授权battle外六保护无漂移，非美术语义/原Sprite/安装清单/暂存绑定通过。全局历史291unexpected和MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky六项既有语义失败保持、新增0，不能称全局PASS。
完整证据：SlugQueen/version_binding_final_20261028.json(全674 PNG SHA)、scope_incremental_final_20261028.json、final_validation_20261028.json、gif_archive_verification_20261028.json、record_note_utf8.txt、visual_review_final_r02_20261028/review.json；均在Docs/EnemyDirectionReview/Remaining_20261024下。record已完成，不能替用户批准。
Unity最终Boot非Play、所有场景非dirty、无编译/重载/更新、ready_for_tools=true，error0、scriptCompilationFailed=false，无review/balance/录像/manual。交接前又读现场，证据{rel(release_path)}。没有强停他人任务或桌面控制。

## 新端口与下一唯一角色

用户直接说明“我已调整到了8088，你再次尝试一下”。当前MyTowerGame为http://127.0.0.1:8088/mcp，已读custom-tools/instances、动态选完整MyTowerGame ID并核对E:/MyTowerGame及2022.3.62f3c1。mcp_call.py默认8088并支持MYTOWERGAME_MCP_URL环境变量；每次调用仍动态核对。旧server工具unityMCP仍可能连接8082的D:/FishTestGame，不得据名字直接操作。根AGENTS旧D盘/8082差异保留；当前用户新端口优先，不擅改另一个工程。
重新评估实时23项未完成：PossessedWarg旧Downuncertain不重发，其他22项只有reference，因此选Swine97。评估{rel(assessment_path)}；六项原保护和参考快照均匹配。
Swine源{target['source']}，图集{target['atlas']}，battle{target['battle']}，源Controller {target['controller']}。先实际审源图/完整prefab及动画生命周期，再定解剖与步态，不套SlugQueen无足结构，也不预设其他猪的配件。新令牌{token}。
新聊天仅在chain.state=active、owner是自己、current_character=Swine且token严格匹配后操作生产/Unity/付费。handoff_ready只读等待，不超时抢锁。默认Curl生成器、standing_network_recovery_authorization_20261028.json的有界恢复和独立桌面确认规则保持。完成一个角色后按CONTINUATION_PROTOCOL总结/更新/释放/创建唯一全新本地后继；不fork/子代理/并行/计时器/模型覆盖。创建成功父线程登记后停止所有工作区写入。
'''
next_text=f'''# 下一唯一角色 Swine(index97)

在E:/MyTowerGame继续敌人四方向串行任务。父聊天{parent}已完成SlugQueen，85/108，待用户美术审核。唯一令牌`{token}`。

## 开工与所有权

必读根AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、实时conversation_chain.json/progress.json、{rel(handoff)}、{rel(assessment_path)}、standing_network_recovery_authorization_20261028.json。相对短文件均在Docs/EnemyDirectionReview/Remaining_20261024。根AGENTS旧FreedomTower_1/D盘差异保持；目标E:/MyTowerGame。
只有chain.state=active、owner_thread_id为本聊天、current_character=Swine且dispatch_token严格匹配才可生产/Unity/付费。handoff_ready只读等待父线程登记；不靠超时抢锁，不fork/子代理/并行角色，不改模型，不计时器。

## 当前Swine阶段与执行

Swine为not_started，只有reference的Enemy_Swine.prefab/Swine.prefab/Swine.png与其meta、source_structure.json、source_prefab_offline.png；没有anatomy/generation/request/raw/stage/install/runtime。现场六项原指纹及参考快照匹配。先针对本角色读git差异、真实源图/完整prefab、调用/动画生命周期，建立自己的生产增量基线并必要prepare；不覆盖已有参考或用户改动。
源{target['source']}；battle{target['battle']}；图集{target['atlas']}；源Controller {target['controller']}。解剖、四方向、足/耳/尾等以实际源为准，不套前角色结构。查原Death与Walk对象池复位，必要时仅加本角色自有动画复位，保留原曲线/PPtr/事件/时长/loop，不改共享C#或动画。
generate_character.ps1默认Curl，SlugQueen上下各一次HTTP200无重试。密钥runtime-only/curl config stdin、HTTPS证书检查、无redirect/retry；gpt-image-2 images/edits、medium、1536x1024、n1，owner/token/六保护/输出存在门禁保持。先正式生成一方向并实际审图，再另一方向。已有成功复用、在途/uncertain先查。正常新角色不用Mounted专属AuthorizedResume；同类TLS故障仅按standing授权每方向最多2次额外新revision，保留uncertain和计数，鉴权/余额/上限问题不盲重试，不用其他角色付费探针。电脑桌面操作仍须先弹对话确认，默认使用Unity MCP。
按原prompt完成源与生成原图实际审阅、透明去底色/切片/pivot/连接、角色专属动画、单角色安装Verify；查Builder是否改原Sprite/接收器。两轮真实Play各84检查，分次1-2图实际审四方向、步态/时序、攻击、受击、死亡复用及暂停倍速；如仅PNG抽样如实说明，不能称GIF全播/全部帧已审。发现问题保留旧revision再修复重跑。绑定原请求/选图/派生/暂存/安装/全部实际帧，前后路径并集范围审计，UTF8备注record、AllGIF归档。只能completed_pending_user_art_review、user_approved=false。
安装清单不删后重装，原raw/失败请求/完整帧保留。除授权battle外六保护不动；历史291unexpected及6其他角色语义失败保留，仅本轮新增0；不称全局PASS。禁止改配置表、Assets/ConfigJson/Gen、声音、其他角色、共享C#；不Git pull/reset/clean/checkout/commit/push，不构建部署。

## Unity8088与自动续接

用户已在本轮把MyTowerGame改为HTTP Local8088，当前正确端点http://127.0.0.1:8088/mcp。原unityMCP工具仍可能接8082的D:/FishTestGame，禁止误操作；不占8080。优先复用mcp_call.py(默认8088，MYTOWERGAME_MCP_URL可指定)，每次动态custom-tools/instances→set现场MyTowerGame完整ID→project/info确认E:/MyTowerGame与2022.3.62f3c1。先读error/状态、全场景dirty、Play/编译/review/录像/manual占用，禁止强停他人或覆盖未保存场景。只在stale_status时用既有短反射ForceUpdate读真实缓存，不改flags。自己的两轮Play已授权；C#如确需修改须完整正确工程编译验证。
SlugQueen已释放Boot非Play、全场景非dirty、空闲、编译失败false、error0，见{rel(release_path)}。其自有Walk有Body三轴旋转复位，不全Build覆盖，不修改其Assets。原670帧为视觉否决历史，最终r02两轮674帧才当前版。
PossessedWarg旧Down仍uncertain，不重发。历史失败/授权范围保留，不挪用专属授权。完成或真实阻断后重新评估实时队列、写完整新交接、更新README/LIVE/NEXT/progress、安全交回Unity，按CONTINUATION_PROTOCOL动态list_projects并仅创建一个全新本地后继。create明确成功后登记新thread/host/token立即停止所有工作区写入；一次有界wait确认。不得等逐角色再授权，不建计时器或多代理。
'''
updates={}
for path,marker in [(H.parent/'README.md','ENEMY_README_LIVE'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','ENEMY_SERIAL_LIVE_STATE')]:
    text=path.read_text(encoding='utf-8');pattern=r'<!-- '+marker+r'_BEGIN -->.*?<!-- '+marker+r'_END -->'
    assert len(re.findall(pattern,text,re.S))==1
    text=re.sub(pattern,'<!-- '+marker+'_BEGIN -->\n'+live+'\n<!-- '+marker+'_END -->',text,flags=re.S)
    if path.name.startswith('REMAINING_'):
        start=text.index('## 8. Unity 工程身份');end=text.index('## 9.',start)
        section=text[start:end].replace('8082','8088')
        section=section.replace('## 8. Unity 工程身份、占用与验证','## 8. Unity 工程身份、占用与验证\n\n2026-10-28 用户已将MyTowerGame端口调整为8088并现场核对成功；8082当前属于D:/FishTestGame，不得误操作。此当前路由优先于根规则和历史章节中的旧端口。')
        text=text[:start]+section+text[end:]
    updates[path]=text
write(assessment_path,dict(observed_at=now(),progress_completed_count=85,unfinished=assessment,blocked_preserved=blocked,available_count=len(available),chosen=successor,target=target,chosen_protected_six=six,protected_drift=[],reason='No recoverable nonblocked stage exists; lowest reference-only not_started is Swine97. PossessedWarg uncertain Down preserved without resend.'))
write(release_path,dict(observed_at=now(),transport=URL,project=project,state=state,cache_refresh=cache_refresh,errors=errors,probe=probe,protocol_history=client.history,note='Own tester already safely returned; no forced Play exit or new C# compile.'))
handoff.write_text(handoff_text,encoding='utf-8')
for path,text in updates.items():path.write_text(text,encoding='utf-8')
readme=H.parent/'README.md';readme.write_text(readme.read_text(encoding='utf-8')+'\n\n'+live+'\n',encoding='utf-8')
(H/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
progress.update(current='Swine',updated_at=now());write(H/'progress.json',progress)
prompt=f'''在 E:/MyTowerGame 接棒敌人四方向串行任务，只处理 Swine(index97)。父聊天已完成SlugQueen，当前85/108，全部完成项仍待用户美术审核。先读取 E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md、Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json、{rel(handoff)}、{rel(assessment_path)}、standing_network_recovery_authorization_20261028.json。未带完整路径的短文件均在Docs/EnemyDirectionReview/Remaining_20261024下。
唯一dispatch_token为{token}。新聊天创建时链可能仍handoff_ready，此时只读等待父线程登记；仅当state=active、owner_thread_id是本聊天、current_character=Swine且token匹配，才能生产/Unity/付费；不超时接管。目标保持E:/MyTowerGame，不转到根AGENTS旧D盘。
用户本轮明确把MyTowerGame端口调到8088，已动态确认E:/MyTowerGame、Unity2022.3.62f3c1。正确HTTP端点http://127.0.0.1:8088/mcp，复用mcp_call.py默认8088且每次动态custom-tools/instances/set/project身份核对。原unityMCP工具仍可能接8082的D:/FishTestGame，不得误操作其他工程；不占8080。桌面电脑控制仍须先弹对话确认。
Swine当前只有reference/not_started，无prepare/request/raw/staging/install/runtime，六保护及参考匹配。先核对工作区git改动、实际源图/完整prefab和Boar动画生命周期，建立增量基线，按原prompt逐关卡执行：实际审源→一方向正式生成并实际审图→另一方向→stage/布局审阅→单角色安装Verify→两轮真实Play→1-2图分次实际审阅→record/GIF归档→全帧版本绑定/并集范围审计。默认Curl生成器和AIHub既有安全参数保持；SlugQueen上下各一次HTTP200没有额外付费返修。正常新角色不用Mounted专属授权，同类TLS故障只按standing授权限次新revision恢复并保留uncertain；不重发PossessedWarg旧Down。
SlugQueen最终Up local_raster_revision_02、runtime_r02/runtime_updeath_r02各84/0共674帧，已record待用户审核。只在其自有Walk加Body三轴Euler0复位，70原绑定/事件/时序保留；不要全Build覆盖，不改其Assets或其他角色。原670帧因Up赭斑遮挡否决保留，不能当当前版。
不fork/子代理/并行角色/计时器/模型或推理覆盖。禁止配置表、Assets/ConfigJson/Gen、声音和共享C#改动；不要Git同步/提交、构建部署。仅completed_pending_user_art_review且user_approved=false。PNG抽样与GIF播放/逐帧审阅必须如实区分。原任务直接授权串行循环：本角色完成或真实阻断后总结、更新README/prompt/NEXT/progress、释放Unity，按CONTINUATION_PROTOCOL动态list_projects创建且只创建一个全新本地后继，明确创建成功后登记所有权立即停止全部工作区写入，再一次有界wait确认；不用逐角色询问。'''
prompt_path=D/('successor_prompt_'+stamp+'.txt');prompt_path.write_text(prompt+'\n',encoding='utf-8')
write(dispatch_path,dict(prepared_at=now(),parent_thread_id=parent,next_character='Swine',dispatch_token=token,handoff_file=rel(handoff),assessment_file=rel(assessment_path),unity_release_file=rel(release_path),prompt=prompt,prompt_file=rel(prompt_path),progress_sha256=sha(H/'progress.json'),handoff_sha256=sha(handoff),created=False))
assert handoff.read_text(encoding='utf-8')==handoff_text
chain.setdefault('completed_handoffs',[]).append(dict(character='SlugQueen',status=item['status'],current_stage='recorded_pending_user_art_review',owner_thread_id=parent,dispatch_token=chain['dispatch_token'],closed_at=now(),handoff_file=rel(handoff),final_evidence='Docs/EnemyDirectionReview/Remaining_20261024/SlugQueen/final_validation_20261028.json'))
chain.update(state='handoff_ready',parent_thread_id=parent,current_character='Swine',character_status_at_handoff='not_started',completed_count_snapshot=85,previous_handoff_file=chain['last_handoff_file'],last_handoff_file=rel(handoff),dispatch_token=token,progress_sha256_at_handoff=sha(H/'progress.json'),handoff_sha256=sha(handoff),unity_release_file=rel(release_path),successor_assessment=rel(assessment_path),prepared_dispatch_file=rel(dispatch_path),current_stage='handoff_ready_for_fresh_local_successor',handoff_ready_at=now(),updated_at=now(),blocked_reason=None,current_blocked=False,mcp_endpoint=URL,ownership_transfer_note='SlugQueen complete and Unity released on8088. No production operations while handoff_ready; await one fresh local Swine chat and explicit registration.')
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(state=chain['state'],next_character='Swine',token=token,handoff_file=rel(handoff),dispatch_file=rel(dispatch_path),progress=85,release=released),ensure_ascii=False))
