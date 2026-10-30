"""Persist Rat completion and safely release the serial production slot."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,os,sys,hashlib,uuid
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
chain=read(H/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='Rat' and chain['dispatch_token']=='ram-to-rat-20261026-7f3d9c2a'
p=read(H/'progress.json');rat=next(i for i in p['items'] if i['name']=='Rat')
assert rat['status']=='completed_pending_user_art_review' and rat['user_approved'] is False
assert p['completed_count']==75
next_item=next(i for i in p['items'] if i['status'] not in ['completed_pending_user_art_review','blocked'])
assert next_item['name']=='RatKing'
scope=read(D/'scope_incremental_20261026.json');final=read(D/'final_validation_20261026.json');runtime=read(D/'runtime_summary.json')
assert not scope['unexpected_incremental'] and scope['prefab_semantics']['pass'] and not scope['installed_asset_drift']
assert runtime['passes']==168 and not runtime['failures']
manifest=read(D/'installed_manifest.json')
assert all(sha(ROOT/x['path'])==x['after'] for x in manifest['changes'])
def unwrap(r):return r.get('structuredContent') or json.loads(r['content'][0]['text'])
c=Client();project=c.identity();state=c.resource('mcpforunity://editor/state')
probe=unwrap(c.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'}))['data']['result']
assert not any(v for k,v in probe.items() if k!='scene') and probe['scene']=='Assets/Scenes/Boot.unity'
assert state['data']['advice']['ready_for_tools'] and not state['data']['compilation']['is_domain_reload_pending']
now=datetime.now(timezone(timedelta(hours=8)));stamp=now.strftime('%Y%m%d_%H%M%S')
release=D/('unity_release_'+stamp+'.json');write(release,dict(observed_at=now.isoformat(),project=project,state=state,probe=probe,protocol_history=c.history))
handoff=H/'conversation_handoffs'/(stamp+'_Rat.md');assert not handoff.exists()
token='rat-to-ratking-'+uuid.uuid4().hex
live=f'''2026-10-26 串行续接更新：75/108。Rat 已完成原始生成图复用、离线局部返修、单角色安装、两轮真实 Play（runtime_r01 / runtime_updeath_r01，各 84 PASS / 0 FAIL，共 680 帧）及实际 PNG 时序审阅，状态 completed_pending_user_art_review、user_approved=false。Rat 安装前增量基线已保存；语义通过、安装资源无 drift、unexpected_incremental=[]；Reporter 的 Play 时间戳更新单独归因。全局历史 scope 仍有 291 unexpected，与既有分类比较新增 0，未宣称全局 PASS。Unity 已恢复非 Play、非 dirty 的 Boot，错误日志 0、scriptCompilationFailed=false。下一唯一角色 RatKing；PossessedWarg 保持 blocked，不重复付费请求。详见 conversation_handoffs/{handoff.name}。实时事实以 progress.json、角色证据与链所有权为准。'''
text=f'''# Rat 串行交接总结

时间：{now.isoformat()}。工程 `E:/MyTowerGame`，Unity `2022.3.62f3c1`。本聊天仅修改 Rat 的生产呈现。

## 结果与证据

- 进度 `75/108`。Rat 为 `completed_pending_user_art_review`，`user_approved=false`。本轮新安装并新执行两轮真实 Play：`runtime_r01` 与 `runtime_updeath_r01` 各 84 PASS / 0 FAIL、340 帧，合计 168 PASS / 0 FAIL、680 帧。
- 两次已有 Up/Down AIHub 原始生成结果均复用，没有重复付费请求。生成原件、request/result 保留；本轮离线调整由 `Rat/refine_offline.py`、`retouch_heels.py`、`raster_revision_01..04` 和 `offline_revision_01_before..05_before` 记录。最终以后续 `offline_review_20261026.json` 内的 staged SHA256 为准；`parts_final_retouch.png` 是真实最终切片板，`parts_clean.png` 属 pack 阶段的修片前板，不作为最终切片证据。
- Up 后脑无脸、颈帽被头片遮住；前足仍在 rig 中并由背身遮挡，后足为连续后跟，不画正面趾沟。Down 四只短足连接在身体内，头、身体与条纹尾保留 Rat 身份。局部修片未写入生成原图，也未改共享 C#。
- 实际查看了两轮 10 张 PNG 时序板、`runtime_r01/four_directions.png`、`runtime_visual_strip.png`，覆盖四向步态/周期、连续转向、攻击与愤怒头、受击白闪、Down 与 Up 死亡淡出回收、同实例复用、暂停恢复及 2x/3x。没有播放 GIF 全片；审阅方式和限制明确记录在 `record_note_utf8.txt` 与 `visual_review_serial_20261026/review.json`。
- 曾从含血条的整幅截图边界怀疑方向尺寸过小；进一步分离血条并核对 Builder 无额外缩放后，保留现有正背投影，未安装第二个版本。所有运行证据对应 `installed_manifest.json`，无 repair manifest、无运行后生产变更。
- prefab SHA256：`{scope['prefab_semantics']['current_sha256']}`。原图、源 prefab 及 GUID 未变；`installed_verify.txt` 的依赖、原横向曲线/事件/时长/循环、重复 clone、引用及 YooAsset collector 检查均 PASS。没有构建发布包或设备验证。
- 安装前保存 `incremental_before_20261026.json`，含 5038 个文件指纹。既有文件增量只有 `Enemy_Rat.prefab` 与 `Assets/StreamingAssets/build_info`；后者由未修改的 ReporterEditor 在 Play 写入，单独列为编辑器副作用。新增生产文件均在 Rat Directions 内；`scope_incremental_20261026.json` 中语义 PASS、安装 drift=[]、unexpected_incremental=[]。
- 全局 `scope_Rat_20261026_final.json` 仍 `pass=false`、291 个历史 unexpected，与 PirateBoar 已分类历史相比新增 0。未重置基线、未宣称全局 PASS。
- Docs 共享 helper `pack_character.py` 增加了可选 warm-foreground mask，仅 Rat 的 `art_selection.json` 启用，以保留死亡舌头；其他角色默认行为未变。`finalize_serial_character.py` 补充严格匹配 Reporter 的已知时间戳副作用归因，其余非目标增量仍拒绝。没有 Assets/Packages C# 修改，没有配置表或导出数据修改。
- `final_validation_20261026.json` 记录错误日志 0、scriptCompilationFailed=false、实际工程身份及 runtime hash。AllGIF 已归档至 1138 项，包含 Rat 两轮 12 个 GIF，旧媒体保留。

## Unity 交还

`{release.name}` 显示 Boot、非 Play、非 dirty、无编译/更新/域重载/评级/审阅/手动模拟占用，ready_for_tools=true。通过现有 `mcp_call.py` 的 HTTP Local 8082 动态发现并选择实例后核对 E:/MyTowerGame 与版本。此前记录的 Codex 原生 8083 握手异常未更改；本轮成功验证使用 8082，不能把端口监听当验证。

## 唯一后继

实时下一独立项是 RatKing（index 87，not_started）。progress.current 仍可能指向 blocked 的 PossessedWarg，这是 record 的正常行为；不要盲用 current。PossessedWarg 的 Down 原付费请求结果不明，保留阻断，不重发、不删除。

接棒令牌：`{token}`。按 CONTINUATION_PROTOCOL 创建唯一全新本地聊天；新聊天等待链 active 且 owner/token/角色一致后才能操作生产资源或 Unity。旧聊天在所有权转移后停止工程修改，不创建子代理或并发角色。
'''
handoff.write_text(text,encoding='utf-8')
prompt=H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md';source=prompt.read_text(encoding='utf-8')
start='<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->';end='<!-- ENEMY_SERIAL_LIVE_STATE_END -->'
head,rest=source.split(start,1);_,tail=rest.split(end,1);prompt.write_text(head+start+chr(10)+live+chr(10)+end+tail,encoding='utf-8')
readme=H.parent/'README.md';source=readme.read_text(encoding='utf-8').replace('本轮当前清单为 1126 个文件','本轮当前清单为 1138 个文件')
readme.write_text(source+chr(10)+live+chr(10),encoding='utf-8')
next_text=f'''# 当前唯一敌人任务：RatKing

工程 `E:/MyTowerGame`，Unity `2022.3.62f3c1`，unityMCP / HTTP Local `http://127.0.0.1:8082/mcp`。根 AGENTS.md 的 FreedomTower_1/D: 标题仍是旧信息，不切换项目，不擅自改 AGENTS。

## 开工与唯一所有权

先读根 AGENTS.md、ProjectSettings/ProjectVersion.txt、本目录 REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、conversation_chain.json、实时 progress.json、`conversation_handoffs/{handoff.name}`、上级 README.md 与 PREFAB_CHANGES_SUMMARY_20261026.md，并查看 RatKing 已有文件和未提交改动。

唯一角色 RatKing，接棒令牌 `{token}`。只有链 state=active、owner_thread_id 等于运行时 CODEX_THREAD_ID、current_character=RatKing 且 token 一致才允许 Unity/生产操作；handoff_ready 时只读等待，不超时接管，不创建子代理或并发角色。

## 本次阶段

最新已完成 75/108，Rat 两轮共 168 PASS / 0 FAIL、680 帧，内部视觉审阅完成但未获用户批准。RatKing 为 index 87、not_started；先核对当前实际阶段，若已有生成或安装结果则恢复，不重复 prepare、付费请求或 install。

只对 RatKing 走完整单角色流程：参考/解剖 → 生成原图实际审阅 → 分件与布局视觉门槛 → 安装前增量指纹与六个保护文件核对 → 单角色安装及 Verify → 普通死亡和 Up 死亡两轮真实 Play（每轮84项）→ 实际媒体审阅及必要返修 → record、GIF归档、总结与唯一后继接棒。安装前基线必须在生产修改前保存，不能借用其他角色的基线。

本轮实际可用的是已有 `mcp_call.py` 8082 通道；Client.identity() 会动态读取 custom-tools/instances、显式选择当前完整实例并核对路径/版本。此前原生 Codex 配置 8083 握手失败，没有更改配置或端口；按工程规则复用正确通道。每次重连/域重载后重做身份检查；进入Play前检查占用。Rat 最后交还 Boot、非Play、非dirty，具体见上述总结与 release证据，开工仍重新核对现场。

## 历史范围与阻断

全局scope的291项既有差异未消除，不宣称全局PASS。按本角色安装前快照与已有历史分类核对增量。finalize_serial_character.py 已严格记录未改 ReporterEditor 在 Play 写 build_info 的时间戳副作用，其余非目标增量仍拒绝。记录原始生成/修片/生产/runtime哈希，视觉通过也只能标 completed_pending_user_art_review，user_approved=false。

PossessedWarg index79仍blocked：Down原付费请求结果不明。不得重发、删原请求或解除阻断。progress.current 可能仍指向该项；实际可独立续接RatKing，不重复做Rat。

## 完成后的自动接棒

完成RatKing完整验收或记录真实阻断并交还Unity后，重读items选择唯一下一项；写时间戳总结、更新原prompt实时块、本文件和README，再按协议释放到handoff_ready。list_projects发现项目ID后只创建一个全新local项目聊天，不fork、不指定模型、不并发。登记返回的真实owner和token，做一次有界wait确认后停止本聊天工程修改。

保留已有dirty工作，不pull/reset/clean/commit/push；不改配置表或Assets/ConfigJson、Assets/Gen，不恢复声音系统；图片分次审阅、原件留盘。
'''
(H/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
chain.update(state='handoff_ready',parent_thread_id=os.environ['CODEX_THREAD_ID'],current_character='RatKing',dispatch_token=token,character_status_at_handoff='not_started',completed_count_snapshot=75,last_handoff_file=handoff.relative_to(ROOT).as_posix(),progress_sha256_at_handoff=sha(H/'progress.json'),handoff_ready_at=now.isoformat(),unity_release_file=release.relative_to(ROOT).as_posix())
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(handoff=handoff.relative_to(ROOT).as_posix(),state=chain['state'],next=chain['current_character'],dispatch_token=token,parent=chain['parent_thread_id'],completed=75,unity=probe),ensure_ascii=False))
