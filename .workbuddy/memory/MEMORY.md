# FreedomTower 长期记忆（只留不变量；细节见 Docs/ 与 memory/ 日志）

## 双版本制度（开工先读）
- 家用D=`D:\FreedomTower_1`；公司E=`E:\MyTowerGame`（Android 工具链不全，补装走 Hub GUI）。开工先看工作区路径定版本，记录标 [家用D]/[公司E]，环境严禁跨版套用。两版经 `Eagle-Lai/MyTowerGame` 同步。
- ★`HotUpdateServer/`、`Bundles/`、`Builds/`(.apk) 被 git 忽略 → 拉完代码各机必须重打 AB+重部署，否则"新 dll + 旧 AB"混搭。

## 铁律
- 名写法：自由人塔防=文档｜FREEDOM TOWER=副标题｜freedomtower=包名｜FreeTower=YooAsset包裹名(改了热更失效)｜FTProject=命名空间；菜单勿改"塔防"；文档不写盘符。
- 跑生成/挂载菜单前 `isCompiling==false && !isPlaying`；改 `Assets/Editor/*.cs` 后必须等编译完成再跑（否则静默用旧程序集，最坑）。所有生成/挂载菜单前核 MCP 连的是本工程（Application.dataPath）。
- 编辑器脚本不弹 DisplayDialog（走 Debug.Log；危险操作拆两档菜单；DOTweenPro 2 处弹窗不动）。
- ★提交约定（用户 2026-10-16 明确要求）：**一律全部一起提交**——每次一笔提交、包含工作区全部改动（含未跟踪新文件/缓存/产物），不拆多笔、不挑拣、不自作主张排除。
- git：① push 弹 credential helper → 用户级 `~/.gitconfig` `[credential]` 插空 `helper =`；失败重试一次，`ls-remote` 核 sha。② 本机 GitHub 只有 env 变量代理稳定：`http_proxy=http://127.0.0.1:7897 https_proxy=…`。③ 判断家用有无新提交看 `git log --format='%h %an %ci'`——Eagle-Lai + 清晨日期=家用提交，可能早已 merge 进本地。
- Unity 2022.3.62f3c1 + Built-in RP；screenshot 偶发丢 Overlay 层。

## 程序集/HybridCLR（细节 Docs/HybridCLR_Integration.md）
- 12 程序集；热更6=Assembly-CSharp/LubanLib/Gen/SuperScrollView/Reporter/Runtime。Assembly-CSharp=兜底集（增删 Assets/ 根脚本须重跑 Generate▸All+拷贝）。★Assets/Scripts 全归 **FTProject.Runtime** → 验证新代码搜 `HotUpdateDlls/Android/FTProject.Runtime.dll`；Assembly-CSharp.dll 恒 5KB 空壳。
- ★AOT 不得引用热更类型；Boot.unity 先 Assembly.Load 再进 main（Boot0/main1）。入口契约 IHotUpdateEntry←HotUpdateEntry。
- dll 名单两处同步 HotUpdateAssembler↔HybridCLRSettings.asset；AOTMetaAssemblies 6 项三处同步；包版本=libil2cpp-version.txt(8.14.1)。
- ★YooAsset 初始化三步 InitializePackageAsync→RequestPackageVersion→LoadPackageManifestAsync 才 SetActiveManifest；EnableAddressable=false；同版本二次构建 ErrorCode115。

## 热更/资源
- dll=独立HTTP(HotUpdateDllDownloader)（{ServerUrl}/Android/HybridCLR/）；AB=YooAsset HostPlayMode。
- ★地址=**UDP 自动发现**，唯一源 `Assets/AOTAssembly/BootServerSelection.cs`：hotupdate_server.py 每秒广播 `FTHOTUPD1|port=8000`(UDP 28000)，真机监听 **1.5s**、HTTP 探测 **1s**，取来源 IP→md5.txt 确认；常量候选只剩模拟器 10.0.2.2；server.txt 最优先（存在则跳过 UDP）。GetServerUrl：server.txt>SelectedUrl>常量。**全在 AOT 侧→改这些必须出 APK**。
- ★★可达性闸门：Boot 探测结束**无条件**调 `MarkReachabilityChecked()`；`RemoteHotUpdateAllowed`（未探测=true｜探测过无胜出=false）经 `ResServerConfig.IsRemoteHotUpdateAllowed()` 成 **dll 与 AB 共用闸门**。不可达时 AB 必走 **OfflinePlayMode**（进 HostPlayMode 会 60s 版本请求硬失败无回退＝"一直等待进不去游戏"根因）+ CheckUpdateCo 开头短路 onDone(false)。EnableHotUpdate 是 const，直接比较 CS0162，须落局部变量。
- ★★AB 三铁律：①**FT_HOTUPDATE 宏三平台组必开**（不开=静默离线）；②HostPlayMode 请求**全平铺在 ServerUrl 根**：/FreeTower.version(内容=版本号)/FreeTower_{ver}.hash/.bytes/{哈希}.bundle，部署跑 `.workbuddy/tools/deploy_free_tower_cdn.py`；③CheckUpdateCo 同版本也校验缺失并下载。★首启竞态：SFS 无法同步等远端下载，新 bundle 首启必失败、二启正常（待修复＝Boot 等检查完再放行 UI）。
- 首启释放 PrefetchStreamingAssetsToPersistent，存在即跳过。dll md5 清单 `{平台}/HybridCLR/md5.txt`（菜单 HybridCLR/4）须与 dll 同传。BuildSandboxParameters 已开 High/1MB/30s/并发8；事件 API=DownloadProgressChanged。
- 热更服务器 `.workbuddy/tools/hotupdate_server.py` 常驻（HTTP 8000 静态 + UDP 28000 广播；--self-test 自收验证）；根=**平铺 AB 部署区**，Android/{HybridCLR,FreeTower} 两 junction；git 忽略，两版各自建。防火墙入站规则 **FT HotUpdate 8000** 已建。发版=构建后跑 deploy_free_tower_cdn.py；启停用同目录 .bat（★必须 CRLF）。★坑：FlyingBird TUN 劫持 curl(502)→自检必须 `curl --noproxy "*"`；偶发 bind 10013 重试即好；★本机派生进程无法常驻（后台任务/Start-Process 均被回收）→须用户终端跑 .bat；并行会话可能"保活"服务器，停服前先叫停对方。

## 配置/多语言/UI
- Luban：改 xlsx 必重导（菜单3，DOTNET_ROLL_FORWARD=LatestMajor）；新表登记 __tables__.xlsx；字段从B列起；ResTable.cs=唯一寻址源。★直接跑 gen_code_json.bat 会删 Assets/Gen/FTProject.Gen.asmdef→级联 CS0246。
- 多语言：主键=英文原文；权威源 `.workbuddy/tools/gen_localization_table.py` ROWS→xlsx；幂等追加用 append_localization_rows_*.py（跑完必走菜单3）；TextLocalizer key 留空自动取（Text 用 _originalText）；回退 当前→英文→原文；菜单308挂/309清理。
- UI 生成器 UIPrefabBuilder（改文案/布局=改它+重编译+重生成）；TMP；SiYuanSongTi SDF 动态+多图集。
- ★塔图标 UI_TowerIcon_{Normal,Power,Retard}=**正式美术 96×96 透明底**，属 AB 包 ui_hud；`UISkinArtGenerator.WriteIcon` 已加闸：**按名单 `ManualArtIconNames` 判**（不能用尺寸判——美术就是 96，与占位图同尺寸会失效）→Skip 不覆盖（改图别跑皮肤菜单，跑 `.workbuddy/tools/tower_icon_bg_remove.py`）。换图后真机需重建 AB。
- ★★用 MCP `execute_code` 验证 UI 时**绝不要 instantiate 预制体资产的子物体**：TMP 会在编辑模式 OnEnable 把升级字段（`m_TextStyleHashCode`/`m_enableAutoSizing`）连同布局结果**写回资产**（曾把 HudView 图标节点改成 88×8 并波及 5 个 prefab）。正确做法=**`new GameObject` 自搭 Canvas+Image**，只 `LoadAssetAtPath<Sprite>`。
- ★refresh/编译会触发 **AB 打标工具加载全部 ResTable 预制体** → 顺带改写若干 UI 预制体与大批 `.meta` 的 assetBundleName（曾写入 SelectLevelItem 宽 1250→1、IsActive 0→1）。**提交前用 `diff_ui_prefabs.py --base` 核对，`git checkout` 掉非本意改动。** 反向同步=prefab 手改回写生成器（见 Docs/UIPrefab_Sync_ChangeList.md）。
- ★★**全量重建三条副作用与顺序**：重建会 ①重排全部 fileID（语义等价）②**清空 `.meta` 的 assetBundleName** ③**抹掉 TextLocalizer**。故必须 **①重建 →②菜单308 挂 TextLocalizer →③菜单4 打 AB 标记**；颠倒则③白做。
- 比对"真实手改 vs 重序列化噪声"：`git show HEAD:<prefab> > .workbuddy/tmp/ui_base/` 导出基准（14 个）后跑 `.workbuddy/tools/diff_ui_prefabs.py --base`。
- UI 细节（已固化进生成器）：塔按钮 Image 96×96；`TipsView/TipBar/TipText`（TipText 四边拉伸，TipBar 居中）；`TowerCodexItem`/`SelectLevelItem` 根 active=false（LoopListView2 池化会强制激活）；TMP=8 处自动字号(18~72)+4 处居中（Gold/Hp/Star/Clear），`SellConfirmView/SellTitle` 不加；VolumeSlider 480×65。
- `ResTable`（`Assets/Scripts/Core/Res/ResTable.cs`）=寻址唯一源，界面登记在 `ResBundle.UiHud`；漏登记=真机打不开。残留：`MonsterCodexView` 登记了但 prefab 不存在→菜单4 恒报 `✘ 资源不存在`。

## SuperScrollView（★最坑）
- InitListView 一次性快照 viewport→绝不能 OnEnable 初始化；SelectView.Build 挂 _pendingInit，首帧 LateUpdate 才 DoInitListView。
- 吸附硬约束：Viewport 宽=卡片宽(**1150×550**)；pivot.x=0、anchoredPosition.x=**-575**。三处同步：UIPrefabBuilder `SelectItemW`↔SelectView `ItemWidth`(**1150**/56)↔登记名 SelectLevelItem。别用 mOnSnapItemFinished→轮询中心距4px。

## 生命周期/存档/音频
- LevelClearView 胜败共用 OnGameOver()（星级先读后写）；唯一拆卸 TeardownLevel()（操作态→战斗实体→场景残留→界面，HudView 其中 Close）。
- 存档只走 SaveManager（禁 SQL/PlayerPrefs，例外 KeyProvider）；改表三步 CreateStatements→CurrentVersion+1→RunMigrations。
- 音频=丢文件+gen_audio_catalog.py；BGM 2源+AudioFadeDriver；倍速唯一源 Core/GameClock.cs（timeScale 只 0/1）。

## 玩法/交互（当前形态）
- ★塔型三类 [2026-10-14 定案]：Normal1(飞+走)/Aoe2 火力=仅走/Slow3 光环(飞+走)；Pierce4/Laser5 已整体删除（枚举编号不回收）。对空唯一判定=塔表 canAttackAir（FindTarget 与 TickSlowAura 同一过滤）。旧档 type=4/5 恢复时跳过。目录 Power=Aoe、Retard=Slow。
- ★建造交互 v3：塔按钮手势两分——快速点按=经典放置态（BuildTowerRequestEvent）；长按0.25s/位移30px=**拖拽建造**（TowerDragBeginEvent→TowerPlacement._dragMode，ghost 跟手+悬停高亮，**松手**校验，拖回按钮/棋盘外=静默取消），触发后一帧 `_suppressTowerClick` 吞 onClick 防误切。HUD 右上角 Btn_Pause（→PauseView timeScale=0）/Btn_Intro（→GameIntroView，含「回到选关」+自关）。拖拽 IsPointerOverUI 已做触摸感知（fingerId 逐一查）。
- 点塔交互：放置态点"已有塔格子"=退出放置并选中。日志前缀 [Place]/[HUD]/[TowerInfoView]/[Audit]（进关延时 1s 扫 missing 汇总一条）。
- 地图链路：棋盘→levelmap_export.json→LevelMap.xlsx→tblevelmap.json→SceneInfo.xlsx。静态校验9个（.workbuddy/tools）改完全跑。

## Unity MCP（两版配置不同，严禁混用）
- [公司E] 官方包 com.coplaydev.unity-mcp v10.3.0，HTTP 127.0.0.1:8082/mcp，条目 UnityMCP-MyTowerGame；CatchFish=自研 ws8080 桥勿混用。
- [家用D] stdio uvx mcpforunityserver 3.4.8；**连接器在 Unity 未启动时拉起会卡死"连接中"、会话内不恢复**→兜底=自起一次性 stdio 实例或 `.workbuddy/tools/mcp_unity.py`（支持 UNITY_MCP_URL）；桥端口 6401 被占回退 6400，**真相源=`~/.unity-mcp/unity-mcp-status-*.json`**；execute_code 须先 `manage_tools activate scripting_ext`（每次新连接都要重激活）。
- ★长调用（GenerateAll/BuildNow）客户端必超时但 Unity 继续执行——靠产物时间戳/状态文件判定，勿重发。
- 无 MCP 时 `ReporterHotfixBuild.Start/StartDllOnly`（状态 Library/FTReporterBuildStatus.txt）；编辑器开着用菜单 9/9a；batchmode 与编辑器互斥；★启动必须用任务机制（shell & 会被收割）。GUI 备用 FT_AutoBuildTrigger（写 Library/FT_AUTOBUILD.trigger=full/dll/uimainmenu/feature，状态 Library/FTFeatureBuildStatus.txt）。

## 真机调试 [公司E]（MuMu）
- adb 优先 SDK 版 adb.exe；每条命令开头先 `connect 127.0.0.1:16384` 自愈；包 com.lzyfreedomtower.freedomtower；`adb root` 可用。★`input tap` 坐标=横屏逻辑 1600x900（截图 1080x600 按 ×1.481/×1.5 换算）；`pm clear` 需引号形式。
- ★真机上挂热更脚本的资源（场景/预制体/SO）**必须 AB 打包**：main 场景+BootUI 三件套进 AB、LocalizationSettings 移 FTProject.AOT；维护菜单 Tools/塔防/YooAsset 接入/5（幂等）。Generate/All 的 dll 可能落后一拍，重跑菜单 7；改 dll 后模拟器须 pm clear。

## APK 构建 [家用D]
- GUI=菜单 6（纯 APK）/菜单 7（DLL▸AB▸APK 完整）；无编辑器时 batchmode：`Unity.exe -batchmode -executeMethod FTProject.EditorTools.BuildApk.BuildNow -buildTarget Android -logFile Logs/batch_apk.log`（后台任务机制起；完建后 executeMethod 不自动退出须手动杀 Unity）。**★编辑器真实路径=`C:\Program Files\Unity 2022.3.62f3c1\`（Hub 目录下是空壳）**；状态文件 Library/FTBuildApkStatus.txt。
- **三铁坑**：①GUI Gradle 失败必弹 ParseAndShowException 模态框卡死主线程（MCP 全堵）；②`AndroidTargetSdkVersion:0`=自动选最高已装平台——**坏平台包会骗过它**（曾选到坏 android-37.0 → "Failed to find Platform SDK"，删包回落 34）；③SBP/资产库对路径**大小写敏感**（改名须绕临时名两步且含 meta）。

## 工具/其他
- ★`scan_missing_script_refs.py` 扫 m_Script 失联 GUID：必须同时收集 Assets+Packages+Library/PackageCache 的 .cs.meta，否则 uGUI/TMP 包脚本全误报。29 个怪物 controller 的 2 个 never-existed StateMachineBehaviour 已用 Compat 占位脚本修复（手写 meta 恢复原 GUID）。
- 怪物素材=侧视拆件图集（每怪 1 张 PNG、全朝左）+ `_Common/Animations/<家族>` 一套无方向动画；左右朝向靠 `BaseEnemy.FaceMoveDirection` 翻转 localScale（纵向不翻转是设计）。`.anim` 只驱动骨骼 Transform、不含精灵引用曲线，表情走动画事件 `SetHead(int)`→MonsterAnimEventReceiver。`gen_monster_catalog.py` 生成 MonsterCatalog.cs。
- 云端资料库镜像 Docs/（md 用 space.importer、svg 用 drive/upload）。
