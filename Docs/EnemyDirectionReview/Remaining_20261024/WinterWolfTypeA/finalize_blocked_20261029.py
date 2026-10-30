"""Persist an accurate blocked handoff. No generation, production edits or Unity calls."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = RUN.parents[2]
NOW = datetime.now(timezone(timedelta(hours=8))).isoformat()
STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
TOKEN = 'winterwarg-to-winterwolftypea-20261029_173527-8e8dd053-9008-4a8f-b69a-61a589f400a4'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def save_new(path, value):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


chain_path = RUN / 'conversation_chain.json'
progress_path = RUN / 'progress.json'
chain = load(chain_path)
progress = load(progress_path)
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['dispatch_token'] == TOKEN and chain['current_character'] == 'WinterWolfTypeA'
assert progress['completed_count'] == 101 and progress['authorized_count'] == 108
item = next(x for x in progress['items'] if x['name'] == 'WinterWolfTypeA')
assert item == {'index': 113, 'name': 'WinterWolfTypeA', 'status': 'reference_prepared'}
inspection_path = HERE / 'closeout_inspection_index_20261029_180355.json'
inspection = load(inspection_path)
requests = load(ROOT / inspection['requests'])
scope = load(ROOT / inspection['scope'])
unity = load(ROOT / inspection['unity_release'])
assessment = load(ROOT / inspection['successor_assessment'])
assert requests['unknown_outcomes'] == 3 and requests['additional_recovery_used'] == 2
assert scope['production_unchanged'] and unity['safe_release'] and unity['error_count_returned'] == 0
assert not assessment['independent_successor_available']
assert load(RUN.parent / 'AllGIF/manifest.json')['count'] == 1642
assert not any((HERE / p).exists() for p in ['staged_art', 'installed_manifest.json', 'runtime_summary.json', 'art_selection.json'])

backup = HERE / ('docs_before_blocked_handoff_' + STAMP)
backup.mkdir()
readme_path = RUN.parent / 'README.md'
prompt_path = RUN / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
next_path = RUN / 'NEXT_ENEMY_TASK.md'
for path in [chain_path, progress_path, readme_path, prompt_path, next_path]:
    shutil.copy2(path, backup / path.name)

report_path = HERE / ('blocked_generation_recovery_' + STAMP + '.json')
handoff_path = RUN / 'conversation_handoffs' / (STAMP + '_WinterWolfTypeA_blocked.md')
recovery_prompt_path = HERE / ('blocked_resume_prompt_' + STAMP + '.md')
reason = ('WinterWolfTypeA Down initial and revision_01 returned Curl55 send-aborted; '
          'revision_02 through the reviewed existing proxy returned Curl52 empty reply. '
          'All three lack HTTP status, image/result or provider query ID; outcomes and possible charges remain unknown. '
          'Both additional standing recovery attempts are consumed (2/2, an agent execution bound, not a user monetary budget). '
          'Up succeeded and has preserved local raster revisions, but no complete Down exists. '
          'No remaining character has an independent complete generation/stage/install/runtime phase; stop the shared image-service chain without a probe successor.')

report = {
    'observed_at': NOW, 'character': 'WinterWolfTypeA', 'index': 113,
    'status': 'blocked', 'current_stage': 'Down_unknown_after_bounded_network_recovery',
    'user_approved': False, 'owner_thread_id': chain['owner_thread_id'], 'dispatch_token': TOKEN,
    'reason': reason, 'attempts': requests['attempts'],
    'current_character_requests': {'Up': 1, 'Down': 3, 'total': 4, 'HTTP200': 1, 'unknown': 3},
    'standing_recovery': {
        'used': 2, 'limit': 2, 'reset': False,
        'limit_origin': 'Conservative agent execution bound, not a user monetary budget',
        'source_thread_id': '01a18093-7687-7313-aaba-7419090cc829',
        'source_user_message_id': '01a180aa-7768-7222-bc85-7aa51e801cdd',
        'statement': '继续任务。后续同样的情况，不再需要我确认，可以继续静默执行',
        'live_original_evidence': rel(HERE / 'standing_authorization_original_messages_20261029.json'),
        'application': rel(HERE / 'standing_recovery_application_20261029_Down.json'),
        'other_characters_consumed_counts_changed': False,
    },
    'billing': 'Unknown for all three Down requests. Aggregate usage and wallet balance do not assign individual charges. No claim of non-billing.',
    'read_only_service_evidence': {
        'file': rel(HERE / 'read_only_service_recheck_20261029T094736Z.json'),
        'sha256': sha(HERE / 'read_only_service_recheck_20261029T094736Z.json'),
        'finding': 'Authenticated GET/models and GET/usage returned200 with valid balance; not evidence of successful paid image POST or disposition of previous requests.',
    },
    'credential_free_control': {
        'file': rel(HERE / 'unauthenticated_transport_control_20261029.json'),
        'sha256': sha(HERE / 'unauthenticated_transport_control_20261029.json'),
        'direct': 'Curl55 after65331 uploaded bytes, no HTTP status',
        'existing_proxy': '434497 uploaded bytes, HTTP401, TLS verify0',
        'paid_followup': 'Down revision_02 still returned Curl52. Control401 did not establish image-generation availability.',
        'system_proxy_changed': False,
    },
    'up': {
        'initial_raw': rel(HERE / 'generation/Up/raw.png'),
        'initial_sha256': sha(HERE / 'generation/Up/raw.png'),
        'last_reviewed_local_candidate': rel(HERE / 'generation/Up/local_revision_03/raw.png'),
        'local_candidate_sha256': sha(HERE / 'generation/Up/local_revision_03/raw.png'),
        'local_raster_not_AI_result': True, 'review': inspection['up_review'],
        'final_art_selection_or_rig_acceptance': False,
    },
    'source_animation_contract': rel(HERE / 'source_animation_contract_complete_20261029.json'),
    'invalid_earlier_contract_capture': 'source_animation_contract_20261029.json retained as history; use the complete capture.',
    'staging': 'not_executed', 'install_verify': 'not_executed', 'runtime': 'not_executed',
    'record': 'not_executed', 'new_gifs': 0, 'production_changes': False,
    'completed_count': 101, 'authorized_count': 108, 'allgif_count': 1642,
    'scope': inspection['scope'], 'unity_release': inspection['unity_release'],
    'unity_error_count': 0, 'unity_safe_release': True,
    'successor_assessment': inspection['successor_assessment'], 'docs_tooling': inspection['docs_tooling'],
    'request_recheck': inspection['requests'], 'process_recheck': inspection['process_check'],
    'handoff_file': rel(handoff_path), 'resume_prompt_file': rel(recovery_prompt_path),
    'no_successor_created': True, 'retained_owner_and_token': True,
    'recovery_conditions': [
        'Recover an existing Down result and its request/version linkage, or obtain concrete provider disposition for the unknown requests.',
        'If another request becomes necessary, diagnose and resolve the actual authenticated POST failure and record a new bounded execution decision under the existing authorization; this report grants no extra attempt.',
        'Preserve all unknown outcomes, possible charges, consumed counters, request/raw/console history and original approvals.',
        'A repeated models/usage200, unauthenticated401, elapsed time or a fresh chat is not sufficient recovery evidence.',
    ],
}
save_new(report_path, report)

full_prompt = f'''# WinterWolfTypeA(index113) 阻塞恢复完整执行 Prompt

在 E:/MyTowerGame 继续敌人四方向续作，本次唯一角色仍为 WinterWolfTypeA(index113)。本文件是完整 UTF8 恢复入口，可以一次复制。任务尚未完成，不把阻塞当作验收，不重新准备或盲目生成，不创建空转后继。当前时间记录 {NOW}；实时进度101/108，AllGIF1642。

## 1. 先读现场与所有权

先完整读取 E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt，以及以下文件；下列相对路径均相对 E:/MyTowerGame：

1. Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
2. Docs/EnemyDirectionReview/Remaining_20261024/CONTINUATION_PROTOCOL_20261026.md 和 IMAGE_RELAY_RECOVERY_20261026.md。
3. Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md、conversation_chain.json、progress.json。
4. Docs/EnemyDirectionReview/README.md 和 PREFAB_CHANGES_SUMMARY_20261026.md。
5. {rel(handoff_path)} 与 {rel(report_path)}。
6. {inspection['requests']}、{inspection['process_check']}、{inspection['scope']}、{inspection['unity_release']}、{inspection['successor_assessment']}、{inspection['up_review']}、{inspection['docs_tooling']}。
7. WinterWolfTypeA 目录中的 sync_start_20261029.json、production_paths_before_20261029.json、anatomy_plan.json、source_animation_contract_complete_20261029.json、standing_authorization_original_messages_20261029.json、standing_recovery_application_20261029_Down.json、proxy_transport_application_20261029.json、read_only_service_recheck_20261029T094736Z.json、unauthenticated_transport_control_20261029.json 和全部 generation 原始材料。
8. 现有 character_step.py、prepare_character.py、generate_character.ps1、generate.mjs、pack_character.py、adjust_layout.py、install_character.py、runtime_runner.py、runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py，local_baseline.json、production_fingerprints_before.json、Batch01_10/user_approval_20261023.json 和 AllGIF/manifest.json。

当前链 state=blocked，owner_thread_id=01a18704-42a8-7f52-bc92-f8ca404a0b39，dispatch_token={TOKEN}，current_character=WinterWolfTypeA。没有新后继聊天，也没有新token。blocked期间只读诊断、核对与保存Docs恢复证据；不能操作Unity或生产资源。恢复条件实证满足后，由同一合法owner记录具体恢复依据、保持owner/token并将链恢复active，再执行后续；若用户另开新聊天，先同步，只能在原owner明确转移唯一所有权后操作，不超时抢锁、不自行改owner、不重复派发。

## 2. 当前准确阻塞与费用状态

Up首次请求HTTP200，原图generation/Up/raw.png，RGB1536×1024，1403379bytes，SHA256={sha(HERE / 'generation/Up/raw.png')}。Down三次都结果不明：

| 请求 | 现场结果 | 当前缺失 |
|---|---|---|
| generation/Down | Curl55 Send failure: Connection was aborted | 无HTTP、raw、result、query/job ID |
| generation/Down/revision_01 | Curl55 Send failure: Connection was aborted | 无HTTP、raw、result、query/job ID |
| generation/Down/revision_02 | 经既有127.0.0.1:7897代理仍Curl52 Empty reply from server | 无HTTP、raw、result、query/job ID |

三个请求的prompt/request/console/uncertain均保留；完整SHA见阻塞报告和down_request_recheck。站立授权原用户原文是“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”，来源聊天01a18093-7687-7313-aaba-7419090cc829、用户消息01a180aa-7768-7222-bc85-7aa51e801cdd，本聊天已read_thread现场核对。两个额外恢复机会2/2均已消耗，数字是代理保守执行上限，并非用户金额预算；不重置前任任何角色计数。本文件没有新增付费机会，不再发送Down或用下一角色付费探测。

认证GET/models与GET/usage曾返回200、余额有效，但不能证明图像POST可用、旧请求未收费或已完成。无密钥诊断中直连上传65331bytes后Curl55，既有代理完整上传434497bytes返回401/TLSverify0；真实代理Down02仍Curl52。系统代理未更改。本轮收尾没有新付费调用，进程复查无在运行的图像生成器；本地进程结束不证明远端未处理。

先查现存结果、文件、服务响应及可用provider查询路径。需要恢复旧Down结果及其版本关联，或获得具体请求处置；确需新请求时，必须先诊断并解决真实认证POST故障，再记录在已有授权内的新有限执行决策。重复GET200、无密钥401、时间经过或换聊天均不是恢复证据。三次费用始终unknown，不推断免费。不要盲查未文档化付费端点，不再重复诊断计费请求。

## 3. 参考、解剖与现有Up局部稿

battle=Assets/Prefabs/Enemy/Enemy_WinterWolfTypeA.prefab；source=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/WinterWolfTypeA.prefab；atlas=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/WinterWolfTypeA.png；controller=Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller；Directions=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/Directions。

已实际看完整原atlas与完整序列化源参考，读战斗/源层级与锚点。真实特征是棕橄榄背、赭圆斑、高尖棕耳、象牙白眉和白眼底/深瞳、白长口鼻、宽白尖胸毛、四条短棕上腿/白爪、整条象牙白加taupe阴影的蓬尾。不是琥珀发光眼，不是只有尾尖白，不沿用WinterWarg的刺或造型。无项圈、鞍、背刺。

原Up躯干出现额外耳状突起，后脚带前趾线。local_revision_01移除躯干重复耳并闭合白肩毛，local_revision_02继续去后趾但填色有斑驳；最新generation/Up/local_revision_03/raw.png将后跟下部内侧平涂为原风格象牙白，保留四像素外描边。最新SHA256={sha(HERE / 'generation/Up/local_revision_03/raw.png')}。全部原件、三份本地修订、processing.json、前后放大对照与retouch脚本保留。本地修订不是新的AI结果，原Up与最新全图及局部对照已实看。最新仍是候选，不是透明分件或最终绑定通过；未建art_selection，未stage。

anatomy_plan和Up/Down提示已按真实源图改好，初始generic副本保留。character_step.py prepare已经执行，不重跑；prepare_reviewed_20261029.py完成计划/提示但首次合同对象序列化错误和末尾打印失败，随后capture_contract_20261029.py保存有效source_animation_contract_complete_20261029.json。早期source_animation_contract_20261029.json仅历史，不把它当结构化合同，也不重跑会覆盖备份的prepare脚本。

原合同：Ready0.5s/loop/24float，Walk0.5s/loop/33float，Attack0.5s/nonloop/48float，Death0.416666657s/nonloop/39float；四clip均0PPtr。Attack SetHead0@0、SetHead1@0.166666672、Event("Attack")和SetHead0@0.333333343；Death SetHead2@0。参数Attack trigger、Action bool、State int、Speed float。完整keys与层级以complete文件为准。保留原侧向所有曲线、时长、loop、事件、状态机及回收复用合同，只追加纵向适配。

## 4. 工程身份、范围和现有生产保护

实际目标E:/MyTowerGame / Unity2022.3.62f3c1 / unityMCP / http://127.0.0.1:8088/mcp。AGENTS里的FreedomTower_1/D:/8082是旧信息，8082现在属于FishTestGame，8080属于CatchFish；不改根规则、不操作其他工程。版本以ProjectVersion文件现场为准。桌面控制必须先询问用户，本轮未使用。

需要Unity操作时，先读mcpforunity://custom-tools及instances，动态选择完整MyTowerGame ID并set_active_instance，再读project/info核路径和版本；新会话/重连/域重载重核。桌面MCP握手失败可审阅复用mcp_call.py Client.identity()直连HTTP8088，loopback禁代理。离线按项目规则自主恢复已有服务/桥接，不抢端口、不杀进程、不依赖离线服务启动自身。

开工时已保存Assets/Packages/ProjectSettings/Luban共5585文件完整路径SHA基线和battle/source/atlas及各meta六保护，六项匹配最初production_fingerprints。收尾全路径并集审计5585→5585，changed/added/deleted全部空，无Reporter时间戳例外，源文件、共享C#、原Wolf合同、其他角色和配置均无本轮漂移；原基线/首批批准/AllGIF清单SHA不变。历史全局scope失败未重审，不宣称全局PASS。原git改动保留，不能以HEAD回滚消除差异。

最新{inspection['unity_release']}通过动态身份确认，clean Boot、非Play、非dirty、review/balance/manual=false，compile/reload/update/tests=false、ready=true、scriptCompilationFailed=false，error与errorCS返回0。没有生产改动、C#改动、stage/install/Verify/Play/runtime/record，没有新GIF，没有构建部署。Unity已空闲安全交还；没有请求刷新或编译。

Docs共享generate.mjs仅增加当前WinterWolfTypeA Down Curl55的standing恢复01/02，以及仅Down02使用SHA绑定无密钥完整上传401证据的既有代理传输。原owner/token/原授权/证据SHA/无成功/计数保护保留。原文件备份和完整patch见docs_tooling证据，不擅自移除防重保护或扩张为通用无限重试。

## 5. 恢复后逐阶段继续，不跨阶段宣称完成

所有流水线Python用 C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8，子进程用sys.executable；不使用PATH Python3.13 isolated。图片任务遵循已读imagegen与full-output-enforcement技能，用户授权AIHub优先于工具默认路由。AIHub https://aihub.dog/v1，既有生成器gpt-image-2/medium/n1/1536x1024；密钥仅运行时从环境或C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml DPAPI读取，仅发送aihub.dog，不明文输出/落盘/跨域重定向。保存每个request/raw/result/uncertain/error，任何请求前核在途与已成功结果，不删旧请求或安装清单绕过防重。

恢复出有效Down后先实看完整Down及Up候选，审正确正脸/前趾与纯后脑/后跟、原色/胸毛/尾根、无影、清晰描边及完整连接。确认后再选art_selection；character_step.py stage WinterWolfTypeA前核暂存不存在，不无条件重跑full stage。按实际分件清品红透明背景，检查边缘污染、描边、孔洞、透明连接根、Atlas切片、PPU、pivot、render order与完整四向离线组合。名义格界不是裁掉耳足尾的理由，必要局部修补必须留原始来源/范围/SHA与修前版本。保留原左右侧图，原有四腿按对角配对、短步幅、轻躯干摆及克制尾摆；Up头在远端上方、肩毛连接，下方棕臀与尾根；Down远臀上方、白胸与头朝下覆盖，尾在臀后。

安装前复核生产全指纹、六保护、正确Unity身份和空闲；Directions.meta位于目录外必须单列。若已有installed_manifest走实际恢复/返修路径，不删除清单。只安装当前角色Builder并Verify，记录最终生产全指纹后才运行。本任务两轮真实Play已有授权，先日志再状态/占用，不覆盖脏场景、不强停他人测试。原生普通死亡与指定Up死亡每轮84PASS0FAIL，保存全部actual_frames.jsonl/actual_runtime_checks.txt/真实PNG及Unityframe、normalizedTime、realtime和SHA，最终runtime_summary绑定实际最终版本，总168PASS0FAIL。恢复原干净场景并确认无录像/测试/编译占用。

覆盖四向步态、纯纵向/斜向滞回、近零保持、连续转向相位、原生状态和头事件、攻击/受击/致死白闪结束、完整死亡旋转收缩淡出、自动回收/同实例复用、暂停恢复及1x2x3x和适用飞行。不得用Animator.Update或离线合成冒充真实Play；程序PASS而画面不对仍须保留旧版本返修并重跑最终两轮。

C#若确需修改，先读实现/调用/生命周期，同批改完再8088 MCP refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，1–2秒轮询compile/reload/update=false且ready=true，再read_console(error/errorCS)及scriptCompilationFailed=false；编译期间不写代码，断线先等约5秒、重连重核，保留历史错误不清控制台。无UnityC#改动不为收尾额外改脚本或编译。

build_runtime_media.py可能写死0.5s；本角色原Walk正好0.5s，但仍需解码GIF累计时长及真实相位，避免非10ms帧间隔截短。必要时仅当前角色Docs保留修前GIF并做累计10ms量化，记录量化误差，不合成姿态、不改共享脚本；不照抄WinterOgre670ms或前任修订计数。

实际审最终两轮four_directions/runtime strip、足够真实时序PNG和最终GIF编码帧，1–2图/次，原件留盘。审图crop不能裁完整耳/足/尾；必要另看未裁nativePNG和GIF整帧。不能播放就准确记录抽样范围，不能声称实时播放或全帧通过。最后使用现有record_review流程，UTF8视觉备注先写文件再传参；最终只能completed_pending_user_art_review、user_approved=false，用户明确批准才可批准。record调用collect_gifs集中归档所有实际GIF，核源与集中副本SHA，区分最终/否决/历史，不固定每角色12或固定总数。现在1642保持，本轮无新GIF无需为阻塞重跑record或collect。

## 6. 队列、恢复后的唯一后继和禁止事项

剩余7项已递归核查：PossessedWarg79旧Down结果不明，只有Up且无stage/install/runtime；WinterWolfTypeA113为当前Down三不明；WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118均not_started且各只有8个嵌套reference文件，无生成、暂存、安装或运行阶段。没有能独立交付的恢复阶段。正常下一个未开始角色是WinterWolfTypeB114，但当前需要同一失败图像POST，不能把它当付费探针或创建空转后继。因此链已blocked，保留当前owner/token，无新聊天，不宣称后台继续。

当前角色真正完成或新现场出现可独立恢复的阶段后，安全交还Unity，重读实时items，优先可恢复已开始项，再选最低index未开始项。保留PossessedWarg未知请求及任何前任消耗。写带时间总结，更新README、主执行prompt实时块、完整UTF8 NEXT和progress；仅确有可执行唯一后继时chain=handoff_ready并生成新token。现场list_projects核E:/MyTowerGame，唯一create_thread(target={{type:"project",projectId:现场ID,environment:{{type:"local"}}}},prompt:完整新提示)，不fork、不覆盖model/thinking。明确成功响应落盘后父最后写链转active新owner/token并停止工程写入，一次有界wait_threads确认启动，最终只用真实created-thread；创建结果不明先查实际响应/聊天，不重复创建。全部108有效完成或只剩真实阻断时停止。

禁止git pull/reset/clean/checkout覆盖、commit/push、构建/部署、删除资源/场景、自动改关卡/敌人/登记数值表、直接写Assets/ConfigJson或Assets/Gen、恢复声音、子代理/并行角色/fork/定时器/自动化、长期memory修改、模型/推理设置覆盖。保留首批10项用户批准及所有历史失败、否决和冻结证据。完整prompt交付一个UTF8文件，不分段、不省略、不使用占位符。
'''
assert '…' not in full_prompt and 'TODO' not in full_prompt
recovery_prompt_path.write_text(full_prompt, encoding='utf-8')

handoff = f'''# WinterWolfTypeA(index113) 阻塞交接 — {NOW}

本角色未完成。进度保持101/108，AllGIF保持1642。唯一owner为{chain['owner_thread_id']}，token为{TOKEN}；串行链停止于共同图像服务阻塞，没有创建后继，没有转移所有权。

## 实际完成与未完成

已同步当前规则、版本、流水线/调用/生命周期、原始完整atlas与完整源参考、战斗和源层级、四条原生clip完整关键帧及事件。原图身份为棕橄榄背/赭斑/高尖棕耳/白眼深瞳/宽白胸毛/白爪/整条象牙taupe蓬尾，无项圈鞍背刺。准备计划/UpDown提示，保留原generic副本；prepare只执行一次。

Up初图HTTP200，1536×1024 RGB；原SHA {sha(HERE / 'generation/Up/raw.png')}。原图、局部比较及最新完整local_revision_03已实际查看。局部修订去躯干重复耳、闭合白肩毛、清后趾线及斑驳，最新后跟是平整象牙cel填色且保留四像素外描边；SHA {sha(HERE / 'generation/Up/local_revision_03/raw.png')}。修订是本地raster，不是新AI结果，不是最终美术批准；所有旧稿/processing和脚本保留。没有art_selection、stage、安装、Verify、Play、runtime、record或新GIF。透明度/pivot/PPU/布局/动画未通过验收。

有效原生合同source_animation_contract_complete_20261029.json：Ready0.5loop/24float、Walk0.5loop/33float、Attack0.5nonloop/48float、Death0.416666657nonloop/39float，均0PPtr；Attack头事件0/.166666672/.333333343，末时刻Attack事件；Death头2@0，参数Attack/Action/State/Speed。早期ToString序列化失败文件保留，仅使用complete。不要重跑prepare_reviewed或覆盖备份。

## 真实阻塞

Down初次Curl55、revision_01 Curl55、既有代理revision_02 Curl52；三次都没有HTTP、raw/result或查询ID，结果与可能费用全部unknown。保存全部prompt/request/console/uncertain和SHA，详细见[{report_path.name}](../WinterWolfTypeA/{report_path.name})。standing原用户“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”已live核原消息；两个额外恢复2/2已消耗，这是保守代理执行上限而非用户金额预算。前任所有计数不变，不再付费重发或换角色探测。

models/usage认证200及余额有效不能证明image POST恢复或旧请求免费。无密钥直连65331bytes后Curl55；既有代理434497bytes完整上传401/TLSverify0，真实Down02仍空响应。没有改系统代理、没有收尾付费调用、没有在运行的本角色生成器。需要恢复既有结果/关联或获得具体provider处置；确需新请求先诊断解决认证POST故障并记录新的有限执行决策，本报告不新增次数。

## 生产审计、工具变化与Unity交还

完整Assets/Packages/ProjectSettings/Luban路径并集5585→5585，新增0/删除0/修改0；battle/source/atlas及各meta六保护仍与本轮开始及原始指纹匹配，原Wolf共享动画/全部C#/其他角色/配置均未漂移，未套用Reporter时间戳例外。原基线、原始指纹、首批用户批准与AllGIFmanifest SHA不变；历史全局scope失败不重分类。见[{Path(inspection['scope']).name}](../WinterWolfTypeA/{Path(inspection['scope']).name})。

唯一共享脚本变化是Docs/generate.mjs：仅当前Down Curl55 standing01/02及仅Down02 SHA绑定无密钥401证据的既有代理传输，保留owner/token/原授权/证据/次数/已有成功防重；备份/patch/两修改记录保留，Unity C#未改。

Unity通过custom-tools→instances→完整动态ID→set_active_instance→project/info核E:/MyTowerGame/2022.3.62f3c1，真实路由8088。最新Boot非Play/非dirty、全部已加载scene干净、compile/reload/update/tests=false、ready=true、failed=false、review/balance/manual=false，error与errorCS0。没有强制切换场景或Play，没有Refresh/编译请求，安全交还。见[{Path(inspection['unity_release']).name}](../WinterWolfTypeA/{Path(inspection['unity_release']).name})。8082/FishTestGame与8080/CatchFish未操作，桌面未控制。

## 剩余项与下一步

递归核查PossessedWarg79仍旧Downunknown、只有Up，无可独立安装运行；WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118各8个嵌套reference，无生成/暂存/安装/运行。正常后继WinterWolfTypeB也依赖同一图像服务。遵循CONTINUATION_PROTOCOL“全部可独立工作均耗尽时停止并报告”，不创建空聊天或付费探针。见[{Path(inspection['successor_assessment']).name}](../WinterWolfTypeA/{Path(inspection['successor_assessment']).name})。

完整恢复说明在[NEXT_ENEMY_TASK.md](../NEXT_ENEMY_TASK.md)，同内容独立副本[{recovery_prompt_path.name}](../WinterWolfTypeA/{recovery_prompt_path.name})。只读恢复先核owner/token及在途/现有结果；不重跑prepare/stage、不给三个旧请求改成失败免费。恢复后仍需完整Down审核、透明分件/布局、单角色安装、最终两轮真实Play168PASS0FAIL、真实PNG/GIF审阅、record/归档与最终范围审计，只能待用户美术审核。没有宣称这些阶段已经执行。

旧README/主prompt/progress/chain/NEXT的本轮收尾前版本完整保存于{rel(backup)}。本次没有提交、推送、构建部署、改Luban、改声音、删除生产资源、子代理、并行角色、fork、定时器或memory修改。
'''
handoff_path.write_text(handoff, encoding='utf-8')

item.update(status='blocked', blocked_at=NOW, blocked_reason=reason,
            blocked_record=rel(report_path), current_stage='Down_unknown_after_bounded_network_recovery',
            user_approved=False, up_review=inspection['up_review'],
            source_animation_contract=report['source_animation_contract'],
            standing_recovery_used=2, standing_recovery_limit=2,
            unknown_request_count=3, production_modified=False,
            staging='not_executed', install_verify='not_executed', runtime='not_executed',
            record='not_executed', new_gifs=0, successor_created=False,
            scope_record=inspection['scope'], unity_release=inspection['unity_release'],
            handoff_file=rel(handoff_path))
progress.update(status='blocked', current='WinterWolfTypeA', updated_at=NOW)
progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

live = (f'{NOW} WinterWolfTypeA113阻塞，101/108、AllGIF1642保持。Up首次HTTP200，完整raw及本地raster03已审，去重复躯干耳/后趾并平整后跟，未作最终分件或绑定验收；无art_selection/stage/install/Verify/Play/runtime/record/新GIF。'
        'Down初次与01均Curl55，02经已审既有代理仍Curl52；三次无HTTP/raw/result/queryID，结果及费用unknown。standing额外2/2已消耗（代理保守限次，非用户金额预算），保留所有旧请求及前任计数，不再付费探测。'
        'models/usage200和无密钥完整上传401不证明认证imagePOST恢复。完整路径并集5585→5585，新增/删除/修改0，六保护/原Wolf/共享C#/其他角色/配置和原批准/基线/GIF清单不变，未使用Reporter例外。'
        'Unity2022.3.62f3c1/8088动态正确身份，clean Boot非Play/全部场景干净/全空闲/ready=true/failed=false/error与errorCS0，未请求刷新编译。'
        '递归核剩余：PossessedWarg79旧Downunknown；WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118各reference8且无独立生成/暂存/安装/运行，不能作为同一故障服务的付费探针。'
        f'chain=blocked保留owner={chain["owner_thread_id"]}及token={TOKEN}，未创建后继。阻塞报告{rel(report_path)}；交接{rel(handoff_path)}；完整恢复入口NEXT_ENEMY_TASK.md。WinterWarg112已record待用户审核和所有历史证据保留，不把本角色标成完成。')


def replace_live(path, begin, end):
    text = path.read_text(encoding='utf-8-sig')
    assert text.count(begin) == text.count(end) == 1
    prefix, rest = text.split(begin, 1)
    old, suffix = rest.split(end, 1)
    path.write_text(prefix + begin + '\n' + live + '\n' + end + suffix, encoding='utf-8')


replace_live(readme_path, '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->')
with readme_path.open('a', encoding='utf-8') as output:
    output.write(f'\n\n{NOW} 串行链阻塞记录：WinterWolfTypeA113的Up初图和本地修订已保存，Down三次传输结果及费用不明，额外恢复2/2已消耗；未改生产、未安装运行，进度101/108和AllGIF1642保持。5585文件全路径并集零变化、六保护不变；8088正确Unity实例clean Boot空闲无错误。其余项无可独立恢复阶段，保留owner/token并停止创建后继。完整交接[{handoff_path.name}](Remaining_20261024/conversation_handoffs/{handoff_path.name})，恢复以NEXT_ENEMY_TASK及实时chain/progress为准。\n')
replace_live(prompt_path, '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->')
next_path.write_text(full_prompt, encoding='utf-8')

# Last scheduling write: keep the current owner/token, stop the chain, preserve dispatch history.
chain['historical_stops'].append({
    'character': 'WinterWolfTypeA', 'blocked_at': NOW, 'blocked_reason': reason,
    'handoff_file': rel(handoff_path), 'recovery_file': rel(report_path),
    'owner_thread_id': chain['owner_thread_id'], 'dispatch_token': TOKEN,
})
chain['stage_history'].append({
    'character': 'WinterWolfTypeA', 'status': 'blocked',
    'current_stage': item['current_stage'], 'closed_at': NOW,
    'owner_thread_id': chain['owner_thread_id'], 'dispatch_token': TOKEN,
    'final_evidence': rel(report_path), 'handoff_file': rel(handoff_path),
    'total_uncertain': 3, 'standing_additional_used': 2, 'successor_created': False,
})
chain.update(state='blocked', current_stage=item['current_stage'], current_blocked=True,
             blocked_reason=reason, stop_reason=reason, stopped_at=NOW, updated_at=NOW,
             completed_count_snapshot=101, successor_created=False, dispatch_ready_for=None,
             previous_handoff_file=chain['last_handoff_file'], last_handoff_file=rel(handoff_path),
             handoff_sha256=sha(handoff_path),
             previous_progress_sha256_at_stop=chain.get('progress_sha256_at_stop'),
             progress_sha256_at_stop=sha(progress_path), recovery_file=rel(report_path),
             resume_character='WinterWolfTypeA', resume_stage=item['current_stage'],
             unity_release_file=inspection['unity_release'], successor_assessment=inspection['successor_assessment'],
             last_stage_evidence=rel(report_path), blocked_owner_retained=True,
             no_successor_creation_reason='No independent recoverable delivery phase; do not use the next character as a paid service probe.')
chain_path.write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Documentation consistency checks only; no repeat production scans, builds or runtime tests.
assert next_path.read_bytes() == recovery_prompt_path.read_bytes()
assert load(progress_path)['completed_count'] == 101
assert load(chain_path)['state'] == 'blocked' and load(chain_path)['dispatch_token'] == TOKEN
for old in load(backup / 'progress.json')['items']:
    if old['name'] != 'WinterWolfTypeA':
        assert old == next(x for x in load(progress_path)['items'] if x['name'] == old['name'])
assert load(chain_path)['dispatch_history'] == load(backup / 'conversation_chain.json')['dispatch_history']
save_new(HERE / ('blocked_closeout_index_' + STAMP + '.json'), {
    'closed_at': NOW, 'report': rel(report_path), 'handoff': rel(handoff_path),
    'recovery_prompt': rel(recovery_prompt_path), 'next_prompt_sha256': sha(next_path),
    'progress_sha256': sha(progress_path), 'chain_sha256': sha(chain_path),
    'docs_backup': rel(backup), 'owner_retained': chain['owner_thread_id'], 'token_retained': TOKEN,
    'completed_count': 101, 'allgif_count': 1642, 'successor_created': False,
    'other_progress_items_unchanged': True, 'dispatch_history_unchanged': True,
})
print(json.dumps({'status': 'blocked', 'report': rel(report_path), 'handoff': rel(handoff_path),
                  'resume_prompt': rel(recovery_prompt_path), 'completed_count': 101,
                  'allgif_count': 1642, 'successor_created': False}, ensure_ascii=False))
