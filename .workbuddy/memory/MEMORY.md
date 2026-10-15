# FreedomTower 长期记忆（只留不变量；细节见 Docs/ 与 memory/ 日志）

## 双版本制度（开工先读）
- 家用D=`D:\FreedomTower_1`（工具链 `C:\Users\78296\`、`D:\Android\`）；公司E=`E:\MyTowerGame`（本机；Android 工具链不完整，补装模块只能走 Hub GUI）。
- 开工第一步识别版本（看工作区路径）；记录标 [家用D]/[公司E]；环境严禁跨版套用。两版经 GitHub `Eagle-Lai/MyTowerGame` 同步（.workbuddy/ 随 git）。
- ★`HotUpdateServer/`、`Bundles/`、`Builds/`(.apk) 均被 git 忽略 → **拉完代码必须各机重打 AB+重部署**，否则"新 dll + 旧 AB"混搭（塔型收敛等变更不随 git 到另一版）。

## 铁律
- 名写法：自由人塔防=文档｜FREEDOM TOWER=副标题｜freedomtower=包名｜FreeTower=YooAsset包裹名(改了热更失效)｜FTProject=命名空间；菜单 `Tools/塔防` 勿改"塔防"；文档不写盘符。
- 动手前核 MCP 连的是本工程（查 Application.dataPath）；跑生成/挂载菜单前 `isCompiling==false && !isPlaying`；改 `Assets/Editor/*.cs` 后必须等编译完成再跑（否则静默用旧程序集，最坑）。
- 编辑器脚本不弹 DisplayDialog（走 Debug.Log；危险操作拆两档菜单；DOTweenPro 2 处弹窗不动）。
- git：① push 弹 credential helper → 用户级 ~/.gitconfig `[credential]` 插空 `helper =`；失败重试一次，`ls-remote` 核 sha。② 本机 GitHub 访问只有 env 变量代理稳定：`http_proxy=http://127.0.0.1:7897 https_proxy=…`（Clash Verge mixed 口；直连与 `-c http.proxy` 均不可靠）。③ 判断家用有无新提交看 `git log --format='%h %an %ci'`——Eagle-Lai author + 清晨日期=家用提交，可能早已 merge 进本地，别只看未合并列表。
- Unity 2022.3.62f3c1 + Built-in RP；screenshot 偶发丢 Overlay 层。

## 程序集/HybridCLR（细节 Docs/HybridCLR_Integration.md）
- 12 程序集；热更6=Assembly-CSharp/LubanLib/Gen/SuperScrollView/Reporter/Runtime。Assembly-CSharp=兜底集（增删 Assets/ 根脚本须重跑 Generate▸All+拷贝）。★Assets/Scripts 全归 **FTProject.Runtime** → 验证 dll 新代码搜 `HotUpdateDlls/Android/FTProject.Runtime.dll`；Assembly-CSharp.dll 恒 5KB 空壳、mtime 旧属正常。
- ★ AOT 不得引用热更类型；Boot.unity 先 Assembly.Load 再进 main（BuildSettings Boot0/main1）。入口契约 IHotUpdateEntry←HotUpdateEntry。
- dll 名单两处同步：HotUpdateAssembler↔HybridCLRSettings.asset；AOTMetaAssemblies 6 项三处同步；包版本=libil2cpp-version.txt(8.14.1)。
- ★ YooAsset 初始化三步：InitializePackageAsync→RequestPackageVersion→LoadPackageManifestAsync 才 SetActiveManifest；漏步报 manifest not found。EnableAddressable=false；同版本二次构建 ErrorCode115。

## 热更/资源
- dll=独立HTTP(HotUpdateDllDownloader)（{ServerUrl}/Android/HybridCLR/）；AB=YooAsset HostPlayMode。
- ★地址=**UDP 自动发现**：唯一源 `Assets/AOTAssembly/BootServerSelection.cs`；hotupdate_server.py 每秒广播 `FTHOTUPD1|port=8000`(UDP 28000)，真机监听窗口 **1.5s**、HTTP 探测超时 **1s**，并行竞争，取来源 IP→md5.txt 探测确认；常量候选只剩模拟器 10.0.2.2；server.txt 覆盖最优先（存在则跳过 UDP）。GetServerUrl 优先级 server.txt>SelectedUrl>常量。**全在 AOT 侧→改这些必须出 APK**。
- ★★ 可达性闸门：Boot 探测段结束**无条件**调 `MarkReachabilityChecked()`；`RemoteHotUpdateAllowed`（未探测=true｜探测过且无胜出=false）经 `ResServerConfig.IsRemoteHotUpdateAllowed()` 成 **dll 与 AB 共用闸门**。不可达时 AB 必走 **OfflinePlayMode**——绝不能进 HostPlayMode（版本请求 60s 硬失败无回退＝"一直等待进不去游戏"根因）+ CheckUpdateCo 开头短路 onDone(false)。EnableHotUpdate 是 const，直接比较会 CS0162，需落局部变量。实测：无服务器 1.5s 决策→3s 进主菜单；有服务器 0.02s→原链路不变。
- ★★ AB 三铁律：①**FT_HOTUPDATE 宏三平台组必开**（不开=静默离线模式）；②HostPlayMode 请求**全平铺在 ServerUrl 根**：/FreeTower.version(内容=版本号)/FreeTower_{ver}.hash/.bytes/{哈希}.bundle，部署跑 `.workbuddy/tools/deploy_free_tower_cdn.py`；③CheckUpdateCo 同版本也校验缺失并下载。★首启竞态：SFS 无法同步等远端下载，新 bundle 首启必失败、二启正常（工程级修复待做＝Boot 等检查完再放行 UI）。
- 首启释放 PrefetchStreamingAssetsToPersistent：存在即跳过（保热更成果）。dll md5 清单 `{平台}/HybridCLR/md5.txt`（菜单 HybridCLR/4）须与 dll 同传。
- YooAsset 3.0.x 默认值全关→BuildSandboxParameters 已显式开 High/1MB/30s/并发8；事件 API=DownloadProgressChanged。

## 配置/多语言/UI
- Luban：改 xlsx 必重导（菜单3，DOTNET_ROLL_FORWARD=LatestMajor）；新表登记 __tables__.xlsx；字段从B列起；ResTable.cs=唯一寻址源。★直接跑 gen_code_json.bat 会删 Assets/Gen/FTProject.Gen.asmdef→级联 CS0246；编辑器外导出后必核对 asmdef。
- 多语言：主键=英文原文；表权威源 `.workbuddy/tools/gen_localization_table.py` ROWS→xlsx；向已有表幂等追加用 append_localization_rows_*.py（跑完必走菜单3重导）；TextLocalizer key 留空自动取（Text 用 _originalText）；回退 当前→英文→原文；菜单308挂/309清理。
- UI 生成器 UIPrefabBuilder（改文案=改它+重编译+重生成）；TMP；SiYuanSongTi SDF 动态+多图集。

## SuperScrollView（★最坑）
- InitListView 一次性快照 viewport→绝不能 OnEnable 初始化；SelectView.Build 挂 _pendingInit，首帧 LateUpdate 才 DoInitListView。
- 吸附硬约束：Viewport 宽=卡片宽(1250×550)；pivot.x=0、anchoredPosition.x=-625。三处同步：UIPrefabBuilder↔SelectView(1250/56)↔登记名 SelectLevelItem。别用 mOnSnapItemFinished→轮询中心距4px。

## 生命周期/存档/音频
- LevelClearView 胜败共用 OnGameOver()（星级先读后写）；唯一拆卸 TeardownLevel()（操作态→战斗实体→场景残留→界面，HudView 其中 Close）。
- 存档只走 SaveManager（禁 SQL/PlayerPrefs，例外 KeyProvider）；改表三步 CreateStatements→CurrentVersion+1→RunMigrations。
- 音频=丢文件+gen_audio_catalog.py；BGM 2源+AudioFadeDriver；倍速唯一源 Core/GameClock.cs（timeScale 只 0/1）。

## Unity MCP（两版配置不同，严禁混用）
- [公司E] 官方包 com.coplaydev.unity-mcp v10.3.0，HTTP 127.0.0.1:8082/mcp；mcp.json 条目 UnityMCP-MyTowerGame；调用前核 dataPath；CatchFish=自研 ws8080 桥勿混用。
- [家用D] stdio uvx mcpforunityserver 3.4.8；连接器在 Unity 未启动时拉起会卡死→自起一次性 stdio 实例或 mcp_unity.py（支持 UNITY_MCP_URL）；桥端口 6401→6400 回退，真相源 `~/.unity-mcp/unity-mcp-status-*.json`。
- 兜底 `.workbuddy/tools/mcp_unity.py`（call execute_code 自动同会话 activate scripting_ext）。★长调用（GenerateAll/BuildNow）客户端必超时但 Unity 继续执行——靠产物时间戳/状态文件判定，勿重发。
- 无 MCP 时：`ReporterHotfixBuild.Start/StartDllOnly`（状态 Library/FTReporterBuildStatus.txt）；编辑器开着用菜单 Tools/塔防/9 与 9a；batchmode 与编辑器互斥；★启动必须用任务机制（shell & 会被收割）。GUI 场景备用 FT_AutoBuildTrigger（写 Library/FT_AUTOBUILD.trigger=full/dll/uimainmenu/feature；feature=一键流水线，状态 Library/FTFeatureBuildStatus.txt）。

## MuMu 真机调试 [公司E]
- adb 优先 SDK 版 adb.exe（比内置稳）；每条命令开头先 `connect 127.0.0.1:16384` 自愈；包 com.lzyfreedomtower.freedomtower；`adb root` 可用。★`input tap` 坐标=横屏逻辑 1600x900（截图 1080x600 按 ×1.481/×1.5 换算）；`pm clear` 需引号形式。
- ★ 真机上挂热更脚本的资源（场景/预制体/SO）**必须 AB 打包**（Resources/BuildSettings 必 missing）：main 场景+BootUI 三件套进 AB、LocalizationSettings 移 FTProject.AOT；维护菜单 Tools/塔防/YooAsset 接入/5（幂等）。Generate/All 的 dll 可能落后一拍，重跑菜单 7；改 dll 后模拟器须 pm clear。

## 工具/其他
- ★缺失脚本排查 `scan_missing_script_refs.py`（须收集 Assets+Packages+Library/PackageCache 的 .cs.meta）；Compat 占位脚本修复素材包 29 怪物 controller 的失效 StateMachineBehaviour。
- 建造交互 v3：快速点按=放置态；长按0.25s/位移30px=拖拽建造（松手校验、_suppressTowerClick 防误切）；HUD 右上 Btn_Pause/Btn_Intro→PauseView/GameIntroView。日志前缀 [Place]/[HUD]/[TowerInfoView]/[Audit]。
- 地图链路：棋盘→levelmap_export.json→LevelMap.xlsx→tblevelmap.json→SceneInfo.xlsx；静态校验9个（.workbuddy/tools）改完全跑。
- ★塔型三类：Normal1(对空)/Aoe2(仅地面)/Slow3光环(对空)；能否对空唯一判定=塔表 canAttackAir；Pierce4/Laser5 已删（枚举不回收），旧档 type=4/5 恢复跳过。
- 热更服务器：`.workbuddy/tools/hotupdate_server.py` 一键常驻（HTTP 8000+UDP 广播）；启停用同目录 .bat（★必须 CRLF）；根=平铺 AB 部署区（Android/HybridCLR、Android/FreeTower 两 junction）；自检 `curl --noproxy "*"`（TUN 代理劫持）。★本机派生进程无法常驻（会话后台任务/Start-Process 均被回收）→ 服务器须用户自己终端跑 .bat。★并行助手会话可能"保活"服务器——停服验证前先叫停相关会话。
