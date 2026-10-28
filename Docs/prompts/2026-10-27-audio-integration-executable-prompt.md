# 《自由人塔防》现有原创音频完整接入执行 Prompt

你是一名熟悉 Unity 2022.3、UGUI、TextMeshPro、YooAsset、HybridCLR、游戏音频与本地存储兼容的高级工程师。请依据下列资料和当前工程，把已经制作并导入的原创音乐、音效真正接入《自由人塔防》，完成播放系统、业务触发、设置与持久化、资源管线和必要文档的联动修改。

目标工程：`D:/FishTestGame`。本文编写日期：2026-10-27。

这是一份完整实施指令。用户正式交付本 Prompt 要求执行后，直接推进工程修改，不停留在设计分析、资源清单或未接入的示例组件。本文件的编写与保存本身不代表已经实施声音功能。

## 一、任务范围与规则冲突处理

1. 本次实施目标为“接入当前已有原创音频”。执行本 Prompt 时，用户对声音接入的当前任务要求覆盖旧任务中“必须维持无声版本”“不得恢复声音系统、声音入口和声音设置”的限制，仅限完成本次声音功能所需范围。不能因为历史无声规则反复询问是否允许接入；也不能把该范围变更扩张到关卡数值、敌人资源或其他系统。
2. 复用 `Assets/Audio/OriginalPack_20261023/` 中现有母版。保留素材、GUID、制作源文件、质量报告及历史记录，不重新生成声音，不购买或下载替代素材，不调用收费生成 API，不把预览 MP3 当正式资源。
3. 保留当前“战术铸舱 / Tactical Forge”UI 和现有业务行为。声音设置是在当前设置页上作必要扩展，不回退到旧版设置布局，也不重做整套 UI。
4. 不恢复已删除的旧声音表、旧音频生成器或旧目录结构。采用独立音频目录配置与现有资源加载链集成，不新增 Luban 声音表。
5. 受保护的 `Luban/Config/Datas/Levels/L01..L30/**`、`EnemyData.xlsx`、`__tables__.xlsx` 禁止脚本批量改写。`Assets/ConfigJson/**` 和 `Assets/Gen/**` 只允许由合法源表与标准 Luban 导出产生，禁止直接改写生成文件。
6. 不修改关卡、金币、价格、伤害、攻击间隔、射程、减速、寻路、波次、评级、解锁、正式存档与战斗快照语义，不为音频重封或伪造 `runtimeContentHash`。
7. 不重建或覆盖敌人 prefab、动画、材质、方向图及 `.meta`，不运行“导入全部怪物”等总入口。允许在 `BaseEnemy` 的明确业务节点增加最小声音通知，但不改变伤害与生命周期逻辑。
8. 不回滚、覆盖、提交其他任务已有改动；不进行远端 pull、merge、发布、安装 APK、覆盖热更服务器或清理历史构建。共享文件写入前重新读取，以最小补丁修改。不自行新建并行代理任务。

## 二、开始前同步与必须阅读的资料

先读当前适用的 `AGENTS.md`、`ProjectSettings/ProjectVersion.txt`、`git status` 与拟改文件差异。当前版本文件为 `2022.3.62f3c1`，执行时重新确认；不得套用 CatchFish 的 Unity 2020 专用约束。

按以下资料优先级研究：当前用户任务与适用规则 → 当前代码、素材、实际资源配置 → 音频包清单 → 制作与移除记录 → 历史设计描述。历史记录只说明当时结果，不证明当前工程已验证。

必须阅读：

- `Audio_Creation_Executable_Prompt.md`：原创音频的风格、内容与制作边界。
- `AudioProduction/OriginalPack_20261023/README_zh.md`。
- `AudioProduction/OriginalPack_20261023/asset_manifest.csv`。
- `AudioProduction/OriginalPack_20261023/Quality/QA_zh.md` 与 `Quality/audio_quality_report.json`。
- `AudioProduction/OriginalPack_20261023/SOURCES_AND_LICENSES_zh.md`。
- `Assets/Audio/OriginalPack_20261023/README_zh.md` 与 `asset_manifest.csv`。
- `Docs/AudioRemoval_Verification_2026-10-23.md`，包括 2026-10-27 恢复编辑器试听的补记。
- `Audio_Removal_Executable_Prompt.md`：只用于理解被移除的链路，不重新执行移除任务。
- `Docs/UI_Redesign/2026-10-26/specs/design-system.md`、`responsive-and-language.md`、`page-inventory.md` 中的设置页要求，以及 `Docs/UI_Redesign/Implementation/2026-10-26/` 中的实际实施记录。
- `Docs/YooAsset_Integration.md`、`Docs/HybridCLR_Integration.md`、`Docs/LocalPersistence_SQLite_Design.md` 的相关章节。

代码研究必须覆盖实际调用者、事件顺序与生命周期：

| 链路 | 重点文件 |
|---|---|
| 启动与管理器 | `Assets/Scripts/Launcher.cs`、`GameSceneLauncher.cs`、`HotUpdateEntry.cs`、`Core/Manager/BaseManager.cs` |
| 游戏流程 | `Assets/Scripts/Game/GameFlowManager.cs`、`Round/WaveManager.cs`、`Core/GameClock.cs`、`Core/Event/EventName.cs` |
| 战斗与建造 | `Assets/Scripts/Tower/BaseTower.cs`、`RetardTower.cs`、`TowerPlacement.cs`、`Bullet/BaseBullet.cs`、`Enemy/BaseEnemy.cs`、`Core/Manager/PlayerDataManager.cs` |
| 敌人声音分组 | `Assets/Scripts/Data/MonsterCatalog.cs`、`EnemyConfig.cs` |
| UI | `Assets/Scripts/Core/UI/UIManager.cs`、`Assets/Scripts/UI/SettingView.cs`、`LevelClearView.cs`、实际使用的其他页面与按钮 |
| 设置与存储 | `Assets/Scripts/Data/SaveData.cs`、`Core/Manager/SaveManager.cs`、`Data/Persistence/ISaveStorage.cs`、`JsonSaveStorage.cs`、`SqliteSaveStorage.cs`、`SaveSchema.cs` |
| 资源加载 | `Assets/Scripts/Core/Res/IResLoader.cs`、`ResLoader.cs`、`ResTable.cs`、`ResBundle.cs`、`YooAssetResLoader.cs` |
| 生成与收集 | `Assets/Editor/UIPrefabBuilder.cs`、`TacticalForgePrefabBuilder.cs`、`LocalizationPrefabBinder.cs`、`UIResolutionLayout.cs`、`Assets/Scripts/Core/UI/TacticalForgeLayout.cs`、`Assets/Editor/YooAsset/FTYooAssetSetupWizard.cs`、`FTBundlePackRule.cs`、`Assets/BundleCollectorSetting.asset` |
| 现有兼容测试 | `Assets/Tests/BalanceRating/SoundRemovalPersistenceTests.cs` |

按相关代码做定点阅读，不进行无目的的全工程主线程扫描。开始实施前给出简短变更清单，然后开展修改。

## 三、已核对的工程事实

以下是编写本 Prompt 时读取磁盘得到的基线，实施前须核对差异：

1. 旧项目 `AudioManager`、`AudioFadeDriver`、`UiClickSfx`、`AudioCatalog`、声音配置及调用已经移除。保留 DOTween 通用音频 API 和 Unity AudioModule 不等于存在可用播放系统。
2. `ProjectSettings/AudioManager.asset` 当前为 `m_DisableAudio: 0`，只说明 Unity 音频引擎已启用；现有 Boot 与 main 场景未发现 AudioListener。必须建立有效监听与播放链，不能把 Inspector 可试听当作游戏已接入。
3. 音频母版已导入 `Assets/Audio/OriginalPack_20261023/`，共 93 个 WAV，约 90 MiB 源文件；全部为 48 kHz / 24-bit PCM。BGM 与短曲为立体声，SFX 为单声道。源文件体积不等于 Player 内存占用。
4. 音频包技术报告记录了格式、信号和循环检查通过；报告明确写着“人工听感待确认”。本次不得把旧自动分析结果升级表述为已通过人工试听。
5. `Launcher` 先初始化管理器，再推进资源、配置、Splash 与 Ready。声音资源加载必须等 `ResLoader.Instance.IsReady`，设置应用必须等存档就绪，不能在管理器静态构造或资源初始化前强行加载 AudioClip。
6. 实际主战斗路径是 `BaseTower.Fire()` 即时命中：普通塔调用 `HurtEnemy()`，爆破塔调用 `DetonateAt()`。`BaseBullet.OnHit()` / `Explode()` 仍有兼容实现，但不能只在旧子弹路径挂声音后宣称战斗已接入。
7. 冰霜塔是 `TowerConfig.IsSlowAura` / type=3 的持续范围减速，走 `BaseTower.TickSlowAura()`，`RetardTower` 不发射减速弹。
8. `GameClock.Speed` 负责模拟倍速，暂停由 `Time.timeScale` 的 0/1 表达。声音不得改变它们，音乐与常规音效不得因为 ×2/×3 自动升调或缩短。
9. `BuildTowerSuccess` 也会在快照恢复建塔的共用内部路径触发；`GameSpeedChangedEvent` 也用于初始化和恢复后的同步。直接订阅这些事件播放一次性声音会造成继续游戏时误播。
10. `LevelClearView.OnLanguageChanged()` 会再次调用 `Show()` 刷新文本。胜利、失败与评级短曲不能绑在每次 `Show()` 或 `OnEnable()` 上重复播放。
11. 暂停相关注释与实现存在差异：当前 `OnPauseRequest()` 实际调用 `SetPausedState(true)`；`EnsureRunning()` 又存在直接恢复 `GameClock` 的路径。音频必须依据执行时真实状态转换，不能只读旧注释，也不能仅假设所有恢复都会发同一个事件。
12. `GameSettings` 当前只有 `language`，JSON 格式版本为 2，SQLite schema 为 4；SQLite 的 `game_settings` 只存 id/updated_at，语言保存在 `kv_store`。
13. 当前启用 YooAsset 与热更新相关宏，manifest 声明 YooAsset 3.0.6、HybridCLR 8.14.1。收集器的 `EnableAddressable` 为 false；须同时核对收集设置、`ResTable` 与加载器的实际地址解析，不能只按文件名猜地址。
14. 声音目录目前未在既有声音移除后的收集计划中恢复。只把 WAV 放在 Assets 下不足以保证 Player 可以加载。
15. 当前工作区有大量 UI、存档管理器、流程及生成文件的已有修改。尤其保护 `SaveManager.cs`、`GameFlowManager.cs`、`Launcher.cs`、`BaseTower` 的调用者、设置 prefab 与 UI 构建器中的最新内容。

## 四、音频资源与完整语义映射

正式资源根为 `Assets/Audio/OriginalPack_20261023/`。下列范围写法用于列出真实存在的变体，必须逐文件登记，不是允许遗漏的占位符。准确技术字段以清单与实际 WAV 为准。

### 4.1 音乐与短曲

| 相对路径 | 时长 | 使用语义 |
|---|---:|---|
| `BGM/ft_bgm_menu.wav` | 80.00 秒 | 主菜单、选关、详情、图鉴等菜单流程 |
| `BGM/ft_bgm_prepare.wav` | 87.27 秒 | 战前布阵、普通回合间准备 |
| `BGM/ft_bgm_battle.wav` | 66.21 秒 | 常规回合战斗 |
| `BGM/ft_bgm_pressure.wav` | 60.00 秒 | 达到明确条件的高压战斗 |
| `Stingers/ft_stinger_victory.wav` | 5.60 秒 | 实际胜利结算，一局一次 |
| `Stingers/ft_stinger_defeat.wav` | 4.50 秒 | 实际失败结算，一局一次 |
| `Stingers/ft_stinger_rating.wav` | 2.40 秒 | 胜利评级首次揭示完成，一局至多一次 |

四首 BGM 均以整个 WAV 为循环区间，末端不包含：menu 为 0～3840000、prepare 为 0～4189091、battle 为 0～3177931、pressure 为 0～2880000 样本帧。若 Unity 导入设置改变采样率，不得把母版样本帧数直接当导入后 `AudioClip.samples` 使用。优先保持原采样率并使用整段循环。

### 4.2 界面与塔操作

| 目录 | 文件名与编号 | 数量 | 触发语义 |
|---|---|---:|---|
| `SFX/UI/` | `ft_sfx_ui_click_01.wav`～`03.wav` | 3 | 普通有效按钮点击 |
| `SFX/UI/` | `ft_sfx_ui_confirm_01.wav`～`02.wav` | 2 | 明确确认动作 |
| `SFX/UI/` | `ft_sfx_ui_back_01.wav`～`02.wav` | 2 | 返回、取消、关闭 |
| `SFX/UI/` | `ft_sfx_ui_invalid_01.wav`～`02.wav` | 2 | 被业务拒绝的操作 |
| `SFX/UI/` | `ft_sfx_ui_toggle_01.wav`～`03.wav` | 3 | 真正发生的开关、选项切换 |
| `SFX/Tower/` | `ft_sfx_tower_select_01.wav`～`03.wav` | 3 | 玩家实际选中塔 |
| `SFX/Tower/` | `ft_sfx_tower_build_01.wav`～`03.wav` | 3 | 新建成功，非预览与恢复 |
| `SFX/Tower/` | `ft_sfx_tower_build_fail_01.wav`～`02.wav` | 2 | 玩家提交建造后失败 |
| `SFX/Tower/` | `ft_sfx_tower_upgrade_01.wav`～`03.wav` | 3 | 升级已经完成 |
| `SFX/Tower/` | `ft_sfx_tower_sell_01.wav`～`03.wav` | 3 | 出售已成功执行 |

### 4.3 战斗

| 目录 | 文件名与编号 | 数量 | 触发语义 |
|---|---|---:|---|
| `SFX/Tower/` | `ft_sfx_normal_fire_01.wav`～`04.wav` | 4 | 普通塔有效开火 |
| `SFX/Tower/` | `ft_sfx_normal_hit_01.wav`～`03.wav` | 3 | 普通攻击有效命中 |
| `SFX/Tower/` | `ft_sfx_blast_fire_01.wav`～`03.wav` | 3 | 爆破塔有效开火 |
| `SFX/Tower/` | `ft_sfx_blast_hit_01.wav`～`03.wav` | 3 | 一次爆炸结算，非每个 AOE 目标一次 |
| `SFX/Tower/` | `ft_sfx_frost_activate_01.wav`～`03.wav` | 3 | 玩家新建冰霜塔后的激活 |
| `SFX/Tower/` | `ft_sfx_frost_pulse_01.wav`～`03.wav` | 3 | 光环本次实际影响到目标后的受控脉冲 |
| `SFX/Tower/` | `ft_sfx_frost_loop_01.wav` | 1 | 4 秒持续光环循环，0～192000 母版样本帧 |
| `SFX/Enemy/` | `ft_sfx_light_hit_01.wav`～`03.wav`、`ft_sfx_light_death_01.wav`～`03.wav` | 6 | 轻型生物受击、死亡 |
| `SFX/Enemy/` | `ft_sfx_wing_hit_01.wav`～`03.wav`、`ft_sfx_wing_death_01.wav`～`03.wav` | 6 | 鸟类、蝙蝠等翼类受击、死亡 |
| `SFX/Enemy/` | `ft_sfx_insect_hit_01.wav`～`03.wav`、`ft_sfx_insect_death_01.wav`～`03.wav` | 6 | 虫、蝎类受击、死亡 |
| `SFX/Enemy/` | `ft_sfx_heavy_hit_01.wav`～`03.wav`、`ft_sfx_heavy_death_01.wav`～`03.wav` | 6 | 重型生物受击、死亡 |

### 4.4 流程提示

下表全部位于 `SFX/Feedback/`。

| 文件名与编号 | 数量 | 触发语义 |
|---|---:|---|
| `ft_sfx_round_start_01.wav`～`02.wav` | 2 | 真正开始一回合 |
| `ft_sfx_round_clear_01.wav`～`02.wav` | 2 | 非最终回合完成 |
| `ft_sfx_enemy_leak_01.wav`～`03.wav` | 3 | 敌人实际漏过终点 |
| `ft_sfx_low_hp_01.wav`～`02.wav` | 2 | 生命跌入低血量区间 |
| `ft_sfx_pause_01.wav`～`02.wav` | 2 | 局内状态从运行切为暂停 |
| `ft_sfx_resume_01.wav`～`02.wav` | 2 | 玩家主动恢复运行 |
| `ft_sfx_speed_change_01.wav`～`03.wav` | 3 | 玩家成功切换模拟倍速 |

数量合计：4 首 BGM、3 段 Stinger、12 个 UI、34 个 Tower、24 个 Enemy、16 个 Feedback，共 93 个正式资源。清单内资源全部具备有效配置；播放按业务和限流选择，不能为了用满变体而在一次动作中全部叠播。

## 五、播放系统与配置设计

### 5.1 统一入口

建立一个项目声音服务，接入当前管理器初始化、资源就绪与退出释放链。可以采用 `AudioManager` 名称，但这是基于当前工程的新实现，不能从 Git 整体恢复旧文件覆盖现有代码。公共入口明确区分：音乐状态、一次性音效、结算短曲、带 owner 的持续循环、音量设置、暂停及停止释放。

新增或复用集中音频配置：优先使用独立 ScriptableObject 与清晰类型，保存语义 ID、逻辑资源名、变体组、分类、基础增益、优先级、冷却、同组并发、循环与 owner 策略。可以放在 `Assets/Audio/Runtime/`；配置、混音器与正式 WAV 的收集规则必须分别明确。本文提出的新配置与服务均为待实现内容，不能在交付时描述成原本已经存在的接口。

禁止业务热路径按字符串拼接 WAV 路径、每次扫描目录、按文件名动态猜资源、反复 `GetComponent`，或绕开当前资源系统直接从磁盘读取。音频目录配置不能成为与 `ResTable` 相互矛盾的第二套地址真相；业务语义最终解析到唯一登记的逻辑名。

声音缺失时一次性输出包含语义、逻辑名与实际地址的诊断，跳过该声音并继续游戏。不得使建造、伤害、结算或存档依赖播放成功；不使用空 AudioClip 或占位 beep 掩盖缺项，也不因可选音效缺失阻塞进入游戏。

### 5.2 混音与监听

- 建立可持久存在且幂等的音频根节点，禁止每切关、每开页面再生成一个管理器。关闭、重启、域重载或禁用 Domain Reload 的编辑器场景下，清理静态状态、事件和协程。
- 有效运行阶段全局恰好一个启用的 AudioListener。针对当前 Boot → main 启动链选择明确持有者，处理直接启动 main、场景切换和重复初始化；不能同时在常驻根与相机留下两个监听器。
- 默认 2D 音频，`spatialBlend=0`，不依赖世界距离衰减、相机 Z 距离或多普勒。可选的轻微声像不能影响玩法或让边缘关键提示听不见。
- 优先采用 AudioMixer，至少包含 Master、Music、SFX 总线；Stinger 归 Music，UI、反馈、战斗归 SFX，可细分子组进行优先级控制。
- 线性音量到 dB 的转换处理 0，不能产生负无穷或 NaN。Master 与分类音量各应用一次，避免同时在 mixer、source 和 Listener 上重复乘用户音量。
- `playOnAwake=false`，不依赖 prefab 打开自动播放。音乐至少两个专用声源完成交叉淡化，Stinger 使用独立通道，短音效使用有上限的池，光环使用可停止的循环槽位。

### 5.3 声源预算与随机数隔离

给出实际可调默认值并落入集中配置：短音效池 20、冰霜循环槽最多 4、BGM 声源 2、Stinger 声源 1，共最多 27 个服务声源，保留当前引擎 32 个 Real Voices 下的余量；执行时若其他系统使用声源，合并计算预算。不得单纯提高 Unity voice 数掩盖无节制叠音。

- 同组与全局同时限流，拒绝低优先级声音时不排队补播。
- 优先级建议：结算与关键状态提示 > 用户 UI/建造操作 > 爆破/普通开火 > 普通命中与生物受击 > 环境光环。短音效池为 UI、漏怪和低血量提示保留至少 4 个可抢占低优先级音效的槽位；结算通道独立保留。
- 实时冷却初值：普通开火同组 0.05 秒、普通命中 0.08 秒、爆破 0.10 秒、生物受击同组 0.12 秒且单敌人 0.20 秒、生物死亡同组 0.08 秒、冰霜脉冲同组 0.30 秒且单塔 0.50 秒、同帧漏怪合并并使用 0.20 秒冷却。可据实际混音调整，不改攻击间隔。
- 变体使用声音系统私有随机源，避免同组连续重复；不消费战斗共用的 `UnityEngine.Random`，不改变确定性回放或策略结果。轻微 pitch 随机只可用于短 SFX，默认 0.97～1.03；BGM、结算与光环保持 1。
- 池内声源完成、抢占、暂停、停止及回收均恢复 clip、loop、pitch、volume、mute 与 mixer group，避免上一条声音属性串到下一条。
- 定时、淡化与声音冷却采用实时或 DSP 时钟。暂停后的回收不能因为 `Time.deltaTime=0` 永久卡住，也不能错误回收被暂停的声音。

## 六、音乐状态与应用生命周期

先把当前流程转换整理成一张实际映射表，再接入统一音乐状态入口。禁止仅按哪个 UI 当前打开来推测整局状态。

| 实际上下文 | 音乐策略 |
|---|---|
| AOT Boot、补丁下载、资源/配置失败 | 默认无声；本轮不为热更前界面引入独立音频体系 |
| 资源与设置就绪后的主菜单、选关、菜单图鉴、关卡详情 | menu；连续菜单导航不重置进度 |
| 真正进入关卡的 Preparing、普通 RoundComplete | prepare |
| RoundRunning | battle，满足高压条件时 pressure |
| 局中设置、介绍、确认框等覆盖层 | 继承当前底层状态，不因开关弹窗重新选曲 |
| 胜利或失败 | 停止/淡出战斗与光环，播放对应短曲；结算页不恢复战斗循环 |
| 返回选关或主菜单 | 取消本局残留播放任务，平滑回到 menu |
| 重开或继续快照 | 从恢复后的真实流程计算音乐，不重放已发生的操作提示 |

具体要求：

1. 默认交叉淡化约 0.6～1.0 秒，使用未缩放时间。相同曲目与相同状态幂等；切换频繁时取消过期请求。异步加载使用请求代次或等价取消机制，旧菜单音乐回调不得覆盖已开始的战斗音乐，退出后不得重新拉起旧 BGM。
2. pressure 默认只在 `RoundRunning` 且 `MaxHp>0` 时启用：生命比例 ≤30% 进入，恢复到 ≥40% 或离开战斗时退出，音乐状态最短驻留约 8 秒；结算和退出优先级更高。阈值与驻留集中配置，不改数值表，不虚构 Boss 战，不按敌人 ID 猜高压。若执行时存在更合适的正式高压状态，可复用并说明依据。
3. 游戏暂停时暂停战斗音效和光环，音乐保持正常音高并降低到当前音乐增益的约 40%；暂停/继续提示与 UI 仍可听。恢复时还原到用户当前设置，不能硬重置为默认音量。不能因为打开设置面板而额外改变原游戏暂停语义。
4. 真实暂停转换以 `GameClock.IsPaused` 与流程层实际路径为准，结合 `PauseStateChangedEvent` 处理；补齐声音状态同步所需的最小通知，或使用集中轻量状态对齐，避免漏掉 `EnsureRunning()` 等路径。初始化与切关的强制复位不播放“继续”提示。
5. ×1/×2/×3 只增加真实战斗事件密度；不修改 BGM pitch，不让音频播放完成时间或限流受模拟倍速影响。`GameSpeedChangedEvent` 只有实际用户改变且值确实变化时播放切换声，初始化与恢复不播。
6. Android 应用进入后台、失去音频输出或系统暂停时停止可听输出；回前台后根据用户 mute、游戏暂停与最新流程恢复，不叠播、不重复初始化。应用暂停状态与游戏暂停状态独立处理，不能覆盖玩家手动静音。
7. BGM 使用整段无缝循环。若压缩或 Streaming 导致接缝、首帧延迟、解码异常，调整导入或调度策略并如实记录，禁止用反复从 0 播放的淡入淡出来掩盖循环问题。

## 七、业务触发落点与防重复规则

### 7.1 通用 UI

优先在现有 `UIManager` 页面创建/绑定链建立幂等的按钮音效接入，支持池化条目、后生成按钮、鼠标/触屏/键盘的真实提交；不每帧扫描整个 Canvas，不改 EventSystem 的业务派发方式。

同一交互选择一种主语义声音。已有返回、确认、无效、建造或升级成功音的按钮，须能关闭通用 click，防止“一次点击同时有普通 click、confirm、tower_upgrade”三重叠播。拖拽开始与拖拽落点提交分别按真实语义处理，不把拖动每帧当点击。

禁用按钮、界面初始化、`SetValueWithoutNotify`、语言刷新、条目复用和代码主动打开页面不播点击。失败声在实际业务拒绝后播放；不能把 pointer down 当成功。取消出售只播返回，不能播出售成功。

### 7.2 建造、升级、出售与选择

- 新建成功：接在 `TowerManager.TryBuildInternal()` 成功且确为玩家新建的分支，或为成功通知附加明确来源；不可仅监听 `BuildTowerSuccess` 而不区分恢复。不要改变现有 HUD 退出放置状态的事件语义。
- 建造失败：在玩家确认放置且校验拒绝时播放一次。预览红格、路径预测、鼠标悬停以及每帧余额检查不播。
- 升级：在 `TowerManager.TryUpgrade()` 完成替换与注册后播放一次，保留现有 `TowerUpgradeSuccess`，不复用新建成功来触发。升级失败走一次拒绝声。
- 出售：仅在 `TowerManager.Sell()` 确认成功后播放；`TowerSellRequestEvent` 与 `TowerSellConfirmEvent` 只是意图或确认，不可当作出售一定成功。`ClearAll()` 与退出清理不得播出售声。
- 选中：只有玩家新选择目标时播放。升级后的自动重选、快照恢复与重复刷新不播。
- 冰霜新建可设计一次激活声替代普通建造成功声，或做受控的两层组合，必须集中定义并限制总体增益。升级主要使用升级声，不因替换实例再次叠播整套新建与激活声音。

### 7.3 普通塔与爆破塔

普通开火与普通命中接在当前 `BaseTower.Fire()` / `HurtEnemy()` 的有效执行路径；爆破开火与爆炸接在 `Fire()` / `DetonateAt()` 对应路径。先确认有效配置、目标及攻击条件，再触发相应声音。

一次 AOE 只产生一次爆炸主体声，不能在半径内每个受害者上重复播放爆炸。普通命中声与敌人生物受击声可以分层，但各自受预算限制，死亡优先于同个敌人的受击叫声。若实际仍有调用者使用 `BaseBullet`，补齐兼容路径并保证同一次攻击不会在新旧路径各播一次；不为音效恢复可见弹体或改变即时命中逻辑。

### 7.4 冰霜光环

光环按实际存活、已建成且参与战斗的塔维护 owner，禁止为每个圈内敌人创建循环声源。默认只为当前战斗中实际有效的冰霜光环播放，最多 4 个循环槽；更多塔通过合并增益或稳定选择代表 owner 表达，不能无限叠加。

`TickSlowAura()` 只有本轮实际作用到有效目标后才申请脉冲，并受单塔与全局冷却限制。不因仅显示射程圈或生成预览 ghost 而发声。快照恢复可以恢复环境光环，但不补播历史激活、建造、升级或脉冲。

出售、升级替换、清关、重开、切场景、结算、暂停与服务销毁时正确停播或转移 owner。销毁旧塔后不能保留悬挂引用，也不能由于新 owner 未抢到槽位永久丢失后续可用光环。

### 7.5 敌人

在独立音频映射中，以 `EnemyConfig.ResName` 对应的 `MonsterCatalog.Names/Families` 建立缓存，使用真实家族映射声音类型，不能修改生成的 MonsterCatalog。

初始分组可采用：Bats/Birds → wing；Insects/Scorpions/Parasites → insect；Cattle/Giants/Horses/Mounts → heavy；Apes/Bunnies/Rats → light；Dogs/Felines/Pigs 按具体怪物体型或明确名称覆盖，默认 heavy。Inanimate 不强行播放动物叫声，默认关闭生物叫声并记录；未知家族有明确降级与一次诊断。映射只影响声音，不改变 `IsFlying`、护甲、配置 ID 或资源包家族。

受击在 `BaseEnemy.Hurt()` 的真实有效伤害后触发，处理护甲后伤害、死亡及 DOT：建议有效伤害 ≥1 且本次未死亡时才申请普通受击，死亡只申请死亡叫声。DOT 不按每帧小额扣血不断播放。只从 `Die()` 或唯一死亡事件路径发出死亡声；`OnReachEnd()` 漏怪、`OnRecycle()` 回收与 `EnemyResetEvent` 不得播放死亡。

所有 per-enemy 声音状态在 `Init()` / `OnRecycle()` 成对重置。一次性死亡和受击声音由服务持有位置/分类快照，不跟随池化敌人重新激活到另一个出生位置。声音系统不得持有已回收敌人的无期限强引用。

### 7.6 回合、漏怪、低血量与结算

- 依据 `RoundStartEvent` / `RoundClearEvent` 的真实发送位置确认回合含义，不在 Wave 与 Round 两层对同一次推进重复播提示。不要仅凭 UI 把某进度叫“波”就重复绑定。
- 最终回合结束时，胜利短曲优先，抑制紧邻的 round_clear，避免清回合与胜利叠成两套结算。
- `EnemyReachedEndEvent` 表示实际漏怪，可监听播放提示；`PlayerHpChangeEvent` 同时会在初始化与恢复触发，只有 delta<0 的真实扣血才考虑低血量提示。
- 低生命采用当前 `Hp/MaxHp`，首次跌入 ≤30% 时提示一次，恢复到 >40% 或新一局后重置，连续低血量扣血不逐帧报警；进入失败结算则停止告警。阈值集中配置，不写源表。
- 胜负以本局唯一结算入口和 `GameOverEvent(bool)` 对齐；`LevelClearEvent`、`AllRoundClearEvent` 与 `GameOverEvent` 不能各播放一次胜利。使用已有 run ID 或明确会话代次去重，不能只用 levelId，避免重打同一关永远不再播放。
- 胜利短曲开始后，评级短曲等待其自然结束或明确评级揭示节点再播放，间隔建议至少 0.2 秒；没有揭示动画时允许建立一次性延后音频调度，不伪造评级状态。失败不播评级短曲。
- 评级短曲安排后，返回、重开、下一关、关闭结算或服务销毁必须取消；切换语言、窗口重新显示和同一数据二次 `Show()` 不重播。
- 不改评级计算、落库结果、持久化重试、下一关开放时机，也不为等待短曲结束阻塞玩家按钮。

## 八、资源加载、导入与构建链

### 8.1 登记和加载

1. 在 `ResTable` 为全部正式音频、运行配置与混音资源建立唯一稳定登记；在 `ResBundle` 维护必要包名与生命周期分组，例如区分音乐、UI/反馈、战斗 SFX 与运行配置。具体包名集中定义，不给每个短 SFX 单独造一个 bundle。
2. 同步 `Assets/BundleCollectorSetting.asset` 与 `FTYooAssetSetupWizard.CollectPlan`，由实际 API 创建或修改收集项，保证“生成/修复收集器配置”不会丢失声音。使用 WAV 限定目录或过滤规则，避免把 README、CSV、生产源代码、预览和质量报告收成运行资源；注意运行配置和 mixer 也须覆盖。
3. 核对 `FTBundlePackRule` 按 `ResTable` 的实际归包，防止未登记音频掉进 misc 或作为共享依赖重复打包。保持其他收集组、启用宏和现有寻址规则不变，不能全局改 `EnableAddressable` 来修单个音频地址。
4. 所有运行加载走 `ResLoader.Instance` 的实际接口：`LoadAsync<T>`、`Preload`、`Release`、`ReleaseBundle`。编辑器与 Player 都须成立，不依赖 `AssetDatabase` 的运行时回退。
5. 当前加载器由逻辑名缓存句柄，不提供“每次 Load 自动增加一份消费者引用”的保证。仔细核对 `Preload` 的逻辑包引用与 `ReleaseBundle` 配对，同一声音多个 source 共用一个 clip 时不能任一 source 结束就把共享句柄释放。
6. UI/反馈小资源可预热；战斗 SFX 在入关准备阶段预热；BGM 按需加载当前与交叉淡化所需下一首，不在启动一次性解压全部长音乐。音频预热有有界完成/失败出口，不破坏当前加载 UI 与配置重试链。
7. 离关先停止并清除对应 source.clip、owner、待处理请求，再清理业务缓存和释放非持久资源；交叉淡化结束前保留旧曲句柄，完成后释放。异步回调在旧会话结束后到达时正确释放本次拥有的引用，不能重新写入已经清空的缓存。
8. 不同关卡切换与反复进入菜单后，音频缓存、循环 owner 和加载引用不能持续增长。禁止用每次 `Resources.UnloadUnusedAssets()` 或强制 GC 代替生命周期管理。

### 8.2 AudioImporter

保留原 WAV 与 GUID，只定点修改这 93 个资源的导入策略和必要新音频配置，不做全工程重导。

- 长 BGM：以 Streaming + Vorbis、保持立体声与原采样率为初始方案，评估循环边界和加载延迟。若其他方案更合适，给出实际依据和内存代价。
- 短 UI、反馈、常规战斗 SFX：优先 Decompress On Load，按音色选择 PCM/ADPCM 或合适压缩；保持单声道。不因机械设置 normalize 改坏既有包内增益关系。
- Stinger：单次播放、立体声，采用能保证结算及时起音的加载方式；纳入可控的解码内存预算。
- 冰霜 loop：保持 4 秒完整循环，优先小资源常驻或战斗期间解码复用，不与普通一次性音效共用回收规则。
- 保持输入采样率；如必须重采样，更新运行循环依据，不修改制作清单来伪装源母版已改变。
- 默认项与 Android 平台覆盖同时核对；不盲目强制所有 WAV 为 PCM、Streaming 或同一 quality。项目实际 Player 平台需现场读取，不因历史文档的 Android 记录擅自切换 Build Target。

### 8.3 HybridCLR 与引导边界

声音服务放入当前合适的运行程序集，遵循 `FTProject.Runtime` 与 AOT 边界。AOT Boot 下载界面默认保持无声，不往 `Assets/Resources/BootUI/HotUpdateView.prefab` 挂热更声音脚本；正式声音在运行程序集与资源系统就绪后启用。

新建含热更脚本的 prefab 或 ScriptableObject 时确认打包、加载与裁剪路径。必要时通过当前项目标准流程更新 HybridCLR/link 保留项；不手写大范围保留全部程序集，不为验证顺带发布 DLL、覆盖服务器或替换正式热更清单。只有编辑器编译通过不能宣称 IL2CPP/HybridCLR Player 已通过。

## 九、设置页、本地化与持久化

### 9.1 用户行为

在当前 `SettingView` 中增加：总音量、音乐音量、音效音量和总静音，保留语言、重置存档及关闭。初始值统一为总音量 80%、音乐 65%、音效 80%、静音关闭，作为可调的产品初值；资源自身基础增益另设，避免用户音量承担全部混音职责。

- 滑块拖动立即改变当前声音；程序同步 UI 用无通知 API，不触发 click/toggle。
- 总静音记住原先各滑块值，取消静音恢复当前保存值；0% 是有效设置，不能当成字段缺失改回默认。
- 音量为 0 或静音时不为了“试听反馈”强制出声；SFX 预览最多在用户完成一次调整后播放短例音，不在每帧拖动时播放。
- 防止滑块每帧写盘，采用短延迟合并与拖动结束、关闭设置、应用暂停/退出时的可靠保存。当前实际存储后端的错误需要正常上报，不能只改内存假装已持久化。
- 保持当前重置存档的二次确认与原有业务范围；如既有重置会重建整个 GameSettings，正确应用新默认并刷新控件，不绕过确认、不为了测试真的重置正式存档。

### 9.2 UI 与语言链

更新实际 `Assets/Prefabs/UI/SettingView.prefab`、`SettingView.cs`、相关布局、`UIPrefabBuilder` 与 `TacticalForgePrefabBuilder` 的对应构建路径，使下次重建不会删掉新控件或回退旧皮肤。注意 `UIPrefabBuilder.BuildSetting()` 当前会转交 `TacticalForgePrefabBuilder.UpdateExisting()`，只修改旧兜底生成分支是不够的。

使用现有字体、颜色、间距、按钮与安全区方案，设置页必要时扩高或滚动；保持简中、繁中、英文和小屏横屏可用，音量控件不得覆盖重置/关闭按钮。不要为了声音设置批量重做其他页面。

文本接入现有 `LanguageManager` / 本地化表。优先复用真实存在的 key；缺少的 Master Volume、Music Volume、SFX Volume、Mute 等词条通过人工维护 `Luban/Config/Datas/Localization.xlsx` 后走标准 Luban 导出补齐三语言。旧任务仅允许自动删除声音条目的授权不能扩展为自动批量写表。本任务不需要改 `__tables__.xlsx` 或新增声音表。

禁止直接编辑 `tblocalization.json`、生成 C# 或建立第二套运行时多语言字典绕过源表。必要的语言源表修改仅处理新增音频词条，保留已有 UI 任务新增内容；写入前重读并检查当前差异。

### 9.3 存档兼容

复用现有 `SaveManager` 与两套 `ISaveStorage` 后端，集中保存声音偏好，不另开 PlayerPrefs 或第二个配置文件造成多个真相。

优先在 `GameSettings` 新增独立、可辨识版本的音频设置对象；SQLite 使用现有 `kv_store` 下的 `settings.audio.version`、`settings.audio.master`、`settings.audio.music`、`settings.audio.sfx`、`settings.audio.muted` 等独立键。沿用语言的存储模式，避免为了音量把已删除的旧 `game_settings.volume/muted` 列再加回来。键名与 JSON 字段最终选定后在文档完整记录。

兼容规则必须明确实现：

1. 新存档：采用本节默认值。
2. 当前无声版本 JSON 与 schema 4 SQLite：缺少新音频设置时补默认，保留语言、评级、关卡进度和快照。
3. 删除声音前的 JSON 可能仍含旧 `volume/muted`。这些旧键继续忽略，不重新解释为本轮独立音乐/音效设置；新版本保存后只写新的音频结构。
4. schema 3 SQLite 按现有 3→4 迁移正常处理，再初始化新音频偏好，保留历史迁移，不绕过或重写旧事务。
5. 已保存的 0%、静音 true 与缺失字段可区分。不能只依赖 `JsonUtility` 字段初始化器判断缺失，也不能用 `value<=0` 代表从未设置；采用明确版本/存在性判定并覆盖旧 JSON 场景。
6. 音量处理越界、NaN、无穷及无效文本，按明确默认/截断规则降级；布尔与浮点序列化使用稳定的文化无关格式。
7. 新设置落库与版本标记保持一致，避免保存到一半把显式静音丢失。多字段 SQLite 更新复用现有事务；JSON 保持现有安全写入机制。
8. 仅复用 `kv_store` 新增键、没有表结构变化时无需为了“接入声音”升级 SQLite schema。确需改表结构才递增版本、提供幂等事务迁移和兼容测试，不无条件删库重建。
9. JSON 是否需要升版本按当前兼容策略判断；新增可选设置不能触发无条件清档。保留旧 version 2 档中的有效玩家数据。
10. 所有迁移验证使用临时目录/隔离库，不读取写回、重置或删除玩家正式存档。不以返回默认数据掩盖读取失败。

同步审视 `SoundRemovalPersistenceTests.cs`：保留“旧字段忽略、语言进度快照保留、旧库可重复迁移”等有效断言；仅将与新合法音频结构冲突的断言更新为明确的新预期，不能删掉整套兼容测试或降低覆盖来获得通过。

## 十、实施顺序与自检边界

按依赖顺序推进：

1. 完成规则与路径同步、音频清单和真实触发链核对。
2. 建立音频配置、混音/声源池、唯一监听器与资源登记，使正常菜单入口具备播放能力。
3. 接入音乐状态、暂停/倍速、应用生命周期与会话取消。
4. 接入建造、战斗、敌人、流程和结算触发，完成限流、来源区分与去重。
5. 接入设置 UI、三语言、JSON/SQLite 持久化，维护构建器与收集器。
6. 所有同批 C# 修改完成后，再进行本工程强制 MCP 编译闭环，编译期间不继续改代码。
7. 更新当前指导文档与实施记录，提交给用户进行实际听感和设备验收。

本任务不自动执行 APK 构建、安装、发布、整局回放或人工听感验收，不擅自进入/退出 Play Mode。用户当前或本会话已有运行授权时按授权执行；否则先完成可独立推进的代码、资源和文档工作。必要的保存兼容测试针对数据风险，采用临时数据运行；不为静态资源枚举或每一行映射编写镜像测试。

## 十一、Unity MCP 强制编译验证

当前目录是 `D:/FishTestGame`，但旧 `AGENTS.md` 仍记录 `D:/FreedomTower_1`。编辑器验证目标必须是 FishTestGame，不得因为相同 Unity 版本、相似名称或共用 8082 端口就验证另一个工程。实施中可同步本工程 `AGENTS.md` 的实际路径与本轮声音规则，保留原配置表保护条款；不要修改其他工程的规则。

1. 使用 `server="unityMCP"` 读取完整 URI `mcpforunity://custom-tools` 与 `mcpforunity://instances`，从现场列表选择实际对应 `D:/FishTestGame` 的完整实例 ID，调用 `set_active_instance`。
2. 读取 `mcpforunity://project/info`，确认 projectRoot 为 `D:/FishTestGame`，Unity 版本与本次版本文件一致。路径统一斜杠、忽略 Windows 大小写。不能使用 FreedomTower_1、MyTowerGame 或 CatchFish 的结果。
3. 读取 `mcpforunity://editor/state`，确认状态后调用 `refresh_unity(mode="force", scope="all", compile="request", wait_for_ready=true)`。
4. 间隔 1～2 秒读取 editor/state，直到 `compilation.is_compiling=false`、`compilation.is_domain_reload_pending=false`、`assets.is_updating=false`、`advice.ready_for_tools=true`。刷新返回或断线不代表编译成功。
5. 域重载或重连后重新发现、选择并核对实例，再继续尚未完成检查。
6. 用 `read_console(action="get", types=["error"], count="50", format="json")` 检查错误与异常，必要时 `filter_text="error CS"` 并分页；不清空日志掩盖历史错误。
7. `execute_code` 可用时补查 `return UnityEditor.EditorUtility.scriptCompilationFailed;`，结果应为 false。本次引入的错误修复后重跑闭环。

MCP 离线时已有授权自主恢复本工程现有 8082 服务与桥接：先区分服务不在线、无实例、编译/域重载、Codex 工具未启用；复用现有服务，不抢端口、不结束其他任务进程、不重复拉起。重载导致断线先等约 5 秒后限次重试。无法恢复时明确说明工程 `D:/FishTestGame`、Unity `2022.3.62f3c1`、`unityMCP / HTTP Local 8082`、失败环节，以及需要用户打开该工程 MCP 窗口启动/连接并在 Codex 重连的步骤。没有端到端连接就标记编译验证未完成，不能用静态扫描代替。

## 十二、验收标准与交付

### 12.1 工程完成标准

- 93 个正式 WAV 均有清晰归属、正确寻址和有效音频配置，预览/源文件不进入正式收集。
- 从现有正式启动链可以初始化声音，运行阶段监听器唯一，重复开页面和切关不增加音频根。
- menu、prepare、battle、pressure 切换与实际状态一致；暂停、恢复、静音、音量 0、×1/×2/×3 和回前台行为明确。
- 普通塔、爆破塔与冰霜光环使用真实路径；多目标爆炸不重复轰鸣，敌人 DOT 不变成连续尖叫，声源与缓存有上限。
- 真正成功才播建造/升级/出售成功；恢复快照不播放历史操作，预览、语言刷新和程序同步 UI 不触发声音。
- 最终结算一次，胜利与失败互斥，评级不与胜利短曲争抢，离开结算可以取消后续短曲。
- 设置即时生效、重启可恢复，语言/进度/评级/快照保留，新旧 JSON 与 SQLite 行为一致；显式 0% 与静音不会被默认值覆盖。
- 设置 UI、构建器、本地化源、资源登记、收集器生成入口与必要裁剪配置同步维护，重建不丢声音功能。
- 本工程 MCP 编译闭环完成或如实标记阻塞；静态检查、自动存储测试、编辑器编译、实际运行、听感、Android Player/设备验证分别报告，不混为一项。

### 12.2 交给用户的运行与听感清单

提供可按顺序操作的清单，至少覆盖：

1. 冷启动到主菜单、主菜单→选关→详情/图鉴→返回，音乐连续且不每开页重头。
2. 进关布阵→开战→普通回合结束→下一回合，四种音乐的正常转换与高压进入/退出。
3. 普通/爆破/冰霜三种塔的选择、新建成功/失败、升级成功/失败、出售确认/取消。
4. 普通命中、单次 AOE、多种敌人受击与死亡、DOT、漏怪及低血量告警。
5. 暂停/继续、局中设置、×1/×2/×3，暂停时 UI 仍可发声，倍速时音乐不升调。
6. 密集战斗中 UI 和漏怪提示能辨识，音效不刺耳、不过分堆叠；冰霜多塔不出现持续增大的噪声。
7. 胜利、失败、评级、立即下一关、重试、返回选关与结算中切换语言，不重播或串播上一局短曲。
8. 四项声音设置在简中/繁中/英文与小屏横屏下可操作，音量归零/静音/解除静音、关闭重开与应用重启行为正确。
9. 当前无声旧档、含更早 volume/muted 字段的 JSON、schema 3 与 schema 4 SQLite 的隔离兼容结果，正式存档未被测试改写。
10. Android 后台/前台、外部音频打断和输出设备切换；只有在用户授权设备验证后执行，设备身份与结果单列。
11. 四首音乐与冰霜 loop 的循环接缝，密集音效下的削波、掩蔽和疲劳。无法实际听取时明确保留“人工听感待用户确认”。

### 12.3 文件交付与文档同步

交付全部实际修改，不遗留空实现、未登记资源或未绑定控件。新增 `Docs/AudioIntegration_Implementation_2026-10-27.md`，完整记录：最终架构、真实 API、音频语义到路径/触发点的映射、混音及声源参数、导入/分包策略、加载释放生命周期、设置字段与持久化键、旧档策略、改动文件、验证结果和用户验收步骤。

同步更新当前使用的音频资源 README、YooAsset、存储、程序设计与编辑器操作文档中的相关说明；本工程 `AGENTS.md` 的无声维护条款改为当前声音接入后的维护规则，保留表格和其他保护约束。对 `Docs/AudioRemoval_Verification_2026-10-23.md` 追加后续接入说明与新文档链接，保留历史移除结果和 2026-10-27 试听补记。旧 UI 设计中“无声音选项”的描述保留历史语境，并由当前实施文档解释本轮设置页扩展，不为声音接入重画历史全套设计稿。

最后用中文简明报告：完成了哪些可用功能、关键文件与文档位置、必要兼容策略、实际执行的检查及结果、尚待用户试听或设备确认的项目。不得把素材已导入、技术报告通过、编译通过或历史工程运行结果写成当前游戏声音已通过设备验收。
