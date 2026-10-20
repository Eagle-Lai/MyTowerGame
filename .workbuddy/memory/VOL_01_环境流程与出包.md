# VOL_01 环境 / 流程 / 出包

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：双版本路径、命名规范、生成/挂载前置条件、编辑器脚本约定、提交规范、git 代理、APK 出包铁律、真机 adb。

## 双版本（按路径区分，严禁跨版）
- 家用版 [家用D] = `D:\FreedomTower_1`；公司版 [公司E] = `E:\MyTowerGame`。
- 每次记录必须标注属于哪个版本；严禁把一版的结论套到另一版。
- 两版通过 GitHub `Eagle-Lai/MyTowerGame`(main) 同步。
- Unity `2022.3.62f3c1` + Built-in Render Pipeline（真实路径 `C:\Program Files\Unity 2022.3.62f3c1\`，Unity Hub 目录下那个是空壳）。
- ★`HotUpdateServer/`、`Bundles/` 被 git 忽略 → **各机拉完必须重打 + 重部署**，否则会出现"新 dll + 旧 AB"混搭的诡异现象（功能看着没生效）。
- `Builds/` 只放行 `Builds/Android/freedomtower.apk`，其余忽略。规则见 `Docs/提交与工作记录规范.md` §3。

## 铁律（流程/规范）
- 命名规范：`自由人塔防` = 文档用名｜`FREEDOM TOWER` = 副标题｜`freedomtower` = 包名｜`FreeTower` = YooAsset 包裹名（★改则热更全部失效）｜`FTProject` = 命名空间。菜单里不要改"塔防"字样；文档里不写盘符。
- 跑生成/挂载类菜单前必须满足 `isCompiling == false && isPlaying == false`；改过 `Assets/Editor/*.cs` 要等编译完再跑菜单；动手前先确认 MCP 连的是本工程（不是 CatchFish）。
- 编辑器脚本不弹 `DisplayDialog`（走 `Debug.Log`）；危险操作拆成两档菜单；DOTweenPro 里那 2 处弹窗保持不变。
- ★提交规范：**全部一起提交**（一笔含未跟踪文件/缓存/产物，不拆不挑）；**先写完记录再提交**（当天 `memory/YYYY-MM-DD.md` + `MEMORY.md` 同一笔）；提交后不再写盘。
  - ※2026-10-19 拆分后补充：`MEMORY.md` 已拆成索引 + 7 个 `VOL_*.md` 分册，"先写完记录"的同一笔里要含当天日档 + `MEMORY.md` + 被改动的相关分册。
- ★可能有并行 Unity/MCP/会话在改资产 → 提交前确认 mtime 静止数分钟；openpyxl 打开 xlsx 会独占锁 → Unity Digest 报 Sharing violation；陈旧 `.git/index.lock`（0 字节且无进程持有）直接删。
- git 走 env 代理（Clash 混合端口 **7897** / socks 7898 亦可 7892）。★本环境默认注入 `http_proxy=127.0.0.1:60044`（服务侧代理，对 github.com 返回 `502 CONNECT tunnel failed`）→ **git 命令必须显式覆盖成 7897**：
  `http_proxy=http://127.0.0.1:7897 https_proxy=http://127.0.0.1:7897 git -c http.version=HTTP/2 pull`
- ★>10MB 推送/拉取必加 `-c http.version=HTTP/2`（HTTP/1.1 过代理必 408，且尾部会混"Everything up-to-date"的假象，别被骗）。
- ★`cannot lock ref` = 并行推送竞态 → 先 `git ls-remote` 确认远端 sha，**不要装 git-lfs**。
- 凭据弹窗 → 在 `~/.gitconfig` 的 `[credential]` 段插一行空 `helper =` 后重试，并用 `ls-remote` 核对 sha。

## 出包铁律（2026-10-19 黑屏事故）
- ★★出 APK 前**必须核对 Build Settings 场景列表**：`Boot.unity` 启用 + `Main.unity` 禁用（main 只能从 AB 加载）。
  `733ba00`（金色换皮提交）曾把 EditorBuildSettings 改成只含 Main 且启用 → APK 直接从 Main 空壳场景启动
  （热更脚本打包时被剔除）→ 全脚本 missing、黑屏卡死、logcat 无任何 `[Boot]` 日志。
  识别特征：启动 1 秒内出现 `The referenced script (FTProject.*) is missing` 且完全无 [Boot] 日志 = 起始场景错了，不是热更链路问题。
  已恢复 `ProjectSettings/EditorBuildSettings.asset` 为 ee973da 版本（Boot enabled / Main disabled）。
- ※原同一节里的"热更部署铁律"（AB 构建后必须立刻 deploy）已移至 `VOL_02_热更与资源.md`，内容一字未改。

## 真机 [公司E]（MuMu）/ APK [家用D]
- adb 先 `connect 127.0.0.1:16384`；包名 `com.lzyfreedomtower.freedomtower`；★`input tap` 坐标按横屏逻辑 1600x900（截图 1080x600 ×1.481/1.5）；`pm clear` 参数需加引号。
- ★真机要热更的资源（场景/预制体/SO）必须 AB 打包：main 场景 + BootUI 三件套进 AB、`LocalizationSettings` 归 `FTProject.AOT`（维护菜单 5）。改 dll 后须 `pm clear`。
- APK：菜单 6/7，或
  `Unity.exe -batchmode -executeMethod FTProject.EditorTools.BuildApk.BuildNow -buildTarget Android -logFile Logs/batch_apk.log`（完建须手动杀进程）；状态 `Library/FTBuildApkStatus.txt`。
- 坑：Gradle 失败会弹模态框卡死／`TargetSdkVersion:0` 会选出坏包／路径大小写敏感。
