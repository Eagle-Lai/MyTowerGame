"""One-shot RoyalBoar closeout and unique successor preparation."""
from serial_common import *
import uuid

chain = owner()
assert not (D / 'successor_create_request.json').exists(), 'Inspect prior handoff before retry'
p = read(H / 'progress.json')
item = next(i for i in p['items'] if i['name'] == NAME)
assert item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
assert p['completed_count'] == 79
pending = [i for i in p['items'] if i['status'] not in ['completed_pending_user_art_review', 'user_approved', 'blocked']]
assert all(i['status'] == 'not_started' for i in pending), pending
next_item = min(pending, key=lambda i: i['index'])
assert next_item['name'] == 'SabretoothTiger' and next_item['index'] == 91
assert len(pending) == 28
assert [(i['name'], i['index']) for i in p['items'] if i['status'] == 'blocked'] == [('PossessedWarg', 79)]
assert all('reference' in path.relative_to(H / next_item['name']).parts
           for path in (H / next_item['name']).rglob('*') if path.is_file())
scope = read(D / 'scope_incremental_20261026.json')
assert scope['unexpected_incremental'] == [] and scope['unexpected_added'] == []
assert scope['installed_asset_drift'] == [] and scope['new_unexpected_vs_preexisting_legacy'] == []
assert scope['legacy_unexpected_count'] == 291 and scope['legacy_pass'] is False
assert len(scope['added_files']) == 20
manifest = read(D / 'installed_manifest.json')
assert len(manifest['changes']) == 20
assert all(sha(ROOT / x['path']) == x['after'] for x in manifest['changes'])
runtime = read(D / 'runtime_summary.json')
assert (runtime['passes'], runtime['failures'], runtime['actual_frames']) == (168, 0, 681)
binding = read(D / 'version_binding_final_20261026.json')
assert binding['manifest_sha256'] == sha(D / 'installed_manifest.json')
assert binding['runtime_summary_sha256'] == sha(D / 'runtime_summary.json')
assert (binding['review_sampling']['sample_slots'], binding['review_sampling']['unique_actual_frames']) == (256, 237)
baseline = read(D / 'incremental_before_20261026.json')
assert len(baseline['files']) == 5118 and len(baseline['protected_royalboar']) == 6
for path, expected in baseline['protected_royalboar'].items():
    if path != 'Assets/Prefabs/Enemy/Enemy_RoyalBoar.prefab':
        assert sha(ROOT / path) == expected, path
archive = read(H.parent / 'AllGIF/manifest.json')
gifs = [x for x in archive['files'] if x['source'].startswith('Remaining_20261024/RoyalBoar/')]
assert archive['count'] == 1210 and len(gifs) == 12
assert all(x['status'] == '当前审核版本' for x in gifs)
for x in gifs:
    assert sha(H.parent / x['source']) == x['sha256'] == sha(H.parent / 'AllGIF' / x['file'])
report = available(Client())
assert report['errors']['success'] and report['errors']['data'] == []
assert report['probe']['scene'] == 'Assets/Scenes/Boot.unity'
stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
release = D / ('unity_release_' + stamp + '.json')
write(release, report)
handoff = H / 'conversation_handoffs' / (stamp + '_RoyalBoar.md')
assert not handoff.exists()
token = 'royalboar-to-sabretoothtiger-' + uuid.uuid4().hex
prefab_sha = sha(ROOT / 'Assets/Prefabs/Enemy/Enemy_RoyalBoar.prefab')
assert prefab_sha == 'C606ED9849D7C3F5D691809D986069A637207F502C9A7677866ED269AAEC4FFF'
raw_hashes = '\n'.join('- ' + path + ': ' + sha(D / path) for path in [
    'generation/Up/raw.png', 'generation/Down/raw.png', 'generation/Up/revision_01/raw.png',
    'raster_revision_02/Down_derived_sheet.png'])
live = f'''2026-10-26 串行续接更新：79/108。RoyalBoar最终installed_manifest.json、raster_revision_02与offline_final_after_revision_04布局；runtime_r01/runtime_updeath_r01各84 PASS/0 FAIL，共681张真实帧(339+342)。实际查看10张整身时序板、256个采样位/237张不同实际帧，另审四方向、strip与两张原尺寸实际帧；未播放GIF，未逐帧查看全部681张。Up/Down初图及Up revision_01共三张HTTP200结果；Down revision_01/02均明确HTTP503并保留，未再付费重试。最终Down为原Down头腿与无方向特征的Up修订斑点躯干的本地派生组装；Up后脑与后蹄局部修补，原件/失败版保留，不冒充AI原图。原六绑定部件无尾巴/皇冠，不新增；透明兼容Tail与移除Tail节点留证。状态completed_pending_user_art_review，user_approved=false。安装前5118文件及六保护指纹；本角色语义通过、安装无drift、unexpected_incremental=[]、unexpected_added=[]，新增20个生产文件均本角色Directions(含目录meta)，Reporter的Play时间戳单独归因。全局291项历史unexpected，新增0，未称全局PASS。Unity交还Boot、非Play、非dirty、空闲、错误0。AllGIF实时1210项，RoyalBoar12项均当前审核版本且来源/归档哈希一致。下一唯一角色SabretoothTiger(index91)，PossessedWarg保持blocked且不重发原Down请求。详见conversation_handoffs/{handoff.name}，实时事实以progress与链所有权为准。'''
handoff.write_text(f'''# RoyalBoar 串行交接总结

时间：{now()}。目标 E:/MyTowerGame，Unity 2022.3.62f3c1。当前聊天只负责RoyalBoar(index90)，无子代理、fork或并发角色。

## 最终结果、版本与原图

- 实时79/108，28项not_started，PossessedWarg一项blocked。RoyalBoar为completed_pending_user_art_review，user_approved=false，没有替用户批准。
- 生产修改仅Enemy_RoyalBoar.prefab与本角色Directions。最终prefab SHA256={prefab_sha}；原指纹AA80CE55E793DA3006E03D29BBFEB7BB63F91C860BFE7D48F6E5A480079CF019。原根/GUID、HP/血条、碰撞器、锚点和业务语义PASS，原图集、源prefab及保护meta指纹不变。
- 实际角色为圆滚金色斑点野猪、奶油金额毛、尖耳、双象牙獠牙、四只短金蹄。原始六绑定部件LegFrontR/LegBackR/Body/LegFrontL/LegBackL/Head，无独立Tail，无皇冠；未按名称凭空添加器官。
- 付费请求共五次：初始Up和Down各HTTP200，Up revision_01为HTTP200；Down revision_01与revision_02均明确HTTP503/No available compatible accounts，失败记录保留，未再重试。三张原始成功图与所有请求/结果保留，密钥只在运行时使用。
- 初始Up有重复脸/额毛躯干及后向足趾问题，初始Down头腿可用但躯干重复额毛/吻部；均有真实审图记录。最终Up选generation/Up/revision_01/raw.png；Down选raster_revision_02/Down_derived_sheet.png，为本地派生图，不是AI原始返回：保留初始Down所有表情头与腿，仅替换无方向性斑点躯干。躯干从x1120开始，避开Dead头边界；早期裁切Dead右缘的失败组装保留。
- 最终raster_revision_02；Up后脑内侧象牙形弯月线用相邻金毛颜色修补，保持外轮廓/alpha，后蹄朝前趾缝同样局部填补。raster_retouch.json、retouch_heels.py记录父版本/范围/哈希，原图没有覆盖。
- 最终离线布局offline_final_after_revision_04，腿根内收遮于圆身下，保留短蹄尖；早期髋根外凸版本保留。对角四足步态legAngle8.5、legLift.009、bodyBob.004、bodyRoll.85、tailSwing0。Up头y.78/w.72/h.45/order22；Down头y.405/w.86/h.60；近腿x±.30/y.29/w.18/h.19，远腿x±.35/y.53/w.18/h.20/±10°。以layout_adjustments.json为权威。
- 兼容Tail切片透明1x1，Up/Down Tail rig节点均移除。installed_manifest.json存在且20项安装变化无drift；不要删除、盲目重装，不要重跑一次性prepare_specific/revise/select_and_stage/refine/preinstall/install。最终暂存与生产绑定见version_binding_final_20261026.json。

原图/派生图指纹：
{raw_hashes}

## 实际运行与视觉审阅

- Builder/Verify PASS；原侧向float/PPtr曲线、事件、时长及loop、root/HP/event receiver契约保留，无Missing/重复clone/Shadow，依赖及现有YooAsset收集覆盖保留。没有构建发布包或进行设备测试，没有生产C#改动。
- runtime_r01：84 PASS/0 FAIL、339帧，records SHA256=E39DDE097A684E9229108EFED83CE34B3C5867F7B02794F729CD6BDA2FBFF309。
- runtime_updeath_r01：84 PASS/0 FAIL、342帧，records SHA256=C449A5A9496897D65CEBD2CA0E7CA9F6DBBE5EC48E32A8D829D15240A704BFAD。
- 合计168 PASS/0 FAIL、681张真实Unity PNG。实际PNG、records与采样来源绑定哈希。两轮_returned.json均保留，未用合成姿态冒充实际帧。
- 实际审阅visual_review_serial_full_20261026全部10张整身时序板，共256个采样位、237张不同实际帧，另查看four_directions/runtime_visual_strip与原尺寸runtime_r01/frames/UpWalk_00006.png、DownWalk_00029.png。覆盖四方向步态、连续转向、Attack/Angry、Hurt/致死白闪、Down和Up死亡倾倒淡出收缩、回收/同实例Normal复用、暂停恢复、1x/2x/3x。
- 抽样中Up后脑无脸、额毛/耳朵归头，头身连接稳定；Down眼睛/鼻吻/双獠牙清楚，Angry眉眼确有变化；短蹄根遮挡稳定、无朝前趾缝、未新增尾巴。两方向死亡整身连接，复用恢复Normal。未见紫底污染、透明孔洞、浮肢、地面阴影或血条遮挡。完整UTF-8观察见record_note_utf8.txt和review.json。
- 采用PNG时序抽样，未播放GIF，未逐张审完681帧。审阅板只移除顶部100px标题区，旧固定y270裁剪可能截断角色。最终status以progress和review.json为准，runtime_summary等pending文字为阶段历史。

## 范围审计、归档与Unity交还

- 安装前incremental_before_20261026.json保存5118生产文件与六项保护指纹，均先与全局及reference核对。既有变化仅本角色prefab和Assets/StreamingAssets/build_info；后者由未修改ReporterEditor进入Play自动写时间戳，严格单独归因。
- 新增20个生产文件均为本角色Directions及目录meta。unexpected_incremental=[]、unexpected_added=[]、installed_asset_drift=[]，Prefab语义PASS。全局scope仍pass=false、291项历史unexpected，与PirateBoar既有分类比较新增0；未重置基线，未声称全局PASS。
- final_validation_20261026.json记录scriptCompilationFailed=false、错误0。未改配置表、Assets/ConfigJson、Assets/Gen、共享C#或声音功能；保留既有dirty，无pull/reset/clean/commit/push。
- AllGIF/manifest.json实时1210项，RoyalBoar共12项均当前审核版本，来源及归档SHA256逐项一致；不表示用户已验收，旧GIF保留。
- {release.name}为最终安全释放证据。mcp_call.py动态读取custom-tools/instances、选择完整MyTowerGame ID并核对E:/MyTowerGame/Unity版本。Boot、非Play、所有场景非dirty、无编译/域重载/更新、无评级/录像/审阅/手动模拟占用、错误0。使用HTTP Local8082，原生Codex8083配置未改，不用CatchFish8080。

## 唯一后继

实时items选择SabretoothTiger(index91,not_started)，目前其目录只有reference。新聊天仍须核对实际阶段、原始解剖和生产指纹。PossessedWarg(index79)保持blocked，原Down付费结果不明，不重发、不删request、不自行解除；progress.current可能仍指它，不盲用。

dispatch_token={token}，parent_thread_id={os.environ['CODEX_THREAD_ID']}。先handoff_ready，唯一全新local聊天创建明确成功后登记真实threadId/hostId并active；新聊天owner/角色/token全匹配才操作Unity/生产。handoff_ready只读等待，不超时接管。旧聊天交接后停止修改，只做一次有界wait。
''', encoding='utf-8')
prompt = H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
s = prompt.read_text(encoding='utf-8')
begin, end = '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->'
assert s.count(begin) == s.count(end) == 1
head, rest = s.split(begin, 1)
_, tail = rest.split(end, 1)
prompt.write_text(head + begin + '\n' + live + '\n' + end + tail, encoding='utf-8')
readme = H.parent / 'README.md'
s = readme.read_text(encoding='utf-8')
assert '本轮当前清单为 1198 个文件' in s
readme.write_text(s.replace('本轮当前清单为 1198 个文件', '本轮当前清单为 1210 个文件') + '\n' + live + '\n', encoding='utf-8')
dispatch = f'''在E:/MyTowerGame继续敌人四方向串行续作，本聊天只负责SabretoothTiger(index91)。接棒token为{token}，parent_thread_id为{os.environ['CODEX_THREAD_ID']}。

先读取根AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024下的REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json、conversation_handoffs/{handoff.name}，以及上级README/PREFAB_CHANGES_SUMMARY。检查未提交改动与SabretoothTiger已有材料，优先恢复已有阶段，禁止重复prepare/付费生成/install。根AGENTS中的FreedomTower_1/D:是旧信息，目标明确E:/MyTowerGame/Unity2022.3.62f3c1，不切工程、不改AGENTS。

创建有异步窗口：只有state=active、owner_thread_id等于本聊天运行时CODEX_THREAD_ID、current_character=SabretoothTiger且token完全匹配后才允许Unity/生产操作。handoff_ready只读等待，不超时接管，旧聊天将登记真实返回threadId。禁止子代理、fork、并发角色或重复创建SabretoothTiger聊天。

RoyalBoar已完整完成，实时79/108，completed_pending_user_art_review、user_approved=false。最终installed_manifest.json、raster_revision_02、offline_final_after_revision_04；runtime_r01/runtime_updeath_r01各84 PASS/0 FAIL，共681张真实帧(339+342)。实际审10张整身时序板256采样位/237张不同帧及四方向、strip与两张原尺寸帧，未播放GIF、未逐张审所有帧。三张成功AI原图与Down两次明确503失败保留；最终Down本地派生组合保留原Down头腿和无方向特征的Up修订躯干，后脑/后蹄局部修补有哈希；没有原尾巴/皇冠，不新增。不要重做RoyalBoar、Rooster、RedScorpion或RatKing，不删安装清单，不重跑前角色一次性脚本。SabretoothTiger交接时not_started、目录只有reference，仍核对现场。PossessedWarg index79保持blocked，Down原付费结果不明，不重发、不删原request、不自行解除；progress.current可能仍指它。

按完整原执行prompt完成SabretoothTiger：实际原图及完整prefab参考与解剖、原始生成实际审阅、分件/透明/布局门槛、安装前增量快照及六保护指纹、单角色安装Verify、普通死亡和Up死亡两轮真实Play各84项、足够实际媒体时序审阅及必要返修、UTF-8观察、record与GIF归档。不能凭文件名或其他四足兽套用；程序PASS仍需返修真实视觉问题，保留revision和原始付费结果，只标实现完成待用户美术验收。图片API遵循imagegen技能与项目已授权AIHub方式，gpt-image-2/medium/1536x1024/n1，密钥仅运行时使用。上一角色遇两次明确上游503，保留事实，按实际响应处理；未知结果不重发。

使用现有mcp_call.py HTTP Local8082，Client.identity动态发现完整实例并核对工程版本；原生Codex8083握手故障未改配置，不用CatchFish8080。开工重查身份/占用；上一角色release为Boot、非Play、所有场景非dirty、空闲、编译失败false、错误0。全局scope仍291既有unexpected，不能称全局PASS；建立SabretoothTiger安装前增量快照并比较历史分类。finalize_serial_character.py单独归因未改ReporterEditor在Play写build_info时间戳，其余非目标增量拒绝，新增文件同样检查。保留dirty，不pull/reset/clean/commit/push，不改配置表/ConfigJson/Gen/声音。图片分次实际审阅，原件留盘，审阅板保留全身，不把预览裁切当实际缺件。AllGIF实时1210，RoyalBoar12项来源与归档哈希已核对。

完整完成SabretoothTiger或记录真实阻断并安全交还Unity后，重读实时items，写时间戳总结，更新README/原prompt实时块/NEXT_ENEMY_TASK，按CONTINUATION_PROTOCOL主动创建唯一全新本地后继聊天并登记真实所有权，做一次有界wait后停止旧聊天修改，循环至全部有效完成或仅剩真实阻断。该串行循环已有用户直接授权，不等待逐角色确认。'''
(H / 'NEXT_ENEMY_TASK.md').write_text('# 当前唯一敌人任务：SabretoothTiger\n\n' + dispatch + '\n', encoding='utf-8')
write(D / 'successor_create_request.json', dict(target=dict(type='project', projectId='935c594c-f414-48e0-bd08-ed8ba342f7fd', environment=dict(type='local')), prompt=dispatch, title='SabretoothTiger 四方向串行续作'))
chain.update(state='handoff_ready', parent_thread_id=os.environ['CODEX_THREAD_ID'], current_character='SabretoothTiger',
             dispatch_token=token, character_status_at_handoff='not_started', completed_count_snapshot=79,
             last_handoff_file=handoff.relative_to(ROOT).as_posix(), progress_sha256_at_handoff=sha(H / 'progress.json'),
             handoff_ready_at=now(), unity_release_file=release.relative_to(ROOT).as_posix())
write(H / 'conversation_chain.json', chain)
assert handoff.read_text(encoding='utf-8') and read(D / 'successor_create_request.json')['prompt'] == dispatch
print(json.dumps(dict(state=chain['state'], next='SabretoothTiger', token=token,
                      handoff=handoff.relative_to(ROOT).as_posix(), release=release.relative_to(ROOT).as_posix(),
                      prefab_sha256=prefab_sha, archive_count=archive['count'], probe=report['probe']), ensure_ascii=False))
