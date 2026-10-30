from serial_common import *
import uuid
chain=owner();p=read(H/'progress.json');item=next(i for i in p['items'] if i['name']==NAME)
assert item['status']=='completed_pending_user_art_review' and item['user_approved'] is False
assert p['completed_count']==77
pending=[i for i in p['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved','blocked']]
assert not [i for i in pending if i['status']!='not_started'],pending
next_item=min(pending,key=lambda i:i['index']);assert next_item['name']=='Rooster' and next_item['index']==89
report=available(Client());assert report['errors']['data']==[]
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
release=D/('unity_release_'+stamp+'.json');write(release,report)
handoff=H/'conversation_handoffs'/(stamp+'_RedScorpion.md')
token='redscorpion-to-rooster-'+uuid.uuid4().hex
scope=read(D/'scope_incremental_20261026.json');assert scope['unexpected_incremental']==[] and scope['unexpected_added']==[] and scope['installed_asset_drift']==[]
prefab_sha=sha(ROOT/'Assets/Prefabs/Enemy/Enemy_RedScorpion.prefab')
live=f'''2026-10-26 串行续接更新：77/108。RedScorpion最终installed_manifest.json，raster_revision_06分件；runtime_r01/runtime_updeath_r01各84 PASS/0 FAIL，共684张真实帧。实际查看10张整身时序板、256个采样位/225张不同实际帧，另审四方向、strip和Up攻击连接放大图；未播放GIF全片。两张原始整套生成和一张定向躯干修复图均已审，局部补片过软/重绘过平的离线版本被否决并保留。状态completed_pending_user_art_review，user_approved=false。安装前5078文件及六保护指纹；本角色语义通过、安装无drift、unexpected_incremental=[]、unexpected_added=[]，Reporter的Play时间戳单独归因。全局291项历史unexpected，新增0，未称全局PASS。Unity交还Boot、非Play、非dirty、空闲、错误0。AllGIF实时1186项，RedScorpion12项均当前审核版本。下一唯一角色Rooster(index89)，PossessedWarg保持blocked且不重发原Down请求。详见conversation_handoffs/{handoff.name}，实时事实以progress与链所有权为准。'''
handoff.write_text(f'''# RedScorpion 串行交接总结

时间：{now()}。目标E:/MyTowerGame，Unity2022.3.62f3c1。本聊天仅负责RedScorpion，无子代理、fork或并发角色。

## 最终结果与美术版本

- 实时77/108，30项not_started、PossessedWarg一项blocked。RedScorpion为completed_pending_user_art_review，user_approved=false，未替用户批准。RatKing未重做。
- 生产仅修改Enemy_RedScorpion.prefab与本角色Directions。最终prefab SHA256：{prefab_sha}。原prefab根、GUID、HP、血条、碰撞器、锚点及业务语义PASS，源prefab/原图及其meta不变。
- 使用imagegen原则及用户明确授权的现有AIHub入口。最初Up、Down各一次gpt-image-2编辑请求，另为躯干发出一次定向修复请求到Up/revision_01；全部HTTP200、quality=medium、n=1、size=1536x1024。未盲目重试结果不明请求，全部prompt/request/result/raw留盘。最终prompt见generation/Up/prompt.txt、generation/Down/prompt.txt、generation/Up/revision_01/prompt.txt。密钥仅进程内使用。
- 原设为金黄赭斑、六步足、双钳、象牙眉角/口钳、三片带轴向尖刺的圆拱背甲及高拱金黄分节尾。已实际查看原图集和完整源prefab。名字未导致红色重涂，未盲套BlueScorpion尾方案。
- 默认stage曾因Down蝎尾超出名义行边界而安全拒绝，art_selection采用实际审过的显式矩形。raster_revision_01去掉Up后脑额外侧刺与散点；r02局部躯干填色过软、r03本地重绘过平被内部视觉否决，未安装。r04选择真实定向生成的两个躯干片；r05按原设加宽、对齐足根；r06仅清理Down尾拱内的小块背景残留。历史版本及原始付费返回全部保留。
- 最终安装installed_manifest.json，最终暂存staged_art。不要重新stage或重跑离线修片脚本覆盖当前成果；默认pack不支持本角色的定向躯干per-part来源，完整选择与处理见art_selection.json及各修片脚本/retouch_record。

## 实际验证与视觉审阅

- Builder/Verify通过：原侧向float/PPtr曲线、事件、时长/loop、重复clone与root/HP契约、无Missing脚本、依赖及现有YooAsset收集覆盖。未构建发布包或做设备测试。
- runtime_r01为84 PASS/0 FAIL、343帧，records SHA256=395481E50EE12F9E332FC2F6C46C7C859293E2AAFF7AEABF5B82313B0793E420；runtime_updeath_r01为84 PASS/0 FAIL、341帧，records SHA256=42C0014B316773623A9A03B7137CF4F0F10143BBFD9C97127BAD46C3DD653D7D。共168 PASS/0 FAIL、684张实际Unity PNG，严格递增真实帧号。安装、原始生成、最终切片、全部684帧绑定见version_binding_final_20261026.json。
- 实际查看四方向、runtime_visual_strip、visual_review_serial_full_20261026下全部10张时序板(256采样位、225张不同实际帧)、Up攻击连接放大图。覆盖四向步态、上下周期、连续转向、攻击/愤怒头、受击白闪、普通Down及Up死亡倾倒/收缩/淡出、回收复用、暂停恢复与2x/3x。抽样中后脑无脸、尾/足/钳根连接，尾尖完整且避开血条，未见地面阴影。
- 审阅方式是时序PNG抽样；未播放GIF全片、未逐张审全部684帧。通用review_actual_frames.py的固定裁剪会截掉本角色高尾，所以新增本角色review_full_frames.py保留整身与血条；旧通用板仍保留，不把其裁剪当实际帧裁切。真实UTF-8观察见record_note_utf8.txt和visual_review_serial_full_20261026/review.json。

## 范围审计与Unity交还

- 安装前incremental_before_20261026.json保存5078文件指纹及六保护文件。现有文件增量只有本角色prefab及Assets/StreamingAssets/build_info；后者由未修改ReporterEditor在Play写入时间戳，严格单独归因。新增20个生产文件均位于本角色Directions(含目录meta)。unexpected_incremental=[]、unexpected_added=[]、installed_asset_drift=[]，语义PASS。
- 全局scope_RedScorpion_20261026_initial.json仍pass=false，291项既有unexpected，与PirateBoar历史分类相比新增0；未重置基线或宣称全局PASS。
- final_validation_20261026.json记录编译失败false、错误0。本聊天未修改Assets/Packages C#，未改配置表/ConfigJson/Gen、共享系统或声音功能。所有其他dirty保留，无pull/reset/clean/commit/push。
- {release.name}通过现有mcp_call.py HTTP Local8082重新动态发现完整实例、核对E:/MyTowerGame与版本；Boot、非Play、所有场景非dirty、无编译/域重载/更新、无评级/录像/审阅/手动模拟占用，错误0。8083原生握手问题未改配置，不用CatchFish8080。
- AllGIF清单1186项，本角色12项均当前审核版本；原GIF保留。

## 唯一后继

重新读取items后选择Rooster(index89,not_started)，其目录当前只有原始reference材料，无生成或安装。仍须后继实时核对，不重复已有阶段。PossessedWarg保持blocked，Down原付费结果不明，不重发、不删request、不自行解除，progress.current可能仍指它。

token={token}，parent_thread_id={os.environ['CODEX_THREAD_ID']}。先进入handoff_ready，创建唯一全新local聊天，登记真实threadId/hostId后active。新聊天只有owner、角色及token完全匹配可操作Unity/生产，handoff_ready只读等待，不超时接管。转交成功后旧聊天只读且只做一次有界wait。
''',encoding='utf-8')
prompt=H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md';s=prompt.read_text(encoding='utf-8');begin='<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->';end='<!-- ENEMY_SERIAL_LIVE_STATE_END -->';head,rest=s.split(begin,1);_,tail=rest.split(end,1);prompt.write_text(head+begin+'\n'+live+'\n'+end+tail,encoding='utf-8')
readme=H.parent/'README.md';s=readme.read_text(encoding='utf-8').replace('本轮当前清单为 1174 个文件','本轮当前清单为 1186 个文件');readme.write_text(s+'\n'+live+'\n',encoding='utf-8')
dispatch=f'''在E:/MyTowerGame继续敌人四方向串行续作，本聊天只负责Rooster(index89)。接棒token为{token}，parent_thread_id为{os.environ['CODEX_THREAD_ID']}。

先读取根AGENTS.md、ProjectSettings/ProjectVersion.txt，Docs/EnemyDirectionReview/Remaining_20261024/下的REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json、conversation_handoffs/{handoff.name}，以及上级README/PREFAB_CHANGES_SUMMARY。检查未提交改动与Rooster已有材料，优先恢复已有阶段，禁止重复prepare/付费生成/install。根AGENTS的FreedomTower_1/D:是旧信息，目标明确E:/MyTowerGame/Unity2022.3.62f3c1，不切工程、不改AGENTS。

创建有异步交接窗口：只有state=active、owner_thread_id等于本聊天运行时CODEX_THREAD_ID、current_character=Rooster且token完全匹配后，才允许Unity/生产资源操作。handoff_ready只读等待，不超时接管。旧聊天会登记创建工具返回的真实threadId。禁止子代理、fork、并发角色或重复创建Rooster聊天。

RedScorpion完整完成，实时77/108、completed_pending_user_art_review、user_approved=false。最终installed_manifest.json和raster_revision_06；runtime_r01/runtime_updeath_r01各84 PASS/0 FAIL，共684张真实帧；实际查看10张整身时序板225张不同采样帧、四方向/strip及Up攻击放大图。原始Up/Down各一次和定向躯干修复一次均HTTP200；离线补片过软和重绘过平的版本被否决并留证，未装生产。勿重做RedScorpion或RatKing。Rooster交接时not_started、只有reference，仍核对实际阶段。PossessedWarg index79保持blocked，Down原付费结果不明，不重发、不删原request、不自行解除；progress.current可能仍指它，本聊天独立继续Rooster。

按完整执行prompt完成本角色：参考与解剖、生成原图实际审阅、分件/透明/布局实际门槛、安装前本角色增量快照及六保护指纹、单角色安装Verify、普通死亡与Up死亡两轮真实Play各84项、足够真实媒体时序审阅和必要返修、UTF-8观察、record及GIF归档。Rooster应以实际图集及完整prefab为准，不能凭文件名或其他鸟类套用。视觉问题即使程序PASS也返修，新revision保留旧证据；仅标实现完成待用户美术验收。

使用现有mcp_call.py HTTP Local8082，Client.identity动态发现完整实例并核对工程版本；原生Codex8083握手故障未改配置，不用CatchFish8080。开工重查身份与占用；上一角色release为Boot、非Play、所有场景非dirty、空闲、编译失败false、错误0。全局scope仍291既有unexpected，不能声称全局PASS；创建自己的安装前增量快照并比较历史分类。finalize_serial_character.py严格单独归因未改ReporterEditor在Play写build_info时间戳副作用，其余非目标增量拒绝；新增文件也对本角色快照检查。保留dirty，不pull/reset/clean/commit/push，不改配置表/ConfigJson/Gen，维持无声版。图片原件留盘分次审阅，避免一次加载历史图片；审阅板裁剪须保留角色全身，不将裁剪当运行缺件。

本角色完整完成或记录真实阻断并安全交还Unity后，重读items，写时间戳总结，更新README/原prompt实时块/NEXT_ENEMY_TASK，按CONTINUATION_PROTOCOL主动创建唯一全新本地后继聊天并登记真实所有权，做一次有界wait确认后停止本聊天修改，循环至全部有效完成或仅剩真实阻断。该串行循环已有用户授权，不等待逐角色确认。'''
(H/'NEXT_ENEMY_TASK.md').write_text('# 当前唯一敌人任务：Rooster\n\n'+dispatch+'\n',encoding='utf-8')
write(D/'successor_create_request.json',dict(target=dict(type='project',projectId='935c594c-f414-48e0-bd08-ed8ba342f7fd',environment=dict(type='local')),prompt=dispatch,title='Rooster 四方向串行续作'))
chain.update(state='handoff_ready',parent_thread_id=os.environ['CODEX_THREAD_ID'],current_character='Rooster',dispatch_token=token,character_status_at_handoff='not_started',completed_count_snapshot=77,last_handoff_file=handoff.relative_to(ROOT).as_posix(),progress_sha256_at_handoff=sha(H/'progress.json'),handoff_ready_at=now(),unity_release_file=release.relative_to(ROOT).as_posix())
write(H/'conversation_chain.json',chain)
assert handoff.read_text(encoding='utf-8') and read(D/'successor_create_request.json')['prompt']==dispatch
print(json.dumps(dict(state=chain['state'],next='Rooster',token=token,handoff=handoff.relative_to(ROOT).as_posix(),release=release.relative_to(ROOT).as_posix(),prefab_sha256=prefab_sha,probe=report['probe']),ensure_ascii=False))
