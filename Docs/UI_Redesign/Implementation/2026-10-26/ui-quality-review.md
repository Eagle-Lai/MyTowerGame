# FishTestGame UI 界面瑕疵审查报告

日期：2026-10-26（Asia/Shanghai）  
状态：瑕疵已修复；隔离编辑器验证通过，Play/Android 设备验收待完成  
对象：本次 Tactical Forge UI 实现，重点为 HudView、选塔环形动作与 TowerInfoView

## 1. 结论

原审查记录了 **4 项确认问题、1 项交互风险**（P1 × 1、P2 × 3、P3 × 1）。本轮已逐项修复，五项都通过编辑器隔离预览或点击几何验证；真实 Play Mode 和 Android 设备验收仍待完成。原问题描述与截图保留为修复依据，当前状态见随附清单。

本轮修改限于 UI 呈现脚本/预制体以及授权的 Localization.xlsx 源表与 Luban 导出。没有修改关卡、敌人、评分、经济或存档语义。

| ID | 等级 | 页面 | 问题 | 证据强度 |
|---|---|---|---|---|
| UI-01 | P1 | HudView / 环形动作 | 边缘选塔时菜单偏离塔中心，升级按钮遮住塔 | 生产定位函数 + 隔离布局复现 |
| UI-02 | P2 | LevelClearView | 2560×1080 下理由文字与底部按钮重叠 | 生产布局几何 + 合成文案复现 |
| UI-03 | P2 | TowerCodexView | 中文界面显示英文工程说明和过细小数 | 正式导出数据 + 当前截图 + 运行填充代码 |
| UI-04 | P2 | TowerInfoView | 减速塔升级对比遗漏减速提升，仍显示 ATK 0 → 0 | 正式塔数据 + 生产表达式在 Unity 中只读求值 |
| UI-05 | P3 | HudView / 圆形按钮 | 可见圆外的透明方角仍处于点击矩形内 | 生产资产与 Image 配置确认；实际误触待 Play 复验 |

等级含义：P1 优先修复，影响核心操作对象辨认；P2 明显影响可读性或决策信息；P3 交互细节风险。没有将本轮问题解释为崩溃、数据损坏或存档失败。

## 2. 审查方式和边界

- 工程根路径经 MCP 确认是 D:/FishTestGame，Unity 2022.3.62f3c1，项目平台 Android。
- 连接使用本工程实际地址 http://127.0.0.1:8084/mcp；现场发现并选定 FishTestGame 实例后再核对项目根路径与版本，没有借用其他工程的 8080/8082。
- 当前 Boot 场景处于 Edit Mode。使用正式预制体、正式导出配置及隔离 PreviewScene 进行渲染；临时对象和 RenderTexture 在 finally 中释放。
- 新生成并检查 12 个页面/语言/尺寸组合，覆盖 10 个页面；另做 5 个定点布局探针。当前矩阵涉及简中、英文、1024×768 和 2560×1080；定点边缘 HUD 探针为 1920×1080。
- 修复后另生成 18 张隔离预览：HUD 边缘塔位 4 张、结算页 5 种分辨率、塔详情 6 种塔型/等级/金币状态、图鉴说明 3 种语言。另对 5 种屏幕尺寸的 455 个 13×7 塔位做安全范围及互相间距测试，0 项失败。
- 圆形点击过滤通过 Unity 的 Image.Raycast 探针：3/3 圆心命中、3/3 边缘容差点命中、0/3 透明方角命中。
- 9 个三语词条已追加至 Localization.xlsx 第 372–380 行并经正式 Luban 导出；总词条为 372，交付扫描 missingLocalizationKeys=0。
- 5 个相关 UI prefab 已原位更新，22 个 prefab 序列化引用/Missing Script 检查为 0 项；新增 9 个显示词条字形已补入 TacticalSans，missing characters 为空。
- 修复批次结束后，本工程 8084 MCP `scriptCompilationFailed=false`、无编译/域重载/资源更新、`ready_for_tools=true`，error 控制台查询 0 条。一次预览探针拼错地图列数字段导致的 CS1061 已更正并重新刷新编译；最终状态以上述修复后结果为准。
- 界面业务脚本在隔离预览中被禁用。HUD 塔图标、选塔位置、结算结果及保存失败提示为合成状态；**不是完整游戏运行截图，也不是一次真实保存失败的现场**。
- 本轮没有进入 Play Mode、构建/部署 APK、修改真实存档、执行完整战斗或进行 Android 安全区/触摸测试。
- 编辑器编译只验证 C# 与导入状态，不代替 APK 构建、真机字体/安全区或真实塔交互验收。

证据索引：

- [12 项当前预览矩阵 MCP 记录](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/current-preview-matrix-mcp.jsonl)
- [当前预览总览 1](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/current-review-contact-sheet-1.jpg)
- [当前预览总览 2](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/current-review-contact-sheet-2.jpg)
- [定点几何探针及输出](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/isolated-layout-probe-mcp.jsonl)
- [正式数据与源文件摘要/哈希](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/source-audit.json)
- [减速塔升级表达式与末次编辑器状态](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/final-review-state-mcp.jsonl)
- [修复后 18 张预览矩阵](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/fix-evidence/final-quality-preview-matrix-mcp.jsonl)
- [455 个塔位几何探针与点击区域测试](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/fix-evidence/final-interaction-verification-mcp.jsonl)
- [最终编译、Luban 导出及预制体检查记录](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/fix-evidence/final-compile-retry-mcp.jsonl)

## 3. 逐项问题

### UI-01 · P1 · 地图上缘选塔时，升级按钮遮住所选塔

**修复已实施**：菜单锚点始终保持在真实塔的 HUD 投影点；靠近边缘/角落时依次尝试向内展开的圆弧，保留按钮尺寸、间隙和地图区域。5 种目标尺寸合计 455 个塔位均找到无越界、无按钮相交的布局。[当前上缘塔位预览](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/evidence/HudView-zh-Hans-1920x1080-quality-edge-top-left-isolated-editor-preview.png)显示三个按钮已移到塔的下方，不遮挡棋盘内的所选塔。

**触发条件**：选中靠近棋盘上缘的塔。1920×1080 的定点样例把合成塔置于 HUD 局部坐标 (0,350)，该位置处于预览棋盘上排。

**现象与证据**：生产 ClampAnchor 将菜单中心从 (0,350) 移至 (0,228)，位移 122 个 UI 逻辑单位；升级按钮相对菜单中心又向上 146。升级按钮中心最终只比塔中心高 24，而按钮直径为 124，所以塔图标被升级按钮大面积遮住。侧边样例 (-800,0) 也会把菜单中心改为 (-756,0)，只是程度较轻。

- [上缘选塔隔离复现截图](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/HudView-zh-Hans-1920x1080-edge-top-probe.png)
- [左缘选塔隔离复现截图](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/HudView-zh-Hans-1920x1080-edge-left-probe.png)
- 定位：[TowerActionMenu.cs:98](D:/FishTestGame/Assets/Scripts/UI/TowerActionMenu.cs:98)，夹取逻辑位于 109–114 行。
- 按钮偏移/尺寸：[TacticalForgePrefabBuilder.cs:244](D:/FishTestGame/Assets/Editor/TacticalForgePrefabBuilder.cs:244)，尺寸位于 256 行。

**影响**：按钮与操作对象的空间关系变差；“提高所选塔层级”仍不能防止 UGUI 按钮覆盖塔。现状不符合“以所选塔为中心呈圆形布局”的预期边缘行为。

实际实现位于 [TowerActionMenu.cs:106](D:/FishTestGame/Assets/Scripts/UI/TowerActionMenu.cs:106) 和 [TowerActionMenu.cs:123](D:/FishTestGame/Assets/Scripts/UI/TowerActionMenu.cs:123)。矩阵检查通过；真实场景下塔投影、层级和点选仍需 Play 验收。

### UI-02 · P2 · 超宽屏结算理由压到操作按钮

**修复已实施**：先预留底部操作栏，再将星级/成绩/评分说明分配在可用纵向区域；理由区从剩余空间计算，文字不会再进入按钮区域。[2560×1080 修复后预览](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/evidence/LevelClearView-zh-Hans-2560x1080-quality-savefailed-isolated-editor-preview.png)及 1920×1080、1280×720、2340×1080、1024×768 预览均通过目视检查。

**触发条件**：2560×1080，结算显示理由文本。

**现象与证据**：按当前 Canvas 缩放，逻辑高度约 935.31。RatingReasons 固定占据自顶端 725–855；底部按钮从 h-145，即约 790.31 开始，因此两者纵向相交约 **64.69 个 UI 逻辑单位**。隔离探针填入已有正式本地化文案后，理由文字贴住并跨过“返回关卡选择”按钮上缘。

- [带理由文案的隔离复现截图](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/LevelClearView-zh-Hans-2560x1080-reasons-probe.png)
- [当前结算合成预览](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/evidence/LevelClearView-zh-Hans-2560x1080-synthetic-savefailed-isolated-editor-preview.png)
- 定位：[TacticalForgeLayout.cs:123](D:/FishTestGame/Assets/Scripts/Core/UI/TacticalForgeLayout.cs:123)，理由与按钮分别位于 130–133 行。
- 正式文案入口：[LevelClearView.cs:169](D:/FishTestGame/Assets/Scripts/UI/LevelClearView.cs:169)，理由填充在 187 行。

**影响**：理由与操作区域难以分辨，长文案和多行内容还可能加重拥挤。此问题是布局问题，不能据此推断评分计算或存档逻辑错误。

实际实现位于 [TacticalForgeLayout.cs:120](D:/FishTestGame/Assets/Scripts/Core/UI/TacticalForgeLayout.cs:120) 附近。布局在目标比例下不重叠；结果数值、评分语义及末关状态仍需通过真实结算验收。

### UI-03 · P2 · 图鉴中文页面暴露英文工程说明

**修复已实施**：图鉴改用按塔型区分的玩家说明，不再展示配置表里的工程备注；9 个升级/说明模板及三语说明已补至 Localization.xlsx 并完成 Luban 导出。缺失字形扫描为空。[修复后简中图鉴](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/evidence/TowerCodexView-zh-Hans-2560x1080-quality-description-isolated-editor-preview.png)显示本地化说明并保留正式数值。

**触发条件**：中文打开塔图鉴的单塔详情。

**现象与证据**：普通塔描述包含英文成本与理论 DPS 等工程表述，中文页同时出现未翻译文字和过细的小数精度。运行代码直接尝试以完整 Desc 字符串查本地化，找不到就显示原文；只读核对与中文截图确认了此回退。

- [中文图鉴当前截图](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/review-evidence/TowerCodexView-zh-Hans-2560x1080-geometry-probe.png)
- 定位：[TowerCodexItem.cs:96](D:/FishTestGame/Assets/Scripts/UI/TowerCodexItem.cs:96)，回退表达式在 98 行。
- 数据：Assets/ConfigJson/tbtowerinfo.json；缺项明细见 source-audit.json。

**影响**：本地化不完整，描述读起来像调试/数值表说明，原始精度破坏页面的信息层级。它不同于上一轮已补齐的 16 个固定 UI 词条；不能以固定词条扫描为 0 证明动态描述全部本地化。

实际逻辑位于 [TowerCodexItem.cs:96](D:/FishTestGame/Assets/Scripts/UI/TowerCodexItem.cs:96) 与 [TowerPresentation.cs:8](D:/FishTestGame/Assets/Scripts/UI/TowerPresentation.cs:8)。修复后覆盖三语代表页；源表与导出译文对照见 `localization-quality-fixes.csv`。

### UI-04 · P2 · 减速塔升级预览遗漏核心收益

**修复已实施**：升级摘要现在按塔型显示实际提升：减速塔显示减速比例、覆盖范围及光环刷新间隔；输出塔显示伤害/DPS、射程、攻击间隔。金币不足仍显示差额，满级继续显示满级状态。多语言预览保留在本目录 evidence 下。

**触发条件**：点击减速塔“更多”，查看 Lv.1→Lv.2 或 Lv.2→Lv.3 的升级预览。

**现象与证据**：主属性区已经按 IsSlowAura 分支显示减速，但升级对比仍使用统一硬编码 ATK / RNG 模板，未表达减速塔的核心提升。


当前中文页面的升级区域也会保留 ATK/RNG 硬编码标签；本轮未调用真实塔的 Show/RefreshButtons 生命周期。

- 定位：[TowerInfoView.cs:296](D:/FishTestGame/Assets/Scripts/UI/TowerInfoView.cs:296)，关键模板在 298 行。
- 已有正确的塔型分支可参考：[TowerInfoView.cs:248](D:/FishTestGame/Assets/Scripts/UI/TowerInfoView.cs:248)。
- 正式数据与求值记录见 source-audit.json 和 final-review-state-mcp.jsonl。

**影响**：玩家看不到减速塔升级最主要的提升，容易以为只是花钱加射程。此项是界面信息缺失，不能据此认为实际减速效果没有升级。

实际逻辑位于 [TowerInfoView.cs:296](D:/FishTestGame/Assets/Scripts/UI/TowerInfoView.cs:296) 与 [TowerPresentation.cs:18](D:/FishTestGame/Assets/Scripts/UI/TowerPresentation.cs:18)。预览覆盖三种塔、不同等级、金币不足/满级及多语言；实际升级事件和金币扣除仍走现有玩法逻辑。

### UI-05 · P3 · 圆形按钮的透明方角仍可能截获点击

**修复已实施**：环形按钮加上 `CircularRaycastFilter`，仅允许圆内点选；不用 Alpha 纹理命中测试，因此不需要启用纹理 Read/Write。Unity `Image.Raycast` 探针测试 3 个按钮共 3/3 圆心命中、3/3 边缘容差命中、0/3 透明方角命中。

**触发条件**：点击圆形按钮矩形范围内、可见圆形之外的透明角区。

**已确认配置**：三个按钮 RectTransform 为 124×124，生产 Image 的 raycastTarget=true、alphaHitTestMinimumThreshold=0；action-circle.png 四角透明（采样 alpha=0）。因此当前命中配置按矩形接收，尚未表达可见圆形边界。

- 定位：[TacticalForgePrefabBuilder.cs:255](D:/FishTestGame/Assets/Editor/TacticalForgePrefabBuilder.cs:255)，圆图及 Image 设置在 257 行。
- 生产资产：Assets/_UIAssets/UI/TacticalForge/Buttons/action-circle.png。
- 参数输出见 isolated-layout-probe-mcp.jsonl，透明度采样见 source-audit.json。

**风险与限制**：玩家视觉上点的是按钮外地图，实际仍可能命中升级/出售/更多；本轮没有运行实际 Pointer/EventSystem 链，因此未声称已复现一次真实误升级或误出售。出售已有确认流程，风险不等于直接卖塔。

实现位于 [CircularRaycastFilter.cs:7](D:/FishTestGame/Assets/Scripts/Core/UI/CircularRaycastFilter.cs:7)，由 [TacticalForgePrefabBuilder.cs:257](D:/FishTestGame/Assets/Editor/TacticalForgePrefabBuilder.cs:257) 接入三个 HUD 动作按钮。实际屏幕密度、触摸手势与地图点选冲突仍需设备检查。

## 4. 已排除的误报与仍需观察项

### 不列为当前缺陷

- 预览的 HUD 中 Pause/Start 英文仍由简化 Populate 直接填入，不能据此声称正式运行缺少本地化。TowerInfo 预览已改为使用生产升级摘要格式；不过它仍是隔离预览，不调用真实玩家存档/金币单例。
- 设置预览里的语言下拉内容未由实际业务脚本初始化，不据此声称运行时语言列表为空。
- 比较模式的第三张卡片在 4:3 首屏部分可见，是垂直 ScrollRect 的内容；不能只看截图认定剩余塔型不可访问。
- 当前三类塔各有 3 个等级。定点英文比较预览中 DescText 的 isTextOverflowing=False，未证实“后续等级被永久截断”。
- 首批 16 个固定本地化词条已补入并导出，使记录由 347 增至 363；本次瑕疵修复另追加 9 个至第 372–380 行，当前为 372 条，交付扫描缺项为 0。
- 隔离 HUD 棋盘保持居中；其宽高受棋盘比例约束。此轮不把合理留白等同于未尽量填充，也不以 UGUI 预览替代真实战斗相机验收。

### R-01：图鉴长描述的潜在行间冲突（已修复）

2560×1080 下，单塔卡片高约 435.31。修复后紧凑卡片的说明从 y=148 开始，属性行与说明框之间至少留 16 个逻辑单位；455px 以下的卡片使用紧凑标题/定位行，不会把说明框延伸到首属性行。长文案对应实际字形仍应随未来翻译改动复查。

定位：[TacticalForgeLayout.cs:202](D:/FishTestGame/Assets/Scripts/Core/UI/TacticalForgeLayout.cs:202)。

### 后续运行检查

真实塔抬层与恢复、边缘选塔、更多→关闭返回快捷组、出售确认、升级刷新、地图空白取消选择、按钮外点击穿透、世界坐标到 UI 坐标、三语切换、真实 Android 安全区和触摸尺寸，仍需在 Play Mode/设备上检查。比较卡片文字在 1024×768 预览中已缩到约 13.6 屏幕像素，仅作为可读性观察；没有 DPI 数据，不能宣称通过或不通过 48dp 标准。

## 5. 修复完成情况

UI-01 至 UI-05 和 R-01 的代码/资源修正已完成。后续只剩 README 所列的 Play Mode 和 Android 真机验收，特别是真实相机投影、塔层级、返回环形菜单、出售确认、不同设备安全区及触摸手势。

可编辑问题清单：[ui-quality-findings.csv](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/ui-quality-findings.csv)。

修复文件与词条行号另见 [修复说明](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/changes.md)、[验证记录](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/validation.md) 和 [9 个新增本地化词条](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/localization-quality-fixes.csv)。

