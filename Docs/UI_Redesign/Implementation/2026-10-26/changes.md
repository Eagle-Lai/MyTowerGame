# UI 改动与维护说明

日期：2026-10-26。工程：`D:/FishTestGame`。视觉基准保留在 `D:/FishTestGame/Docs/UI_Redesign/2026-10-26/`，没有改写原设计图使其迁就实现。

## 文件与目的

以下路径以 `D:/FishTestGame/` 为根；完整动态状态及数据对应关系见同目录 `ui-state-implementation.csv`。

| 文件或资产 | 实际变化 |
|---|---|
| `Assets/Editor/TacticalForgePrefabBuilder.cs` | 新增可重复的定点 UI 更新入口；原位保存现有预制体并保留 GUID，生成网格条目、怪物卡片、切角皮肤、盾塔标记和两段式背景。同步静态与动态文本绑定。 |
| `Assets/Editor/TacticalForgeAssets.cs` | 生成三语共用的许可字体；只读复制原怪物 SpriteRenderer 层级进行独立相机合成，输出 119 张 UI 肖像。版本标记避免反复导出；透明空图可修复。方向图可能是身体零件，不能把第一个切片当完整形象。 |
| `Assets/Editor/TacticalForgePreview.cs` | 独立 PreviewScene 布局渲染和定点引用检查；读取正式导出表，不写配置、不调用删档，不改变正式语言/存档单例。 |
| `Assets/Editor/UIPrefabBuilder.cs` | 正常页面入口优先更新现有 Tactical Forge 资产；旧删除操作改为保留 GUID 的覆盖保存。 |
| `Assets/Editor/UIResolutionLayout.cs` | 新页面走 TacticalForgePrefabBuilder，不再被旧布局覆盖。 |
| `Assets/Editor/UISkinArtGenerator.cs` | 保留旧资源用途，并同步新皮肤生成；新皮肤使用独立目录。 |
| `Assets/Editor/LocalizationPrefabBinder.cs` | 排除继续、保存、射程、比较等动态按钮的静态 TextLocalizer，防止切语言覆盖状态文案。 |
| `Assets/Scripts/Core/UI/TacticalForgeLayout.cs` | 按实际内容矩形计算网格、详情弹窗、结算与图鉴布局；HUD 使用对称的上/下操作区，缓存页面与节点并在尺寸/安全区/继续状态变化时重排。 |
| `Assets/Scripts/UI/TowerActionMenu.cs` | HUD 内非模态环形塔操作组；跟随选中塔、边缘限位、升级/出售原事件和 More 详情入口；升级换实例、售出/取消选择与弹窗遮挡时同步隐藏。 |
| `Assets/Scripts/Camera/CameraController.cs` | SetDisplayArea 对称避让紧凑 HUD，地图回到可用区域中央且选塔时不为详情留侧栏；相机 pixel rect 与 ScreenToWorldPoint 坐标体系保持不变。 |
| `Assets/Scripts/Tower/TowerPlacement.cs`、`Assets/Scripts/Game/Board.cs` | 当前选中塔临时提高 SortingGroup 序；取消选择、换塔、出售与对象销毁时恢复常态层级。 |
| `Assets/Scripts/UI/LevelMapPreviewGraphic.cs` | 读取正式地图，复用 BoardGeometry.IsWalkable 绘制预览路线；缺少终点不进行错误 BFS，不替代实战路线。 |
| `Assets/Scripts/UI/MainMenuView.cs` | 有效继续查询、怪物图鉴入口、新主按钮色；继续关卡来自兼容检查点。 |
| `Assets/Scripts/UI/SelectView.cs` | 正式全量关卡网格、真实状态、选择预览、明确简报入口；新结构绕过旧横向轮播自动吸附/进入逻辑。 |
| `Assets/Scripts/UI/LevelDetailView.cs` | 正式地图、波次引用的敌人肖像条、继续入口、重开确认、介绍来源与锁定解释；保留原评级数据接口。 |
| `Assets/Scripts/UI/HudView.cs` | 新布局生效时跳过旧底栏几何重排；原点按/拖动和建造事件继续使用。 |
| `Assets/Scripts/UI/TowerInfoView.cs` | 真实类型图标、升级差异、范围显隐、出售与关闭；不修改费用、射程或升级规则。 |
| `Assets/Scripts/UI/TowerCodexView.cs`、`TowerCodexItem.cs` | 三塔型标签页、单塔展示与正式全等级比较；复用卡片、语言字体和读表失败重试。 |
| `Assets/Scripts/UI/MonsterCodexView.cs` | 新增可达图鉴；按 ResName 分组，119 个大卡片及返回列表的详情；属性使用真实配置范围；读表重试与过期回调保护。 |
| `Assets/Scripts/UI/LevelClearView.cs` | 持续显示未保存原因、保存重试、防重复；未保存返回只能留下或重试；新纪录、下一关仍受成功保存与评级有效性约束。 |
| `Assets/Scripts/UI/LoadingView.cs`、`Assets/Scripts/Launcher.cs` | 配置失败后真实重试/退出；复用时清理进度、回调与失败状态，不制造已完成进度。 |
| `Assets/Scripts/UI/SettingView.cs`、`SellConfirmView.cs`、`PauseView.cs`、`GameIntroView.cs`、`TipsView.cs` | 重置/出售等待与失败恢复、风险确认、介绍来源、暂停返回和无缩放时间提示；关闭时清理协程与监听。 |
| `Assets/Scripts/Game/GameFlowManager.cs` | 选塔不再自动打开 TowerInfoView；环形动作交由 HUD 组件呈现；其他暂停、保存重试和战斗流程沿用。 |
| `Assets/Scripts/UI/TowerInfoView.cs` | 改作明确的居中详情弹窗；关闭回到环形动作而不取消所选塔。 |
| `Assets/Scripts/Core/Manager/SaveManager.cs` | TryResetAll 返回实际成功/失败；存储重置成功后才更新内存，失败不伪报成功。保留 ResetAll 兼容入口。 |
| `Assets/Prefabs/UI/` | 已更新正式使用的主菜单、选关、详情、HUD、塔详情、图鉴、确认、出售、设置、暂停、提示、介绍、结算；新增 TacticalLevelItem、TacticalMonsterItem、TacticalBriefingEnemyItem 与 MonsterCodexView。 |
| `Assets/_UIAssets/UI/TacticalForge/Buttons/action-circle.png`、`Icons/action-*.png` | 新增圆形操作按钮及升级、出售、更多符号；仅用于 HUD 内嵌快捷组。 |
| `Assets/HotUpdateUI/`、`Assets/Resources/BootUI/HotUpdateView.prefab` | 已保存正式 Splash/Loading/AOT 壳新样式，不移动原有加载位置。 |
| `Assets/Localization/LocalizationSettings.asset` | 三语字体统一指向许可 Noto / TacticalSans。没有直接改写生成的本地化 JSON。 |
| `Tools/ui_mcp.py`、`Tools/export_ui_delivery.py` | 本任务专属 8084 身份核对客户端；只读工程、生成交付 CSV 和统计的工具。 |

## 资源与加载

主视觉从设计包复用；本轮没有调用 Image API。按钮、面板和标记为独立程序绘制图像，没有烘焙语言文字或数值。

图像、字体放在 `Assets/_UIAssets/UI/TacticalForge/`；图像由实际生产 prefab 序列化引用。已有 `Assets/_UIAssets` 收集器覆盖这些资源，未把整个工程或 Docs 加入收集器。怪物卡片由 MonsterCodexView 序列化引用，不单独新增资源逻辑名。

MonsterCodexView 的逻辑名在现有 ResTable 中已经登记，本轮接通实际脚本、预制体与入口；没有重写 MonsterCatalog 或敌人登记。塔图标和 Range_Ring、Path_Arrow 按现有逻辑名复用。

HotUpdateView 继续保留在 Resources/BootUI，仅依赖 AOT 壳脚本与 Unity/TMP 类型；没有挂热更布局或 TextLocalizer。其直接引用使原生字体、材质和动态字体源随 APK 嵌入。Splash/Loading 保持 HotUpdateUI 中的正式 AB 加载链。未构建 APK 或发布 AB，包内结果仍待用户验证。

主视觉与肖像 Android 覆盖为 ETC2_RGBA8；肖像最大 512，主视觉最大 2048；小型几何皮肤为 RGBA32，无 mipmap。默认 UI/TMP 共享材质继续使用。许可源字体与动态字库会增加包体和首次补字成本，真机内存/字库增长尚未测量。

## 实现差异与原因

| 项目 | 当前落地与边界 |
|---|---|
| 关卡/波数 | 按当前正式导出记录呈现有效关卡与波数，视觉稿不覆盖业务数据。 |
| 怪物资料 | 配置记录按现有 ResName 分组对应图像；详情显示全部配置变体的属性范围。没有虚构统一怪物 HP，也没有批量生成战斗对象作为图鉴。 |
| 图鉴插图 | 复用当前有效原始视觉的完整 SpriteRenderer 组合，展示静态姿态；没有制作新敌人或修改动画。 |
| 战前敌人展示 | 按正式波次引用及 ResName 去重显示肖像/名称；种类较多时横向滚动，缺图仍显示真实名称。 |
| 塔型展示 | 使用现有塔型图标与正式等级数据；图鉴没有替换炮塔生产预制体。 |
| 条目新纪录 | 保存记录可证明历史最佳，不能证明“刚刚产生”；条目显示最佳，瞬时徽标只在已保存结算出现。 |
| HUD 地图取景 | 地图在顶部/底部紧凑 HUD 之间保持居中并尽量铺满；选中塔不再触发相机或右侧详情栏预留。实际安全区/触摸仍由设备验收。 |
| 选中塔操作 | 单塔临时抬层，升级/出售/更多环绕排列；详情仅由更多按钮打开，关闭回到环形组。 |
| 三语 | 首批 16 个新增 key 按用户授权补入源表并完成标准导出，记录由 347 增至 363；后续瑕疵修复再追加 9 个，当前共 372 条，缺项扫描为 0。原文案、占位符和字体字形已核对，实际运行切换仍待用户验收。 |
| 暂停/恢复 | 热更新界面只展示实际会话已有的回调，未支持的能力不伪装可用。 |
| 视觉证据 | 编辑器预览只能证明对应布局可渲染，不能证明输入、保存与完整运行成功。 |

## 保护范围

最终交付统计将本轮授权的 `Luban/Config/Datas/Localization.xlsx` 与标准导出的 `Assets/ConfigJson/tblocalization.json` 单独列为 authorizedLocalizationTrackedDiffs。除此之外，敌人预制体、怪物原始美术、MonsterCatalog、其他 Luban 源表、其他配置数据和生成 C# 均无内容变更；Assets/Gen 的 C# 仅由标准导出统一为 LF，程序集定义原样保持。

没有改变塔伤害/经济/升级/返还、敌人属性、波次、寻路、评级、解锁或存档字段语义。未恢复声音系统；存档失败呈现和重置返回值属于 UI 所需的错误传播。没有重置真实用户存档。

原有 DOTweenSettings.asset、StreamingAssets/build_info.meta 和原设计资料改动保留，不纳入本任务提交；本轮没有创建提交。

收尾补齐 `LocalizationPrefabBinder` 识别 HUD 环形动作动态标签前的父节点判空，避免根节点 Label 触发空引用；同步 README 本地化词条统计，并清理既有 UI 同步文档末尾空行。该 C# 补丁已重新通过本工程 8084 MCP 编译与定点引用检查。

用户追加明确“手工”不要求通过表格界面操作，允许代码补充源表。首批本地化补齐追加 16 项，保留既有 355 行；生成 JSON 全由现有 Luban 链产生。随后瑕疵修复阶段再追加 9 项至 B372:F380，累计 372 条。交付统计工具支持零缺项，已完成词条、源表行号、导出对照及 MCP 证据均已落盘；新增文案字形已预热到 TacticalSans，简中/繁中 HUD 环形预览同步显示“更多”。


## 瑕疵报告后续修复（2026-10-26）

- `TowerActionMenu` 保持选中塔锚点不动；在边缘与角落向内重排圆弧上的三个按钮，按钮仍有间距，不跨过塔遮挡主体。
- `TacticalForgeLayout` 按可用高度压缩结算信息行，并为底部操作栏预留空间。`ArrangeTowerCard` 加紧凑模式，为塔说明与属性行留出间距。
- 新增 `TowerPresentation`：三类塔的说明与升级摘要在运行 UI / 隔离预览间共用，包含减速、伤害/DPS、射程与刷新/攻击间隔。
- 新增 `CircularRaycastFilter`，按钮只响应圆形区域内点击；无需启用纹理读写。
- `Localization.xlsx` 追加 9 个三语塔说明/升级模板到 B372:F380，经 `LubanExporter.ExportInternal` 导出，正式词条数为 372；关卡/敌人及其他数值源表未改，Assets/Gen 规范化检查无语义差异。
- 受影响 UI prefab 原位更新 HudView、LevelClearView、TowerInfoView、TowerCodexItem、TowerCodexView，GUID 保持不变。9 个新增显示 key 已预热到 TacticalSans。
- 修复文档及5项状态：[瑕疵审查](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/ui-quality-review.md)、[问题清单](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/ui-quality-findings.csv)、[词条清单](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/localization-quality-fixes.csv)。

