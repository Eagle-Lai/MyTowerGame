# VOL_03 配置 / 多语言 / UI

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：Luban 表与重导、多语言词条与 TextLocalizer、名字本地化、UI 生成器 UIPrefabBuilder、全量重建副作用、HUD 两按钮职责。

## 配置 / 多语言 / UI
- Luban：改任何 xlsx 必重导（菜单 3）；新表要在 `__tables__.xlsx` 登记；字段从 B 列开始；`ResTable.cs` 是唯一寻址源。
  - ★`gen_code_json.bat` 会删 `FTProject.Gen.asmdef` → CS0246，跑完要还原。
- 多语言：主键 = 英文原文。
  - ★`gen_localization_table.py` 里的 ROWS **已过期**（168 条 vs 表内 352 条），**禁止重跑**（会丢 180+ 词条）。加词条走 `.workbuddy/tools/append_localization_*.py` + 菜单 3。
  - `TextLocalizer` 的 key 留空会自动取文本；回退链：当前语言 → 英文 → 原文。菜单 308 挂载 / 309 清除。
  - 改 SettingView 的文案 → 重建 → 308 → 菜单 4。
  - ★★两态文本（MuteBtn、Btn_Pause 的 Pause⇄Continue）**不能挂 TextLocalizer**（会被刷回原文）；308 时按父节点名跳过，由 View 按状态写入 + 监听语言事件重算。
- ★名字本地化：塔名 = `TowerConfig.DisplayName`｜关卡名 = `Localization.LevelName(id)`｜怪物名 = 123 词条（`Get(name) ?? name`）。★在 `Awake` 里一次性写文案是坑（切语言不刷新）。
- UI 生成器 `UIPrefabBuilder`：改文案/布局 = 改它 + 重编译 + 重生成。
  - ★塔图标 `UI_TowerIcon_{Normal,Power,Retard}` = 96×96 透明底（`ui_hud`），改图跑 `tower_icon_bg_remove.py`。
  - ★logo = `Assets/Art/Logo/app_icon_512x512.png`（ResTable 里登记 `UI_AppLogo`）。
- ★★用 MCP 验证 UI 时严禁 instantiate 预制体的子物体（TMP 的 OnEnable 会把状态写回资产）→ 自搭 Canvas + Image。
- ★refresh/编译会触发 AB 打标 → 改写 UI prefab / .meta 的 `assetBundleName`；提交前用 `diff_ui_prefabs.py --base` 核对。
- ★★全量重建三个副作用：重排 fileID／清空 `assetBundleName`／抹掉 TextLocalizer → 必须「重建 → 308 → 菜单 4」补齐。
  - 关键尺寸：塔按钮 96×96、VolumeSlider 480×65、`TowerCodexItem` / `SelectLevelItem` 根节点 active=false。
  - ResTable 漏登记 = 真机打不开。
- ★HUD 右上两按钮职责：`Btn_Pause` = 只切暂停/继续（不弹窗，两态文本）；`Btn_Intro` = 只打开暂停菜单（不暂停，文案 `Menu`）。暂停的唯一写入口 = `GameClock.SetPaused`，`PauseView` 不写 timeScale；标题按 `IsPaused` 取词。

## Luban 多文件 input 与拆表（2026-10-21 实测，未落地）

- ★`__tables__.xlsx` 的 `input` 列**支持逗号分隔多个 xlsx**，Luban 会合并成一张逻辑表、导出单一 json，行序 = 文件声明顺序；支持子目录相对路径（`Levels/L01/RoundData.xlsx`）。这是"物理按关拆表、逻辑仍是单表、运行时零改动"的唯一可行路径。
- ★★**一个 xlsx 里不能放多张表**：Luban 会把该文件**所有 sheet** 按同一张表读入（实测 `OtherData` sheet 的 id=91 被并进 TBRoundData）。所以"每关一个工作簿、内含关卡/波次/出怪多张 sheet"**被否决**，只能"每关一个目录 + 每张表一个文件"。
- ★跨文件重复主键会明确报错（`主键字段:'id' 主键值:'1' 重复`），不会静默覆盖——拆表出错能被抓住。
- 命令行：`Luban.ClientServer.exe -j cfg -c <cache> -- -d <root.xml> --input_data_dir ... --output_code_dir ... --output_data_dir ... --gen_types code_cs_unity_json,data_json -s all`。`-d` 必须在 `--` 之后，否则报 `unknown argument:-d`；环境变量 `DOTNET_ROLL_FORWARD=LatestMajor` 必带；缺 `__beans__.xlsx` / `__enums__.xlsx` 会直接失败。
- ★易漏的**非**管线消费者：`Assets/Editor/LevelMapEditorWindow.cs` 的「一键写入」→ `.workbuddy/tools/apply_levelmap_export.py`，脚本里硬编码 `Datas/LevelMap.xlsx` 与 `Datas/SceneInfo.xlsx`，拆表后必须按 `level_id` 改路径（C# 侧只读 `ConfigJson/tblevelmap.json`，不用改）。
- 历史脚本（`add_levels_9_15/16_20_*.py`、`apply_m2_*.py`、`gen_wave_data.py`、`gen_m3_waves_rounds.py`、`gen_challenge_data.py`）直写聚合表，拆表后失效 → 标 LEGACY，不修。
- 拆表验收口径：**纯物理拆分必须做到 `Assets/ConfigJson/tb*.json` 语义等价**，按 id 排序逐字段比对。

## 改配置表的标准动作与三个坑（2026-10-31 实测）

> ★★★**2026-11-01 重大变更：星级评分体系整体删除。** `tblevelrating` 表、30 张 `Levels/Lxx/LevelRating.xlsx`、
> `LevelRatingEvaluator/Profile/Result`、`RatingPresentation`、`SaveProgressMigration`、`Configs.VerifyRatingContent/
> CalculateRuntimeContentHash/ValidateRatingPlan/RatingContentVerified`、编辑器 `LevelRatingTests` 全部移除；
> 通关一律记 `SaveManager.MaxStars`（5 星）。**本节下面关于 `runtimeContentHash` 重封的内容全部成为历史记录**，
> 现在改表只需「改 xlsx → 跑 Luban 导出 → 进 Unity 看 `[Config]` 无失败表」。
> 顺带：`.workbuddy/tools/_rating_hash.py` 已删除（没有哈希可重封了）。评分待 30 关数值定稿后重做。

- **流程**（AGENTS.md 口径）：改 `Levels/Lxx/*.xlsx` → 跑 Luban（`DOTNET_ROLL_FORWARD=LatestMajor Luban/Tools/Luban.ClientServer/Luban.ClientServer.exe -j cfg -c Luban/.cache.meta -- -d Luban/Config/Defines/__root__.xml --input_data_dir Luban/Config/Datas --output_code_dir Assets/Gen --output_data_dir Assets/ConfigJson --gen_types code_cs_unity_json,data_json -s all`，别用 `gen_code_json.bat`，末尾 `pause` 会卡住非交互会话）→ **重封 `runtimeContentHash`**。
- ★★**Luban 导出会删掉 `Assets/Gen/FTProject.Gen.asmdef`**（日志 `[remove] file: ...FTProject.Gen.asmdef`）。每导一次就要 `git checkout -- Assets/Gen/FTProject.Gen.asmdef`，否则 Gen 代码掉进别的程序集。同一次导出里 `Assets/Gen/*.cs` 只是行尾变化（git diff 为空），不用管。
- ★★**`runtimeContentHash` 是全局哈希，同一个值写进全部 30 张 `Levels/Lxx/LevelRating.xlsx`**（不是每关一份）。算法权威是 `Configs.CalculateRuntimeContentHash`：9 张 json（多一个 `tblevelrules`，比 `balance_pipeline.py` 里那个 Python 版本多）按 `key\n内容\n` 拼接（去 BOM、CRLF→LF），再接 30 行评级字段（17 个，`runtimeContentHash` 自身不参与），SHA256 小写十六进制。
  - 实操校验法：先用该算法复算**改动前**的哈希，若等于表里现值（= Unity 日志 `[Rating] Runtime configuration SHA256 verified` 的那个），说明实现正确，再算改动后的值写回、重跑一次 Luban 让 `tblevelrating.json` 带上新值。
- ★★**`EnemyList.desc` 里的 EHP 口径 = Σ hp ÷ (1−armor)**（含护甲），不是 Σhp。写调参记录时算错会留下假数据；先拿上一条记录的 EHP 反推验证口径再写。
- ★`Levels/L01/EnemyData.xlsx` 的敌人变体是**每波一个独立 id**（如 W20=5000195、W21=5000205、W22=5000215），`EnemyList.EnemyIndexs` 里只被该波引用 → 改某波血量不会外溢；改前确认 `isFlying` 与引用波次，避免改错行。
- ★**现成重封脚本**：`.workbuddy/tools/_rating_hash.py`（2026-11-01 新建）。无参＝按 C# 算法复算并逐关打印 `OK/DIFF`；`--seal`＝写回 30 张 LevelRating 并回读校验。用法固定为「先无参复算改动前值 == 表内值，再改表导出，再 `--seal`」，`--seal` 之后必须**再跑一次 Luban** 让 `tblevelrating.json` 带上新值（哈希不含 `runtimeContentHash` 字段，重导不会改变哈希值）。
- ★`Assets/ConfigJson/tbenemydata.json` 的 `hp` 被 Luban 序列化成 **6 位有效数字**（`546.033103` → `546.0331`、`491.429793` → `491.42978`）。游戏读的是 JSON 值，表里保留 6 位小数；误差 1e-5 量级，属既有行为，但**别拿 JSON 值反算百分比**（会算出 −10.0002% 之类）。

## 改关卡数值的范围铁律与执行话术（2026-11-01 用户定规）

- ★★★用户提出"改关卡数值"时：**先问再改**，不是先改再汇报。四问固定：①哪几关（`L01`…`L30` 具体编号）②粒度（表 / `roundId` / 怪种 / 字段）③数值与口径（目标值或倍率、基准是配置现值还是实测值）④本轮是否"全部关卡应用"。
- 默认范围 = 用户点名的那一部分。禁止：顺手把其他关改成一致、把同类行一起对齐、做"顺便调平"、因导出产物看起来不一致而回改其他关的表。
- 跨关授权只在**当次请求**有效；"上次你说过全部关卡"不能复用。
- 交接口径：报告 `文件 / 关卡 / 波次 / 字段 / 旧值 → 新值`，并给出"其余关卡未改动"的可复核证据（`git diff --stat`、导出 json 行数比对）。
- 常见误判排查：`runtimeContentHash` 要在 30 张 `LevelRating.xlsx` 写同一个值（全局哈希），这是流程要求、**不算**扩展到其他关；拆分不清时先看 `Assets/ConfigJson/tblevelrating.json` 是否 30 行同值。
- 定位前先确认"这个 id 只被目标波次引用"（如 `EnemyList.EnemyIndexs` 只在 W22 引 `5000215`），确认后再动手；不确定就回到第①问向用户确认，不要自己扩大范围找"更合适"的行。


## ★用脚本生成关卡表的三组必查断言（2026-11-02 踩坑）

- 背景：`Tools/generate_l02_final.py` 以 L01 为模板生成 L02 四张表，编译与 Luban 导出都成功，但数据是坏的。**「导出成功 + 编译通过」不能证明表对**。
- ★断言一「`levelId` 分布」：导出后按 `levelId` 分组统计 `tbenemydata.json`，**目标关必须有自己的 levelId 且条数等于本关 xlsx 行数**。本次 L02 新写的 106 条全部落在 `levelId=1`，导致 `levelId=2` 记录归零、L01 分组条数翻倍。
- ★断言二「`SceneInfo` 关键字段」：逐字比 `name / mapId / MapName / CameraPosition / initialGold / initialHp / desc`。本次 L02 的 SceneInfo **整行是 L01 的**（`mapId=1`、`MapModel1`、`initialHp=10`、desc 也是 L01），且 `initialGold` 被写成 **2**（脚本参数是 100）。这类错不会报错，只会让目标关加载别的地图、开局 2 金。
- ★断言三「首末波 hp + 总数」：取目标关 W1/W5/W25 的地面与空中各一条，和 L01 同波同怪比比值；再比 hp 总和。本次比值恒为 1.05，把此前手工调过的 0.75 覆盖掉了都能从这两组数看出来。
- 生成器写「基于 L01 模板」时，**SceneInfo / LevelMap / LevelRules 这类「一关一行」的表必须从目标关原表读，不能从模板抄**；`EnemyData` 的 id 段与 `levelId` 要在同一处赋值，别一个用 `id_base` 一个用源表列。
- 提交这类产物前先问自己：这份表能不能在不看文档的情况下自证？不能就别标「完成」，标 WIP。

## UI 品牌化与字号层级（2026-11-02，桌面《UI界面问题文档》19:12 版实施）

### 四层同步（任何品牌文案/字号改动都按此走，缺一层必翻车）

1. **源表** `Luban/Config/Datas/Localization.xlsx`：改单元格 → 跑标准 `LubanExporter.ExportInternal`（导出 11 张表）→ 只应改 `Assets/ConfigJson/tblocalization.json`。
2. **AOT 启动层** `Assets/AOTAssembly/BootLocalization.cs`：`BrandTitleKey`/`BrandSloganKey` 常量 + `Get(key, language)` 显式语言重载。**APK 内的启动页/更新页不能挂 `TextLocalizer`**（那是热更层，AOT 阶段还没有）；`"Title"` 与 `BrandTitleKey` 走同一分支，旧 `"游戏更新"/"GAME UPDATE"` 文案已删除。
3. **实际 prefab**（5 个）：`Assets/Resources/BootUI/HotUpdateView.prefab`、`Assets/HotUpdateUI/LoadingView.prefab`、`Assets/HotUpdateUI/SplashView.prefab`、`Assets/Prefabs/UI/MainMenuView.prefab`、`Assets/Prefabs/UI/{ConfirmView,SellConfirmView}.prefab`。
4. **生成器**：`TacticalForgePrefabBuilder.BrandText/ApplyBrandTypography`（规则）、`UIPrefabBuilder`（首次生成的初始文案与字号）、`TacticalForgeLayout`（主菜单 `Panel/GameTitle` 144 高 / `Subtitle` 88 高，运行时按分辨率重排）。只改 prefab → 下次重生成被覆盖；只改生成器 → 现场 prefab 不更新。

- **词条约定**：品牌名主键仍是 `FREEDOM TOWER`（值改成 `Freedom Tower` 只为显示大小写，**不要动主键**，代码里 `BrandTitleKey` 用它）；slogan 主键 = 英文整句 `Winding paths, thrills at every turn.`（id 与 en 同值，简中「曲径通幽，步步惊心」/ 繁中「曲徑通幽，步步驚心」），在 `Localization.xlsx` 第 385 行。**换 slogan = 改这一行 + 重导表 + 跑菜单 `Tools/塔防/Tactical Forge/同步问题文档修正（2026-11-02）`（MenuItem priority 94）**。
- **字号层级**（TMP 逻辑画布基准，实际随分辨率缩放）：HotUpdate 104/40（状态·进度·失败 22、下载详情 20、按钮 24）；Loading 104/40（状态 22、百分比 24、提示 20、按钮 24）；Splash 112/40（启动提示 22、版本 18）；MainMenu 96/40（统计 24、主操作 28、次要按钮 24、版本 18）。品牌标题/slogan 的 `fontSizeMin` 固定 **72 / 32**，否则 auto-size 会把层级差抹平。辅助文字统一走 `ApplyBrandTypography`，`ButtonAt`/`FontSize` 会同时设 `fontSizeMax`。

### 四个坑（都是本次踩的）

- ★**`BrandText` 会改字体资产**：它对英/简/繁三语各跑 `_font.HasCharacters` → `TryAddCharacters`，缺字直接 `throw`（`Brand font is missing characters: ...`）。加新中文 slogan 前先确认 `Assets/_UIAssets/UI/TacticalForge/Fonts/TacticalSans.asset` 有字形；生成时会自动补进图集并 `SetDirty`，**这个 .asset 要跟着提交**（本次补了「曲/惊/驚」）。保留原 GUID，不要让 TMP 生成新字体资产。
- ★**ConfirmView 去图标要三处一起删**：`ConfirmView.cs` 的 `_dangerIcon` 字段与两处赋值、prefab 的 `Panel/DangerIcon` 节点、生成器里的 `DangerIcon`/`StatusGlyph` 创建段。只删 prefab 会在 `panel.Find("DangerIcon").GetComponent<Image>()` 直接 NRE。删后 `BodyText` 由 `(160,140,752)` 改全宽 `(48,140,864)`。
- ★**LoadingView 的 `StatusText` 不要挂 `TextLocalizer`**：生成器里 `DestroyImmediate` 掉了；运行时 `Awake` 先写「Initializing resources...」、`OnProgress` 到 1.0 写「Starting...」（旧版会覆盖成 Ready 标题）。要改文案改 `Assets/Scripts/UI/LoadingView.cs`，不是改表。
- ★**`TowerBuildMenu` 的视觉必须在 `Configure` 末尾应用**：生成器也会调 `Configure` 保存 prefab，只写在 `Awake` 会让「新生成 prefab」与「旧 prefab 运行时修补」两套表现不一致。样式口径：face 全透明 + `ColorBlock` 五态全透明 + 关 Outline，`IconWell` 84×84、`PriceBadge` 76×20（深金 + 塔色描边）、`PriceMark` 10×10 金币点，图标 68×68，名字 19（下限 14，SemiBold），价格 18（下限 13，Bold，金色 `1,0.8,0.34`），Backdrop 340×340 / `(.12,.22,.31,.28)`。**本次没有重跑菜单 93（HUD 建造圆盘）**，HudView 靠运行时 `ApplyButtonVisuals` 兜底；要固化进 prefab 就跑菜单 93。
- **SellConfirmView 单底板**：`SharedContentPlate(root, surfaces, "Panel/ContentBacking", 0, 24, 936, 440, 塔图/塔名/警告/退款标签/退款值 5 个节点)`，然后把 `paths` 置 `Array.Empty<string>()`，否则 `ApplyContentSurfaces` 还会给每行补一块独立底板。

