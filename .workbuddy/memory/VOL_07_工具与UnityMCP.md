# VOL_07 工具 / Unity MCP / 环境事实与待办

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：Unity MCP 两版连接方式与坑、Python/脚本兜底、怪物素材管线、发布核查、已知待办与环境事实。

## Unity MCP（两版严禁混用）
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

## MCP 改 PlayerSettings 图标（2026-10-29 实测技巧，可复用）
- **PlayerSettings 是 `UnityEngine.Object` 派生类**（UnityCsReference `Editor/Mono/PlatformSupport/PlayerSettingsPlatformIcons.bindings.cs`）：`Resources.FindObjectsOfTypeAll(typeof(UnityEditor.PlayerSettings))` 拿到原生单例后可直接 `new SerializedObject(...)` 改序列化数据（本项目 instanceID 命中 1 个）。iOS/tvOS 等无 Kind API 的平台就靠这条路。
- `m_BuildTargetPlatformIcons` 的 `m_BuildTarget` 是**字符串**（"Android"/"tvOS"/"iPhone"），读 `intValue` 会抛 "type is not a supported int value" 并刷控制台 error；每槽 `m_Icons` 元素含 m_Textures/m_Width/m_Height/m_Kind/m_SubKind，赋值 = `m_Textures.arraySize=1` + `objectReferenceValue=Texture2D`。
- API 路线：Standalone 用旧版 `PlayerSettings.SetIconsForTargetGroup(BuildTargetGroup.Standalone, Texture2D[])`（数组按 GetIconSizesForTargetGroup 顺序 1024..16）；Android 用 `GetSupportedIconKindsForPlatform(Android)` 得 Legacy/Round/Adaptive 三个 Kind，`GetPlatformIcons` 取槽、`slot.SetTextures(texs)`、`SetPlatformIcons` 写回；**Adaptive 槽 SetTextures 顺序 = [Background, Foreground]**（来自 `PlatformIconKind.customLayerLabels` 反射）。`BuildTargetGroup.iPhone` 已废弃，要用 `iOS`。
- execute_code 是 CodeDom（C#6）：无 out var/本地函数/模式匹配；复杂片段写临时 .cs 文件再读入执行，避免 shell 转义地狱。
- 改完必须 `EditorApplication.ExecuteMenuItem("File/Save Project")`（2022.3 存在，返回 true）才落盘；磁盘核验直接 grep ProjectSettings.asset 的 guid 引用数（本工程图标节应为 8+50=58 处）。
