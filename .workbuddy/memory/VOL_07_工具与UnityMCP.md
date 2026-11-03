# VOL_07 工具 / Unity MCP / 环境事实与待办

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：Unity MCP 两版连接方式与坑、Python/脚本兜底、怪物素材管线、发布核查、已知待办与环境事实。

## ★★★ 现行规则：多实体工程 + MCP 端口失败即问（2026-11-03 用户定规，最高优先级）

> 以下为**当前有效**口径，与本节下方所有固定端口记录冲突时，以本节为准。下方历史记录只作线索保留。

- **前提**：本工程包含**多个不同的实体工程**（`E:\MyTowerGame` / `D:\FreedomTower_1` / 历史 `D:\FishTestGame` 等），路径、Unity 版本、插件版本、端口、客户端服务名都可能不同，**运行时按当次实际情况判断，严禁跨工程套用**。
- **端口不是固定值**：以当前实体工程编辑器 `MCP for Unity` 窗口的 HTTP URL / EditorPrefs `MCPForUnity.HttpUrl` 为准。历史出现过的 `8080`/`8082`/`8084`/`8088` 都只是某次某工程的实测值，**不得当默认端口**。
- **触发条件**（满足任一即触发）：① 任一 Unity MCP 工具连接失败/超时/`Not Acceptable`/`session not found`/工具表为空；② `mcpforunity://instances` 为空或找不到当前工程实例；③ 新会话首连、客户端重连、域重载后重连；④ 切换实体工程；⑤ 客户端配置里的 URL 缺失或与当前工程不一致。
- **执行步骤**：① 先按「工作区根目录 + `ProjectSettings/ProjectVersion.txt` + `Packages/manifest.json`」三项只读核对，确认是哪个实体工程（身份不明先问，不猜）；② 只做一次低成本只读自检（插件窗口 URL / EditorPrefs / 客户端配置），**不扫端口段、不逐个试连、不改端口、不重复起服务**；③ 自检仍定不了端口 → **停止动作，主动问用户"当前这个工程用的 MCP 端口是多少？"**，可列历史端口作候选但**不得预选、不得默认采用**；④ 拿到答复才连 → `set_active_instance` → `project/info` 核对 `projectRoot` 与版本；⑤ 连上后把「工程路径 ↔ 端口 ↔ 服务名」记到本文件，**只作线索**，下次仍重新确认；⑥ 用户当次说的"固定用某端口"只管当次/当工程，不跨会话、不跨工程。
- **适用范围**：全部 Unity MCP 操作（资产/场景/编译/Console/Play/菜单/构建）；所有实体工程与所有客户端（Claude Code / Codex / WorkBuddy）；MCP 未启动、端口被改、插件升级、切工程、换机器。**不适用**非 Unity 的 MCP（如 Agent Mail）。
- 完整条文见工程根目录 `AGENTS.md` 的「工程与 MCP」与「MCP 未开启时」两节。

## Unity MCP（两版严禁混用）

> **2026-11-03 起：本节所有固定端口（8082 / 8084 / 8088）全部降级为历史线索**，现行口径见上方「现行规则」；别再照抄这里的端口直接连。
- ★用户授权（10-16）：可自行连接 / 刷新编译 / 进 Play / 验证，无需逐次申请。
- ★工具表刷不出 → 自写 streamable-HTTP 客户端（`.workbuddy/tmp_monkey_dir/mcp_unity.py`，内置 `ProxyHandler({})`）；`execute_code` 里 codedom 一律用双引号。
- [公司E] `com.coplaydev.unity-mcp` v10.3.0，HTTP `127.0.0.1:8082/mcp`（CatchFish 是自研 ws 8080，勿混）。
  - ★系统代理会劫持 127.0.0.1 → 502，脚本必须 `ProxyHandler({})`；
  - `execute_code` 参数需 `{"action":"execute","code":...}`；
  - 客户端先 `initialize` 取 `mcp-session-id`，再按 SSE 解析。
- [家用D] stdio `uvx mcpforunityserver 3.4.8`；Unity 未启动会卡"连接中" → 兜底自起 stdio/`mcp_unity.py`；桥端口 6401 → 6400；`execute_code` 前先 `manage_tools activate scripting_ext`。
- ★长调用（GenerateAll / BuildNow）客户端会超时但 Unity 仍在跑 → 靠产物时间戳判定，**勿重发**；batchmode 与编辑器互斥。
- 无 MCP 时的兜底：`ReporterHotfixBuild.Start` / `StartDllOnly`；GUI 备用 `FT_AutoBuildTrigger`。

## 工具 / 其他
- ★Unity 调用外部 Python 的兜底**禁止硬编码用户路径** → `LevelMapEditorWindow.BuildAbsFallbackCandidates()` 动态扫描；本机命中 `~/.workbuddy/binaries/python/envs/default`（openpyxl 3.1.5）。
- ★`scan_missing_script_refs.py` 必须同时收集 `Assets` + `Packages` + `Library/PackageCache` 的 `.cs.meta`。
- 怪物素材 = 侧视拆件图集（每怪 1 PNG，全朝左）+ `_Common/Animations/<家族>`；朝向靠 `BaseEnemy.FaceMoveDirection` 翻 localScale；表情走动画事件 `SetHead(int)`；`gen_monster_catalog.py` 生成 `MonsterCatalog.cs`。
- 发布就绪核查见 `Docs/ReleaseReadiness/`；云端资料库镜像 `Docs/`（md → space.importer、svg → drive/upload）。

## 已知待办 / 环境事实
- 2026-10-19 [公司E]：已 pull 到 `f3a747a`（UI 多分辨率适配 + HUD 暂停/菜单两按钮职责重划）。拉取含热更码与 Luban xlsx 变更，**尚未**重导配置 / 重编 dll / 重打 AB。

## ★[家用D] FishTestGame 的 MCP 端口是 8088（2026-11-02 实测，纠正 AGENTS.md 的 8084）——**历史线索，已被 2026-11-03「失败即问」规则取代，不再是默认值**
- 插件窗口 `MCP for Unity v10.3.0` 里 Transport=`HTTP Local`、HTTP URL=`http://127.0.0.1:8088`、`Session Active (FishTestGame)`。
  **8084 实测无监听**（`curl` 返回 000），按 8084 查会误判成"MCP 没开"。**先看插件窗口里的 URL 再定端口**，别照抄 AGENTS.md 的 8084。
- 本会话工具表里没有 `mcp__unityMCP__*` 时，可直接用 curl 走 streamable-HTTP（实测可用，49 个工具全部拿到）：
  ```bash
  SID=$(curl -s --noproxy '*' -X POST http://127.0.0.1:8088/mcp \
    -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"x","version":"0"}}}' \
    -D - -o /dev/null | grep -i mcp-session-id | tr -d '\r' | awk '{print $2}')
  # 之后每个请求带 -H "Mcp-Session-Id: $SID"，先发一次 notifications/initialized
  # 响应是 SSE：用 sed -n 's/^data: //p' 取 JSON
  ```
- ★**必须 `--noproxy '*'`**：系统代理会劫持 127.0.0.1（返回 502/000）。
- `execute_code` 必须带 `{"action":"execute","code":...}`，只传 code 会被 pydantic 拒（"Missing required argument: action"）。
- `read_console` 参数：`{"action":"get","types":["error"],"count":"50","format":"json"}`；`refresh_unity` 参数：`{"mode":"force","scope":"all","compile":"request","wait_for_ready":true}`（域重载会断连，返回 `recovered_from_disconnect` 属正常）。
- ★**外部编辑器改 .cs 后 Unity 不会在后台重编译**：`Library/ScriptAssemblies/*.dll` 停在旧时间戳 ≠ 编译失败，是压根没触发。判定"编没编"看 dll mtime；判定"是否失败"用 `execute_code` 取 `UnityEditor.EditorUtility.scriptCompilationFailed`。

## ★多个 AI 客户端可同时连同一个 Unity MCP（2026-11-02 实测）

- **结论：可以**。同一 `http://127.0.0.1:8088/mcp` 连续 `initialize` 出两个独立 `Mcp-Session-Id`，各自 `notifications/initialized` → `tools/list` 都拿到 49 个工具；A 会话在 B 建立后仍有效；两会话**并发** `tools/call read_console` 均成功（406ms / 535ms），无互踢。
- 架构：Unity 侧 `WebSocketTransportClient` 是**客户端**（单条 ws 连 hub），Python `mcpforunityserver` 用 FastMCP + `StreamableHTTPSessionManager`（mcp 1.30.0，`DEFAULT_MAX_SESSIONS=10000`，空闲 30 分钟回收）对外提供 HTTP。客户端只连 URL，不参与 Unity 注册。
- ★**红线：所有客户端必须指向同一个 URL，禁止让各客户端用 uvx/command 自己拉一个 server 进程**。`PluginRegistry.register` 按 `project_hash` 注册，同工程重复注册会 **evict 旧 session**（`plugin_hub._handle_register` 打 "superseded"），后起的会把先起的顶掉，结果是所有客户端一起失联。
- **全局共享（会互相影响）**：`manage_tools` 的工具启用/禁用是 Unity 工程级状态；场景/资产/Play Mode 是同一份工程；`TransportCommandDispatcher` 默认 30s 超时，`refresh_unity(wait_for_ready)`/打包/`ExecuteMenuItem` 这类长任务串行排队 → 同一时刻只让一个客户端跑编译或构建。
- **会话级隔离（互不影响）**：`set_active_instance` 存在 `UnityInstanceMiddleware` 的 per-`session_id` state（session_id = HTTP 的 `Mcp-Session-Id`），各客户端可各选各的 Unity 实例；客户端重启后 session 丢失需重新 set。
- **传输不能混**：`TransportManager` 的 HTTP Local / stdio 只实际用一套；切到 stdio 会让所有 HTTP 客户端瞬间全断。多客户端统一走 HTTP。
- 已接的客户端：Codex `[mcp_servers.unityMCP] url=http://127.0.0.1:8088/mcp`；WorkBuddy `~/.workbuddy/mcp.json` 暂无本工程条目（只有 disabled 的 8082 旧配置），要双开就加同 URL 的 `"type":"http"` 条目。
  - **2026-11-03 复核更正**：`~/.workbuddy/mcp.json` 现已存在 `UnityMCP` 条目 = `{"type":"http","url":"http://127.0.0.1:8088/mcp"}`，其余 6 个 MCP 均 `disabled`。该 URL 仍只是**线索**：连接失败时按现行规则先问用户当前工程的端口，不要因为配置里写着 8088 就直接沿用。

## MCP 改 PlayerSettings 图标（2026-10-29 实测技巧，可复用）
- **PlayerSettings 是 `UnityEngine.Object` 派生类**（UnityCsReference `Editor/Mono/PlatformSupport/PlayerSettingsPlatformIcons.bindings.cs`）：`Resources.FindObjectsOfTypeAll(typeof(UnityEditor.PlayerSettings))` 拿到原生单例后可直接 `new SerializedObject(...)` 改序列化数据（本项目 instanceID 命中 1 个）。iOS/tvOS 等无 Kind API 的平台就靠这条路。
- `m_BuildTargetPlatformIcons` 的 `m_BuildTarget` 是**字符串**（"Android"/"tvOS"/"iPhone"），读 `intValue` 会抛 "type is not a supported int value" 并刷控制台 error；每槽 `m_Icons` 元素含 m_Textures/m_Width/m_Height/m_Kind/m_SubKind，赋值 = `m_Textures.arraySize=1` + `objectReferenceValue=Texture2D`。
- API 路线：Standalone 用旧版 `PlayerSettings.SetIconsForTargetGroup(BuildTargetGroup.Standalone, Texture2D[])`（数组按 GetIconSizesForTargetGroup 顺序 1024..16）；Android 用 `GetSupportedIconKindsForPlatform(Android)` 得 Legacy/Round/Adaptive 三个 Kind，`GetPlatformIcons` 取槽、`slot.SetTextures(texs)`、`SetPlatformIcons` 写回；**Adaptive 槽 SetTextures 顺序 = [Background, Foreground]**（来自 `PlatformIconKind.customLayerLabels` 反射）。`BuildTargetGroup.iPhone` 已废弃，要用 `iOS`。
- execute_code 是 CodeDom（C#6）：无 out var/本地函数/模式匹配；复杂片段写临时 .cs 文件再读入执行，避免 shell 转义地狱。
- 改完必须 `EditorApplication.ExecuteMenuItem("File/Save Project")`（2022.3 存在，返回 true）才落盘；磁盘核验直接 grep ProjectSettings.asset 的 guid 引用数（本工程图标节应为 8+50=58 处）。

## 2026-11-03 Codex 本轮连接线索
- E:/MyTowerGame / Unity 2022.3.62f3c1 / unityMCP / http://127.0.0.1:8087/mcp。已由当前 EditorPrefs、Codex 配置、实例 MyTowerGame@9e28c50b510eeb91 与 project/info 互相核对；仅作线索，下次仍重新确认。

## ★[公司E] MyTowerGame 的 MCP 端口 = 8087（2026-11-03 实测，仅作线索）

- 判定依据（只读）：EditorPrefs `MCPForUnity.HttpUrl_h*` = `http://127.0.0.1:8087`；监听 8087 的进程是
  `uv\...\Scripts\mcp-for-unity.exe --transport http --http-url http://127.0.0.1:8087 --project-scoped-tools --pidfile E:/MyTowerGame/Library/...` → **project-scoped 到本工程**，端点 `http://127.0.0.1:8087/mcp`，服务名 `mcp-for-unity-server 3.4.8`。
- 连上后核对：`execute_code` 返回 `E:/MyTowerGame/Assets | 2022.3.62f3c1 | compileFailed=False`，即身份与版本正确。
- ★**WorkBuddy `~/.workbuddy/mcp.json` 里的 `UnityMCP` 仍指向 `http://127.0.0.1:8088/mcp`（旧工程值）**，所以本会话原生工具列表里没有 `mcp__UnityMCP__*`；改配置需用户信任并重连，且单条 entry 无法同时服务两个端口不同的工程（建议新增 `UnityMCP_MyTower` 条目，而不是覆盖 8088）。
- 不改配置时的兜底：`.workbuddy/tools/mcp_unity.py` + `UNITY_MCP_URL=http://127.0.0.1:8087/mcp`，能列工具/调工具，已验证 `execute_code`、`refresh_unity`、`read_console` 全可用。
  ★**别在 shell 里手拼 JSON 传参**（代码里有 `"` 和 `,` 极易被吃成 `JSONDecodeError: Expecting ',' delimiter`）：用 `python - <<'PY'` 驱动脚本 `importlib` 加载 `mcp_unity.py` → `mu.init()` → `mu.call(tool, dict)`，代码块放 Python 三引号里最稳。
- 编辑器内校验配置表的可靠姿势（`Configs.LoadAsync` 在 Edit 模式**不会完成**，`IsLoaded` 一直 False，别用它做 [Config] 校验）：
  `new cfg.TBEnemyData(SimpleJSON.JSON.Parse(AssetDatabase.LoadAssetAtPath<TextAsset>("Assets/ConfigJson/tbenemydata.json").text))`，再 `GetOrDefault(id).Hp` 对比期望值；这一步同时证明了 Luban json 能被生成类解析。
