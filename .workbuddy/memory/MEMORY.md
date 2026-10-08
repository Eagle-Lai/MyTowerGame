# FreedomTower 项目长期记忆

> 跨会话**必须遵守**的不变量与入口。流水账写 `YYYY-MM-DD.md`，专题细节看 `Docs/`。
> ⚠️ 本文件有注入体积上限，**超了会被截断失效** —— 只记"踩坑就返工"的事，**新增前先想能不能删**。

## 工程与工具链

- **Unity 2022.3.62f3c1**，2D 塔防（"FreeTower"），根目录 `D:\FreedomTower_1`。
- **远端只有 `origin` = GitHub `Eagle-Lai/MyTowerGame.git`**（原 Gitee 已移除），走本机代理 `127.0.0.1:7892`（端口会变，`netstat -ano | grep 127.0.0.1` 查）。
- ★★ **`git push` 静默挂死**：鉴权其实已成功，卡在 `git credential-helper-selector store` 调 `git config --system -e` → 开了交互式编辑器永久等待。判据：`git ls-remote` 正常、`git push` 却零输出卡住（可挂 6 分钟+）。
  - **唯一有效解法**：`GIT_CONFIG_SYSTEM=/dev/null git push origin main`（每次推送都带上）。
  - ⚠️ 别再试的"根治"：写系统配置 `credential.helperselector.selected=manager` —— **已证伪**，helper-selector 无条件开编辑器。**凭据不缺**（`git credential fill` 秒回 `username=Eagle-Lai`），别往"没令牌"方向查。
  - ⚠️ `.git` 积压 ~2.18GB **孤儿对象**，`main` 可达仅 ~137MB —— **估推送量按可达对象算**，别看 `count-objects` 的 `size-pack`。
- **Luban**：`Luban/Config/Datas/*.xlsx` → `Assets/Gen/*.cs` + `Assets/ConfigJson/*.json`。改表必重导（`gen_code_json.bat`；直调 `Luban.ClientServer.exe` 需 `DOTNET_ROLL_FORWARD=LatestMajor`）。**新表先在 `__tables__.xlsx` 登记**。
- **`ResTable.cs` 是唯一寻址源**（逻辑名 → bundle / assetName / editorPath），**新资源必须登记**。⚠️ 盲区：`check_code.py` 只扫 `ResTable.Get("字面量")`，不扫 `Configs.ConfigKeys` 数组 → 给 ConfigKeys 加表须**手工**同步。
- **AB 分包**：包名常量在 `ResBundle.cs`（全小写下划线）；`Fixed` 定打包范围，`Persistent` 定开机常驻。
- **战斗**：无物理；`EnemyGrid` 空间哈希 + `CombatSystem` 集中 tick；子弹按资源名分池；`BaseManager<T>` 单例；UI 走 `EventDispatcher`。**不变量：塔无目标绝不开火。**

## 资源加载：三套实现并存（★ 改资源链路先读）

- **`ResLoader.Instance`（`IResLoader`）按宏选实现**：`USE_YOOASSET`→`YooAssetResLoader`；`UNITY_EDITOR && !FORCE_AB`→`EditorResLoader`；其余（真机 / `FORCE_AB`）→`BundleResLoader`。回退只需删宏；**新依赖一律加宏**（同 `FORCE_AB`），否则 UPM 拉不下来时整个工程编译不过。
- **分包 `FTBundlePackRule`（`Assets/Editor/YooAsset/`，套宏）读 `ResTable.Bundle`**，输出与 `ResBundle` 逐包一致。**不能用目录规则** —— 分包按玩法语义跨目录（如 `enemy_rats` 跨 `Prefabs/Enemy/` 与 `_UIAssets/Monsters/Rats/`）。未登记资源三级降级：同目录 → 最近的有登记祖先目录 → `misc_<顶层>`；**只有 `misc_*` 是异常信号**。
- ⚠️ **收集器必须 `EnableAddressable = false`**：开寻址会强制地址全局唯一，六个收集目录有 **123 组同名文件** → 收集阶段抛 `Address already exists`。关掉后**定位键 = 资源路径**，与 `ResAddress.EditorPath` 天然对齐。
- ⚠️ **模拟模式不能传空 packageRoot**（`EditorFileSystem.OnCreate` 直接抛）→ `CreateInitOptions()` 先 `EditorSimulateBuildInvoker.Build(pkg, (int)EBundleType.VirtualAssetBundle)` 拿目录。真实包构建用 `EnableSharePackRule = true`。
- ⚠️ **同一版本号构建第二次必抛 `[ErrorCode115] Package output directory exists`** → 向导已自动先删本次版本目录；`ClearBuildCacheFiles=true` 会连 `Simulate` 一起删，故默认关（做成「彻底重建」开关）。
- **入口菜单** `Tools ▸ 塔防 ▸ YooAsset 接入 ▸`，四步：生成收集器配置 / 静态校验 / 构建 / **回读校验**。⚠️ **宏开关在 `FTYooAssetDefine.cs` 且刻意不套宏**（向导本身套宏，否则"用被宏挡住的代码去开宏"死循环）；宏要写**四个平台组**。`BundledCopyOption=ClearAndCopyAll` 只清 `StreamingAssets/yoo`，旧 `AssetBundles` 安全可并存。细节见 `Docs/YooAsset_Integration.md`。
- ⚠️ **3.0.x 与 2.x API 不兼容，网上 2.x 教程不能直抄。★ 初始化必须三步**：`InitializePackageAsync`（**只建文件系统、不加载清单**）→ `RequestPackageVersionAsync()` → `LoadPackageManifestAsync(version)`（**最后这步才 `SetActiveManifest`**）。症状极具欺骗性：初始化日志一切正常，但之后**每次**加载都报 `Active package manifest not found.`。**判据：启动日志版本号是真实值才算成功，打成 `版本=(未知)` 就是漏了后两步。** 有重复初始化检测，已成功过的要复用。
- ⚠️ **释放 `AssetHandle` = 引用计数归零 → 会被 `UnloadUnusedAssets` 回收** → `ReleaseBundle` 只在计数**真正归零**才放句柄。**YooAsset 异常时"抛异常"而非返回失败句柄** → 适配器内全部 try/catch 兜住，否则沿 `Launcher` 回调链抛出 = "启动卡死且看不到原因"。
- ⚠️ **现状：`ReleaseBundle` 业务代码零调用**（`TeardownLevel` 也不调）→ 计数只增不减、资源常驻（AB 实现同样）。接入点在 `TeardownLevel` 第三段，**三套实现要一起改**。

## 字体与 UI

- **全工程统一 TextMeshPro（TMP），禁止再新增 UGUI `UnityEngine.UI.Text`。** 中文字体 `Assets/Font/SiYuanSongTi SDF.asset`（TMP Settings 的 `m_defaultFontAsset` 已指向它）；编辑器取字体走 `EditorUtil.GetDefaultTmpFont()`。字体分包 `font`，常驻。
- 运行时文本用 `TMP_Text`；但 `Button`/`Image`/`CanvasScaler` 仍属 `UnityEngine.UI`（对应文件需 `using UnityEngine.UI;`）。**描边走字体材质 `_OutlineWidth`/`_OutlineColor`**（TMP 不支持 UGUI `Outline`）。
- **`Assets/Editor/UIPrefabBuilder.cs`**：只管理"自己产出的节点"，全量重建会抹掉手工摆位 → 日常用「补缺」，确要重建用「高级（单步重建）」；`UiTmpMigrator.cs` 幂等迁移。对话框骨架走 `CreateDialogShell`。
- ⚠️ **节点名契约（易错）**：View 的 `transform.Find("Panel/X")` 与 `UIPrefabBuilder` **没有映射层**，两边写死同一套名字；写岔只静默打「缺少节点」然后 UI 空白。改名必须**成对改**并跑 `check_ui_contract.py`。

## 关卡结算（通关弹窗）

- 通关与失败**共用** `LevelClearView`，由 `LevelClearInfo.victory` 区分。**打开位置 `GameFlowManager.OnGameOver()`**；**不要**监听 `LevelClearEvent` 开界面（只带 levelId/stars/hpLeft，信息不足）。
- ⚠️ **星级必须"先读后写"**：`SaveManager.RecordClear` 是**只升不降**合并，必须先 `GetStars()` 拿 `previousBest` 再 `RecordClear()`，否则"本局之前"的成绩与"新纪录"都会错。
- 下一关 = **id 大于本关的最小一关**（别写 `id + 1`）。**`Bg` 刻意不接"点击关闭"**（结算是终结状态）；调试键 **F2 强制获胜**走完整结算（含记星）。

## 关卡地图编辑器（一键写入链路）

- **入口** `Tools ▸ 塔防 ▸ 地图编辑器（可视化刷格子）` → `Assets/Editor/LevelMapEditorWindow.cs`。**唯一通路**（改前先读全）：`页面棋盘 → .workbuddy/levelmap_export.json → (Python) LevelMap.xlsx → (Luban) Assets/ConfigJson/tblevelmap.json`。窗口棋盘**只从最后那个 json 读**，漏掉 Luban 这步 = 改了表但工具页和游戏都看不到。
- **「一键写入 xlsx」= 5 步闭环**：①自检（行长 / S·E 各一个 / BFS 可达）→②导 json→③Python 写 xlsx（整表备份）→④`LubanExporter.ExportInternal` 重导→⑤回读 json **逐格比对**；任一步失败即停。**Luban 重导幂等**。
- ⚠️ 写 xlsx 需 `openpyxl`（绕外部 Python 是为不把 ClosedXML 引进 `Assets/Editor`）；用 `…/python/envs/default/Scripts/python.exe`，**PATH 上的 `python` 没装**。校验口径**两处必须一致**：窗口 `CollectProblems()` 与 `apply_levelmap_export.py`。
- ⚠️ 只加棋盘不加 `SceneInfo.xlsx`，那关在游戏里进不去（棋盘 / 波次 / 经济分属两张表）。

## Unity MCP（✅ 已接通并实测，2026-10-08）

- ✅ **2026-10-08 13:02 实测连通**：实例 `FreedomTower_1@520e2c6d`（port 6400，Unity 2022.3.62f3c1）；`read_console` 与 `mcpforunity://project/info` 均已成功返回内容。**Unity 编辑器现在可以直接驱动了 —— 改任何"建东西"的模块前，优先想到可以实际跑一遍验证。**
- **WorkBuddy ↔ Unity 走 MCP for Unity（CoplayDev，MIT）**；官方 `com.unity.ai.assistant` 要求 Unity 6，本工程 2022.3 用不了。我侧配置在 `C:\Users\78296\.workbuddy\mcp.json`（server 名 `unityMCP`）：`uvx --from mcpforunityserver==10.3.0 mcp-for-unity --transport stdio`。
- ⚠️ 三个高频坑（细节见 `2026-10-08.md`）：① uvx 在隔离 venv、PATH 上没有 → 配置里**必须写绝对路径** `…\python\envs\default\Scripts\uvx.exe`；② `mcp.json` **只在启动时读**，改完要完全退出重启 WorkBuddy，再去左侧边栏「连接器」▸ 右上角「自定义连接器」点**「信任」**；③ 两端传输模式必须一致，且 **Unity 里改完 Transport 下拉还要再点会话按钮**（`Start Session` / `Connect`）才真正启动 —— 改下拉只 `StopAsync` 旧传输、**不启动新的**。
- ⚠️ **传输错配的判据**：`instance_count: 0` + 6400 未监听 + 8080 在听 = 错配。HTTP 走 **8080**（Unity 自拉服务端），**Stdio 走 Unity 内 6400 桥**；切换处 = `Window ▸ MCP for Unity` ▸ Connect 页 ▸ Server 区块 ▸ **Transport**。

## 环境限制（沙箱内做不到的事）

- **无法编译**（`MSBuild.exe` / `dotnet msbuild` / `csc.exe` 被拦截）→ 最终编译仍必须在 Unity 里做。~~Unity 编辑器不可直接驱动~~ **已于 2026-10-08 通过 Unity MCP 打破**（见上节）：场景 / 控制台 / 菜单命令 / 脚本读写都可远程驱动。
- **静态校验工具**（`.workbuddy/tools/`，9 个，改动后应全跑）：`check_code`（括号/重名/类名==文件名/EventName/逻辑名）、`check_usings`→CS0246、`check_arity`→CS1501、`check_members`→CS1061、`check_unity_api`、`check_events`、`check_native_symbols`、`check_ui_contract`、`verify_save_roundtrip`。
  - **ROOT 由脚本自身位置推导**，禁止硬编码；已加「扫到 0 文件就 FAIL」自检，**新写的检查必须注入故障证明它会 FAIL**。改动后核对**扫描文件数与 `find` 一致**（本工程：89 Scripts + 21 Editor = 110）。
  - ⚠️ **shell 里跑 Python 别用 `\s`/`\b`/`\w`**（MSYS 转义 → 正则静默失效却仍输出结论）。`check_arity` 仅在**接收者是批内已知类型名**时比对，新文件要加进 `_CHANGED`。

## 命名口径易错点

- `TowerType`：`Normal=1, Aoe=2, Slow=3, Pierce=4, Laser=5`；美术/节点/资源目录里 "**Power**"=Aoe、"**Retard**"=Slow —— 别处不要各写一份。`EffectType`（塔表与子弹表共用）：`None=0, Slow=1, Dot=2, Aoe=3, Laser=4`。
- **塔分等级 prefab**：每塔 3 个 `Tower_<Type>0|1|2`，放 `Assets/Prefabs/Tower/<Type>/`（目录 `Normal`/`Power`/`Retard`）；`TowerInfo.xlsx` 的 `resName` **逐级**指向它们；`BaseTower` 升级换实例并逐级预载；`TowerPrefabConverter.TowerResNames`（9 项）与配置 resName 必须逐行一致。
  ⚠️ 新增/替换塔美术要**四层同步**：配置 resName → `ResTable` → 代码兜底/预载 → prefab+meta(AB 名)。Pierce(4)/Laser(5) 暂无独立美术，resName 占位指向 `Tower_Normal0`。

## 本地数据持久化（M4 架构，细节见 `Docs/LocalPersistence_SQLite_Design.md`）

- 目录 `Assets/Scripts/Data/Persistence/`（12 文件：抽象 / SQLite / 加密 / 回退组装）。**调用只走 `SaveManager`**，零散数据用 `SetUserValue`/`TryGetUserValue`/`DeleteUserValue`；**禁止**直接写 SQL 或用 `IDatabase`；**禁止**新增 `PlayerPrefs`（例外：`KeyProvider` 密钥分片、`Assets/Reporter/` 第三方）。
- **P/Invoke 直连原生库**（不引 Mono.Data.Sqlite / sqlite-net），库名在 `SqliteNative.Library`（iOS→`__Internal` / Android→`sqlite3` / Windows→`winsqlite3`）。⚠️ 绑串必须 `SQLITE_TRANSIENT`；读 text 用 `sqlite3_column_bytes` + 显式长度按 UTF-8 解码；长连接 + `FULLMUTEX` + 托管锁。
- ⚠️ **Android 必须自带 `libsqlite3.so`（★）**：系统 `/system/lib64/` 那个是**平台私有库**，targetSdk ≥ 24 时 namespace 拒绝 `dlopen`（是**加载失败**，不是版本旧）。产物 `Assets/Plugins/Android/libs/{arm64-v8a,armeabi-v7a}/`，重建 `bash Tools/build_android_sqlite.sh`；`.meta` 必须手写（ABI 与 `CPU` 一致，guid 已固定），ARMv7 必须 **softfp**，由 `check_native_symbols.py` 核对。
- **加密**：AES-256-CBC + HMAC-SHA256（Encrypt-then-MAC），前缀 `ft1:`，存 TEXT 列，`Decrypt` 对无前缀输入原样返回（兼容旧明文）；密钥无硬编码，拆两半存 `ft_keystore.bin` + PlayerPrefs。**7 张表**（单行表 `CHECK (id = 1)`）；**敏感列密文是 TEXT → 不能参与 SQL 排序/聚合**，总星数在 C# 累加。
- ⚠️ **改表结构必须三步**：①`SaveSchema.CreateStatements` 加语句 ②`CurrentVersion` +1 ③`RunMigrations` 补 `ALTER TABLE`；且 `JsonSaveStorage` 同步实现新方法。降级是刻意设计：密钥不可用→明文；SQLite 打不开→`JsonSaveStorage`。

## 关卡生命周期（★ 切关残留，改任何"建东西"的模块先读）

- **唯一拆卸入口 `GameFlowManager.TeardownLevel()`**，顺序固定四段：①玩家操作态（放置预览/选中高亮/射程圈）→②战斗实体（怪→弹→塔→统计）→③**场景视觉残留**（棋盘格子/路径箭头/飘字/激光束）→④界面。①必须在②之前：①要访问塔与格子，②清完再收 = 操作已销毁对象。
- ⚠️ **根因模式（已修，新增代码要防）**：`BoardRoot / PathRoot / TowerRoot / EnemyRoot / BulletRoot` 都是**场景常驻**节点，不随关卡切换销毁。任何往它们下 `new GameObject` 的模块，**必须自己提供清空方法并在 TeardownLevel 登记**。历史坑：`BoardView.Build` 只建不清 → "通关后两张地图叠一起"；`BoardView.Clear()` 只销毁 `_views` 记录的自有格子。
- ⚠️ **可复用界面会"状态残留"**：`UIManager.Open` 对已存在实例直接返回原对象 → **HudView 必须在 TeardownLevel 里 Close**。**清除实体必须走"归还对象池"**：`EnemyManager.ClearAll` 走 `RecycleEnemy`（注销 + `pool.Release`），**不能直接 `e.OnRecycle()`**；已 `IsFullyRecycled` 的不能重复归还。
- ⚠️ **`RecycleBullet` 绝不能补 `CombatSystem.UnregisterBullet`**：子弹**创建时注册一次**（`RegisterBullet` 只在 `CreateBullet`），`_bullets` 是"池内所有实例"的稳定注册表；摘掉后池化复用的子弹永远不再被 tick。
- `TipsView` **不**随切关关闭（全局 toast）；`PauseView` 靠 `OnDisable` 恢复 timeScale；`LevelClearView` 由 `OnGameOver` 打开，也在 TeardownLevel 里关。
