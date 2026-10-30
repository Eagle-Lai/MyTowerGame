"""Release completed RatKing and prepare exactly one fresh RedScorpion successor."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import os,json,sys,hashlib,uuid
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2];sys.path.insert(0,str(H))
from mcp_call import Client
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
chain=read(H/'conversation_chain.json');assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and chain['current_character']=='RatKing' and chain['dispatch_token']=='rat-to-ratking-5222dbfeb5d146d7ad666975e4e8d90e'
p=read(H/'progress.json');item=next(i for i in p['items'] if i['name']=='RatKing')
assert item['status']=='completed_pending_user_art_review' and item['user_approved'] is False and p['completed_count']==76
unfinished=[i for i in p['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved','blocked']]
started=[i for i in unfinished if i['status']!='not_started'];next_item=min(started or unfinished,key=lambda i:i['index']);assert next_item['name']=='RedScorpion' and next_item['status']=='not_started'
s=read(D/'scope_incremental_20261026.json');assert s['prefab_semantics']['pass'] and not s['unexpected_incremental'] and not s['unexpected_added'] and not s['installed_asset_drift']
runtime=read(D/'runtime_summary.json');assert runtime['passes']==168 and runtime['failures']==0
manifest=read(D/'repair_tail_r06/manifest.json');assert all(sha(ROOT/x['path'])==x['after'] for x in manifest['changes'])
def unwrap(r):return r.get('structuredContent') or json.loads(r['content'][0]['text'])
c=Client();project=c.identity();state=c.resource('mcpforunity://editor/state')
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));assert errors['data']==[]
probe=unwrap(c.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'}))['data']['result']
assert not any(v for k,v in probe.items() if k!='scene') and probe['scene']=='Assets/Scenes/Boot.unity',probe
assert state['data']['advice']['ready_for_tools'] and not state['data']['compilation']['is_domain_reload_pending']
now=datetime.now(timezone(timedelta(hours=8)));stamp=now.strftime('%Y%m%d_%H%M%S')
release=D/('unity_release_'+stamp+'.json');write(release,dict(observed_at=now.isoformat(),project=project,state=state,probe=probe,errors=errors,protocol_history=c.history))
handoff=H/'conversation_handoffs'/(stamp+'_RatKing.md');assert not handoff.exists();token='ratking-to-redscorpion-'+uuid.uuid4().hex
live=f'''2026-10-26 串行续接更新：76/108。RatKing 最终 repair_tail_r06，runtime_final_r03 / runtime_final_updeath_r03 各84 PASS / 0 FAIL，共680张真实帧；实际审阅10张时序板、256个采样位/230张不同实际帧及四方向和strip。初版体量过小、比例版尾尖穿过血条均已返修，旧证据保留。状态 completed_pending_user_art_review，user_approved=false。安装前5058个文件指纹；本角色语义通过、安装无drift、unexpected_incremental=[]、unexpected_added=[]，Reporter的Play时间戳单独归因。全局291项历史unexpected，新增0，未称全局PASS。Unity交还Boot、非Play、非dirty、空闲、错误0。AllGIF实时1174项，RatKing共36项含12个当前版本。下一唯一角色RedScorpion(index88)，PossessedWarg保持blocked且不重发原Down请求。详见conversation_handoffs/{handoff.name}，实时事实以progress与链所有权为准。'''
handoff.write_text(f'''# RatKing 串行交接总结

时间：{now.isoformat()}。目标 `E:/MyTowerGame`，Unity `2022.3.62f3c1`。本聊天仅负责 RatKing，未启动子代理或并发角色。

## 结果与版本

- 实时进度76/108，31项not_started，PossessedWarg一项blocked。RatKing是completed_pending_user_art_review，user_approved=false；未替用户批准。
- 生产仅修改Enemy_RatKing.prefab与本角色Directions；原prefab根、GUID、HP、血条、碰撞器、锚点及业务语义检查通过。最终prefab SHA256为 `{s['prefab_semantics']['current_sha256']}`。
- 使用现有AIHub流程，仅首次Up、Down各一次gpt-image-2编辑请求(quality=medium,n=1,size=1536x1024)，均HTTP200，原始request/result/raw保留。没有重复付费请求。Prompt见RatKing/generation/Up/prompt.txt与Down/prompt.txt，原始返回不被本地修片覆盖。
- 实际查看源图集和完整源prefab。保留橄榄棕背毛、赭斑、金冠及正面黑菱形、单侧银耳环、四足与浅金环纹尾。raster_revision_01..04记录背耳/后跟、去除躯干重复腿、背冠和边缘返修。parts_clean是早期未修片板；parts_final_retouch是最终切片板。不要重跑stage覆盖最终切片。
- 初始installed_manifest.json与runtime_r01/runtime_updeath_r01各84 PASS，但画面体量偏小，已内部否决；678帧保留，未宣称全部视觉审完。repair_proportions_r05及对应两轮各84 PASS、669帧因Down尾尖穿过血条再次返修，旧版保留。最终采用repair_tail_r06/manifest.json，仅调整尾部至后右侧，未移动血条。
- 最终两轮runtime_final_r03 / runtime_final_updeath_r03各84 PASS/0 FAIL、各340帧，共168 PASS/0 FAIL、680帧。两轮记录SHA256见runtime_summary.json和version_binding_final_20261026.json，后者绑定最终安装、原始生成、切片及所有680张实际PNG哈希。
- 已实际查看最终四方向图、runtime_visual_strip、两轮共10张时序板(256采样位、230不同实际帧)，覆盖四向步态、上下周期、连续转向、攻击/愤怒头、受击白闪、Down与Up死亡倾倒/收缩/淡出、回收复用、暂停恢复和2x/3x。后脑无脸，尾根与足根相接，最终尾尖避开血条，抽样未见地面阴影。审阅方法为时序PNG抽样；未播放GIF全片，未逐张审全部680帧。真实UTF-8观察见record_note_utf8.txt，版本和采样限制见visual_review_final_serial_20261026/review.json与sources.json。
- Builder/Verify包含原侧向曲线/事件/时长/循环、依赖、重复clone及YooAsset收集覆盖PASS；不表示构建发布包或设备测试。本聊天没有修改Assets/Packages C#、共享系统、配置表、ConfigJson或Gen，也没有恢复声音。

## 范围归因与Unity交还

- 安装前incremental_before_20261026.json保存5058文件指纹及六个保护文件。现有文件增量只有本角色prefab与Assets/StreamingAssets/build_info；ReporterEditor未改且其Play写时间戳严格单独归因。新增20个生产文件全部位于本角色Directions(含目录meta)。unexpected_incremental=[]、unexpected_added=[]、installed_asset_drift=[]，本角色语义PASS。
- 全局scope_RatKing_20261026_tail_final.json仍pass=false，291项既有unexpected，与PirateBoar已分类历史相比新增0；没有重置基线或宣称全局PASS。final_validation_20261026.json记录错误0、scriptCompilationFailed=false。
- `{release.name}`重新动态发现8082实例、核对E:/MyTowerGame与版本，确认Boot、非Play、所有场景非dirty、无编译/更新/域重载/评级/录像/审阅/手动模拟占用。当前可用通道是mcp_call.py HTTP Local8082；此前原生Codex8083握手问题未改配置，不能使用CatchFish8080替代。
- AllGIF清单1174项，RatKing36个GIF(含两轮旧版与最终版)，12个标当前审核版本；历史及原件保留。

## 唯一后继

实时下一项RedScorpion(index88,not_started)。progress.current仍可能指PossessedWarg；它的Down原付费请求结果不明，保持blocked，不重发、不删原请求、不自动解除。

接棒token：`{token}`。先保持handoff_ready，创建唯一全新local聊天，登记返回真实threadId/hostId后改active；新聊天只有owner、角色与token完全匹配才能操作Unity/生产资源，不超时抢锁。旧聊天转交后只读，做一次有界wait确认并停止工程修改。
''',encoding='utf-8')
prompt=H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md';source=prompt.read_text(encoding='utf-8');begin='<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->';end='<!-- ENEMY_SERIAL_LIVE_STATE_END -->';head,rest=source.split(begin,1);_,tail=rest.split(end,1);prompt.write_text(head+begin+'\n'+live+'\n'+end+tail,encoding='utf-8')
readme=H.parent/'README.md';source=readme.read_text(encoding='utf-8').replace('本轮当前清单为 1138 个文件','本轮当前清单为 1174 个文件');readme.write_text(source+'\n'+live+'\n',encoding='utf-8')
next_text=f'''# 当前唯一敌人任务：RedScorpion

目标E:/MyTowerGame，Unity2022.3.62f3c1，unityMCP HTTP Local8082。AGENTS的FreedomTower_1/D:是旧信息；本任务不切换工程、不改AGENTS。

先读根AGENTS、ProjectSettings/ProjectVersion.txt、本目录REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、本文件、conversation_chain.json、实时progress.json、conversation_handoffs/{handoff.name}及上级README/PREFAB_CHANGES_SUMMARY。检查未提交改动、RedScorpion已有参考/生成/安装/运行证据，已有阶段先恢复，不重复prepare/付费请求/install。

唯一角色RedScorpion(index88，交接时not_started)，token为`{token}`。只有state=active、owner_thread_id等于本聊天运行时CODEX_THREAD_ID、current_character=RedScorpion、token完全匹配后才允许Unity/生产操作；handoff_ready只读等待，不超时接管。禁止子代理、fork、并发角色或重复建RedScorpion聊天。

RatKing已完整完成，76/108，状态completed_pending_user_art_review/user_approved=false。最终repair_tail_r06和runtime_final_r03/runtime_final_updeath_r03各84 PASS/0 FAIL、共680帧，实际查看最终10张时序板230不同采样帧，记录及GIF归档完成。勿重做RatKing。旧运行因体量和尾尖血条相交问题已返修，全部保留。全局scope仍291历史unexpected；本角色unexpected增量为空，不宣称全局PASS。

按完整prompt对RedScorpion走参考/解剖、原图实际审阅、分件/透明/布局视觉门槛、安装前本角色增量基线及六个保护指纹、单角色安装Verify、普通死亡与Up死亡各84项真实Play、足够真实媒体时序审阅与必要返修、UTF-8观察、record及GIF归档。RedScorpion名称不代表红色，源资源为金黄/赭斑，六条步足、两钳与高拱分节蝎尾；准确外观仍以实际原图和完整源参考为准，不能盲套BlueScorpion尾方案。

开工重新通过mcp_call.py Client.identity动态发现完整实例并核对E:/MyTowerGame及版本，检查编译、Play、脏场景、评级/录像/审阅/手动模拟占用。RatKing交还Boot、非Play、非dirty、空闲、错误0，见总结及release证据；不能以历史状态替代本次检查。可用8082通道不改配置，不能使用CatchFish8080或硬编码旧实例。最终仍仅能标待用户美术验收。

PossessedWarg index79保持blocked，Down原付费结果不明，不重发、不删原request、不自行解除。progress.current可能仍指它；实际独立续接RedScorpion。保留全部dirty，不pull/reset/clean/commit/push；不改配置表、Assets/ConfigJson或Assets/Gen，维持无声版。图片原件留盘、分次审阅，不一次加载历史图片。

完整完成或记录真实阻断并安全交还Unity后，重读items，写时间戳总结，更新README、原prompt实时块及NEXT_ENEMY_TASK；按协议list_projects发现项目ID，只创建唯一全新local后继，登记真实所有权，做一次有界wait后停止本聊天修改。串行循环已获用户授权，不等待逐角色重复确认。
'''
(H/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
dispatch=f'''在E:/MyTowerGame继续敌人四方向串行续作，本聊天只负责RedScorpion。接棒token为{token}，parent_thread_id为{os.environ['CODEX_THREAD_ID']}。先读取根AGENTS.md、ProjectSettings/ProjectVersion.txt，以及Docs/EnemyDirectionReview/Remaining_20261024/下的REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json、conversation_handoffs/{handoff.name}，再检查未提交改动和RedScorpion已有材料。根AGENTS的FreedomTower_1/D:是旧信息；明确目标E:/MyTowerGame/Unity2022.3.62f3c1，不切项目、不改AGENTS。

创建有异步交接窗口：只有state=active、owner_thread_id等于本聊天运行时CODEX_THREAD_ID、current_character=RedScorpion且token完全匹配后才允许Unity/生产资源操作；handoff_ready只读等待，不超时抢锁。旧聊天会登记创建工具返回的真实threadId。禁止子代理、fork、并发角色或再建重复RedScorpion聊天。

RatKing已完成，76/108，completed_pending_user_art_review，user_approved=false。最终repair_tail_r06；runtime_final_r03/runtime_final_updeath_r03各84 PASS/0 FAIL、共680帧；真实审阅10张时序板230张不同实际采样帧、四方向和strip，未播放GIF全片。初版和比例版曾因体量偏小/尾尖穿血条返修，全部证据保留。勿重做RatKing。RedScorpion index88交接时not_started，仍核对实际阶段；已有生成/安装优先恢复，不重复付费或删防重证据。PossessedWarg index79保持blocked，Down原付费结果不明，不重发、不删原请求、不自行解除；progress.current可能仍指它，本聊天继续RedScorpion。

按完整执行prompt完成本角色参考及解剖、生成原图实际审阅、分件/透明/布局实际门槛、安装前本角色增量快照及六保护指纹、单角色安装Verify、普通死亡与Up死亡两轮真实Play各84项、足够真实媒体时序审阅和必要返修、UTF-8观察、record及GIF归档。RedScorpion原设是金黄赭斑、六步足双钳高拱分节尾，名称不要求红色；仍以实际原始图集和源prefab为准。视觉问题即使程序PASS也返修，新revision留旧证据；仅标实现完成待用户美术验收。

使用现有mcp_call.py的HTTP Local8082，Client.identity动态发现完整实例并核对工程版本；原生Codex8083握手故障未改配置，不用CatchFish8080。开工重查身份与占用，上一角色release证据为Boot、非Play、非dirty、空闲、无编译错误。全局scope仍有291既有unexpected，不能声称全局PASS。创建自己的安装前增量快照并比较历史分类；finalize_serial_character.py已严格单独归因未改ReporterEditor在Play写build_info的时间戳副作用，其他非目标增量仍拒绝。新增文件也要与本角色快照比较。保留dirty，不pull/reset/clean/commit/push，不改配置表/ConfigJson/Gen，维持无声版。图片原件留盘、分次审阅，避免重复载入历史图片。

本角色完整完成或记录真实阻断并安全交还Unity后，重读items，写时间戳总结、更新README/原prompt实时块/NEXT_ENEMY_TASK，按CONTINUATION_PROTOCOL主动创建唯一全新本地后继聊天并登记真实所有权，做一次有界wait确认后停止本聊天修改，循环至全部有效完成或仅剩真实阻断。该串行循环是现有用户授权，不等待逐角色确认。'''
write(D/'successor_create_request.json',dict(target=dict(type='project',projectId='935c594c-f414-48e0-bd08-ed8ba342f7fd',environment=dict(type='local')),prompt=dispatch,title='RedScorpion 四方向串行续作'))
chain.update(state='handoff_ready',parent_thread_id=os.environ['CODEX_THREAD_ID'],current_character='RedScorpion',dispatch_token=token,character_status_at_handoff='not_started',completed_count_snapshot=76,last_handoff_file=handoff.relative_to(ROOT).as_posix(),progress_sha256_at_handoff=sha(H/'progress.json'),handoff_ready_at=now.isoformat(),unity_release_file=release.relative_to(ROOT).as_posix())
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(state=chain['state'],next='RedScorpion',token=token,handoff=handoff.relative_to(ROOT).as_posix(),release=release.relative_to(ROOT).as_posix(),probe=probe,dispatch_file=str(D/'successor_create_request.json')),ensure_ascii=False))
