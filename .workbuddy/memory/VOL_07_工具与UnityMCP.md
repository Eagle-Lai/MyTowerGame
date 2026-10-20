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
- 2026-10-19 [家用D]：GitHub 最新提交 `2b74516`（完成30关25波长路线经济重设计）含 3928 个文件、768MB 平衡证据产物（`Luban/BalanceDesign/Evidence30x25` + `Docs/BalanceEvidence`，占 98%）；`.git` 已 2.8GB。用户决定**不做任何清理**，保持原样。
