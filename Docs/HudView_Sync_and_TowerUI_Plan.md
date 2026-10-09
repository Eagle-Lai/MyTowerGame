# HudView 预制体同步说明 + 塔升级/出售「逻辑先行」实施口径

> 编制日期：2026-09-29
> 适用工程：本工程
> 关联文档：`Docs/Tower_Interaction_Dev_Plan.md`（分阶段开发计划）
> 本文性质：**接口契约同步**（不改代码，只固化命名与实施口径）

---

## 一、HudView 预制体现状实测

### 1.1 实测节点树

对 `Assets/Prefabs/UI/HudView.prefab` 做类型/名称扫描后得到：

```
HudView                                  [HudView.cs / guid bdb6610511...]
├── GoldText         Text  "金币 0"        锚(0,1)  pos(40,-30)  size(520×52)  左对齐  32号
├── HpText           Text  "生命 0/0"      锚(0,1)  pos(40,-84)  size(520×52)  左对齐  32号
├── RoundText        Text  "准备中"        锚(0.5,1) pos(0,-30)  size(700×56)  居中    38号
├── StartButton      Button 220×72         锚(0.5,0)  pos(140,60)  子: Label(Text "开始")
├── Btn_Tower_Normal Button 128×128        锚(0.5,0.5) pos(-633,-427)
│   └── Image        Image → sprite guid b9d6ad05651198d4f9b779f1716416eb
├── Btn_Tower_Power  Button 128×128        锚(0.5,0.5) pos(-359,-427)
│   └── Image        Image → sprite guid b148824b0df998444b13140ef3c26ba7
└── Btn_Tower_Retard Button 128×128        锚(0.5,0.5) pos(-123,-427)
    └── Image        Image → sprite guid d2c510517efd5364e9935dbbabb8c228
```

> ⚠️ **重要**：旧的单个 `TowerButton`（含 `TowerButton/Label`）**已被移除**，替换为三个塔型图标按钮。
> HudView.prefab 有 439 行新增、65 行删除的未提交改动。

### 1.2 与代码的严重不一致（**当前必然报错**）

`HudView.cs` 的 `BindNodes()` 仍在查找 `"TowerButton"` 与 `"TowerButton/Label"`：

```csharp
_towerButton = FindButton("TowerButton");          // ← prefab 里已无此节点
_towerLabel  = FindChildText("TowerButton/Label"); // ← prefab 里已无此节点
```

而 `FindButton` 在找不到节点时会 **`Debug.LogError`（显式报错，不静默）**：

> `[HUD] 缺少按钮节点「TowerButton」（prefab 与 HudView.cs 不一致）`

**结论：当前 prefab 与代码处于不一致状态，Play 时 Console 必然出现上述 Error，且建塔按钮事件不会被订阅。**

### 1.3 三个按钮的差异（确认是否是我方编辑）

| 节点 | `m_Layer` | `m_Transition` | 生命周期 |
|---|---|---|---|
| `StartButton` | 0 | 1（ColorTint） | 生成器产出的标准件 |
| `Btn_Tower_*` ×3 | 0 | **0/1 不一，`m_Colors` 为 Unity 默认值** | **手工在 Unity 里拖拽生成** |

`Btn_Tower_*` 的 `m_Colors` 未按 `UIPrefabBuilder.CreateButton` 的约定设置
（生成器用的是 `highlighted=(1.15,1.15,1.15)`/`disabled=(0.5,0.5,0.5,0.6)`，而这三颗是 Unity 默认的
`(0.9607…)/(0.7843…,0.502)`），说明它们**不是由 `UIPrefabBuilder` 生成的**，是编辑器内手工摆放。

**这带来一个风险**：`UIPrefabBuilder.BuildHud()` 开头是 `AssetDatabase.DeleteAsset(HudPath)` ——
**一旦有人执行「Tools ▸ 塔防 ▸ 5. 生成 UI 预制体」或「一键完成 M0 资源准备」，这三个手工按钮会被整份删除。**

### 1.4 三张图标贴图的 GUID 指向

| 节点 | sprite guid | 初步对应 |
|---|---|---|
| `Btn_Tower_Normal/Image` | `b9d6ad05651198d4f9b779f1716416eb` | `_UIAssets/Tower/Normal/turret_base_128.png` |
| `Btn_Tower_Power/Image` | `b148824b0df998444b13140ef3c26ba7` | `Tower_Power.prefab` 也引用同一 guid → 应为 `Power/tower_base.png` |
| `Btn_Tower_Retard/Image` | `d2c510517efd5364e9935dbbabb8c228` | 应为 `retard/slowtower_base.png` |

> ✅ `Btn_Tower_Power` 的 sprite guid 与 `Tower_Power.prefab` 里的 `m_Sprite` 一致 ——
> **确认这三个按钮就是为三塔型准备的建造入口，不是误放。**

---

## 二、统一后的命名契约（**实现时必须严格遵守**）

三个按钮都**没有 Label 子节点**（纯图标，这是合理的 —— 原作也是图标塔栏）。
命名采用 `Btn_Tower_<TypeName>`，与 `TowerType` 枚举一一对应：

| `TowerType` 枚举 | 值 | 按钮节点名 | 状态 |
|---|---|---|---|
| `Normal` | 1 | `Btn_Tower_Normal` | ✅ 已存在 |
| `Power` | 2 | `Btn_Tower_Power` | ✅ 已存在 |
| `Slow` | 3 | `Btn_Tower_Retard` | ✅ 已存在 |

**契约规则**

1. **按钮名 = `Btn_Tower_` + `TowerType` 枚举名**（注意 `Slow=3` 对应节点 `Btn_Tower_Retard`，
   节点名用的是美术名 Retard，**不是枚举名 Slow** —— 这一处不一致按现有 prefab 为准，
   并在 `BuildBarView` 里用**显式映射表**落地，不要靠字符串推导）
2. **按钮不配 Label**；后续如需显示价格，在按钮下新增 `PriceText` 子节点，而不是复用 Label
3. 三个按钮**同一父节点（HudView 根）**，平级；不新增 `BuildBar` 中间层
   （避免再次与生成器结构冲突，也少一次 Canvas 层级变动）
4. 新增/删除塔型时：**`UIPrefabBuilder` 与 `HudView.cs` 与 prefab 三处同时改**

### 2.1 建议的映射表落地方式（实现参考，非本次交付）

```csharp
// HudView.cs 内，显式映射，避免"节点名推导"踩 Retard/Slow 不一致的坑
private static readonly (int type, string btnName)[] TowerButtons =
{
    (1, "Btn_Tower_Normal"),
    (2, "Btn_Tower_Power"),
    (3, "Btn_Tower_Retard"),
};
```
若按钮数量会增长，再改为从配置表 `level==1` 的行生成（但**节点名仍需显式映射**，
因为 `resName` 与 `TowerType` 枚举名不一定同形）。

---

## 三、"逻辑先行"实施口径（核心决策）

> **用户决策**：防御塔升级 UI 资源尚未准备，因此
> **本轮先只提升逻辑（数据 / 服务 / 事件 / 状态机），UI 表现层留空位，
> 待美术资源补齐后以最小改动接入。**

### 3.1 分层与"可先做 / 必须等资源"对照

| 层 | 内容 | 能否现在做 | 说明 |
|---|---|---|---|
| **配置数据** | `TowerInfo.xlsx` 补 type=2/3 各级行、`upgradeTo` 链、`sellPrice` | ✅ **可先做** | 纯数据，无美术依赖 |
| **资源登记** | `ResTable` / `ResBundle` 补三塔逻辑名与包名统一 | ✅ **可先做** | 只需路径 |
| **服务层** | `TowerManager.TryUpgrade(tower)` | ✅ **可先做** | 纯逻辑 |
| **事件层** | 新增 `UpgradeTowerSuccess` / `UpgradeTowerFail` / `SellTowerRequestEvent` 等 | ✅ **可先做** | `EventName.cs` 常量 |
| **状态机** | `TowerInteractionState { Idle, Building, Selected }` | ✅ **可先做** | 纯逻辑 |
| **选中逻辑** | 点击塔 → `TowerSelectedEvent(BaseTower)` | ✅ **可先做** | 不依赖面板，事件先通 |
| **建造栏接线** | `HudView` 绑定三个 `Btn_Tower_*` → 发 `BuildTowerRequestEvent(type,1)` | ✅ **可先做** | **图标 prefab 已在**，无需新资源 |
| **射程圈** | `RangeIndicatorView`（可先用生成的占位圆贴图） | 🟡 **可先做占位** | `PlaceholderArtGenerator` 可生成圆 |
| **升级/出售面板视觉** | `TowerInfoView` 的底板/图标/按钮**美术** | ❌ **必须等资源** | 缺升级 UI 图 |
| **面板交互骨架** | `TowerInfoView` 脚本 + 逻辑名 + 事件绑定 | ✅ **可先做（不挂资源）** | 用纯色 `Image` 占位即可跑通 |

**结论**：**除"面板美术皮肤"外，其余全部可以先做。**
面板本身可以用 **纯色 `Image` 占位**（现有 `UIPrefabBuilder.CreateButton` 就是这么做的 ——
`sprite` 为空时 `Image` 画纯色矩形），跑通交互后再换皮，**换皮时不需要动任何逻辑代码**。

### 3.2 关键解耦要求（为将来换 UI 资源预留）

为了"资源补齐后只改 prefab、不改代码"，本轮逻辑实现必须遵守：

| # | 要求 | 理由 |
|---|---|---|
| 1 | `TowerInfoView` **只按节点名查找**（`transform.Find`），不缓存 sprite 引用 | 换皮只改 prefab 的 sprite 字段 |
| 2 | 图标刷新走**逻辑名 → `ResLoader`**，不在代码里写死 sprite guid | 换图只需改 `ResTable` 一行 |
| 3 | 面板的**布局参数不在代码里写死**（宽高/位置由 prefab 决定） | 美术改版不碰代码 |
| 4 | 按钮状态（可点/置灰/文案）由**代码只改状态**，视觉由 prefab 的 `ColorBlock` 表达 | 换皮肤自然继承 |
| 5 | 所有文案集中在 `TowerInfoView` 顶部的常量或 `TBAudio`/语言表**（建议后者，M3）** | 便于统一改文案 |
| 6 | 升级/出售**必须走事件**（`UpgradeTowerRequestEvent` 等），不由 View 直接调 `TowerManager` | 与 §6.8「UI 与战斗解耦」一致，也便于将来换 View |

### 3.3 新增逻辑名（需登记 `ResTable` + `ResBundle.UiHud`）

| 逻辑名 | 路径 | 何时需要 |
|---|---|---|
| `TowerInfoView` | `Assets/Prefabs/UI/TowerInfoView.prefab` | 面板骨架阶段（可先用纯色占位） |
| `Range_Ring` | `Assets/Art/Generated/Range_Ring.png` | 射程圈（占位圆，后续可换美术） |
| `Tower_Icon_Normal` | `Assets/_UIAssets/Tower/Normal/turret_base_128.png` | 面板图标 |
| `Tower_Icon_Power` | `Assets/_UIAssets/Tower/Power/tower_base.png` | 面板图标 |
| `Tower_Icon_Retard` | `Assets/_UIAssets/Tower/retard/slowtower_base.png` | 面板图标 |

> ⚠️ 面板图标贴图的 `m_TextureType` 必须是 `Sprite (2D and UI)`，
> 否则 `EditorResLoader` 会报「是图片，但未以 Sprite 形式导入」（操作指南 §11 有该坑记录）。

---

## 四、HudView 改造任务（同步 prefab 与代码）

### H-1 🔴 `HudView.cs` 适配三塔按钮（**修复当前必然报错**）

- **改什么**：`BindNodes()` 不再查找 `TowerButton`/`TowerButton/Label`，
  改为遍历 2.1 的映射表绑定三颗按钮，各自 `onClick` 发
  `BuildTowerRequestEvent(type, 1)`（把 `type` 作为闭包参数捕获）
- **涉及**：`Assets/Scripts/UI/HudView.cs`
- **验收**：
  1. Play 时 Console **无** `[HUD] 缺少按钮节点「TowerButton」`
  2. 点 `Btn_Tower_Normal` → Console/事件可观察 `BuildTowerRequestEvent(type=1, level=1)`
  3. 点 `Btn_Tower_Power` → `type=2`；点 `Btn_Tower_Retard` → `type=3`
  4. `_towerType`/`_towerLevel` 硬编码字段移除，改为点击时传参

### H-2 🔴 `UIPrefabBuilder.BuildHud()` 同步生成三按钮（**防踩踏**）

- **为什么**：当前 `BuildHud()` 会 `DeleteAsset` 整个 prefab，
  **执行一次就抹掉手工摆的三颗按钮**。必须把三按钮纳入生成器（幂等）
- **改什么**：
  - `BuildHud()` 改为生成 `GoldText/HpText/RoundText/StartButton` + 三颗 `Btn_Tower_*`
  - 三按钮 `Image.sprite` 从 `ResTable` 逻辑名加载（或至少写注释标明应挂哪张图）
  - 保持现有坐标 `(-633,-427) / (-359,-427) / (-123,-427)`、`128×128`
  - 按钮 `ColorBlock` 采用统一约定（`highlighted=(1.15)…`、`disabled=(0.5,0.5,0.5,0.6)`）
- **涉及**：`Assets/Editor/UIPrefabBuilder.cs`
- **验收**：
  1. 执行「5. 生成 UI 预制体」后，prefab 仍为 **7 个直接子节点**（3 文本 + 1 开始 + 3 塔按钮）
  2. 连续执行两次，结果一致（幂等，不累加、不丢失）
  3. 生成后 Play，Console 无节点缺失报错
  4. **执行「一键完成 M0 资源准备」不再破坏手工布局**

### H-3 🟠 选中态与金币态表达（复用现有按钮）

- **改什么**：
  - 三颗塔按钮增加"当前选中"表达（`Button.interactable` 保持 true，
    另用 `Image.color` 或启用 `m_SpriteState.m_SelectedSprite` 做描边；**优先用 SpriteState，不改代码**）
  - 金币不足时置灰：三颗按钮各自判断自己的 `type` 对应 L1 价格
- **涉及**：`Assets/Scripts/UI/HudView.cs`（只改状态）、`UIPrefabBuilder.cs`（SpriteState）
- **验收**：
  1. 进入建造态后对应按钮显示选中态，退出后复位
  2. 金币 < 某塔价格时该按钮置灰且不可点；金币回升自动恢复
  3. 置灰状态点击无任何副作用

### H-4 🟡 按钮角标与 Tooltip（可选，等美术）

- **内容**：按钮右下角显示价格、悬停显示塔名与数值
- **状态**：🟡 **等 UI 资源**，本轮不做

---

## 五、升级/出售「逻辑先行」任务

### L-1 🔴 事件定义扩展（`EventName.cs`）

新增（`TowerSelectedEvent`/`TowerDeselectedEvent` 已存在，直接用）：

| 新事件名 | 参数 | 用途 |
|---|---|---|
| `UpgradeTowerRequestEvent` | `<BaseTower>` | UI → 逻辑：请求升级 |
| `SellTowerRequestEvent` | `<BaseTower>` | UI → 逻辑：请求出售 |
| `UpgradeTowerSuccess` | `<BaseTower>` | 逻辑 → UI：升级完成，刷新面板 |
| `UpgradeTowerFail` | `<string>`（原因） | 逻辑 → UI：升级失败（金币不足/满级） |
| `TowerSellConfirmed` | `<BaseTower, int>` | 逻辑 → UI：出售完成（塔 + 返还额） |

- **验收**：常量已定义；`check_events.py` 校验通过（Trigger/Add 的 arity 一致）

### L-2 🔴 `TowerManager.TryUpgrade(BaseTower)` 逻辑实现

```
TryUpgrade(tower):
  1. tower 无效 / Config==null / !IsBuilt / IsMaxLevel  → 返回 false + UpgradeTowerFail
  2. nextCfg = Configs.GetTower(tower.Config.UpgradeTo)
  3. PlayerDataManager.TrySpend(nextCfg.Prices)
       失败 → Tips「金币不足」+ UpgradeTowerFail，返回 false（★ 不扣费不换塔）
  4. 记录原 cell / 原注册状态
  5. 实例化 nextCfg.ResName（失败 → 退还金币 + 保留原塔）
  6. 新塔 Init(nextCfg, cell) + SnapToCell(cell)
  7. 清理旧塔：cell.Tower 指向新塔；CombatSystem 注销旧的、注册新的
  8. 触发 UpgradeTowerSuccess(newTower)；AStar 无需重算（仍占同一格，墙状态未变）
```

- **待决策（R1）**：**换实例**（推荐，可换 resName 换皮）vs **仅换配置**（无闪动，需同级共用 resName）
  → 建议先实现"换实例"，并在 `TowerInfo.xlsx` 里让三等级**共用同一 resName**（当前 NormalTower 即如此），
  则视觉效果与"仅换配置"等价，且代码路径与 `TryBuild` 统一
- **注意**：升级**不应**触发路径重算（格子占用不变），避免怪物无谓改道
- **验收**：
  1. L1→L2 后 `Config.Level==2`，伤害/射程/CD 与表 L2 行一致
  2. 金币正确扣 `L2.prices`；不足时**不升级、不扣费、塔保持 L1**
  3. 满级时返回 false 并发 `UpgradeTowerFail("已满级")`
  4. 升级后塔仍在原格、仍能索敌开火（CombatSystem 注册未丢）
  5. 升级后怪物路径未被重置（不触发无谓改道）
  6. 资源加载失败时金币已退还、原塔仍在

### L-3 🔴 交互状态机（单一状态源）

新增 `TowerInteractionState { Idle, Building, Selected }`，避免状态散落：

| 事件 | 状态迁移 |
|---|---|
| 点塔按钮且金币足 | `Idle → Building` |
| 建造成功（连建）/ 点同按钮 / 右键 / ESC | `Building → Idle`（或保持 Building） |
| 点已建塔 | `Idle → Selected` |
| 点空地 / ESC / 面板关闭 | `Selected → Idle` |
| `Building` 时点塔 | 忽略（不进入 Selected） |

- **建议**：把该状态放在**新增的 `TowerInteractionController`**，
  `TowerPlacement` 只管建造、`TowerSelector` 只管选中，控制器负责互斥
  （现状 `TowerPlacement` 已同时管放置+出售+输入，再加会过载 —— 见计划文档 R6）
- **验收**：
  1. 状态组合互斥，任何时刻只有一个非 Idle 态
  2. 建造态点塔不弹面板；选中态点塔按钮先退出选中再进建造
  3. ESC 分层退出：面板 → 建造态 → 选中态

### L-4 🔴 `TowerInfoView` 骨架（**纯色占位，不依赖美术**）

- **内容**：新建 prefab + 脚本，节点按最终结构搭好，但**外观全用纯色 `Image` 占位**
  ```
  TowerInfoView
  ├── Panel            Image（纯色半透明底，占位）
  │   ├── TitleText    塔名 + Lv.
  │   ├── IconImage    Image（挂 ResLoader 逻辑名图标，或先留空）
  │   ├── StatText     伤害/射程/攻速/DPS
  │   ├── UpgradeButton → Label   「升级  ¥30」
  │   ├── SellButton    → Label   「出售  +¥14」
  │   └── CloseButton   → Label   「×」
  ```
- **解耦要求**：见 §3.2 的 6 条（只按节点名查找、图标走逻辑名、布局不写死代码等）
- **验收**：
  1. 点塔弹出面板（占位底板可辨识），点「×」/空地/ESC 关闭
  2. 面板打开时点击面板区域不穿透到棋盘
  3. 标题/数值与所选塔配置一致；升级后数值刷新
  4. 关闭后 `UIManager.IsOpen("TowerInfoView")==false`
  5. **换皮验证**：仅替换 prefab 里的 sprite / 布局参数，**不改任何 .cs**，面板仍正常工作

### L-5 🟠 出售确认（逻辑先行，视觉待美术）

- **内容**：按钮原地变「确认出售？」，3 秒超时复位（不弹二级窗口）
- **验收**：首次点不执行；再点执行并返还；超时自动复位；返还额与 `sellPrice × SellRefundRate` 一致

### L-6 🟠 射程圈（占位圆先行）

- **内容**：世界空间 `SpriteRenderer` 圆，建造态/选中态显示，半径 = `radius × cellSize`
- **占位**：由 `PlaceholderArtGenerator` 生成圆环贴图，逻辑名 `Range_Ring`
- **验收**：半径随塔型/等级变化；退出后消失；连续切换无泄漏；**换正式美术只改 `ResTable` 一行**

### L-7 🟡 面板正式美术接入（**等资源**）

- **内容**：拿到升级 UI 资源后，替换 `TowerInfoView.prefab` 的底板/图标/按钮皮肤，调整布局
- **验收**：§L-4 全部验收项在换皮后仍通过；**零代码改动**（用 `git diff --stat` 确认无 `.cs` 变更）

---

## 六、文档同步清单

| 文档 | 章节 | 更新 |
|---|---|---|
| `Docs/Tower_Interaction_Dev_Plan.md` | A-4 / B-3 | 建造栏按钮命名由"`BuildBar/Slot_{type}`"订正为**已存在的 `Btn_Tower_*`**；补 H-1~H-4 与 L-1~L-7 |
| 同上 | §1.3 | 补记"HudView 已手工改造为三塔按钮，`HudView.cs` 未同步" |
| 同上 | §4.3 | 前置项新增：**`UIPrefabBuilder` 会删掉手工按钮**（H-2） |
| `Docs/TowerDefense_Design_and_Implementation.md` | §6.8 | `TowerInfoView` 行补"逻辑先行、视觉待资源"说明 |
| 同上 | Z 附录 | 记录"升级先做逻辑、UI 资源后补"的决策与理由 |
| `Docs/Unity_Editor_Operation_Guide.md` | §9 目录地图 | 补 `TowerInfoView.prefab` |
| 同上 | §11 故障排查 | 新增一行：Console 报 `缺少按钮节点「TowerButton」` → 执行 H-1 |

---

## 七、执行顺序建议

```
① H-2 让生成器纳入三按钮   ← 必须先做，否则任何人跑一次向导就丢按钮
② H-1 HudView.cs 适配三按钮 ← 修掉当前必然报错
③ L-1 事件扩展
④ L-3 交互状态机骨架
⑤ L-2 TryUpgrade 逻辑      ← 先于面板，可单独用日志验证
⑥ L-4 TowerInfoView 骨架（纯色占位）
⑦ L-5 出售确认 + L-6 射程圈（占位圆）
⑧ L-7 换正式 UI 资源（等美术到位，零代码）
```

**可先做占比**：H-1/H-2/H-3 + L-1~L-6 共 10 项 = **本轮可完成**；
仅 **L-7（面板美术皮肤）** 与 **H-4（按钮角标/Tooltip）** 需等 UI 资源。
