from serial_common import *
import uuid

chain = owner()
p = read(H / 'progress.json')
item = next(i for i in p['items'] if i['name'] == NAME)
assert item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
assert p['completed_count'] == 78
pending = [i for i in p['items'] if i['status'] not in ['completed_pending_user_art_review', 'user_approved', 'blocked']]
assert not [i for i in pending if i['status'] != 'not_started'], pending
next_item = min(pending, key=lambda i: i['index'])
assert next_item['name'] == 'RoyalBoar' and next_item['index'] == 90
assert not (D / 'successor_create_request.json').exists(), 'Inspect existing handoff before retry'
scope = read(D / 'scope_incremental_20261026.json')
assert scope['unexpected_incremental'] == [] and scope['unexpected_added'] == [] and scope['installed_asset_drift'] == []
assert scope['new_unexpected_vs_preexisting_legacy'] == [] and scope['legacy_unexpected_count'] == 291 and scope['legacy_pass'] is False
assert len(scope['added_files']) == 20
runtime = read(D / 'runtime_summary.json')
assert runtime['passes'] == 168 and runtime['failures'] == 0 and runtime['actual_frames'] == 681
binding = read(D / 'version_binding_final_20261026.json')
assert binding['review_sampling']['sample_slots'] == 256 and binding['review_sampling']['unique_actual_frames'] == 231
baseline = read(D / 'incremental_before_20261026.json')
assert len(baseline['files']) == 5098 and len(baseline['protected_rooster']) == 6
archive = read(H.parent / 'AllGIF/manifest.json')
gifs = [x for x in archive['files'] if x['source'].startswith('Remaining_20261024/Rooster/')]
assert archive['count'] == 1198 and len(gifs) == 12 and all(x['status'] == '当前审核版本' for x in gifs)
for x in gifs:
    assert sha(H.parent / x['source']) == x['sha256'] == sha(H.parent / 'AllGIF' / x['file'])
report = available(Client())
assert report['errors']['success'] and report['errors']['data'] == []
assert report['probe']['scene'] == 'Assets/Scenes/Boot.unity', report['probe']
stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
release = D / ('unity_release_' + stamp + '.json')
write(release, report)
handoff = H / 'conversation_handoffs' / (stamp + '_Rooster.md')
token = 'rooster-to-royalboar-' + uuid.uuid4().hex
prefab_sha = sha(ROOT / 'Assets/Prefabs/Enemy/Enemy_Rooster.prefab')
assert prefab_sha == '5B43FF006893FE9B1CD610B2F3BA9FB61F90214C676CF4B5FC9DC1E1A24FCABF'
live = f'''2026-10-26 串行续接更新：78/108。Rooster最终installed_manifest.json，raster_revision_02与offline_final_after_revision_03布局；runtime_r01/runtime_updeath_r01各84 PASS/0 FAIL，共681张真实帧。实际查看10张整身时序板、256个采样位/231张不同实际帧及四方向、strip；未播放GIF，未逐帧查看全部681张。Up/Down原始生成各一次均HTTP200，Up脚本地修成后跟/单后趾，翅根内收、头颈重叠消除重复颈段；原未绑定金色Tail不新增，透明兼容Tail与移除Tail节点留有记录。状态completed_pending_user_art_review，user_approved=false。安装前5098文件及六保护指纹；本角色语义通过、安装无drift、unexpected_incremental=[]、unexpected_added=[]，新增20个生产文件均本角色Directions，Reporter的Play时间戳单独归因。全局291项历史unexpected，新增0，未称全局PASS。Unity交还Boot、非Play、非dirty、空闲、错误0。AllGIF实时1198项，Rooster12项均当前审核版本。下一唯一角色RoyalBoar(index90)，PossessedWarg保持blocked且不重发原Down请求。详见conversation_handoffs/{handoff.name}，实时事实以progress与链所有权为准。'''
handoff.write_text(f'''# Rooster 串行交接总结

时间：{now()}。目标 E:/MyTowerGame，Unity 2022.3.62f3c1。本聊天仅负责 Rooster(index89)，无子代理、fork 或并发角色。

## 最终结果与美术版本

- 实时78/108，29项not_started、PossessedWarg一项blocked。Rooster为completed_pending_user_art_review，user_approved=false，未替用户批准。RatKing和RedScorpion未重做。
- 生产仅修改Enemy_Rooster.prefab与本角色Directions。最终prefab SHA256：{prefab_sha}；原指纹F34C12FE29DCF28CD90648E977C3EEED229E2CFABCBBBCCF22B5A7EB7585C280。原根、GUID、HP、血条、碰撞器、锚点及业务语义PASS，原始图集、源prefab及meta保护指纹不变。
- 已完成两次付费原始生成，Up与Down各一次，均HTTP200、1536x1024。原始Up SHA256=E7EDC078ECA475C51A58793E4555EC97E1C2EAA1AD7626E01B2A0D7508AE610E；Down SHA256=45715E82B2C9193D7CE07B29B113D747F5D8736B830401E30C346D60FC37F136。请求、prompt、result及raw保留于generation，未追加生成、未重发不明请求；密钥仅运行时使用。
- 原prefab实际绑定五部件LegR、Body、LegL、Head、Wing；原图中的金色Tail未绑定，不擅自增加。为七部件兼容契约保留透明1x1 Tail资产，并移除Up/Down Tail rig节点。左右翅根内收，头颈重叠以消除重复颈段；Up脚本地修为后跟/单后趾，去除朝前的三趾扇。权威调整见layout_adjustments.json、raster_retouch.json。
- 最终raster_revision_02，离线布局offline_final_after_revision_03。被否决及中间版本全部保留。installed_manifest.json已存在且20项安装变化无drift；不要删除、盲目重装，不要重跑一次性refine_offline.py/preinstall_gate.py。当前staged_art和最终生产安装绑定在version_binding_final_20261026.json。

## 实际验证与视觉审阅

- Builder/Verify通过；原侧向float/PPtr曲线、事件、时长与loop、root/HP/event receiver契约保留，无重复clone/Missing脚本，依赖与现有收集覆盖保留。未构建发布包或进行设备测试。
- runtime_r01为84 PASS/0 FAIL、341帧，records SHA256=B030F60E413CC300F5CADA97948CBB40D046F12CBD013950E76D6980198E59C4；runtime_updeath_r01为84 PASS/0 FAIL、340帧，records SHA256=909214BF2868723B3BACE98600ECFDF6A3C0DCEA2DEC6205B704B08D809F3E9D。合计168 PASS/0 FAIL、681张真实Unity PNG，全部绑定SHA256。两轮结束均安全交还Unity，返回证据仍保留。
- 实际查看visual_review_serial_full_20261026下全部10张整身时序板，256个采样位、231张不同真实帧，另看四方向及runtime_visual_strip。覆盖四方向步态、连续转向、Attack/Angry、Hurt白闪、Down及Up死亡、倾倒/淡出/收缩、回收复用、暂停恢复和1x/2x/3x。
- 抽样中正面眼嘴与垂肉清楚，Down Angry眉眼确有变化；后脑无脸，颈/翅根连接稳定，Up脚后跟可见且无前方三趾扇；死亡及同实例Normal复用连贯。未见紫边、透明孔洞、脱离部件、地面阴影或血条遮挡。完整UTF-8观察见record_note_utf8.txt与review.json。
- 审阅是按时间顺序的实际PNG抽样，未播放GIF全片，也未逐张审681帧。整身板排除顶部100px标题区；固定y270裁剪会截断颈部，不能以该裁剪判运行时缺件。最终status以progress和review.json为准；runtime_summary、raster_retouch中的pending描述为其阶段历史。

## 范围审计与Unity交还

- incremental_before_20261026.json保存安装前5098文件及六保护指纹。既有文件变化只有本角色prefab及Assets/StreamingAssets/build_info；后者为未修改ReporterEditor在Play写入的时间戳，已严格单独归因。新增20个生产文件全部本角色Directions(含目录meta)。unexpected_incremental=[]、unexpected_added=[]、installed_asset_drift=[]，Prefab语义PASS。
- scope_Rooster_20261026_205023.json全局仍pass=false、291项历史unexpected，与PirateBoar既有分类比较新增0。未重置基线，不声称全局PASS。
- final_validation_20261026.json记录scriptCompilationFailed=false、错误0。本聊天没有修改生产C#、配置表、Assets/ConfigJson、Assets/Gen、共享系统或声音功能。保留其他dirty，无pull/reset/clean/commit/push。
- {release.name}通过现有mcp_call.py HTTP Local8082动态发现完整实例并核对E:/MyTowerGame及版本。Boot、非Play、所有场景非dirty，无编译/域重载/更新、评级/录像/审阅/手动模拟占用，错误0。原生工具8083握手故障未改配置，不使用CatchFish8080。
- AllGIF清单1198项，本角色12项均当前审核版本；已核对来源及归档SHA256，历史原GIF保留。GIF归档身份不表示用户已验收。

## 唯一后继

重读实时items，下一项RoyalBoar(index90,not_started)。当前目录仅reference原始材料，无生成或安装；后继仍须实时核对阶段。PossessedWarg(index79)保持blocked，原Down付费结果不明，不重发、不删request、不自行解除。progress.current可能仍指它，不盲用该字段。

token={token}，parent_thread_id={os.environ['CODEX_THREAD_ID']}。先handoff_ready，唯一全新local聊天创建明确成功后登记真实threadId/hostId，转为active。新聊天必须owner/角色/token全部匹配才操作Unity及生产；handoff_ready只读等待，不超时接管。旧聊天转交后停止修改，只做一次有界wait。
''', encoding='utf-8')
prompt = H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
s = prompt.read_text(encoding='utf-8')
begin = '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->'
end = '<!-- ENEMY_SERIAL_LIVE_STATE_END -->'
assert s.count(begin) == s.count(end) == 1
head, rest = s.split(begin, 1)
_, tail = rest.split(end, 1)
prompt.write_text(head + begin + '\n' + live + '\n' + end + tail, encoding='utf-8')
readme = H.parent / 'README.md'
s = readme.read_text(encoding='utf-8')
assert '本轮当前清单为 1186 个文件' in s
readme.write_text(s.replace('本轮当前清单为 1186 个文件', '本轮当前清单为 1198 个文件') + '\n' + live + '\n', encoding='utf-8')
dispatch = f'''在E:/MyTowerGame继续敌人四方向串行续作，本聊天只负责RoyalBoar(index90)。接棒token为{token}，parent_thread_id为{os.environ['CODEX_THREAD_ID']}。

先读取根AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024下的REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json、conversation_handoffs/{handoff.name}，以及上级README/PREFAB_CHANGES_SUMMARY。检查未提交改动与RoyalBoar已有材料，优先恢复已有阶段，禁止重复prepare/付费生成/install。根AGENTS中的FreedomTower_1/D:是旧信息，目标明确E:/MyTowerGame/Unity2022.3.62f3c1，不切工程、不改AGENTS。

创建存在异步窗口：只有state=active、owner_thread_id等于本聊天运行时CODEX_THREAD_ID、current_character=RoyalBoar且token完全匹配后才允许Unity/生产资源操作。handoff_ready只读等待，不超时接管。旧聊天会登记创建工具返回的真实threadId。禁止子代理、fork、并发角色或重复创建RoyalBoar聊天。

Rooster已完整完成，实时78/108，状态completed_pending_user_art_review、user_approved=false。最终installed_manifest.json、raster_revision_02、offline_final_after_revision_03；runtime_r01/runtime_updeath_r01各84 PASS/0 FAIL，共681张真实帧；实际查看10张整身时序板256采样位/231张不同帧及四方向、strip，未播放GIF、未逐张审所有帧。两张Up/Down原始图均HTTP200；本地修正Up脚后跟/单后趾、头颈重复与翅根。原绑定仅五部件，未绑定金色Tail未新增，透明兼容Tail和移除Tail节点留证。不要重做Rooster、RedScorpion或RatKing，不要重跑Rooster一次性refine_offline.py/preinstall_gate.py，不删安装清单。RoyalBoar交接时not_started、目录只有reference，仍核对现场阶段。PossessedWarg index79保持blocked，Down原付费结果不明，不重发、不删原request、不自行解除；progress.current可能仍指它。

按完整原执行prompt完成RoyalBoar：实际原图及完整prefab参考与解剖、生成原图实际审阅、分件/透明/布局门槛、安装前增量快照及六保护指纹、单角色安装Verify、普通死亡与Up死亡两轮真实Play各84项、足够真实媒体时序审阅和必要返修、UTF-8观察、record及GIF归档。不能凭文件名或其他野猪方案套用；程序PASS仍需返修真实视觉问题，保留旧revision与原始付费结果，只标实现完成待用户美术验收。

使用现有mcp_call.py HTTP Local8082，Client.identity动态发现完整实例并核对工程版本；原生Codex8083握手故障未改配置，不用CatchFish8080。开工重查身份与占用；上一角色release为Boot、非Play、所有场景非dirty、空闲、编译失败false、错误0。全局scope仍291既有unexpected，不能称全局PASS；建立RoyalBoar安装前增量快照并比较历史分类。finalize_serial_character.py单独归因未改ReporterEditor在Play写build_info时间戳，其余非目标增量拒绝，新增文件也须检查。保留dirty，不pull/reset/clean/commit/push，不改配置表/ConfigJson/Gen，维持无声版。图片分次实际审阅，原件留盘，审阅板必须保留全身，不把预览裁切当实际缺件。

完整完成RoyalBoar或记录真实阻断并安全交还Unity后，重读实时items，写时间戳总结，更新README/原prompt实时块/NEXT_ENEMY_TASK，按CONTINUATION_PROTOCOL主动创建唯一全新本地后继聊天并登记真实所有权，做一次有界wait后停止旧聊天修改，循环至全部有效完成或仅剩真实阻断。该串行循环已有用户直接授权，不等待逐角色确认。'''
(H / 'NEXT_ENEMY_TASK.md').write_text('# 当前唯一敌人任务：RoyalBoar\n\n' + dispatch + '\n', encoding='utf-8')
write(D / 'successor_create_request.json', dict(target=dict(type='project', projectId='935c594c-f414-48e0-bd08-ed8ba342f7fd', environment=dict(type='local')), prompt=dispatch, title='RoyalBoar 四方向串行续作'))
chain.update(state='handoff_ready', parent_thread_id=os.environ['CODEX_THREAD_ID'], current_character='RoyalBoar', dispatch_token=token, character_status_at_handoff='not_started', completed_count_snapshot=78, last_handoff_file=handoff.relative_to(ROOT).as_posix(), progress_sha256_at_handoff=sha(H / 'progress.json'), handoff_ready_at=now(), unity_release_file=release.relative_to(ROOT).as_posix())
write(H / 'conversation_chain.json', chain)
assert handoff.read_text(encoding='utf-8') and read(D / 'successor_create_request.json')['prompt'] == dispatch
print(json.dumps(dict(state=chain['state'], next='RoyalBoar', token=token, handoff=handoff.relative_to(ROOT).as_posix(), release=release.relative_to(ROOT).as_posix(), prefab_sha256=prefab_sha, probe=report['probe']), ensure_ascii=False))
