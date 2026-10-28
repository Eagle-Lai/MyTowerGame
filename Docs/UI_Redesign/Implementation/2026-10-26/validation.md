# 验证范围与结果

本轮只做工程要求的 MCP 编译、定点资产检查和隔离编辑器布局预览。最终交互、发布包及 Android 设备验收由用户执行。

## 工程身份与连接

- 工程根：`D:/FishTestGame`。
- 磁盘与现场版本：`2022.3.62f3c1`。
- 本任务 MCP：`http://127.0.0.1:8084/mcp`，现场实例 `FishTestGame@0c9048e2c2ec99ee`；实例 ID 只作本轮证据，重连应重新发现。
- 项目目标 Android；编辑器宿主 WindowsEditor。验证期间活动场景 Boot，未播放。
- 使用本任务专属 8084 客户端读取 custom-tools/instances，选定本工程，再核对 projectRoot 与 ProjectVersion.txt。常规入口为 `Tools/ui_mcp.py`；最后一次收尾通过本机 Node 原生 Streamable HTTP 完成同一身份核对与验证流程，没有切换其他任务的连接配置。

## 编译与日志

代码批次完成后执行 force/all/request 刷新；等待重载恢复，再重新选择实例、核对身份并读取 editor/state。HUD/塔操作改动的最终证据保存在 `evidence/mcp-hud-radial-refresh-final.jsonl` 与 `evidence/mcp-hud-radial-compile-final.jsonl`；prefab 与预览证据在 `evidence/mcp-hud-radial-assets-final.jsonl`。

最终编译结果为 `EditorUtility.scriptCompilationFailed=false`；编辑器无编译/域重载/资源更新，ready=true。本次 error 控制台查询返回 0 条，涵盖当前编译检查；刷新遇过域重载暂时断连，服务恢复后继续核对，未把断连当编译成功。

收尾补齐 `LocalizationPrefabBinder` 的 HUD 标签父节点空引用防护后，再次执行 force/all/request 刷新及重连身份核对。`evidence/mcp-hud-radial-final-guard-refresh.jsonl` 与 `evidence/mcp-hud-radial-final-guard-compile.jsonl` 记录本次最终结果：编译失败标志为 false、编辑器 ready、error 查询 0 条、22 个 UI prefab 引用问题 0 项。当前仍为 Boot 场景 Edit Mode，没有重新进入 Play Mode。

之前实施阶段曾观察到 Curl 18/52 网络传输错误且无文件/堆栈；最终检查当前 error 查询为 0。未清空控制台；这些传输记录没有被认作 UI 编译错误。

## 定点资产检查

`TacticalForgePreview.ValidateAssets()` 覆盖 22 个 UI prefab，检查 Missing Script 和已失效的序列化对象引用；当前 issueCount=0。结果在 `evidence/prefab-reference-check.json`。同时检查 AOT 壳没有对 Assets/Scripts 热更脚本的直接依赖，并列出其嵌入字体依赖。

该检查不会证明所有运行路径或字段语义正确，也不覆盖打包后的 Shader、资源加载和 HybridCLR 剥离。

在独立 PreviewScene 对首关正式 7×13 地图做五种目标比例的相机投影检查：棋盘四角均位于预留显示区内，相机 pixel rect 未改变，WorldToScreenPoint → ScreenToWorldPoint 的回转误差最大约 0.00000184 世界单位。证据为 `evidence/mcp-camera-framing.jsonl`；此项仅验证几何投影，不覆盖运行输入或真实安全区。

资源清单记录每项 SHA256 与引用方式。119 张独立肖像均有可见 alpha；已修复透明导出和错误地把方向图身体零件当完整肖像的问题。最终统计见 delivery-inventory.json。

85 行状态表逐项匹配 page-manifest 的唯一 ID；没有用“其余沿用”代替逐项映射。首批 UI 文案审查发现的 16 项缺项已按用户追加授权，用代码定点补入 Localization.xlsx 并由标准 Luban 导出；随后瑕疵审查另追加 9 项塔说明/升级模板。当前正式导出共 372 条，交付缺项扫描为 0；两批新增行与三语译文分别见 localization-added.csv 和 localization-quality-fixes.csv，没有直接编辑生成 JSON。

## 编辑器预览证据

文件名同时包含页面、语言、分辨率、状态和 `editor-preview`。当前覆盖 1920×1080、1280×720、1024×768、2340×1080、2560×1080，包含简中、繁中和英文代表页。

| 预览 | 能说明什么 | 不能说明什么 |
|---|---|---|
| MainMenu | 正式 prefab 主视觉、按钮、品牌和字体渲染 | 兼容存档实际存在、启动成功 |
| Select formal-config | 正式有效关卡记录、地图网格、当前选择结构 | 真实解锁/成绩；合成预览统一未评级不是用户记录 |
| LevelDetail formal-config | 实际地图、初始金币/生命、配置波数、正式波次敌人肖像/名称与双栏适配 | 完整评级/历史字段及运行交互；隔离预览只填部分评级/历史字段 |
| Hud synthetic-radial | 地图居中构图、精简HUD、选中塔、三按钮环形布局 | 相机运行取景、真实塔层级、点击/升级/出售结果 |
| Hud synthetic-more | 4:3 下的地图布局和“更多”触发的塔详情弹窗 | 实际输入、遮罩关闭、返回环形动作及塔操作 |
| TowerCodex | 标签页单塔与正式全等级比较布局 | 图鉴按钮运行时切换、加载句柄正确 |
| MonsterCodex | 独立完整肖像、大卡片与详情布局 | 所有条目运行滚动、点击与读表恢复正确 |
| LevelClear synthetic-savefailed | 保存失败解释、禁用下一关和恢复按钮布局 | 真正评级/保存失败/重试成功；没有写真实存档 |

早期 `*-authored-editor-preview.png` 保留作实施过程证据，其中旧 SelectView 没有填充正式列表，不能作为数据绑定成功证明；最新检查使用 `formal-config-isolated-editor-preview`。

## 未执行及需用户完成

没有进入 Play Mode、做 APK/AAB 构建、发布 AB/热更 DLL、安装部署、真实删档或长时间压测。

用户应按 README 的正式入口验证：继续与解锁、点按/拖动单次扣款、非法落点、点塔后的层级/环形操作和边界夹取、More 详情弹窗的关闭回退、暂停来源、风险确认、图鉴切换、三语刷新、胜败/低星/新纪录、保存失败与重试、真实末关。稀有失败状态使用隔离测试记录。


## UI 瑕疵修复验证（2026-10-26）

- 项目仍为 D:/FishTestGame / Unity 2022.3.62f3c1，经实际 8084 MCP 现场重新选择 FishTestGame 实例并核对路径/版本。Boot 场景 Edit Mode。
- 最终 C# 修复批次执行 `refresh_unity(force/all/request, wait_for_ready=true)`；末次 `scriptCompilationFailed=false`，compiling/domain reload/assets updating 均为 false，ready_for_tools=true；error 控制台查询 0。中间有一轮预览代码字段名错误（CS1061），已改为 `map.Cols` 并重跑最终刷新，最终日志为零错误。
- 更新 5 个正式 UI prefab 后，`TacticalForgePreview.ValidateAssets()` 对 22 个 UI prefab 检查 missing script/坏引用为 0，原 prefab GUID 未变。
- `TowerActionMenu.TryGetButtonPositions` 在 1920×1080、1280×720、2340×1080、2560×1080、1024×768 五种逻辑尺寸，遍历首关 13×7 棋盘共 455 个锚点：无按钮越出 HUD/地图安全边距、无按钮彼此相交、无布局失败。
- Unity Image.Raycast 圆形过滤探针：3个按钮中心均命中；离轴边缘点3/3命中；透明方角0/3命中。该 API 探针不等同真机触摸/完整 EventSystem 输入路径。
- 隔离预览矩阵共18张：四种HUD边缘/角落、结算页五种尺寸、TowerInfo六种塔型/等级/金币状态、塔图鉴三语。目视确认所列内容与按钮无重叠；预览仍禁用玩法脚本且合成选择/结算状态。
- Localization.xlsx 第372–380行追加9个唯一 key；新增文案占位符三语一致。Luban 正式导出 10 张表完成，导出词条总数372、固定/动态 key 缺项扫描0；原关卡与非本地化 XLSX、非本地化 JSON 和 Assets/Gen 生成代码的哈希/规范化语义检查未变。显式允许的文件仅 Localization.xlsx 与 tblocalization.json。
- UI 本地化新字形预热缺项为空。没有进入 Play Mode、没有构建或部署 APK、没有在 Android 真机验证安全区/尺寸/点击，没有真实结算或存档写入。
- 证据：`fix-evidence/final-compile-retry-mcp.jsonl`、`final-quality-preview-matrix-mcp.jsonl`、`final-interaction-verification-mcp.jsonl`、`export-and-compile-mcp.jsonl`、`localization-quality-fixes.csv` 与 `fix-evidence/before-config-hashes.json`。

相机显示区现在按顶部/底部 HUD 对称留边，让地图在游戏可用区域居中；选择塔或打开详情不再预留右侧相机区域。pixel rect 与原坐标换算保持不变。实际安全区、地图可见性、点击位置一致性、缩放平移及环形动作边缘限位仍需运行检查。48dp、低亮度可读性、Android ETC2 支持/画质、图鉴内存、动态字体开销和密集战斗性能未通过设备验收。

## 本地化源表补齐

- 首批本地化补齐新增 `Localization!B356:F371` 的 16 个唯一 ID，三语与交付清单一致；该阶段原 347 条记录逐条未变，记录总数增至 363。UI 瑕疵修复后又新增 B372:F380 的 9 个唯一 key，当前正式导出总数 372，见上方本轮验证记录。
- 使用现有 Luban 导出链；批处理会清掉不属于生成代码的 FTProject.Gen.asmdef，已按导出前 SHA256 原样恢复，再通过本工程 `LubanExporter.ExportInternal` 的 KeepFilesInCodeDir 保护入口成功导出。程序集划分未变，其他源表及配置数据无变化；生成 C# 只有换行格式差异，没有语义差异。
- 本轮没有改关卡/评级配置，因此 tblevelrating.json 及原 runtimeContentHash 原样保持。对照结果见 `evidence/localization-export-check.json`。
- 通过 8084 MCP force/all/request 刷新并重连核对后，scriptCompilationFailed=false、无编译或域重载、ready=true；error 查询 0 条，22 个 UI prefab 引用问题 0 项。证据为 `evidence/localization-refresh-mcp.jsonl`、`evidence/localization-compile-font-preview-mcp.jsonl`。
- 新增文案涉及的 170 个唯一字符已预热到现有许可字体，missingCharacters 为空；更新简中 HUD 环形预览，并新增繁中同状态预览，“更多”由正式导出表取得。未进入 Play Mode，没有进行设备验收。

