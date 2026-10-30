# 敌人剩余预制体四方向美术补全与动画接入：续作可执行 Prompt

请在 Unity 工程 `E:/MyTowerGame` 中，继续完成已获授权的剩余敌人预制体四方向美术补全、方向接入、动画优化、逐角色真实运行验证和审核资料归档。任务不是从头重新设计方向系统：先复核并沿用工程内已经完成的成果、共享代码、脚本、角色进度和用户已批准版本。

本文件是 2026-10-24 后续工作的当前执行入口。它汇总此前原始任务 prompt、首批用户审核、三角色动画返修、BlueScorpion 尾巴反复修正、后续全部预制体授权、集中 GIF 要求和本轮实际进度。若历史 README、冻结 progress 文件、旧生成图或旧对话描述与本文件及当前生产文件冲突，以当前用户明确指令、有效的最终批准版本、`Remaining_20261024/progress.json` 和现场 Unity 工程身份为准。保留历史证据，不把旧状态改写成新验证。

## 1. 授权范围与停止条件

1. 用户已经明确批准 AdvancedHen 示例方案，并确认首批 10 个角色修改通过审核；随后明确要求“继续处理剩余的所有预制体”，并要求所有生成 GIF 集中到一个文件夹。可以继续顺序处理队列内全部 108 个目标，不需要每做完一个角色就停下来等待新的批量授权。
2. 已确认通过的 10 个角色是 Bat、BattlePanther、Bear、BearMounted、BlackBear、BlackBoar、BlackWolf、BlueScorpion、Boar、BoarMounted。它们的批准范围包含 BlackBear/BlackWolf 动画返修，以及 BlueScorpion 的最终背面参考尾巴修订。AdvancedHen 是先前示例，也不属于当前 108 个待办目标。
3. 逐角色生成、安装、实际运行、查看真实画面、记录和归档；发现错误时先修复当前角色，再继续下一个。等待用户美术审核不构成停止处理剩余队列的理由。只有遇到工程身份不符、并行任务占用 Unity、生产指纹漂移无法协调、实际验证失败或其他会导致不安全覆盖的阻断时才暂停受影响操作，并清楚记录原因。
4. 每个角色记录为 `completed_pending_user_art_review` 只表示实现与程序验证完成，不表示用户已批准美术。不得把自动检查 PASS、内部视觉检查或历史批准扩大成新的用户批准。整批完成后提交可浏览的成果和总览，等待用户对本批剩余角色美术验收。
5. 不覆盖、删除或伪造已有证据；失败版本也保留并标注。不能因旧记录写着“等待进一步指令”而撤销用户已给出的继续授权。

## 2. 已知进度与立即续做位置

权威队列：`Docs/EnemyDirectionReview/Remaining_20261024/progress.json`，总计 108 项，按其 `index` 和 `name` 逐项恢复。当前进度快照：`completed_count=6`，当前角色 `Butcher`，前 6 个为 BugQueen、Bull、BullMounted、BullyRooster、Bunny、Burro，均已完成两轮实际 Unity Play 检查，各 `168 PASS / 0 FAIL`，但尚未标成用户美术批准。其后尚有 102 项未完成，Butcher 已生成、修订、切片并完成离线拼装，状态为 `staged_pending_visual_check`，还没有安装到战斗预制体或实际运行验证。

从 Butcher 的已准备状态继续，不要重新生成或覆盖已有合格成果：

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 'Docs/EnemyDirectionReview/Remaining_20261024/character_step.py' install-and-review Butcher
```

随后打开并实际检查：

- `Docs/EnemyDirectionReview/Remaining_20261024/Butcher/runtime_r01/four_directions.png`
- `Docs/EnemyDirectionReview/Remaining_20261024/Butcher/runtime_visual_strip.png`
- 该角色 `runtime_r01`、`runtime_updeath_r01` 原始帧、运行检查和 GIF

重点核对 Butcher 的右手菜刀、围裙正背面、矮壮体型、双臂双腿连接、背面结构、攻击表现、死亡淡出和对象池复用。确认真实帧视觉与程序检查均合格后记录实际观察备注：

备注必须描述检查过的实际画面，不要复制预期文案冒充检查。使用该实际备注作为 `character_step.py record Butcher` 的第三个参数。`record` 会检查两轮运行结果并触发 GIF 集中归档。完成后从最新 `progress.json` 读取下一个目标；不得依赖手写的旧序号或猜测名称。

后续每个角色均从最新 `progress.json` 动态读取名字。逐条执行并在提示的视觉检查点停下来检查，不要把整段命令一次性连续执行：

```powershell
$python = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$step = 'Docs/EnemyDirectionReview/Remaining_20261024/character_step.py'
$progressPath = 'Docs/EnemyDirectionReview/Remaining_20261024/progress.json'
$name = (Get-Content -Raw $progressPath | ConvertFrom-Json).current
& $python -X utf8 $step prepare $name
# 检查新生成的 anatomy_plan.json、源参考图和 Up/Down prompt，再分别请求两个方向。
& 'Docs/EnemyDirectionReview/Remaining_20261024/generate_character.ps1' -Character $name -Direction Up
& 'Docs/EnemyDirectionReview/Remaining_20261024/generate_character.ps1' -Character $name -Direction Down
# 查看两方向原图结果后再继续；必要时用新 revision 返修，不覆盖已有请求。
& $python -X utf8 $step stage $name
# 查看离线四方向拼装和布局，合格后才安装并启动两轮真实运行。
& $python -X utf8 $step install-and-review $name
```

按 `prepare`、参考检查和个体 anatomy plan、Up/Down 生成、离线去底/切片与布局、离线静态检查、单例安装、两轮真实运行、实际帧视觉审阅、记录归档的顺序操作。角色专属目录已有 `request.json`、`raw.png` 或 revision 时，先判断上次请求是否已有结果；不能盲目重复可能计费的 Image API 请求。返修使用新的 revision，保留旧输入、结果、patch 和说明。

`install-and-review` 结束后打开真实帧图和 GIF，完成人工检查，再以实际观察到的内容作为 `character_step.py record` 的最后一个参数。不要在未查看媒体时提前执行记录。

## 3. 工程和当前工作边界

- 目标根目录 `E:/MyTowerGame`，当前磁盘 `ProjectSettings/ProjectVersion.txt` 确认 Unity `2022.3.62f3c1`。只使用 MyTowerGame 的 `unityMCP` / HTTP Local `http://127.0.0.1:8082/mcp`，不使用 CatchFish_Android 的 Unity 2020/8080。
- 用户在当前会话提供了 MyTowerGame 专用 `AGENTS.md` 规则。此前现场读取到的磁盘根 `AGENTS.md` 写有其他项目根目录；每次必须以本轮明确的 `E:/MyTowerGame`、版本文件和正确 MCP 实例核对工程身份，不得因为文件内容或窗口焦点切到别的工程。发现规则文件仍不匹配时记录该差异并按当前用户提供的 MyTowerGame 规则工作。
- 首次连接、重连、域重载、切换实例后，读取 `mcpforunity://custom-tools` 和 `mcpforunity://instances`，从现场列表选取 MyTowerGame 的完整 `Name@hash` 并调用 `set_active_instance`，再读取 `mcpforunity://project/info`，确认 `data.projectRoot` 和版本完全匹配。`Remaining_20261024/mcp_call.py` 也会动态发现实例并执行身份核对；不要硬编码旧实例 ID。
- 每轮开始读取最新规则、任务进度、相关资源与已有改动；保存本轮本地基线/指纹。同步是读取当前磁盘，不代表从远端 pull。绝不执行 `git pull/reset/clean`，不覆盖其他任务或用户改动。修改前后差异以本地基线为准。
- Assets/Unity Editor 可能存在其他并行任务。每次安装、刷新、编译或进入 Play 前检查编辑器、场景是否已保存、是否正在编译或被录像/验证任务使用。遵守已有协调与安全移交；不能把时间过去、对方无响应或单次工具超时解释成交接。
- 用户此前已明确授权：本批剩余预制体可继续处理；此前 L02 录像任务完成后，用户也已明确回复 Unity 交回并授权接入实测。但若现场出现新的 Unity 占用，仍需先协调，不得中断对方运行、录制或切换 Play 状态。
- 目前工作区存在其他文件的脏改动，开始时重新检查 `git status` 和涉及文件内容，只改本任务必要范围；不要还原无关内容。
- 禁止脚本批量改写 `Luban/Config/Datas/Levels/L01..L30/**`、`EnemyData.xlsx`、`__tables__.xlsx`；禁止直接写 Luban 导出产物 `Assets/ConfigJson/**` 和 `Assets/Gen/**`。本美术任务不修改关卡、敌人数值或战斗配置。

## 4. 美术设计总规则

### 原角色设计和视角

1. 每个角色都先检查当前原始图集、从序列化源预制体得到的完整参考图、战斗 prefab、控制器、动画、事件和其余节点。原始图集未必是完整行走角色；不得只凭一张侧图猜测缺失器官。
2. 使用角色当前原图作为颜色、描边、比例、材质、明暗、表情、装备和轮廓唯一基准。用户参考图可用于对应的结构/姿态方向，但不照搬其色板、材质、机位、文字或水印。旧生成版本被否决后，旧图只作历史，不再作为设计目标。
3. `Up` 是角色背向屏幕上方移动的背面，`Down` 是角色面向屏幕下方移动的正面；按当前固定相机的观察方向设计真实正背视角。不能旋转、翻转、拉伸或镜像侧面图伪造正背面。左右使用既有侧图和水平镜像规则。
4. 正背面分别呈现正确的头、躯干、胸腹、腿/足、尾巴、翅膀、甲壳、装备和附肢；关节接入、视线/足尖方向、前后遮挡、地面落点和身体重心符合角色解剖。不得出现悬空、断肢、空心根部、穿插、背面脸、重复附肢或不属于原角色的器官。
5. 每个角色的身体比例、运动方式、腿数、器官朝向、装备及尾巴必须按自身原设计单独制定，不将模板的颜色、部件位置、尾部造型或动作参数复制给别的角色。生成图必须去除纯色背景为真实透明，检查抗锯齿边缘、色污染、透明孔、切片、Pivot、PPU、渲染顺序和导入设置。新美术与方向资源放在该角色自己的 `Directions/` 目录并保留现有 GUID/Sprite ID 和无关切片。

### 无地面阴影

逐个完成时，Left、Right、Up、Down 四个方向及攻击、受击、死亡和对象池复用后都不得有角色地面阴影。按角色 prefab 结构移除战斗呈现中的阴影节点或阴影 Renderer，并确保方向接入、Builder 重建和生命周期不会恢复阴影。不得把阴影画进新增 PNG。保留可能仍被其他角色引用的原始资源。

### 专属步态和动作质量

1. 上下方向提供循环行走，步态与动物类型和肢体数量相符；步幅、抬足、落足、身体起伏和左右/前后遮挡自然，循环首尾连续。飞行、漂浮和无足爬行类使用符合原设的推进动作，不硬套四足走路。
2. 头、躯干、翅膀、尾巴、钳子、触角、装备和远近侧肢体可以错相跟随，但必须连接正确并服从同一重心。转向时保留当前行走相位，不因轻微方向变化反复重播或抖动。
3. 保留当前动作契约和时长；已有 `Idle/Ready/Walk/Run/Attack/Death` 状态按角色实际 Controller 使用，保留 `State`（int）、`Speed`（float）、`Attack` Trigger、兼容 `Action` 参数和原有事件。正常、愤怒、死亡头状态、受击闪白、致死闪白结束、死亡淡出/收缩、自动回收与同一对象池实例复用必须正常。
4. 接入或返修上下行走/攻击/死亡时，不改变原侧面美术的 Action 事件、PPtr 曲线、float 曲线、时长、loop 设置、伤害/碰撞参数、移动参数、根节点、血条、HP 或对象池逻辑。需要独立曲线时生成角色专用动画与 Controller，避免修改共享动作影响其他敌人。
5. 尽量沿用已有 `BaseEnemy.Tick` 和方向组件，不增加不必要的每帧 Update、层级查找、材质实例或分配。出生、纯纵向路径、横纵转向、斜向主轴判断、路径刷新、近零位移保留最后方向、飞行直线和缩放/血条翻转都要正确。

## 5. 从历史返修中已确认的角色专属经验

这些是已批准角色的最终经验，用于理解用户对方向与动作质量的要求；不要重新修改这 10 个角色，也不要把其细节套给新角色。

- **BlackBear**：腿根收进躯干并由身体遮住肩胯，重型四拍步态有明确抬腿、落足和轻微重心变化；攻击先蓄力再前压，左右前肢错时；侧倒死亡时四肢收拢。该角色三类动画都需要顾及腿部衔接、步态、攻击、死亡，而非只调行走速度。
- **BlackWolf**：对角肢体交替，抬腿绕固定关节收回；头与躯干错相；尾轴落在真实尾根并延迟跟随；攻击包含短蓄力和扑咬，死亡时附肢随躯干收拢。
- **BlueScorpion**：前、中、后足分别按身体结构安排朝向与遮挡，交替三足组略有相位差；左右钳与尾部有独立跟随，攻击先张钳蓄力再合击，死亡时收腿、收钳、垂尾。
- **BlueScorpion 最终背面尾巴**：用户连续指出位置、朝向错误；最终参考要求尾巴向上形成高拱，尾梢向外弯而非向内收钩，再按“弯曲再往中间靠一下”将弯钩适度向身体中线收拢。定稿是 `rear_reference_r02_centered_hook`：尾根固定，静态角度 20°，高拱弯钩接近身体中线；不可恢复被否决的朝下、内卷或远离身体侧向伸展版本。只在将来被授权修改 BlueScorpion 时参考最终稿。
- **Bull / BullMounted**：短粗腿的关节在躯干内连接；尾部从后躯自然下垂；BullMounted 的鞍具/马镫按侧面和背面可见位置放置，不能无故放到背部中线，也不能新增骑手。
- **BullyRooster**：保留大金色鸡冠、深色卷尾、折翼和腿部颜色；背向足部要显示合理脚跟/后足，不暴露脚趾正面；翅根藏在躯干下，颈部不能断开。
- **Bunny**：四足兔子采用双后足成对跳跃的特征步态，棉球尾自然并入背面后躯，去除把后脚画成趾部朝后的错误纹理。
- **Burro**：保留长耳、原奶油色口鼻/腹部与斑点；背耳外侧按纯背面处理，不发明鬃毛或肩部突起；窄蹄腿用克制的斜步，尾巴从臀部摆动。
- **BugQueen**：腹甲/背壳是主体轮廓，六足需连接躯干并使用交替三足步态，正背头部按视角区分；不要增加翅、钳或刺。

相应原始记录位于 `Batch01_10/`、`AnimationPolish_20261023/`、`BlueScorpionTailReference_20261023/` 和 `Remaining_20261024/`。复用经验前先看最终 revision 和用户批准记录，不把旧 GIF 或失败 revision 当作最终版本。

## 6. 代码和 prefab 接入限制

- 对每个目标做单角色接入。不得运行全目录怪物导入、批量 prefab 重建或批量移除其余角色阴影。只安装队列当前角色，不在其他角色 prefab 或共享动画上顺手改动。
- 使用已有 `EnemyDirectionalRigBuilder`、`EnemyDirectionPrefabBuilder`、`EnemyDirectionBatchReview`、`EnemyDirectionRemainingCatalog` 和 `EnemyDirectionRemainingMotion` 中已批准/已编译的实现，先读当前版本，确认实际调用和角色配置。不要重复添加组件或另建第二套重复方向系统。
- 每次安装前检查 `install_character.py` 的目标资源、源预制体和原图集基线指纹。遇并行漂移停止覆盖，比较变化并协调。安装脚本发现已有 `installed_manifest.json` 时不得强行覆盖；返修必须通过新 revision 和明确修复流程保留旧证据。
- 保持原 prefab GUID、Sprite GUID、Sprite ID、资源逻辑路径、Prefab 根节点、碰撞器、移动、战斗参数、HP、血条、动画事件接收器和对象池契约。新 PNG、Profile、Controller、动画、材质依赖纳入现有 YooAsset/AssetBundle 收集路径；实际检查收集覆盖，但不得将收集器检查说成发布包回读。
- 共享编辑器 C# 文件已在本轮加入可选角色配置与专属动作曲线支持。只有确实需要改 C# 才修改代码；完成一批代码改动后遵循 `AGENTS.md` 对 8082 的强制刷新、编译等待、错误检查及 `scriptCompilationFailed=false` 验证。编译期间不继续改代码。若只改 PNG/JSON/prefab，也完成正确实例的资源刷新、安装检查和真实运行验证。

## 7. 每个角色的实际验收

1. **安装前核验**：正确实例、非编译/非导入、场景已保存、无 Play/录像/审核器占用、资源指纹无漂移。脚本仅作用于一个角色，安装后保留精确变化清单与 SHA256。
2. **Builder / 静态验证**：单角色构建与 Verify 通过；引用、切片、四方向布局、身体与附肢计数、Controller、Profile、事件接收、依赖/收集覆盖无缺项；左右四向无 Shadow；无 Missing 引用；Prefab 原有非美术组件语义一致。
3. **真实运行验证**：当前流程用 `runtime_runner.py` 对安装后的真实 Prefab 执行两轮 Unity Play：`runtime_r01` 及 `runtime_updeath_r01`（后一轮指定 Up 死亡）。必须每轮 84 项通过，合计 168 PASS / 0 FAIL；异常或断言失败时保留失败现场、修复后使用新的 revision 复测。不得手动 `Animator.Update` 或用离线模拟冒充真实 Play 帧。
4. 覆盖四方向移动和行走相位、连续转向、Idle/Ready/Walk/Run/Attack/Death、正常/愤怒/死亡头事件、受击与致死白闪消退、死亡淡出和收缩、自动回收与同实例再生、纯纵向出生/路径变化/零移动方向保持、暂停跨真实帧恢复及 1x/2x/3x 速度、角色适用的飞行直线行为，以及未启用方向角色兼容性抽查。
5. 记录严格递增的实际 Unity 帧号、原始 PNG 帧、normalizedTime、检查结果、revision 和帧日志 SHA256。等待自动回到非 Play 且审核器停止；不得为了赶进度强制退出对方 Play、切换场景或清除控制台。
6. 至少查看最终安装后生成的 `four_directions.png` 与 `runtime_visual_strip.png`，并播放最终上下行走 GIF、转向 GIF、攻击/受击/死亡/复用 GIF 和暂停/倍速 GIF。人工检查和程序断言分开记录；视觉备注只写实际观察到的内容。视觉或动画不合格时先修当前角色，禁止 record 为完成。
7. 做完且仅在视觉与两个 runtime revision 都通过后执行 `character_step.py record`，并将角色名设为刚核验的 `$name`。它会调用 `record_review.py` 更新该角色进度，再调用 `collect_gifs.py` 更新总 GIF 目录。随后复查进度、归档和计数，并按新进度进入下一角色。

### Unity 验证路由

按本工程 `AGENTS.md`：读取 `mcpforunity://editor/state`；需要刷新/编译时调用 `refresh_unity(mode="force", scope="all", compile="request", wait_for_ready=true)`；每 1～2 秒检查 `is_compiling`、`is_domain_reload_pending`、`is_updating` 与 `ready_for_tools` 直到就绪；用 `read_console(action="get", types=["error"], count="50", format="json")` 检查错误，必要时分页和过滤 `error CS`；用 `execute_code` 探测 `UnityEditor.EditorUtility.scriptCompilationFailed` 应为 false。编译/域重载短暂断线先等约 5 秒，之后重新选择实例并核对工程身份。不要清空控制台掩盖历史错误。

## 8. GIF 集中目录和证据归档

- 所有历史、最终、返修、准备和被否决方案的 GIF 都集中平铺复制到 `Docs/EnemyDirectionReview/AllGIF/`，入口为 `index.html`，清单为 `manifest.json`，说明为 `README.md`。用户要求所有 GIF 都集中查阅；不能只收录最终方案。
- 归档脚本：`Docs/EnemyDirectionReview/Remaining_20261024/collect_gifs.py`。保留所有来源文件，不移动、不删原件；用来源相对路径生成含角色/版本信息的文件名并记录 SHA256。若同名且内容不同，脚本应产生 hash 后缀，不覆盖内容。
- 每次角色记录后确认集中目录已重建、数量和清单正确、`index.html` 可浏览；若新增媒体不是由 record 流程生成，主动运行收集脚本。归档状态如实标成“当前审核版本”“历史或准备材料”或“已否决历史方案”，状态仅供索引，不代表用户审批。
- 当前进度快照的集中目录有 105 个 GIF；每个已完成角色的两轮真实验证合计通常追加 12 个运行 GIF。实际总数以重建后的 `manifest.json` 为准，不手写假数字。
- 每个角色目录保存生成 prompt、请求与返回、处理记录、原图/分件、布局、安装前后指纹、Verify 结果、两轮原始帧、运行检查、媒体清单、静态四方向图、可视 strip、异常/修订记录和最终人工视觉备注。`progress.json` 是当前续跑状态；绝不因重新生成 prompt 抹掉既有状态。

## 9. 单角色阶段记录与最终交付

实时将状态写入 `progress.json` 和角色目录，至少区分 `not_started`、`reference_prepared`、`staged_pending_visual_check`、`runtime_complete_pending_visual_check`、`completed_pending_user_art_review`、`user_approved`、`blocked`。只有用户明确审核通过后才写 `user_approved`。任务中断时状态必须能通过 `progress.json`、角色 revision、指纹和原始运行媒体恢复。

若任何角色失败或阻断，记录名称、阶段、错误、已完成内容、资源版本、revision、Unity 状态、指纹漂移和可执行下一步；不静默跳过。共享代码变化需评估对此前已完成角色的影响并做必要回归，不要为了记录状态改写冻结的历史证据。

全部 108 项完成后，交付：

1. 用户可直接浏览的 [GIF 总览页](../AllGIF/index.html) 和正确总数；所有 GIF 的来源、版本、哈希和审核分类完整。
2. 每个角色的四方向静图、实际行走/转向/攻击死亡等 GIF、`168 PASS / 0 FAIL` 或如实记录的例外、SHA256 和进度状态。
3. 修改文件、范围审计、编译/错误日志结果、Prefab 语义保护、依赖与收集覆盖结果；清楚列出未运行的 APK/真机、发布包回读、长期战斗或其他测试，不夸大结论。
4. 失败项、待修复项、当前批准状态和需要用户美术决策的问题。没有明确用户回复时，不把待审核角色写成用户已批准。

## 10. 本次继续任务的开工动作

先确认这份 prompt、`progress.json`、`Butcher` 已生成资源、Unity 当前身份/状态和 `AllGIF/manifest.json` 之间一致；确认现场没有新的 Unity 占用后，从 Butcher 的 `install-and-review` 开始。不要重新做已完成的 BugQueen、Bull、BullMounted、BullyRooster、Bunny 或 Burro，也不要重新运行已批准前 10 个角色的生成或接入。

当记录完一个角色后，持续读取队列并处理下一个，直到 108 项全部达到 `completed_pending_user_art_review`，或遇到必须由用户处理的真实阻断。随后提交完整总览并等待用户审核；用户审核前不把本批标记为已通过。
