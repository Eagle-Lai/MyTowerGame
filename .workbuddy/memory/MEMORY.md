# FreedomTower 项目长期记忆

> 只记"踩坑就返工"的不变量；细节见 `Docs/` 与 `YYYY-MM-DD.md`。⚠️ 有注入上限，超了会被截断 —— **新增前先想能不能删**。

## 铁律

- **游戏名 = 《自由人塔防》**，英文名 **FREEDOM TOWER**（工程 `productName: freedomtower`、包名 `com.lzyfreedomtower.freedomtower`，**不填中文名**）。
  ⚠️ 文档/效果图里出现《坚守阵地》时，**先判断指谁**：指**原版 Fieldrunners** 的引用（"对标《坚守阵地》（Fieldrunners）"、代码注释"这是《坚守阵地》的核心机制"）**保留不动**；指本工程的才改。
- **当前工程根就是本工程根目录**（Unity 驱动）。⚠️ 历史文档/记忆里出现过的 `D:\FreedomTower`、`D:\FreedomTower_1` 均已失效，**不要再引用绝对路径**。
- ⚠️ **写交付文档一律不写盘符路径**：用"本工程 / 工程根目录"等相对表述；配置文件/脚本内的路径从脚本自身位置推导（`.workbuddy/tools/*.py` 已全部如此）。
- **Unity MCP 可用**（菜单/execute_code/read_console/screenshot）→ 编译与编辑器操作都走它，"建东西"的模块先实际跑一遍验证。
- ⚠️ **跑生成类菜单前必须确认 `isCompiling==false && isPlaying==false`**，否则用旧程序集静默生成旧结果；编辑器会自己重进播放态。
- ⚠️ `screenshot` 偶发丢 Overlay 层（重截即可）；单次调用延迟数秒~十几秒，抓不到 1.2s 瞬态。
- ⚠️ 改 `UIPrefabBuilder` 后比对 `ui_prefabs_preRebuild/*.prefab` 的 anchor/pivot/pos 查回归。
- `git push` 挂死唯一解法 `GIT_CONFIG_SYSTEM=/dev/null git push origin main`（"写系统配置根治"已证伪）。远端只有 GitHub `Eagle-Lai/MyTowerGame.git`。
  ⚠️ **但该 workaround 会禁用 system config 里的 credential helper** → `could not read Username`。**真正阻塞是 403**：本地存的是 `laizhangyin88-glitch` 的凭证，仓库属 `Eagle-Lai` → push 被拒。需先在凭据管理器换成有权限的账号。
- Unity 2022.3.62f3c1，**Built-in RP**（霓虹只能烘进贴图）。

## 配置 / 资源

- **Luban** 改 `Luban/Config/Datas/*.xlsx` 必重导（菜单`3.导出配置表`，需 `DOTNET_ROLL_FORWARD=LatestMajor`）；新表先登记 `__tables__.xlsx`。
- **`ResTable.cs` 唯一寻址源**。⚠️ `check_code.py` 只扫 `Get("字面量")` 不扫 `Configs.ConfigKeys` → 加表须手工同步。`ResLoader` 三套按宏切，**新依赖一律加宏**。
- ★ **YooAsset 初始化必须三步**：`InitializePackageAsync`（只建文件系统）→ `RequestPackageVersionAsync()` → `LoadPackageManifestAsync`（**最后才 `SetActiveManifest`**）。漏了症状极欺骗：日志一切正常，之后每次加载都报 `Active package manifest not found.`。收集器必须 `EnableAddressable=false`；同版本二次构建抛 `ErrorCode115`。
- 战斗无物理：`EnemyGrid` + `CombatSystem` 集中 tick。**塔无目标绝不开火**。

## 音频 / 倍速

- 音频 18 个在 `Assets/Audio/{SFX,BGM}/`。**加音频 = 丢文件 + 跑 `gen_audio_catalog.py`**；常量在 `Data/AudioName.cs`。
- BGM 用**固定 2 源 + `AudioFadeDriver`**（长音进音效池会被"顶掉最旧"误杀）。⚠️ **音量只由 `ApplyBgmVolume()` 写** = 基准×淡化系数×主音量×(静音?0:1)，驱动只改系数；用 `unscaledDeltaTime`。
- `UiClickSfx` 由 `UIManager.Open` 自动挂、每 0.4s 重扫 Button → 新界面不用写点击音。
- **倍速唯一源 `Core/GameClock.cs`**：`DeltaTime=dT×Speed` 按帧号惰性缓存（与执行顺序无关）；`timeScale` 只允许 0/1。改档走请求事件→GameFlowManager 四道校验→`GameSpeedChangedEvent`；`ResetGameSpeed()` 在 InitLevel/OnGameOver/QuitToSelect。**CombatSystem 改一行即覆盖怪/塔/弹**。

## UI / 字体

- **统一 TMP，禁新增 UGUI Text**。⚠️ `SiYuanSongTi SDF.asset` **必须"动态+多图集"**：单图集只装 ~119 字，关掉后新字（★☆×难度…）**渲染成空白且不报错**；判据 `TryAddCharacters("难★")`==false 即满。
- ⚠️ **塔按钮锚点必须 (0.5,0.5)**（`spec.Pos` 以画布中心为原点），写成左下锚点 → 整排塔按钮出屏、无法建塔。
- ⚠️ `SpeedButton/StartButton` 在塔栏**两侧**（SideBtnX=786,SideBtnY=77）；效果图的"底中"会挡住第 3/4 颗塔按钮。
- ⚠️ **节点名契约**：View 的 `Find("Panel/X")` 与生成器无映射层，写岔只静默打「缺少节点」→ 成对改 + `check_ui_contract.py`。

## 列表 / SuperScrollView

- `SelectView` = **整页全屏**横向画廊（Panel 铺满 1920×1080），条目资产 `Assets/Prefabs/UI/SelectLevelItem.prefab`（生成器产出，**不必登记 ResTable**，靠引用进包）。
- 交互约定：**居中的那一关才算"选中"**，点居中卡→同帧进关；点非居中卡→先动画滑到正中再进关；左右箭头只挪不进关；未解锁只提示。
- ⚠️ **横向吸附几何**：条目能居中程度 = (视口宽−条目宽)/2，且需 **步长 ≥ 视口宽** → 条目宽必须 ≡ 视口宽，否则首/末条永远偏心。
- ⚠️ 要"邻卡可见"就得**视口比可视区窄**：`RectMask2D` 放 List（1300），Viewport 收窄 900 且与之同心。
- ⚠️ **Viewport pivot.x 必须预置 0**（`AdjustPivot` 会强改），矩形一律用 `offsetMin/offsetMax` 描述；用居中点锚点会被平移。
- ⚠️ **别用 `mOnSnapItemFinished` 判断"滑到位"**（它传的 `mCurSnapNearestItemIndex` 只在容器移动帧才重算，会提前触发）。
  改为**每帧轮询目标条目到视口中心的距离**；判定阈值 4px（插件自己的 0.01 要 2 秒收尾），兜底 2.5s。
- ⚠️ `InitListView` 只可调一次（界面复用 → `_listInited` 守）；条目池化复用 → `onClick` **只在 `IsInitHandlerCalled` 首次挂**，回调读 `UserIntData1/2`。
- 视觉层（缩放/淡化）挂卡片的 `Body` 子节点，**不能缩条目根节点**（pivot 固定 (0,0.5)，缩它会偏心）。首次定位延后到第一帧 `LateUpdate`。
- 箭头等新字形用 ASCII（`<` `>`）：中文 SDF 缺字形只渲染空白不报错；首次渲染会把字形烘进 `SiYuanSongTi SDF.asset`。



## 结算 / 生命周期

- `LevelClearView` 胜败共用（`LevelClearInfo.victory`），在 `OnGameOver()` 打开（别监听 `LevelClearEvent`）。⚠️ **星级先读后写**（RecordClear 只升不降）。下一关=**大于本关的最小 id**。F2=强制获胜。
- **唯一拆卸 `TeardownLevel()`** 四段：①操作态→②战斗实体→③场景残留→④界面；①在②前。
- ⚠️ `BoardRoot/PathRoot/TowerRoot/EnemyRoot/BulletRoot` 场景常驻，往其下 new 的模块**必须自带清空并登记**。⚠️ HudView 必须在 TeardownLevel Close。⚠️ **`RecycleBullet` 绝不能补 `UnregisterBullet`**。`TipsView` 不随切关关闭。

## 存档

- `Data/Persistence/`：**只走 `SaveManager`**；**禁**直接 SQL/`IDatabase`、**禁**新增 `PlayerPrefs`（例外 KeyProvider）。见 `Docs/LocalPersistence_SQLite_Design.md`。
- **Android 必须自带 `libsqlite3.so`**（系统的是平台私有库，targetSdk≥24 拒 dlopen），ARMv7 必须 softfp。
- **改表三步**：`SaveSchema.CreateStatements` → `CurrentVersion`+1 → `RunMigrations` 补 ALTER；**密文 TEXT 不能参与 SQL 排序/聚合**。

## 工具 / 命名

- 地图编辑器唯一通路：棋盘→`levelmap_export.json`→LevelMap.xlsx→tblevelmap.json；⚠️ 只加棋盘不加 `SceneInfo.xlsx` 进不去。
- 静态校验 9 个（`.workbuddy/tools/`）改动后全跑；⚠️ `check_arity` 的 `_CHANGED` 不许留已删文件；⚠️ shell 跑 Python 别用 `\s`/`\b`/`\w`。**沙箱内不能编译**。
- `TowerType` Normal1/Aoe2/Slow3/Pierce4/Laser5；目录里 **Power**=Aoe、**Retard**=Slow。换塔美术要**四层同步** resName→ResTable→代码预载→prefab+meta；Pierce/Laser 占位 `Tower_Normal0`。
