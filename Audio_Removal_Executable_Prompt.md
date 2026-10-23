请结合本 Unity 工程的实际依赖，彻底移除游戏自身的声音系统及其资源、配置、界面、存档设置和生成入口，使游戏成为完整可运行的无声版本。需要落实修改并完成验证，不要只提交分析或删除清单，也不要用全局静音、音量置零、空实现或保留空音频表替代删除。

以下路径相对于最终核实的工程根目录。执行前重新扫描，以实际文件和引用为准。

1. 核对工程身份和已有改动。

   当前检查的工作区是 D:\FreedomTower_1，ProjectSettings/ProjectVersion.txt 为 Unity 2022.3.62f3c1；AGENTS.md 却约定 E:\MyTowerGame，且本次检查时该路径不存在。先查明工程路径是否迁移或存在映射，核对实际修改目录与 Unity 打开的工程一致。不要用另一份工程的编译、运行结果验证当前工作区。

   编辑器操作严格遵守 AGENTS.md：读取 unityMCP 的 mcpforunity://custom-tools、mcpforunity://instances，使用当前列表里的完整实例 ID 调用 set_active_instance，再读取 mcpforunity://project/info 核对 projectRoot 和版本。使用本项目 8082 服务，不使用 CatchFish_Android 的 8080。断线按规范自主恢复；身份矛盾未解决时不得对未确认的实例执行修改。

   先检查 git status 并保留已有改动。当前 Assets/Audio 目录、16 个音频文件及相关 .meta 已在 Git 中显示为待删除，沿用该删除状态，不恢复或重新生成它们。

2. 移除声音业务代码及调用依赖。

   删除以下专用脚本，并正确处理对应 .meta 和序列化组件引用：
   - Assets/Scripts/Core/Manager/AudioManager.cs
   - Assets/Scripts/Core/Manager/AudioFadeDriver.cs
   - Assets/Scripts/Core/UI/UiClickSfx.cs
   - Assets/Scripts/Data/AudioName.cs
   - Assets/Scripts/Data/AudioConfig.cs
   - Assets/Scripts/Data/AudioCatalog.cs

   清理 Launcher 中的管理器注册、初始化和 ApplyToAudio；清理 UIManager 中 EnsureClickSfx 的实现、调用和动态组件挂载；删除 BaseTower、BaseEnemy、GameFlowManager、PlayerDataManager 中所有 BGM、开火、建造、升级、出售、受击、死亡、漏怪、回合、胜负及按钮声音调用。

   清理 Configs.cs、Configs.EditorCandidates.cs 中 AudioTable、GetAudio、音频索引缓存、tbaudio 加载及预加载项、候选配置构造和回滚逻辑、统计输出，并检查日志格式参数。清理 ResTable.cs 的 tbaudio 注册和 RegisterAudio，清理 ResBundle.cs 的 Audio 常量及 All 集合构造。所有关联调用方同步调整，不留下专用音频类型、假接口、失效注释和错误的表数量假设。

   删除声音调用时，保留调用相邻的伤害、金币、生命、回合、结算、动画、特效、后坐、震动和 UI 转场逻辑。MonsterAnimEventReceiver 同时负责 SetHead 等动画事件，不能因注释提到声音而整类删除；若清理专用声音事件，必须同步处理动画事件发送端，避免 has no receiver。

3. 清理设置界面与存档，保留旧存档兼容。

   同步修改 Assets/Scripts/UI/SettingView.cs、Assets/Prefabs/UI/SettingView.prefab 和 Assets/Editor/UIPrefabBuilder.cs，移除 VolumeText、VolumeSlider、MuteBtn 及其文本、字段、事件监听和刷新逻辑。重新布局剩余的语言、重置和关闭功能，确保没有空洞、重叠、失效导航及悬空引用。同步调整 LocalizationPrefabBinder.cs、LocalizationPrefabCleaner.cs 等相关工具。

   清理 SaveData.cs 中 GameSettings.volume、muted 及仅为音量存在的 Clamp；清理 SaveManager 的 SetVolume、SetMuted、ApplyToAudio 以及相关调用。检查 JsonSaveStorage、SqliteSaveStorage 和 SaveSchema：当前 SQLite 的 game_settings 表实际含 volume、muted 列，读写 SQL 直接访问这些字段，不能只删 C# 字段。

   对 SQLite 设计与实际后端兼容的版本迁移，使新建数据库和迁移后的旧数据库都不再使用音频设置；必要时在事务中重建相关设置表，不依赖未经确认支持的 DROP COLUMN。保留 settings.language 及其他有效数据。旧 JSON 中多出的声音字段应能安全忽略，重新保存不再写入这些字段。不得通过清档、删除数据库或无条件重置进度解决兼容问题。迁移过程使用的历史字段名可以保留，并在交付说明中解释。

4. 从源表移除音频配置，通过 Luban 更新产物。

   移除 Luban/Config/Datas/AudioData.xlsx，并通过人工编辑工作簿的方式删除 Luban/Config/Datas/__tables__.xlsx 中对应 TBAudio 的登记；核对关联定义和引用。人工清理 Localization.xlsx 中仅服务于声音的 Volume {0}%、Volume +、Volume -、Mute、Unmute 等条目，保留仍有其他用途的文本。

   严格遵守 AGENTS.md 的手工改表规定，禁止使用 Python、PowerShell、Excel COM、openpyxl 等脚本写入或批量改写受保护的配置表。不要执行现存旧写表脚本，也不要恢复 balance_pipeline.py 已删除的 apply、rollback 或事务写表能力。

   源表调整后，使用现有 Assets/Editor/LubanExporter.cs 提供的正常导出流程，优先复用其保护 FTProject.Gen.asmdef 及 .meta 的机制。由 Luban 更新 Assets/Gen/Tables.cs，移除旧的 AudioData.cs、TBAudio.cs、Assets/ConfigJson/tbaudio.json 等导出产物，并检查孤立 .meta 的处理。禁止手写、脚本直改或绕过源表直接删除 Assets/Gen/**、Assets/ConfigJson/** 下的产物。

   当前 Configs.CalculateRuntimeContentHash 的输入未包含 tbaudio 和 tblocalization。核对导出是否意外改变参与校验的其他表，不因本次音频删除修改平衡参数或批量重写 Levels、EnemyData。若确实涉及关卡源表变更，按既有手工流程重算并重封各关 runtimeContentHash。运行时必须继续通过 [Rating] Runtime configuration SHA256 verified 校验。

   如缺少人工工作簿编辑能力，先完成可独立处理的工作，明确列出尚需手工调整的工作簿、登记和后续导出步骤；不得违规使用脚本补写，也不得将未完成的配置清理报告为完成。

5. 清理场景、资源收集和会重新生成声音的工具。

   扫描项目自有场景、预制体、动画事件和 Timeline，删除纯音频对象及 AudioSource、AudioListener、AudioMixer、音频轨道和音频专用脚本引用；已确认 Assets/Scenes/Boot.unity 中存在 AudioListener。混合对象只移除音频组件，保留摄像机和其他功能。检查 Missing Script、丢失 GUID、UnityEvent 及序列化引用。

   清理 Assets/BundleCollectorSetting.asset 和 Assets/Editor/YooAsset/FTYooAssetSetupWizard.cs 中 Audio / Assets/Audio 收集项，清理项目自有配置预检和资源清单中的音频条目。检查 Assets/HybridCLRGenerate/link.xml 的生成来源，由正确的生成流程调整仅为声音需要的保留项；核实共享依赖后再处理，避免下次生成恢复。

   删除 Assets/Editor/PlaceholderBgmGenerator.cs、.workbuddy/tools/gen_audio_catalog.py、.workbuddy/tools/apply_m2_audio_table.py 等专用声音生成工具及相关菜单入口、引用。同步清理 gen_m3_ui_prefabs.py、gen_localization_table.py 中会重建音量、静音控件或文案的内容，以及 check_arity.py 等检查器中的已删除文件路径。其他历史脚本如仍含声音处理分支，也要核实和处理，禁止运行它们改写配置表。

   更新仍用于指导当前工程的文档，移除恢复声音的操作步骤和过时功能描述。历史证据、备份、Git 历史及既有发布产物不做关键词式批量清除；不得顺手删除整套文档、Library、Builds、Bundles 或服务器目录。

   本任务的删除范围是项目自身的声音功能和专用内容。Unity 标准 ProjectSettings/AudioManager.asset、Packages 的内置音频模块，以及 DOTween、iTween 等共享插件的通用音频 API，按实际依赖判断；不要为追求 audio 关键字零命中而破坏引擎设置和第三方库。若保留共享依赖，最终说明具体原因。后续构建和热更新生成的有效清单不得再包含本项目已删除的音频资源；本任务不自动发布或覆盖线上内容。

6. 验证并交付结果。

   开始运行时验证前先读取目标工程当前错误日志，记录基线，不擅自清空 Console。完成同一批 C# 修改后，核对实例并调用 refresh_unity(mode="force", scope="all", compile="request", wait_for_ready=true)，每隔 1～2 秒读取 editor/state，直到 is_compiling=false、is_domain_reload_pending=false、is_updating=false、ready_for_tools=true。编译期间不继续修改代码。

   调用 read_console(action="get", types=["error"], count="50", format="json") 检查编译错误与异常，需要时用 filter_text="error CS" 定位并分页；execute_code 可用时补查 UnityEditor.EditorUtility.scriptCompilationFailed 应为 false。修复后重复上述验证。MCP 断线按 AGENTS.md 限次恢复，恢复后重新选定实例并核对工程身份。

   在目标工程的隔离测试存档环境中验证启动、加载配置、选关、进入战斗、建造/升级/出售、受击/死亡/漏怪、回合切换、胜利/失败、返回选关、设置开关、语言切换和继续游戏。验证新存档、含旧声音字段的 JSON 存档和旧 SQLite 数据库升级，不修改用户正式存档。验证完整流程无声、运行时不再生成 AudioRoot 或项目音频组件，且无由移除 AudioListener 引起的告警；如需引擎配置调整，应有实际验证依据。

   检查 UI 重建、资源收集设置重建和正常 Luban 重导不会重新生成声音内容。对有数据丢失风险的存档迁移添加必要的兼容性测试，复用适当的现有测试；不为删除静态文件编写无意义测试。完成全局引用、资源 GUID、Missing Script 和配置加载检查，确认评级 SHA256 校验仍通过。

   最终用中文给出：实际修改的工程路径、删除和修改清单、配置表与 Luban 导出结果、存档兼容方案、编译与运行验证证据、保留的共享音频依赖及原因、尚未完成或无法验证的项目。未连接目标 Unity 时，明确写出失败环节和“Unity 编辑器验证未完成”，不得声称编译或运行验证通过。
