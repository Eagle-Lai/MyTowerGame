"""Persist Mounted closeout, release Unity, prepare exactly one Sheep successor."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,re,sys,uuid
D=Path(__file__).resolve().parent;HERE=D.parent;ROOT=HERE.parents[2];sys.path.insert(0,str(HERE))
from mcp_call import Client
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now():return datetime.now(timezone(timedelta(hours=8)))
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
chain=read(HERE/'conversation_chain.json');assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and chain['current_character']=='ScarabMounted' and chain['dispatch_token']=='scarab-to-scarabmounted-dd3da45145854f44998a5b6bdc48d12e'
intent_path=D/'successor_dispatch_intent_20261028.json';assert not intent_path.exists(),'Inspect current successor intent before retry'
p=read(HERE/'progress.json');item=next(i for i in p['items'] if i['name']=='ScarabMounted')
assert p['completed_count']==83 and item['status']=='completed_pending_user_art_review' and item['user_approved'] is False
binding=read(D/'version_binding_final_20261028.json')
assert all(sha(D/x)==s for x,s in binding['files'].items()) and all(sha(ROOT/x)==s for x,s in binding['installed_files'].items())
scope=read(D/'scope_incremental_final_20261028.json');assert scope['unexpected_incremental']==[] and scope['new_unexpected_vs_preexisting_legacy']==[] and scope['new_semantic_failures']=={}
gifs=read(D/'gif_archive_verification_20261028.json');assert gifs['total']==read(HERE.parent/'AllGIF/manifest.json')['count']==1294
incomplete=[i for i in p['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
candidates=[]
for i in incomplete:
    d=HERE/i['name'];candidates.append(dict(index=i['index'],name=i['name'],status=i['status'],requests=[x.relative_to(d).as_posix() for x in d.rglob('request.json')],raws=[x.relative_to(d).as_posix() for x in d.rglob('raw.png')],installed=(d/'installed_manifest.json').exists(),runtime=(d/'runtime_summary.json').exists(),anatomy=(d/'anatomy_plan.json').exists()))
assert all(not x['installed'] and not x['runtime'] for x in candidates)
next_item=next(i for i in incomplete if i['status']!='blocked');assert next_item['name']=='Sheep' and next_item['index']==95 and next_item['status']=='not_started'
sheep=next(x for x in candidates if x['name']=='Sheep');assert sheep['requests']==[] and sheep['raws']==[] and not sheep['anatomy']
stamp=now().strftime('%Y%m%d_%H%M%S');token='scarabmounted-to-sheep-'+uuid.uuid4().hex
assessment_path=D/('successor_assessment_'+stamp+'.json')
write(assessment_path,dict(observed_at=now().isoformat(),decision='Sheep index95 is first not-started independent candidate; PossessedWarg old Down remains blocked/uncertain and is not reissued',candidates=candidates,next_character='Sheep',reference_only=True,paid_requests_made_by_handoff=0,generator='generate_character.ps1 now defaults Transport=Curl, same endpoint/model/quality/size/n, no redirect/retry, verified TLS. Mounted Down03 succeeded with curl while Node failed before TLS. Node syntax check passed. All old outcome/intent/fingerprint guards retained. Do not use Mounted-only AuthorizedResume for Sheep.'))
c=Client();project=c.identity();errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
cache=unwrap(c.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Mounted_handoff_live_state_read"});return true;')));assert cache['success'] and cache['data']['result'] is True
state=c.resource('mcpforunity://editor/state');s=state['data'];assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']
probe=unwrap(c.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success'];observed=probe['data']['result'];assert not any(v for k,v in observed.items() if k!='scene') and observed['scene']=='Assets/Scenes/Boot.unity'
assert errors['success'] and errors['data']==[]
release_path=D/('unity_release_completed_'+stamp+'.json');write(release_path,dict(observed_at=now().isoformat(),project=project,state=state,probe=probe,errors=errors,cache_refresh=cache,protocol_history=c.history,cache_note='ForceUpdate only rebuilds actual Editor API snapshot; no flags/plugin changes; no desktop control'))
handoff_path=HERE/'conversation_handoffs'/(stamp+'_ScarabMounted_completed.md')
handoff=f'''# ScarabMounted 完成与 Sheep 唯一串行交接

- 时间：{now().isoformat()}；工程 E:/MyTowerGame / Unity2022.3.62f3c1 / unityMCP HTTP Local8082。根AGENTS的FreedomTower_1/D盘旧文案保留，不转工程、不改规则。
- ScarabMounted(index93)已安装Verify、完成最终两轮真实Play、实际PNG审阅、record和GIF归档。进度83/108，仅completed_pending_user_art_review，user_approved=false。
- Up选generation/Up/revision_04/raw.png；旧Up402、Up01/02 uncertain、被否决Up03及全部原件保留。Down初次/01/02仍uncertain，不推定未收费。用户新“继续任务”在明确阻断后触发一次新有界恢复；先用无密钥GET诊断Node TLS失败、curl TLS正常，再按authorized_resume_20261028.json只发Down03一次，HTTP200、1478274 bytes。standing两次限额原值及旧计数不改；不声称实际费用或余额。
- Down03原图保留，local_raster_revision_01仅用本图完好中腿圆根修前腿根底色污染；14 RGBA分件、透明/足尖/pivot/连接经离线实际审阅。六足、双触角、橙眼、象牙口器、斑甲壳、唯一鞍，无骑手/尾/翅。Up无眼口；Down三表情可辨。
- side_reuse_repair_r01只给Mounted自有Walk副本新增Body三轴Euler常量0，147条既有副本float曲线、PPtr、事件、时长/loop保持。源Death把Body z翻到-180，源Walk无Body轨；此修复防止同实例复用后侧身倒置。不要全Build丢失这三轨，不改Scarab或共享源动画/C#。
- 初轮r01虽168/0、691帧且视觉抽样可接受，范围审计发现Builder预览ResetForSpawn把原Head Sprite PPtr从共享Scarab atlas改为Mounted接收器数组的Normal。source_head_repair_r02只恢复原Renderer的m_Sprite，原接收器数组、PPtr动画及事件不改；Verify再次PASS。旧r01/审图/失败范围审计完整保留，最终依据r02。
- 最终runtime_r02/runtime_updeath_r02各84 PASS/0 FAIL、各346帧，总168/0和692真实帧。实际查看四方向、strip和10张时序/步态/愤怒细节板：256采样位/228不同实际帧。六足错相、腿根藏壳下、头身连接；两轮ContinuousTurns左右侧身直立，受击/致死白闪结束、死亡倾斜淡出、回收和复用恢复、暂停/恢复/2x/3x推进，抽样未见地面阴影。未播放GIF全片、未逐张审完692帧；中足遮挡密度、正背俯视程度和鞍视角留给用户美术判断。
- 最终证据在ScarabMounted/installed_manifest.json、side_reuse_repair_r01/repair.json、source_head_repair_r02/repair.json、visual_review_final_r02_20261028/review.json、record_note_utf8.txt、version_binding_final_20261028.json、final_validation_20261028.json。最终版本绑定所选raw/局部修补/暂存/安装/记录/checks/全部692 PNG/媒体及审图板，哈希漂移0。
- 相对5198文件resumed基线，前后并集22变化、20新增；生产仅当前battle prefab与Directions含目录meta，Reporter未改源码的Play时间戳单独归因。本角色语义PASS、六保护除授权battle外无漂移；增量unexpected0。全局历史291unexpected和6其他角色语义失败(MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky)原样保留，新增0，不称全局PASS。见scope_incremental_final_20261028.json及scope_ScarabMounted_20261028_r02_final.json。
- AllGIF1294项，Mounted24含12个当前r02和12个历史r01，来源/归档SHA一致；gif_archive_verification_20261028.json。不是1294个角色或用户批准数。
- 生成工具仅Docs修复：generate_character.ps1默认Transport=Curl，Node generate.mjs以curl config stdin传内存密钥，HTTPS校验、禁跨域重定向和自动retry；endpoint/model/medium/1536x1024/n1及防重/owner/指纹/intent保护不变。Down03证明curl可用，node --check通过。未来新角色可沿用默认Curl，不要复用Mounted专属AuthorizedResume；仍须先实际审参考及prompt。
- Unity刚动态重新选择MyTowerGame并核对路径/版本；Boot非Play、所有场景非dirty、编译/更新/review/录像/手动模拟空闲、编译失败false、error0。释放：{release_path.relative_to(ROOT).as_posix()}。没有桌面控制、Assets C#、表/ConfigJson/Gen/音频或其他角色修改，没有Git同步/重置/提交、构建部署。

## 下一唯一角色：Sheep(index95)

dispatch_token：`{token}`；评估：{assessment_path.relative_to(ROOT).as_posix()}。Sheep进度not_started，仅已有reference快照与source_prefab_offline，未见anatomy/prompt/request/raw/install/runtime；检查最新现场后可正常prepare。使用Cattle/Sheep源图与Goat源Controller，不凭Scarab或名称猜器官；保持原图、侧图及事件契约，按自身羊的体态设计正背/步态。不要提前在父聊天生成或安装。

PossessedWarg旧Down依旧uncertain，无可独立继续的已安装运行工作，不重发也不改分类；SabretoothTiger/Scarab/Mounted所有旧uncertain均保留。其余未完成无install/runtime。按顺序选择Sheep是独立工作，不是拿其他角色试服务。用户已经授权整队续作及逐角色自动开启唯一后继，仍禁止并行角色、fork/子代理、定时器或模型覆盖。

后继先读原执行prompt、协议、实时chain/progress及本记录，只有active且owner为自己、token/角色吻合才操作生产/Unity；handoff_ready只读。MCP优先；若确需电脑桌面控制仍先弹确认。完成或真实阻断后按协议完整落盘、更新LIVE/NEXT/README、安全释放Unity、动态list_projects创建唯一全新本地后继。创建成功后父聊天登记新owner并停止所有工作区与chain写入。
'''
handoff_path.write_text(handoff,encoding='utf-8')
live=f'2026-10-28 ScarabMounted93完成，83/108，待用户美术审核user_approved=false。Up04/Down03+局部腿根修补；自有Walk三轴复位及原侧头Sprite恢复后，最终r02两轮168/0、692真实帧；实际审四方向/strip和10板(256位/228帧)。旧r01、失败/uncertain原件完整保留。AllGIF1294，Mounted24含12当前版。5198基线并集22变化20新增，增量unexpected0，原绑定/六保护通过；全局历史291unexpected/6其他角色语义失败保留新增0。Unity安全释放Boot非Play、全部场景非dirty、空闲、编译失败false、error0。下一唯一Sheep95，仅reference、尚未prepare/request/install/runtime；默认Curl传输已成功、原防重保护保留。完整交接：{handoff_path.relative_to(ROOT).as_posix()}。所有权以实时chain为准，桌面控制仍须先对话确认。'
prompt_path=HERE/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md';prompt=prompt_path.read_text(encoding='utf-8')
prompt,count=re.subn(r'(?<=<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->).*?(?=<!-- ENEMY_SERIAL_LIVE_STATE_END -->)','\n'+live+'\n',prompt,flags=re.S);assert count==1;prompt_path.write_text(prompt,encoding='utf-8')
next_text=f'''# 下一唯一角色 Sheep(index95)

在E:/MyTowerGame继续敌人四方向续作。父聊天{chain['owner_thread_id']}已完成ScarabMounted，83/108、待用户美术审核。唯一令牌`{token}`。

## 开工与所有权

必读根AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、实时conversation_chain.json/progress.json、{handoff_path.relative_to(ROOT).as_posix()}、{assessment_path.relative_to(ROOT).as_posix()}、standing_network_recovery_authorization_20261028.json。根AGENTS旧FreedomTower_1/D盘差异已记录，保持E:/MyTowerGame，不改规则、不转工程。

只有chain.state=active、owner为本新聊天、dispatch_token严格匹配且current_character=Sheep才可操作Unity和生产。handoff_ready期间只读等待登记，不靠超时抢锁，不fork/子代理/并行角色，不改模型，不计时器。

## Sheep现场与执行

Sheep为not_started，只有reference中的Enemy_Sheep.prefab/Sheep.prefab/Sheep.png及其meta、source_structure.json和source_prefab_offline.png，尚无anatomy、generation请求、raw、staging、install或runtime。先核对现场git差异、源指纹及原图/完整prefab，再建立自己的增量基线和必要prepare，不覆盖参考或用户改动。实际源为Assets/_UIAssets/Monsters/Cattle/Sheep，battle为Assets/Prefabs/Enemy/Enemy_Sheep.prefab，源Controller为_Common/Animations/Goat/Controller.controller。所有器官、头、尾、足蹄与装备以实际源资源为准，不套前角色解剖。

generate_character.ps1默认Transport=Curl：已用Mounted Down03一次HTTP200确认此传输；Node在本机曾多次ECONNRESET/TLS前失败。密钥runtime-only、curl config stdin，不输出或写盘；HTTPS证书检查、无redirect/retry。原endpoint=gpt-image-2 images/edits、medium、1536x1024、n1及owner/指纹/输出存在保护不变。新角色正常请求不使用Mounted专属AuthorizedResume。先一方向正式生成并实际审图，再做另一方向；成功原图复用，有在途/uncertain先调查。用户standing授权覆盖同类TLS故障的有限新revision恢复，每方向最多2次追加，保留原uncertain；不得静默提高计数、鉴权/余额无界重试或拿其他角色作付费探针。无需逐角色重复确认，但电脑桌面控制仍须先弹对话确认。

按原prompt完成：实际源与生成原图审阅、透明/去底色/切片/足尖/pivot/头身尾根连接、角色步态，单角色安装Verify；检查安装初始化是否改动原Sprite/接收器绑定，源动画是否缺死亡复用reset，只在本角色自有副本最小修补，不改源/共享C#。两轮真实Play各84检查、实际四方向/时序PNG/GIF证据审阅，发现问题保留旧revision并修后重跑；绑定最终选图/安装/运行/全部帧哈希，前后文件并集范围审计、UTF8实际备注record与AllGIF归档。只能completed_pending_user_art_review、user_approved=false，不以技术PASS代替视觉验收。

已安装清单不可删后重装；分次1-2图审阅，raw/失败请求/完整帧全留。六保护除本角色battle授权外不动；全球历史291unexpected与6其他角色语义失败保留，只以本轮增量0新增判断，不能称全局PASS。禁止配置表、Assets/ConfigJson/Gen、音频、其他角色及共享C#改动，不Git pull/reset/clean/checkout/commit/push，不构建部署。

## Unity与续接

Unity2022.3.62f3c1 / unityMCP / HTTP Local8082。每次动态读custom-tools/instances、set现场MyTowerGame完整ID、核对project/info=E:/MyTowerGame及ProjectVersion。可复用mcp_call.py；不要向另一个工程操作或占8080。先读error和状态，全场景dirty、Play/编译/review/录像/manual占用检查。只有stale_status时可按Mounted/finalize_resumed_20261028.py的短反射ForceUpdate实际snapshot，不改ready/编译flags或插件。任务已授权两轮Play；不强停他人任务或覆盖未保存场景。C#若真有必要修改则遵守本工程MCP完整编译验证。

PossessedWarg旧Down仍uncertain，不重发。SabretoothTiger/Scarab/Mounted所有旧uncertain保持，专用授权不挪用。Mounted最新完成摘要与证据已绑定，不修改其Assets。

完成或真实阻断后，重新读取实时队列，写完整新交接，更新README/LIVE/NEXT/progress，确认Unity回Boot非Play、全场景非dirty、空闲、编译失败false/error检查；按CONTINUATION_PROTOCOL主动动态list_projects并创建唯一全新本地后继，不等待逐角色授权。create明确成功后登记新thread/host/token，立即停止所有工作区和chain写入，仅一次有界wait确认启动。只剩真实阻断才停止并准确报告。
'''
(HERE/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
readme=HERE.parent/'README.md';content=readme.read_text(encoding='utf-8');content=re.sub(r'本轮当前清单为 \d+ 个文件','本轮当前清单为 1294 个文件',content)
marker='<!-- ENEMY_README_LIVE_BEGIN -->';block='\n'+marker+'\n'+live+'\n<!-- ENEMY_README_LIVE_END -->\n'
if marker in content:content=re.sub(r'\n<!-- ENEMY_README_LIVE_BEGIN -->.*?<!-- ENEMY_README_LIVE_END -->\n',lambda m:block,content,flags=re.S)
else:first,rest=content.split('\n',1);content=first+'\n'+block+rest
readme.write_text(content,encoding='utf-8')
p.update(current='Sheep',status='in_progress',updated_at=now().isoformat());write(HERE/'progress.json',p)
chain.setdefault('stage_history',[]).append(dict(character='ScarabMounted',status=item['status'],current_stage='recorded_pending_user_art_review',closed_at=now().isoformat(),owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],handoff_file=handoff_path.relative_to(ROOT).as_posix(),final_evidence='Docs/EnemyDirectionReview/Remaining_20261024/ScarabMounted/final_validation_20261028.json'))
chain.update(state='handoff_ready',parent_thread_id=chain['owner_thread_id'],dispatch_token=token,current_character='Sheep',dispatch_ready_for='Sheep',character_status_at_handoff='not_started',current_stage='Sheep_reference_only_pending_owner',resume_character='Sheep',resume_stage='Inspect existing reference, prepare only missing work, then full single-character workflow',completed_count_snapshot=83,previous_handoff_file=chain['last_handoff_file'],last_handoff_file=handoff_path.relative_to(ROOT).as_posix(),unity_release_file=release_path.relative_to(ROOT).as_posix(),handoff_ready_at=now().isoformat(),updated_at=now().isoformat(),stopped_at=None,stop_reason=None,blocked_reason=None,current_blocked=False,successor_created=False,progress_sha256_at_handoff=sha(HERE/'progress.json'),ownership_transfer_note='Mounted completed and Unity released; waiting for exactly one fresh local Sheep owner registration')
intent=dict(created_at=now().isoformat(),parent_thread_id=chain['parent_thread_id'],next_character='Sheep',index=95,dispatch_token=token,handoff_file=handoff_path.relative_to(ROOT).as_posix(),assessment=assessment_path.relative_to(ROOT).as_posix(),unity_release=release_path.relative_to(ROOT).as_posix(),project_root='E:/MyTowerGame',state='handoff_ready_pending_single_create_thread',max_successors=1)
write(intent_path,intent);write(HERE/'conversation_chain.json',chain)
assert handoff_path.read_text(encoding='utf-8')==handoff and (HERE/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8')==next_text
print(json.dumps(intent,ensure_ascii=False))
