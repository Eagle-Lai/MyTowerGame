# Tactical Forge UI 工程实施交付

目标工程：`D:/FishTestGame`，Unity `2022.3.62f3c1`，Android。实际 UI 预制体、呈现脚本、字体、图像与构建器已经落盘；85 个设计状态已建立逐项实施映射。当前是工程实现交付，尚未完成用户运行与真机验收。

## 从哪里查看

- [界面瑕疵审查报告](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/ui-quality-review.md)：原审查与逐项修复结论；Play/Android 设备验收仍待完成。
- [瑕疵问题清单](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/ui-quality-findings.csv)：5 项状态、修复证据和后续验收条件。
- [本轮新增本地化词条](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/localization-quality-fixes.csv)：9 个塔型说明/升级文案 key，源表行 372–380；已走 Luban 正式导出。
- [逐状态实施表](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/ui-state-implementation.csv)：85 个 ID 的入口、预制体、脚本、数据源、触发条件及限制。
- [修改说明](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/changes.md)：工程链路、文件用途、设计差异。
- [验证记录](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/validation.md)：MCP 编译、引用检查和未执行项。
- [资源清单](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/asset-manifest.csv)：来源、尺寸、GUID、SHA256 和加载方式。
- [首批已补齐词条](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/localization-added.csv)：首批 16 项简中、繁中、英文及源表行号（含 More）；已写入源表并完成标准 Luban 导出。瑕疵修复阶段追加的 9 项见上方词条清单。
- [待补词条扫描](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/localization-required.csv)：当前 0 项；本 CSV 不参与运行。
- [机器可读统计](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/delivery-inventory.json)。

本轮瑕疵修复使用实际 8084 MCP：455 个塔位几何组合通过，18 张修复后隔离预览已生成；编译失败标志为 false、控制台 error 查询为 0。没有进入 Play Mode、构建 APK 或做真机输入测试。

代表性编辑器预览：[主菜单](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/evidence/MainMenuView-en-1920x1080-formal-config-isolated-editor-preview.png)、[HUD 环形快捷动作](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/evidence/HudView-en-1920x1080-synthetic-radial-isolated-editor-preview.png)、[HUD 更多详情弹窗](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/evidence/HudView-en-1024x768-synthetic-more-isolated-editor-preview.png)、[塔型比较](D:/FishTestGame/Docs/UI_Redesign/Implementation/2026-10-26/evidence/TowerCodexView-en-1920x1080-formal-compare-isolated-editor-preview.png)。

## 实际接入范围

启动壳 HotUpdateView、Splash、Loading；主菜单、有效继续、全量选关网格、战前简报、玩法介绍；HUD、塔详情、范围显隐、升级与出售；暂停、设置、风险确认、通用提示；塔型图鉴与全等级比较、怪物列表与详情；胜败、历史比较、保存失败与重试、末关去向。

UIManager 仍通过正式 ResTable / ResLoader 入口打开这些资产。没有另建替代游戏入口，也没有用整页效果图覆盖运行界面。

新增资源位于 `D:/FishTestGame/Assets/_UIAssets/UI/TacticalForge/`。其中 119 张怪物肖像是从既有原始预制体的 SpriteRenderer 层级只读合成的独立 UI 图片，不实例化敌人业务组件；没有修改敌人预制体、图集或制作管线。源字体为 Noto Sans CJK SC，许可在 `Fonts/OFL.txt`。

关卡、波数和敌人记录由当前正式导出配置提供；界面按正式记录显示全部有效内容。图鉴按 119 个 ResName 分组，并展示该形象各配置变体的真实属性范围。

## 用户运行检查入口

1. 使用本工程 Unity，打开 `D:/FishTestGame/Assets/Scenes/Boot.unity`，由用户进入 Play Mode。编辑器资源加载沿现有模拟构建链；若使用已发布的旧 AB/热更 DLL，旧发布内容不会自动包含本轮本地改动，应使用工程既有发布流程更新，不能靠删缓存解决。
2. 从启动链进入主菜单，分别检查没有兼容检查点和存在有效检查点的入口；继续按钮应对应实际关卡。
3. 点选不同关卡应只更新预览；点击“查看简报”后才打开详情。列表应能滚动到最后一个有效关卡，不能自动误进关。
4. 从详情检查挑战、继续、重开风险确认、介绍和返回。核对地图、波数、资源、评级目标、敌人名称与正式配置一致。
5. 在战斗中检查三种塔的点按与拖动、合法/非法落点、取消、范围、倍率、下一波。点选已建塔应只抬高该塔并围绕塔显示“升级 / 出售 / 更多”环形动作；升级沿原逻辑执行，出售先确认，更多打开详情弹窗，关闭后回到环形动作。点地图空处取消选择。一次松手只能建造一次；失败不能扣款。
6. 检查暂停 → 设置 → 返回仍暂停 → 继续恢复。确认离开/重开先解释后果。普通确认可取消；已提交动作禁止重复。
7. 检查三种塔标签页、全等级比较、怪物列表滚动、详情返回列表。详情属性范围不等于当前关卡的单一敌人数值。
8. 正常胜败后检查星级、扣星原因、历史最佳、新纪录与末关；保存失败路径应重试，不能跳过保存进入下一关。失败注入及重置测试请使用隔离测试存档，不操作真实用户记录。
9. 在五种目标分辨率和真实 Android 安全区下切换三语，检查长文本、最大数值、触摸热区、棋盘入口/基地、图鉴滚动及选中塔环形按钮/详情弹窗。

## 已知交付边界

- 用户已明确允许用代码定点补源表。首批 16 个词条追加到 `Luban/Config/Datas/Localization.xlsx` 的 B356:F371，使记录由 347 条增至 363 条；随后瑕疵修复追加 9 个词条至 B372:F380，当前共 372 条，交付扫描 `missingLocalizationKeys=0`。两批均经标准 Luban 导出；三语文案与占位符已核对，运行切换及设备验收仍待完成。
- 战前简报按正式波次引用显示可横向滚动的敌人肖像与名称；不裁切有效敌人种类。
- 条目显示真实最佳记录，不伪造永久“刚产生新纪录”徽标；瞬时新纪录只在成绩成功保存的结算中显示。
- `evidence/` 中是明确标注的编辑器布局预览；结算/HUD 的进度状态为隔离合成状态，不是运行截图。不得以这些图片声称完整战斗、存档、48dp、安全区或性能验收通过。
- 本轮未进入 Play Mode、未构建/部署 APK、未发布热更、未清理真实存档，也未提交或推送。

## 继续维护

定点更新菜单：`Tools/塔防/Tactical Forge/更新实际 UI（保留 GUID）`。它仅更新 UI、UI 字体与独立肖像；不得替换为会重建敌人资源的全工程向导。普通 UIPrefabBuilder 页面入口和 UIResolutionLayout 已同步调用新样式，现有 UI 的 GUID 保留。

本任务专属 MCP 客户端为 `D:/FishTestGame/Tools/ui_mcp.py`，固定 `http://127.0.0.1:8084/mcp`。每次连接重新发现实例并核对项目根路径与版本；本任务没有借用其他工程的 8080/8082 来验证。

