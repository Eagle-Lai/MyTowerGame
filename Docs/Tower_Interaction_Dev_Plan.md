# FreeTower 塔防交互（建塔 / 升级 / 出售）分阶段开发计划

> ⚠️ **本文件已被 `Docs/Tower_Interaction_Dev_Plan_v2.md` 取代（2026-09-29 晚）**
> v2 的变更：① 升级实现方式定案为「换实例」；② 新增「编辑器菜单治理」阶段（M-1~M-6）；
> ③ 修正建造栏方案（改为复用已存在的 `Btn_Tower_*`，而非新建 `BuildBar`）；④ 工时由 11.2d 修正为 17.0d。
> **请以 v2 为准**，本文件保留供追溯 v1 的原始分析。

> 编制日期：2026-09-29
> 适用工程：`D:\FreedomTower_1`　Unity 2022.3.62f3c1
> 定位：M2「内容扩展与手感」阶段的可执行落地计划
> 结论：**暂不写代码**，本文只做现状梳理 + 任务拆分 + 验收标准

---

## 第一部分　现状梳理

### 1.1 塔的数据结构与配置

**表结构（`TBTowerInfo`，Luban 生成，`Assets/Gen/TBTowerInfo.cs`）**

一行 = **某个塔型的某个等级**。已具备升级/出售所需的全部字段：

| 字段 | 含义 | 现有数据（3 行） |
|---|---|---|
| `id` | 唯一 id | 1 / 2 / 3 |
| `type` | 塔型（1 单体 / 2 AOE / 3 减速 / 4 穿透 / 5 激光） | 全部 = 1 |
| `name` | 显示名 | 全为 `NormalTower` |
| `resName` | AB 资源逻辑名 | 全为 `Tower_Normal` |
| `level` | 等级 | 1 / 2 / 3 |
| `radius` | 攻击半径（格） | 3 / 4 / 6 |
| `power` | 伤害 | 10 / 12 / 15 |
| `CD` | 攻击间隔（ms） | 300 / 200 / 100 |
| `prices` | **本等级价格**（L1 建造价，L2/L3 升级价） | 20 / 30 / 50 |
| `bulletId` | 子弹 id | 全为 1 |
| `targetMode` | 索敌策略 0/1/2 | 0 |
| `searchIntervalMs` | 索敌节流 | 100 |
| `rotateSpeed` | 炮管转速 | 360 |
| `upgradeTo` | **下一等级 id，0 = 满级** | 2 / 3 / **0** |
| `sellPrice` | **出售返还基数** | 14 / 35 / 70 |
| `effectType` / `effectValue` | 效果类型/数值（AOE/减速用） | 0 / 0 |
| `desc` | 描述 | 空 |

**配置访问层（`Assets/Scripts/Data/TowerConfig.cs` + `Configs.cs`）**
- `TowerConfig` 是 `TowerInfo` 的只读包装，已暴露 `Prices` / `SellPrice` / `UpgradeTo` / `IsMaxLevel` / `EffectType` / `EffectValue` 等。
- `Configs.GetTowerByTypeAndLevel(type, level)` — 遍历查 `type + level` 匹配项。**这是多塔型的关键入口，已存在且可用**。
- `Configs.GetTower(id)` — 按 id 取（升级链用得上）。
- `RadiusWorld = radius × Global.CellSize` — 射程已有"格→世界单位"换算，**射程圈可直接复用**。

> ⚠️ **关键缺口**：表里 3 行**全是 `type=1`**，`TowerInfo.xlsx` 里**没有 `type=2/3` 的行**。
> 而工作区已有 `Tower_Power` / `Tower_Retard` 两个 prefab 与美术（未提交），**属"资源先到、数据未补"的半成品状态**。

### 1.2 已有塔基类与建造链路

**`BaseTower`（`Assets/Scripts/Tower/BaseTower.cs`）**

| 成员 | 说明 |
|---|---|
| `Config` / `Cell` / `IsBuilt` | 数据与格子绑定 |
| `TickAttack(dt)` | **由 `CombatSystem` 集中驱动**（不自行订阅 UpdateEvent） |
| `Init(cfg, cell)` | 初始化：缓存渲染器、取 `barbette/Img_gun` 与 `BarrelPoint`、`SetTint(white)` |
| `SetTint(Color)` / `SetPreviewAlpha(float)` | **已有染色与半透明接口** — 选中高亮可直接复用 `SetTint` |
| `SnapToCell(CellData)` | 吸附格子中心 |
| `MarkDestroyed()` | 出售时标记失效 |
| `SearchCount` / `FireCount` | 自检计数 |
| `BarrelNativeAngle = 90f` | 炮管贴图原生朝向（美术事实，换皮要改） |

**已定义但未使用的枚举**：`TowerType { None=0, Normal=1, Power=2, Slow=3 }` — **已为多塔型预留，目前全工程无人引用**。

**`TowerManager`（同在 `BaseTower.cs`，`BaseManager<T>` 单例）**

| 方法 | 现状 |
|---|---|
| `TryBuild(type, level, row, col)` | ✅ **完整**：占位校验 → 临时设墙跑 A*（堵死回滚）→ 扣费 → 实例化 → 注册 CombatSystem → 触发 `BuildTowerSuccess` → `RequestRefresh()`。<br>**已支持 `type` 参数**，多塔型无需改造 |
| `Sell(tower)` | ✅ **完整**：释放格子 → 还原 `IsWall` → `MarkDestroyed` → 注销 → `AddGold(sellPrice × SellRefundRate)` → 触发 `DestroyTower` → 释放实例 → `RequestRefresh()` → Tips |
| `Towers` / `Count` | 已有列表 |
| `TryUpgrade(...)` | ❌ **不存在，需新增** |

> **重要结论**：**建塔与出售的服务端逻辑（`TowerManager`）几乎已经写完**，缺的是 ①升级方法 ②UI 入口 ③点击选中。
> 这是本计划最大的有利条件 —— 工作量集中在 UI 与交互，不在底层。

**`NormalTower`（`NormalTower.cs`）**：空壳子类，注释明确写「**新增塔型主要靠配置，而不是新增子类**，本类留作 M2 塔特有逻辑（如激光持续伤害）的扩展点」。

### 1.3 UI 层级与输入事件处理方式

**UI 分层（`Core/UI/UIManager.cs`）**
- 场景结构：`UICanvas`(tag=UICanvas) ├─ `BgPanel` ├─ `NormalPanel` └─ `TipsPanel`
- `UIManager.Open<T>(logicalName, UILayout)` — 从 `ResTable` 按逻辑名实例化，铺满所在层，已打开则复用（不重复实例化）
- `UIManager.Close(logicalName)` / `IsOpen` / `Get<T>`
- **界面一律是挂在 prefab 上的 MonoBehaviour**（`BaseView` 那套已废弃）
- 现有界面：`HudView`（NormalPanel）、`TipsView`（TipsPanel）— **`TowerInfoView` 不存在，需新建**

**HUD 节点（`UIPrefabBuilder.cs` 生成，节点名与代码强绑定）**
```
HudView
├── GoldText / HpText / RoundText
├── TowerButton → TowerButton/Label     （建塔，当前唯一建塔入口）
└── StartButton → StartButton/Label      （开始 / 下一回合）
```
底部两按钮锚点均为 `(0.5, 0)`、`sizeDelta = 220×72`，位置 `(-140,60)` 与 `(140,60)`。

**`HudView` 关键现状**
- `_towerType = 1`、`_towerLevel = 1` **硬编码**（注释：「M0 固定 1/1，M2 接塔选择栏」）
- `OnClickTower()` 只做一件事：`TriggerEvent<int,int>(BuildTowerRequestEvent, _towerType, _towerLevel)`
- `SetTowerButtonInteractable(bool)` 已存在（金币不足置灰），但**当前无调用者**

**输入处理：`TowerPlacement`（`Assets/Scripts/Tower/TowerPlacement.cs`）**

| 环节 | 现状 |
|---|---|
| 进入放置 | 监听 `BuildTowerRequestEvent(type, level)`；已在放置态则**再点一次退出**（toggle） |
| 前置校验 | `TryPeek(prices)` 金币预检 → 不足直接 Tips 并**不进入放置态** |
| 预览体 | `CreateGhost` 实例化该塔 prefab，`alpha = 0.55`（`GhostAlpha`），命名 `TowerGhost` |
| 跟随与吸附 | `Update()` 每帧 `ScreenToCell` → 命中则吸附 `CellCenter3`，棋盘外则自由跟随鼠标 |
| 合法/非法提示 | 悬停格变化时才校验（`EvaluateCell`，A* 探测不每帧做）→ `CellHighlight.Buildable`(绿) / `Blocked`(红) |
| 取消 | **右键** 或 **ESC**（仅在放置态） |
| 放置 | **左键**，且 `!IsPointerOverUI()` 防误触 |
| 出售（M0 简化） | **非放置态右键直接卖**（`TrySellUnderCursor`），注释明确：「后续要做"选中塔 → 弹菜单 → 确认"时，把 `TrySellUnderCursor` 换掉即可」 |
| 校验顺序 | 棋盘内 → `IsBuildable` → 无塔 → 无怪 → 金币够 → 不堵路 |

**事件体系（`Core/Event/EventName.cs`）— 已为升级/出售**预留**了事件名**
- ✅ 已定义但**无人使用**：`TowerSelectedEvent`（参数 `BaseTower`）、`TowerDeselectedEvent`、`BuildTowerFail`（参数 `string`）
- ✅ 在用：`BuildingTower` / `BuildTowerSuccess(BaseTower)` / `DestroyTower(BaseTower)` / `BuildTowerRequestEvent(int,int)` / `CancelBuildRequestEvent` / `ShowTipEvent(string)` / `GoldChangeEvent(int,int)`

**棋盘与高亮（`BoardView.cs` / `CellView.cs`）**
- `SetHighlight(row,col,CellHighlight)` / `ResetHighlight` / `ResetAllHighlight()`（✅ 已有批量清除，选中态切格时用得上）
- `CellHighlight { None, Buildable, Blocked }` — **颜色写死在 `CellView`：绿 `(0.4,1,0.4)` / 红 `(1,0.35,0.35)`**，加"选中"色需改枚举与 `CellView`
- `ScreenToCell(screenPos, out row, out col)` — 屏幕→格子唯一入口
- `BoardSorting { Cell=0, Enemy=200, Tower=300, Bullet=400 }` — 射程圈若走 SpriteRenderer，排序值需在此登记

### 1.4 现状小结（能力矩阵）

| 能力 | 数据层 | 逻辑层 | UI/交互层 | 结论 |
|---|---|---|---|---|
| 单塔建造 | ✅ | ✅ `TryBuild` | ✅ `TowerButton` + `TowerPlacement` | 完成 |
| 放置预览/取消 | ✅ | ✅ | ✅ 半透明 ghost + 红绿格 + 右键/ESC | 完成 |
| **多塔型** | ⚠️ 只有 type=1 | ✅ `TryBuild(type,…)` 已支持 | ❌ 无选择 UI | **缺数据 + 缺 UI** |
| **升级** | ✅ `upgradeTo/prices` | ❌ 无 `TryUpgrade` | ❌ 无面板 | **缺逻辑 + 缺 UI** |
| **出售** | ✅ `sellPrice` | ✅ `Sell()` 完整 | ❌ 仅右键直接卖（无确认） | **缺面板/确认** |
| 选中态高亮 | — | ❌ 无选中概念 | ❌ 无 | 全缺 |
| 攻击范围提示 | ✅ `RadiusWorld` | — | ❌ 无 | **仅缺视图** |
| 误触防护 | — | — | ✅ `IsPointerOverUI()` | 已有基础 |
| 金币不足 | ✅ `TryPeek` | ✅ | ⚠️ `SetTowerButtonInteractable` 有但无调用者 | **需接线** |

---

## 第二部分　目标交互设计（对标《坚守阵地》）

### 2.1 三态交互模型

```
【空闲态 Idle】
  点击空地 / ESC / 右键  → 取消选中，范围圈消失，格子高亮复位

【建造态 Build】（点击建造栏某一塔型进入）
  塔 ghost 半透明跟随鼠标
  ├─ 悬停合法格 → 绿 + 范围圈（显示该塔射程）
  ├─ 悬停非法格 → 红 + 范围圈（红）+ Tips 说明原因
  ├─ 左键合法格 → 落位扣费，**默认留在建造态**（可连建，原作手感）
  ├─ 右键 / ESC → 退出建造态
  └─ 再次点击同一塔型卡片 → 退出建造态

【选中态 Selected】（点击已建造的塔进入）
  该塔高亮 + 显示射程圈 + 弹出 TowerInfoView 面板
  ├─ 点击「升级」→ 扣费升级，面板刷新数值与价格
  ├─ 点击「出售」→ 二次确认 → 返还金币，面板关闭
  ├─ 点击其它塔 → 切换到那座塔
  └─ 点击空地 / ESC / 面板「×」→ 关闭面板
```

**三态互斥**：进入任一态必须先退出另一态（单一状态源，避免"建造中又弹出升级面板"）。

### 2.2 操作手感要点（原作对齐）

| # | 要点 | 说明 |
|---|---|---|
| 1 | **连建不退出** | 原作建筑是"选一次类型可连续摆放"；当前实现是"建一次就退出"，需改 |
| 2 | **射程圈常驻预览** | 原作拖放与选中时都显示攻击圈，是判断塔位的核心依据 |
| 3 | **左键选中、右键快捷出售** | 原作左键点塔开菜单；右键快捷操作可保留为"快捷出售"但**需二次确认** |
| 4 | **升级在面板内完成** | 不弹出二级窗口，按钮原地变化（价格/等级/数值联动刷新） |
| 5 | **金币不足时按钮置灰** | 灰色不可点，价格数字变红，而非点击后弹错 |
| 6 | **误触防护** | 点击 UI 不穿透到棋盘（已有）；面板打开时点面板外区域关闭需谨慎（避免战斗中误关） |

### 2.3 沿用现有技术栈（强制约束）

- UI 一律 **UGUI**，挂 `UICanvas` 下，经 `UIManager.Open<T>()` 加载，逻辑名登记进 `ResTable` + `ResBundle.UiHud`
- 界面与战斗逻辑**只通过 `EventDispatcher` 通信**，HUD/面板**不直接持有 TowerManager 引用**
  （例外：`TowerInfoView` 需要展示具体塔的数据，建议同样走事件传 `BaseTower`，与 `TowerSelectedEvent` 一致）
- 战斗对象一律世界空间 `SpriteRenderer`，**不进 UGUI**；射程圈用 SpriteRenderer
- 节点名与 Editor 生成脚本**成对修改**（`UIPrefabBuilder.cs` ↔ `*View.cs`）
- 新增 MonoBehaviour **必须独立成文件**（类名 = 文件名，Unity 硬性要求）
- 事件监听带参数的回调**必须显式写泛型**（`AddEventListener<int>(...)`），否则 `CS1503`
- 数值全部走配置表，**新增塔型不改代码**

---

## 第三部分　分阶段任务拆分

> 优先级：🔴 P0 = 阻塞/必做　🟠 P1 = 核心体验　🟡 P2 = 打磨/可选
> 工时按 1 名熟练 Unity 开发估算

### 阶段 A：多塔型支持（P0）

#### A-1 🔴 补齐塔配置数据与资源登记
- **任务**：`TowerInfo.xlsx` 按"每型 × 每级"补行
  - `type=2 Power`（如 L1: radius 3 / power 25 / CD 800 / prices 40 / sellPrice 28）
  - `type=3 Slow`（如 L1: radius 3 / power 6 / CD 500 / prices 35 / sellPrice 24 / `effectType=1` / `effectValue=0.5`）
  - 每型补齐 L1→L2→L3 三行，`upgradeTo` 串成链，最后一级填 0
- **涉及模块**：`Luban/Config/Datas/TowerInfo.xlsx`、重跑 `gen_code_json.bat`、`Assets/ConfigJson/tbtowerinfo.json`
- **验收标准**：
  1. 导出后 `tbtowerinfo.json` 含 9 行（3 型 × 3 级），Console `[Config] 交叉引用自检通过。`
  2. `Configs.GetTowerByTypeAndLevel(2,1)` / `(3,1)` 返回非 null
  3. 每型 `upgradeTo` 链正确：L1→L2→L3→0

#### A-2 🔴 资源登记与 AB 包名统一（**同时修掉已知的包名不一致**）
- **任务**：
  - `ResTable.cs` 补 `Tower_Power` / `Tower_Retard` 逻辑名 + 真实路径
  - 补两型的 base/barrel 贴图条目（`Power/tower_base`、`Power/tower_barrel`、`retard/slowtower_base`、`retard/slowtower_crystal`）
  - **统一 AB 包名**：三个 prefab 的 `.meta` 已标 `tower`，而 `ResBundle.TowerNormal = "tower_normal"` — 二选一
    （建议：`ResBundle` 新增 `Tower = "tower"` 常量，三塔共包，`ResTable` 改引用它，格式与 `enemy_<家族>` 分包风格一致）
- **涉及模块**：`Core/Res/ResTable.cs`、`Core/Res/ResBundle.cs`、`Assets/Prefabs/Tower/*.meta`
- **验收标准**：
  1. 自检 `ResTable` 每条路径真实存在（`Tools ▸ 塔防 ▸ 0. 自检` 无 ✘）
  2. 三个塔 prefab 的 `assetBundleName` 与 `ResBundle` 常量完全一致
  3. `8b. 打包 AssetBundle` 后 `StreamingAssets/AssetBundles/<平台>/tower` 存在，且**旧 `tower_normal` 不再产出**

#### A-3 🔴 新增 `TowerType` 枚举接线与塔型元数据
- **任务**：
  - 复用已有 `TowerType { Normal=1, Power=2, Slow=3 }`
  - 因"一型多级"需按 `type` 找 L1 行来显示卡片，新增 `Configs.GetTowerLevel1(type)` 或复用 `GetTowerByTypeAndLevel(type, 1)`
  - 为建造栏提供"可建造塔型列表"（建议：从 `TowerTable` 遍历 `level==1` 的行生成，**不硬编码**，加新塔只需补表）
- **涉及模块**：`Tower/BaseTower.cs`（枚举位置）、`Data/Configs.cs`、`Data/TowerConfig.cs`
- **验收标准**：
  1. 遍历配置能得到 N 个 L1 塔型（当前应为 3）
  2. 新增一行 `type=4 level=1` 的表数据后，**不改代码**即出现在建造栏

#### A-4 🔴 建造栏 UI（塔选择卡片列表）
- **任务**：
  - 在 `HudView` 底部新增 `BuildBar` 容器，替换现有单个 `TowerButton`
  - 卡片结构：`BuildBar/Slot_{type}` → 图标（塔贴图）+ 名称 + 价格
  - 卡片状态：**可选 / 已选中（高亮描边）/ 金币不足（置灰 + 价格红字）**
  - 点击卡片 → `BuildTowerRequestEvent(type, 1)`
- **涉及模块**：`Assets/Editor/UIPrefabBuilder.cs`（生成节点）、`UI/HudView.cs`、`UI/BuildBarView.cs`(新)、`ResTable`（卡片图标）
- **验收标准**：
  1. 底部显示 3 个塔卡片，各自显示名称与价格，数值与 `TowerInfo.xlsx` 一致
  2. 金币 < 某塔价格时该卡片置灰且不可点击，价格文字变红
  3. 点击卡片进入建造态，卡片显示选中态；再点一次退出
  4. 建造态下卡片区仍可见（原作可随时换塔型），且**不响应棋盘点击**（`IsPointerOverUI` 生效）
  5. 节点名与 `BuildBarView.cs` 完全一致，无「缺少子节点」报错

#### A-5 🟠 切换塔型与预览体刷新
- **任务**：
  - 建造态下点击**另一张**卡片 → 直接换型（销毁旧 ghost、建新 ghost），**不退出建造态**
  - `TowerPlacement` 增加 `SwitchType(type, level)` 或让 `OnBuildRequest` 支持"已在放置态且 type 不同 → 换型"
  - 换型后立刻按当前悬停格重算红绿
- **涉及模块**：`Tower/TowerPlacement.cs`、`UI/BuildBarView.cs`
- **验收标准**：
  1. 建造态下点另一卡片，ghost 模型与射程数值立即变化，无需退出重进
  2. 换型后悬停颜色与新塔的合法性一致（如价格变化导致金币不足 → 变红）
  3. 全程无 ghost 泄漏（`CreateGhost` 内先 `DestroyGhost`）

#### A-6 🟠 连建模式（手感修正）
- **任务**：建造成功后**不退出建造态**，继续跟随鼠标可连续摆放（原作手感）
- **涉及模块**：`Tower/TowerPlacement.cs`（`TryPlace` 不再调 `ExitPlacement`）、`UI/HudView.cs`
- **验收标准**：
  1. 连续左键可连续建塔，金币逐次扣减
  2. 金币不足时自动退出建造态并 Tips「金币不足」
  3. 右键 / ESC 可随时退出；退出后卡片选中态复位

> ⚠️ **注意**：这条与 M0 现有行为（建完即退）**是行为变更**，需在文档 §6.2.2 同步更新，并确认验收清单第 7 项描述。

---

### 阶段 B：升级与出售（P1）

#### B-1 🔴 点击选中已建造塔
- **任务**：
  - `TowerPlacement`（或新增 `TowerSelector`）在**非建造态**下监听左键：`ScreenToCell` → `cell.Tower != null` → 选中
  - 选中后 `TriggerEvent<BaseTower>(TowerSelectedEvent, tower)`；再点空地 → `TowerDeselectedEvent`
  - **与建造态互斥**；用 `IsPointerOverUI()` 防误触（已有）
- **涉及模块**：`Tower/TowerPlacement.cs`（或新建 `Tower/TowerSelector.cs`）、`EventName.cs`（事件已存在）
- **验收标准**：
  1. 非建造态左键点塔，Console 可观察到 `TowerSelectedEvent`（含 tower 实例）
  2. 点空地 / 点另一座塔 → 正确切为空 / 切换
  3. 建造态下点击塔**不会**触发选中
  4. 点击 UI 区域不会触发选中

#### B-2 🔴 `TowerManager.TryUpgrade` 升级逻辑
- **任务**：新增升级方法
  ```
  TryUpgrade(BaseTower tower)：
    1. 校验 tower 有效且 !IsMaxLevel
    2. 取 nextCfg = Configs.GetTower(tower.Config.UpgradeTo)
    3. 扣费 TrySpend(nextCfg.Prices)，不足 → Tips「金币不足」返回 false   ← 先扣费？
    4. 原地替换：销毁旧实例 → 实例化 nextCfg.ResName → 吸附同一格 → Init(nextCfg, cell)
       并保持 CombatSystem 注册与 cell.Tower 指向新实例
    5. 触发事件（建议新增 UpgradeTowerSuccess(BaseTower)）
  ```
- **关键决策点**（需实现前定）：**升级是"原地换 prefab"还是"只换配置不换模型"**
  - 推荐 **替换实例**：与 `TryBuild` 复用同一套流程，配置可指向不同 resName（如 L2/L3 换更华丽的塔）
  - 若各等级共用同一 resName（当前 NormalTower 就是），替换会有一次视觉闪动 → 可优化为"仅 `Init` 换配置"
- **涉及模块**：`Tower/BaseTower.cs`（`TowerManager`）、`EventName.cs`、`Core/Combat/CombatSystem.cs`（重新注册）
- **验收标准**：
  1. L1 → L2 升级后：伤害/射程/CD 变化与 `TowerInfo.xlsx` L2 行一致（可打日志核对）
  2. 金币正确扣减 `L2.prices`；不足时**不升级不扣费**
  3. 满级（`upgradeTo=0`）时升级按钮不可点
  4. 升级后塔仍在原格，格子占用不丢；路径不被误改
  5. 升级后仍能正常索敌开火（`CombatSystem` 注册未丢）

#### B-3 🔴 `TowerInfoView` 升级/出售面板
- **任务**：新建界面 prefab + 脚本
  - 布局（建议右侧竖排，参考原作贴边面板）：

    ```
    TowerInfoView（NormalPanel 层）
    ├── Panel（半透明底板，Image 纯色）
    │   ├── TitleText        塔名 + 等级「NormalTower Lv.1」
    │   ├── IconImage        塔图标
    │   ├── StatText         伤害 / 射程 / 攻速 / DPS
    │   ├── UpgradeButton → Label   「升级  ¥30」
    │   ├── SellButton    → Label   「出售  +¥14」
    │   └── CloseButton             「×」
    ```
  - 监听 `TowerSelectedEvent(BaseTower)` → 打开并 `Bind(tower)`
  - 监听 `TowerDeselectedEvent` / `DestroyTower` → 关闭
  - 面板**不直接调 TowerManager**，改为发 `UpgradeTowerRequestEvent` / `SellTowerRequestEvent`，由 `TowerPlacement`（或专门的 `TowerInteractionController`）执行
- **涉及模块**：`Assets/Editor/UIPrefabBuilder.cs`、`UI/TowerInfoView.cs`(新)、`ResTable.cs`、`ResBundle.cs`、`EventName.cs`
- **验收标准**：
  1. 点击塔弹出面板，标题/图标/数值与所选塔配置一致
  2. 面板显示真实等级、真实升级价、真实出售返还
  3. 点「×」或点空地关闭；关闭后无残留（`UIManager.IsOpen == false`）
  4. 面板打开时，点击面板区域**不会**穿透到棋盘（不误建塔/误选中）
  5. 节点名与 `UIPrefabBuilder.cs` 严格一致

#### B-4 🟠 等级与费用展示联动
- **任务**：
  - 面板显示"当前等级 / 最高等级"（如 `Lv.1 / 3` 或三颗星）
  - 升级按钮展示**下一等级增量**：伤害 `10→12`、射程 `3→4`、价格 `¥30`
  - 满级时按钮文案变「已满级」并置灰
  - 金币不足时按钮置灰 + 价格红字
- **涉及模块**：`UI/TowerInfoView.cs`
- **验收标准**：
  1. 升级前后数值文本正确刷新，无残留旧值
  2. 满级塔按钮为「已满级」且不可点
  3. 金币不足时按钮置灰且**点击无反应**（不是点了才提示）
  4. 升级/出售后金币变化，HUD 与面板价格同步刷新

#### B-5 🟠 出售返还规则与二次确认
- **任务**：
  - 返还 = `TowerConfig.SellPrice × Global.SellRefundRate`（`Sell()` 已实现，默认 rate=1）
  - **累进规则**：若塔已升级，`sellPrice` 应反映"总投入的返还"——需明确：用**当前等级的 sellPrice**，还是"各级 prices 之和 × rate"
    → **建议**：表里每级 `sellPrice` 直接写成期望返还款（当前数据 L1=14 / L2=35 / L3=70 已近似"累计投入的 70%~80%"），**逻辑不改**，只靠填表
  - **二次确认**：点「出售」→ 按钮变「确认出售？」（3 秒内再点生效，超时复位）—— **不弹二级窗口**，保持手感流畅
- **涉及模块**：`UI/TowerInfoView.cs`、`Luban/Config/Datas/TowerInfo.xlsx`（数据口径）
- **验收标准**：
  1. 出售返还金额 = 面板显示金额，且 HUD 金币同步增加
  2. 首次点「出售」不执行，显示确认态；再点执行
  3. 确认态 3 秒超时自动复位为「出售」
  4. 出售后格子恢复可建造、路径重算（怪物改道）、面板自动关闭
  5. 出售后该格可立即重新建塔

#### B-6 🟡 保留右键快捷出售（可选）
- **任务**：现 `TrySellUnderCursor` 为"右键直接卖"，与 B-5 的确认机制冲突。二选一：
  - (a) 移除右键直接卖，统一走面板（**推荐**，与原作一致）
  - (b) 保留但加确认态
- **涉及模块**：`Tower/TowerPlacement.cs`
- **验收标准**：右键在非建造态不再静默卖塔（或行为符合所选方案），文档同步更新

---

### 阶段 C：交互细节与异常处理（P1/P2）

#### C-1 🔴 选中态高亮
- **任务**：
  - 塔本体高亮：复用 `BaseTower.SetTint(Color)` — 选中时染亮色（如 `Color(1.25,1.25,1.25)` 或描边色），取消恢复 `white`
  - 格子高亮：`CellHighlight` 新增 `Selected` 枚举值 + `CellView` 加对应颜色（如亮黄 `(1,0.95,0.5)`）
  - 切换选中时用 `ResetAllHighlight()` 或精确复位上一格
- **涉及模块**：`Tower/BaseTower.cs`、`Game/Board.cs`（枚举）、`Game/CellView.cs`
- **验收标准**：
  1. 选中的塔明显区别于未选中（颜色变化可辨）
  2. 切换选中/取消后**所有**高亮正确复位（无残留亮色）
  3. `CellHighlight` 新增值不影响建造态红绿逻辑

#### C-2 🔴 攻击范围提示（射程圈）
- **任务**：
  - 世界空间半透明圆，用 SpriteRenderer（**不用 LineRenderer/UGUI**，与 §6.8 性能约定一致）
  - 实现方式二选一：① 一张圆形 Sprite 按 `radius` 缩放；② 用生成的圆环贴图
  - 触发场景：**建造态跟随鼠标**、**选中态显示所选塔射程**
  - 颜色：建造态合法→绿 / 非法→红；选中态→白/黄
  - 排序值需在 `BoardSorting` 登记（建议 `RangeIndicator = 250`，在怪之下、格子之上，或 450 在最上，需目视确认不遮挡）
  - 走对象池或单例复用（**不要每次选中都 Instantiate/Destroy**）
- **涉及模块**：`Game/RangeIndicatorView.cs`(新)、`Game/Board.cs`（`BoardSorting`）、`Tower/TowerPlacement.cs`、`Editor/PlaceholderArtGenerator.cs`（生成圆贴图）、`ResTable.cs`
- **验收标准**：
  1. 建造态移动鼠标时，圈半径随塔型变化（比例 = `radius × cellSize`）
  2. 选中已建塔时显示其**当前等级**射程；升级后圈变大
  3. 退出建造/取消选中后圈消失，无残留
  4. 连续切换选中 10 次无对象泄漏（`Instantiate` 次数不增长）
  5. 圈不遮挡塔与怪的可见性（目视）

#### C-3 🟠 误触防护完善
- **任务**：
  - 所有棋盘点击统一先判 `IsPointerOverUI()`（已有，需覆盖新增的选中路径）
  - 建造态下点击建造栏卡片 → 换型而非取消
  - 面板打开时，点击面板外区域的处理：**建议不自动关闭**（避免战斗中误关），仅「×」/ESC/点空地关闭
  - `ESC` 优先级：先关面板 → 再退建造态 → 再取消选中
- **涉及模块**：`Tower/TowerPlacement.cs`、`UI/TowerInfoView.cs`、`UI/HudView.cs`
- **验收标准**：
  1. 点 HUD/建造栏/面板任何区域都不会在棋盘上建塔或选中
  2. ESC 按优先级逐层退出，不会一次全退
  3. 面板打开时点面板内部不会关闭面板

#### C-4 🟠 金币不足与异常状态
- **任务**：
  - 建造栏卡片：金币不足置灰 + 价格红字（A-4 已含）
  - 升级按钮：不足置灰 + 价格红字（B-4 已含）
  - 接线已有的 `HudView.SetTowerButtonInteractable(bool)`（当前无调用者）或随 BuildBar 改造一并废弃
  - 监听 `GoldChangeEvent` 刷新所有价格类 UI 的可点状态（**统一入口，避免各界面各写一遍**）
  - 其它异常：资源加载失败（`TryBuild` 已回滚+退钱）、满级、塔被怪围住时的建造拒绝（`HasAliveEnemyNear` 已实现）
- **涉及模块**：`UI/BuildBarView.cs`、`UI/TowerInfoView.cs`、`UI/HudView.cs`、`EventName.cs`（复用 `GoldChangeEvent`）
- **验收标准**：
  1. 金币从充足降到不足时，建造栏与升级按钮**自动**变灰（无需手动刷新）
  2. 金币回升后自动恢复可点
  3. 所有"不可点"状态点击均无副作用、无报错
  4. Console 无 `NullReferenceException`（覆盖：面板打开时塔被卖/被销毁）

#### C-5 🟡 数值展示与手感打磨
- **任务**：塔面板显示 DPS（`power / CD`）、射程秒数；金币变化时数字跳动/闪烁（§6.8 反馈清单第 3 项）；升级/出售的音效钩子（`MonsterAnimEventReceiver` 已有音效分发惯例）
- **涉及模块**：`UI/TowerInfoView.cs`、`UI/HudView.cs`
- **验收标准**：DPS 数值与 `power/(CD/1000)` 一致；金币变化有明显视觉反馈

---

## 第四部分　任务汇总与依赖

### 4.1 优先级与工时

| 编号 | 任务 | 优先级 | 主要模块 | 依赖 | 工时 |
|---|---|---|---|---|---|
| A-1 | 补塔配置数据 | 🔴 | Luban/TowerInfo.xlsx | — | 0.5d |
| A-2 | 资源登记 + AB 包名统一 | 🔴 | ResTable/ResBundle/*.meta | — | 0.5d |
| A-3 | TowerType 接线 + 塔型列表 | 🔴 | Configs/TowerConfig | A-1 | 0.5d |
| A-4 | 建造栏 UI | 🔴 | UIPrefabBuilder/HudView/BuildBarView | A-2,A-3 | 1.5d |
| A-5 | 切换塔型 | 🟠 | TowerPlacement | A-4 | 0.5d |
| A-6 | 连建模式 | 🟠 | TowerPlacement | A-4 | 0.5d |
| B-1 | 点击选中塔 | 🔴 | TowerPlacement | — | 0.5d |
| B-2 | TryUpgrade 逻辑 | 🔴 | TowerManager/CombatSystem | A-1 | 1.0d |
| B-3 | TowerInfoView 面板 | 🔴 | UIPrefabBuilder/TowerInfoView | B-1,B-2 | 1.5d |
| B-4 | 等级费用联动 | 🟠 | TowerInfoView | B-3 | 0.5d |
| B-5 | 出售返还 + 二次确认 | 🟠 | TowerInfoView/TowerInfo.xlsx | B-3 | 0.5d |
| B-6 | 右键快捷出售口径 | 🟡 | TowerPlacement | B-5 | 0.2d |
| C-1 | 选中态高亮 | 🔴 | BaseTower/Board/CellView | B-1 | 0.5d |
| C-2 | 射程圈 | 🔴 | RangeIndicatorView/BoardSorting | A-4,B-1 | 1.0d |
| C-3 | 误触防护 | 🟠 | TowerPlacement/TowerInfoView | B-3 | 0.5d |
| C-4 | 金币不足与异常态 | 🟠 | BuildBarView/TowerInfoView/HudView | A-4,B-3 | 0.5d |
| C-5 | 数值与手感打磨 | 🟡 | TowerInfoView/HudView | B-4 | 0.5d |

**合计 ≈ 11.2 人日**（含联调返工）

### 4.2 依赖关系

```
      【并行起跑线】
      A-1 配置数据 ──→ A-3 塔型列表 ──┐
      A-2 资源/包名 ──────────────────┤
                                      ↓
                                 A-4 建造栏 UI ──┬──→ A-5 切换塔型
                                                └──→ A-6 连建模式
                                                
      B-1 点击选中 ──→ B-3 面板 ──┬──→ B-4 等级费用联动
      A-1 ──→ B-2 升级逻辑 ───────┘    └──→ B-5 出售确认 ──→ B-6 右键口径
      
      B-1 ──→ C-1 选中高亮
      A-4,B-1 ──→ C-2 射程圈
      B-3 ──→ C-3 误触防护
      A-4,B-3 ──→ C-4 金币不足
```

**建议实施顺序**：`A-1 ∥ A-2` → `A-3` → `A-4` → `B-1 ∥ B-2` → `B-3` → `C-1 ∥ C-2` → `A-5/A-6/B-4/B-5` → `C-3/C-4` → `C-5`

**关键路径**：`A-1 → A-3 → A-4 → B-3 → C-2` ≈ **5.5 人日**
（B-1/B-2 可与 A-4 并行，不在关键路径上）

### 4.3 落地前置（**必须先修**）

以下问题来自仓库现状扫描，会直接阻塞本计划：

| # | 问题 | 影响 | 处理 |
|---|---|---|---|
| 1 | `TowerInfo.xlsx` 无 `type=2/3` 行 | A-3/A-4 无数据可显示 | A-1 必做 |
| 2 | `ResTable` 未登记新塔 | 加载必失败 | A-2 必做 |
| 3 | 塔 prefab 标记 `tower` vs `ResBundle.TowerNormal="tower_normal"` 冲突 | **真机 AB 必炸** | A-2 一并统一 |
| 4 | `Luban/Config/Datas/` 3 个 `~$*.xlsx` 锁文件 | 导出可能报错 | 改表前先删 |
| 5 | `StreamingAssets/AssetBundles/` 仅 Android 旧包 | 验证真 AB 前需重打 | A-2 完成后重打 |

---

## 第五部分　需同步更新的文档

| 文档 | 章节 | 更新内容 |
|---|---|---|
| `Docs/TowerDefense_Design_and_Implementation.md` | §6.2.2 | 建塔流程改为"连建不退出"；补充塔型切换 |
| 同上 | §6.2.4 | 由"升级与出售（M2，表结构已就绪）"改为**已实现**，补 `TryUpgrade` 与二次确认口径 |
| 同上 | §6.8 | `TowerInfoView` 由"M2"改为"✅ 已做"；新增 `BuildBarView` / `RangeIndicatorView` 行 |
| 同上 | §8 M2 | 勾掉"多塔型 / 塔升级与出售"，标注完成日期 |
| 同上 | Z 附录 | 记录本轮新增缺陷（若有）与决策（如升级是"换实例"还是"仅换配置"） |
| `Docs/Unity_Editor_Operation_Guide.md` | §4 快捷键 | 补充：左键选中塔、ESC 分层退出、右键出售口径变更 |
| 同上 | §4 验收清单 | 新增多塔型/升级/出售的验收项 |
| 同上 | §12 已知遗留 | 移除"塔升级/出售 UI 缺接线" |

---

## 第六部分　风险与决策点

| # | 风险 / 待决策 | 说明 | 建议 |
|---|---|---|---|
| R1 | **升级实现方式** | 换实例 vs 仅换配置。换实例复用 `TryBuild` 流程但有一次视觉闪动；仅换配置需保证各等级共用 resName | 默认**换实例**（配置可换皮）；若共用 resName 再优化为"仅换配置" |
| R2 | **`sellPrice` 口径** | 升级后的返还是"当前级 sellPrice"还是"累计投入"？ | 逻辑不改，**靠填表**：每级 sellPrice 写成期望返还额（现有数据已符合） |
| R3 | **连建模式改变 M0 验收行为** | 验收清单第 7 项"建塔"描述可能需修订 | 同步改文档，避免回归时判定不一致 |
| R4 | **射程圈排序值** | 排序过高会遮塔，过低会被格/怪盖住 | 先在 `BoardSorting` 加常量，Play 目视后定值 |
| R5 | **面板与建造态互斥** | 状态管理散在 `TowerPlacement` 易膨胀 | 建议抽 `TowerInteractionState` 枚举（Idle/Building/Selected）**单一状态源**，避免多处判空 |
| R6 | **`TowerPlacement` 职责过载** | 已同时管放置、出售、输入；再加选中/面板控制会更臃肿 | 建议把"选中与面板"拆到新 `TowerSelector`，`TowerPlacement` 只管建造 |
| R7 | **渲染性能** | 建造栏/面板是 UGUI，频繁 `SetActive`/改文本会触发 Canvas Rebuild | 遵守 §6.8：用脏标记，数值变化时才写 `text`；卡片常驻不做增删 |
| R8 | **移动端中文字体** | 新增面板文本同样受 `LegacyRuntime.ttf` 限制 | 出移动包前统一换 TTF（见操作指南 §10） |

---

## 附：与现有代码规范的对照（实现时须遵守）

1. **MonoBehaviour 类名 = 文件名**（否则拿不到 `MonoScript`，Editor 无法序列化进 prefab）
2. **prefab 节点名 ↔ `UIPrefabBuilder.cs` ↔ `*View.cs` 三处成对**，节点查找必须显式报错不静默
3. **事件监听带参回调显式写泛型**：`AddEventListener<int, int>(...)` / `AddEventListener<BaseTower>(...)`
4. **UI 只发事件不持逻辑引用**；战斗逻辑不碰 UGUI
5. **数值全走配置表**，新增塔型/等级只改 xlsx + 重跑 `gen_code_json.bat`
6. **资源逻辑名统一登记 `ResTable`**，路径与真实文件一致
7. **改 xlsx 流程**：编辑 → 保存 → `gen_code_json.bat` → 回 Unity 等导入 → `Tools ▸ 塔防 ▸ 0. 自检` → Play
8. **改 prefab 结构**：`Tools ▸ 塔防 ▸ 一键完成 M0 资源准备` → 自检 → Play
