# WinterOgre(index111) 阻断恢复：完整执行入口

在 `E:/MyTowerGame` 继续敌人四方向串行任务。当前真实状态是共同图片网络阻断，不能把本文件当成新增付费请求、重置上限或创建下一聊天的指令。先按以下完整说明读取并恢复既有阶段。

## 当前所有权和进度

- chain.state=blocked；保留owner_thread_id `01a18619-6aa0-7a31-ac62-10a82077950b`。
- dispatch_token `winterboar-to-winterogre-20261029_131318-14b528b1-8990-455f-8069-d7ea49019046`；当前唯一角色WinterOgre(index111)，user_approved=false。
- 进度99/108：99项completed_pending_user_art_review，2项blocked（PossessedWarg79、WinterOgre111），7项not_started（WinterWarg112、WinterWolfTypeA113、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118）。108是授权数量，终项Zombie118。
- AllGIF1594，本角色新增0。没有后继聊天、后台代理或定时器。旧生成/审核/批准/失败历史全部保留。
- state=blocked期间只读检查文件和既有服务结果；不能改生产、操作Unity或新增付费。满足已有恢复条件后，原owner明确保存恢复评估再转active；换聊天必须有用户授权的所有权交接，不凭超时抢锁。只有active、owner和token同时匹配才可生产/Unity/付费操作。

## 必须先读的当前磁盘

1. `E:/MyTowerGame/AGENTS.md`、`ProjectSettings/ProjectVersion.txt`。
2. `Docs/EnemyDirectionReview/README.md`、`PREFAB_CHANGES_SUMMARY_20261026.md`。
3. `Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md`、`CONTINUATION_PROTOCOL_20261026.md`、`IMAGE_RELAY_RECOVERY_20261026.md`。
4. 同目录实时 `conversation_chain.json`、`progress.json` 和本文件；历史数字不作为当前状态。
5. `standing_network_recovery_authorization_20261028.json`、`TreasureChest/standing_recovery_application_20261028.json`、`WinterOgre/standing_recovery_application_20261029_Up.json`。
6. `Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_134607_WinterOgre_blocked.md`。
7. `Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/blocked_generation_recovery_20261029_134607.json`、`WinterOgre/unity_release_blocked_20261029_134607.json`、`WinterOgre/scope_incremental_blocked_20261029_134607.json`、`WinterOgre/successor_assessment_blocked_20261029_134607.json`、`WinterOgre/docs_tooling_change_20261029_134607.json`。
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
