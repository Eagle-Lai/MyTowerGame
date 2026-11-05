# Unity 多语言本地化运行时审计

审计日期：2026-11-05（Asia/Shanghai）  
工程：`E:/MyTowerGame`  
Unity：`2022.3.62f3c1`；活动构建目标：Android  
验证通道：Codex `unityMCP`，本次现场 URL `http://127.0.0.1:8086/mcp`，实例 `MyTowerGame@9e28c50b510eeb91`

## 结论

配置表的 377 个词条在 English、简体中文、繁体中文中都有非空文本，运行时取词、占位符和字体字形检查全部通过。界面字体引用、atlas、三种语言的设置页显示与受检 TMP 溢出检查也通过。

发现 6 个被生产 C# 调用、但配置表中没有同名 key 的本地化项，共涉及 7 个调用点；每种语言的运行时查询都返回 `null`。这些调用点虽然设了 fallback，却将简体中文硬编码为 fallback，所以英语及繁体中文的相应页面可能混入简体中文。这是本次发现的确定性缺陷。

本轮只审计，没有改游戏源码、配置表、Prefab 或存档。Play Mode 已退出，编辑器回到未修改的 `Assets/Scenes/Boot.unity`。

## 检查记录

| 检查项 | Unity MCP 验证方式 | 实际结果 | 证据 |
|---|---|---|---|
| 工程与编辑器身份 | 读取 `custom-tools`、`instances`，选中完整实例 ID；读取 `project/info`、`editor/state`，并用 `execute_code` 取 `Application.unityVersion`、项目绝对路径、目标平台与 Play Mode | 路径 `E:/MyTowerGame`、Unity `2022.3.62f3c1`、Android 目标匹配；实例正确 | 本报告开头的实例信息；最终状态为 Boot、未播放、场景未修改 |
| 词条唯一性与空值 | `execute_code` 加载 Unity 中的 `Assets/ConfigJson/tblocalization.json`，以生成的 `cfg.TBLocalization` 解析并逐项计数 | 377 行、377 个唯一 ID、重复 0；英文/简中/繁中空值均为 0；任一译文与英文完全相同的条目数为 0 | [localization-entry-checks.csv](evidence/localization-entry-checks.csv) |
| 词条运行时解析 | 每种语言调用 `LanguageManager.SetLanguage`；对每个 ID 调用 `LanguageManager.GetText`；对格式串以 20 个运行时参数调用格式化取词，并比对源文案占位符索引 | 1,131 次（377 × 3）；查词与源文本完全匹配 1,131；空值 0；占位符索引不匹配 0；格式化失败 0 | [localization-entry-checks.csv](evidence/localization-entry-checks.csv) |
| 代码调用点覆盖 | Unity Editor `execute_code` 枚举当前 `Assets/**/*.cs`、排除注释后提取字面量 `Localization.Get("...")` 调用，并在运行时逐语言取词 | 173 个调用点、131 个唯一 key、519 次检查；6 个唯一 key 缺失，`Not cleared` 出现于两个调用点，故有 7 个调用点 × 3 语言 = 21 次 miss | [runtime-localization-callsite-checks.csv](evidence/runtime-localization-callsite-checks.csv) |
| 本地化 Prefab | Unity Editor `AssetDatabase.FindAssets("t:Prefab", new[] {"Assets"})` 实例化 16 个带 `TextLocalizer` 的 Prefab 到隔离根；启用实际可用组件，逐语言触发运行时语言变更并读取 TMP 文本、字体、矩形、溢出与字形 | 269 个 `Assets` Prefab 中 16 个带本地化组件；47 个 `TextLocalizer`（46 启用、1 禁用）。141 条记录中 138 条适用检查全部匹配；文本错误 0、错误字体 0、溢出 0、缺字 0 | [ui-prefab-localizer-checks.csv](evidence/ui-prefab-localizer-checks.csv) |
| 活跃 UI 与切换 | 在 Main 场景实际打开设置页，用游戏设置的语言 Dropdown 分别切换三种语言；经 `execute_code` 读取活跃 TMP 文本、已应用字体及 `isTextOverflowing`；截图由 Unity MCP `manage_camera` 获取 | 每种语言抽样 Main Menu 11 条 + Settings 13 条，共 24 条；三种语言合计 72 条。语言切换正确，字体匹配 72/72，溢出 0。每种语言各 1 个空 `Title` 文本是未填值的布局占位，不是显示空文案的可见标签。重新验证主菜单时，进入 Play Mode 后立即截图曾只有过渡背景；等待画面稳定后重摄，最终图中标题和各菜单按钮完整显示 | [active-screen-checks.csv](evidence/active-screen-checks.csv)、本报告“画面证据” |
| Boot 阶段文案 | 在 Unity 运行时逐语言调用 `BootLocalization.Get(key, language)` 检查 20 个加载/品牌 key | 60 次检查，空文案 0 | [boot-localization-checks.csv](evidence/boot-localization-checks.csv) |
| TMP 字体和字形 | Unity MCP `execute_code` 读取 LocalizationSettings 的字体引用、atlas、character/glyph/fallback 数量；遍历 377 条译文并调用 TMP `HasCharacter(..., searchFallbacks:true)`；再通过 `AssetDatabase.FindAssets("t:Prefab", new[] {"Assets"})` 检查 Prefab TMP 引用 | LocalizationSettings 的 3 个语言引用均指向 `TacticalSans`；该资产 character table 838、glyph table 837，2048×2048 atlas 有效、fallback 0。译文缺字 0。269 个 `Assets` Prefab 的 173 个 TMP 中有 172 个使用 `TacticalSans`、1 个使用 `SiYuanSongTi SDF`；两个资产均有有效路径和 atlas，空字体引用 0、无效路径 0、缺 atlas 0 | `localization-entry-checks.csv` 的 `fontAsset`/`missingGlyphs` 列、[tmp-font-asset-checks.csv](evidence/tmp-font-asset-checks.csv)、`ui-prefab-localizer-checks.csv` |
| 编辑器 Console | Unity MCP `read_console(action="get", types=["error"])`，不清理 Console | 0 条 Error/Exception。运行期间看到资源 manifest 的重复 location 警告，但不是本地化或字体报错 | 最终 MCP 查询返回 `Retrieved 0 log entries` |
| 结束状态 | Unity MCP `editor/state` 与 `execute_code` | Play Mode=false；活动场景 `Assets/Scenes/Boot.unity`；scene dirty=false；`scriptCompilationFailed=false`；编辑器就绪 | `mcpforunity://editor/state` 最终读数 |

## 确定缺陷

下列 key 在运行时表中都不存在；`runtime-localization-callsite-checks.csv` 对 English、简中、繁中都记录 `rawRuntimeValue` 为空。fallback 使简中可以继续显示，但 English 与繁中会落到表中列出的简体中文文案。

| 缺失 key | 使用位置 | 当前 fallback | 风险 |
|---|---|---|---|
| `Combat {0} · Level {1}` | [LevelClearView.cs](/E:/MyTowerGame/Assets/Scripts/UI/LevelClearView.cs:176) | `战斗 {0} · 整局 {1}` | 结算页的时间标题在 English/繁中显示简中；表中另有旧式 `Combat {0} / Par {1} · Level {2}`，但 key 和参数口径不匹配 |
| `Boss leaks {0}` | [LevelClearView.cs](/E:/MyTowerGame/Assets/Scripts/UI/LevelClearView.cs:179) | `首领漏怪 {0}` | 有首领漏怪时，English/繁中显示简中；表中复合旧 key 是 `Boss leaks {0} · Critical leaks {1}` |
| `Best stars: {0}/5` | [LevelDetailView.cs](/E:/MyTowerGame/Assets/Scripts/UI/LevelDetailView.cs:166) | `历史最佳：{0}/5` | 战前简报的最佳星数在 English/繁中显示简中 |
| `Not cleared` | [LevelDetailView.cs](/E:/MyTowerGame/Assets/Scripts/UI/LevelDetailView.cs:167)、[SelectView.cs](/E:/MyTowerGame/Assets/Scripts/UI/SelectView.cs:339) | `未通关` | 未通关状态在 English/繁中显示简中；表中只有 `Not cleared yet`，不是当前代码 key |
| `Best clear: {0}` | [LevelDetailView.cs](/E:/MyTowerGame/Assets/Scripts/UI/LevelDetailView.cs:208) | `最佳整关用时：` + 时间 | 战前简报最佳整关用时在 English/繁中显示简中 |
| `Clearing a level awards five stars until the rating rules are rebuilt` | [LevelDetailView.cs](/E:/MyTowerGame/Assets/Scripts/UI/LevelDetailView.cs:217) | `评分规则重建前，通关即记 5 星` | 战前简报规则说明在 English/繁中显示简中 |

建议修复时对齐“调用 key ↔ 三语配置项”，并保持 `{0}` 占位符一致；这次仅记录发现，没有擅自改配置表。

## 字体专项结果

- `LocalizationSettings.asset` 中 English、ChineseSimplified、ChineseTraditional 三项都引用 `TacticalSans`，序列化字体引用、材质与 atlas 均非空。
- `TacticalSans Atlas` 为 2048×2048；TMP 运行时读数为 character table 838 项、glyph table 837 项，fallback 列表为空。
- 对全表三种译文的每个非空白字符调用 TMP 字符覆盖查询，缺字数为 0；设置页实测的中英文控件均应用 `TacticalSans` 且无 `isTextOverflowing`。
- `Assets` 中 269 个 Prefab 的 173 个 TMP 组件均有有效字体资产和 atlas。`SelectLevelItem.prefab` 留有一个禁用的旧 `TextLocalizer`；运行时实际卡片由 `SelectView` 数据绑定且显式调用 `LanguageManager.ApplyFont`，故该禁用脚本不计为活跃渲染缺陷。

## 画面证据

以下均由 Unity MCP `manage_camera` 从 Game View 截图生成，实际分辨率均为 1920×1080。主菜单图在 Play Mode 从 Boot 自动进入 Main、画面稳定后重新捕获：

- 简体中文主菜单：[main-menu-zh-hans.png](evidence/main-menu-zh-hans.png)
- English 设置页：[settings-en.png](evidence/settings-en.png)
- 简体中文设置页：[settings-zh-hans-stable.png](evidence/settings-zh-hans-stable.png)
- 繁体中文设置页：[settings-zh-hant.png](evidence/settings-zh-hant.png)

其余 CSV 按记录保留每项的 key、语言、期望与实际文本、字体、占位符、字符覆盖和溢出值，可用于定位到具体词条或 Prefab 子节点。

## 覆盖边界

资产表、调用点和被扫描的 Prefab 都通过 Unity MCP 在当前运行工程中读取；Prefab 范围限定为 `Assets`，排除 `Packages/com.unity.2d.spriteshape` 下 2 个编辑器默认 Prefab。字符串取词、TMP 字形覆盖、TMP 溢出和语言切换均实际调用了 Unity/TMP 运行时 API。调用点提取范围是 `Assets/**/*.cs` 中字面量 `Localization.Get("...")`；动态构造 key、服务器远程文案、文本烘焙在图片内，以及未实际打开的每一种游戏结果/错误弹窗不属于 519 条字面量调用点结果。主菜单和设置页已做逐语言实际画面检查，其余动态结算页的缺失 key 已由运行时表查询和 Unity 调用点扫描证实，但本轮没有通过完成一局游戏来触发每一种结算分支。
