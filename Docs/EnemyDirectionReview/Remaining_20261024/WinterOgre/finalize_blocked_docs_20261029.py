"""Publish factual blocked recovery documents; block the chain as the last write."""
from pathlib import Path
import copy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_winterogre import *


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')


def put(path, data, fresh=False):
    owner()
    path = Path(path)
    if fresh:
        assert not path.exists(), str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def replace_block(data, begin, end, content):
    first = begin.encode('ascii')
    last = end.encode('ascii')
    assert data.count(first) == data.count(last) == 1
    a = data.index(first) + len(first)
    b = data.index(last, a)
    # Preserve every byte outside the live state block, including old history.
    return data[:a] + b'\n' + content.encode('utf-8') + b'\n' + data[b:]


chain_before = owner()
stamp = read(D/'blocked_closeout_stamp.json')['stamp']
assert stamp == '20261029_134607'
block_path = D/('blocked_generation_recovery_'+stamp+'.json')
blocked = read(block_path)
release = read(D/blocked['unity_release'])
scope = read(D/blocked['scope'])
assessment = read(D/blocked['successor_assessment'])
assert blocked['status'] == 'blocked' and blocked['new_uncertain'] == 3
assert blocked['additional_network_attempts_used'] == {'Up':2, 'Down':0}
assert not release['error_free_release'] and release['error_count'] == 2
assert release['safe_to_stop_with_recorded_transport_error_limitation']
assert assessment['selected_successor'] is None
assert scope['unexpected_incremental'] == [] and scope['protected_six_unchanged']
assert snapshot() == {p:(scope['changes'][0]['after'] if p == 'Assets/StreamingAssets/build_info' else s)
                      for p,s in read(D/'incremental_before_20261029.json')['files'].items()}

progress_path = H/'progress.json'
chain_path = H/'conversation_chain.json'
readme_path = H.parent/'README.md'
prompt_path = H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
next_path = H/'NEXT_ENEMY_TASK.md'
tracked = [progress_path, chain_path, readme_path, prompt_path, next_path]
before = {p:p.read_bytes() for p in tracked}
progress = json.loads(before[progress_path].decode('utf-8-sig'))
assert progress['current'] == NAME and progress['completed_count'] == 99 and progress['authorized_count'] == 108
item = next(i for i in progress['items'] if i['name'] == NAME)
assert item['status'] == 'reference_prepared'
other_items = copy.deepcopy([i for i in progress['items'] if i['name'] != NAME])
closed_at = now()
handoff = H/'conversation_handoffs'/('20261029_134607_WinterOgre_blocked.md')
receipt = D/('blocked_closeout_receipt_'+stamp+'.json')
assert not handoff.exists() and not receipt.exists()
relative_block = block_path.relative_to(ROOT).as_posix()
relative_handoff = handoff.relative_to(ROOT).as_posix()

live = (
    '2026-10-29 WinterOgre111真实阻断，进度仍99/108（99项completed_pending_user_art_review，未代替用户批准），AllGIF1594、无新增媒体。'
    'Up初次与revision_01为Curl55发送中断，revision_02为fetch failed/ECONNRESET、TLS建立前断开；3次均无HTTP状态/raw/result/服务查询ID，结果及费用仍不明。'
    '两次额外恢复上限已耗尽，Down仅提示词未请求；不再新增Up请求，不用Down或其他角色付费探针。'
    '已审原atlas/完整源prefab并保存Giant动画契约：金色斑驳双足裸脚、白毛腰裙/护腕、空拳；原Weapon renderer禁用，不能新增拐杖。'
    '未stage/install/Verify/Play/record，未修改角色生产资源或共享C#。5545文件路径并集仅Reporter既有InitializeOnLoad回调自动更新时间戳，六保护/其他角色/配置无漂移；历史global291unexpected/6其他角色语义失败未重审。'
    'Unity8088动态核对E:/MyTowerGame/2022.3.62f3c1，单一clean Boot、非Play、tests/review/balance/recording/manual/compile/reload/update全空闲，failed=false、ready=true；保留2条MCP WebSocket连接Error，当前端到端可用，error0条件未满足，未清日志。'
    '其余7个not_started仅各8个reference文件，无独立生成/安装/运行工作；PossessedWarg旧Down不明阻断保留。'
    'chain=blocked，保留WinterOgre owner/token，没有创建后继。完整阻断证据WinterOgre/blocked_generation_recovery_20261029_134607.json；'
    '交接conversation_handoffs/20261029_134607_WinterOgre_blocked.md；唯一恢复入口NEXT_ENEMY_TASK.md，须按真实恢复条件推进，不能重置重试次数。')

handoff_text = f'''# WinterOgre(index111) 网络恢复耗尽：阻断交接

封存编号：{stamp}，沿用第一次封存尝试建立的编号；实际完成记录时间：{closed_at}。
工程 `E:/MyTowerGame`，Unity `2022.3.62f3c1`，实际 MCP `http://127.0.0.1:8088/mcp`。本聊天 `{OWNER}`，dispatch_token `{TOKEN}`。链设为 blocked，保留本 owner/token；没有创建后继。

## 真实进度和未执行项

实时 99/108；99 项都是 completed_pending_user_art_review，不代表用户美术批准。WinterOgre 从 reference_prepared 改为 blocked、user_approved=false。PossessedWarg79 原 blocked/Down结果不明保持不变；WinterWarg112、WinterWolfTypeA113、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118 共7项 not_started。原始名字 WolfMounfed 保留，不自行改名。

本角色没有 stage、安装、Verify、Play、两轮168检查、运行帧、record 或 GIF。AllGIF manifest 仍1594，无新增归档；没有借用前任168/0或旧角色结果。没有生成图可以美术审阅。当前只有源图审阅、独立解剖与提示词、原组件与动画契约及三次请求证据。

## 图片请求和费用

同一 `https://aihub.dog/v1/images/edits`，gpt-image-2 / medium / 1536x1024 / n=1。三次分别为：

| 路径 | UTC开始时间 | 实际已知结果 |
|---|---|---|
| generation/Up | 2026-10-29T05:31:17.279Z | Curl55 Send failure: Connection was aborted |
| generation/Up/revision_01 | 2026-10-29T05:40:23.008Z | Curl55，相同发送中断，额外恢复1 |
| generation/Up/revision_02 | 2026-10-29T05:43:16.148Z | Node fetch failed，ECONNRESET，TLS建立前断开，额外恢复2 |

三次均无 HTTP 状态、raw.png、result.json 或服务查询 ID；结果仍 uncertain，实际账单未知，不能写成明确失败或未收费。原 request、console、intent、uncertain_result 全部保留，逐文件 SHA 在 `{blocked['scope'].replace('scope_incremental_blocked_', 'blocked_generation_recovery_')}` 的 attempts 中。Down 只有 prompt，未发请求。当前未发现匹配本流水线的 node/curl 生成进程。

`standing_network_recovery_authorization_20261028.json` 的每方向2次额外网络恢复上限已耗尽。首次恢复使用本角色独立 application 与原证据 SHA；Docs/generate.mjs 仅定点允许本角色Up Curl55的revision_01/02，差异与前后SHA见 `{blocked['docs_tooling']}`。没有放宽 owner/token、intent、输入SHA、防重、请求参数或上限。不得再请求 Up，不重置计数，不新建空revision，不拿Down或其他角色付费试探。之前无密钥HEAD的404不证明图片POST恢复；费用未知也不因TLS报错而变为零。

## 源图与原生契约

实际查看 `reference/WinterOgre.png` 和 `reference/source_prefab_offline.png`。角色是秃头尖耳、金色斑驳皮肤、厚肚、白毛腰裙、两只巨型棕皮白毛护腕、两臂空拳与两只金色裸脚；没有毛靴、尾巴、骑手、角或背鬃。图集中条纹拐杖存在，但源与战斗prefab的 Weapon SpriteRenderer 都是 m_Enabled=0。保持 ArmR/FistR/Weapon 原层级与禁用状态，不新增手持武器。

原生Giant动画：Ready约0.5s且loop，Walk约0.6666667s且loop，Attack1s，Death0.5s；float bindings依次18/30/27/24，PPtr均0。Attack依次SetHead(0)@0、SetHead(1)@0.25、Event("Attack")@0.766666651、SetHead(0)@0.783333361；Death SetHead(2)@0。完整曲线/事件/时长/loop、层级与依赖在 `source_contract_20261029.json`，原序列化对象在 `original_serialized_objects_20261029.json`。不能套用野猪四足参数。

## 范围审计与第一次封存失败

开工前当前磁盘完整基线是 `incremental_before_20261029.json`，files为路径到SHA的dict，涵盖Assets/Packages/ProjectSettings/Luban共5545文件，包含既有用户修改，未用Git HEAD替代。封存完整路径并集仍5545，仅 `Assets/StreamingAssets/build_info` 一条变化：

- before：B0F0E60D467FF1667D356F9F300769E32AC0DB6A99769DB65CD1580D5EF55A73
- after：97518424ECA99D1F6E29D6946E56A9D899EFD32F740CD3B09C9D096415D466B3
- 文本：Build from BF-202610081033 at 2026/10/29 13:36:33

`Assets/Reporter/Editor/ReporterEditor.cs` SHA未变；既有InitializeOnLoad BuildInfo监听EditorApplication.update，初始isCompiling=true，在空闲时写一次时间戳，也响应后续编译结束，不要求Play。目标Unity进程现场报告开始于13:36:16，域重载和时间戳与启动相符；没有给回调增加仪表，因此不夸大为精确触发归因。本任务没有请求Play或直接写该文件，没有回滚它。六项保护文件全等，角色生产资源、共享C#、其他角色和配置无漂移；新增/删除均0，unexpected_incremental=[]。历史global291unexpected/6其他角色语义失败没有重审，不称全局PASS。

第一次 `release_blocked.py` 在assert not changes处停止，只建立了blocked_closeout_stamp.json，未执行后续封存。原脚本、原stamp和 `closeout_drift_probe_20261029.json` 保留；后补事实记录 `{blocked['retained_failed_closeout']}` 明确是回溯记录，未冒充原始stdout。新分类封存脚本只接受已观察到的这一条时间戳和两条MCP错误，其他变化会停止。导入目录问题首次运行即退出、未生成封存证据，修正后执行成功；没有追加图片请求。

## Unity现场和限制

通过8088 Client.identity现场发现实例，先custom-tools/instances、set_active_instance，再project/info核E:/MyTowerGame及2022.3.62f3c1；未使用8082其他工程结果。最新证据 `{blocked['unity_release']}` 记录：单一clean Boot、非Play、tests/review/balance/recording/manual/compile/reload/update均idle，scriptCompilationFailed=false、ready_for_tools=true、external_changes_dirty=false。只读刷新了MCP状态缓存，没有请求资源刷新或C#编译。

控制台保留2条MCP WebSocket Connection failed Error，堆栈为插件WebSocketTransportClient/McpLog.cs:50。当前identity/execute_code/editor state端到端请求成功，error CS查询为空，但error0交还条件未满足，不能报零错误；未清日志。13:25:32 preflight是0，13:46:37保存快照是2，精确发出时间不可证。目标Application.consoleLogPath与本机多编辑器共享Editor.log路径；现场文件头实际是D:/FishTestGame，因此该文件被排除，不当目标日志。目标LogEntry没有时间戳字段。

## 停链与恢复

`{blocked['successor_assessment']}` 实查9项未完成：7个not_started各只有8个reference文件，无raw/result/staged/install/runtime；PossessedWarg只有已成功Up与结果不明Down，没有可独立完成的阶段；WinterOgre没有图。共同图片网络故障下没有独立可推进工作，因此不创建后继、不用新角色收费探测。

完整恢复prompt为 `../NEXT_ENEMY_TASK.md`，单文件UTF8、可一次复制。首先只读检查保留请求、现有结果和服务记录；优先找回已有raw，不重新付费。没有可查询ID，不能凭猜测认定服务未处理。新的付费恢复需要真实故障解决证据与新允许的有界范围，现有2次上限不会因“继续”或新聊天自动重置。满足恢复条件后由正确owner明确记录恢复决定、重核当前基线和Unity身份，再按原阶段继续。原授权两轮真实Play仍有效，但本次没有执行。

禁止子代理、fork、计时器、模型/推理覆盖、Git改写/提交、构建/部署和长期memory写入；桌面控制仍须另行确认，优先目标Unity MCP。没有修改根AGENTS或其历史错配。全部后续工作仍保持源图/GUID/root/HP/碰撞/锚点/运动战斗参数、动画绑定事件、暂停/倍率/回收复用、白闪与死亡效果及无声版本；不写配置表/ConfigJson/Gen。完成角色最多记录completed_pending_user_art_review、user_approved=false。
'''

next_text = f'''# WinterOgre(index111) 阻断恢复：完整执行入口

在 `E:/MyTowerGame` 继续敌人四方向串行任务。当前真实状态是共同图片网络阻断，不能把本文件当成新增付费请求、重置上限或创建下一聊天的指令。先按以下完整说明读取并恢复既有阶段。

## 当前所有权和进度

- chain.state=blocked；保留owner_thread_id `{OWNER}`。
- dispatch_token `{TOKEN}`；当前唯一角色WinterOgre(index111)，user_approved=false。
- 进度99/108：99项completed_pending_user_art_review，2项blocked（PossessedWarg79、WinterOgre111），7项not_started（WinterWarg112、WinterWolfTypeA113、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118）。108是授权数量，终项Zombie118。
- AllGIF1594，本角色新增0。没有后继聊天、后台代理或定时器。旧生成/审核/批准/失败历史全部保留。
- state=blocked期间只读检查文件和既有服务结果；不能改生产、操作Unity或新增付费。满足已有恢复条件后，原owner明确保存恢复评估再转active；换聊天必须有用户授权的所有权交接，不凭超时抢锁。只有active、owner和token同时匹配才可生产/Unity/付费操作。

## 必须先读的当前磁盘

1. `E:/MyTowerGame/AGENTS.md`、`ProjectSettings/ProjectVersion.txt`。
2. `Docs/EnemyDirectionReview/README.md`、`PREFAB_CHANGES_SUMMARY_20261026.md`。
3. `Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md`、`CONTINUATION_PROTOCOL_20261026.md`、`IMAGE_RELAY_RECOVERY_20261026.md`。
4. 同目录实时 `conversation_chain.json`、`progress.json` 和本文件；历史数字不作为当前状态。
5. `standing_network_recovery_authorization_20261028.json`、`TreasureChest/standing_recovery_application_20261028.json`、`WinterOgre/standing_recovery_application_20261029_Up.json`。
6. `{relative_handoff}`。
7. `{relative_block}`、`WinterOgre/{blocked['unity_release']}`、`WinterOgre/{blocked['scope']}`、`WinterOgre/{blocked['successor_assessment']}`、`WinterOgre/{blocked['docs_tooling']}`。
8. `WinterOgre/reference_review_20261029.json`、`anatomy_plan.json`、`source_contract_20261029.json`、`original_serialized_objects_20261029.json`、`incremental_before_20261029.json`。
9. `WinterOgre/generation/Up`、`Up/revision_01`、`Up/revision_02`中的全部request/intent/console/uncertain_result；Down仅prompt。

只读核对已有阶段，不重跑establish_baseline.py、prepare_winterogre.py、prepare_network_recovery.py、release_blocked.py或已完成的封存脚本，不覆盖基线/历史证据，不删除清单绕过防重。基线files是路径到SHA的dict；已建立的5545文件基线包含既有用户修改，不以Git HEAD替换。

## 当前不可绕过的请求阻断

Up初次请求2026-10-29T05:31:17.279Z、revision_01请求05:40:23.008Z均为Curl55发送中断；revision_02请求05:43:16.148Z为fetch failed、ECONNRESET、TLS建立前断开。三次无HTTP状态、raw.png、result.json或服务查询ID，结果仍uncertain、费用仍未知。原件和逐文件SHA在blocked JSON中。Down从未请求，仅有提示词。

每方向最多2次额外网络恢复已用于Up，不能发第三次额外Up请求，不能清空或重置计数，不能借Down未用次数或新角色作付费探针。历史HEAD返回404只证明当时域名可达，不证明图片POST已恢复。PossessedWarg原Down请求仍结果不明，不重发、不删阻断。

先检查已有生成进程、原请求目录和实际可取得的服务结果/账单；不明请求必须保留，不推定未收费。若找回现有raw，确认对应请求与哈希后复用；不得重新生成同一成功图。若没有结果且上限耗尽，保留blocked。只有真实故障解决证据和新允许执行的有界范围才能扩大已耗尽的尝试；“继续任务”、新聊天或elapsed time本身不构成自动扩额。

现有图片参数固定 `https://aihub.dog/v1/images/edits`、gpt-image-2、medium、1536x1024、n=1；原generate_character.ps1/generate.mjs保留owner/token、SHA、intent和防重。不得换端点/质量/候选升级绕过阻断。若以后满足允许条件需要Image API，先读imagegen技能，密钥仅运行时从AIHUB_IMAGE_API_KEY或DPAPI `C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml`读取，只发aihub.dog、不随跨域跳转、不输出或落明文，结束清理；按实际格式/尺寸保存，usage估算不等于账单。

## WinterOgre身份、生产路径与原契约

- battle：`Assets/Prefabs/Enemy/Enemy_WinterOgre.prefab`
- source：`Assets/_UIAssets/Monsters/Giants/WinterOgre/WinterOgre.prefab`
- atlas：`Assets/_UIAssets/Monsters/Giants/WinterOgre/WinterOgre.png`
- controller：`Assets/_UIAssets/Monsters/_Common/Animations/Giant/Controller.controller`

已实际看原atlas和完整源prefab：金色斑驳秃头尖耳巨人、圆肚、白毛腰裙、棕皮白毛边巨护腕、双足裸脚、双臂空拳。没有毛靴、尾巴、背鬃、角或骑手。atlas的条纹拐杖不是可见装备，源与战斗Weapon renderer均m_Enabled=0；保留ArmR/FistR/Weapon层级、曲线与禁用状态，不新增拐杖。Up纯后脑、无眼鼻嘴和内耳面，后跟无正面脚趾；Down保持原脸和正面腰扣。每个部件连接根必须实心完整，肩颈/护腕/腰裙/腿根不得悬空；不要套野猪四足模板。

Giant原Ready0.5s loop、Walk约0.6666667s loop、Attack1s、Death0.5s；float bindings为18/30/27/24，PPtr均0。Attack有SetHead(0)@0、SetHead(1)@0.25、Event("Attack")@0.766666651、SetHead(0)@0.783333361；Death SetHead(2)@0。完整原float/PPtr/事件/时长/loop在source_contract中，必须逐项保留，不只对计数。结合已读直接调用/依赖/生命周期保护攻击、受击与致死白闪、全身死亡缩小旋转淡出、回收及同实例复用、暂停与1x/2x/3x；所有方向/状态无地面阴影，不加逐帧材质或层级查找。

## 满足恢复条件后的原流水线

当前没有任何生成图可审、没有stage/install/Verify/Play/record/运行媒体；不能写美术通过或两轮168/0。恢复后严格逐阶段推进：

1. 核对本角色原始图、源结构、当前六保护和完整当前磁盘路径并集；已有漂移先调查，不覆盖或回滚用户修改。
2. 优先复用找回的成功raw；只有符合新允许的请求条件才补缺失方向。每次实际看1–2张清晰原图，判断身份、正背面、裸脚、空拳、白毛护腕、连接与无阴影。未看不得称通过。
3. 透明分件、atlas、pivot、PPU、布局与离线完整rig分别审阅；保留失败revision，不能裁掉坏肢体掩盖，不把原侧面翻转当新正背面。
4. 保护与Unity空闲复核后，仅本角色Builder安装/Verify；保护源atlas/source prefab/GUID/root/HP/碰撞/锚点/运动战斗参数，核原侧面契约。未另获授权不改共享C#或其他角色。
5. 本链已明确授权两轮真实Unity Play，无需重复问；每轮84项，第二轮Up死亡。只停本任务Play，不强停外来Play。按实际运行结果修复再测，不能用历史/程序PASS替代当前美术复核。
6. 分批查看实际原PNG、时序板、GIF或编码帧，诚实写查看数量及不能实时播放/未逐帧全审等限制；记录最终安装和运行SHA绑定、UTF8 note，使用现有record流程。
7. GIF归档做源/目标SHA核对，完整路径并集及本角色原组件语义审计；历史291unexpected/6其他角色语义失败保留，不称全局PASS。角色最多completed_pending_user_art_review、user_approved=false。
8. 最后释放Unity、写完整带时间交接，重读实时items。优先已开始可恢复，否则最低index非blocked；有独立可推进工作才按协议创建唯一fresh local后继。先handoff_ready，现场list_projects，create_thread不传model/thinking、不fork，保存真实成功响应后最后一次工作区写入转新active owner/token；父随后只读。创建不明先查真实列表，不重复派发。仅剩共同阻断时停止，不创建空转后继。

## 正确Unity路由与现有交还限制

本任务用户已明确正确MCP是 `http://127.0.0.1:8088/mcp`，使用Remaining_20261024/mcp_call.py的Client.identity动态custom-tools/instances、明确选完整现场MyTowerGame ID，再project/info核E:/MyTowerGame与版本文件2022.3.62f3c1。根AGENTS的FreedomTower/D盘/8082是历史错配，本任务8088指令覆盖但不改根文件；8082是其他工程、8080是CatchFish。不能用注入的错误路由结果替代。断线/域重载后重新选实例核身份，按已有授权限次自主恢复；失败说明实际环节和具体开启步骤，不靠端口监听当成功。

最后现场是单一clean Boot、非Play、tests/review/balance/recording/manual/compile/reload/update全idle，failed=false、ready=true、external_changes_dirty=false。保留2条MCP WebSocket连接Error，当前8088端到端可用、error CS为空；error0条件未满足，未清控制台。目标LogEntry没有时间戳字段；共同Editor.log文件头是D:/FishTestGame，被排除为目标证据，不能借它推断本工程错误时间。

完整路径并集仅Assets/StreamingAssets/build_info从B0F0E60D467FF1667D356F9F300769E32AC0DB6A99769DB65CD1580D5EF55A73变为97518424ECA99D1F6E29D6946E56A9D899EFD32F740CD3B09C9D096415D466B3，文本为Build from BF-202610081033 at 2026/10/29 13:36:33。ReporterEditor.cs未变，InitializeOnLoad既有回调在启动/编译空闲时写时间戳，不需Play；没有回滚或把它写成做过Play。六保护、角色生产资源、共享C#、其他角色和配置均无漂移；原第一次封存失败脚本/stamp/回溯记录保留。

C#只有另获明确授权才改，若改完一批必须正确工程refresh_unity(force/all/request/wait_for_ready)、等compile/reload/update为false、ready=true，再read_console及scriptCompilationFailed闭环；编译时不继续改。不要因本次仅Docs而无端请求编译。默认只Unity MCP；桌面控制仍须另行弹窗确认。

## 固定边界

一次只做WinterOgre，不并发、不子代理、不fork、不计时器、不覆盖模型或推理设置。不git pull/reset/clean/commit或改写既有用户修改，不构建/设备部署，不更新长期memory。禁止资源/场景删除和未经授权外来Play变更。禁止脚本改关卡/敌人数值表或直接写Assets/ConfigJson/Assets/Gen，维持无声版本。输出中文UTF8，完整prompt保持单文件一次复制、无省略或占位符。无法推进的真实阻断保留，不伪造完成、费用、生成/运行审核、零错误或后台接棒。
'''

item.update(status='blocked', user_approved=False, blocked_at=closed_at,
    blocked_record=relative_block, blocked_reason=blocked['reason'],
    recovery_stage='Up_uncertain_network_recovery_limit_exhausted',
    additional_network_attempts_used={'Up':2,'Down':0},
    generation_outcome='Three Up requests uncertain; Down not requested; fees unknown',
    unity_release_file=(D/blocked['unity_release']).relative_to(ROOT).as_posix())
progress.update(status='blocked', current=NAME, updated_at=closed_at, completed_count=99)
assert [i for i in progress['items'] if i['name'] != NAME] == other_items
assert sum(i['status'] == 'completed_pending_user_art_review' for i in progress['items']) == 99
assert sum(i['status'] == 'blocked' for i in progress['items']) == 2
assert sum(i['status'] == 'not_started' for i in progress['items']) == 7

updated_readme = replace_block(before[readme_path], '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->', live)
updated_prompt = replace_block(before[prompt_path], '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->', live)
updated_readme += ('\n\n'+live+'\n').encode('utf-8')

backup_dir = D/('blocked_docs_before_'+stamp)
assert not backup_dir.exists()
for p in tracked:
    assert p.read_bytes() == before[p], 'Concurrent document change: '+str(p)
for p in tracked:
    put(backup_dir/p.name, before[p], fresh=True)
put(handoff, handoff_text.encode('utf-8'), fresh=True)
put(next_path, next_text.encode('utf-8'))
put(readme_path, updated_readme)
put(prompt_path, updated_prompt)
put(progress_path, encoded(progress))

# Check only the just-written delivery documents, not a new project test pass.
for p in [handoff, next_path]:
    text_value = p.read_text(encoding='utf-8')
    assert '\ufffd' not in text_value and '\x00' not in text_value
    assert OWNER in text_value and TOKEN in text_value
assert read(progress_path) == progress
assert handoff.read_bytes() == handoff_text.encode('utf-8')
assert next_path.read_bytes() == next_text.encode('utf-8')
assert chain_path.read_bytes() == before[chain_path], 'Owner changed before final transition'

chain_after = copy.deepcopy(chain_before)
chain_after.update(state='blocked', current_character=NAME,
    current_stage='WinterOgre_Up_uncertain_network_recovery_limit_exhausted',
    current_blocked=True, blocked_reason=blocked['reason'], stop_reason=blocked['reason'],
    stopped_at=closed_at, updated_at=closed_at, completed_count_snapshot=99,
    successor_created=False, dispatch_ready_for=None,
    resume_character=NAME, resume_stage='Read-only request/result inspection; no further paid Up attempt under exhausted existing limit',
    resume_conditions=['Recover an existing image result, or obtain actual network resolution evidence and newly permitted bounded paid execution.',
                       'Preserve three uncertain outcomes, unknown charges and consumed Up recovery count=2.',
                       'Record a valid owner-controlled resume decision before any Unity/production operation.'],
    previous_handoff_file=chain_before['last_handoff_file'], last_handoff_file=relative_handoff,
    handoff_sha256=sha(handoff), recovery_file=relative_block, last_stage_evidence=relative_block,
    unity_release_file=(D/blocked['unity_release']).relative_to(ROOT).as_posix(),
    successor_assessment=(D/blocked['successor_assessment']).relative_to(ROOT).as_posix(),
    progress_sha256_at_stop=sha(progress_path),
    closeout_receipt_file=receipt.relative_to(ROOT).as_posix())
chain_after.setdefault('stage_history', []).append(dict(character=NAME, status='blocked',
    current_stage=chain_after['current_stage'], owner_thread_id=OWNER, dispatch_token=TOKEN,
    closed_at=closed_at, handoff_file=relative_handoff, final_evidence=relative_block,
    unity_error_count=2, successor_created=False))
assert chain_after['owner_thread_id'] == OWNER and chain_after['dispatch_token'] == TOKEN
chain_bytes = encoded(chain_after)
delivered = [handoff, next_path, readme_path, prompt_path, progress_path]
put(receipt, encoded(dict(
    observed_at=now(), closed_at=closed_at, stamp=stamp, status='blocked', completed_count=99,
    owner_thread_id=OWNER, dispatch_token=TOKEN, no_successor_created=True,
    blocked_record=dict(path=relative_block, sha256=sha(block_path)),
    unity_error_count=2, error_free_release=False,
    production_scope=dict(path=(D/blocked['scope']).relative_to(ROOT).as_posix(), sha256=sha(D/blocked['scope'])),
    full_prompt=next_path.relative_to(ROOT).as_posix(),
    delivered_files={p.relative_to(ROOT).as_posix():sha(p) for p in delivered},
    archived_before_files={p.name:sha(backup_dir/p.name) for p in tracked},
    chain_before_sha256=hashlib.sha256(before[chain_path]).hexdigest().upper(),
    chain_after_sha256=hashlib.sha256(chain_bytes).hexdigest().upper(),
    final_workspace_write='conversation_chain.json: active -> blocked; owner/token retained',
    remaining_status_counts={'completed_pending_user_art_review':99, 'blocked':2, 'not_started':7})), fresh=True)

# Last workspace write: session owner guards intentionally reject future writes.
put(chain_path, chain_bytes)
print(json.dumps(dict(status='blocked', current=NAME, completed_count=99, owner=OWNER,
    requests=3, uncertain=3, errors=2, successor_created=False,
    handoff=relative_handoff, complete_recovery_prompt=next_path.relative_to(ROOT).as_posix(),
    receipt=receipt.relative_to(ROOT).as_posix()), ensure_ascii=False))
