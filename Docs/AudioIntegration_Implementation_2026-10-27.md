# 原创声音接入实施记录

日期：2026-10-27。目标工程：`D:/FishTestGame`，Unity `2022.3.62f3c1`，当前 Player 目标 Android。

本轮执行 `Docs/prompts/2026-10-27-audio-integration-executable-prompt.md`，将现有原创音频接入运行代码、设置页、存储及资源管线。当前代码已通过本工程 MCP 编译检查和隔离存档测试；游戏播放、人工听感、循环接缝与 Android Player/设备验收尚待用户执行。没有将素材技术 QA 或编辑器预览当作设备验收。

## 1. 最终结构与启动边界

- `AudioManager` 接入 Launcher 的管理器列表，创建一个常驻 `GameAudio` 对象与 `AudioRuntime`，重复初始化复用已有实例。
- `AudioRuntime.Awake` 将监听器统一到该常驻根；场景加载后关闭其他场景监听器。Boot/main 无需再增加监听器组件。声源均为 2D、`playOnAwake=false`、doppler=0。
- 真正加载配置与声音须同时满足 `Launcher.IsBootComplete`、`ResLoader.Instance.IsReady`。AOT Boot/下载、资源失败和配置失败流程保持无声。直接从 Main 启动仍使用 Launcher 的同一就绪链。
- `AudioResourceMap` 显式登记 93 个 WAV、catalog、mixer，由 `ResTable` 静态注册；所有运行加载都经过 `ResLoader.Instance.LoadAsync<T>`。业务调用只使用 `SoundCue`，不扫描目录或拼 WAV 路径。
- `GameAudio` 是无初始化副作用的业务通知入口；没有声音服务时通知直接返回。音频可选失败不阻止伤害、建造、结算或保存。
- `AudioCatalog` 是独立 ScriptableObject。它只记录逻辑名和策略，不直接引用长音乐 AudioClip，避免加载配置时连带加载全部 BGM。不恢复 Luban 声音表。

### 公共接口

| 入口 | 用途 |
|---|---|
| `GameAudio.Play(SoundCue)` | 请求受限的一次性 UI、操作、战斗或流程音效 |
| `GameAudio.EnemyHit(BaseEnemy)` | 受击分类、单敌人冷却与死亡抢占 |
| `GameAudio.FrostPulse(BaseTower)` | 有效光环脉冲及 owner 活跃通知 |
| `GameAudio.BeginLevel()` / `EndLevel()` | 新局代次、离关取消、停止与释放 |
| `GameAudio.CancelRating()` | 关闭结算时取消评级调度；不修改评级结果 |
| `SaveManager.SetAudioPreferences(AudioPreferences)` | 更新内存偏好并立即应用声音增益 |
| `SaveManager.SaveAudioSettings()` | 保存当前设置并 Flush，返回实际后端是否报告成功 |
| `AudioRuntime.FlushSettings()` | 合并后的脏设置落盘；失败保留脏标记并延后重试 |
| `AudioRuntime.Diagnostics()` | ready、clip/pending 数、短声源占用、光环 owner 数、目标音乐、局代次 |

音乐状态、结算短曲与 owner 循环由服务集中维护，业务不直接操作 AudioSource。

## 2. 音乐、结算与生命周期

| 真实状态 | 音乐 |
|---|---|
| Ready 后的菜单/选关/详情/图鉴 | Menu，页面切换不重启相同曲目 |
| 局内 Loading/None | 不启动局内 BGM；进入失败调用 EndLevel 回到菜单语境 |
| Preparing、普通 RoundComplete | Prepare |
| RoundRunning | Battle；满足高压条件时 Pressure |
| 局内设置、介绍等覆盖页 | 继承底层流程 |
| GameOver / 唯一实际胜负事件 | 停止战斗与光环，淡出 BGM，播放胜负短曲 |
| 返回、重开或新关 | 取消旧代次请求，重新计算真实状态 |

- 交叉淡化默认 0.8 秒，两个音乐声源使用未缩放时间。相同目标幂等；过期异步结果按当前 wanted 集合丢弃并释放。旧曲在淡出完成前保留句柄。
- 高压仅在 RoundRunning、MaxHp>0 时按当前生命判断：≤30% 进入，≥40% 退出，音乐最短驻留 8 秒。离开战斗、结算、离关优先处理。未读取每帧克隆的 RunMetrics，未更改任何数值表。
- 胜负在 `GameOverEvent(bool)` 去重，每局以 epoch 区分，同一关重打可再次结算。无正常胜负事件的流程 GameOver 降级为失败声音收尾，不伪造胜利。
- 普通 round_clear 延后 0.2 秒再检查本局是否已结算，最终回合让位于胜利短曲。胜利 5.6 秒、失败 4.5 秒。
- 胜利后预取评级短曲，等待胜利声源自然结束，再留至少 0.2 秒间隔。后台暂停不会用绝对截止时间提前截断胜利。评级最多一次，不绑定 `LevelClearView.Show()`；切换语言不会重播。
- EndLevel、新局、流程对象销毁和服务 Shutdown 取消旧调度。关闭 LevelClearView 也取消待播或正在播放的评级短曲。声音不会阻塞下一关、重试或持久化重试按钮。
- 游戏暂停由 PauseStateChangedEvent 即时通知，并以 `GameClock.IsPaused` 轻量对齐，覆盖 EnsureRunning 路径。战斗与光环暂停，音乐音高保持 1、增益降到当前值的 40%；UI 与暂停/继续提示可播放。强制初始化/离关恢复不播放继续提示。
- ×1/×2/×3 只影响事件密度，所有音频冷却、淡化、评级间隔均用实时计时，不更改 GameClock、Time.timeScale 或音乐 pitch。
- 应用后台与失焦单独暂停全部输出并保存设置，回前台依据当前 mute、游戏暂停和最新状态恢复。监听 AudioSettings 的配置变化，重新核对可用声源，音乐/有效 owner 循环可在输出重置后恢复。输出设备切换和 Android 音频打断的实际表现仍须设备验证。

## 3. 声源、混音与限流

实际配置：短音效池 20，光环最多 4，BGM 2，Stinger 1，最多 27 个服务声源。保持项目现有 32 Real Voices 设置，不提高引擎预算。当前资产中没有另行增加音频声源的 prefab 改动。

混音器是 `Assets/Audio/Runtime/GameAudioMixer.mixer`，Master 下有 Music、SFX 两组。Stinger 走 Music，UI/流程/战斗/光环走 SFX。

本实现把用户线性增益统一合成在 source 上：`cueGain × master × music或sfx × 音乐淡化/暂停系数`；Mixer 总线保持默认 0 dB，Listener 不再乘用户音量。总静音使用 source.mute。此方案没有对 0 求 log 的过程，0% 能精确静音，避免 source/mixer/listener 重复乘音量。

| 分类 | 基础增益 | 同组实时冷却 | 并发上限 | 优先级 |
|---|---:|---:|---:|---:|
| BGM | 0.55 | 状态幂等 | 两个交叉淡化声源 | 100 |
| 胜负/评级短曲 | 0.70 | 每局调度 | 独立 1 | 100 |
| UI、塔操作、普通流程 | 0.50 | 0.08s | 3 | 75 |
| 普通开火 | 0.27 | 0.05s | 4 | 45 |
| 普通命中 | 0.22 | 0.08s | 3 | 30 |
| 爆破开火/爆炸 | 0.38 | 0.10s | 每组 3 | 55 |
| 生物受击 | 0.22 | 同组 0.12s；单敌人 0.20s | 2 | 25 |
| 生物死亡 | 0.36 | 0.08s | 3 | 60 |
| 冰霜脉冲 | 0.25 | 同组 0.30s；单塔 0.50s | 2 | 20 |
| 冰霜 loop | 0.18，再按槽数平方根分摊 | owner 活跃检测 | 4 | 20 |
| 漏怪/低血量 | 0.60 | 0.20s | 每组 1 | 95 |

短池最后 4 个槽只接优先级≥70 的声音；高优先级可抢占低优先级。超预算的请求立即丢弃，不排队补播。服务私有 `System.Random` 选择变体并避免连续重复，不消费战斗 `UnityEngine.Random`。仅短 SFX 轻微随机 pitch 0.97～1.03，音乐、短曲和光环始终为 1。

声源回收复位 clip、loop、pitch、volume、mute、mixer group、业务 owner 与暂停标记。被暂停的 source 不以 isPlaying=false 误判完成。所有增益是当前产品初值，密集战斗中的掩蔽、削波及疲劳仍需人工试听调校。

## 4. 实际业务落点

- 普通/爆破塔：在有效目标和 BulletConfig 已确认后的 `BaseTower.Fire()` 即时命中路径，分别申请开火和命中/单次爆炸声。爆炸主体在 AOE 外层只申请一次，不在每个目标上重复。
- 兼容子弹：`BulletManager.Fire` 在实际生成弹体后申请开火，`BaseBullet.OnHit/Explode` 申请命中。当前 BaseTower 不调用旧发弹路径，避免同一次攻击重复。
- 冰霜：`TickSlowAura()` 的 applied>0 分支才通知服务。每塔一个 owner，稳定选择最多 4 个有效循环；出售、替换、销毁、结算和离关清理。暂停保留光环剩余活跃时间，不因真实时间经过误回收。空射程圈和预览 ghost 不发声。
- 建造：`TryBuildInternal` 成功且 charge=true 时播放；快照恢复的 charge=false 保持静默。冰霜新建以激活声替代普通建造声。
- 建造失败：玩家提交放置被拒绝时通知，包括点击不可建格和拖放拒绝；每帧预览不播。点击已有塔转选中只播放选择，拖回 UI/棋盘外取消不当作失败。
- 升级/出售：在真正完成替换/登记或出售/退款后播放；升级返回 null 时请求一次 UiInvalid。ClearAll、恢复和自动重选不播成功声。
- 生物受击：`BaseEnemy.Hurt` 处理护甲后，未死亡且实际伤害≥1 时通知。单敌人冷却，死亡优先停掉该敌人尚在播放的受击叫声。
- 家族：Bats/Birds→wing；Insects/Scorpions/Parasites→insect；Cattle/Giants/Horses/Mounts/Dogs/Felines/Pigs→heavy；Apes/Bunnies/Rats→light；Inanimate 无动物叫声。以 MonsterCatalog.LogicalName/真实 family 缓存，未知项一次诊断后 light 降级，不改 MonsterCatalog。
- 死亡只订阅唯一 EnemyKilledEvent；漏怪订阅 EnemyReachedEndEvent；回收仅清掉敌人缓存引用，不播放死亡。一次性 source 不挂在池化敌人上。
- 低血量仅 delta<0 的真实扣血，首次跌入≤30% 时提示；恢复到>40% 或新局重置。初始化、恢复同步和治疗不报警；失败停止告警。
- 倍速在玩家实际改变成功后直接通知，初始化/恢复事件同步静默。暂停反馈对应真实暂停转换。
- UIManager 页面创建后幂等绑定 `UiAudio`，Select/Monster/Tower 图鉴动态条目在创建或首次池化绑定时补齐。只响应真实 pointer click/submit，不响应程序 onClick 调用、语言刷新或 SetValueWithoutNotify。升级、建造、HUD 开始/暂停/倍速等已有业务声音的按钮抑制普通 click，出售确认最终按钮也抑制通用声。

## 5. 资源、导入与释放

| 逻辑包 | 内容 |
|---|---|
| audio_runtime | GameAudioCatalog、GameAudioMixer |
| audio_music | 4 首 BGM、3 段 Stinger |
| audio_ui | 12 个 UI、16 个 Feedback |
| audio_combat | 34 个 Tower、24 个 Enemy |

已同步实际 `BundleCollectorSetting.asset` 与 `FTYooAssetSetupWizard.CollectPlan`，新增 7 个精确目录收集项：BGM、Stingers、SFX/UI、Tower、Enemy、Feedback 与 Audio/Runtime。原有组保留，EnableAddressable=false；FTBundlePackRule 按 ResTable 归包。README、CSV、生产源码和预览没有放进这些收集目录。

全部运行资源由逻辑名经现有加载器解析。目录内 WAV 使用带扩展名全路径或去扩展名全路径候选，不依赖文件名可寻址，也不使用运行时 AssetDatabase 回退。

- BGM：Streaming + Vorbis quality 0.75、立体声、保留 48kHz、不预解码；按当前/交叉淡化需求加载。
- SFX：DecompressOnLoad + PCM、单声道、保留 48kHz、关闭 normalize。PCM 保留短音色和循环边界；这 86 个素材的总样本量较小。
- Stinger：DecompressOnLoad + PCM、立体声，保留采样率，结算按需加载与预取。
- 同时设置默认与 Android 覆盖，精确处理 93 个 importer，保留 WAV/GUID。`sampleRateOverride=44100` 是 PreserveSampleRate 模式下未使用的序列化字段，不表示实际重采样。
- 用母版帧数×声道×4 作 float PCM 量级估算：全部 SFX 约 7.97 MiB，三段 Stinger 合计约 4.58 MiB；不是 Player 实测内存，另有 source、压缩包、流缓冲和 Unity 开销。全部 BGM 若全量解码约 107.48 MiB，因此采用流式按需方案。

| 循环 | 实际导入 samples | frequency |
|---|---:|---:|
| menu | 3840000 | 48000 |
| prepare | 4189091 | 48000 |
| battle | 3177931 | 48000 |
| pressure | 2880000 | 48000 |
| frost_loop_01 | 192000 | 48000 |

循环整段播放，末端不包含，不硬编码压缩后循环截点。Vorbis/Streaming 的实际接缝、首帧延迟和 Android 解码表现尚待听感/设备确认。

UI/非战斗小声音 Ready 后预热；战斗音效与局内反馈入关预热。每个资源最多等待 10 秒，一次预热批次以 20 秒为上限，失败不阻塞原游戏流程。未就绪的一次性请求丢弃，不补播历史操作。缺失资源只诊断一次，后续不逐帧重复发起失败加载；需要修复资源后重新初始化服务。

服务以 wanted/loading/cache 三组状态独占同一逻辑名的一份加载器句柄，不把每个声源当作新消费者。共享 clip 直到整类生命周期结束才 Release；未使用 Preload，因而不产生或伪造额外包引用计数。EndLevel 先停战斗声源、清 clip/owner 和请求，再释放战斗/结算资源；UI 常驻到 Shutdown，旧 BGM 淡出后释放。过期异步回调只释放不再需要的资源；新局仍需要的同 key 请求合并复用。未调用强制 GC 或每关 UnloadUnusedAssets。

本轮运行代码位于 FTProject.Runtime；AOT HotUpdateView prefab 未挂声音脚本。已通过标准 `HybridCLR.Editor.Commands.LinkGeneratorCommand.GenerateLinkXml()` 本地编译当前 Android 热更 DLL 并生成 `Assets/HybridCLRGenerate/link.xml`，包含 AudioModule、Slider、Toggle 与相关事件类型。未发布 DLL、构建真实资源包、构建 APK 或覆盖热更清单。下次按项目正常发布链构建匹配的新资源和运行 DLL，旧 Player 资源包不会因本轮源码修改自动获得声音。

## 6. 设置、三语言与存档

实际 `SettingView.prefab` 扩展为 940×860 的 Tactical Forge 对话框，保留现有语言、重置二次确认与关闭，沿用 UIFitInParent/安全区缩放。增加 3 条 slider 与 mute toggle，控件根具有完整点击区域；支持触屏拖动和键盘调整。slider 即时应用，只在一次调整结束时申请短例音，不强制绕过静音或 0%。

`AudioSettingsPrefabBuilder.Apply` 接在 TacticalForgePrefabBuilder.Apply 与 UIPrefabBuilder 的兜底 BuildSetting 分支；现有 UIResolutionLayout 也经 Tactical Forge 路径复用这套设置布局。重新生成设置页会保留音频控件。新标签和值由 SettingView 刷新，LocalizationPrefabBinder 跳过 Audio 前缀节点，程序同步使用无通知 API。

用户本轮单独授权定点写表后，Localization.xlsx 只新增以下 4 行，原 380 行未变，随后由标准 LubanExporter 导出 10 张表；没有直接写生成 JSON/C#，没有修改 __tables__ 或恢复旧声音表。

| key / English | 简中 | 繁中 |
|---|---|---|
| Master Volume | 总音量 | 總音量 |
| Music Volume | 音乐音量 | 音樂音量 |
| SFX Volume | 音效音量 | 音效音量 |
| Mute | 静音 | 靜音 |

JSON 版本继续为 2，SQLite schema 继续为 4。新 JSON 设置结构：

```json
{"settings":{"language":"zh-Hans","audio":{"version":1,"master":0.8,"music":0.65,"sfx":0.8,"muted":false}}}
```

SQLite 使用 `settings.audio.version/master/music/sfx/muted` 独立 kv_store 键，语言沿用 settings.language。master/music/sfx 使用 InvariantCulture 的 R 格式，muted 用 0/1。语言、五个音频键和 game_settings 时间戳在同一事务内提交，版本标记与数值原子一致；写入失败保留旧值并报告 LastError。

- 缺失 audio/null、无版本或未知版本采用统一默认：80%/65%/80%、mute=false。
- 旧 JSON 的 settings.volume/muted 继续忽略，不解释成新音量；保存仅输出合法的新嵌套 audio 字段。
- version=1 时显式 0 和 true 保留；越界值截到 [0,1]，NaN/无穷或 SQLite 无效文本降级到该字段默认。SQLite 缺字段用字段默认。
- schema 3 仍走原有 3→4 迁移，再初始化独立音频键；不恢复旧音量列。语言、进度、评级载荷和快照保持原语义。
- 控件变化先更新内存，0.35 秒延迟合并保存；拖动结束、设置关闭/禁用、应用后台/失焦/退出和 Launcher 销毁前 Flush。失败保留 dirty，5 秒后再尝试，并正常记录后端错误。
- 总静音不改三条音量；解除静音使用当前值。既有重置成功后恢复新默认，仍保留原二次确认，不为测试调用正式重置。

## 7. 本轮改动范围

新增：`Assets/Scripts/Audio/` 的 AudioPreferences、AudioCatalog、AudioManager/GameAudio、AudioRuntime、AudioResourceMap、UiAudio、AudioSliderFeedback；`Assets/Editor/AudioIntegrationSetup.cs`、`AudioSettingsPrefabBuilder.cs`；运行 catalog/mixer；`AudioPreferencesPersistenceTests.cs`；本文与三语言设置预览。

定点修改：Launcher、ResTable/ResBundle、UIManager、GameFlowManager、BaseTower、TowerPlacement、BaseEnemy、BaseBullet、GameSettings/SaveData、SaveManager、JSON/SQLite 存储、SettingView、LevelClearView、SelectView、TowerCodexView、MonsterCodexView、设置 prefab、UI 两条生成链、LocalizationPrefabBinder、TacticalForgePreview、收集器及其生成计划、93 份 WAV 导入 meta、旧存档兼容测试、标准导出的本地化和 link.xml、相关指导文档与本工程 AGENTS。

本轮没有运行敌人总导入/重建，没有写敌人 prefab、动画、方向图、材质或母版 WAV，没有改关卡数值、评级哈希、战斗快照含义或正式存档。工作区之前已有的大量 UI 和生成文件改动继续保留，不能把整个 git diff 都归为本轮声音修改。

## 8. 已执行检查与边界

| 检查 | 实际结果 |
|---|---|
| MCP 工程身份 | FishTestGame@0c9048e2c2ec99ee，projectRoot=D:/FishTestGame，2022.3.62f3c1，Android |
| 强制刷新/编译/重载检查 | 完成；is_compiling、is_domain_reload_pending、is_updating 均 false，ready_for_tools=true |
| 当前编译失败标记与控制台 | scriptCompilationFailed=false；最终 error 查询 0 条；没有清空控制台 |
| 隔离 EditMode 存储测试 | 7/7 通过，0 失败、0 跳过；job 49cc77e215b0472d948c33a43a3fdf69 |
| 兼容覆盖 | 新/旧 JSON、schema 3/4 SQLite、重复迁移、0%、静音、非有限值、小数文化、事务失败回滚、语言/进度/快照保留 |
| 资源静态核对 | 93 个有效 AudioClip，39 cues，全部 FTBundlePackRule 归包一致，93 个 Android 覆盖 |
| mixer 与设置 prefab | Music/SFX 分组有效；3 slider+mute；缺失组件 0 |
| 循环数据 | 上表 5 个资源导入 samples/frequency 与母版一致 |
| 表格保护 | 182 个受保护 XLSX SHA256 与任务开始时一致；Localization 仅批准的 4 行增量 |
| 标准导出与裁剪 | Luban 10 表导出成功；Android 热更 DLL 本地编译与标准 link.xml 生成成功 |
| 设置页编辑器预览 | 1280×720，en/zh-Hans/zh-Hant 三语言已检查，无文本/按钮遮挡；隔离预览不读取正式存档 |

历史/预期警告：旧编辑器工具使用过时动画/贴图接口、BaseManager 未使用字段、MCP 重载重连警告，以及事务回滚测试故意产生的 `audio-test-write-failure` 警告，不代表本轮实际存档写入失败。初次实现中发现的 AudioImporter API 和 mixer 反射调用问题已修复后重新完成检查。

测试均使用临时目录。没有进入 Play Mode、完整回放战斗、调用正式存档重置、构建/安装 APK、发布资源或人工听音。本轮只确认编辑器编译、配置一致性、离线 UI 几何及隔离存储行为，不能宣称 Android 音频性能或 Player 播放已验收。

## 9. 用户运行与听感验收步骤

1. 从正式 Boot 冷启动：主菜单有 menu；在选关、详情、双图鉴间导航后返回，menu 连续、不每开页重头。
2. 进关布阵→开战→普通回合结束→下一回合，依次检查 prepare/battle；生命≤30% 且驻留条件满足进入 pressure，恢复≥40% 后退出。结算和退出优先切走。
3. 三种塔分别选择、新建、失败、升级成功/失败、出售确认/取消。恢复快照不补播建造/升级/倍速；鬼影、红格预览、自动重选保持静默。
4. 普通命中、单次 AOE、多目标 AOE、四类敌人受击/死亡、Inanimate、DOT、漏怪及低血量。低血量连续扣血不连续报警，同一爆炸不因目标数扩大主体声数。
5. 暂停/继续、局中设置和×1/×2/×3：战斗/光环暂停，UI 可听，音乐降低增益而不升调；恢复不重置音量。
6. 密集战斗和多冰霜塔：UI、漏怪、低血量可辨识，声源不无界增长，光环不随敌人数持续变响；反复出售/升级后无悬挂 loop。
7. 胜利、失败、评级，立即下一关/重试/返回和结算切语言：只播本局结果，评级等待胜利结束，离开可取消；保存重试不会重播胜利或评级。
8. 三语言和小屏横屏操作设置：slider 即时生效、每次调整结束最多一次例音；0%、静音、解除静音、关页重开与应用重启恢复正确。不要用正式重置验证音量。
9. 旧档兼容自动测试已通过；如人工复查，请用正式档复制件与临时目录，确认语言、关卡、评级、快照无变化，不覆盖原档。
10. 获设备运行授权后，单独记录 Android 设备身份、APK/资源版本、后台/前台、音频打断、耳机/输出切换及性能。编辑器结果不能替代这一项。
11. 听四首 BGM 和 4 秒 frost loop 的接缝、起音，评估密集战斗削波、掩蔽、尖锐度与疲劳；目前仍为“人工听感待用户确认”。

三语言隔离预览位于 `Docs/UI_Redesign/Implementation/2026-10-26/evidence/SettingView-{language}-1280x720-audio-settings-isolated-editor-preview.png`。历史 UI 设计的无声音选项描述属于旧轮次，本轮以本文说明设置页扩展，不改写历史设计结论。

## 10. 维护入口

- `Tools/塔防/声音/生成音频配置与设置控件`：重建默认 catalog、确保 mixer 与声音收集目录、定点更新设置 prefab。catalog 已人工调音时先保留其差异，该入口会恢复默认 cue 策略。
- `Tools/塔防/声音/应用 93 个 WAV 导入策略`：只更新本清单导入设置，不修改源 WAV。
- `AudioIntegrationSetup.Validate()`：静态检查实际映射、类型、catalog、mixer 与设置控件；不代表运行或听感验收。
- 下次发版仍走项目标准 Luban/HybridCLR/YooAsset 构建链；本轮未更改线上发布状态。

## 附录：完整语义与文件登记

下表按当前 AudioResourceMap 自动整理；每个逻辑名等于对应 WAV 去扩展名。全部文件均为正式包中的实际文件。

| SoundCue | 相对目录 | 全部实际文件名 | 数量 | 逻辑包 |
|---|---|---|---:|---|
| `Menu` | `BGM` | `ft_bgm_menu.wav` | 1 | `audio_music` |
| `Prepare` | `BGM` | `ft_bgm_prepare.wav` | 1 | `audio_music` |
| `Battle` | `BGM` | `ft_bgm_battle.wav` | 1 | `audio_music` |
| `Pressure` | `BGM` | `ft_bgm_pressure.wav` | 1 | `audio_music` |
| `Victory` | `Stingers` | `ft_stinger_victory.wav` | 1 | `audio_music` |
| `Defeat` | `Stingers` | `ft_stinger_defeat.wav` | 1 | `audio_music` |
| `Rating` | `Stingers` | `ft_stinger_rating.wav` | 1 | `audio_music` |
| `UiClick` | `SFX/UI` | `ft_sfx_ui_click_01.wav`<br>`ft_sfx_ui_click_02.wav`<br>`ft_sfx_ui_click_03.wav` | 3 | `audio_ui` |
| `UiConfirm` | `SFX/UI` | `ft_sfx_ui_confirm_01.wav`<br>`ft_sfx_ui_confirm_02.wav` | 2 | `audio_ui` |
| `UiBack` | `SFX/UI` | `ft_sfx_ui_back_01.wav`<br>`ft_sfx_ui_back_02.wav` | 2 | `audio_ui` |
| `UiInvalid` | `SFX/UI` | `ft_sfx_ui_invalid_01.wav`<br>`ft_sfx_ui_invalid_02.wav` | 2 | `audio_ui` |
| `UiToggle` | `SFX/UI` | `ft_sfx_ui_toggle_01.wav`<br>`ft_sfx_ui_toggle_02.wav`<br>`ft_sfx_ui_toggle_03.wav` | 3 | `audio_ui` |
| `TowerSelect` | `SFX/Tower` | `ft_sfx_tower_select_01.wav`<br>`ft_sfx_tower_select_02.wav`<br>`ft_sfx_tower_select_03.wav` | 3 | `audio_combat` |
| `TowerBuild` | `SFX/Tower` | `ft_sfx_tower_build_01.wav`<br>`ft_sfx_tower_build_02.wav`<br>`ft_sfx_tower_build_03.wav` | 3 | `audio_combat` |
| `TowerBuildFail` | `SFX/Tower` | `ft_sfx_tower_build_fail_01.wav`<br>`ft_sfx_tower_build_fail_02.wav` | 2 | `audio_combat` |
| `TowerUpgrade` | `SFX/Tower` | `ft_sfx_tower_upgrade_01.wav`<br>`ft_sfx_tower_upgrade_02.wav`<br>`ft_sfx_tower_upgrade_03.wav` | 3 | `audio_combat` |
| `TowerSell` | `SFX/Tower` | `ft_sfx_tower_sell_01.wav`<br>`ft_sfx_tower_sell_02.wav`<br>`ft_sfx_tower_sell_03.wav` | 3 | `audio_combat` |
| `NormalFire` | `SFX/Tower` | `ft_sfx_normal_fire_01.wav`<br>`ft_sfx_normal_fire_02.wav`<br>`ft_sfx_normal_fire_03.wav`<br>`ft_sfx_normal_fire_04.wav` | 4 | `audio_combat` |
| `NormalHit` | `SFX/Tower` | `ft_sfx_normal_hit_01.wav`<br>`ft_sfx_normal_hit_02.wav`<br>`ft_sfx_normal_hit_03.wav` | 3 | `audio_combat` |
| `BlastFire` | `SFX/Tower` | `ft_sfx_blast_fire_01.wav`<br>`ft_sfx_blast_fire_02.wav`<br>`ft_sfx_blast_fire_03.wav` | 3 | `audio_combat` |
| `BlastHit` | `SFX/Tower` | `ft_sfx_blast_hit_01.wav`<br>`ft_sfx_blast_hit_02.wav`<br>`ft_sfx_blast_hit_03.wav` | 3 | `audio_combat` |
| `FrostActivate` | `SFX/Tower` | `ft_sfx_frost_activate_01.wav`<br>`ft_sfx_frost_activate_02.wav`<br>`ft_sfx_frost_activate_03.wav` | 3 | `audio_combat` |
| `FrostPulse` | `SFX/Tower` | `ft_sfx_frost_pulse_01.wav`<br>`ft_sfx_frost_pulse_02.wav`<br>`ft_sfx_frost_pulse_03.wav` | 3 | `audio_combat` |
| `FrostLoop` | `SFX/Tower` | `ft_sfx_frost_loop_01.wav` | 1 | `audio_combat` |
| `LightHit` | `SFX/Enemy` | `ft_sfx_light_hit_01.wav`<br>`ft_sfx_light_hit_02.wav`<br>`ft_sfx_light_hit_03.wav` | 3 | `audio_combat` |
| `LightDeath` | `SFX/Enemy` | `ft_sfx_light_death_01.wav`<br>`ft_sfx_light_death_02.wav`<br>`ft_sfx_light_death_03.wav` | 3 | `audio_combat` |
| `WingHit` | `SFX/Enemy` | `ft_sfx_wing_hit_01.wav`<br>`ft_sfx_wing_hit_02.wav`<br>`ft_sfx_wing_hit_03.wav` | 3 | `audio_combat` |
| `WingDeath` | `SFX/Enemy` | `ft_sfx_wing_death_01.wav`<br>`ft_sfx_wing_death_02.wav`<br>`ft_sfx_wing_death_03.wav` | 3 | `audio_combat` |
| `InsectHit` | `SFX/Enemy` | `ft_sfx_insect_hit_01.wav`<br>`ft_sfx_insect_hit_02.wav`<br>`ft_sfx_insect_hit_03.wav` | 3 | `audio_combat` |
| `InsectDeath` | `SFX/Enemy` | `ft_sfx_insect_death_01.wav`<br>`ft_sfx_insect_death_02.wav`<br>`ft_sfx_insect_death_03.wav` | 3 | `audio_combat` |
| `HeavyHit` | `SFX/Enemy` | `ft_sfx_heavy_hit_01.wav`<br>`ft_sfx_heavy_hit_02.wav`<br>`ft_sfx_heavy_hit_03.wav` | 3 | `audio_combat` |
| `HeavyDeath` | `SFX/Enemy` | `ft_sfx_heavy_death_01.wav`<br>`ft_sfx_heavy_death_02.wav`<br>`ft_sfx_heavy_death_03.wav` | 3 | `audio_combat` |
| `RoundStart` | `SFX/Feedback` | `ft_sfx_round_start_01.wav`<br>`ft_sfx_round_start_02.wav` | 2 | `audio_ui` |
| `RoundClear` | `SFX/Feedback` | `ft_sfx_round_clear_01.wav`<br>`ft_sfx_round_clear_02.wav` | 2 | `audio_ui` |
| `EnemyLeak` | `SFX/Feedback` | `ft_sfx_enemy_leak_01.wav`<br>`ft_sfx_enemy_leak_02.wav`<br>`ft_sfx_enemy_leak_03.wav` | 3 | `audio_ui` |
| `LowHp` | `SFX/Feedback` | `ft_sfx_low_hp_01.wav`<br>`ft_sfx_low_hp_02.wav` | 2 | `audio_ui` |
| `Pause` | `SFX/Feedback` | `ft_sfx_pause_01.wav`<br>`ft_sfx_pause_02.wav` | 2 | `audio_ui` |
| `Resume` | `SFX/Feedback` | `ft_sfx_resume_01.wav`<br>`ft_sfx_resume_02.wav` | 2 | `audio_ui` |
| `SpeedChange` | `SFX/Feedback` | `ft_sfx_speed_change_01.wav`<br>`ft_sfx_speed_change_02.wav`<br>`ft_sfx_speed_change_03.wav` | 3 | `audio_ui` |

合计 39 个语义、93 个 WAV。相对目录根为 `Assets/Audio/OriginalPack_20261023/`；表格是实现文档快照，运行时唯一登记仍为 AudioResourceMap/ResTable。

另有 `GameAudioCatalog` → `Assets/Audio/Runtime/GameAudioCatalog.asset`、`GameAudioMixer` → `Assets/Audio/Runtime/GameAudioMixer.mixer`，两者均归 `audio_runtime`。
