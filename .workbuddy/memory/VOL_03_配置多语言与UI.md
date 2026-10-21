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
- 拆表改造的必改点（`balance_pipeline.py`）：`source_hashes()`（否则 `assert_sources` 误报源表被改）、`excel_write()`（按 L 分文件 + `tbenemydata` 原型/变体分流）、`write_rating_excel()`、`__tables__` input 自动生成、`commit_files()` 的**删除事务**（旧聚合文件必须消失且可回滚）、`validate()` 加归属一致性。
- ★易漏的**非**管线消费者：`Assets/Editor/LevelMapEditorWindow.cs` 的「一键写入」→ `.workbuddy/tools/apply_levelmap_export.py`，脚本里硬编码 `Datas/LevelMap.xlsx` 与 `Datas/SceneInfo.xlsx`，拆表后必须按 `level_id` 改路径（C# 侧只读 `ConfigJson/tblevelmap.json`，不用改）。
- 历史脚本（`add_levels_9_15/16_20_*.py`、`apply_m2_*.py`、`gen_wave_data.py`、`gen_m3_waves_rounds.py`、`gen_challenge_data.py`）直写聚合表，拆表后失效 → 标 LEGACY，不修。
- 拆表验收口径：**纯物理拆分必须做到 `Assets/ConfigJson/tb*.json` 语义等价**（按 id 排序逐字段比对）。先拆表、再改数值，两阶段分开 apply，否则出问题无法二分定位。
