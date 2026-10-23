# FreedomTower_1 —— 项目工作规范

## 工程与 MCP

- 工程根目录：`D:\FreedomTower_1`；Unity `2022.3.62f3c1`，实际版本以 `ProjectSettings/ProjectVersion.txt` 为准。
- MCP 插件：`com.coplaydev.unity-mcp`；Codex 服务名 `unityMCP`，工具前缀 `mcp__unityMCP__*`，HTTP 地址 `http://127.0.0.1:8082/mcp`。
- 插件使用 HTTP Local `http://127.0.0.1:8082` 并启用 Auto-Start on Editor Load。8080 是另一个 Unity 2020 工程 CatchFish_Android 的桥接端口；本项目验证使用 8082。
- 操作前先读取 `mcpforunity://custom-tools`、`mcpforunity://instances`（`server="unityMCP"`），选择当前列表中 FreedomTower_1 的完整 ID，调用 `set_active_instance`；再读 `mcpforunity://project/info`，确认 `data.projectRoot=D:/FreedomTower_1` 与 Unity 版本正确。新会话、重连、域重载后重新选定并核对，不依赖窗口焦点或上个会话的实例 ID。

## MCP 未开启时

- 用户允许为本项目开发与验证自主启动/重连已有 MCP，无需逐次询问。先检查 8082 服务和本工程桥接实例；复用在线服务，优先使用插件 HTTP Local 自动启动或 MCP 窗口的启动/连接功能。服务离线时可通过可用的本机进程/编辑器界面操作恢复；不要依赖已离线的 MCP 工具启动自身。
- 编译重载短暂断线先等约 5 秒再重试；无进展则限次尝试，不重复启动服务、抢占端口或连接另一个工程。
- 无法自主恢复时，及时提示用户打开 `D:\FreedomTower_1` 的 Unity 2022.3.62f3c1，在 MCP 窗口开启 HTTP Local `http://127.0.0.1:8082` 服务并连接，并在 Codex 启用/重连 `unityMCP`；说明实际失败环节。恢复后重新选定实例、核对工程身份并补做验证；最终未连接则明确说明编辑器验证未完成。

## 代码修改后的强制验证

1. 完成同一批 C# 改动后，确认目标实例和编辑器状态，调用 `refresh_unity(mode="force", scope="all", compile="request", wait_for_ready=true)`。
2. 间隔 1~2 秒读取 `mcpforunity://editor/state`，直到 `data.compilation.is_compiling=false`、`data.compilation.is_domain_reload_pending=false`、`data.assets.is_updating=false`、`data.advice.ready_for_tools=true`；编译期间不继续修改代码。
3. 使用 `read_console(action="get", types=["error"], count="50", format="json")` 检查编译错误及异常，必要时用 `filter_text="error CS"` 定位并分页。`execute_code` 可用时补查 `return UnityEditor.EditorUtility.scriptCompilationFailed;` 应为 `false`。
4. 本次错误修复后重复验证。历史错误结合时间和现状说明，不擅自清空日志。MCP 断线先等约 5 秒重试，并重新选定实例和核对身份；未连上就明确报告未完成编辑器验证。

运行时排查先读取本工程错误日志，再查看状态、复现和修改；不得使用 CatchFish_Android 的 `unity` 结果作为本工程验证。Unity 2020 的专用语言/API 限制不自动适用于本项目。进入/退出 Play Mode 和破坏性操作按用户当前授权处理。

## 配置表只能手工维护（2026-10-21 用户定规，最高优先级）

- **禁止任何脚本批量改写关卡配置表**：`Luban/Config/Datas/Levels/L01..L30/**`、`Luban/Config/Datas/EnemyData.xlsx`、`Luban/Config/Datas/__tables__.xlsx`。
- `Assets/ConfigJson/**` 与 `Assets/Gen/**` 是 Luban 的**导出产物**，只由「改表 → 跑 Luban 导出」这条链产生，不允许第三方脚本直接写。
- `.workbuddy/tools/balance_pipeline.py` 的 `apply` / `rollback` 及事务提交层**已整体移除**（`apply_plan` / `commit_files` / `job_lock` / `restore_transaction` / `check_managed_conflicts` / `assert_sources`）。不要为了"方便"把它们加回来；只允许用它的只读能力：`inspect` / `generate` / `preview` / `validate` / `simulate` / `verify-layout` / `stage`（`stage` 只写 `--out`，且禁止指向 `Luban/`、`Assets/`）。
- 手工改表后的标准流程：改 `Levels/Lxx/*.xlsx` → 跑 Luban 导出到 `Assets/ConfigJson` → **重算并重封 `runtimeContentHash`**（每关 LevelRating 行）→ Unity 里确认日志 `[Rating] Runtime configuration SHA256 verified`。
- 已被删除的写表脚本（需要时从 git 历史取）：`migrate_split_level_tables.py`、`migrate_config.py`、`gen_m3_levelmaps.py`、`gen_m3_waves_rounds.py`、`apply_m2_monsters.py`、`add_levels_9_15/16_20_*.py`。
- 仍然保留的两个人工工具：`apply_levelmap_export.py`（地图编辑器「一键写入」只写当前关的 `LevelMap.xlsx`）、`_manual_l1_tune.py`（第一关数值手工调整，按倍率写入）。


## 无声版本维护（2026-10-23）

- 本轮用户明确允许删除声音表，并以自动方式定点移除 `__tables__.xlsx` 中的声音登记和 `Localization.xlsx` 中仅服务于声音的条目；该授权不适用于关卡、敌人及其他数值表。
- 项目声音系统及声音生成入口已移除。Luban、UI 与资源收集器重建必须维持无声版本；保留语言、存档、评级、动画、特效及共享插件通用 API。
