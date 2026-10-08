# 《坚守阵地》程序案（v3.0）

> 配套文档：`Docs/GameDesign_坚守阵地_v3.md`（策划案，数值与规则的唯一来源）
> 工程：`G:\MyTowerGame`　Unity 2022.3.62f3c1　|　目标平台：Android（minSdk 22 / IL2CPP / arm64-v8a + armeabi-v7a）
> 基线：2026-10-08 工程实测（89 运行时脚本 / 21 编辑器工具 / 23 Luban 生成文件，namespace 分别为 `FTProject` / `FTProject.EditorTools` / `cfg`）
> 读者：按本文档分步执行的 AI 或开发。每阶段含**执行步骤 + 验收标准**，严格按 P1→P5 顺序执行，P6 依赖外部资源不阻塞。

---

## 1. 场景划分

**单场景方案**：全游戏仅 `Assets/Scenes/Main.unity`（已登记 EditorBuildSettings），界面切换全部走 UIManager 面板栈，不走场景加载。理由：塔防战斗与 UI 强耦合、单场景免去跨场景对象重建与 AB 重复加载，启动后零场景切换开销。

Main.unity 实测层级（由 `Editor/SceneMainBuilder.cs` 自动搭建连线，勿手工改）：

```
Launcher                 全局启动器：注册管理器 → 初始化资源加载器 → 加载 9 张配置表 → 广播 ConfigLoadedEvent
GameSceneLauncher        场景组合根：Awake 集中校验引用并注入 GameFlowManager
GameFlow                 GameFlowManager：关卡流程状态机（策划案 §7.4）
Camera                   2D 正交相机 + CameraController（平移/缩放/自适应）
EventSystem              UGUI 输入
Background               背景 + BackgroundParallax（视差）
BattleRoot
  ├─ BoardRoot           棋盘格子（BoardView 逐格 SpriteRenderer）
  ├─ PathRoot            路径箭头（PathArrowView）
  ├─ TowerRoot           塔实例父节点
  ├─ EnemyRoot           怪物实例父节点
  └─ BulletRoot          子弹实例父节点
UICanvas                 UIManager 三层
  ├─ BgPanel             底层面板
  ├─ NormalPanel         主面板层（SelectView/HudView/PauseView/SettingView/LevelClearView/TowerInfoView）
  └─ TipsPanel           顶层提示（TipsView + 伤害飘字）
```

世界层战斗画面与 UI 布局见效果图：`Docs/ui_mockups/09_WorldLayer_Combat.svg`、`Docs/ui_mockups/02_HudView_Normal.svg`（UI 逐界面规格见策划案 §6）。

---

## 2. 目录结构（实测终态）

```
G:\MyTowerGame\
├── Assets/
│   ├── Scenes/Main.unity            唯一主场景
│   ├── Scripts/                     运行时 89 个 .cs（见 §3）
│   ├── Editor/                      编辑器工具 21 个（18 + YooAsset/3）
│   ├── Gen/                         Luban 生成代码 23 个（namespace cfg，勿手改）
│   ├── LubanLib/                    Bright.Serialization + SimpleJSON（第三方）
│   ├── ConfigJson/                  Luban 导出产物 9 个 json（编辑器直读 + 进 config 包）
│   ├── Prefabs/
│   │   ├── Tower/{Normal,Power,Retard}/   3 塔型 × 3 级 = 9 个（Pierce/Laser 暂复用 Normal，P6 换皮）
│   │   ├── Enemy/                   119 个怪物 prefab（16 族系）
│   │   ├── Bullet/Bullet_Normal.prefab
│   │   └── UI/                      HudView/SelectView/PauseView/SettingView/LevelClearView/TipsView/TowerInfoView
│   ├── _UIAssets/                   美术：Monsters(16族系+_Common) / Tower / Backgrounds
│   ├── Art/Generated/               程序生成占位图 9 张（PlaceholderArtGenerator.cs 产物）
│   ├── Font/                        思源宋体 ttf + TMP SDF + Outline 材质
│   ├── Audio/                       音频目录（当前仅 README，P3 阶段填入）
│   ├── StreamingAssets/             AB 产物输出（P4 重打）
│   ├── SuperScrollView/ TextMesh Pro/ Demigiant(DOTween) / Reporter/ Plugins/   第三方
│   └── Plugins/Android/libs/        libsqlite3.so（arm64-v8a + armeabi-v7a）
├── Luban/                           配置工具链
│   ├── Config/Datas/*.xlsx          策划源表 13 张（9 有效 + 定义表）
│   ├── Tools/Luban.ClientServer/    Luban CLI
│   └── gen_code_json.bat            一键导出（C#→Assets/Gen，JSON→Assets/ConfigJson）
├── Docs/                            策划案 v3 + 程序案 v3 + 历史文档
│   └── ui_mockups/                  UI 正式版效果图 14 张 SVG·深色科幻（非 Assets，Unity 不导入）
└── ProjectSettings/ Packages/       工程设置与包清单
```

**P1 阶段清理项**（见 §6-P1）：死代码 `Scripts/Core/UIEventListenerManager.cs`、`Scripts/Core/EventManager.cs`；根部游离 `Assets/PopMain.cs`、`Assets/TestTileMap.cs`（运行时程序集 using UnityEditor，真机构建必炸）；根目录 `tips.zip`（38MB）、`Csharp_CustomTemplate_AsyncLoad/`、`GenerateDatas/`、`Luban/Config/Gen`（Luban 示例遗留，不参与编译）；StreamingAssets 下 3 个孤儿 .meta。

---

## 3. 核心脚本职责表

### 3.1 运行时模块（Assets/Scripts，89 个）

| 模块 | 文件（个数） | 职责 |
|---|---|---|
| 启动 | `Launcher.cs`、`GameSceneLauncher.cs` | 管理器注册/配置加载编排；场景引用校验与注入 |
| Core/Res（11） | `IResLoader/ResLoader/EditorResLoader/BundleResLoader/YooAssetResLoader/ResTable/ResAddress/ResBundle/ResPathUtil/ResLoaderRunner(+Behaviour)` | AB 资源系统。**ResTable 是唯一寻址源**（逻辑名→包名+资产名+编辑器路径）；编辑器直读/真机 Bundle/YooAsset 三实现按宏与平台切换 |
| Core/Combat（2） | `CombatSystem`、`EnemyGrid` | 全局唯一 UpdateEvent 订阅者，固定顺序 tick（怪→塔→子弹）；均匀网格空间哈希索敌 |
| Core/Manager（6） | `BaseManager/IManagerInterface/PlayerDataManager/AudioManager/SaveManager/PerfProbe` | 单例基类；金币/生命经济；音效（配置→ResLoader→AudioSource 池三段查找，无文件静默降级）；存档门面；性能探针（F3，p50/p95/p99） |
| Core/Event（3） | `EventDispatcher/EventController/EventName` | 事件总线（0–4 参数），事件名常量表 |
| Core/UI（3） | `UIManager/SafeAreaFitter/UIFader` | 三层面板管理（View=prefab 上 MonoBehaviour，BaseView 已废弃）；刘海屏适配；淡入（unscaled） |
| Core/Enum（1） | `EnumFile.cs` | 怪物类型等枚举 |
| Core（1·P2b 新增） | `GameClock` | 全局模拟速度参数：`Speed`（float 1/2/3，默认 1）+ 每帧 `Tick()` 缓存 `DeltaTime = Time.deltaTime × Speed`；**全工程唯一速度源**，timeScale 不参与倍速 |
| AStarWrapper（4） | `AStarManager/AStarWrapper/Point/Singleton` | A\* 寻路（建塔堵路校验 + 路径刷新），namespace `AStar` |
| Data（12） | `Configs/MonsterCatalog/TowerConfig/EnemyConfig/BulletConfig/LevelConfig/WaveConfig/GlobalConfig/AudioConfig/AudioCatalog/AudioName/SaveData` | Luban 9 表加载与包装；怪物/音频目录 |
| Data/Persistence（12） | `ISaveStorage/SaveStorageFactory/JsonSaveStorage/SqliteSaveStorage/IDatabase/SqliteDatabase/SqliteNative/SqliteTransaction/DbRow/CryptoService/KeyProvider/SaveSchema` | JSON+SQLite 双存储、加密、事务、schema 版本 |
| Game（6） | `Board/BoardView/CellView/GameFlowManager/PathArrowView/BackgroundParallax` | 棋盘数据与视图；关卡流程状态机；路径箭头；视差 |
| Round（1） | `WaveManager` | 回合→(时刻,怪id) 扁平时间轴，单计时器推进 |
| Enemy（3） | `BaseEnemy/EnemyManager/MonsterAnimEventReceiver` | 怪物基类（血条/受击/四态动画）；生成与池化；动画事件接收 |
| Tower（7） | `BaseTower(含 TowerManager 内嵌@561行)/NormalTower/PowerTower/RetardTower/TowerPlacement/RangeIndicatorView/SlowAuraView` | 塔基类与建/升/售管理（含 A\* 堵路校验+扣费+回滚）；放置拾取；射程圈/减速光环表现 |
| Bullet（2） | `BaseBullet/LaserBeamView` | 子弹（穿透/AOE/减速/持续伤害）；激光纯表现（hitscan 结算在 BaseTower.Fire） |
| Camera（1） | `CameraController` | 2D 正交平移/缩放/自适应 |
| UI（9） | `HudView/TipsView/SelectView/PauseView/SettingView/LevelClearView/LevelClearInfo/TowerInfoView/FloatingTextManager` | 见策划案 §6.1 |
| 对象池 | `Core/ObjectPool.cs` | 通用池（工厂+reset 委托） |

### 3.2 编辑器工具（Assets/Editor，21 个，菜单 Tools▸塔防）

`M0SetupWizard`（0.自检/一键补齐）· `ProjectSettingsConfigurator`（2.工程设置）· `LubanExporter`（3.导表）· `ABNameSetter`（4.按 ResTable 打 AB 标记）· `BuildAssetBundles`（5.打包 AB/5b 严格模式）· `LevelMapEditorWindow`（地图编辑器）· `MapGenerator` · `PlaceholderArtGenerator` · `TowerPrefabConverter` · `BattlePrefabBuilder` · `MonsterPrefabBuilder` · `PhysicsComponentCleaner` · `UIPrefabBuilder` · `UiTmpMigrator` · `SceneMainBuilder` · `MissingScriptCleaner(+Window)` · `EditorUtil` · `YooAsset/FTYooAssetDefine`（USE_YOOASSET 宏开关）· `YooAsset/FTBundlePackRule`（按 ResTable 分包）· `YooAsset/FTYooAssetSetupWizard`

### 3.3 勿动文件清单（核心链路，改动需单独评审）

`ResTable.cs`、`CombatSystem.cs`、`EnemyGrid.cs`、`GameFlowManager.cs`、`WaveManager.cs`、`BaseTower.cs`（含 TowerManager）、`BaseBullet.cs`、`AStarManager.cs`、`Configs.cs`、`EventDispatcher.cs`、`SaveManager.cs`、`Launcher.cs`。规则：这些文件只许**追加**不许改写既有行为；新功能优先走事件总线挂接。**P2b 唯一豁免**：允许且仅允许把上述文件中的「时间消费点」由 `Time.deltaTime`（含 `×1000` 的 ms 累计）**单行替换**为 `GameClock.DeltaTime`，不改任何逻辑结构（diff 逐行可查，验收时逐文件列出）；`Core/GameClock.cs` 为 P2b 新增文件，落地后纳入本清单。

---

## 4. 数据配置方式（Luban 全链路）

### 4.1 链路

```
策划改 Luban/Config/Datas/*.xlsx
  → 关闭 Excel（确认无 ~$ 锁文件）
  → 双击 Luban/gen_code_json.bat（或 Tools▸塔防▸3.导出配置表）
  → 产物：Assets/Gen/*.cs（namespace cfg）+ Assets/ConfigJson/*.json
  → 运行时：Launcher → Configs.cs 加载 9 表 → 各包装类安全访问（缺字段走默认值，不报错不阻塞）
```

### 4.2 九张表

| 表 | json | 行数 | 关键字段 |
|---|---|---|---|
| 塔 | tbtowerinfo | 15 | id/type/name/resName/level/radius/power/CD/prices/bulletId/targetMode/searchIntervalMs/rotateSpeed/upgradeTo/sellPrice/effectType/effectValue/canAttackAir |
| 子弹 | tbbulletdata | 5 | id/speed/hitRadius/lifeTimeMs/pierce/aoeRadius/effectType/effectValue/scale |
| 敌人 | tbenemydata | 132 | id/speed/hp/name/type/resName/armor/reward/damageToPlayer/scale/bodyRadius/isFlying |
| 波次编组 | tbenemylist | 40 | id/EnemyIndexs[]/interval/enemyInterval |
| 回合 | tbrounddata | 40 | id/EnemyIndexs[]/interval/rewardGold |
| 关卡 | tbsceneinfo | 8 | id/RoundList[]/mapId/initialGold/initialHp/waveIntervalMs/difficulty（`CameraRotration`/`EenemyPosition` 为历史拼写，**保留不改**，生成代码沿用） |
| 棋盘 | tblevelmap | 8 | 格子布局（空地/障碍/S/E） |
| 全局 | tbglobal | 1 | cellSize/池大小/maxEnemyAlive=200/sellRefundRate/autoNextRoundDelayMs=5000/deathRecycleDelayMs=600 等 |
| 音频 | tbaudio | 16 | logicalName/volume/pitch/loop/is3d |

### 4.3 改表落地 SOP（AI 执行顺序）

1. 用 Python（openpyxl，managed python 3.13.12）**直接改 xlsx 值**，不改列结构、不改 id 主键；
2. 检查 `Luban/Config/Datas/` 无 `~$*.xlsx` 锁文件（有则先删）；
3. 执行 `Luban/gen_code_json.bat`；
4. 校验：`Assets/ConfigJson/` 9 个 json 刷新时间与行数符合预期；`Assets/Gen/` 重新生成；
5. Unity 菜单 `Tools▸塔防▸0. 自检` 全绿；
6. 进 Preparing 状态实测：建塔扣费/出怪数值与新表一致（抽查 3 行）。

---

## 5. 资源命名规范

| 类别 | 规则 | 示例 |
|---|---|---|
| 怪物 prefab/Sprite | `Enemy_<PascalCase>`，美术与 prefab 同名同目录 | `Enemy_Rat.prefab` / `_UIAssets/Monsters/Rats/Rat/Rat.png` |
| 塔 prefab | `Tower_<Type><LevelIndex0起>` | `Tower_Normal0/1/2` |
| 塔美术 | `_UIAssets/Tower/<Type>/`，基座+炮管分件 | `turret_base_128.png`、`tower_barrel_lv2.png` |
| UI prefab/脚本 | 视图名 = 类名 = prefab 名，`<Name>View` | `HudView.prefab` ↔ `HudView.cs` |
| 子弹 | `Bullet_<Name>` | `Bullet_Normal` |
| 配置 json | `tb<表名>` 全小写 | `tbtowerinfo.json` |
| 音频逻辑名 | `sfx_<动作>_<对象>` / `bgm_<场景>` | `sfx_tower_fire_normal` |
| 资源逻辑名（ResTable） | 与 prefab 名一致，一处登记 | `Tower_Normal0` |
| 拼写修正 | `Enemy_WolfMounfed.prefab` → `Enemy_WolfMounted.prefab`（P1 阶段连同 meta 改名，并同步 tbenemydata.resName 与 MonsterCatalog） | |

---

## 6. 分阶段实施步骤与验收标准

> 每步可直接交给 AI 执行。除标注【Unity】的步骤需在编辑器内操作外，其余均可脚本化。完成一个阶段并过验收后再进下一阶段。

### P1 工程卫生（前置，半天）

**目标**：清除死代码与冗余物，让仓库回到"随时可出包"的干净基线。

**前置条件**：无（第一阶段）；先 `git status` 确认工作区无未提交的有效改动。

**操作步骤（命令级）**
1. 删除文件（连同 .meta）：`Assets/Scripts/Core/UIEventListenerManager.cs`、`Assets/Scripts/Core/EventManager.cs`、`Assets/PopMain.cs`、`Assets/TestTileMap.cs`；
2. 改名：`Enemy_WolfMounfed.prefab` → `Enemy_WolfMounted.prefab`（meta 随行），然后全局搜索 `WolfMounfed` 同步引用——`Luban/Config/Datas/EnemyData.xlsx` 的 resName 列、`Assets/Scripts/Data/MonsterCatalog.cs`，改完走 §4.3 SOP 重新导出；
3. 移除根目录 `tips.zip`；StreamingAssets 下 3 个孤儿 meta（`AssetBundles.meta`/`build_info.meta`/`yoo.meta`，对应目录已不存在）；
4. 移出版本控制（或删除）：`Csharp_CustomTemplate_AsyncLoad/`、`GenerateDatas/`、`Luban/Config/Gen`（均为 Luban 示例遗留，不参与 Unity 编译）；
5. `.gitignore` 增补：`tips.*`、`*_BurstDebugInformation_DoNotShip/`；
6. 【Unity】`Tools▸塔防▸0. 自检`。

**改动文件与脚本要点**：仅删除/改名，不改任何保留文件；`MonsterCatalog.cs` 是工具生成文件，改名后需同步重新生成或手改对应行。注意 `EventManager.cs` 与正常事件系统（`Core/Event/EventDispatcher`）无关，删除无影响。

**验收检查点**
- [ ] Unity 编译 0 错误、无新增警告
- [ ] `Tools▸塔防▸0. 自检` 全绿（20+ 项）
- [ ] 全局搜索 `UIEventListenerManager|EventManager|PopMain|TestTileMap|WolfMounfed` 零残留
- [ ] 关卡 1 完整打完一遍无回归

### P2 数值落地（策划案 §3/§4 新数值进表）

**目标**：策划案重新设计的塔/敌人/波次数值全部进 Luban 源表并导出，游戏实际运行新数值。

**前置条件**：P1 完成；先备份 `Luban/Config/Datas/` 到 `backup_YYYYMMDD/`；确认 Excel 全部关闭、无 `~$*.xlsx` 锁文件。

**操作步骤（命令级）**
1. 用 managed python（`C:\Users\lzy\.workbuddy\binaries\python\versions\3.13.12\python.exe`，venv 内装 openpyxl）写改表脚本 `change_tower.py`：按策划案 §3.2 表逐行改 `TowerInfo.xlsx` 15 行的 power/CD/prices/sellPrice/radius/effectValue/bulletId 字段 + `BulletData.xlsx` id=2 的 aoeRadius→1.5；**只改值，不动列结构与 id**；
2. 写 `change_enemy.py`：按策划案 §4.2「原型×梯度」规则回填 `EnemyData.xlsx` 132 行——先建 resName→原型归类映射（16 族系→5 原型），再按梯度 T（=所属关卡难度）套公式 hp=base×k^(T-1)、reward=基础+T；**先输出 diff 预览（行数/旧值/新值）人工确认后再写回**；
3. 写 `change_wave.py`：按策划案 §2.2 血量预算 `HP(w)=1400×1.10^(w-1)` 与 §2.3 编组模板重排 `EnemyList.xlsx` 40 波（EnemyIndexs/interval/enemyInterval，enemyInterval 由 560ms 逐波递减 ~8ms）与 `RoundData.xlsx` 40 回合（rewardGold=30+4×(n−1)）；约束：每关第 5 波重甲/Boss 档占比 ≥40%，第 3 关起每波 ≥1 只 isFlying=1；
4. 走 §4.3 SOP：删锁文件 → `Luban/gen_code_json.bat` → 校验 ConfigJson/Gen 刷新 → 【Unity】`Tools▸塔防▸0. 自检`。

**改动文件与脚本要点**：仅 4 张 xlsx + 导出产物（`Assets/ConfigJson/`、`Assets/Gen/`）；不改任何 .cs。 enemies 映射脚本归类表是唯一人工决策点，需按族系语义判断（如 Pigs/Giants→重甲，Bats/Birds→飞行，Rats/Bunnies→杂兵）。

**验收检查点**
- [ ] ConfigJson 行数不变：15/5/132/40/40/8/8/16/1
- [ ] 抽查：Normal L1 = power 12/CD 400/prices 25/sellPrice 18；Retard L1 bulletId=4；子弹 id=2 aoeRadius=1.5
- [ ] 第 1 波总血量 ∈ [1300,1500]；第 40 波含 Boss 档且重甲+Boss ≥40%
- [ ] 关卡 1 实测：开局 100 金建 4 座 Normal L1 无漏怪过第 1 波（策划案 §5 平衡约束 1）

### P2b 倍速功能（新增代码，唯一的功能开发项）

**目标**：HUD 增加 ×1/×2/×3 倍速按钮（策划案 §7.3，效果图 02 中标注的新增元素）。实现方式为**单一速度参数 `GameClock.Speed` 驱动全部模拟系统**，`Time.timeScale` 不参与倍速（仅作暂停开关 0/1）。

**前置条件**：P2 完成（避免数值与代码改动互相干扰排查）。

**操作步骤（命令级）**
1. `Assets/Scripts/Core/Event/EventName.cs` 追加常量 `GameSpeedChangeRequestEvent`、`GameSpeedChangedEvent`；
2. 新建 `Assets/Scripts/Core/GameClock.cs`（静态类）：`float Speed`（默认 1，档位 1/2/3，支持降档 2.5）、`void Tick()`（每帧缓存 `DeltaTime = Time.deltaTime × Speed`，供同帧所有系统取同一份值）、`void Reset()`（Speed=1）；落地后纳入 §3.3 勿动清单；
3. `Assets/Scripts/Game/GameFlowManager.cs`（追加）：`Update()` 首行调用 `GameClock.Tick()`；订阅 `GameSpeedChangeRequestEvent` → 校验（档位合法、非 Paused、局中状态）→ 写 `GameClock.Speed` → 派 `GameSpeedChangedEvent(int)`；GameOver / QuitToSelect / RestartLevel / 进 Loading 时调用 `GameClock.Reset()`；
4. `Assets/Scripts/UI/HudView.cs`：增倍速按钮绑定（底中 (-140,60)，220×72，与 StartButton 对称），点击循环 1→2→3→1 并派 `GameSpeedChangeRequestEvent`；订阅 `GameSpeedChangedEvent` 同步按钮文案；暂停遮罩打开期间的请求由 GameFlowManager 校验拦下（双保险）；
5. `Assets/Prefabs/UI/HudView.prefab`：照 StartButton 复制按钮节点改名 `SpeedButton`（可用 `Editor/UIPrefabBuilder.cs` 模式生成或【Unity】手工复制）；
6. **模拟系统迁移（本步为主体工作量，适用 §3.3「P2b 唯一豁免」）**：将下列系统的「时间消费点」由 `Time.deltaTime`（含 `×1000` 的 ms 累计）**单行替换**为 `GameClock.DeltaTime`，不改任何逻辑结构——`WaveManager`（出怪时间轴）· `BaseEnemy`（移动/攻击 CD）· `BaseTower`（CD/searchInterval/rotateSpeed）· `BaseBullet`（弹道位移与追踪）· `SlowAuraView`/减速 Buff 计时 · `FloatingTextManager`（0.7s 上浮淡出）· 回合倒计时（RoundComplete 5s 自动开波与 StartButton 倒计时）· `BackgroundParallax`（视差）；
7. **Animator 同步**：BaseEnemy/Boss 的 Animator 在初始化与 `GameSpeedChangedEvent` 时设 `animator.speed = GameClock.Speed`，死亡/回收时还原 1（防对象池复用残留）；暂停冻结依赖 timeScale=0（Animator 默认 Normal 更新模式），无需额外处理；
8. 全局校验：grep 全工程 `Time.timeScale` 确认除 PauseView/GameFlowManager 暂停恢复外无任何赋值；grep `Time.deltaTime` 确认战斗系统无遗漏未迁移点（UI/Tips/PerfProbe 除外）；静态校验后【Unity】编译、自检。

**改动文件与脚本要点**：只许追加不许改写既有行为（§3.3 勿动文件清单约束），**唯一豁免见 §3.3「P2b 唯一豁免」条款（仅限第 6 步时间消费点单行替换）**；`GameClock` 是全工程唯一速度源，禁止任何系统自行 `Time.deltaTime * Speed`；**禁止绕过事件总线让 HudView 直接调 GameFlowManager**；音效 pitch 不随倍速变化（AudioManager 现状即满足，无需改）；Tips（1.2s/条）、出售确认（3s，unscaledDeltaTime）、全部 UI 动画与 PerfProbe 保持实时/unscaled，不受倍速影响。

**验收检查点**
- [ ] ×3 时出怪/移动/攻击/弹道/飘字/减速倒计时/回合倒计时节奏均为 3 倍；切回 ×1 完全还原
- [ ] 倍速切换前后 `Time.timeScale` 恒为 1，仅暂停时为 0（grep 校验通过）
- [ ] 暂停→继续后保持所选档位并立即生效；倍速按钮在 GameOver 后不可用；重开/下一关/回选关回 ×1
- [ ] Animator 速度随档位同步，对象池复用无残留（×3 怪死亡回收后再刷出即为当前档位速度）
- [ ] 音效 pitch 不变；Tips 1.2s 与出售确认 3s 仍为实时
- [ ] ×3 下 PerfProbe p95 ≤16.6ms（不达标按 §7 风险表降档处理：`GameClock.Speed` 为 float，可直接降 ×2.5）
- [ ] 静态校验（check_code/events/members）通过，Unity 编译 0 错误

### P3 音频接入（依赖外部资源，接口已就位）

**目标**：16 项音效 + 2 首 BGM 全部接入，AudioManager 不再静默降级。

**前置条件**：音频资源到位（策划案 §8 清单：wav/ogg、SFX ≤1.5s、BGM ogg ≤128kbps 循环）；P2 完成。

**操作步骤（命令级）**
1. 音频文件放入 `Assets/Audio/`（命名 = tbaudio 的 logicalName，如 `sfx_tower_fire_normal.wav`、`bgm_battle.ogg`）；
2. openpyxl 改 `Audio.xlsx`：增 2 行 BGM（loop=1，volume 0.5/0.4），走 §4.3 SOP 导出；
3. 跑音频目录生成流程刷新 `Assets/Scripts/Data/AudioCatalog.cs` 与 `AudioName.cs`（增 `BgmBattle`/`BgmSelect` 常量）；
4. `ResTable.cs` 登记音频地址（逻辑名→包名/资产名）；【Unity】`Tools▸塔防▸4. 按 ResTable 打 AB 标记` 把音频打进 audio 包；
5. `SelectView.cs`/`HudView.cs` 进入界面时 `AudioManager.Instance.Play(AudioName.BgmXxx)`。

**改动文件与脚本要点**：AudioManager 三段式查找（配置→ResLoader→AudioSource 池）已就绪，**不许改 AudioManager 本体**；BGM 播放点在 View 层追加，走既有 Play 接口。

**验收检查点**
- [ ] 战斗全流程有音：建塔/升级/出售/开火×5 型/受击/死亡/漏怪/回合起止/胜负/UI 点击
- [ ] AudioManager 日志无「缺省静默」；静音/音量 ± 实时生效
- [ ] BGM 循环无缝，切界面（选关⇄战斗）正确切换

### P4 AB 重打与真链冒烟

**目标**：产出与当前 ResTable 一致的 Android AB，验证真机加载链路。

**前置条件**：P1–P3 完成（资源登记终态）；Unity 编辑器可用。

**操作步骤（命令级）**
1. 【Unity】`Tools▸塔防▸4. 按 ResTable 打 AB 标记`；
2. 【Unity】`Tools▸塔防▸5. 打包 AB`（Android）；产物在 `Assets/StreamingAssets/AssetBundles/Android/`；
3. 核对包清单：config（9 json）/ tower / enemy 各族系分包 / ui / audio（P3 后）均在；
4. 定义 `FORCE_AB` 宏（PlayerSettings▸Scripting Define Symbols）跑编辑器冒烟：完整打完关卡 1；
5. （备选）启用 `USE_YOOASSET` 宏走 `YooAsset▸FTYooAssetSetupWizard` 收集/构建/回读——二选一，默认步骤 1–4 的原生 AB 链路。

**改动文件与脚本要点**：不改代码；`ABNameSetter` 与 `BuildAssetBundles` 已按 ResBundle 常量自动化，若新增资源类型须先在 `ResBundle.cs`/`ResTable.cs` 登记再打标。

**验收检查点**
- [ ] FORCE_AB 模式全程无「资源地址表中找不到逻辑名」与包加载错误
- [ ] AB 包清单与 ResTable 登记一一对应（导出清单 diff 为空）
- [ ] 冒烟后撤销 FORCE_AB 宏，编辑器直读模式回归正常

### P5 发布配置与出包（硬性验收，可上线标准）

**目标**：产出可上线的 Release APK 并真机验收。

**前置条件**：P1–P4 完成；真机至少 2 台（中端 + 低端各一）。

**操作步骤（命令级）**
1. 【Unity】Player Settings：锁 `Landscape Left`；`productName=坚守阵地`；version 1.0.0 / Bundle Version Code 1；复核 IL2CPP + arm64-v8a/armeabi-v7a、minSdk 22、包名 `com.<company>.shouzhuzhendi`；
2. 【Unity，**人执行**】创建发布 keystore：`keytool -genkey -v -keystore release.keystore -alias szjd -keyalg RSA -keysize 2048 -validity 10000`；keystore 与别名密码由人保管，**不入库**（.gitignore 加 `*.keystore`）；
3. 【Unity】Build：Build Settings▸Android▸Build（关 Development Build）；或命令行 `Unity.exe -batchmode -projectPath G:\MyTowerGame -executeMethod BuildPipeline.BuildPlayer ...`（需先写 Editor 构建方法，可复用 `ProjectSettingsConfigurator` 模式新增）；
4. 真机 `adb install -r app-release.apk`，完整打完关卡 1，覆盖：暂停/倍速/升级/出售/失败重打/杀进程重进（局内快照继续）；
5. 高负载验证：后期关卡（200 怪+50 塔），F3 PerfProbe 记录 p50/p95/p99。

**改动文件与脚本要点**：仅 ProjectSettings 与构建配置；不写运行时代码。

**验收检查点（上线门槛，全部满足才算完成）**
- [ ] APK 可安装、启动不崩、横屏锁定正确、刘海屏 UI 不遮挡（SafeAreaFitter 生效）
- [ ] 关卡 1 完整可通关、可失败、星级正确写入、下一关解锁
- [ ] 存档断电恢复：杀进程重进可从回合边界继续
- [ ] 性能：200 怪+50 塔 p95 ≤16.6ms（中端机 60fps）；低端机 p95 ≤25ms 可接受；Reporter 无 Error 红条
- [ ] 包体 ≤150MB（超出则回 P4 做 AB 拆包/压缩优化）

### P6 表现替换（外部资源依赖，不阻塞 P5 之后迭代）

**目标**：占位美术全部退役，表现达到上线品质。

**前置条件**：美术资源到位（策划案 §8 清单）；P5 完成（先保证"能上线"，再迭代"更好看"）。

**操作步骤（命令级）**
1. Pierce/Laser 塔皮：美术放入 `Assets/_UIAssets/Tower/Pierce|Laser/`，【Unity】`Tools▸塔防▸高级▸转换防御塔预制体` 生成 6 个 prefab，改 `TowerInfo.xlsx` resName 指向新 prefab → §4.3 SOP 导出；
2. 8 关背景：替换 `Assets/_UIAssets/Backgrounds/`，按 mapId 挂接（BoardView/BackgroundParallax 配置点）；
3. 打击粒子：命中/死亡/AOE 爆炸 3 组 prefab 挂到 Bullet/Enemy 表现层已抛出的事件点；
4. 怪物帧动画：接入 `MonsterAnimEventReceiver` 既有挂点；
5. 每接入一批跑 `Tools▸塔防▸0. 自检` + 关卡 1 冒烟。

**改动文件与脚本要点**：以 prefab/资源替换为主；事件挂接只追加订阅，不改战斗逻辑。

**验收检查点**
- [ ] `Art/Generated/` 9 张占位图全部退役（全局无引用）
- [ ] 5 塔型视觉可区分；8 关背景不重复
- [ ] 风格统一走查通过；性能不回退（复测 P5 性能项）

---

## 7. 风险登记

| 风险 | 等级 | 应对 |
|---|---|---|
| P2 数值重排波及 132 行敌人 + 80 行波次/回合 | 中 | 映射脚本先输出 diff 预览再写表；保留改前 xlsx 备份（`Luban/Config/Datas/backup_YYYYMMDD/`） |
| `CameraRotration`/`EenemyPosition` 拼写修正诱惑 | 低 | **明确不修**：改名需 Gen 代码+表+引用全链路同步，收益为零 |
| 倍速 ×3 下帧率跌破目标 | 中 | PerfProbe 实测；不达标则 ×3 档降为 ×2.5（`GameClock.Speed` 为 float，直接改档即可，无需改结构）或对 maxEnemyAlive 分档 |
| 无发布 keystore 管理经验 | 低 | P5 步骤 2 由人执行，AI 只出命令模板 |
| 音频/美术外部资源延期 | 低 | AudioManager 静默降级 + 占位图机制保证 P5 不依赖 P3/P6 |
