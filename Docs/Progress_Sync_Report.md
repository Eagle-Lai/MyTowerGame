# FreeTower 进度同步报告

> 扫描范围：`D:\FreedomTower_1`（当前工作目录，含子目录）
> 报告日期：2026-09-29
> 依据：`Docs/TowerDefense_Design_and_Implementation.md`(v2.1 + 附录 Z)、`Docs/Unity_Editor_Operation_Guide.md`、
> 源码与资源实测、`git log`、`.workbuddy/memory/` 工作日志、工作区未提交改动

---

## 一、结论速览

| 维度 | 状态 |
|---|---|
| **M0（单回合→多回合闭环）** | ✅ **已交付**（代码、配置、资源、编辑器工具、文档齐备） |
| **M1（怪物资源批量接入 + 波次递进）** | ✅ **基本完成**（119 怪 / 128 行数据 / 15 波组 / 12 回合），剩小尾巴 |
| **M2（多塔型 / 升级出售 / 特效音效）** | 🔄 **进行中**（代码 30% 左右；新塔资源已进但**未接线**） |
| **M3–M5（多关卡 / 打磨 / 发布）** | ⬜ **未开始** |
| **仓库卫生** | ⚠️ 有 2 处**未提交改动**、1 处**AB 包名不一致**、3 个残留临时文件 |

**一句话**：M0/M1 主体已落地且质量较高；当前正处在 M2 的"多塔型"半途——**美术与新 prefab 已就位，但配置表、资源表、HUD 都还没连上**，属"做了但还没接上线"的状态。

---

## 二、目录结构与模块用途

```
D:\FreedomTower_1\
├── Assets/                      ★ 工程主体
│   ├── Scripts/                 运行时代码（54 个 .cs）
│   │   ├── Core/
│   │   │   ├── Res/             ★ AB 资源系统，ResTable 是唯一寻址源
│   │   │   ├── Combat/          ★ 去物理战斗：EnemyGrid(空间哈希) + CombatSystem(集中 tick)
│   │   │   ├── Manager/         BaseManager<T> 单例基类 + PlayerDataManager(金币/生命)
│   │   │   ├── Event/           事件总线（EventController/EventDispatcher/EventName）
│   │   │   ├── UI/              UIManager（三层布局 + 面板缓存）
│   │   │   └── ObjectPool.cs    对象池
│   │   ├── Data/                配置读取层：Configs + 6 个包装类 + MonsterCatalog
│   │   ├── Game/                Board(几何/数据) / BoardView / CellView / GameFlowManager / PathArrowView
│   │   ├── Round/WaveManager.cs 波次时间轴状态机
│   │   ├── Enemy/               BaseEnemy / EnemyManager / MonsterAnimEventReceiver
│   │   ├── Tower/               BaseTower / NormalTower / TowerPlacement
│   │   ├── Bullet/BaseBullet.cs 子弹 + BulletManager
│   │   ├── UI/                  HudView / TipsView
│   │   ├── Camera/CameraController.cs  2D 正交相机（平移/缩放/自适应视野）
│   │   └── AStarWrapper/        A* 寻路（只建数据不生成物件）
│   ├── Editor/                  16 个编辑器工具（菜单 Tools ▸ 塔防）
│   ├── Gen/                     Luban 生成的 C# 配置类（勿手改）
│   ├── LubanLib/                Bright.Serialization + SimpleJSON（第三方）
│   ├── ConfigJson/              ★ Luban 导出产物，编辑器直读 + 进 config 包
│   ├── Scenes/main.unity        ★ 唯一主场景（脚本自动搭建）
│   ├── Prefabs/                 Tower(3) / Enemy(119) / Bullet(1) / UI(2)
│   ├── Art/Generated/           程序生成的占位美术
│   ├── _UIAssets/               美术资源（塔贴图 / 怪物包 / 背景）
│   ├── StreamingAssets/AssetBundles/  AB 产物（现仅有 Android）
│   └── SuperScrollView / TextMesh Pro / Demigiant / Reporter / Plugins  第三方
├── Luban/                       ★ 配置表工具链与源表（唯一配置来源）
│   ├── Config/Datas/*.xlsx      策划源表（8 张有效 + 3 张定义表）
│   ├── Tools/Luban.ClientServer/  Luban CLI
│   └── gen_code_json.bat        ★ 双击导出
├── Docs/                        2 份核心文档
│   ├── TowerDefense_Design_and_Implementation.md   设计+实施（2716 行，含附录 Z 实施记录）
│   └── Unity_Editor_Operation_Guide.md             编辑器操作指南（含 23 项验收清单）
├── .workbuddy/                  工具与记忆
│   ├── tools/                   9 个校验/生成脚本（check_*.py / gen_*.py / migrate_config.py）
│   └── memory/                  工作日志（2026-09-25、2026-09-26）
└── （Unity 生成物）Library/ Temp/ obj/ Logs/ UserSettings/ .vs/  *.csproj  *.sln
    （冗余物）tips.apk / tips.zip / ttttt/ / test_*_BurstDebugInformation_DoNotShip/
```

### 配置表清单（`Luban/Config/Datas/`，实测记录数）

| 表 | 记录数 | 用途 | 状态 |
|---|---|---|---|
| `EnemyData.xlsx` | 128 | 119 具体怪 + 9 梯度档 | ✅ |
| `EnemyList.xlsx` | 15 | 波次编组（出怪列表+间隔） | ✅ |
| `RoundData.xlsx` | 12 | 回合 → 波次映射 | ✅ |
| `LevelMap.xlsx` | 1 | 棋盘布局（全开阔，仅 S/E） | ✅ |
| `SceneInfo.xlsx` | 8 | 关卡（金币/生命/回合链） | ✅ 仅用第 1 关 |
| `TowerInfo.xlsx` | **3** | 塔（NormalTower L1–L3） | ⚠️ **无新塔行** |
| `BulletData.xlsx` | 1 | 子弹参数 | ⚠️ 仅 1 种 |
| `Global.xlsx` | 1 | 全局常数（唯一常数表） | ✅ |

---

## 三、已完成（M0 + M1 主体）

**基础设施**
- ✅ **AB 资源系统**：`IResLoader` 双实现（编辑器 `AssetDatabase` 直读 / 真机 `BundleResLoader`），`ResTable` 唯一寻址源、包级引用计数、编辑器模拟模式、`FORCE_AB` 宏切换
- ✅ **去物理战斗**：彻底移除 `OnTriggerEnter`/Rigidbody，改**空间哈希网格 + 距离判定 + 集中式 tick**
- ✅ **配置驱动**：Luban 全链路（xlsx → `gen_code_json.bat` → `Assets/ConfigJson/` + `Assets/Gen/`），改数值不改代码
- ✅ **编辑器工具链**：一键资源准备向导 + 6 类 20+ 项自检（`Tools ▸ 塔防`）

**玩法闭环**
- ✅ 自由布塔 + **建塔即重算路径、怪物立即改道**（《坚守阵地》灵魂机制）
- ✅ **禁止完全堵路**（建造前临时设墙跑 A*，不可达则回滚 + 变红）
- ✅ 塔自动索敌（空间哈希 + 节流 + 目标锁定 + 炮管转向），**无目标不开火且有自检计数器**
- ✅ 金币经济闭环（建塔扣费 / 击杀奖励 / 回合奖励 / **出售返还**）
- ✅ 生命闭环（漏怪扣血 → 归零失败提示）
- ✅ **10 个回合推进 + 通关判定**、自动开下一回合（可配）
- ✅ HUD / TipsView / 相机自适应 / 调试快捷键（F1/F2/空格/滚轮/右键）

**内容与验证**
- ✅ **119 种怪物**全部转战斗 prefab（去物理 / 挂 `BaseEnemy` / 自适应血条），**按家族分包**
- ✅ 128 行怪物数据、15 个波次编组（递进）、12 个回合
- ✅ 已修复 **19 个实施缺陷**（附录 Z.2 有完整记录，含 A* 轴语义反转、事件系统静默吞异常等隐蔽 bug）
- ✅ **6 个静态校验脚本**（`check_code/events/usings/members/unity_api.py`）用于编译前拦截
- ✅ 真 AB 链路 + PC 出包路径已验证，Android AB 已产出

---

## 四、正在进行（未完成的 M2）

代码侧预留点（源码中明确标注）：

| 位置 | 内容 | 状态 |
|---|---|---|
| `BaseBullet.cs:116` | AOE 半径伤害 | 🟡 分支已留（`aoeRadius=0` 未启用） |
| `BaseBullet.cs:141` | 穿透后继续寻敌 | 🟡 已留分支，待完善 |
| `TowerConfig.cs:78` | `UpgradeTo` 升级链 | 🟡 数据就绪，**缺 UI 接线** |
| `MonsterAnimEventReceiver.cs:75` | 按动画名播音效/特效 | 🟡 预留给 M2 |
| `NormalTower.cs:8` | 塔特有逻辑扩展点 | 🟡 占位 |
| `HudView.cs:29` | 塔选择栏（M0 固定 1/1） | 🟡 注释标注"H2 接塔选择栏" |
| `UIEventListenerManager.cs:277` | 旧版 `UIEventListener` 残留 | 🔴 死代码「TODO,临时解决」 |

**⚠️ 工作区有未提交改动（正在做的多塔型工作）**

```
 M Assets/Prefabs/Tower/Tower_Normal.prefab.meta     ← AB 包名 tower_normal → tower
 M Assets/Prefabs/UI/HudView.prefab
?? Assets/Prefabs/Tower/Tower_Power.prefab(+meta)    ← 新增：强化塔
?? Assets/Prefabs/Tower/Tower_Retard.prefab(+meta)   ← 新增：减速塔
?? Assets/_UIAssets/Tower/Power/{tower_base,tower_barrel}.png
?? Assets/_UIAssets/Tower/retard/{slowtower_base,slowtower_crystal}.png
```

---

## 五、尚未开始（M3–M5）

| 阶段 | 内容 |
|---|---|
| **M3** | 多关卡（8 关）、选关界面（星级/解锁）、可视化地图编辑工具、存档系统（含局内快照）、暂停/设置 |
| **M4** | 美术统一、动画打磨、多分辨率适配（16:9 / 19.5:9 / iPad）、相机边缘拖拽、背景视差与粒子 |
| **M5** | AB 包体分析与拆包、SpriteAtlas 合批、低端机压测（200 怪+50 塔 60fps）、对象池统一、HybridCLR 取舍、PC+Android 出包、崩溃上报、仓库瘦身（2.17 GiB → <100 MB） |

---

## 六、发现的问题（缺失 / 命名不一致 / 与预期进度不符）

### 🔴 P0 — 阻断性 / 会直接报错

**1. 新塔只做了一半：prefab 有了，但配置、资源表、HUD 全没接**
- `Tower_Power` / `Tower_Retard` 两个 prefab 与美术已就位，但：
  - `TowerInfo.xlsx` **仍只有 3 行**（全是 `NormalTower` L1–L3，`resName` 全指向 `Tower_Normal`）→ 新塔**没有任何数据行**，游戏里永远建不出来
  - `ResTable.cs` **未登记** `Tower_Power` / `Tower_Retard` → 即使配了表，加载时也会报「资源地址表中找不到逻辑名」
  - `ResBundle.cs` **无对应包常量**，但 prefab 的 `.meta` 已把包名标成 `tower`
  - `HudView` 仍是单按钮「建塔」，无塔选择栏（`_currentTowerType` 写死 1/1）
- **判断**：这是一次**中途停下、尚未接线的重构**。属"看起来做完了、实际跑不到"的典型状态，建议优先补齐或明确回滚。

**2. AB 包名不一致 —— 改标了 prefab，但没改代码常量**
- `Tower_Normal/Power/Retard.prefab.meta` 的 `assetBundleName` 现为 **`tower`**
- 但 `ResBundle.cs` 里常量仍是 **`TowerNormal = "tower_normal"`**，`ResTable.cs` 也仍引用 `ResBundle.TowerNormal`
- 后果：`ABNameSetter` 按 ResTable 打标 → 会把三个塔**打回 `tower_normal`**（覆盖手工改动）；若先进 AB 验证，则 `BundleResLoader` 会去找不存在的 `tower_normal` 包 → **真机 AB 模式必炸**
- **必须二选一**：把三个 prefab 的标记改回 `tower_normal`，**或**同步改 `ResBundle.TowerNormal` 的值与 `ResTable` 的引用

### 🟠 P1 — 一致性 / 卫生问题

**3. `StreamingAssets/AssetBundles/Android/` 是旧包，与当前标记不匹配**
- 目录里还是 `tower_normal` 等旧包，而 prefab 已改标 `tower`；且只打了 Android、没有其他平台
- 属"过期产物"，验证真 AB 前必须重打

**4. `Luban/Config/Datas/` 里有 3 个 Office 锁文件**
- `~$EnemyData.xlsx`、`~$EnemyList.xlsx`、`~$RoundData.xlsx` 未清理
- 操作指南 §1 明确写了这类文件会导致导出报错，**且要求关闭 Excel 后删除**。当前仍存在 → 下次跑 `gen_code_json.bat` 有风险

**5. 仓库冗余物仍在版本控制内（文档已列但未处理）**
- `tips.apk` + `tips.zip` 各 38 MB、`ttttt/`、`test_*_BurstDebugInformation_DoNotShip/`
- 文档 §12.5 与 M5 都提到要清，属**计划中但未执行**

### 🟡 P2 — 文档与代码偏差

**6. 文档声称与实际有轻微偏差**
- 设计文档 §1.1 写「`Assets/Scripts` 62 个脚本」→ **实际 54 个**（重构中删了一批，数字未回填）
- 文档 §Z.3 写「运行时 31 个文件 / 编辑器 12 个」→ **实际脚本 54 个、编辑器工具 16 个**（M1/M2 新增未同步）
- 操作指南提到 F3 键「已移除」，但 §4 快捷键表里仍保留该行，属历史残留说明

**7. 命名不一致（文档 §1.6 T6 已记录，未修）**
- `TowerCofig`（应为 `TowerConfig`，代码里已是正确拼写，历史名残留在文档）
- 表字段 `EenemyPosition`（SceneInfo）
- 设计文档 §3.1 标题写「`D:\FreedomTower\Luban`」，而 v2.1 修订说明写「已由 `Luaban` 重命名」→ **历史文本仍有两处 `Luaban` 残留**，易误导
- **实际工程根目录是 `D:\FreedomTower_1`**（带 `_1`），但文档全篇写 `D:\FreedomTower`（无 `_1`）→ 按文档里的绝对路径操作会**找不到目录**

**8. 记忆/日志断档**
- `.workbuddy/memory/` 只有 **09-25、09-26** 两天，**9-27 / 9-28 的工作（多塔型、AB 改包名）没有任何日志记录** → 当前这轮改造缺少决策留痕，新人接手看不出"为什么把塔包名改成 tower"

**9. 文档结构异常**
- 设计文档附录编号跳变：`Z.1 → Z.2 → Z.6 → Z.3 → Z.4 → Z.5`（**Z.6 插在 Z.2 和 Z.3 之间**），阅读顺序混乱，建议重排

---

## 七、下一步建议

**立即处理（P0，半天内）**
1. **决定多塔型的走向**：
   - 若继续 → 补 `TowerInfo.xlsx` 两行（Power/Retard，含 `type`/`effectType`/`bulletId`）、`ResTable` 登记、`ResBundle` 包常量、HUD 塔选择栏
   - 若暂停 → **把 3 个 prefab 的 AB 标记改回 `tower_normal`**，把新 prefab 挪出 AB 范围，避免污染现有链路
2. **统一 AB 包名**：让 prefab 标记与 `ResBundle.TowerNormal` 一致（当前必有一处是错的）
3. **删除 3 个 `~$*.xlsx` 锁文件**，再跑一次 `gen_code_json.bat` 确认导出正常

**本周（P1）**
4. 重打 Android AB（现网包已过期），跑一次 `Tools ▸ 塔防 ▸ 0. 自检`
5. 在 Unity 里完整触发一次编译（文档 §Z.6 已说明本机无法编译，类型推导层未被静态脚本覆盖）

**收尾（P2）**
6. 回填文档中的脚本数量、删掉 `Luaban`/`D:\FreedomTower` 的历史残留（改指 `_1` 或加一句"路径以实际工程为准"）
7. 重排附录 Z 的编号顺序
8. 清理 `tips.apk/zip`、`ttttt/`；补一份 09-27/09-28 的工作日志

**M2 剩余既定项**：塔升级/出售 UI（`TowerInfoView` 世界空间版）、AOE/减速/穿透子弹特性、伤害飘字、音效系统。
