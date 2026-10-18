UI 多分辨率适配修复与验收记录（2026-10-18）

目标工程：`D:\FreedomTower_1`，Unity `2022.3.62f3c1`。本次使用项目已有的 Unity MCP，连接 `http://127.0.0.1:8082/mcp`，核对实例 `FreedomTower_1@520e2c6d9c8bc788` 和 `projectRoot=D:/FreedomTower_1`。检查了 `Assets/Prefabs/UI` 全部 15 个预制体，其中两个条目随所属列表验证。

**结果与问题原因**

适配异常涉及固定面板超出可用高度、页面中部内容挤占顶底信息区、安全区使全屏遮罩缩小、图鉴视口依赖父宽度，以及文本框、换行和字体行高余量不足。保留主场景 CanvasScaler 的 1920×1080 / Match=0.5 设置，改用父 RectTransform 的实际可用尺寸进行局部布局。

现有正式预制体通过 LoadPrefabContents / SaveAsPrefabAsset 定点更新；与任务开始时的本地快照比较，15 份 `.meta` 完全一致，节点路径保持原有契约。已有未提交修改在原基础上保留；本次未提交 Git、未构建 APK。

| 界面或节点 | 最终调整与原因 |
| --- | --- |
| 各界面 `Bg` | 保持拉伸，增加 `UIFullScreenBackground`，按 root Canvas 世界角点计算偏移。交互内容继承安全区，遮罩覆盖整个屏幕，避免边缘漏出可点击区域。 |
| ConfirmView、GameIntroView、LevelClearView、LevelDetailView、PauseView、SellConfirmView、SettingView、TowerInfoView 的固定 `Panel` | 增加 `UIFitInParent`。保留设计尺寸，仅在实际父尺寸不足时等比缩小，四边预留 24 Canvas 单位，最大缩放为 1。内部直接按钮改为底边锚定，同时补偿 anchoredPosition，保持原基准矩形。 |
| `LevelClearView/Panel`、`LevelDetailView/Panel` | 仍为 1040×980、900×900；在超宽屏、带安全区导致有效高度降低时按局部面板约束缩放。 |
| `MainMenuView/Panel` 的 Logo、GameTitle、Subtitle、StartBtn、CodexBtn、SettingBtn | 使用 `UIResponsivePage.MainMenu`。内容列基准范围为 [-348,460]；预留顶部 80、底部 192，统一计算内容列内部的位置与缩放。退出按钮、版本行继续相对底部布局，1920×1080 内容列缩放为 1。 |
| `SelectView/Panel/List/Viewport` | 保留固定本地 1150×500、pivot=(0,0.5)，卡片仍为 1150×550。根据可用尺寸缩放视口变换，保留插件初始化缓存的本地几何；同时调整左右箭头高度，标题/统计行宽度不超过父宽度减 64。List 仍承担可视裁切。 |
| `TowerCodexView/Panel/CodexTitle` | 中心锚点、y=472 → 顶部锚点、y=-68，明确 pivot=(0.5,0.5)。保持基准位置并跟随顶部，避免超宽屏时越界。 |
| `TowerCodexView/Panel/List/Viewport` | 从跟随 List 宽度的拉伸内缩改为中心固定 460×640，x=-230、pivot=(0,0.5)。`List` 本地 1300×640，缩放 List 祖先变换以保留 460 的插件视口宽度。 |
| `TowerCodexView/Panel/PageText` | 改为底部锚点、y=184、pivot=(0.5,0.5)，与缩放后的卡片区及返回按钮留出空间。 |
| `TowerCodexView.UpdateItemVisuals` | 以视口本地坐标计算卡片中心距离。修复使用世界位置和条目左缘造成的居中卡片被错误缩小、淡化，以及分辨率缩放后视觉衰减变化。 |
| `TowerCodexItem/Body` 的文本 | 塔名 28～40、定位 20～26、四项数值 20～26，按文本框自动字号。描述开启换行及 16～24 自动字号，框为 380×70、y=-275；修复英文描述串到相邻卡片，并与价格行留出间距。 |
| `SellConfirmView/Panel/TowerName`、`WarnText` | 塔名框 740×52、字号 28～36；警告框 700×88、开启换行、字号 24～30，适应真实字体行高和两行英文。 |
| `GameIntroView/Panel/Info1..4` | 开启 24～30 自动字号并保留换行，修复简繁中文长说明的高度溢出。 |
| `TowerInfoView/Panel/Title` | 开启 28～40 自动字号，适应塔名与等级组合的字体行高。 |
| `TipsView/TipBar` | 采用任务开始时正式资源的顶部锚点与 (0,-263)，将生成器同步到该状态；生成器 CanvasGroup 初始 alpha 与现有资源统一为 1，运行时仍由 TipsView 管理淡入淡出。 |
| `HudView` | 保留已有 RefreshBottomLayout / OnRectTransformDimensionsChange 的布局修正。检查了速度按钮、三颗塔按钮、右侧开始按钮以及恢复原分辨率，无新增布局改动。 |
| `SelectLevelItem` | 保留 1150×550、左侧 pivot 和非激活存储状态；未将条目或 Content 改成全拉伸。 |

关键静态参数和组件变化记录在 [layout-changes.json](D:/FreedomTower_1/Docs/UIResolution/20261018/layout-changes.json)，其中 before 来自本次任务开始时的工作区资源，并非 Git HEAD。运行时计算产生的位置与缩放以组件实现和截图为准。

**生成器同步与回归方式**

`Assets/Editor/UIResolutionLayout.cs` 是现有资源同步与新资源保存的共同布局规则。`UIPrefabBuilder` 各保存入口都会应用这些规则，避免下次生成恢复旧布局。已有资源通过菜单 `Tools/塔防/高级（单步重建）/同步 UI 分辨率布局（保留现有资源）` 更新。

新增 `UIPrefabBuilder.BuildLayoutPreview("Assets/__UIResolutionPreview...")`，将生成保存与删除目标限制到 Assets 下的专用单层临时目录。执行了隔离生成，比较正式资源与生成结果后移除临时资产。未对正式资源调用全量删除重建。

- 15/15 正式预制体的节点路径、active、anchorMin、anchorMax、pivot、anchoredPosition、sizeDelta 与生成结果一致，详见 [generator-comparison.json](D:/FreedomTower_1/Docs/UIResolution/20261018/generator-comparison.json)。
- 14 个调整过的文本节点，其自动字号范围、换行和溢出模式与生成结果一致，详见 [text-layout-comparison.json](D:/FreedomTower_1/Docs/UIResolution/20261018/text-layout-comparison.json)。
- 同步连续执行两次，第二次没有文件内容变化；没有重复组件、重复节点或再次位移。
- 隔离生成 18 份预制体（15 个 UI + 3 个 BootUI），正式 UI 文件内容未被隔离生成改变。
- `Assets/Resources/BootUI`、`Main.unity` 与 `SceneMainBuilder.cs` 未产生差异。共同布局规则明确跳过三个启动界面。
- 快照脚本补充 GameIntroView 与 pivot，缓存覆盖 15 个预制体 / 231 个节点；重新生成并执行 `--check` 通过。

**运行验证**

通过 Unity MCP 在 Play Mode 使用实际预制体、View 脚本、配置与字体；数据展示使用隔离存档和代表性测试数据。矩阵使用临时 World Space Canvas 和相机，其逻辑尺寸严格按主场景 CanvasScaler 的 Match=0.5 公式计算。每个界面在同一实例上连续切换尺寸并恢复初始尺寸；每种语言重新启用界面，覆盖英文、简体中文、繁体中文。

| 物理分辨率 | 安全区 | 检查结果 |
| --- | --- | --- |
| 1280×720 | 全屏 | 13 个界面 × 3 种语言通过 |
| 1920×1080 | 全屏；序列末恢复此尺寸 | 13 个界面 × 3 种语言通过，含尺寸恢复 |
| 1920×1200 | 全屏 | 13 个界面 × 3 种语言通过 |
| 1440×1080 | 全屏与内缩 | 13 个界面 × 3 种语言通过 |
| 2340×1080 | 全屏 | 13 个界面 × 3 种语言通过 |
| 2400×1080 | 全屏 | 13 个界面 × 3 种语言通过 |
| 2560×1080 | 全屏与内缩 | 13 个界面 × 3 种语言通过 |

内缩模拟值：左 120、右 80、上 48、下 24 物理像素，先转换为标准化锚点再应用到安全区父节点。总计 390 个界面 / 语言 / 尺寸步骤；没有检测到活跃关键文字和控件越界、TMP 文本溢出、兄弟按钮重叠、可交互按钮中心被 GraphicRaycaster 阻挡或缺字。11 个带 Bg 的界面完成 330 次全 Canvas 背景覆盖检查。

选关和图鉴在每个尺寸步骤遍历所有条目并检查吸附后的中心误差，分别为 600、90 个位置样本；选关最大误差约 0.000123 Canvas 单位，图鉴最大误差小于 0.0001。视口本地宽度始终为 1150、460。两个列表的左右箭头业务回调和 PointerEventData 拖动均为 30/30 通过；选关卡片中心射线命中为 30/30。图鉴卡片按现有设计没有点击业务。

另外通过真实 `UIManager.Open` 在主场景 Canvas（当前 Game View 为 4000×2000）验证：首次打开选关可生成列表；EventSystem 射线命中居中卡片，派发 PointerClick 后打开 levelId=1 的详情页；先居中第二张再点击相邻的第一张，详情页在吸附完成后打开，保持既有交互约定。

随后在 2860×1272 的真实 Game View 重复验证居中卡片点击，仍正确打开 levelId=1。等待详情弹窗淡入完成（CanvasGroup alpha=1）后保存[真实 Canvas 选关详情截图](D:/FreedomTower_1/Docs/UIResolution/20261018/actual-canvas-select-detail.png)。

每批 C# 改动后请求 force/all/compile 刷新，重新核对实例，读取编辑器状态与 Console，最终 `scriptCompilationFailed=false`。最终运行复查只有任务开始前已存在的 `CommandInvokationFailure: Unity Remote requirements check failed`，未清空 Console。验证过程中曾因 HUD 展示夹具调用了主菜单状态下的 levelId=0 查询产生配置错误，已改成不访问关卡的展示夹具；最后一轮复测未再次产生该错误。

完整机器可读结果见 [validation-summary.json](D:/FreedomTower_1/Docs/UIResolution/20261018/validation-summary.json) 和本目录各 `*View.json`。编辑器验证工具为 `Assets/Editor/UIResolutionVerifier.cs`；它要求 Play Mode、配置加载完成和隔离存档，避免将 UI 展示夹具写入正常存档。验证结束后退出 Play Mode，恢复 Boot 场景、原 playModeStartScene 和测试存档上下文。

**截图与实际验证边界**

本目录保留 65 张矩阵截图：每个界面的英文基准、4:3、超宽屏、超宽屏带安全区，以及简体中文带安全区。下图为所有界面的英文超宽屏安全区缩略图；原图可在本目录放大查看。

![13 个界面的 2560×1080 安全区检查](D:/FreedomTower_1/Docs/UIResolution/20261018/wide-safe-contact-sheet.jpg)

这是 Unity 编辑器内的运行、渲染与事件验证，尚未进行 Android/iOS 真机安装。安全区是模拟内缩，拖动由 PointerEventData 驱动；触摸硬件、系统手势及拖动惯性的实际手感仍需真机确认。文本检查覆盖代表性展示数据，未穷举所有业务状态、自定义提示文案或未来新增本地化内容。
