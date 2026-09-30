# 塔防交互开发计划 · 更新版 v2

> 编制日期：2026-09-29（v2 更新）
> 适用工程：`D:\FreedomTower_1`
> 本版变更：
>   ① **升级实现方式定案 = 「换实例」**（原计划 R1 待决策项，现关闭）
>   ② 新增 **编辑器菜单破坏性操作治理**（删除/收口危险入口）
>   ③ 修正计划中与实测不符的部分（HudView 三按钮已存在、生成器会踩踏）
> 前置文档：`Docs/Tower_Interaction_Dev_Plan.md`（v1）、`Docs/HudView_Sync_and_TowerUI_Plan.md`

---

## 第零部分　执行进度（2026-09-29 更新）

### 0.1 已完成

| 编号 | 任务 | 状态 | 产物 |
|---|---|---|---|
| **M-1** | 一键向导改"检查并补缺" | ✅ 完成 | `M0SetupWizard.RunAll` 改名「一键补齐 M0 资源（安全：只补缺失）」；场景步骤改调 `EnsureOrBuildInternal`（已存在则跳过）；`CheckUiPrefab` 节点表同步为三塔按钮 |
| **M-2** | 塔转换收口 + 覆盖三塔 | ✅ 完成 | `TowerPrefabConverter` 三塔循环（Normal/Power/Retard）；`IsAlreadyConverted` 已合规即跳过；备份仅首次。贴图名逐塔指定（Power=`tower_base/barrel`，Retard=`slowtower_base/crystal`，目录小写 `retard`） |
| **M-3** | UI 生成器纳入三塔按钮 + 防误删 | ✅ 完成 | `UIPrefabBuilder` 新增三塔按钮（`-633/-359/-123, -427`，`128×128`）+ `IsSafeToRebuild` 护栏；新增 `TowerInfoView` 生成 |
| **M-4** | 场景搭建拆"补缺/重建" | ✅ 完成 | `SceneMainBuilder` 新增 `EnsureOrBuildInternal`（安全）；原 `Build` 改名为「重建 main 场景（危险：会清空重建）」+ 强确认 |
| **M-5** | 8c 清标记限定 ResTable 范围 | ✅ 完成 | `ABNameSetter.ClearAll` 只遍历 ResTable 登记路径 |
| **M-6** | 一级菜单收口 + 高级子菜单 | ✅ 完成 | 单步重建工具全部移入 `Tools ▸ 塔防 ▸ 高级（单步重建）`；一级菜单 7 项 |
| **A-1** | 补塔配置数据（3 型 × 3 级） | ✅ 完成 | `TowerInfo.xlsx` 追加 id 4~9；Luban 已重新导出（`tbtowerinfo.json` 9 行） |
| **A-2** | 资源登记 + AB 包名统一 | ✅ 完成 | `ResBundle` 加 `TowerPower`/`TowerRetard`；`ResTable` 登记三塔 prefab + 贴图 + `TowerInfoView` |
| **A-4** | `HudView.cs` 适配三按钮 | ✅ 完成 | 三按钮数组 + 金币不足置灰 + `Retard↔Slow` 显式映射 |
| **B-1** | 点击选中塔 | ✅ 完成 | `TowerPlacement` 新增 `Select`/`Deselect`/`HandleSelectClick`；右键改"取消选中"（不再直接卖） |
| **B-2** | `TryUpgrade` 逻辑（换实例） | ✅ 完成 | `TowerManager.TryUpgrade`：先扣费→摘注册→释放旧→实例化新→重 `Init`+`SnapToCell`→注册→**不触路径重算** |
| **B-3** | 面板骨架（纯色占位） | ✅ 完成 | 新增 `TowerInfoView.cs` + `UIPrefabBuilder.BuildTowerInfo`；纯色块、缺节点容错 |
| **B-4** | 等级费用联动 | ✅ 完成 | 面板按 `upgradeTo` 链取下一级、显示费用与可用性 |
| **B-5** | 出售返还 | ✅ 完成（简化） | 面板出售按钮 → `TowerSellRequestEvent` → `TowerManager.Sell`；返还文案 `sellPrice × SellRefundRate`。**二次确认 UI 待美术** |
| **C-4** | 金币不足统一刷新 | ✅ 完成 | `HudView.RefreshTowerAffordability` + `TowerInfoView.RefreshButtons`，均订阅 `GoldChangeEvent` |
| **L-1** | 事件扩展（升级/出售） | ✅ 完成 | `EventName` 新增 `TowerUpgradeRequestEvent`/`TowerUpgradeSuccess`/`TowerSellRequestEvent` |
| **辅助** | 新增塔子类 | ✅ 完成 | `PowerTower.cs` / `RetardTower.cs`（空子类，命名与文件一致） |
| **辅助** | 清理锁定文件 | ✅ 完成 | 删除 3 个 `~$*.xlsx` |

### 0.2 未完成（待美术 / 后续）

| 编号 | 任务 | 状态 | 说明 |
|---|---|---|---|
| A-3 | 塔型列表（从表遍历） | ⏳ 部分 | 目前三塔按钮 type 硬编码为 1/2/3；金额足够时后续改成遍历 TBTowerInfo 去重 |
| A-5 | 切换塔型 | ✅ 隐含完成 | 点不同 `Btn_Tower_*` 即换 type（`HudView.OnClickTower(type)`），无需额外工作 |
| A-6 | 连建模式 | ⏳ 未做 | 当前建完即退出放置态，符合 M0 行为（R3 需同步文档） |
| B-6 | 右键出售口径统一 | ✅ 完成 | 右键已改"取消选中"，出售只走面板 |
| C-1 | 选中态高亮 | ⏳ 未做 | `TowerPlacement.ClearSelectionHighlight` 留空占位，待描边资源 |
| C-2 | 射程圈（占位圆） | ⏳ 未做 | 待 `RangeIndicatorView` + 贴图 |
| C-3 | 误触防护 + ESC 分层 | ⏳ 部分 | ESC 在放置态取消放置、非放置态取消选中；面板层级确认尚未做 |
| C-5 | 数值与手感打磨 | ⏳ 未做 | 待美术齐后统一调 |
| L-2 | 交互状态机单一状态源 | ⏳ 部分 | 现由 `TowerPlacement` 兼任选中态；`R6` 建议后续拆 `TowerSelector` |
| L-3 | 解耦要求落地（6 条） | ⏳ 部分 | 面板不持业务引用已达成；其余随美术接入补齐 |
| L-4 | 出售返还口径（填表） | ✅ 完成 | 三塔三级 `sellPrice` 已填（见 `TowerInfo.xlsx`） |
| L-7 | 面板正式美术接入 | ⏳ 待资源 | 换 prefab 即可，`.cs` 不改 |
| H-4 | 按钮角标 / Tooltip | ⏳ 待资源 | 待美术 |

### 0.3 实测修正（与 v2 计划不符处）

1. **塔 prefab 已存在**：`Tower_Power.prefab` / `Tower_Retard.prefab` 已在工程中（非计划假设的"待生成"）
2. **美术目录名是小写 `retard`**（计划里写的是 `Retard`）；三塔贴图文件名各不相同，无法用统一模板拼路径
3. **`tbtowerinfo.json` 原本只有 type=1 的 3 行** → A-1 补 6 行后为 9 行

### 0.4 编译错误修复记录

| 项 | 内容 |
| --- | --- |
| 报错 | `M0SetupWizard.cs(227,95)(230,64): error CS0117: 'TowerPrefabConverter' does not contain a definition for 'TargetPath'` |
| 根因 | M-2 重写把「单塔常量 `TargetPath`」换成「多塔 `Specs()` 数组」，但 M-1 改的 `CheckPrefabs` 仍在引用旧常量 —— 两笔改动**接口脱节** |
| 修复 | ① `TowerPrefabConverter` 补公共入口 `TowerResNames[]` + `TowerPath(resName)`；② `M0SetupWizard` 抽出 `CheckOneTower`，三塔遍历自检；③ 根组件校验放宽为「挂了 `BaseTower` 及其子类」 |
| 定位手段 | 读 Unity 编辑器日志 `%LOCALAPPDATA%\Unity\Editor\Editor.log` → `grep "error CS"`（沙箱不能起 Unity/dotnet，这是唯一可靠路径） |
| 验证 | 括号配平 + 新符号存在性 + 旧符号残留=0 + 编辑器脚本跨类成员引用扫描，全部通过 |

---

## 第一部分　决策定案

### 1.1 【已定】升级实现方式 = 换实例

**决策**：`TowerManager.TryUpgrade` 采用 **销毁旧实例 → 实例化新 prefab → 承接格子与战斗注册** 的方式。

**理由**
1. 与 `TryBuild` **复用同一套实例化/注册/吸附流程**，代码路径统一，回归面小
2. 各等级可指向**不同 `resName`** → 将来 L2/L3 换更华丽的塔外观**零改动**
3. `TowerInfo.xlsx` 三级**先共用同一 `resName`**，则视觉与"仅换配置"等价 → 既不闪变、又保留换皮余地

**实现要点（定案细节）**

| 环节 | 做法 |
|---|---|
| 扣费时机 | **先校验 → 扣费 → 实例化**；实例化失败则**退还金币**并保留原塔（与 `TryBuild` 的回滚风格一致） |
| 格子承接 | `cell.Tower = newTower`；`cell.Point` 沿用（格子占用不变） |
| 战斗注册 | `CombatSystem.UnregisterTower(old)` → `RegisterTower(new)`；**顺序不能反**（先注册后注销会短暂双份 tick） |
| 路径重算 | **不触发**。格子占用未变，墙状态未变 → 触发 `RequestRefresh()` 只会让怪物无谓改道 |
| 旧塔清理 | `ResLoader.Instance.ReleaseInstance(oldCfg.ResName, oldGo)`（与 `Sell` 同款释放） |
| 视觉衔接 | 新旧塔贴图相同时，天然无感；若 resName 不同，可加一次极短缩放过渡（P2，可选） |

> ⚠️ **注意**：`BaseTower.Cell` 是 `private set`，`TowerManager` 通过 `Init(cfg, cell)` 注入；
> 新塔必须重新 `Init(nextCfg, cell)` + `SnapToCell(cell)`，**不能只改 `Config`**（`_renderers`/`_barrel`/`_muzzle` 缓存需按新 prefab 重建）。

### 1.2 【已定】命名契约（承接上一份文档）

- 建造入口按钮：`Btn_Tower_Normal(1)` / `Btn_Tower_Power(2)` / `Btn_Tower_Retard(3)`
- ⚠️ `Retard` 对应枚举 `Slow` → **必须用显式映射表，禁止字符串推导**
- 图标按钮**无 Label 子节点**；需要价格时另加 `PriceText`

---

## 第二部分　编辑器菜单治理（**本版新增，优先执行**）

### 2.1 现状：`Tools ▸ 塔防` 全部入口盘点（实测）

| # | 菜单项 | 优先级 | 破坏性 | 判断 |
|---|---|---|---|---|
| 0 | `0. 自检（先跑这个）` | 9 | 🟢 只读 | **保留**（每次改完必跑） |
| 1 | `一键完成 M0 资源准备` | 10 | 🔴🔴 **极高** | **收口**（见 2.2） |
| 2 | `1. 生成占位美术` | 100 | 🟠 覆盖 `Art/Generated` | 保留（受控产出目录） |
| 3 | `2. 转换防御塔预制体` | 101 | 🔴 **高** | **危险，需收口**（见 2.3） |
| 4 | `3. 生成战斗预制体` | 102 | 🔴 覆盖子弹+怪物 | 合并进向导，单列降级 |
| 5 | `4. 清理选中预制体的物理组件` | 103 | 🟠 改选中资源 | 保留（有选中前提） |
| 6 | `4b. 清理全部战斗预制体的物理组件` | 104 | 🟠 批量改 119 个 | 保留 |
| 7 | `5. 生成 UI 预制体` | 105 | 🔴🔴 **极高** | **必须改**（见 2.4） |
| 8 | `6. 配置工程设置` | 106 | 🟠 改 ProjectSettings | 保留 |
| 9 | `7. 搭建 main 场景` | 107 | 🔴 **极高** | **危险，需收口**（见 2.5） |
| 10 | `8a. 按 ResTable 打 AssetBundle 标记` | 110 | 🟠 改 .meta | 保留 |
| 11 | `8b. 打包 AssetBundle` | 111 | 🟢 只读源码、写产物 | 保留 |
| 12 | `8b-严格模式 打包` | 113 | 🟢 | 保留 |
| 13 | `8c. 清除全部 AssetBundle 标记` | 112 | 🔴 清空全工程标记 | **危险，需收口** |
| 14 | `9. 导入全部怪物` | 108 | 🔴 覆盖 119 个怪物 prefab | 合并进向导，单列降级 |
| 15 | `10. 导出配置表（Luban）` | 109 | 🟠 覆盖 `ConfigJson` | 保留 |

**核心结论：14 个入口里，真正"会静默破坏手工工作成果"的是 4 个** ——
`一键向导`、`2. 转换防御塔预制体`、`5. 生成 UI 预制体`、`7. 搭建 main 场景`，
另有 `8c. 清除全部标记` 属"范围过大"型危险。

### 2.2 🔴 M-1　`一键完成 M0 资源准备` 收口（最高优先）

**现有破坏链**（从上到下全部会执行）：
```
DeleteAsset(HudView.prefab)          ← 删掉手工三塔按钮
DeleteAsset(TipsView.prefab)
DeleteAsset(Tower_Normal.prefab)     ← 删掉手工调过的塔 prefab
DeleteAsset(Bullet/Enemy prefab × 120)
DeleteAsset(TargetPath)              ← 场景：清空全部根对象后重建
DeleteAsset/覆盖 main.unity          ← 手工在场景里调的一切都丢
```

**改造方案（三选一，建议 A+C 组合）**

| 方案 | 做法 | 评价 |
|---|---|---|
| **A. 降级为"检查 + 补缺"** | 每步先判产物是否存在且结构合规，**已存在且合规就跳过**，只补缺失项 | ✅ **推荐** |
| B. 加二次确认 + 列出将被覆盖的文件清单 | 保住现状，只提升知情度 | 治标 |
| **C. 从菜单移除，仅保留自检** | 向导改由 `Tools ▸ 塔防 ▸ 自检` 报告里的"一键修复"按钮触发 | ✅ 配合 A 使用 |

**推荐落地**：
1. `M0SetupWizard.RunAll` 改为 **"按需补缺"** —— 每步调用前先检查，已合规则 `report.Skip("已就绪，跳过")`
2. 用户已手工改造过的产物（HudView / Tower prefab / main.unity）**默认不被覆盖**
3. 菜单项文案改为 **`一键检查并补缺资源（不覆盖已就绪产物）`**，priority 保持 10 或降到 11
4. 确需强制重建时，走**独立**的 `强制重建全部资源（危险）` 菜单 + 强确认弹窗

- **涉及**：`Assets/Editor/M0SetupWizard.cs`（主）、各 `*Internal` 返回值改为"是否已就绪"
- **验收**：
  1. 在**已手工改造过 HudView/Tower/main.unity** 的工程上执行向导，上述三者**内容不变**（可用 `git diff --stat` 验证无变化）
  2. 缺失产物（如删掉 `Cell_Ground.png`）仍能被自动补齐
  3. 报告里能清晰看到"✔ 已就绪跳过 / ✔ 已补齐 / ✘ 失败"三类

### 2.3 🔴 M-2　`2. 转换防御塔预制体` 收口

**现状**：`ConvertInternal` 开头 `AssetDatabase.DeleteAsset(TargetPath)`，**无条件重建**。
虽然会 `BackupSource` 备份到 `_UI_Source/`，但：
- 备份是**一次性**的（先删再写，重复执行会覆盖备份）
- 三塔时代，`TargetPath` 只指 `Tower_Normal` → **`Tower_Power` / `Tower_Retard` 完全不在覆盖范围内**，
  一旦有人手工调过这两座塔，跑向导也不受影响（但 `Tower_Normal` 会被打回生成器版本）

**改造方案**
1. 增加 **`Tower_Normal` / `Tower_Power` / `Tower_Retard` 三塔循环**（当前只处理 Normal）
2. 每塔转换前先检测：**若已合规（有 `barbette/Img_gun/BarrelPoint` + 挂 `BaseTower` 派生类 + 无 `RectTransform`）→ 跳过**
3. 备份改为**带时间戳/仅首次**，避免反复覆盖唯一备份
4. 菜单文案补 `（已就绪的塔会跳过）`

- **涉及**：`Assets/Editor/TowerPrefabConverter.cs`、`ResTable`（三塔贴图路径）
- **验收**：
  1. 已合规的塔执行后**文件无变化**（`git diff` 为空）
  2. 三座塔都在处理范围内（报告列出 ×3）
  3. 不合规的塔仍能被正确转换

### 2.4 🔴 M-3　`5. 生成 UI 预制体` 收口（**当前已造成实际丢失风险**）

**现状**：`BuildHud()` / `BuildTips()` 均 `AssetDatabase.DeleteAsset(...)`。
**实测证据**：`HudView.prefab` 已被手工改造为三塔按钮，但生成器**仍只生成单 `TowerButton`** ——
执行一次即 **`DeleteAsset` 抹掉三颗按钮**（已在上一份文档记为 H-2）。

**改造方案（与 H-2 合并执行）**
1. `BuildHud()` 纳入三颗 `Btn_Tower_*`（保持坐标 `(-633,-427)/(-359,-427)/(-123,-427)`、`128×128`）
2. `BuildTips()` 无手工改造，保持现状即可
3. **生成前检测**：若 prefab 已存在且"节点集合与生成器预期一致"→ 仍重新生成（幂等）；
   若**发现生成器不认识的节点**（如未来又手工加了东西）→ **中止并提示**，不静默删除
4. 菜单文案补 `（会重建 UI prefab，手工新增的节点请先确认）`

- **涉及**：`Assets/Editor/UIPrefabBuilder.cs`
- **验收**：
  1. 连续执行两次结果一致（幂等）
  2. 生成的 prefab 含三塔按钮；Play 时 `HudView.cs` 不再报"缺少节点"
  3. 若 prefab 含生成器未知节点，**中止并报明确错误**，不做破坏性删除

### 2.5 🔴 M-4　`7. 搭建 main 场景` 收口

**现状**：备份后 `DestroyImmediate` **清空全部根对象**再重建。
场景里任何手工调整（相机位置、节点层级、Inspector 上的引用手动修正）**全部丢失**。
`M0SetupWizard` 第 8 步会调用它 → 属于"跑一次向导就重置场景"。

**改造方案**
1. **默认改为"检查并补缺"**：逐项检查 16 个必需对象，缺哪个建哪个，**已存在的不动**
2. 保留现有"全量重建"为**独立危险入口**：`7b. 重建 main 场景（危险：清空场景）`
3. 危险入口加**强确认**（要求输入确认文本或明确的红色警示弹窗），并提示备份路径
4. 菜单文案：`7. 检查并补全 main 场景`（安全）/ `7b. 重建 main 场景（危险）`

- **涉及**：`Assets/Editor/SceneMainBuilder.cs`、`M0SetupWizard.cs`
- **验收**：
  1. 手工在场景里挪动 `Camera` 后执行安全版，**相机位置保持**，且缺失对象被补上
  2. 危险版仍能产出可运行场景，且执行前有明确警示
  3. 两种入口的 Console 报告分别标明"补缺/重建"

### 2.6 🟠 M-5　`8c. 清除全部 AssetBundle 标记` 收口

**现状**：`FindAssets(string.Empty, Assets)` 全工程清空，范围过大。
**改造**：改为**只清除 `ResTable` 已登记路径**的标记（与 `8a` 打标范围对称）。

- **涉及**：`Assets/Editor/ABNameSetter.cs`
- **验收**：执行后仅 ResTable 覆盖的资源标记被清空，其余第三方资源的标记不受影响

### 2.7 🟡 M-6　单步菜单降级为"高级子菜单"

**建议**：把 1/3/4/4b/9 等单步重建工具收进 **`Tools ▸ 塔防 ▸ 高级（单步重建）`** 子菜单，
一级菜单只留：
```
Tools ▸ 塔防
├── 0. 自检（先跑这个）
├── 一键检查并补缺资源（安全）
├── 10. 导出配置表（Luban）
├── 8a/8b/8b-严格  打包相关
├── 7. 检查并补全 main 场景（安全）
└── 高级（单步重建）▸
    ├── 1. 生成占位美术
    ├── 2. 转换防御塔预制体
    ├── 3. 生成战斗预制体
    ├── 4/4b. 清理物理组件
    ├── 5. 生成 UI 预制体
    ├── 6. 配置工程设置
    ├── 7b. 重建 main 场景（危险）
    └── 8c. 清除全部 AB 标记（危险）
```
**强制约束**：所有 `*Internal` 方法（供向导调用）必须**同时**是"可重复执行且不破坏人工成果"的。

- **验收**：一级菜单 ≤ 8 项；危险项均带"危险"字样且需二次确认

---

## 第三部分　任务总表（更新版）

### 3.1 阶段划分

| 阶段 | 内容 | 项数 |
|---|---|---|
| **阶段 0** | 编辑器菜单治理（**本版新增，最先做**） | M-1 ~ M-6 |
| **阶段 A** | 多塔型 | A-1 ~ A-6 |
| **阶段 B** | 升级与出售 | B-1 ~ B-6 |
| **阶段 C** | 交互细节 | C-1 ~ C-5 |
| **阶段 D** | 升级逻辑先行（UI 资源后补） | L-1 ~ L-7 |

### 3.2 任务清单

| 编号 | 任务 | 优先级 | 主要模块 | 依赖 | 工时 |
|---|---|---|---|---|---|
| **M-1** | 一键向导改"检查并补缺" | 🔴 | M0SetupWizard.cs | — | 1.0d |
| **M-2** | 塔转换收口 + 覆盖三塔 | 🔴 | TowerPrefabConverter.cs | — | 0.7d |
| **M-3** | UI 生成器纳入三塔按钮 + 防误删 | 🔴 | UIPrefabBuilder.cs | — | 0.6d |
| **M-4** | 场景搭建拆"补缺/重建" | 🔴 | SceneMainBuilder.cs | — | 0.8d |
| **M-5** | 8c 清标记限定 ResTable 范围 | 🟠 | ABNameSetter.cs | — | 0.3d |
| **M-6** | 一级菜单收口 + 高级子菜单 | 🟡 | 各 Editor 脚本 | M-1~M-5 | 0.4d |
| A-1 | 补塔配置数据（3 型 × 3 级） | 🔴 | TowerInfo.xlsx | — | 0.5d |
| A-2 | 资源登记 + AB 包名统一 | 🔴 | ResTable/ResBundle/*.meta | — | 0.5d |
| A-3 | 塔型列表（从表遍历 L1） | 🔴 | Configs/TowerConfig | A-1 | 0.5d |
| A-4 | `HudView.cs` 适配三按钮 | 🔴 | HudView.cs | M-3 | 0.5d |
| A-5 | 切换塔型 | 🟠 | TowerPlacement.cs | A-4 | 0.5d |
| A-6 | 连建模式 | 🟠 | TowerPlacement.cs | A-4 | 0.5d |
| B-1 | 点击选中塔 | 🔴 | TowerPlacement/新增 Selector | — | 0.5d |
| B-2 | `TryUpgrade` 逻辑（**换实例**） | 🔴 | TowerManager/CombatSystem | A-1 | 1.0d |
| B-3 | 面板骨架（纯色占位） | 🔴 | 新增 TowerInfoView | B-1,B-2 | 1.2d |
| B-4 | 等级费用联动 | 🟠 | TowerInfoView.cs | B-3 | 0.5d |
| B-5 | 出售确认（原地二段式） | 🟠 | TowerInfoView.cs | B-3 | 0.5d |
| B-6 | 右键出售口径统一 | 🟡 | TowerPlacement.cs | B-5 | 0.2d |
| C-1 | 选中态高亮 | 🔴 | BaseTower/Board/CellView | B-1 | 0.5d |
| C-2 | 射程圈（占位圆） | 🔴 | 新增 RangeIndicatorView | A-4,B-1 | 0.8d |
| C-3 | 误触防护 + ESC 分层 | 🟠 | TowerPlacement/各 View | B-3 | 0.5d |
| C-4 | 金币不足统一刷新 | 🟠 | HudView/TowerInfoView | A-4,B-3 | 0.5d |
| C-5 | 数值与手感打磨 | 🟡 | TowerInfoView/HudView | B-4 | 0.5d |
| L-1 | 事件扩展（升级/出售） | 🔴 | EventName.cs | — | 0.3d |
| L-2 | 交互状态机（单一状态源） | 🔴 | 新增 Controller | B-1 | 0.5d |
| L-3 | 解耦要求落地（6 条） | 🔴 | TowerInfoView 等 | B-3 | 0.5d |
| L-4 | 出售返还口径（填表） | 🟠 | TowerInfo.xlsx | A-1 | 0.2d |
| **L-7** | **面板正式美术接入（等资源）** | 🟡 | TowerInfoView.prefab | 美术到位 | 0.5d |
| **H-4** | **按钮角标 / Tooltip（等资源）** | 🟡 | UIPrefabBuilder/HudView | 美术到位 | 0.5d |

> 说明：`L-5`（面板骨架）已并入 B-3；`L-6`（射程圈）已并入 C-2；编号保持连续以免与旧文档混淆。

### 3.3 优先级汇总

| 优先级 | 任务 | 工时 |
|---|---|---|
| 🔴 P0 | M-1, M-2, M-3, M-4, A-1, A-2, A-3, A-4, B-1, B-2, B-3, C-1, C-2, L-1, L-2, L-3 | **10.9d** |
| 🟠 P1 | M-5, A-5, A-6, B-4, B-5, C-3, C-4, L-4 | **4.2d** |
| 🟡 P2 | M-6, B-6, C-5, L-7, H-4 | **1.9d** |
| | **合计** | **17.0d** |

### 3.4 建议执行顺序

```
第 1 波（保命，防手工成果被冲掉）
  M-3（UI 生成器纳入三按钮，防再被删）
  M-2（塔转换覆盖三塔 + 跳过合规）
  M-1（向导改"检查并补缺"）
  M-4（场景拆"补缺/重建"）
        ↓
第 2 波（修当前必然报错 + 打通多塔型）
  A-4（HudView.cs 适配三按钮）
  A-1 → A-2 → A-3（配置 + 资源 + 塔型列表）
  A-5 / A-6（换型 / 连建）
        ↓
第 3 波（升级出售）
  L-1（事件）→ B-1（选中）→ B-2（TryUpgrade 换实例）
  B-3（面板骨架·纯色占位）→ B-4 / B-5
        ↓
第 4 波（交互细节）
  C-1 → C-2 → C-3 → C-4 → C-5
        ↓
第 5 波（等美术）
  L-7（换面板皮，零代码）
  H-4（按钮角标）
  M-5 / M-6（菜单收尾）
```

**关键路径**：`M-3 → A-4 → B-3 → C-2` ≈ **3.1 人日**
（M-1/M-2/M-4 与 A 阶段可并行）

### 3.5 交付里程碑

| 里程碑 | 内容 | 完成判据 |
|---|---|---|
| **MS-1 工具安全化** | M-1~M-4 | 跑完向导后 `git diff` 对已手工改造的 HudView/Tower/main.unity **无变化**；Play 无报错 |
| **MS-2 多塔型可用** | A-1~A-6 | 三种塔都能建、能切换、能连建；金币/路径校验正常 |
| **MS-3 升级出售可用** | B-1~B-6 + L-1~L-4 | 点塔弹面板、能升级（数值正确）、能出售（返还正确、二次确认生效） |
| **MS-4 手感达标** | C-1~C-5 | 选中高亮、射程圈、ESC 分层、金币不足置灰全部生效 |
| **MS-5 换皮完成** | L-7 + H-4 | 换 UI 资源后 `git diff --stat` **无 `.cs` 变更**且功能不变 |

---

## 第四部分　风险与待决策（更新）

| # | 项 | 状态 |
|---|---|---|
| ~~R1 升级实现方式~~ | ✅ **已定：换实例** | 见 §1.1 |
| R2 `sellPrice` 口径 | 🟡 待定 | 建议**不改逻辑，靠填表**：每级 `sellPrice` = 期望返还额（现有 L1=14/L2=35/L3=70 已符合） |
| R3 连建改变 M0 验收行为 | 🟠 需同步文档 | 改操作指南 §4 验收清单第 7 项描述 |
| R4 射程圈排序值 | 🟡 待定 | 先加 `BoardSorting.RangeIndicator` 常量，Play 目视后定值 |
| R5 状态管理散落 | 🔴 已识别 | 抽 `TowerInteractionState` 单一状态源（L-2） |
| R6 `TowerPlacement` 职责过载 | 🔴 已识别 | 拆出 `TowerSelector`，`TowerPlacement` 只管建造 |
| R7 UGUI Canvas Rebuild | 🟠 需遵守 | 用脏标记，数值变化时才写 `text`；卡片常驻不增删 |
| R8 移动端中文字体 | 🟡 已知 | 出新面板同样受 `LegacyRuntime.ttf` 限制，出移动包前统一换 TTF |
| **R9（新增）工具链破坏性** | 🔴 **本版处理** | 见第二部分 M-1~M-6；**根因是"生成器 = 无条件删除+重建"，与手工调优互斥** |
| **R10（新增）升级的视觉衔接** | 🟡 待定 | resName 不同的等级切换时是否加过渡。建议 M2 先不做，观察实际观感 |

---

## 第五部分　文档同步清单

| 文档 | 章节 | 更新 |
|---|---|---|
| `Docs/Tower_Interaction_Dev_Plan.md` | 全文 | 标注"已被 v2 取代"，指向本文件 |
| `Docs/HudView_Sync_and_TowerUI_Plan.md` | §7 顺序 | 顺序并入本版 §3.4 |
| `Docs/TowerDefense_Design_and_Implementation.md` | §6.2.4 | 升级实现方式明确为**换实例**，补回滚与"不触发路径重算"的说明 |
| 同上 | §6.2.2 | 建塔改"连建不退出"（R3） |
| 同上 | §6.8 | `TowerInfoView` 标注"逻辑先行、视觉待资源" |
| 同上 | §Z 附录 | 记录决策：升级=换实例；工具链安全化（M 系列） |
| 同上 | §9 风险登记册 | 新增 R9/R10 |
| `Docs/Unity_Editor_Operation_Guide.md` | §0 总览 / §13 速查 | 菜单改名后同步（"一键检查并补缺资源"） |
| 同上 | §2 | `TowerButton` → 三颗 `Btn_Tower_*`；补"已就绪产物会被跳过" |
| 同上 | §9 目录地图 | 补 `TowerInfoView.prefab` |
| 同上 | §11 故障排查 | 新增：`缺少按钮节点「TowerButton」` → 执行 A-4；`跑向导后手工改动丢失` → 已由 M-1 修复 |
| 同上 | §12 已知遗留 | 移除"塔升级/出售 UI 缺接线"；新增"面板视觉待资源" |
| `Assets/Editor/*.cs` | 各菜单头注释 | 同步改名与"跳过已就绪"行为说明 |

---

## 附：本版相较 v1 的差异速览

| 项 | v1 | v2 |
|---|---|---|
| 升级实现 | R1 待决策（换实例 / 仅换配置） | ✅ **定案：换实例** |
| 建造栏 | 计划新建 `BuildBar/Slot_{type}` | ⚠️ **改为复用已存在的 `Btn_Tower_*`** |
| 预估工时 | 11.2d | **17.0d**（新增阶段 0 菜单治理 4.3d + 骨架细化） |
| 首要任务 | A-1 补配置 | **M-3/M-2/M-1/M-4 工具安全化**（防手工成果被冲掉） |
| 新增阶段 | — | **阶段 0：编辑器菜单治理** |
| 面板交付 | 直接做正式面板 | **先纯色占位跑通逻辑**，美术到位后零代码换皮 |
