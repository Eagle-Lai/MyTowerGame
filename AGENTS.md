# 自由人塔防 —— 项目工作规范

## 工程与 MCP

### 多实体工程（2026-11-03 用户定规，最高优先级）

本工程**包含多个不同的实体工程**：同一份规范与记忆会被多台机器、多个 Unity 工程复用，各实体工程的磁盘路径、Unity 版本、MCP 插件版本、桥接端口、客户端服务名都可能不同。**任何路径、端口、服务名、实例 ID 都必须按"当前实际运行的那个实体工程"判断，不得跨工程套用，也不得沿用上一次会话或其它工程的结论。**

- 已知实体工程（**只作线索，不是默认值**，一律以运行时核对为准）：
  - `E:\MyTowerGame`（公司 E 机，Unity `2022.3.62f3c1`）
  - `D:\FreedomTower_1`（家用 D 机）
  - `D:\FishTestGame`（历史路径/工程名，仅作线索）
- **判定当前实体工程（只读，三者互相印证）**：当前工作区根目录 + `ProjectSettings/ProjectVersion.txt`（Unity 版本）+ `Packages/manifest.json`（依赖与 MCP 插件版本）。三者一致才算确认；不一致或无法判断时先问用户，不要猜。
- Unity 版本一律以 `ProjectSettings/ProjectVersion.txt` 为准，不采信文档里的旧值。
- MCP 插件：`com.coplaydev.unity-mcp`（版本以 `Packages/manifest.json` 为准），传输统一 HTTP Local。
- **端口不是固定值**：以当前实体工程编辑器 `MCP for Unity` 窗口显示的 HTTP URL / EditorPrefs `MCPForUnity.HttpUrl` 为准。历史上出现过的 `8080`、`8082`、`8084`、`8088` 都只是**某次、某个工程**的实测值，**一律不得当作默认端口**（`8080` 曾属 Unity 2020 工程 CatchFish_Android）。
- 服务名按客户端区分、大小写敏感：Claude Code 为 `UnityMCP`（工具前缀 `mcp__UnityMCP__*`），Codex 为 `unityMCP`（工具前缀 `mcp__unityMCP__*`）；以当前客户端实际工具前缀为准。
- 连接后按固定流程核对身份：读 `mcpforunity://custom-tools` → `mcpforunity://instances`（`server` 用当前客户端服务名）→ `set_active_instance` 选当前实体工程的完整 ID → 读 `mcpforunity://project/info` 比对 `data.projectRoot` 与 Unity 版本。新会话、重连、域重载、切换实体工程后都要重做，不依赖窗口焦点或上个会话的实例 ID。
- Unity 操作一律通过 MCP 工具调用；禁止用 Bash/curl/python 直连 `/mcp` 端点。该端点是 streamable HTTP，需要 MCP 会话与 `Accept: application/json, text/event-stream`，手工请求只会得到 400 / Not Acceptable，不能据此判定「MCP 不可用」。

### ★★ MCP 连接失败时的端口确认规则（2026-11-03 用户定规，最高优先级）

**触发条件**（满足任一即触发，不得直接硬试或换端口重试）：

1. 任一 Unity MCP 工具返回连接失败、超时、`Not Acceptable`、`session not found`，或工具列表为空；
2. `mcpforunity://instances` 为空，或列表中找不到当前实体工程的实例；
3. 新会话首次连接、客户端重连、域重载/编译后重连；
4. 切换实体工程（工作区路径变化、用户改开另一个 Unity 工程、或用户明确说"换工程"）；
5. 客户端配置里该工程的 URL 缺失，或与当前工程不一致。

**执行步骤**：

1. **先确认实体工程身份**：按上节三项只读核对，确认当前是哪个实体工程；身份不明时先问用户，不猜路径、不猜版本。
2. **只做一次低成本只读自检**：查看 `MCP for Unity` 插件窗口显示的 HTTP URL、EditorPrefs `MCPForUnity.HttpUrl`、当前客户端配置（如 `~/.workbuddy/mcp.json`）里对应条目。**不扫描端口段、不逐个端口试连、不改插件端口、不重复启动服务、不抢占端口。**
3. **自检无法确定端口 → 立即停止动作，主动询问用户**：「当前这个工程用的 MCP 端口是多少？」必要时一并问清：实体工程路径、Unity 是否已打开、客户端服务名。提问时**可列出历史端口作为候选供参考，但不得预选、不得默认采用任何一项**。
4. **拿到用户答复后才连接**：按用户给出的 URL 建连 → `set_active_instance` 选当前工程实例 → 读 `mcpforunity://project/info` 核对 `projectRoot` 与 Unity 版本。
5. 连上后把「实体工程路径 ↔ 端口 ↔ 客户端服务名」写入 `.workbuddy/memory/VOL_07_工具与UnityMCP.md`，作为**线索记录**；下次仍按本规则重新确认，不自动升格为默认值。
6. 用户在当次会话明确说"这个工程固定用某端口"时，该口径**只对当次会话/当次工程有效**，不构成跨工程、跨会话的默认值。

**适用范围**：

- 覆盖全部 Unity 相关 MCP 操作：资产/场景读写、编译刷新、Console 读取、Play Mode、菜单执行、构建出包。
- 覆盖所有实体工程与所有客户端（Claude Code、Codex、WorkBuddy 等）。
- 覆盖 MCP 服务未启动、端口被改、插件升级、切换工程、换机器等场景。
- **不适用**于非 Unity 的 MCP 连接器（如 Agent Mail），那类按各自连接器状态处理。
- 与本规范其它章节并行生效；与旧文任何"固定端口"表述冲突时，**以本节为准**。

## MCP 未开启时

- 用户允许为本项目开发与验证自主启动/重连**已有**的 MCP，无需逐次询问；但"启动/重连"不等于"猜端口"，端口一律按上节确认。
- 编译重载短暂断线先等约 5 秒再重试（限次）；不重复启动服务、不抢占端口、不连接另一个实体工程。
- 自检与限次重试仍失败 → 按上节第 3 步**主动询问用户当前工程的 MCP 端口**，并说明实际失败环节（卡在哪一步、报什么错）。
- 恢复后重新选定实例、核对 `projectRoot` 与 Unity 版本，补做被中断的验证；最终未连上必须明确报告「编辑器验证未完成」，不得用其它工程的结果替代。

## 代码修改后的强制验证

1. 完成同一批 C# 改动后，确认目标实例和编辑器状态，调用 `refresh_unity(mode="force", scope="all", compile="request", wait_for_ready=true)`。
2. 间隔 1~2 秒读取 `mcpforunity://editor/state`，直到 `data.compilation.is_compiling=false`、`data.compilation.is_domain_reload_pending=false`、`data.assets.is_updating=false`、`data.advice.ready_for_tools=true`；编译期间不继续修改代码。
3. 使用 `read_console(action="get", types=["error"], count="50", format="json")` 检查编译错误及异常，必要时用 `filter_text="error CS"` 定位并分页。`execute_code` 可用时补查 `return UnityEditor.EditorUtility.scriptCompilationFailed;` 应为 `false`。
4. 本次错误修复后重复验证。历史错误结合时间和现状说明，不擅自清空日志。MCP 断线先等约 5 秒重试，并重新选定实例和核对身份；未连上就明确报告未完成编辑器验证。
5. **不得跳过验证**：端口/实例身份未确认时，先按「MCP 连接失败时的端口确认规则」确认，再补做验证；不得改用其它实体工程的实例顶替。

运行时排查先读取本工程错误日志，再查看状态、复现和修改；不得使用 CatchFish_Android 的 `unity` 结果作为本工程验证。Unity 2020 的专用语言/API 限制不自动适用于本项目。进入/退出 Play Mode 和破坏性操作按用户当前授权处理。

## 配置表按授权定点维护（2026-10-21 定规；2026-11-05 用户澄清，所有 AI 必须遵守）

- **“手动改表 / 手工维护”的准确含义**：利用程序代码，精确定位指定工作簿、工作表、行与列（或唯一 ID 对应的字段），定点修改本次获授权的单元格数据。**不要求通过 Excel/WPS 界面点击、键盘输入或电脑控制完成，不得再把“手动”解释成必须操作桌面。**
- **允许代码定点修改源表**：适用于 `Luban/Config/Datas/Levels/L01..L30/**`、`Luban/Config/Datas/EnemyData.xlsx`、`Luban/Config/Datas/__tables__.xlsx` 等配置源表。已确认的修改清单可以由一个程序逐项执行；涉及多个单元格或多个获授权关卡，本身不构成违规。禁止的是**未经授权扩范围、整表重建/覆盖、批量调平或生成器擅自重算配置**。此澄清取代旧文“一律禁止脚本写源表 / 任何脚本批量改写”的字面禁令。
- **定点修改要求**：写入前确定文件、sheet、单元格/唯一 ID、字段及预期旧值 → 新值；核对旧值与当前文件一致，保留改前基准；只写白名单单元格，保留其余数据、公式、格式与工作簿结构。写后回读逐格比对，报告实际改动及白名单外零改动；旧值、定位或范围不符时停止该次写入并核查，不猜测覆盖。
- `Assets/ConfigJson/**` 与 `Assets/Gen/**` 是 Luban 的**导出产物**，只由「改表 → 跑 Luban 导出」这条链产生，不允许第三方脚本直接写。
- `.workbuddy/tools/balance_pipeline.py` 的 `apply` / `rollback` 及事务提交层**已整体移除**（`apply_plan` / `commit_files` / `job_lock` / `restore_transaction` / `check_managed_conflicts` / `assert_sources`）。不要为了"方便"把它们加回来；只允许用它的只读能力：`inspect` / `generate` / `preview` / `validate` / `simulate` / `verify-layout` / `stage`（`stage` 只写 `--out`，且禁止指向 `Luban/`、`Assets/`）。
- 定点改表后的标准流程：代码定点修改获授权的 `Levels/Lxx/*.xlsx` → 跑 Luban 导出到 `Assets/ConfigJson` → 进 Unity 确认 `[Config]` 汇总无失败表。
  **2026-11-01 起不再有 `runtimeContentHash` 重封这一步**：星级评分体系（`tblevelrating` / 30 张 `Levels/Lxx/LevelRating.xlsx` / `LevelRatingEvaluator`）已按用户要求整体删除，通关一律记 5 星，改表不再需要动任何评级表，也不会再出现 `content hash mismatch` 拦关。评分规则待 30 关数值定稿后重做。
- 已被删除的写表脚本（需要时从 git 历史取）：`migrate_split_level_tables.py`、`migrate_config.py`、`gen_m3_levelmaps.py`、`gen_m3_waves_rounds.py`、`apply_m2_monsters.py`、`add_levels_9_15/16_20_*.py`。
- 仍然保留的两个人工工具：`apply_levelmap_export.py`（地图编辑器「一键写入」只写当前关的 `LevelMap.xlsx`）、`_manual_l1_tune.py`（第一关数值手工调整，按倍率写入）。

## 关卡数值改动的范围与确认（2026-11-01 用户定规，最高优先级，与上节并行生效）

适用于用户提出「改关卡数值 / 调难度 / 调血量 / 调金币产出 / 调出怪」等任何涉及关卡数值的请求。

- **默认最小范围**：只改本次请求中明确点名的那一部分（指定关卡 / 指定波次 / 指定怪种 / 指定字段 / 指定行）。**禁止任何形式的外扩**：不"顺手"统一其他关、不为对齐而连带改同类行、不做未被要求的批量调平、不因"看起来不一致"而改其他关。拿不准就问，不拿不准就默认不动。
- **必须先提问确认，得到答复才动手**：每次收到关卡数值修改请求，改表之前必须先向用户提问，至少确认以下四项：
  1. **关卡范围**：哪几关（`L01`…`L30` 具体编号），是否只改其中一关；
  2. **粒度**：哪张表 / 哪个波次（`roundId`）/ 哪一类怪或塔 / 哪个字段；
  3. **数值与口径**：改成多少，或按倍率/百分比改；基准值是配置现值还是实测值；
  4. **是否本轮为"全部关卡应用"**。
  用户未明确范围时，**不得**自行挑一个"最合理"的范围开工，必须等确认。
- **跨关卡只有一种合法情形**：用户在**当次请求**里明确写出「全部关卡应用」（或等价表述：所有关卡都改、L01–L30 全改）。历史会话说过一次**不构成长期授权**，跨请求不复用。即使授权全部关卡，仍要先确认字段与数值，并在动手前列出受影响关卡清单。
- **改完必须交代边界**：报告实际改动的文件 / 关卡 / 波次 / 字段、旧值 → 新值，并给出"其余关卡未改动"的核对结论（`git diff --stat`、导出 json 行数比对等可复核证据），不要只说"改好了"。
- **适用范围**：`Levels/Lxx/*.xlsx`（含 `EnemyData` / `EnemyList` / `RoundData` / `LevelMap` / `LevelRules` / `SceneInfo`）、关卡级代码常量与生成器参数，一律按本条执行。
- **不是扩展的例外**：（2026-11-01 起该条仅作历史说明）原 `runtimeContentHash` 是全局哈希，30 张 `LevelRating.xlsx` 写同一个值属正常重封流程，不算"改到其他关卡"。评级表删除后已无此项，存档语义本身仍不得因本条而改动。

## 空中怪不得相邻出生（2026-11-05 用户定规，所有 AI 必须遵守）

- **规则**：同一关的实际出怪顺序中，任意两只空中怪之间必须至少隔一个非空中出生位置；不论是否同种、同 ID，均禁止空中接空中。仅保证位置隔开，不擅自增加最小秒数要求。
- **唯一判定依据**：`EnemyData.isFlying != 0`。不得根据名称、资源名、`type`、`desc`、旧报告或历史记忆推断；例如名为 `QuickEnemy` 的记录也可能是空中怪。
- **检查顺序**：按当前 `SceneInfo.RoundList` → `RoundData.EnemyIndexs` → `EnemyList.EnemyIndexs` 展开实际出生序列；检查同编组、同回合跨编组和同关相邻回合的边界，禁止只查重复 ID 或只查单个单元格。
- **修改边界**：本规则是长期约束，不构成未来跨关改表的授权。每次修改仍先按「关卡数值改动的范围与确认」取得当次范围。修复顺序时保留每波怪物 ID 的多重集合、数量、属性及出怪间隔；不得顺手改血量、奖励、速度、波型、地图或其他关卡。
- **维护方式**：按上文“配置表按授权定点维护”的定义，允许代码按获授权的单元格清单定点修改 `EnemyList.EnemyIndexs`，无需电脑控制。禁止未经授权扩范围或整表重建，禁止直接改 `Assets/ConfigJson` / `Assets/Gen`，禁止在运行时静默重排或复制/删除怪物来掩盖配置问题。只读工具可以检测并生成待审调整清单。
- **验收**：改表前后运行 `.workbuddy/tools/check_air_spawn_order.py`，分别核查现行 XLSX 与 Luban 导出的 JSON；任何相邻空中怪或缺失/重复引用都必须作为失败报告。输出关卡、关内波号、roundId、编组 ID、出生位置、怪物 ID 及源表单元格。标准流程为代码定点改表 → Luban 导出 → Unity 核对 `[Config]` 汇总；编辑器验证未完成时不得声称全部完成。
- **2026-11-05 本次授权边界**：用户明确确认 L01–L30 全部关卡应用，仅调整 `EnemyList.xlsx` 的 `EnemyIndexs` 顺序，以改前配置为基准，保持每波数量、种类、属性和出生间隔；L01、L02 已符合，源表保持不动。该授权不自动延续至下次请求。

## 原创声音维护（2026-10-27）

- 当前用户已执行 `Docs/prompts/2026-10-27-audio-integration-executable-prompt.md`，本工程接入现有 93 个原创 WAV，覆盖历史“维持无声版本”限制。历史移除报告保留为历史证据。
- 声音入口与生命周期统一由 `Assets/Scripts/Audio/` 管理；语义策略在 `Assets/Audio/Runtime/GameAudioCatalog.asset`，寻址由 `AudioResourceMap` 登记并接入 `ResTable`。不得恢复旧 Luban 声音表或旧生成器。
- 保留 WAV 母版、GUID、源文件和质量报告；人工听感与 Android Player 验收须单独说明，不能由编译或旧技术 QA 代替。
- 声音设置使用 `GameSettings.audio` 与 SQLite `settings.audio.*` 键，沿用 schema 4；不得恢复旧 `game_settings.volume/muted` 列、另开 PlayerPrefs，或修改评级/快照语义。
- 用户在本轮单独授权：仅定点新增 `Localization.xlsx` 的 Master Volume、Music Volume、SFX Volume、Mute 四个三语言词条，并执行标准 Luban 导出。该授权不扩展为其他源表的自动维护权限；上述关卡、敌人和表登记保护条款继续有效。
- 设置 prefab 更新必须同步 `AudioSettingsPrefabBuilder` 与 Tactical Forge / UIPrefabBuilder 调用链。声音收集同时维护现有资产与 `FTYooAssetSetupWizard.CollectPlan`，不得收集 README、CSV、预览或制作源码。
- 实施、接口、存档兼容、实际检查结果和用户验收步骤见 `Docs/AudioIntegration_Implementation_2026-10-27.md`。
