# 单机 2D 塔防《FreeTower》设计与实施文档

> 目标定位：实现一款**单机 2D** 版、核心机制对标《坚守阵地》（Fieldrunners）的塔防游戏。
> 文档版本：**v2.1**（2D 重构版 · SpriteRenderer 路线修正）　|　编制日期：2026-09-26
> 工程路径：`D:\FreedomTower`　|　主场景：`Assets/Scenes/main.unity`
> 配置表目录：**`D:\FreedomTower\Luban`**（2026-09-26 已由 `Luaban` 重命名，提交 `8ab496b1d`）
>
> **v2.1 修订要点**：实测发现怪物资源**已全部替换为 2D `SpriteRenderer` + `Animator` 实现**
> （`_UIAssets/Monsters/**`：119 prefab / 122 Sprite / 120 anim / 30 Controller，原 120 个 3D prefab 已删除），
> 而 v2.0 定案的 UGUI 路线与之冲突，故 **§2.3 技术路线改为「世界空间 2D + `SpriteRenderer`」**，HUD 保留 UGUI。
> 全文相关章节（§0.1、§1.1、§1.3、§1.4、§3.3、§6.1、§6.3、§6.8、§7、§9、§10）已同步修正。

---

## 0. 文档说明

### 0.1 本次修订的 8 项要求与落实位置

本文档是对 v1.0 的**整体重写**。v1.0 中基于 3D 引擎特性的设计（3D 网格、`Rigidbody`、物理触发器、`Vector3` 寻路、ASCII 地图文件等）已全部作废并替换。

| # | 要求 | 落实章节 | 关键变化 |
|---|---|---|---|
| **1** | 由 3D 重构为 2D，保留《坚守阵地》核心机制 | §2、§6.1、§6.7 | 定案 **世界空间 2D + `SpriteRenderer`**（玩法对象）+ **UGUI**（HUD）；移除全部 3D 专用 API |
| **2** | 地图生成相关内容重写或舍弃 | §6.1.3、§3.3.6 | **废弃** `StreamingAssets/Map/Map*.txt` ASCII 文件方案，改为**配置表驱动棋盘布局** |
| **3** | 说明配置表位于 `D:\FreedomTower\Luban` | **§3.1** | 完整标注目录树、工具链、导出命令与产物路径 |
| **4** | 塔防数据尽量配置表驱动 | **§3.3、§3.4** | 新增 `TBBullet`/`TBLevelMap`/`TBGlobal` 表；经济、波次、怪物、塔全量进表 |
| **5** | 仅 1 种塔 + 数量待定怪物；第一阶段只做单回合闭环 | §0.3、**§7** | **M0 范围收窄为「单回合闭环」**；表结构预留扩展位，缺失字段走默认值不阻塞 |
| **6** | 玩法在 `Assets/Scenes/main.unity` 内实现 | **§6.1** | 明确该场景现状（仅 4 个对象）与需要补齐的层级结构 |
| **7** | `ResourcesManager` 改造为 **AB（AssetBundle）** 加载 | **§4** | 全新 AB 系统设计：打包粒度、Manifest 依赖、异步加载、引用计数、编辑器模拟模式 |
| **8** | 战斗判定不再用 `OnTriggerEnter`（低端机性能问题） | **§5** | **彻底移除物理系统**，改为集中式 tick + 网格空间哈希 + 距离判定 |

### 0.2 阅读指引

| 章节 | 内容 | 读者 |
|---|---|---|
| §1 | 现状分析（2D 视角重估）与阻塞问题 | 全员 |
| §2 | 2D 玩法设计与技术路线定案 | 策划 + 主程 |
| **§3** | **配置表驱动设计（含 Luban 目录说明）** | **策划 + 开发** |
| **§4** | **AB 资源加载系统** | **开发** |
| **§5** | **战斗判定优化** | **开发** |
| §6 | 各子系统设计（场景/塔/怪/子弹/波次/经济/寻路/UI） | 开发 |
| **§7** | **第一阶段（M0）详细计划与依赖** | **全员，落地依据** |
| §8 | M1–M5 阶段概要 | 排期参考 |
| §9 | 风险登记册 | 主程 |
| §10 | 附录（常量迁移、文件清单、代码骨架、验收清单） | 开发 |

### 0.3 第一阶段范围界定（重要）

按需求 5，**M0 只做「一个简单回合的闭环」**，不做多波次、不做升级出售、不做多关卡：

```
启动 → 读配置 → 生成 2D 棋盘 → 拖放 1 种塔 → 生成 1 波怪
     → 塔索敌开火 → 命中扣血 → 怪死亡给金币 / 漏怪扣玩家血
     → 本波怪清空 → 弹「回合完成」
```

**范围纪律**：需求 5 明确"功能缺失不应影响实际实现"。因此本文档的所有表结构都**预留**字段，但 M0 阶段：
- 表里没有的字段 → 走代码默认值（§3.5 容错策略），**不报错、不阻塞**
- 怪物只有 1 种也能跑通（`TBEnemy` 只配 1 行）
- 塔只有 1 种（`TBTower` 已有 NormalTower 的 3 个等级，M0 只用 level=1，升级逻辑留到 M2）
- 没有音效、没有特效、没有结算界面，用 `Debug.Log` + 一个简单 Tips 面板即可

---

## 1. 项目现状分析（2D 视角重估）

### 1.1 工程概况

| 项 | 现状 |
|---|---|
| 引擎 | Unity 2022.3 LTS |
| 2D 支持 | `com.unity.feature.2d` 2.0.1、`com.unity.modules.physics2d` **已安装** |
| 主场景 | `Assets/Scenes/main.unity` — **新建，目前仅有 4 个对象**：`Camera`、`Canvas`、`EventSystem`、`bg` |
| 相机 | **正交相机**（`orthographic: 1`, size = 5）→ 已是 2D 配置 |
| Canvas | `RenderMode = ScreenSpaceCamera`，`UiScaleMode = ScaleWithScreenSize`，参考分辨率 **1920×1080** |
| 代码规模 | `Assets/Scripts` 62 个脚本、约 5,789 行（命名空间 `FTProject`） |
| 配置管线 | Luban，源表在 **`D:\FreedomTower\Luban`**（详见 §3.1） |
| 现有 2D 美术 | `Assets/_UIAssets/Tower/Normal/`：`turret_base_128.png`、`turret_barrel_128.png`；`Assets/_UIAssets/Backgrounds/Paper.png` |
| **现有怪物资源（已 2D 化）** | **`Assets/_UIAssets/Monsters/**`：119 个 prefab + 122 张 Sprite（PPU=100）+ 120 个 `.anim` + 30 个 `.controller`**；14 个族系 + `_Common`（含 `Animations/<族系>/` 与 `Sprites/`）。每怪含 **`Ready` / `Walk` / `Attack` / `Death`** 四态动画。<br>形态：`Transform` + **`SpriteRenderer`×8**（分部件骨骼式）+ `Animator` + `SortingGroup`(order 200) + `CapsuleCollider2D`。**原 120 个 3D prefab 已删除。** |
| 现有塔预制体 | `Assets/Prefabs/Tower/Tower_Normal.prefab` — **3 个 `RectTransform` + 2 个 `Image`**（子节点 `barbette` 炮座、`Img_gun` 炮管），**尚未挂 `BaseTower` 脚本、无排序组** → 需转为 `SpriteRenderer` 以统一渲染路线（§2.3） |
| 第三方面板 | DOTween、SuperScrollView、HybridCLR（未接入）、Reporter |
| AssetBundle | **工程内无任何 AB 代码**（已确认）→ §4 需从零建设 |

### 1.2 已具备的基础（可复用）

#### A. 架构骨架（与 2D/3D 无关，可直接复用）

| 模块 | 文件 | 评价 |
|---|---|---|
| 管理器基类 | `Core/Manager/BaseManager.cs` + `IManagerInterface.cs` | 单例 + OnInit/OnDestroy，规范 |
| 启动器 | `Launcher.cs` | 注册 6 个 Manager，职责清晰 |
| 事件总线 | `Core/Event/EventDispatcher.cs`、`EventName.cs` | 可用，但**需要改造**（见 §5.2 集中式 tick） |
| 定时器 | `Core/TimerManager.cs` | 够用 |
| UI 框架 | `Core/UI/UIManager.cs`、`BaseView.cs` | 三层布局 + 面板缓存 + 空闲回收，**2D UGUI 下价值更高** |
| 工具扩展 | `Util/FTProjectUtils.cs` | 部分方法需 2D 化 |

#### B. 塔防核心机制（**最值得保留**）

| 机制 | 位置 | 2D 下的处理 |
|---|---|---|
| **布塔动态重算路径** | `AStarManager.UpdateStarPath` + 事件 | ✅ 逻辑保留，坐标体系改 2D（§6.7） |
| **禁止堵死路径** | `TowerPosition.BuildTower` 临时设墙 → A* 校验 → 回滚 | ✅ **逻辑完全保留**，这是《坚守阵地》的灵魂 |
| **A\* 寻路** | `AStarWrapper/AStarWrapper.cs`、`Point.cs` | ✅ 算法保留，`Point.position` 由 `Vector3` 改网格索引/`Vector2` |
| 建造交互流程 | `TowerPosition.cs` | ⚠️ 交互逻辑保留，坐标换算改**世界空间**版（`Camera.ScreenToWorldPoint` + `BoardView.WorldToCell`） |
| 塔攻击节奏 | `BaseTower.cs` | ⚠️ 保留节奏，开火条件重写（§6.2） |
| 敌人血条/受击飘字 | `BaseEnemy.cs` | ⚠️ 3D 世界空间方案作废，改 UGUI（§6.3） |
| 对象池思路 | `EnemyManager`/`BulletManager` 双字典 | ✅ 保留思路，统一为 `ObjectPool<T>` |

#### C. 数据驱动管线（已设计完成）

`Luban/Config/Datas/*.xlsx` 已有 5 张表，**数据基本够用，只是代码没读**：

| 表 | 记录数 | 关键字段 |
|---|---|---|
| `TBEnemyData` | 9+ 种 | id, **speed**, **hp**, name, type(1/2/3), interval |
| `TBEnemyList` | 40 波 | id, EnemyIndexs(编组), interval(本波开始 ms), enemyInterval(波内单敌间隔 ms), desc |
| `TBRoundData` | 21 回合 | id, EnemyIndexs(引用 EnemyList id), interval |
| `TBSceneInfo` | 8 关 | id, RoundList, CameraPosition, CameraRotration, MapName, EenemyPosition, MapPosition, PointScale |
| `TBTowerInfo` | 3 级 | id, type, name, path, **level**, **radius**, **power**, **CD**, **prices** |

### 1.3 阻塞问题（不改就跑不起来）

| # | 问题 | 证据 | 后果 |
|---|---|---|---|
| **B1** | **配置表 JSON 缺失** | `Assets/StreamingAssets/json/` 为空；`Data/DataTables.cs` 要读 5 个文件 | 启动即崩，配置全空 |
| **B2** | **运行时资源被清空** | `Assets/Resources/` 仅剩 `DOTweenSettings.asset`；而 `AssetData.cs` 仍引用约 20 个路径 | 资源加载全返回 null |
| **B3** | **`.gitignore` 曾含 `*.json`** | 已于提交 `e1d8582f9` 修复 | 修复前配置表永远提交不进去 |
| **B4** | **Build Settings 引用已删场景** | 列的是 `Launcher/Start/Main.unity`，实际只有 `main.unity` | 打包失败 |
| **B5** | **运行时代码污染编辑器程序集** | `Json/JsonDataManager.cs` 顶层 `using UnityEditor;` | 打包编译失败 |
| **B6** | `main.unity` 是空骨架 | 仅 `Camera`/`Canvas`/`EventSystem`/`bg` | 无 UICanvas 层级、无游戏管理器挂载点、无棋盘 |
| **B7** | **塔与怪物的渲染体系不统一** | 怪物是 `SpriteRenderer` + `Animator`（世界空间），塔是 `Image` + `RectTransform`（UGUI） | 塔需转为 `SpriteRenderer`（**仅 1 个 prefab，成本≈0**）；否则"塔怪按 Y 互相遮挡"与坐标换算无法统一（§2.3） |

> 注：B3 已在上一轮修复；B1/B2/B4/B5 的修复方式见 §7 的 P0 任务。

### 1.4 2D 重构的影响面（哪些代码必须重写）

这是 v1.0 → v2.0 最实质的变化，**逐文件列出，避免漏改**：

| 文件 | 3D 依赖 | 2D 处理 |
|---|---|---|
| `Enemy/BaseEnemy.cs` | `Rigidbody`、`transform.Translate`、`Vector3.ProjectOnPlane` 广告牌、世界空间 TMP 血条 | **重写**：`RectTransform.anchoredPosition` 移动、UI Image 血条、`Vector2` 朝向 |
| `Tower/Tower/TowerPosition.cs` | `Camera.WorldToScreenPoint` + `ScreenToWorldPoint`、`Collider` 触发 | **重写**：`ScreenToWorldPoint`（`z` 取 `-camera.transform.position.z`）→ `BoardView.WorldToCell`；节点判定改**网格索引计算**（不再靠触发器） |
| `Tower/Tower/Targetter.cs` | `SphereCollider` + `OnTriggerEnter/Exit` | **删除**，由 §5 的 `EnemyGrid` + `CombatSystem` 取代 |
| `Tower/BaseTower.cs` | `transform.Find("Head/BulletPoint")` 3D 层级、`GetComponentsInChildren<Renderer>` 换色 | 改为 `RectTransform` 层级与 `Image.color` |
| `Tower/NormalTower.cs` | 子弹跟随 3D 炮口 | 炮管旋转改 `localRotation.z` |
| `Bullet/BaseBullet.cs` | `transform.Translate(Vector3.forward)`、`OnTriggerEnter` 命中 | **重写**：`Vector2` 速度 + 距离判定（§5.4） |
| `Node/BasePoint.cs` | `Renderer.material.color` 染色、`Collider` 触发高亮 | 改 `Image.color`；高亮由网格索引计算触发 |
| `Node/*`（Start/End/Normal/Empty） | 继承 `BasePoint` 并被当 3D 物件用 | 简化为**格子数据 + 视图**两层（§6.1.3） |
| `Obstacle/*` | `Collider` | 合并进格子类型，删除独立脚本 |
| `AStarWrapper/Point.cs` | `Vector3 position`、`GameObject` 引用 | 改 `int row/col` + `Vector2 center`；**移除 GameObject 强引用**（解耦数据与视图） |
| `AStarWrapper/AStarManager.cs` | 3D 物件生成、`LineRenderer` 路径绘制、从 txt 读地图 | **重写地图来源**（配置表，§6.1.3）；路径绘制改 UGUI 箭头池 |
| `Camera/CameraController.cs` | 透视相机旋转/平移 | 改正交相机的平移 + 缩放（`orthographicSize`），或 M0 干脆不实现 |
| `Core/ResourcesManager.cs` | `Resources.Load` | **整体替换为 AB 系统**（§4） |
| `Data/AssetData.cs` | 名称→`Resources` 路径字典 | **替换为 AB 地址表**（bundle + asset，§4.4） |
| `Enemy/EnemyManager.cs` | 3D prefab 实例化 | 改**世界空间** prefab 实例化（怪物 prefab 已 2D 化），并**修复池化字典键硬编码 Bug** |
| `GameSceneLauncher.cs` | 3D 相机就位、`MapPosition` | 改 2D 棋盘初始化入口 |

**保留不改（或仅微调）**：
`Core/Manager/*`、`Core/TimerManager`、`Core/Event/*`、`Core/UI/*`、`Core/ObjectPool`、`Gen/*`、`LubanLib/*`、`Data/DataTables.cs`（仅改加载方式）、`Config/GlobalConst.cs`（数值逐步迁表）。

### 1.5 玩法层缺口（沿用 v1.0 结论）

| # | 子系统 | 现状 | 缺口 |
|---|---|---|---|
| G1 | 金币经济 | 只有显示文本 | 建塔不扣费、击杀无奖励、卖塔不返还 |
| G2 | 生命值闭环 | 只有显示文本，漏怪直接回收 | 漏怪不扣血、无失败判定 |
| G3 | 波次推进 | 靠手动按钮 / `R` 键调试触发 | 无波次状态机、无自动推进、无胜负 |
| G4 | 塔升级 | `TowerInfoView.OnClickUpgradBtn()` 空函数 | `TBTowerInfo` 从未被读取（M2 再做） |
| G5 | 塔出售 | `ShellTower()` 有实现 | 缺金币返还、缺打开面板的入口（M2 再做） |
| G6 | 数值配置化 | 塔/怪数值硬编码于 `GlobalConst`、`TowerCofig` | 与配置表脱节（表里 hp 100+ vs 常量 6） |
| G7 | 索敌系统 | `Targetter.GetNearsetTarget()` 返回 `_enemyList[0]` | 无空检查会崩；非"路径进度最靠前"策略；`NormalTower` 根本没用它 |
| G8 | 敌人类型 | `EnemyType` 只有 Normal/Quick | 表里 type=3 无法生成；池化字典键硬编码 Bug |
| G9 | 伤害结算 | 子弹固定 `Hurt(1)` | 与塔 `power` 无关 |
| G10 | 命中判定 | `name.Contains("Enemy")` 字符串匹配 | 脆弱且慢（§5 一并解决） |
| G11 | 职责重复 | `RoundCountManager` 空壳 | 与 `EnemyManager` 波次逻辑重复，需归并 |

### 1.6 技术债

| # | 项 | 处理 |
|---|---|---|
| T1 | `AStarManager.GetAStarPath` 的 `while(true)` 有死循环/NRE 风险 | §7 P0-9 加固 |
| T2 | 每帧 `UpdateEvent` 全量分发（每个塔/怪/子弹都订阅） | §5.2 改集中式 tick |
| T3 | `TowerManager.GetTower<T>() where T : BaseTower, new()` 对 MonoBehaviour 用 `new()` 是反模式 | §6.2 重写 |
| T4 | `ObjectPool` 形同虚设 | §6 统一 |
| T5 | 遗留测试代码（`PopMain.cs`、`TestTileMap.cs`、`AStarWrapper/Scenes/`） | §7 P0-9 |
| T6 | 命名问题（`Luban`→`Luban`、`TowerCofig`→`TowerConfig`、`GetNearsetTarget`、`EenemyPosition`） | 逐步修正，**表名/字段名改动需同步重导** |
| T7 | 无音频系统 | M2 |
| T8 | HybridCLR 已引入未接入 | 单机项目建议 M5 决策是否移除 |

---

## 2. 2D 玩法设计与技术路线

### 2.1 核心玩法（对标《坚守阵地》）

五个不可替代的核心体验：

| # | 机制 | 说明 | 能否删减 |
|---|---|---|---|
| C1 | **自由布塔 + 动态重算路径** | 敌人路径随玩家布塔实时改变，玩家可主动"绕路" | **不可删** |
| C2 | **路径不可完全阻断** | 至少保留一条通路 | **不可删** |
| C3 | **多塔型 + 升级 + 出售** | 差异体现在效果而非仅数值 | 塔型数量可减，机制不可删 |
| C4 | **波次 + 金币 + 生命** | 击杀给钱、建塔花钱、漏怪扣命、命尽失败 | **不可删** |
| C5 | **多关卡递进 + 敌人多样化** | 难度递增，敌人有快/慢/高血/护甲/飞行区分 | 数量可减，机制不可删 |
| — | 美术风格、音效、UI | 不影响玩法成立 | 可自由调整 |

**M0 只落地 C1、C2、C4 的最简形态**（1 塔、1 波、1 回合），C3/C5 留待 M1–M3。

### 2.2 与原作对齐 + 2D 化取舍

| 原作机制 | 2D 版实现 | 判定 |
|---|---|---|
| C1 布塔动态重算 | 2D 网格 A*，建塔后重算并重绘路径箭头 | ✅ 已具备（需 2D 化） |
| C2 不可全阻断 | 建造前临时占格跑 A* 校验，不可达则回滚 + 变红提示 | ✅ 已具备（逻辑可直接保留） |
| C3 多塔型 | M0 只做 1 种（NormalTower）；表结构预留 `type`/`bulletId`/`effectType` | ⚠️ 分阶段 |
| C3 三级升级 | M0 只读 level=1；`TBTowerInfo` 已有 3 行数据，M2 接线 | ⚠️ 分阶段 |
| C3 出售 | M2 实现 | ⚠️ 分阶段 |
| C4 波次 | M0：1 回合 1 波；M1：多波自动推进 | ⚠️ 分阶段 |
| C4 金币 | **M0 就做**（建塔扣费 + 击杀奖励），因为它是闭环的必要组成 | ✅ M0 |
| C4 生命 | **M0 就做**（漏怪扣血 + 归零失败提示） | ✅ M0 |
| C5 多关卡 | M0：只跑 `TBLevel` 第 1 行 | ⚠️ 分阶段 |
| C5 敌人多样化 | M0：1 种怪物；M2 扩展类型/护甲/飞行 | ⚠️ 分阶段 |
| **★ 2D 化的天然收益** | 飞行单位、护甲、AOE、激光等效果在 2D 下实现成本远低于 3D | ✅ |

**明确允许偏离原作的地方**
1. **寻路实现**：原作是"路点 + 自由堆叠"，本作是"2D 网格 + A*"。**最终玩法结果一致（自由布塔形成迷宫），实现方式更工程化，可接受。**
2. **视角**：斜俯视 2D（固定视角，无旋转），而非原作的透视 3D。
3. **UI 布局、动效、音效**：完全自由设计。
4. **美术风格**：定案为 **2D 纸片/扁平风**（已有 `Paper.png` 背景与塔贴图，方向一致）。

### 2.3 2D 技术路线定案

**结论：世界空间 2D —— 玩法对象用 `SpriteRenderer`，HUD 用 UGUI。**
（本节在 v2.1 中**推翻了 v2.0 的 UGUI 方案**，原因见下）

#### 2.3.1 现状：两套渲染体系并存（必须先统一）

实测结果（Unity YAML 类型 ID 统计）：

| 对象 | 预制体 | 组件构成 | 渲染体系 |
|---|---|---|---|
| **怪物** | `_UIAssets/Monsters/Rats/Rat/Rat.prefab` | `Transform`×12、**`SpriteRenderer`×8**、`Animator`×1、`SortingGroup`×1、`CapsuleCollider2D`×1 | **世界空间 2D** |
| **防御塔** | `Assets/Prefabs/Tower/Tower_Normal.prefab` | **`RectTransform`×3**、`CanvasRenderer`×2、`Image`×2（`barbette` 炮座 + `Img_gun` 炮管） | **UGUI** |

两者不在同一个渲染/坐标系内。**若不做统一，会出现三个具体问题：**
1. **层级穿插失效** —— 塔防需要"塔和怪按 Y 坐标互相遮挡"（靠 `SortingGroup` / `transparencySortMode`），而 UGUI 元素由 Canvas 层级顺序决定，两套排序规则无法混用
2. **坐标双轨** —— 棋盘坐标要同时维护 RectTransform 局部坐标与世界坐标，每个交互点都要两套换算
3. **点击/拖拽双份实现** —— SpriteRenderer 走 `Physics2D.OverlapPoint` / 自算，UGUI 走 `RectTransformUtility` + EventSystem

#### 2.3.2 为什么选 SpriteRenderer 而不是 UGUI

| 决策依据 | 说明 |
|---|---|
| **① 怪物资源不可动（决定性）** | `_UIAssets/Monsters/**` 已投入：**119 个 prefab + 122 张 Sprite + 120 个 .anim + 30 个 Controller**，且是**分部件骨骼式**结构（Rat 有 Body/Head/Tail/4 条腿共 8 个 SpriteRenderer）+ `Animator` 驱动。改成 UGUI 要把 119 个 prefab 的 8 个 `SpriteRenderer` 全部换成 `Image`，并重做 `SortingGroup`（UI 下无意义）。**成本高且无收益。** |
| **② 塔的改造成本≈0** | 塔只有 **1 个** prefab、2 个 `Image`。把 `Image` 换成 `SpriteRenderer`（复用同样那 2 张 PNG）即可，**半天内可完成**。 |
| **③ 2D 动画链路现成** | 怪物包已含 `Ready` / `Walk` / `Attack` / `Death` 四态动画与 Controller。`Animator` + `SpriteRenderer` 是 Unity 2D 的标准组合；UGUI `Image` 无法直接吃这套 Controller。 |
| **④ 性能方向一致** | 需求 8 提出低端机性能问题。**SpriteRenderer 没有 Canvas 重建（Rebuild）开销**，而大量 UGUI `Image` 一旦有节点增删/属性变更就会触发整层 Canvas Rebuild —— 这正是低端机卡顿的常见根因。 |
| **⑤ 世界空间是主流 2D 塔防做法** | 「玩法对象 `SpriteRenderer` + HUD `UGUI`」是 Unity 2D 游戏的标准分层，教程/插件/现成方案最丰富。 |
| ⑥ 适配成本可接受 | 棋盘尺寸由正交相机 `orthographicSize` 控制，配合 `CameraController` 即可适配多比例；HUD 仍由 `CanvasScaler` 自动适配。 |

**保留 UGUI 的部分**：HUD、Tips、结算、设置等**纯界面**，用 `ScreenSpaceOverlay`（不再用 `ScreenSpaceCamera`，避免与场景坐标耦合；HUD 不需要参与游戏对象的遮挡排序）。

#### 2.3.3 世界空间 2D 的关键参数（由现有资源反推）

| 参数 | 取值 | 依据 |
|---|---|---|
| Sprite `Pixels Per Unit` | **100** | `Rat.png.meta` 中 `spritePixelsToUnits: 100` |
| 相机 | 正交，`orthographicSize` | `main.unity` 现为 `5` |
| 可视世界高度 | `2 × orthographicSize = 10` 世界单位 | 正交相机定义 |
| **格子尺寸 `CellSize`** | **1 世界单位**（= 100 像素） | 与 PPU 100 对齐，怪物占 1 格，数值整洁 |
| 棋盘可容纳格数 | 高 **10** 格 / 宽约 **17 格**（16:9，`5 × 16/9 × 2 ≈ 17.8`） | 由 `orthographicSize` 与宽高比推出 |
| 建议 M0 棋盘 | **16 × 9** 格 | 留出边距，且为整格 |
| Sprite 排序 | `SortingGroup`（怪物现有 `m_SortingOrder: 200`） | 复用怪物包既有约定 |
| 排序轴 | 需在 `Graphics Settings` 设 `Transparency Sort Mode = Custom Axis`，轴 `(0, -1, 0)` | 让 Y 越小（越靠下）的越靠前，实现 2D 前后遮挡 |
| 像素对齐 | 需装 `com.unity.2d.pixel-perfect`（工程已有 `Unity.2D.PixelPerfect` 包）或自算 | 避免 Sprite 抖动 |

#### 2.3.4 坐标系约定（贯穿全文，务必统一）

- 棋盘原点 `BoardRoot` 放在**世界坐标**中，`main.unity` 内建议置于 `(0, 0, 0)`
- 格子尺寸 `CellSize = 1f`（世界单位）
- 格子中心世界坐标（**以棋盘左上角为原点，`y` 向下为负**）：
  `cellCenter(row, col) = boardOrigin + new Vector2((col + 0.5f) * CellSize, -(row + 0.5f) * CellSize)`
- 网格索引 ↔ 世界坐标互转由 `BoardView` 统一提供，**禁止各模块自行换算**
  ```csharp
  public Vector2 CellCenter(int row, int col)
      => new Vector2((col + 0.5f) * CellSize, -(row + 0.5f) * CellSize) + (Vector2)_root.position;

  public bool WorldToCell(Vector2 worldPos, out int row, out int col)
  {
      Vector2 local = worldPos - (Vector2)_root.position;
      col = Mathf.FloorToInt(local.x / CellSize);
      row = Mathf.FloorToInt(-local.y / CellSize);
      return row >= 0 && row < _rows && col >= 0 && col < _cols;
  }
  ```
- 屏幕坐标 → 世界坐标：`Camera.main.ScreenToWorldPoint(Input.mousePosition)`，再走 `WorldToCell`
  > **注意**：正交相机下 `ScreenToWorldPoint` 的 `z` 需取 `-Camera.main.transform.position.z` 才落在 `z=0` 平面
- 塔/怪的**位置 = 世界坐标**（`Transform.position`），不再有 `anchoredPosition`
- 寻路数据层（`Point`）只保存 `row/col` 与 `Vector2 center`，**不持有 GameObject 引用**（解耦数据与视图，这是 v1.0 的设计缺陷）


### 2.4 单局核心循环（目标态）

```
进入关卡（读 TBLevel：初始金币 / 初始生命 / 回合列表 / 棋盘布局）
      ↓
[准备阶段] 倒计时 or 点击「开始」
      ↓
[回合进行] 按 TBWave 定时生成怪物 → 怪物沿 A* 路径在棋盘上移动
      ↑                                        ↓
      │                          ┌─── 被塔击杀 ─→ +金币
      │                          └─── 走到终点 ─→ -生命
      │                                        ↓
      │                            生命 ≤ 0 ? ─→ 【失败】
      │
      └── 波次间隙：玩家建塔（-金币）→ 重算 A* → 怪物改道
      ↓
本回合怪物清空 ─→ 还有下一回合？─是→ 下一回合
                                └─否→ 【胜利】
```
（M0 只有 1 个回合，走一遍即结束）

---

## 3. 配置表驱动设计

> **需求 3 + 需求 4 的落实章节。** 本章是本次重构的核心之一：项目内与塔防相关的**所有可变数值**都必须进配置表，代码中不允许出现硬编码的业务数值。

### 3.1 配置表位置与工具链（`D:\FreedomTower\Luban`）

**所有配置表的源文件都在工程根目录下的 `Luban` 文件夹内**，不在 `Assets` 下（`Assets` 内只有生成产物）。

#### 3.1.1 目录结构

```
D:\FreedomTower\
├── Luban\                                  ★ 配置表根目录
│   ├── gen_code_json.bat                    ★ 一键导出脚本（双击运行）
│   ├── Config\
│   │   ├── Datas\                           ★★ 【策划编辑源表】Excel 源文件
│   │   │   ├── __tables__.xlsx              表注册（全名/类名/索引/分组）
│   │   │   ├── __enums__.xlsx               枚举定义
│   │   │   ├── __beans__.xlsx               结构体定义
│   │   │   ├── EnemyData.xlsx               怪物属性表  → TBEnemyData
│   │   │   ├── EnemyList.xlsx               波次编组表  → TBEnemyList
│   │   │   ├── RoundData.xlsx               回合表      → TBRoundData
│   │   │   ├── SceneInfo.xlsx               关卡表      → TBSceneInfo
│   │   │   └── TowerInfo.xlsx               防御塔表    → TBTowerInfo
│   │   ├── Defines\
│   │   │   └── __root__.xml                 ★ 导出配置（分组、模块名、服务）
│   │   └── Gen\                             生成的代码副本（备用）
│   └── Tools\                               Luban 工具链（已随仓库提交）
│       ├── Luban.ClientServer\              ★ 导出用命令行工具
│       ├── Luban.Client\
│       ├── LubanAssistant\
│       ├── Excel2TextDiff\
│       └── build-luban-server.bat
│
└── Assets\
    ├── Gen\                                 ★ 生成的 C# 配置类（命名空间 cfg）
    │   ├── Tables.cs                             总入口
    │   ├── TBEnemyData.cs / EnemyData.cs
    │   ├── TBEnemyList.cs / EnemyList.cs
    │   ├── TBRoundData.cs / RoundData.cs
    │   ├── TBSceneInfo.cs / SceneInfo.cs
    │   ├── TBTowerInfo.cs / TowerInfo.cs
    │   └── ...
    ├── LubanLib\                            运行时反序列化库（Bright.Serialization + SimpleJSON）
    └── StreamingAssets\
        └── json\                             ★ 生成的数据文件（运行时读取）
            ├── tbenemydata.json
            ├── tbrounddata.json
            ├── tbenemylist.json
            ├── tbsceneinfo.json
            └── tbtowerinfo.json
```

#### 3.1.2 关键约定

| 项 | 约定 |
|---|---|
| 源表位置 | **`D:\FreedomTower\Luban\Config\Datas\*.xlsx`**（唯一的编辑入口） |
| 导出脚本 | `D:\FreedomTower\Luban\gen_code_json.bat`（工作目录必须是 `Luban\`） |
| 生成代码 | `Assets/Gen/` — **全部为生成产物，禁止手改**（改表后重导会覆盖） |
| 生成数据 | `Assets/ConfigJson/*.json` |
| 表注册 | 新增表必须先在 `__tables__.xlsx` 里登记一行，否则不会被导出 |
| 模块名 | `__root__.xml` 中 `<topmodule name="cfg"/>` → 所有生成类在 `cfg` 命名空间 |
| 分组 | `-s all` 导出 c/s/e 全分组；单机项目实际只用 client 组 |
| 文件命名 | 生成的数据文件名 = 表名全小写（`TBEnemyData` → `tbenemydata.json`），**与 `DataTables.cs` 中 `Reader("...")` 的字符串必须完全一致** |
| 临时文件 | 编辑 Excel 时产生的 `~$*.xlsx` 是 Office 锁文件，**不应提交**（已加入 `.gitignore` 的待办项） |

#### 3.1.3 导出命令

`gen_code_json.bat` 内容（已存在于仓库）：

```bat
set WORKSPACE=..
set GEN_CLIENT=%WORKSPACE%\Luban\Tools\Luban.ClientServer\Luban.ClientServer.exe
set CONF_ROOT=%WORKSPACE%\Luban\Config

%GEN_CLIENT% -j cfg --^
 -d %CONF_ROOT%\Defines\__root__.xml ^
 --input_data_dir %CONF_ROOT%\Datas ^
 --output_code_dir %WORKSPACE%/Assets/Gen ^
 --output_data_dir ..\Assets\StreamingAssets\json ^
 --gen_types code_cs_unity_json,data_json ^
 -s all
pause
```

等价的手工命令（便于 CI 或脚本化）：

```bash
cd D:/FreedomTower/Luban
./Tools/Luban.ClientServer/Luban.ClientServer.exe -j cfg \
  -d ../Luban/Config/Defines/__root__.xml \
  --input_data_dir ../Luban/Config/Datas \
  --output_code_dir ../Assets/Gen \
  --output_data_dir ../Assets/ConfigJson \
  --gen_types code_cs_unity_json,data_json \
  -s all
```

**导出后必做的自检（建议写成 Editor 菜单项）**
1. `Assets/ConfigJson/` 下 8 个文件都存在且非空，且能被按 `TextAsset` 加载
2. 每个文件能被 `JSONNode.Parse` 成功解析
3. 关键表记录数 > 0（`TBEnemy` ≥ 1、`TBTower` ≥ 1、`TBLevel` ≥ 1）
4. 交叉引用完整（`TBWave.enemyIds` 指向的 `TBEnemy.id` 都存在；`TBLevel.roundIds` 指向的回合都存在）

> **⚠️ 历史坑位**：`.gitignore` 曾含 `*.json` 规则，导致导出的配置文件永远无法提交。该规则已于提交 `e1d8582f9` 移除。**今后严禁使用宽泛的 `*.json` 通配符。**

### 3.2 运行时的配置加载方式

配置数据 json 的加载有两条路，本文档**推荐方案 B**：

| 方案 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| A. StreamingAssets 直读 | 保留现状，读 `Application.streamingAssetsPath/json/*.json` | 简单；改配置不用重新打包 | 与 AB 体系割裂；Android 下需 `UnityWebRequest` |
| **B. 打进 AB（✅ 推荐）** | 把 json 作为 `TextAsset` 打进 `bundle_config`，走 §4 的 AB 系统 | **统一资源管理**；包体可控；与需求 7 一致 | 改配置需重新打包（开发期由编辑器模拟模式缓解） |

**推荐实现（方案 B）**

```csharp
// Assets/Scripts/Data/DataTables.cs 改造要点
public class DataTables : MonoBehaviour
{
    public TBEnemy   TBEnemy   { get; private set; }
    public TBTower   TBTower   { get; private set; }
    public TBWave    TBWave    { get; private set; }
    public TBLevel   TBLevel   { get; private set; }
    public TBLevelMap TBLevelMap { get; private set; }
    public TBGlobal  TBGlobal  { get; private set; }

    public void LoadAll(Action onDone)
    {
        // 一次异步加载整个 config bundle
        ResLoader.Instance.LoadAssetAsync<TextAsset>("config", "config", (ta) =>
        {
            JSONNode root = JSONNode.Parse(ta.text);
            TBEnemy = new TBEnemy(root["tbenemy"]);
            // ... 逐表构造
            ValidateTables();     // ★ 自检，失败给出明确日志
            onDone?.Invoke();
        });
    }
}
```

**统一的表加载器基类**（消除 6 份重复的 `Reader` 协程）：

```csharp
public abstract class TableBase
{
    protected Dictionary<int, IBean> _dataMap = new(64);
    public int Count => _dataMap.Count;

    protected void LoadFrom(JSONNode root, string key, Func<JSONNode, IBean> ctor)
    {
        var arr = root[key];
        if (arr == null || !arr.IsArray || arr.Count == 0)
        {
            Debug.LogError($"[Config] 表 {key} 为空或缺失，请检查 Luban 导出结果");
            return;
        }
        for (int i = 0; i < arr.Count; i++) { var b = ctor(arr[i]); _dataMap[b.Id] = b; }
    }
    public IBean Get(int id) => _dataMap.TryGetValue(id, out var b) ? b : null;   // ★ 返回 null 而非抛异常
}
```

### 3.3 配置表结构设计

#### 3.3.1 表关系总览

```
TBLevel ──roundIds──→ TBRound ──waveIds──→ TBWave ──enemyIds──→ TBEnemy
   │                                                                  │
   └──mapId──→ TBLevelMap（棋盘布局）                                 │
                                                                      │
TBTower ──bulletId──→ TBBullet ──hitRadius/effect──────────────────────┘
   │
   └──upgradeTo──→ TBTower（自引用，形成升级链）

TBGlobal（全局参数表，单行）
```

#### 3.3.2 `TBEnemy`（怪物）— 扩展现有 `TBEnemyData`

| 字段 | 类型 | 说明 | 状态 |
|---|---|---|---|
| id | int | 主键 | 已有 |
| name | string | 展示名 | 已有 |
| **resName** | string | AB 资源名（对应 §4 地址表键） | ★新增（原 `name` 兼任资源名，语义混用，拆开） |
| type | int | 敌人类型枚举（1 普通 / 2 快速 / 3 强壮 / 4 护甲 / 5 飞行 / 6 Boss） | 已有（枚举待扩） |
| speed | float | 移动速度（**像素/秒**，2D 单位） | 已有（需改单位口径） |
| hp | float | 生命值 | 已有 |
| **armor** | float | 护甲减伤（0–1，最终伤害 = damage × (1 − armor)） | ★新增（M2 用，M0 可缺省为 0） |
| **reward** | int | 击杀奖励金币 | ★新增（M0 必填，缺失则取 `TBGlobal.defaultReward`） |
| **damageToPlayer** | int | 漏怪扣除玩家生命 | ★新增（M0 必填，缺失取默认 1） |
| **scale** | float | 显示缩放 | ★新增 |
| **isFlying** | bool | 是否飞行（无视迷宫走直线） | ★新增（M2） |
| **animController** | string | AnimatorController 资源名（如 `"Rat"` → `_Common/Animations/Rat/Controller`）。**不同家族各有独立 Controller，切换怪物类型时必须替换 `runtimeAnimatorController`** | ★新增（**M0 需要**，用于驱动 Ready/Walk/Attack/Death 四态动画） |
| **bodyRadius** | float | 受击半径（**供 §5 距离判定使用**，单位：格） | ★新增（**M0 必填**） |
| interval | int | 出现间隔 | 已有（保留兼容） |
| desc | string | 备注 | ★新增 |

#### 3.3.3 `TBTower`（防御塔）— 改造现有 `TBTowerInfo`

| 字段 | 类型 | 说明 | 状态 |
|---|---|---|---|
| id | int | 主键 | 已有 |
| type | **int** | 塔类型枚举（1 单体 / 2 AOE / 3 减速 / 4 穿透 / 5 激光） | ★改造（原 string，改枚举更严谨） |
| name | string | 展示名 | 已有 |
| **resName** | string | AB 资源名 | ★新增（原 `path` 是 `Resources` 路径，AB 化后重命名） |
| level | int | 等级 1–3 | 已有 |
| **upgradeTo** | int | 下一等级 id（0 = 满级） | ★新增（M2） |
| radius | **float** | 攻击半径（**单位：格**，便于与棋盘尺寸解耦） | ★改造（原 int） |
| power | **float** | 攻击力 | ★改造（原 int） |
| CD | float | 攻击间隔（**毫秒**） | 已有 |
| prices | int | 建造/升级价格 | 已有 |
| **sellPrice** | int | 出售返还金币 | ★新增（M2） |
| **bulletId** | int | 子弹 id → `TBBullet` | ★新增（**M0 必填**） |
| **targetMode** | int | 索敌策略：0 路径最靠前 / 1 距离最近 / 2 血量最高 | ★新增（M0 用 0） |
| **searchIntervalMs** | int | 索敌间隔（毫秒，默认 100） | ★新增（§5.3 节流） |
| **rotateSpeed** | float | 炮管转向速度（度/秒） | ★新增（原硬编码在 `TowerCofig`） |
| **effectType / effectValue** | int/float | 特殊效果（如减速比例、持续时长） | ★新增（M2） |
| desc | string | 备注 | ★新增 |

> **当前数据状态**：`TowerInfo.xlsx` 已有 `NormalTower` 的 3 个等级（level 1/2/3，radius 3/4/6，power 10/12/15，CD 300/200/100，prices 20/30/50）。
> **M0 只用 id=1（level=1）**，但升级链数据已就绪，M2 接 `upgradeTo` 即可。

#### 3.3.4 `TBBullet`（子弹）★全新表

2D 塔防下子弹行为需要独立配置化（3D 时代完全硬编码）。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 主键 |
| name | string | 展示名 |
| resName | string | AB 资源名 |
| speed | float | 飞行速度（**像素/秒**） |
| hitRadius | float | 命中判定半径（**像素**，供 §5.4 距离判定） |
| lifeTimeMs | int | 最大存活时间（超时回收，防子弹追不上目标时无限飞） |
| pierce | int | 穿透数量（0 = 命中即消失，>0 = 可继续穿透，M2） |
| aoeRadius | float | 爆炸半径（0 = 单体，M2） |
| effectType | int | 效果类型（0 无 / 1 减速 / 2 持续伤害，M2） |
| effectValue | float | 效果参数 |
| resScale | float | 显示缩放 |

**M0 最少配置 1 行**（普通子弹：speed 900、hitRadius 24、lifeTimeMs 3000）。

#### 3.3.5 `TBWave`（波次编组）+ `TBRound`（回合）

沿用现有 `TBEnemyList` / `TBRoundData` 结构，重命名以贴合 2D 语义（也可保持原名，二选一，**改名需同步 `__tables__.xlsx` 与 `DataTables` 的 key**）：

**`TBWave`**（原 `TBEnemyList`）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 主键 |
| enemyIds | (list#sep=,),int | 本波出现的怪物 id 列表（**按顺序生成**） |
| startDelayMs | int | 本波开始的绝对延迟 |
| spawnIntervalMs | float | 波内相邻两只怪的间隔（**毫秒**） |
| desc | string | 备注 |

**`TBRound`**（原 `TBRoundData`）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 主键 |
| waveIds | (list#sep=,),int | 本回合包含的波次 id 列表 |
| intervalMs | int | 回合开始前的准备延迟 |
| **rewardGold** | int | 回合通关奖励（M1） |

#### 3.3.6 `TBLevel` + `TBLevelMap`（关卡 + 棋盘布局）★**替代原 ASCII 地图文件**

> **需求 2 的落实**：v1.0 的方案是「`Assets/StreamingAssets/Map/Map{n}.txt` ASCII 文件 + `AStarManager.InitMap` 逐字符生成 3D 物件」。
> **该方案整体废弃**，原因：
> 1. 文本文件游离于配置体系之外，策划无法在一个地方看到全部关卡数据
> 2. 依赖 StreamingAssets 目录结构，与 AB 化（需求 7）方向冲突
> 3. 3D 物件生成方式在 UGUI 下完全不适用
>
> **新方案**：棋盘布局进配置表，运行时由 `BoardView` 一次性生成**世界空间 `SpriteRenderer` 格子**。

**`TBLevel`**（扩展原 `TBSceneInfo`）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 主键 |
| name | string | 关卡名 |
| roundIds | (list#sep=,),int | 本关卡的回合列表 |
| **mapId** | int | 引用的棋盘布局 id → `TBLevelMap` |
| **backgroundRes** | string | 背景图 AB 资源名 |
| **initialGold** | int | 初始金币（替代 `GlobalConst.GoldCoin`） |
| **initialHp** | int | 初始生命（替代 `GlobalConst.PlayerHp`） |
| **waveIntervalMs** | int | 回合间准备时间（M1） |
| **difficulty** | int | 难度标签（1–3，用于关卡选择显示） |
| 已废弃 | — | `CameraPosition` / `CameraRotration` / `MapPosition` / `EenemyPosition` / `PointScale` — **2D 固定视角下不需要**，可保留字段但代码不再读取 |

**`TBLevelMap`**（★全新表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 主键 |
| levelId | int | 所属关卡 |
| cols | int | 列数 |
| rows | int | 行数 |
| cells | (list#sep=\|),string | **每行一个字符串**，长度 = cols，字符集见下 |
| desc | string | 备注 |

**格子字符集**（沿用原 ASCII 约定的语义，但改为配置表内配置）

| 字符 | 含义 | 可建造 | 可通行 |
|---|---|---|---|
| `S` | 起点（Spawn） | ✗ | ✓ |
| `E` | 终点（End） | ✗ | ✓ |
| `.` | 空地（可建造地砖） | ✓ | ✓ |
| `#` | 障碍（不可通行） | ✗ | ✗ |
| `X` | 空洞（不可通行且不可建造） | ✗ | ✗ |
| `P` | 装饰地砖（可通行、不可建造） | ✗ | ✓ |

**配置示例**（`TBLevelMap` id=1，12×8 棋盘，`|` 分隔每行）

```
id | levelId | cols | rows | cells                                                                          | desc
1  | 1       | 12   | 8    | #..S....#..|>.|..#....E.|..#..........|..#.....|...|.....|.. | #...  | 第一关测试棋盘
```

> **设计建议**：`cells` 使用 `(list#sep=|),string`。地图字符集不含 `|`，因此分隔是安全的。
> **备选方案（棋盘很大时）**：改用稀疏表 `TBLevelCell(id, levelId, row, col, cellType)`，只配非 `.` 的格子，可显著减小表体积。M0 用主方案即可。

#### 3.3.7 `TBGlobal`（全局参数表）★全新

把 `GlobalConst` / `TowerCofig` 中所有硬编码迁移到表（**需求 4：尽可能配置表驱动**）。

| 字段 | 类型 | 说明 | 迁移来源 |
|---|---|---|---|
| id | int | 主键（固定为 1，单行表） | — |
| defaultReward | int | 怪物未配 `reward` 时的默认击杀奖励 | 新增 |
| defaultDamageToPlayer | int | 怪物未配 `damageToPlayer` 时的默认漏怪伤害 | 新增 |
| defaultBodyRadius | float | 默认受击半径（格） | 新增 |
| defaultBulletSpeed | float | 默认子弹速度（像素/秒） | `GlobalConst.BulletSpeed = 25` |
| defaultBulletLifeMs | int | 默认子弹存活时间 | `GlobalConst.BulletResetTimeInterval = 3` |
| cellSize | float | 棋盘格子像素尺寸 | 新增 |
| boardPadding | float | 棋盘边距 | 新增 |
| enemyPoolSize | int | 怪物对象池初始容量 | 新增 |
| bulletPoolSize | int | 子弹对象池初始容量 | 新增 |
| maxEnemyAlive | int | 同屏怪物上限（性能保护） | 新增 |
| searchIntervalMs | int | 索敌默认间隔（毫秒） | 新增 |
| firstRoundDelayMs | int | 开局准备时间 | 新增 |
| targetFrameRate | int | 目标帧率 | 新增 |

#### 3.3.8 `TBEconomy`（经济，可选）→ 建议**并入 `TBLevel` + `TBGlobal`**

M0 不需要独立经济表：初始金币/生命来自 `TBLevel`，击杀奖励来自 `TBEnemy.reward`，建塔花费来自 `TBTower.prices`。M1 若需要"难度系数""金币增长率"等再加表。

### 3.4 配置驱动的覆盖范围（**红线清单**）

以下内容**必须**来自配置表，代码中不允许写死：

| 类别 | 必须进表的项 | 对应表 |
|---|---|---|
| **怪物** | 血量、速度、类型、护甲、受击半径、击杀奖励、漏怪伤害、显示缩放、资源名、动画前缀 | `TBEnemy` |
| **防御塔** | 类型、等级、攻击力、攻击半径、攻击间隔、建造/升级价格、出售价、子弹 id、索敌策略、转向速度、效果参数、资源名 | `TBTower` |
| **子弹** | 速度、命中半径、存活时间、穿透、爆炸半径、效果、资源名 | `TBBullet` |
| **波次** | 敌人编组、波内间隔、开始延迟、回合奖励 | `TBWave` / `TBRound` |
| **关卡** | 初始金币、初始生命、回合列表、棋盘布局、背景资源、难度、准备时间 | `TBLevel` / `TBLevelMap` |
| **经济** | 初始金币、击杀奖励、建塔花费、出售返还、回合奖励 | 分散在上述各表 |
| **全局** | 格子尺寸、对象池容量、同屏上限、索敌间隔、默认值兜底 | `TBGlobal` |
| **棋盘布局** | 起终点位置、可建造格、障碍格 | `TBLevelMap` |

**允许保留在代码里的**
- 纯表现参数**默认值**（如动画时长、飘字上浮距离）—— 但若策划需要调，仍应进表
- 算法参数（A* 启发函数权重、空间哈希 cell 尺寸）—— 属于实现细节
- UI 布局常量（参考分辨率 1920×1080、锚点）—— 属于表现层配置

### 3.5 容错与缺省策略（应对"功能缺失不应阻塞"）

需求 5 明确功能可缺失。因此配置读取**必须零崩溃**：

```csharp
/// 统一的安全读取工具
public static class Cfg
{
    public static float Float(JSONNode n, string key, float def)
        => (n != null && n[key] != null && n[key].IsNumber) ? n[key].AsFloat : Log(def, key);

    public static int Int(JSONNode n, string key, int def)
        => (n != null && n[key] != null && n[key].IsNumber) ? n[key].AsInt : Log(def, key);

    public static T Get<T>(Dictionary<int, T> map, int id, string tableName) where T : class
    {
        if (map == null || !map.TryGetValue(id, out var v) || v == null)
        {
            Debug.LogError($"[Config] {tableName} 中找不到 id={id}，请检查 Luban 配置");
            return null;
        }
        return v;
    }
}
```

**规则**
1. 缺失字段 → 取默认值 + `Debug.LogWarning`，**不抛异常**
2. 缺失整行（id 不存在）→ 返回 `null` + `Debug.LogError`，调用方必须判空
3. 交叉引用断裂（如 `TBTower.bulletId` 指向不存在的子弹）→ 回退到 `TBGlobal` 默认子弹 + 告警
4. `TBEnemy` 只有 1 行、`TBTower` 只有 1 行、`TBWave` 只有 1 行 —— **都能正常跑通 M0**
5. 启动时执行 `ValidateTables()`，把问题一次性汇总打印，而不是散落各处报错

---

## 4. AB（AssetBundle）资源加载系统

> **需求 7 的落实章节。** 现有 `Core/ResourcesManager.cs` 用 `Resources.Load`，存在三个问题：
> 1. `Resources` 目录下所有内容**无条件打进包体**，无法按需分包，包体不可控
> 2. 无法做资源热更与增量更新
> 3. 已被 Unity 官方明确不推荐（大型项目首包膨胀的主因）
>
> 因此按需求改造为 **AssetBundle** 形式。

### 4.1 设计目标与约束

| 目标 | 说明 |
|---|---|
| 单机免服务器 | AB 包放 `StreamingAssets`，随包发布，不依赖 CDN |
| 开发期高效 | **编辑器下默认直读资源，不必每次打 AB**（否则开发效率灾难） |
| 接口统一 | 业务层只依赖 `IResLoader`，不感知底层是 `AssetDatabase` 还是 `AssetBundle` |
| 按需加载 | 按功能分包（config / tower / enemy / bullet / ui / level） |
| 可卸载 | 引用计数 + `AssetBundle.Unload(false)`，切关卡时释放 |
| 依赖安全 | 用 `AssetBundleManifest` 正确处理共享依赖，杜绝丢资源/重复加载 |

### 4.2 打包粒度与命名

| Bundle 名 | 内容 | 加载时机 | 是否常驻 |
|---|---|---|---|
| `config` | `ConfigJson/*.json`（TextAsset） | 启动 | ✅ 常驻 |
| `ui_common` | 公共 UI 预制体、图集、字体 | 启动 | ✅ 常驻 |
| `ui_hud` | 战斗 HUD、Tips、回合结果面板 | 进入关卡 | 关卡内常驻 |
| `level_1` … `level_n` | 各关卡背景图 + 棋盘装饰 | 进入对应关卡 | 关卡结束卸载 |
| `tower_normal` | `Tower_Normal` 预制体 + 炮座/炮管贴图 | 进入关卡 | 关卡内常驻 |
| `enemy_common` | M0 的 1 种怪物 + 血条资源 | 进入关卡 | 关卡内常驻 |
| `bullet_normal` | 普通子弹预制体 + 贴图 | 进入关卡 | 关卡内常驻 |
| `atlas_battle` | 战斗用 SpriteAtlas（塔/怪/子弹小图） | 进入关卡 | 关卡内常驻 |

**命名规范**：全小写下划线，`<类别>_<名字>`。**禁止在 bundle 名里带平台/版本号**（由构建脚本按平台分目录）。

**产物路径**
```
Assets/StreamingAssets/AB/
├── Android/
│   ├── ab_manifest                  ← 总清单（AssetBundleManifest）
│   ├── config.ab
│   ├── ui_common.ab
│   └── ...
├── Windows/
│   ├── ab_manifest
│   └── ...
└── manifest.json                    ← 自定义清单（版本、包名、hash、大小）
```

> 单机定位下用 `StreamingAssets` 免服务器；若 M5 需要热更，把目录换成 CDN 地址即可，**接口不变**。

### 4.3 资源地址表（替代 `AssetData`）

现有 `Data/AssetData.cs` 是"名称 → `Resources` 路径"字典，改为"逻辑名 → (bundle 名, asset 名)"。

```csharp
[Serializable]
public struct ResAddress
{
    public string Bundle;   // 如 "tower_normal"
    public string Asset;    // 如 "Tower_Normal"
}

public static class ResTable
{
    public static readonly Dictionary<string, ResAddress> Map = new()
    {
        // 配置
        { "config",            new ResAddress{ Bundle="config",          Asset="config" } },
        // 塔
        { "Tower_Normal",      new ResAddress{ Bundle="tower_normal",    Asset="Tower_Normal" } },
        // 子弹
        { "Bullet_Normal",     new ResAddress{ Bundle="bullet_normal",   Asset="Bullet_Normal" } },
        // 怪物
        { "Enemy_Rat",         new ResAddress{ Bundle="enemy_common",    Asset="Enemy_Rat" } },
        // UI
        { "HudView",           new ResAddress{ Bundle="ui_hud",          Asset="HudView" } },
        { "TipsView",          new ResAddress{ Bundle="ui_hud",          Asset="TipsView" } },
        { "RoundResultView",   new ResAddress{ Bundle="ui_hud",          Asset="RoundResultView" } },
        // 关卡
        { "Level_1_Bg",        new ResAddress{ Bundle="level_1",         Asset="Level_1_Bg" } },
        { "Cell_Tile",         new ResAddress{ Bundle="level_1",         Asset="Cell_Tile" } },
    };

    public static bool TryGet(string logicalName, out ResAddress addr)
        => Map.TryGetValue(logicalName, out addr);
}
```

> **关键收益**：业务代码里写的是**逻辑名**（如 `Tower_Normal`），配置表里的 `resName` 也写逻辑名。**换 bundle 划分时只需改这张表，业务与配置表都不用动。** 这正是需求 4 与需求 7 的衔接点。

### 4.4 运行时接口设计

```csharp
namespace FTProject
{
    public interface IResLoader
    {
        void Init(Action onDone);

        /// 同步加载（仅建议用于极小资源或已在内存中的情况）
        T Load<T>(string logicalName) where T : Object;

        /// 异步加载（推荐）
        void LoadAsync<T>(string logicalName, Action<T> onDone) where T : Object;

        /// 实例化（内部处理 bundle 引用计数 + 池化接入）
        GameObject Instantiate(string logicalName, Transform parent);

        /// 释放（引用计数归零后真正卸载）
        void Release(string logicalName);
        void ReleaseBundle(string bundleName);

        /// 预加载（进关卡前把本关需要的 bundle 一次性预热）
        void Preload(string[] bundleNames, Action onDone);
    }
}
```

**加载流程（异步，含依赖处理）**

```
LoadAsync("Tower_Normal")
  → ResTable 查到 { bundle: tower_normal, asset: Tower_Normal }
  → 若 bundle 未加载：
       读 AssetBundleManifest.GetAllDependencies("tower_normal")
       → 递归先加载所有依赖 bundle（引用计数 +1）
       → AssetBundle.LoadFromFileAsync 加载自身
  → 引用计数 +1
  → bundle.LoadAssetAsync<T>("Tower_Normal")
  → 回调返回；asset 级引用计数 +1
```

**两个实现**

| 实现 | 生效条件 | 行为 |
|---|---|---|
| `EditorResLoader` | `#if UNITY_EDITOR && !FORCE_AB`（默认） | 用 `AssetDatabase.LoadAssetAtPath` 直读；**引用计数空实现**；改资源即时生效，不用打包 |
| `BundleResLoader` | 打包后 / 勾选 `FORCE_AB` | 真实读 AB；完整依赖与引用计数 |

> **这是本方案最关键的工程决策**：编辑器模拟模式让开发期保持"改完就能跑"的体验，同时生产环境走真正的 AB。Unity 官方与主流商业项目均采用此模式。

### 4.5 引用计数与卸载

```csharp
class BundleRef
{
    public AssetBundle Bundle;
    public int RefCount;          // bundle 级引用（被谁依赖 + 被业务直接使用）
    public Dictionary<string,int> AssetRefs = new();   // asset 级引用
}
```

**规则**
1. bundle 被依赖时其引用计数也要 +1，否则父 bundle 卸载会带走依赖
2. `Release` 使 asset 计数 -1，归零则从缓存移除（bundle 仍留）
3. `ReleaseBundle` 使 bundle 计数 -1，归零时：
   ```csharp
   bundle.Unload(false);        // ★ false：保留已 load 的 asset，避免"资源变紫/Missing"
   Resources.UnloadUnusedAssets();   // 延迟到帧末，回收无引用 asset
   ```
   **严禁 `Unload(true)`** —— 会让正在使用的资源变成 Missing，是 AB 系统最常见的线上事故来源。
4. **常驻包**（`config`、`ui_common`）永不解引用，用 `AddPersistent` 标记
5. 切关卡时统一 `ReleaseBundle` 本关的 5 个包，并回收对象池与 SpriteAtlas 引用

**与对象池的配合（易错点）**
- 池化对象（怪物、子弹）在切关卡时**不 Destroy**，只隐藏并归池
- 但它们引用的 sprite/prefab 来自本关 bundle —— 因此**卸 bundle 前必须先清空池并 `Unload(false)`**，顺序不能颠倒
- 卸载时机放在"下一关加载完成后 + 帧末"，避免卸载瞬间画面闪白

### 4.6 编辑器内的 AB 构建脚本

新增 `Assets/Editor/BuildAssetBundles.cs`：

```csharp
[MenuItem("Tools/资源工具/构建 AssetBundle/当前平台")]
public static void BuildCurrent()
{
    BuildTarget target = EditorUserBuildSettings.activeBuildTarget;
    Build(target);
}

public static void Build(BuildTarget target)
{
    string outDir = $"Assets/StreamingAssets/AB/{target}";
    Directory.CreateDirectory(outDir);

    var options = BuildAssetBundleOptions.ChunkBasedCompression      // LZ4，加载快
                | BuildAssetBundleOptions.DeterministicAssetBundle;  // 稳定增量
    //  ★ 必须显式指定 Manifest 所在包名，否则依赖信息无法读取
    var manifest = BuildPipeline.BuildAssetBundles(
        outDir, BuildAssetBundleOptions.None, target);
    BuildPipeline.BuildAssetBundles(
        outDir,
        Array.Empty<AssetBundleBuild>(),
        options | BuildAssetBundleOptions.ForceRebuildAssetBundle,
        target);

    // 生成自定义清单（包名/大小/哈希），供运行时与版本比对
    WriteManifest(manifest, outDir);
    AssetDatabase.Refresh();
    Debug.Log($"[AB] 构建完成 → {outDir}，共 {manifest.GetAllAssetBundles().Length} 个包");
}
```

**AB 标记方式（两种二选一，推荐前者）**

1. **代码标记**（推荐）：在 `AssetImporter` 层用脚本按目录规则自动打标，避免人工漏标
   ```csharp
   // Assets/Editor/ABNameSetter.cs
   // Resources/Tower/*          → tower_*      规则：目录名映射
   // Assets/_UIAssets/Tower/**  → tower_normal
   // 等等
   ```
2. **Inspector 手工标记**：每个资源底部 AssetBundle 栏填写 `bundle/asset` —— 易漏、易冲突，**不推荐**

### 4.7 从 `ResourcesManager` 迁移的步骤

| 步骤 | 内容 |
|---|---|
| 1 | 新增 `Assets/Scripts/Core/Res/IResLoader.cs`、`EditorResLoader.cs`、`BundleResLoader.cs`、`ResTable.cs` |
| 2 | 把 `AssetData.AssetDictionary` 的内容**逐条翻译**到 `ResTable` |
| 3 | 全工程替换调用点：`ResourcesManager.Instance.LoadAndInitGameObject(name, parent, ...)` → `ResLoader.Instance.Instantiate(name, parent)` |
| 4 | `ResourcesManager.cs` 标记 `[Obsolete]` 保留一个版本，最后删除 |
| 5 | 新增 `Assets/Editor/BuildAssetBundles.cs` 与 `ABNameSetter.cs` |
| 6 | 验证：编辑器下（模拟模式）跑通全流程 → 切 `FORCE_AB` 再跑一遍 → 出包跑一遍 |
| 7 | 清理 `Assets/Resources/` 剩余内容（`DOTweenSettings.asset` 需保留，DOTween 依赖它） |

**调用点清单（当前依赖 `ResourcesManager` 的位置）**

| 文件 | 用途 |
|---|---|
| `Core/UI/UIManager.cs` | 加载 UI 面板预制体 |
| `Enemy/EnemyManager.cs` | 加载怪物 prefab |
| `Bullet/BulletManager.cs` | 加载子弹 prefab |
| `Tower/TowerManager.cs` | 加载塔 prefab |
| `GameSceneLauncher.cs` | 加载地图/棋盘对象 |
| `AStarWrapper/AStarManager.cs` | 加载格子/路径箭头 prefab |

---

## 5. 战斗判定优化（去物理化）

> **需求 8 的落实章节。** 现状：塔的索敌靠 `Targetter` 上的 `SphereCollider`（`isTrigger`）+ `OnTriggerEnter/OnTriggerExit` 维护敌人列表；子弹命中同样靠 `OnTriggerEnter`。在低端机上这是明确的性能热点。

### 5.1 现有实现为什么慢

#### 5.1.1 现状代码

| 位置 | 机制 |
|---|---|
| `Tower/Tower/Targetter.cs` | 塔上挂 `SphereCollider`，`OnTriggerEnter` 把进入范围的敌人加入 `_enemyList`，`OnTriggerExit` 移除；`GetNearsetTarget()` 返回 `_enemyList[0]` |
| `Bullet/BaseBullet.cs` | 子弹 `OnTriggerEnter` 命中后 `BaseEnemy.Hurt(1)` 并 `Reset()` |
| 判定方式 | `other.gameObject.name.Contains("Enemy")` 字符串匹配 |

#### 5.1.2 性能问题逐条

| # | 问题 | 说明 |
|---|---|---|
| **P1** | **物理引擎的宽相/窄相开销** | 塔与子弹都是触发器，Unity 物理引擎每帧要对所有触发器做 Broadphase（AABB 排序）+ Narrowphase；2D 项目里这一步纯属浪费 |
| **P2** | **触发器对数量随规模平方增长** | N 座塔 × M 只怪 → 最坏 O(N·M) 个触发器对；再加 B 颗子弹 × M 只怪。100 塔 + 200 怪 + 300 子弹时，每帧潜在检测对数达到数万级 |
| **P3** | **`OnTriggerEnter` 的托管调用开销** | 每个进入/离开事件都是一次跨原生↔托管的调用 + 委托回调；`OnTriggerExit` 触发频繁（怪快速穿过塔范围时进进出出）时抖动明显 |
| **P4** | **列表维护成本与泄漏** | `_enemyList` 是 `List<GameObject>`，无空引用清理；敌人被回收（`SetActive(false)`）后若未正确触发 `Exit`，列表残留失效引用 |
| **P5** | **字符串比较** | `name.Contains("Enemy")` 每帧对每个触发回调做一次字符串匹配，且对命名强依赖（脆弱） |
| **P6** | **索敌语义错误导致行为 Bug** | `GetNearsetTarget()` 名为"最近"实为"最先进入"，且无空列表检查 → **空列表时 `IndexOutOfRange` 直接崩溃** |
| **P7** | **每对象独立订阅 `UpdateEvent`** | 每个塔/怪/子弹都 `EventDispatcher.AddEventListener(UpdateEvent, ...)`，全局事件分发每帧遍历全部监听者并做一次虚调用，随对象数线性增长且不可控 |

#### 5.1.3 优化目标（量化）

| 指标 | 现状（估） | 目标 |
|---|---|---|
| 索敌复杂度 | O(N·M)（物理宽相） | **O(N·c)**，c = 邻域常数（≈9） |
| 命中判定 | 物理触发器 | **O(B)** 距离判定，无物理 |
| 每帧托管回调次数 | 受触发器事件影响，不可预测 | **可控**：塔索敌节流 + 子弹距离判定 |
| 100 塔 / 200 怪 / 300 弹 单帧 CPU | 未测（低端机掉帧） | **< 2 ms**（中端手机） |
| 崩溃风险 | 空列表 `IndexOutOfRange` | **零崩溃**（全部判空） |

### 5.2 新方案总览

**核心思想：2D 塔防不需要物理引擎。把"空间关系查询"从物理系统接管过来，用一个集中式战斗系统统一驱动。**

```
┌────────────────────────────────────────────────────────────┐
│  CombatSystem（新增，BaseManager<CombatSystem>）            │
│  ─ 唯一持有 Update 的模块，集中驱动塔与子弹                   │
│                                                            │
│  Update(dt):                                               │
│    1. EnemyGrid 同步（敌人移动后更新所在格子）                │
│    2. TowerTick(dt)  → 节流索敌 → 锁定目标 → 冷却好了就开火    │
│    3. BulletTick(dt) → 移动 + 距离命中判定 + 超时回收          │
├────────────────────────────────────────────────────────────┤
│  EnemyGrid（新增，均匀网格空间哈希）                          │
│  ─ cellSize = 2 格；Dictionary<int, List<BaseEnemy>>         │
│  ─ QueryCircle(center, radiusGrid) → 候选敌人列表             │
└────────────────────────────────────────────────────────────┘
        ▲                                    ▲
        │ 注册/注销 + 位置更新                 │ 查询候选
   EnemyManager                          TowerManager / BulletManager
```

**三个关键改造**
1. **移除全部 Collider 与 Rigidbody**（塔、怪、子弹都不再挂物理组件）
2. **集中式 tick 取代分散的 `UpdateEvent` 订阅**（解决 P7）
3. **空间哈希 + 距离判定取代物理查询**（解决 P1–P5）

### 5.3 索敌：空间哈希 + 路径进度优先

#### 5.3.1 均匀网格空间哈希

```csharp
public class EnemyGrid
{
    private readonly Dictionary<int, List<BaseEnemy>> _cells = new(256);
    private readonly float _cellSize;        // 世界（棋盘）单位，建议 = 2 × CellSize
    private readonly int _cols;

    public EnemyGrid(float cellSize, int cols) { _cellSize = cellSize; _cols = cols; }

    private int Key(int cx, int cy) => cy * _cols + cx;

    /// 敌人移动后调用：先算出新格子，与旧格子不同才迁移（避免每帧增删）
    public void Update(BaseEnemy e, Vector2 pos)
    {
        int cx = Mathf.FloorToInt(pos.x / _cellSize);
        int cy = Mathf.FloorToInt(pos.y / _cellSize);
        int key = Key(cx, cy);
        if (e.GridKey == key) return;            // ★ 关键：未跨格则零开销
        Remove(e);
        if (!_cells.TryGetValue(key, out var list)) _cells[key] = list = new List<BaseEnemy>(8);
        list.Add(e);
        e.GridKey = key;
    }

    /// 查询圆形范围覆盖到的所有格子，返回候选（含少量范围外元素，由调用方精确过滤）
    public void QueryCircle(Vector2 center, float radius, List<BaseEnemy> result)
    {
        result.Clear();
        int minX = Mathf.FloorToInt((center.x - radius) / _cellSize);
        int maxX = Mathf.FloorToInt((center.x + radius) / _cellSize);
        int minY = Mathf.FloorToInt((center.y - radius) / _cellSize);
        int maxY = Mathf.FloorToInt((center.y + radius) / _cellSize);
        for (int y = minY; y <= maxY; y++)
        for (int x = minX; x <= maxX; x++)
            if (_cells.TryGetValue(Key(x, y), out var list))
                result.AddRange(list);
    }
}
```

**cellSize 取值建议**：等于最大索敌半径的一半左右。本项目塔半径 3–6 格，取 `cellSize = 2 格` 时邻域约 3×3 ~ 7×7 个格子，`c` 稳定在 9–49 之间，且与全场怪物总数无关。

#### 5.3.2 索敌算法（分策略 + 节流 + 锁定）

```csharp
public enum TargetMode { FurthestAlongPath = 0, Nearest = 1, HighestHp = 2 }

// BaseTower 新增字段
private BaseEnemy _target;            // 当前锁定目标
private float _searchTimer;           // 索敌节流计时
private readonly List<BaseEnemy> _candidates = new(32);   // 复用的候选缓冲，避免每帧 GC

private void TickAttack(float dt)
{
    if (!_isBuildSuccess) return;

    // ① 目标有效性检查：失效立刻清空（死亡/回收/走出射程）
    if (_target != null && (!_target.IsAlive || !InRange(_target)))
        _target = null;

    // ② 节流索敌：有锁定目标时不重复搜索
    _searchTimer += dt;
    if (_target == null && _searchTimer >= _searchInterval)
    {
        _searchTimer = 0f;
        _target = FindTarget();
    }

    if (_target == null) return;                     // ★ 无目标不空放

    // ③ 炮管转向
    RotateBarrelTowards(_target.Position, dt);

    // ④ 冷却到了就开火
    _fireTimer += dt;
    if (_fireTimer >= _cooldown) { _fireTimer = 0f; Fire(_target); }
}

private BaseEnemy FindTarget()
{
    CombatSystem.Instance.Grid.QueryCircle(Position, _radiusGrid, _candidates);
    if (_candidates.Count == 0) return null;         // ★ 空校验，杜绝 IndexOutOfRange

    float r2 = _radiusGrid * _radiusGrid;
    BaseEnemy best = null; float bestScore = float.MinValue;
    for (int i = 0; i < _candidates.Count; i++)
    {
        var e = _candidates[i];
        if (e == null || !e.IsAlive) continue;               // 跳过失效引用
        float d2 = (e.Position - Position).sqrMagnitude;
        if (d2 > r2) continue;                               // ★ 精确过滤（网格查询会带出范围外元素）
        float score = _targetMode switch
        {
            TargetMode.FurthestAlongPath => e.PathProgress,   // 最危险的优先（塔防标准策略）
            TargetMode.Nearest           => -d2,              // 最近优先
            TargetMode.HighestHp         => e.CurrentHp,      // 最高血优先
            _                            => e.PathProgress,
        };
        if (score > bestScore) { bestScore = score; best = e; }
    }
    return best;
}
```

**要点说明**
- **`PathProgress` 是"最危险优先"的基础**：`BaseEnemy` 新增 `public float PathProgress => (float)_pathIndex / _path.Count;`（0 = 刚出生，1 = 快到终点）。这是塔防的标准索敌策略，也是修正 G7 语义错误的关键。
- **节流**：`_searchInterval` 来自 `TBTower.searchIntervalMs`（默认 100ms）。有目标时零搜索，目标消失才重新搜索 —— 这是性能提升的最大来源。
- **候选缓冲复用**：`_candidates` 是成员字段而非每帧 `new List`，消除 GC 抖动。
- **平方距离**：全程用 `sqrMagnitude` 比较，避免 `Sqrt`。

### 5.4 子弹命中：距离判定，不用物理

```csharp
// BaseBullet 重写要点
private BaseEnemy _target;          // 发射时锁定的目标（追踪弹）
private Vector2 _dir;               // 直线弹的方向
private float _lifeTimer;

public void Tick(float dt)
{
    if (_state != BulletState.Fire) return;

    // ① 追踪目标（目标死亡则改为沿最后方向飞完剩余寿命）
    if (_target != null && _target.IsAlive)
        _dir = (_target.Position - Position).normalized;

    // ② 位移
    Position += _dir * _speed * dt;

    // ③ 命中判定：距离 < hitRadius（二选一，见下）
    if (_target != null && _target.IsAlive)
    {
        float d2 = (_target.Position - Position).sqrMagnitude;
        if (d2 <= _hitRadius * _hitRadius) { OnHit(_target); return; }
    }

    // ④ 超时回收（防"追不上的子弹"永久存在，也顺带覆盖丢失目标的情况）
    _lifeTimer += dt;
    if (_lifeTimer >= _lifeTime) Recycle();
}

private void OnHit(BaseEnemy e)
{
    e.Hurt(_damage);                       // ★ 伤害来自 TBTower.power，不再硬编码 1
    if (_pierce > 0) { /* M2: 继续穿透 */ }
    else Recycle();
}
```

**命中判定的两种实现（按精度/成本选择）**

| 方案 | 做法 | 成本 | 适用 |
|---|---|---|---|
| **A. 当前距离判定（✅ M0 采用）** | 每帧比较子弹与目标的平方距离 < `hitRadius²` | O(B) | 有追踪目标；简单可靠；低端机友好 |
| B. 线段扫掠判定（防高速穿透） | 比较"上一帧位置→当前位置"线段与目标圆是否相交 | O(B)，略高 | 子弹速度快到可能单帧跨过目标时必须用 |

> **注意高速穿透问题**：若 `speed × dt > 2 × hitRadius`，方案 A 可能"穿过"目标而漏判。M0 的规避手段是**限制子弹速度并放大 hitRadius**（配置表里可控），或直接锁追踪目标（本方案已锁）。若 M2 出现明显漏判，升级到方案 B。
> 配置自检建议：启动时校验 `TBBullet.speed × (1/60) < TBBullet.hitRadius`，不满足则告警。

### 5.5 集中式 tick（取代分散的 `UpdateEvent` 订阅）

**改造前**：每个塔/怪/子弹在 `Awake` 里 `EventDispatcher.AddEventListener(EventName.UpdateEvent, MyUpdate)` → 每帧全局分发一次，遍历全部监听者。对象数 500 时 = 500 次委托调用 + 500 次字典/列表遍历开销，且**顺序不可控**（塔可能比怪先更新，导致索敌基于上一帧位置）。

**改造后**：只有 `CombatSystem` 订阅一次 `UpdateEvent`，内部按**固定顺序**遍历三个列表：

```csharp
public class CombatSystem : BaseManager<CombatSystem>
{
    private readonly List<BaseEnemy>  _enemies = new(256);
    private readonly List<BaseTower>  _towers  = new(64);
    private readonly List<BaseBullet> _bullets = new(512);

    public EnemyGrid Grid { get; private set; }

    public override void OnInit()
    {
        Grid = new EnemyGrid(cellSize: 2f * Cfg.Global.CellSize, cols: 64);
        EventDispatcher.AddEventListener(EventName.UpdateEvent, OnUpdate);   // ★ 全局仅此一处
    }

    private void OnUpdate()
    {
        float dt = Time.deltaTime;

        // 固定顺序：先同步位置 → 再塔索敌开火 → 最后子弹推进判定
        SyncEnemyGrid(dt);
        TickTowers(dt);
        TickBullets(dt);
    }

    private void SyncEnemyGrid(float dt)
    {
        for (int i = _enemies.Count - 1; i >= 0; i--)
        {
            var e = _enemies[i];
            if (e == null) { _enemies.RemoveAt(i); continue; }   // ★ 顺手清理失效引用
            e.Tick(dt);                     // 移动
            Grid.Update(e, e.Position);     // 同步格子（未跨格零开销）
        }
    }
    // TickTowers / TickBullets 同理，均倒序遍历 + 失效清理
}
```

**收益**
- 每帧仅 1 次事件分发 + 3 次紧凑数组遍历（**连续内存、无虚调用爆炸、可预测**）
- **更新顺序确定**：怪先动 → 塔再索敌 → 子弹最后判定，消除一帧延迟
- 顺带解决**失效引用清理**（倒序遍历时移除 null），不再依赖 `OnDestroy` 回调的时序
- 便于统一做**帧率无关**处理（全部用 `dt`）与**同屏上限**保护（`TBGlobal.maxEnemyAlive`）

### 5.6 复杂度与预算对比

| 环节 | 改造前 | 改造后 | 备注 |
|---|---|---|---|
| 索敌 | 物理宽相 O(N·M) + 触发器回调 | **O(N·c)**，c ≈ 9–49；且有目标时**完全跳过** | N=100 塔时约 900–4900 次距离计算，仅在有塔失去目标时发生 |
| 命中 | 物理窄相 + 触发器回调 | **O(B)** 分支 + 一次 `sqrMagnitude` | B=300 时约 300 次 |
| 每帧事件回调 | O(塔+怪+子弹) 次 | **1** 次 | |
| 物理引擎 | 参与全部宽相/窄相 | **完全不参与**（塔/怪/子弹无 Collider） | 最大的省钱项 |
| GC | 每帧 `new List` + 委托闭包 | 缓冲复用 + 无闭包 | 消除帧抖动 |

**M0 性能自检方法**：Profiler 中 `Physics2D` / `Physics` 分区应**恒为 0**；`CombatSystem.OnUpdate` 的 GC Alloc 应为 **0 B**。

### 5.7 实施注意事项

1. **删除清单**：`Tower/Tower/Targetter.cs` 整个删除；`BaseTower`/`BaseBullet`/`BaseEnemy` 与 `TowerPosition`/`BasePoint` 上的所有 `Collider`、`Rigidbody` 组件移除；`Prefab` 上残留的物理组件也要清（用 2026-09-25 新增的 Missing Script 清理工具思路，写个"清理物理组件"的 Editor 工具）。
2. **`EnemyGrid` 的容量**：`cols` 要覆盖棋盘最大列数 + 1，否则 `Key()` 会撞键。建议由 `TBLevelMap.cols` 动态确定。
3. **飞行单位（M2）**：飞行怪不进 `EnemyGrid` 的普通查询，或单独一个 grid；同时塔需要有 `canAttackAir` 标记（进 `TBTower` 表）。
4. **`PathProgress` 的维护**：路径重算（建塔）后所有敌人的 `_pathIndex` 需要按当前世界位置重新映射，否则索敌策略会错乱。**这是 2D 重构中最容易出 Bug 的地方**，M0 阶段建议：路径重算后先 `PathProgress = 0` 简单处理，M1 再做精确映射。
5. **`IsAlive` 标记**：`BaseEnemy` 增加 `public bool IsAlive { get; private set; }`，回收时置 false。所有跨帧引用（塔的 `_target`、子弹的 `_target`、网格里的元素）都靠它判有效，比 `== null` 更可靠（因为对象池复用会导致"非 null 但已回收"的危险状态）。

---

## 6. 系统设计

### 6.1 场景与棋盘（`main.unity` 落地）

> **需求 6 的落实章节。** 玩法必须在 `Assets/Scenes/main.unity` 内实现。

#### 6.1.1 场景现状与需要补齐的内容

**现状**（已核实）：`main.unity` 仅有 4 个对象 —— `Camera`（正交，size=5）、`Canvas`（ScreenSpaceCamera，1920×1080）、`EventSystem`、`bg`。

**目标层级结构**（在 `main.unity` 内搭建）

> **关键分层（v2.1 修正）**：`BattleRoot` 及其子树是**世界空间**对象（`Transform` + `SpriteRenderer`），**不要**放进 Canvas；`UICanvas` 只承载 HUD 等纯界面，并**建议把 `RenderMode` 从 `ScreenSpaceCamera` 改为 `ScreenSpaceOverlay`**（HUD 不需要参与游戏对象的遮挡排序，Overlay 更省且不与场景坐标耦合）。

```
main.unity
├── Camera                          [已有] 正交相机（size=5，可视世界高度 10 单位）
│   └── (CameraController)                   平移/缩放，M1
├── EventSystem                     [已有] UI 事件系统（仅服务 UGUI）
├── Launcher                        ★新增 挂 Launcher.cs（DontDestroyOnLoad）
├── UICanvas                        ★新增 打 Tag = "UICanvas"（UIManager 靠 Tag 查找）
│   │                                 建议 RenderMode 改 ScreenSpaceOverlay
│   ├── BgPanel                     ★新增  背景层（bg 移到这里，或改为世界空间背景）
│   ├── NormalPanel                 ★新增  常规面板层
│   │   ├── HudView                 ★新增  战斗 HUD（金币/生命/回合/开始按钮）
│   │   ├── TipsView                ★新增  简单提示（M0 用它代替结算界面）
│   │   └── RoundResultView         ★新增  回合结果（M1）
│   └── TipsPanel                   ★新增  浮层提示
├── BattleRoot                      ★新增  战斗棋盘根节点【世界空间 · Transform】
│   ├── BoardRoot                   ★     棋盘格子容器（CellView = SpriteRenderer）
│   │   └── Cell(r,c) × rows×cols    运行时按 TBLevelMap 生成
│   ├── PathRoot                    ★     路径箭头容器（SpriteRenderer）
│   ├── TowerRoot                   ★     已建造的塔
│   ├── EnemyRoot                   ★     怪物（来自对象池）
│   ├── BulletRoot                  ★     子弹
│   └── EffectRoot                  ★     特效（M2）
└── GameSceneLauncher               ★新增 挂 GameSceneLauncher.cs（关卡初始化入口）
```

**M0 只需**：`UICanvas` 三层 + `BattleRoot` 各容器 + `HudView` + `TipsView`。其余可后补。

> ⚠️ `UIManager.UICanvas` 通过 `GameObject.FindGameObjectWithTag("UICanvas")` 查找，且 `GetPanelLayoutParent` 要求 `BgPanel`/`NormalPanel`/`TipsPanel` 三个子节点存在 —— **这三层必须齐备，否则 UI 打不开**。

**需要同步调整的工程设置**
| 设置 | 值 | 原因 |
|---|---|---|
| `Graphics Settings → Transparency Sort Mode` | `Custom Axis`，轴 `(0, -1, 0)` | 让 Y 越小（越靠下）的 Sprite 越靠前，实现塔/怪前后遮挡 |
| `Physics2D` 重力 | 建议 `(0, 0)` | 项目不用物理，但怪物 prefab 自带 `CapsuleCollider2D`，避免残留影响 |
| `Camera.clearFlags` | `SolidColor` 或 `Skybox` | 2D 场景 |
| 说明 | 不要新增 `SortingLayer`，沿用怪物包既有的 `SortingGroup`（`order: 200`）约定 | 减少与既有资源的冲突 |

#### 6.1.2 棋盘生成流程

```
GameFlowManager.InitLevel()
  ├─ 读 TBLevel[1] → 拿到 mapId / initialGold / initialHp / roundIds
  ├─ 读 TBLevelMap[mapId] → 拿到 cols / rows / cells(每行字符串)
  ├─ 通过 AB 加载背景图与格子贴图（bundle: level_1）
  ├─ 按棋盘尺寸调整相机：orthographicSize = max(rows, cols/aspect) / 2 + 边距
  ├─ BoardView.Build(cells, cols, rows, cellSize)
  │    ├─ 逐格创建 Cell(r,c)（SpriteRenderer + CellView），按字符决定外观与状态
  │    └─ 记录 spawnCell / endCell
  ├─ AStarManager.BuildGrid(cells, cols, rows)   ← 只建数据层 Point[,]，不生成物件
  ├─ 初始路径计算 + 路径箭头绘制
  └─ 通知 HudView 刷新金币/生命/回合数
```

#### 6.1.3 棋盘数据模型（**替代原 ASCII 地图文件方案**）

**数据与视图分离**（这是 v1.0 的核心缺陷：`Point` 直接持有 GameObject 引用）：

```csharp
/// 纯数据层：不持有任何 Unity 对象引用，便于单元测试与算法复用
public class CellData
{
    public int Row, Col;
    public CellType Type;          // Spawn / End / Ground / Obstacle / Hole / Decor
    public Vector2 Center;         // 棋盘局部坐标（由 BoardView 计算后写入）
    public bool IsWalkable => Type != CellType.Obstacle && Type != CellType.Hole;
    public bool IsBuildable => Type == CellType.Ground;
    public bool IsWall;            // 寻路用：被塔占位或被障碍阻挡
    public BaseTower Tower;        // 该格上的塔（视图引用，仅用于业务查询）
}

/// A* 节点：只保留算法需要的字段
public class Point
{
    public int Row, Col;
    public Vector2 Center;
    public bool IsWall;
    public Point Parent;
    public float G, H, F;
    // ★ 移除 v1.0 里的 GameObject gameObject / Transform transform 字段
}
```

**`BoardView`（视图层）职责**
- 按 `CellData` 生成**世界空间格子**（`SpriteRenderer`，挂在 `BattleRoot/BoardRoot` 下），存入 `CellView[,]`
  > 若格子数很多（如 32×18 = 576 格），可为底板单独做一张整图以避免 576 个 DrawCall；M0 棋盘 16×9 共 144 格，用 `SpriteRenderer` + 图集即可接受。也可对**不可建造格**做合并。
- 提供 `WorldToCell(Vector2 worldPos)` → `(row, col)`：**纯数学除法，不用物理**（完整实现见 §2.3.4）
  ```csharp
  public bool WorldToCell(Vector2 worldPos, out int row, out int col)
  {
      Vector2 local = worldPos - (Vector2)_root.position;
      col = Mathf.FloorToInt(local.x / _cellSize);
      row = Mathf.FloorToInt(-local.y / _cellSize);   // y 向下为负
      return row >= 0 && row < _rows && col >= 0 && col < _cols;
  }
  ```
- 提供格子高亮：`SetCellColor(row, col, Color)`（改 `SpriteRenderer.color`）/ `ResetAll()`
- 提供 `ScreenToCell(Vector2 screenPos, out int row, out int col)`：
  ```csharp
  Vector3 wp = Camera.main.ScreenToWorldPoint(
      new Vector3(screenPos.x, screenPos.y, -Camera.main.transform.position.z));
  return WorldToCell(wp, out row, out col);
  ```
- **不再有 `Collider`、不再有 `OnTriggerEnter`** —— 拖塔时用"鼠标位置 → 格子索引"直接判定（这也顺带解决了需求 8 中塔放置部分的触发依赖）
- **必须先剔除怪物 prefab 上残留的 `CapsuleCollider2D`**，否则物理系统仍会被拉起

**地图来源对比**

| | v1.0（废弃） | v2.1（采用） |
|---|---|---|
| 存放位置 | `Assets/StreamingAssets/Map/Map{n}.txt` | **`Luban/Config/Datas/SceneInfo.xlsx`（`TBLevelMap`）** |
| 编辑方式 | 文本编辑器手写 | **策划在 Excel 里编辑** |
| 加载方式 | `WWW` 读文件 | **AB 系统读配置** |
| 与关卡关联 | 靠命名约定 `Map{Id}.txt` | 靠 `TBLevel.mapId` 显式引用 |
| 生成物 | 3D 物件（Point 预制体） | **世界空间 `SpriteRenderer` 格子** |

#### 6.1.4 路径可视化

- 用一组池化的箭头 `SpriteRenderer`（`MapArrow`）沿寻路结果逐格摆放，挂在 `PathRoot` 下
- 路径重算后：先全部隐藏 → 按新路径重新摆放 → 数量不足时扩容池
- 箭头朝向按"当前格 → 下一格"的方向设置 `transform.localEulerAngles.z`
- 排序：设较小 `sortingOrder`（如 0），确保在格子之上、塔/怪之下
- **M0 可简化**：只画起终点标记，路径箭头留 M1

### 6.2 塔系统

> **首要改动：把 `Tower_Normal.prefab` 从 UGUI 转为 `SpriteRenderer`（§2.3 决策的落地）**
>
> 现状：根 `Tower_Normal`（`RectTransform` 100×100，Layer 5，无脚本）+ 子节点 `barbette`（炮座，`Image` 128×128）、`Img_gun`（炮管，`Image` 128×128）。
>
> 转换步骤（半天内可完成，仅 1 个 prefab）：
> 1. 在根节点加 `BaseTower`（`NormalTower`）脚本；**`Layer` 从 5(UI) 改为 Default(0)**
> 2. 三个节点的 `RectTransform` → `Transform`（删除 `CanvasRenderer` 与 `Image`）
> 3. `barbette` / `Img_gun` 各加 `SpriteRenderer`，`sprite` 仍引用原来那两张 PNG（`turret_base_128` / `turret_barrel_128`）—— 若 PNG 的 `Texture Type` 是 `Sprite (UI and 2D)` 则无需改动，直接可用
> 4. 加 `SortingGroup`，`sortingOrder` 设为与怪物协调的值（怪物是 200，塔建议 **300**，保证塔在怪之上；如需塔被前排怪遮挡则改用自定义排序轴 + Y 位置）
> 5. `Img_gun` 的 `Pivot` 建议设为炮管旋转中心（如 `(0.3, 0.5)`），使转向自然；炮口发射点加一个空子节点 `BarrelPoint`
> 6. 保留 prefab 路径 `Assets/Prefabs/Tower/Tower_Normal.prefab`，`ResTable` 中逻辑名 `Tower_Normal` 不变 → **不影响配置表与业务代码**

#### 6.2.1 数据与视图

```csharp
/// 塔的配置封装（从 TBTower 读取，供业务层使用）
public class TowerConfig
{
    public int Id, Type, Level, UpgradeTo, Prices, SellPrice, BulletId, TargetMode;
    public float Radius;        // 格
    public float Power;
    public float Cooldown;      // 秒（表里是 ms，此处已换算）
    public float RotateSpeed;
    public float SearchInterval;// 秒
    public string ResName;
    public int EffectType; public float EffectValue;
}
```

#### 6.2.2 放置流程（保留原核心逻辑，2D 化交互）

```
点击塔按钮 → TrySpend(TBTower.prices)
    ├─ 金币不足 → 按钮置灰 + TipsView 提示"金币不足"
    └─ 足够 → 进入"待放置"状态：
              生成塔实例（暂挂 BattleRoot/TowerRoot 下，Sprite 半透明）
              跟随鼠标：Camera.ScreenToWorldPoint(mouse) → BoardView.WorldToCell
              ↓ 每帧
              transform.position = BoardView.CellCenter3(row, col)
              ├─ 格不可建造 / 已有塔 → 格子染红，禁止放置
              └─ 可建造 → 格子染绿
                        ↓ 鼠标点击（或抬起）
                     临时置 IsWall=true 跑 A*
                       ├─ 路径被堵死 → 回滚 IsWall，格子染红 + 提示"不能完全阻断敌人路径"
                       └─ 通过 → 吸附到格子中心、扣金币、注册到 TowerManager
                              → 触发路径重算事件 → 怪物改道 → 出音效（M2）
```

**关键改进（相对 v1.0）**
- 格子判定从"触发器"改为"坐标除法"，消除物理依赖（需求 8 联动）
- 扣费时机统一为**建造成功时扣**（v1.0 完全不扣）
- 新增**不可建造的红色提示**（v1.0 只有绿色）
- 拖动中显示**射程预览圈**（世界空间半透明 Sprite，M1）
- 半透明预览改 `SpriteRenderer.color.a`（不再是 `CanvasGroup.alpha`）

#### 6.2.3 塔的开火（重写）

见 §5.3.2 的 `TickAttack`。要点：
- 无目标 **不开火**（v1.0 是每 0.2s 无条件空放）
- 炮管转向目标（`barbette` 子节点 `localRotation.z` 插值）
- 冷却来自 `TBTower.CD / 1000`
- 索敌策略来自 `TBTower.targetMode`
- 射程来自 `TBTower.radius`（格 → 像素：`radius * cellSize`）

#### 6.2.4 升级与出售（M2，**已实现**）

> v2.2 更新（2026-09-29）：本节由"设计"升级为"实现记录"。

**入口**：点击已建造塔 → 选中 → 打开 `TowerInfoView`
- 塔是纯 `SpriteRenderer`、无 `Collider`；选中靠 `TowerPlacement.HandleSelectClick`
  用"屏幕坐标 → `BoardView.ScreenToCell` → `cell.Tower`"反查（与放置预览同一套换算）
- 选中态由 `TowerPlacement` 单一持有，广播 `TowerSelectedEvent(BaseTower)` / `TowerDeselectedEvent`
- 面板 `TowerInfoView` 由 `GameFlowManager.OnTowerSelected` **惰性**打开（走 `UIManager` + `ResTable` 逻辑名 `TowerInfoView`）

**升级 = 换实例**（决策见 `Docs/Tower_Interaction_Dev_Plan_v2.md` §1.1）
- `TowerManager.TryUpgrade(old)`：读 `upgradeTo` 行 → 校验 → **先扣费** → `UnregisterTower(old)` → 释放旧实例
  → 实例化新 prefab → `Init(nextCfg, cell)` + `SnapToCell(cell)` → 写回 `cell.Tower` → `RegisterTower(new)`
- **顺序关键**：`UnregisterTower` 必须先于 `RegisterTower`（否则短暂双份 tick）
- **不触发 `RequestRefresh()`**：格子占用未变，重算只会让怪物无谓改道
- **回滚**：扣费后任一步失败 → 退还金币 `AddGold(prices)`，格子恢复原状
- 旧塔释放用 `ResLoader.ReleaseInstance(oldCfg.ResName, oldGo)`（与 `Sell` 同款）
- 升级后 `TowerPlacement.ReselectAfterSwap` 把选中态迁到新实例（不发 Deselect，避免面板闪烁）

**出售**
- `TowerManager.Sell(tower)`：返还 = `sellPrice × Global.SellRefundRate` → 释放格子 + `Point.IsWall=false`
  → `UnregisterTower` → 广播 `DestroyTower` → `ReleaseInstance` → `RequestRefresh()`（**出售必须重算路径**）
- 交互变更：**右键不再是"直接出售"**，改为"取消选中/关闭面板"；出售统一走面板按钮
  （`TowerSellRequestEvent` → `GameFlowManager` → `TowerManager.Sell`）

**面板 `TowerInfoView`（逻辑先行版，纯色占位）**
- 节点：`Bg` / `Panel(Title / Stats / UpgradeBtn / SellBtn / CloseBtn)`，全部查找容错（缺节点只警告）
- 展示：塔名+等级、攻击/射程/攻速；升级按钮显示费用并按金币置灰，满级显示「已满级」
- **美术皮肤待接入**（L-7）：换 prefab 即可，`.cs` 不改

### 6.3 敌人系统

#### 6.3.0 资源包结构与动画集成（v2.1 新增）

**资源包实测结构**

```
Assets/_UIAssets/Monsters/
├── _Common/
│   ├── Sprites/                           公共 Sprite
│   └── Animations/
│       ├── <家族>/Controller.controller    ★ AnimatorController
│       └── <家族>/  Ready.anim  Walk.anim  Attack.anim  Death.anim
├── Rats/
│   ├── Rat/  Rat.prefab  Rat.png
│   ├── RatKing/ ...
│   └── ...（CaveRat / Ghost / FlyingDemon / CrystalLizard / Porcupine / ...）
├── Birds/  Bats/  Dogs/  Pigs/  Cattle/  Felines/  Giants/  Insects/
├── Mounts/  Parasites/  Scorpions/  Bunnies/  Horses/  Apes/  Inanimate/
└── （共 14 个族系 + _Common）
```

**规模**：119 prefab / 122 Sprite（PPU=100）/ 120 `.anim` / 30 `.controller`

**动画状态命名统一为四态**（这是集成点，务必按此驱动）：

| 状态 | 触发时机 | 对应业务事件 |
|---|---|---|
| `Ready` | 待机（出生前/停下） | 从对象池取出、尚未开始移动 |
| `Walk` | 沿路径移动 | `EnemyState.Move` |
| `Attack` | 攻击（本项目怪物不主动攻击，可留空/不用） | M2 若加"怪物攻击塔"机制再启用 |
| `Death` | 死亡 | `Hp <= 0` 时播放，播完再回收 |

**`BaseEnemy` 与 `Animator` 的对接**

```csharp
// 缓存 hash，避免每帧字符串查找
static readonly int H_STATE = Animator.StringToHash("State");   // 若 Controller 用 int 参数
// 或按 Controller 里实际的参数/Trigger 名调整；若 Controller 用默认状态机（无参数），
// 则改用 animator.Play("<StateName>") 直接切状态

public void SetAnimState(EnemyAnimState s)
{
    if (_anim == null) return;
    switch (s)
    {
        case EnemyAnimState.Ready: _anim.Play("Ready"); break;
        case EnemyAnimState.Walk:  _anim.Play("Walk");  break;
        case EnemyAnimState.Death: _anim.Play("Death"); break;
    }
}
```
> **待确认项（实现前必须打开一个 `.controller` 看）**：State 是用「参数名/Trigger」驱动，还是「无参数、直接 `Play` 具名状态」驱动。上例按后者写；若用前者，改为 `SetInteger`/`SetTrigger`。
> **注意**：不同家族（`Bat` / `Bear` / `Pig` …）各有独立 Controller，**切换怪物类型时要换 `runtimeAnimatorController`**（或每个家族各做一个 prefab 变体）。

**死亡流程与动画的配合**：`Death` 动画需要播完再回收，因此：
```csharp
private void Die()
{
    IsAlive = false;
    SetAnimState(EnemyAnimState.Death);
    PlayerDataManager.Instance.AddGold(_reward);          // 奖励即时结算，不等动画
    _pendingRecycle = true;                              // 标记待回收
    _recycleDelay = _deathAnimLength;                    // 从 Controller 取，或配置表配
}
// Tick 中：if (_pendingRecycle) { _recycleDelay -= dt; if (_recycleDelay <= 0) Recycle(); }
```
> 注意：`IsAlive = false` 后该敌人**立即**从索敌与存活统计中排除，但 GameObject 还在播死亡动画 —— 网格与存活计数必须按 `IsAlive` 过滤，否则"回合完成"判定会推迟到动画播完。

**其它要点（沿用 v2.0）**

- **类型枚举扩展**：`EnemyType { None, Normal, Quick, Strong, Armored, Flying, Boss }`，并在 `EnemyManager.CreateEnemy` 的 switch 补齐所有 case
- 怪物 prefab 自带 `CapsuleCollider2D` 与 `SortingGroup`(order 200)：**`CapsuleCollider2D` 必须删除**（§5 去物理）；`SortingGroup` 保留
- `Transform` 是普通 Transform（世界空间），位置用 `transform.position`
- **修复池化字典键 Bug**：v1.0 里创建与回收都硬编码 `EnemyType.NormalEnemy`，必须改为真实 `type`
- **属性全部来自 `TBEnemy`**：血量、速度、护甲、受击半径、奖励、漏怪伤害、缩放（删除 `GlobalConst.EnemyHp` 依赖）
- **移动（2D）**：
  ```csharp
  public void Tick(float dt)
  {
      if (_state != EnemyState.Move) return;
      Vector2 target = _path[_pathIndex].Center;
      Vector2 dir = (target - Position).normalized;
      Position += dir * _speed * dt;                  // 像素/秒
      _view.SetRotation(dir);                         // 2D 朝向（翻转 X 或绕 z 旋转）
      if (Vector2.Distance(Position, target) < ArriveThreshold)
      {
          _pathIndex++;
          UpdatePathProgress();
          if (_pathIndex >= _path.Count) OnReachEnd(); // ★ 漏怪处理
      }
  }
  ```
- **`PathProgress`**：`_pathIndex / (float)_path.Count`，供索敌使用（§5.3.2）
- **`IsAlive`**：跨帧引用有效性的唯一判据（§5.7 第 5 点）
- **受击**：
  ```csharp
  public void Hurt(float damage)
  {
      if (!IsAlive) return;
      _currentHp -= damage * (1f - _armor);
      UpdateHpBar();                       // 世界空间 SpriteRenderer 血条
      ShowDamageNumber(damage);            // M1，UGUI 飘字
      if (_currentHp <= 0f) Die();
  }
  private void Die()
  {
      IsAlive = false;
      PlayerDataManager.Instance.AddGold(_reward);          // ★ 击杀奖励
      EventDispatcher.TriggerEvent(EventName.EnemyKilledEvent, this, _reward);
      PlayDeath();                                          // M2
      Recycle();
  }
  private void OnReachEnd()
  {
      IsAlive = false;
      PlayerDataManager.Instance.LoseHp(_damageToPlayer);    // ★ 漏怪扣血
      EventDispatcher.TriggerEvent(EventName.EnemyReachedEndEvent, this, _damageToPlayer);
      Recycle();
  }
  ```
  > **修正 v1.0 的错误逻辑**：原 `Hit()` 是"血量>0 才更新血条，否则 Reset"，死亡时**不发奖励**；且到达终点直接 `Reset()` **不扣玩家血**。
- **血条（UGUI）**：`HpBar`（Image，type=Filled）挂在怪物预制体上，随怪物一起移动，无需 Billboard 处理（2D 天然正视）
- **池化**：统一走 `ObjectPool<T>`（v1.0 的双字典池保留思路，修正键 Bug）

### 6.4 子弹与伤害结算

- `BaseBullet.Tick(dt)` 见 §5.4
- `Damage` 由发射塔注入：`bullet.Init(target, damage: _config.Power, bulletCfg)`
- 命中后调 `target.Hurt(damage)`；AOE/穿透/减速按 `TBBullet` 的 `aoeRadius`/`pierce`/`effectType` 分支（M2）
- 命中判定路径：**无物理**，纯距离
- 回收：命中 / 超时（`lifeTimeMs`）双保险，回收时 `IsAlive=false` 语义等价物为 `_state = Idle`
- 复用时必须**重置状态**（`_target=null`、`_dir=zero`、`_lifeTimer=0`、位置归位），否则池化会出现"带着上次目标飞出去"的经典 Bug

### 6.5 波次与回合

**M0（单回合）**
```
GameFlowManager:
  Prepare → 显示"点击开始"
  点击开始 → WaveManager.PlayRound(roundId)
     读 TBRound[roundId].waveIds → 逐个 TBWave
     对每个 wave：
        延迟 wave.startDelayMs
        按 wave.enemyIds 顺序、每隔 wave.spawnIntervalMs 生成一只
  所有怪生成完 && 场上存活 == 0 → RoundComplete
  弹出 TipsView「回合完成」→ M0 结束
```

**M1（多回合 + 自动推进）**：`WaveState { Idle, Prepare, Spawning, Fighting, Interval, Finished }`，回合间给 `waveIntervalMs` 布塔窗口，全回合完成 → 胜利。

**调度实现要点**
- 用**单个累加计时器 + 时间轴游标**驱动（`Time.deltaTime` 累加），**不要用递归 Timer 嵌套**（v1.0 的 `RecycleGenerateEnemy` 递归写法有索引错位 Bug）
- 生成时间轴在回合开始前一次性展开成 `List<(float timeSec, int enemyId)>` 并排序，便于日志排查与单元测试
- 存活数来源：`CombatSystem._enemies` 中 `IsAlive == true` 的数量（**不再遍历场景**）
- 取代 `RoundCountManager`（v1.0 的空壳，职责与 `EnemyManager` 重复）

### 6.6 经济与生命

```csharp
public class PlayerDataManager : BaseManager<PlayerDataManager>
{
    public int Gold { get; private set; }
    public int Hp   { get; private set; }
    public int TotalKilled { get; private set; }

    public void InitFromLevel(TBLevel lv) { Gold = lv.InitialGold; Hp = lv.InitialHp; }

    public bool TrySpend(int amount)
    {
        if (amount <= 0 || Gold < amount) return false;
        Gold -= amount;
        EventDispatcher.TriggerEvent<int,int>(EventName.GoldChangeEvent, Gold, -amount);
        return true;
    }
    public void AddGold(int amount)
    {
        if (amount <= 0) return;
        Gold += amount;
        EventDispatcher.TriggerEvent<int,int>(EventName.GoldChangeEvent, Gold, amount);
    }
    public void LoseHp(int amount)
    {
        if (amount <= 0 || Hp <= 0) return;
        Hp = Mathf.Max(0, Hp - amount);
        EventDispatcher.TriggerEvent<int,int>(EventName.PlayerHpChangeEvent, Hp, -amount);
        if (Hp <= 0) EventDispatcher.TriggerEvent(EventName.GameOverEvent, false);
    }
}
```

**规则**
- 所有金币变更**必须**走 `TrySpend` / `AddGold`，禁止直接改字段（保证事件与 UI 一致）
- 初始金币/生命来自 `TBLevel.initialGold` / `initialHp`（**不再用 `GlobalConst`**）
- `MainView` 里被注释掉的 `PlayerHpChangeEvent` / `PlayerRoundCountChange` 监听要**接回来**，并新增金币监听
- 失败判定在 `LoseHp` 内统一处理

### 6.7 寻路（2D 化）

**保留**：`AStarWrapper.AStarWrapper.FindPath` 的算法实现（标准 A*，279 行，逻辑正确）

**改造**：
| 项 | v1.0 | v2.1 |
|---|---|---|
| 节点坐标 | `Vector3 position` | `int Row/Col` + `Vector2 Center`（世界坐标） |
| 节点↔物件 | `Point.gameObject` / `Point.transform` 强引用 | **移除**，改由 `BoardView.WorldToCell` 互查 |
| 地图来源 | ASCII txt | **`TBLevelMap` 配置表** |
| 网格构建 | `InitMap` 逐字符生成 3D 物件 | `AStarManager.BuildGrid` **只建数据**（`Point[,]` + `IsWall`） |
| 路径绘制 | `LineRenderer` + 3D `MapArrow` | **世界空间 `SpriteRenderer` 箭头池**（§6.1.4） |
| 重算时机 | 建造中/完成/拆除/升级 | **建造成功、出售、升级（仅占位变化时）**；建造中不重算 |

**必须加固的点（技术债 T1）**
```csharp
public List<Point> GetAStarPath(Point start, Point target)
{
    var result = new List<Point>();
    if (start == null || target == null) return result;

    int guard = mapWidth * mapHeight + 1;      // ★ 迭代上限，杜绝死循环
    Point cur = target;
    while (cur != null && cur != start && guard-- > 0)
    {
        result.Add(cur);
        cur = cur.Parent;
    }
    if (guard <= 0) { Debug.LogError("[AStar] 路径回溯超出上限，Parent 链可能断裂"); return result; }
    return result;
}
```

**其他加固**
- `mapWidth` 按**最长行**补齐（v1.0 取第一行长度，行长不一致会错位）
- 过滤配置行末尾的空行/空白
- `Enemy.UpdatePath` 增加 `_path` 为 null / `_pathIndex` 越界的保护（技术债 T3）
- 路径重算节流：脏标记 + 每帧最多重算 1 次

### 6.8 UI 设计

> **分层原则（v2.1）**：本节所有界面都是 **UGUI**，挂在 `UICanvas` 下，与 `BattleRoot` 的世界空间对象**完全隔离**。
> 界面只通过 `EventDispatcher` 事件与战斗逻辑通信，**不直接引用塔/怪/子弹对象**（`HudView` 只认数字，不认场景对象）。这是保持两层解耦的关键。

| 界面 | M0 | 说明 |
|---|---|---|
| `HudView` | ✅ 必做 | 金币、生命、回合进度、**开始/下一波**按钮、塔选择栏（1 个按钮） |
| `TipsView` | ✅ 必做 | 简单提示（"金币不足"/"不能阻断路径"/"回合完成"）—— M0 用它代替结算界面 |
| `RoundResultView` | M1 | 胜利/失败结算 |
| `TowerInfoView` | M2 | 升级/出售面板（已有框架，升级按钮待接线） |
| `SettingView` / `PauseView` | M3 | 音量、倍速、暂停 |

**关键反馈清单**（M0 至少实现前 3 项）
1. 金币不足时塔按钮置灰
2. 格子可建造染绿 / 不可建造染红（**改 `SpriteRenderer.color`**，不再是 `Image.color`）
3. 金币/生命变化时数值跳动与闪烁
4. 射程预览圈（M1，世界空间半透明 Sprite 或 `LineRenderer` 画圆）
5. 回合倒计时与下一波构成预览（M1）
6. 伤害数字、击杀特效、漏怪红屏（M2；伤害数字建议世界空间 `TextMeshPro`，不用 UGUI）

**性能注意（低端机）**
- **HUD 用 `ScreenSpaceOverlay`**，不与场景相机耦合，也不参与排序计算
- **HUD 节点数量要少**：只保留必要的 Text/Image，避免深层嵌套与频繁 `SetActive`
- **战斗对象不是 UGUI**，因此**不存在 Canvas Rebuild 风险** —— 这是选 `SpriteRenderer` 的重要收益（§2.3 依据④）；仍要避免每帧改 HUD 文本（用脏标记，数值变化时才写 `text`）
- 战斗 Sprite 全部进 **SpriteAtlas**，减少 DrawCall
- 世界空间血条：挂在怪物子节点上的 `SpriteRenderer`（两张 Sprite：底 + 填充，用 `size`/`transform.localScale` 表示比例），**不要用 UGUI 血条**（否则又变成两套坐标）
- 伤害数字：世界空间 `TextMeshPro` + DOTween 上浮淡出，走对象池

---

## 7. 第一阶段（M0）详细计划

### 7.0 目标与完成定义（DoD）

**目标（一句话）**：在 `Assets/Scenes/main.unity` 中，从 `Luban` 配置表驱动，跑通「读配置 → 生成 2D 棋盘 → 拖放 1 种塔 → 出生 1 波怪 → 塔自动索敌开火 → 命中扣血 → 怪死亡给金币 / 漏怪扣玩家血 → 本波清空 → 提示回合完成」的**单回合闭环**；资源经 AB 系统加载；战斗判定完全不依赖 `OnTriggerEnter`。

**明确不包含**（范围纪律，对应需求 5）：多波次自动推进、多回合、塔升级、塔出售、多关卡、结算界面、音效、特效、存档、HybridCLR。

**DoD 验收清单（16 项，全部满足才算 M0 完成；逐条勾选版见 §10.4）**

| # | 验收项 | 判定方式 |
|---|---|---|
| 1 | 游戏在 `main.unity` 中 Play 全程无异常 | Console 无 `Exception` / `NullReference` / `Error` |
| 2 | 配置表从 `Luban` 导出后能被正确加载 | Console 打印各表记录数，与 Excel 行数一致 |
| 3 | **`Tower_Normal.prefab` 已转为 `SpriteRenderer`**，与怪物同一渲染体系 | Inspector 中无 `RectTransform`/`CanvasRenderer`/`Image` |
| 4 | 塔与怪物的 `sortingOrder` 生效（塔盖住怪） | 目视 |
| 5 | 棋盘按 `TBLevelMap` 正确生成，相机尺寸匹配 | 目视：行列数、起终点、障碍位置与表一致，棋盘完整可见 |
| 6 | **改 Excel 数值 → 重导 → 游戏内生效** | 改 1 个怪物血量/塔攻击力验证 |
| 7 | 拖塔可放置；落在非法格变红；堵死路径被拒并回滚 | 目视 + Console |
| 8 | 无目标时塔**不开火**（空放计数为 0） | 计数器日志 |
| 9 | 有目标时塔转向、开火、命中扣血，伤害 = `TBTower.power` | 目视 + 日志 |
| 10 | 怪物四态动画可切换（`Ready` / `Walk` / `Death`） | 目视 |
| 11 | 怪物死亡金币增加；金币不足无法建塔 | 目视 HUD |
| 12 | 怪物走到终点扣玩家生命；生命归零提示失败 | 目视 |
| 13 | 本波清空后提示「回合完成」 | 目视 |
| 14 | **Profiler 中 `Physics` / `Physics2D` 分区恒为 0** | Profiler 截图 |
| 15 | **`CombatSystem.OnUpdate` 的 GC Alloc 为 0 B**；100 怪 + 30 塔单帧 CPU < 2ms | Profiler |
| 16 | 切 `FORCE_AB` 后仍能正常跑通（真 AB 路径）；能打出 PC 包并启动 | 重新运行 + Build |

### 7.1 任务清单（优先级 + 依赖 + 工时）

> 🔴 P0 = 阻塞项；🟠 P1 = 核心闭环；🟡 P2 = 可并行/收尾。工时按 1 名熟练 Unity 开发估算。

| 序号 | 优先级 | 任务 | 主要涉及文件 | 依赖 | 工时 |
|---|---|---|---|---|---|
| **P0-0** | 🔴 | **定义 `IResLoader` 接口 + 编辑器直读实现**（**解锁并行的关键前置**） | `Core/Res/IResLoader.cs`、`EditorResLoader.cs`、`ResTable.cs` | 无 | 0.5 |
| **P0-1** | 🔴 | **配置表链路打通 + 2D 表结构落地** | `Luban/**`、`Assets/Gen/**`、`Data/DataTables.cs`、`Core/Cfg.cs` | 无 | 1.5 |
| **P0-2** | 🔴 | **2D 场景与棋盘搭建** | `Assets/Scenes/main.unity`、`Game/BoardView.cs`、`CellView.cs`、`GameFlowManager.cs` | P0-0、P0-1 | 2.0 |
| **P0-3** | 🔴 | **AB 资源加载系统**（真机实现 + 构建脚本 + 打标） | `Core/Res/BundleResLoader.cs`、`Editor/BuildAssetBundles.cs`、`Editor/ABNameSetter.cs` | P0-0 | 3.0 |
| **P0-4** | 🔴 | **资源就绪化与渲染路线统一**（塔转 `SpriteRenderer` + 清物理组件 + 建子弹/敌人战斗 prefab） | `Assets/Prefabs/Tower/Tower_Normal.prefab`、新建 `Bullet_Normal`、新建 `Enemy_Rat`、`Editor/PhysicsComponentCleaner.cs` | P0-0 | 1.0 |
| **P0-5** | 🟠 | **2D 化改造**（敌人/塔/子弹运动与坐标，去 3D API） | `Enemy/BaseEnemy.cs`、`Bullet/BaseBullet.cs`、`Tower/BaseTower.cs`、`Node/*`、`AStarWrapper/Point.cs` | P0-1、P0-4 | 2.0 |
| **P0-6** | 🟠 | **战斗判定改造**（去物理 + `EnemyGrid` + 索敌/命中 + 集中 tick） | `Core/Combat/CombatSystem.cs`、`EnemyGrid.cs`、`Tower/*`、`Bullet/*`；**删除** `Targetter.cs` | P0-5、P0-2 | 2.5 |
| **P0-7** | 🟠 | **塔的放置**（2D 交互 + A* 校验 + 扣费 + 红绿提示） | `Tower/TowerPosition.cs`（重写）、`TowerManager.cs`、`BoardView.cs` | P0-2、P0-6 | 1.5 |
| **P0-8** | 🟠 | **单回合流程 + 经济/生命闭环** | `Round/WaveManager.cs`（新）、`Core/PlayerDataManager.cs`（新）、`GameFlowManager.cs`、`EventName.cs` | P0-6、P0-7 | 2.0 |
| **P0-9** | 🟠 | **HUD 与提示** | `UI/HudView.cs`（新）、`TipsView.cs`（新）、UI prefab | P0-8 | 1.0 |
| **P0-10** | 🟡 | **收尾**：场景/Build Settings 修复、清理 3D 残留与物理组件、寻路加固 | `EditorBuildSettings.asset`、`JsonDataManager.cs`、`AStarManager.cs`、清理脚本 | P0-4 | 1.0 |

**合计 ≈ 18 人日**（含联调与回归）

### 7.2 依赖关系图

```
   【并行起跑线】
   ┌────────────┐              ┌────────────┐
   │   P0-0     │              │   P0-1     │
   │ IResLoader │              │ 配置表链路  │
   │ 接口+编辑器 │              │  (1.5d)    │
   │  (0.5d)    │              └─────┬──────┘
   └─────┬──────┘                    │
         │ 解锁所有资源相关任务         │
   ┌─────┴───────────────┐           │
   ↓                     ↓           ↓
┌──────────┐     ┌────────────┐  ┌────────────┐
│  P0-3    │     │   P0-4     │  │   P0-2     │
│ AB 系统   │     │ 2D 素材     │  │ 场景与棋盘  │←── P0-1
│ (3.0d)   │     │  (1.0d)    │  │  (2.0d)    │
└────┬─────┘     └─────┬──────┘  └─────┬──────┘
     │                 │                │
     │                 ↓                │
     │          ┌────────────┐          │
     │          │   P0-5     │←─────────┘(P0-1 提供 TBEnemy)
     │          │ 2D 化改造   │
     │          │  (2.0d)    │
     │          └─────┬──────┘
     │                ↓
     │          ┌────────────┐
     │          │   P0-6     │←── P0-2（棋盘坐标）
     │          │ 战斗判定    │
     │          │  (2.5d)    │
     │          └─────┬──────┘
     │                │
     │          ┌─────┴──────┐
     │          ↓            ↓
     │    ┌──────────┐  ┌──────────┐
     └───→│  P0-7    │  │  P0-8    │
          │ 塔的放置  │─→│ 回合闭环  │
          │ (1.5d)   │  │ (2.0d)   │
          └──────────┘  └────┬─────┘
                             ↓
                       ┌──────────┐
                       │  P0-9    │
                       │ HUD 提示  │
                       │ (1.0d)   │
                       └────┬─────┘
                            ↓
                    ┌───────────────┐
                    │ M0 验收        │
                    │ P0-10 收尾     │
                    └───────────────┘
```

**关键路径**：`P0-1 → P0-5 → P0-6 → P0-8 → P0-9 → 验收` = 1.5 + 2.0 + 2.5 + 2.0 + 1.0 = **9.0 人日**

**关键设计洞察（P0-0 的价值）**
> AB 系统（P0-3，3 天）看似是最重的任务，但**不应在关键路径上**。
> 做法：**先定接口 `IResLoader`，编辑器实现用 `AssetDatabase` 直读**（P0-0，仅 0.5 天）。
> 这样 P0-2 / P0-4 / P0-5 / P0-7 / P0-9 全部可以立刻开工，**P0-3 的 AB 真机实现与构建脚本成为并行支线**，
> 只要在 M0 验收前完成即可（验收项 13 专门校验）。
> 这是把 18 人日压到 10 个工作日左右的关键。

### 7.3 任务明细（可执行粒度）

---

#### P0-0　定义 `IResLoader` 接口 + 编辑器直读实现　`0.5d`　🔴 **最先做**

**为什么最先做**：它是"解锁并行"的开关（见 §7.2 洞察）。接口一旦定死，资源加载的两条实现（编辑器直读 / 真 AB）可以完全并行开发。

**交付物**
1. `Assets/Scripts/Core/Res/IResLoader.cs` — 接口定义（§4.4）
2. `Assets/Scripts/Core/Res/ResTable.cs` — 逻辑名 → (bundle, asset) 地址表（§4.3）
3. `Assets/Scripts/Core/Res/EditorResLoader.cs` — 编辑器实现（`AssetDatabase.LoadAssetAtPath`，引用计数空实现）
4. `Assets/Scripts/Core/Res/ResLoader.cs` — 静态门面，按 `#if` 选择实现
   ```csharp
   public static class ResLoader
   {
   #if UNITY_EDITOR && !FORCE_AB
       public static IResLoader Instance { get; } = new EditorResLoader();
   #else
       public static IResLoader Instance { get; } = new BundleResLoader();
   #endif
   }
   ```
5. `Assets/Scripts/Core/Res/ResPathUtil.cs` — 逻辑名 → 编辑器路径的推导规则（与 `ABNameSetter` 的打标规则**必须一致**，否则会出现"编辑器能跑、真机丢资源"的经典问题）

**验收**：`ResLoader.Instance.Instantiate("Tower_Normal", parent)` 在编辑器下能正确实例化塔预制体。

> **务必先做的一件事**：把"逻辑名 → 编辑器路径"和"逻辑名 → bundle 名"两条映射规则写进一个共享配置文件（如 `ResTable`），由 `EditorResLoader` 与 `ABNameSetter` **共同读取**。两边规则分叉是 AB 系统最常见的翻车点。

---

#### P0-1　配置表链路打通 + 2D 表结构落地　`1.5d`　🔴

**依赖**：无

**步骤**
1. **备份并改造 Excel 源表**（位置：`D:\FreedomTower\Luban\Config\Datas\`）：
   - `TowerInfo.xlsx`：`type` 由 string 改 int；`path` 改名为 `resName`；新增 `upgradeTo`、`sellPrice`、`bulletId`、`targetMode`、`searchIntervalMs`、`rotateSpeed`
   - `EnemyData.xlsx`：新增 `resName`、`armor`、`reward`、`damageToPlayer`、`scale`、`bodyRadius`、`isFlying`、`animPrefix`、`desc`
   - 新增 `Bullet.xlsx` → `TBBullet`（字段见 §3.3.4），至少 1 行
   - 新增 `Level.xlsx` → `TBLevel`（字段见 §3.3.6），至少 1 行
   - 新增 `LevelMap.xlsx` → `TBLevelMap`（棋盘布局，M0 至少 1 张）
   - 新增 `Global.xlsx` → `TBGlobal`（单行，字段见 §3.3.7）
   - `EnemyList.xlsx` / `RoundData.xlsx`：M0 保持原结构即可（重命名为 TBWave/TBRound 可选，若改名须同步 `DataTables` 的 key）
   - **`__tables__.xlsx` 里为每张新表登记一行**（最容易漏，漏了就不会导出）
2. 运行 `D:\FreedomTower\Luban\gen_code_json.bat`（工作目录必须在 `Luban\`）
3. 校验产物：
   - `Assets/Gen/` 出现 `TBBullet.cs`、`TBLevel.cs`、`TBLevelMap.cs`、`TBGlobal.cs` 等
   - `Assets/ConfigJson/` 出现对应 json，且**非空**
4. **改造 `Assets/Scripts/Data/DataTables.cs`**：
   - 增加 6 张表的字段与加载
   - 加载方式改为经 AB（`ResLoader`）读 `config` 包内的 `TextAsset`；编辑器下走主读
   - 增加 `ValidateTables()`：记录数、交叉引用完整性检查，一次性汇总打印
5. 新增 `Assets/Scripts/Core/Cfg.cs`：`Float/Int/String/Get<T>` 安全读取工具（§3.5）
6. **修 `Json/JsonDataManager.cs`**：删除顶层 `using UnityEditor;`（否则打包编译失败，阻塞项 B5）
7. **补 `.gitignore`**：加入 `Luban/Config/Datas/~$*.xlsx`（Office 锁文件）

**验收**：Play 后 Console 打印 6 张表记录数与 Excel 一致；故意删掉 `tbtower.json` 时给出明确的 error 而非崩溃。

---

#### P0-2　2D 场景与棋盘搭建　`2.0d`　🔴

**依赖**：P0-0、P0-1

**步骤**
1. **在 `main.unity` 内搭建层级**（§6.1.1）：
   - 新建 `UICanvas`（打 Tag = `UICanvas`），其下创建 `BgPanel` / `NormalPanel` / `TipsPanel`；**`RenderMode` 改为 `ScreenSpaceOverlay`**
   - 现有 `bg` 移入 `bgPanel`
   - 新建 `BattleRoot`【**普通 `Transform`，世界空间**】，其下 `BoardRoot` / `PathRoot` / `TowerRoot` / `EnemyRoot` / `BulletRoot`（均为空 `Transform` 容器）
   - 新建 `Launcher`（挂 `Launcher.cs`）、`GameSceneLauncher`（挂 `GameSceneLauncher.cs`）
   - **工程设置**：`Graphics Settings → Transparency Sort Mode = Custom Axis`，轴 `(0,-1,0)`（§6.1.1）
2. **新建 `BoardView.cs`**（`Assets/Scripts/Game/`）：
   - `Build(TBLevelMap map, float cellSize)`：按 `rows/cols/cells` 生成 `CellView[,]`；**世界空间按 `CellCenter()` 摆放**，每个 `CellView` 是 `SpriteRenderer`
   - `WorldToCell(Vector2 worldPos, out int row, out int col)`：坐标除法（§2.3.4）
   - `CellCenter(row, col) → Vector2`：反向换算；`CellCenter3(row, col) → Vector3` 便于直接赋 `transform.position`
   - `SetCellHighlight(row, col, CellHighlight.None/Green/Red)`（改 `SpriteRenderer.color`）、`ResetAllHighlight()`
   - `ScreenToCell(Vector2 screenPos, out int row, out int col)`：`Camera.main.ScreenToWorldPoint`（**`z` 取 `-camera.transform.position.z`**）→ `WorldToCell`
3. **新建 `CellView.cs`**：单格视图（`SpriteRenderer` + 高亮状态）
4. **改造 `AStarWrapper/Point.cs`**：去 `Vector3`/`GameObject`，改 `Row/Col/Center(世界坐标)/IsWall`（§6.1.3）
5. **改造 `AStarWrapper/AStarManager.cs`**：
   - 新增 `BuildGrid(cells, cols, rows)`：**只建数据**，不生成物件
   - **删除** `OnInitMapData` 里的 `ReadData`（读 txt）与 `InitMap`（逐字符生成 3D 物件）两段逻辑
   - 路径绘制改**世界空间 `SpriteRenderer` 箭头池**（或 M0 先只画起终点标记 + Console 打印路径长度）
6. **新建 `GameFlowManager.cs`**（`Assets/Scripts/Game/`）：关卡初始化入口（读 `TBLevel` → 建棋盘 → 按棋盘尺寸调整相机 `orthographicSize` → 建网格 → 初始路径 → 通知 HUD）
7. **改造 `GameSceneLauncher.cs`**：改为调用 `GameFlowManager.InitLevel(levelId)`，移除 3D 相机就位逻辑
8. **改造 `CameraController.cs`**：正交相机的平移（拖拽）与缩放（改 `orthographicSize`）；M0 可只做"相机对准棋盘中心"

**验收**：Play 后棋盘按 `TBLevelMap` 正确生成（行列数、起终点、障碍一致）；Console 打印出初始路径的格子序列；格子高亮接口可手动调用生效。

---

#### P0-3　AB 资源加载系统　`3.0d`　🔴 **并行支线**

**依赖**：P0-0（接口）

**步骤**
1. `Assets/Scripts/Core/Res/BundleResLoader.cs`：
   - `Init`：加载 `ab_manifest`（`AssetBundleManifest`）→ 缓存全部包名与依赖关系
   - `LoadAsync<T>`：查 `ResTable` → 递归加载依赖包（引用计数 +1）→ `AssetBundle.LoadFromFileAsync` → `LoadAssetAsync<T>`
   - **并发合并**：同一个 bundle 的多个并发请求只发起一次实际加载，其余挂到回调队列（避免重复 IO）
   - 缓存：`Dictionary<string, BundleRef>` + `Dictionary<string, Object>`（asset 级）
   - 卸载：`Unload(false)` + `Resources.UnloadUnusedAssets()`（§4.5，**严禁 `Unload(true)`**）
   - 常驻包标记：`config`、`ui_common`
2. `Assets/Editor/BuildAssetBundles.cs`：构建脚本（§4.6）
   - 输出到 `Assets/StreamingAssets/AB/<BuildTarget>/`
   - 生成自定义清单 `manifest.json`（包名/大小/哈希/版本）
   - 菜单项：`Tools/资源工具/构建 AssetBundle/当前平台`
3. `Assets/Editor/ABNameSetter.cs`：按目录规则**自动打 AB 标记**（与 `ResPathUtil` 规则共用同一配置）
   - `Assets/_UIAssets/Tower/**` → `tower_normal`
   - `Assets/Prefabs/Tower/Tower_Normal.prefab` → `tower_normal`
   - `Assets/_UIAssets/Monsters/**` → `enemy_common`
   - `Assets/_UIAssets/Backgrounds/**` → `level_1`
   - UI 预制体 → `ui_hud` / `ui_common`
   - json（`Assets/ConfigJson/*.json`，普通 Assets 目录，TextAsset）→ `config`
     > ⚠️ 起初把 json 放在 `Assets/StreamingAssets/json/`，结果**读不出来**：
     > StreamingAssets 下的文件被 Unity 当作"原始文件"（DefaultAsset）处理，
     > **不会导入成 `TextAsset`** —— `LoadAssetAtPath<Object>()` 拿得到、
     > `LoadAssetAtPath<TextAsset>()` 返回 null。所以 Luban 的输出目录改为
     > `Assets/ConfigJson/`（普通 Assets 目录），编辑器直读与 AB 打包共用同一份。
4. `Assets/Scripts/Core/Res/ResPathUtil.cs`：逻辑名 → 编辑器路径推导（与 ABNameSetter 共用规则）

**验收**：菜单执行构建 → `AB/Windows/` 下生成 `.ab` 与 `ab_manifest`；切 `FORCE_AB` 宏后 Play，资源正常加载；Profiler 中 `AssetBundle` 分区显示正确的包加载与卸载（切关卡后计数归零）。

---

#### P0-4　资源就绪化与渲染路线统一　`1.0d`　🔴

**依赖**：P0-0

**v2.1 重大简化**：怪物资源**已是 2D**（119 prefab + Sprite + Animator），**不再需要占位素材、也不需要 3D→2D 转换工具**。本任务的重心从"造资源"变成"**统一渲染路线 + 清物理组件**"。

| 现有资源 | 状态 | 处理 |
|---|---|---|
| `Assets/_UIAssets/Monsters/**`（119 个 2D prefab） | ✅ **已就绪** | 直接用；仅需**删除 `CapsuleCollider2D`** |
| `Assets/_UIAssets/Tower/Normal/turret_base_128.png`、`turret_barrel_128.png` | ✅ 已是 2D | 保留，转为 `Tower_Normal` 的 `SpriteRenderer` |
| `Assets/_UIAssets/Backgrounds/Paper.png` | ✅ 已是 2D 背景 | 保留 |
| `Assets/Prefabs/Tower/Tower_Normal.prefab` | ⚠️ 仍是 UGUI | **转为 `SpriteRenderer`**（§6.2 有详细步骤） |
| `Bullet_Normal.prefab` | ❌ 不存在 | 新建（`SpriteRenderer` + `BaseBullet`） |

**步骤**
1. **转换 `Tower_Normal.prefab`（UGUI → SpriteRenderer）**：按 §6.2 开头的 6 步执行；同时挂 `NormalTower`(继承 `BaseTower`) 与 `TowerPlacement` 脚本，`Layer` 改 Default，加 `SortingGroup`
2. **新建 `Bullet_Normal.prefab`**：`SpriteRenderer` + `BaseBullet`，占位贴图用一张 8×8 圆点 PNG（安全起见 `Texture Type = Sprite`，PPU 100）
3. **新建怪物战斗 prefab（可选但推荐）**：从 119 个怪物 prefab 里挑 **1 个**（如 `Rat`）做 M0 用怪，在其上**附加 `BaseEnemy` 脚本 + `HpBar` 子节点（两张 Sprite）**，输出为 `Assets/Prefabs/Enemy/Enemy_Rat.prefab`
   > 不要直接改原包 prefab（会污染美术资源包，且升级素材包时被覆盖）。**用 Prefab Variant 或复制一份到 `Assets/Prefabs/Enemy/`**。
4. **批量清理物理组件**：写 Editor 工具 `Assets/Editor/PhysicsComponentCleaner.cs`，扫描指定目录批量移除 prefab 上的 `Collider2D`/`Rigidbody2D`/`Collider`/`Rigidbody`/`Targetter`
   - **M0 至少清掉 `Enemy_Rat.prefab` 与 `Tower_Normal.prefab` 上的物理组件**（完整批处理可以后做）
   - 复用 2026-09-25 新增的 `MissingScriptCleaner` 的写法与交互（菜单项 + 结果面板 + 预览模式）
5. **`SortingLayer` / `sortingOrder` 约定**（写进文档，避免各改各的）：
   | 对象 | sortingOrder | 说明 |
   |---|---|---|
   | 棋盘格子 `CellView` | 0 | 最底 |
   | 路径箭头 `MapArrow` | 10 | |
   | 怪物 | 200（沿用资源包默认） | |
   | 塔 | 300 | 默认盖住怪 |
   | 血条 / 伤害数字 | 500 | 最上 |
6. **创建 SpriteAtlas** `atlas_battle`（塔/怪/子弹/格子小图打进去，减少 DrawCall）
7. **创建 UI prefab**：`HudView`、`TipsView`（节点名与 `HudView.cs` 的 `transform.Find` 严格一致）
8. **校验一张怪物 PNG 的导入设置**：`Texture Type = Sprite`、`Pixels Per Unit = 100`、`Filter Mode` 与项目风格一致（像素风用 `Point`，手绘风用 `Bilinear`）

**验收**：转换后的塔与怪可在编辑器下经 `ResLoader` 加载并正常渲染；两者 `sortingOrder` 生效（塔能盖住怪）；M0 用的 prefab 上无任何物理组件。

---

#### P0-5　2D 化改造　`2.0d`　🟠

**依赖**：P0-1、P0-4

**步骤**（严格按 §1.4 的表格逐文件过）

1. **`Enemy/BaseEnemy.cs` 重写运动与表现**
   - 移除 `Rigidbody`、`Vector3.ProjectOnPlane`（广告牌）、世界空间 TMP 血条
   - `Position` 属性基于 `RectTransform.anchoredPosition`
   - `Tick(dt)` 按 §6.3 实现（`Vector2` 移动 + 到达阈值 + `PathProgress`）
   - 新增 `IsAlive`
   - 血条改**世界空间 `SpriteRenderer`**（挂怪物子节点，两张 Sprite：底 + 填充）
   - 朝向改 `localScale.x` 翻转（左右朝向）或 `localRotation.z`（支持全方位）
   - 删除 `_rigidbody`、`LookAtCamera` 相关代码
2. **`Bullet/BaseBullet.cs` 重写**
   - 按 §5.4 实现 `Tick(dt)`：`_dir` 位移 + 距离命中 + 超时回收
   - 移除 `OnTriggerEnter`、`transform.Translate`
   - 新增 `Damage`、`Init(target, damage, cfg)`、`IsAlive`/`_state`
   - **复用时必须重置**（`_target`/`_dir`/`_lifeTimer`/位置）
3. **`Tower/BaseTower.cs` 改造**
   - 移除 `Renderer`/`GetComponentsInChildren<Renderer>` 换色 → 改 `Image.color`
   - `_bulletPoint` 改从 `RectTransform` 层级查找 `Img_gun/BarrelPoint`（或直接用 `Img_gun`）
   - 攻击逻辑抽出为 `TickAttack(dt)`（§5.3.2），**不再在 `OnUpdate` 里无条件开火**
4. **`Tower/NormalTower.cs` 改造**：`Fire(target)` 经 `BulletManager` 取池化子弹并 `Init`
5. **`Node/*` 与 `Obstacle/*` 简化**：删除 `BasePoint`/`NormalPoint`/`StartPoint`/`EndPoint`/`EmptyPoint`/`NormalObstacle` 这些 MonoBehaviour（**格子改为纯数据 `CellData` + 视图 `CellView`**），或保留 `CellView` 一个类承载
   > 这一步是"删代码"最多的地方，也最能降低复杂度。建议**直接删除** `Assets/Scripts/Node/` 与 `Assets/Scripts/Obstacle/` 两个目录。
6. **`Util/FTProjectUtils.cs`**：`GetPointDistance` 增加 `Vector2` 重载；`SetObjParent` 增加 `RectTransform` 版本
7. **`Camera/CameraController.cs`**：M0 可只做正交相机的拖拽/滚轮缩放（`orthographicSize`），或整体注释掉

**验收**：怪物能沿 A* 路径平滑移动并正确到达终点；子弹朝目标飞并命中；Console 无 3D 相关警告。

---

#### P0-6　战斗判定改造　`2.5d`　🟠 **（需求 8 核心）**

**依赖**：P0-5、P0-2

**步骤**
1. **删除** `Assets/Scripts/Tower/Tower/Targetter.cs`
2. 新建 `Assets/Scripts/Core/Combat/EnemyGrid.cs`（§5.3.1）
3. 新建 `Assets/Scripts/Core/Combat/CombatSystem.cs`（§5.5）
   - 唯一订阅 `UpdateEvent`
   - 固定顺序：`SyncEnemyGrid` → `TickTowers` → `TickBullets`
   - 倒序遍历 + 失效引用清理
   - 同屏上限保护（`TBGlobal.maxEnemyAlive`）
4. 改造 `BaseTower.TickAttack(dt)`：实现 §5.3.2 的"锁定 + 节流 + 转向 + 冷却"流程
   - `_candidates` 成员缓冲复用（消除 GC）
   - 全程 `sqrMagnitude`
   - 空列表严格判空
5. 改造 `BaseBullet.Tick(dt)`：§5.4
6. **移除全部物理组件**：塔/怪/子弹 prefab 上的 `Collider`/`Rigidbody` 全删
7. 在 `Launcher.managerList` 注册 `CombatSystem`
8. 在 `ProjectSettings/DynamicsManager` 中确认无 2D/3D 碰撞层需求（可全部禁用相关层交互）
9. **写一个自检日志**：每 5 秒打印 `塔数 / 怪数 / 子弹数 / 索敌次数 / 命中次数 / 空放次数（应为 0）`

**验收**（对应 DoD 6、7、11、12）
- 无怪时"空放次数"恒为 0
- 有怪时塔转向、命中、伤害与 `power` 一致
- Profiler `Physics`/`Physics2D` 分区为 0
- `CombatSystem.OnUpdate` GC Alloc = 0 B
- 100 怪 + 30 塔单帧 CPU < 2ms

---

#### P0-7　塔的放置　`1.5d`　🟠

**依赖**：P0-2、P0-6

**步骤**
1. 重写 `Assets/Scripts/Tower/Tower/TowerPosition.cs` → 建议改名 `TowerPlacement.cs`：
   - 跟随鼠标：`BoardView.ScreenToCell(Input.mousePosition, out row, out col)` → `transform.position = BoardView.CellCenter3(row, col)`
   - 高亮：可建造染绿 / 不可建造染红（`BoardView.SetCellHighlight`）
   - 半透明预览：待放置塔的 `CanvasGroup.alpha = 0.6`
2. **重写 `TowerManager`**（修技术债 T3）：
   ```csharp
   public bool TryBuild(TowerType type, int row, int col, out BaseTower tower)
   {
       tower = null;
       var cell = BoardView.Instance.GetCell(row, col);
       if (cell == null || !cell.IsBuildable || cell.Tower != null) { Tips("该位置无法建造"); return false; }

       TowerConfig cfg = TowerConfigHelper.Get(type, level: 1);
       if (cfg == null) { Debug.LogError($"[Tower] 配置缺失 type={type}"); return false; }

       // ★ 先做路径校验（临时占位），通过后才扣费 —— 避免"扣了钱又建不成"
       cell.Point.IsWall = true;
       if (!AStarManager.Instance.IsFindPath())
       {
           cell.Point.IsWall = false;
           BoardView.Instance.SetCellHighlight(row, col, CellHighlight.Red);
           Tips("不能完全阻断怪物路径");
           return false;   // ★ 未扣费，无需退还
       }

       if (!PlayerDataManager.Instance.TrySpend(cfg.Prices))   // ★ 金币校验
       {
           cell.Point.IsWall = false;
           Tips("金币不足");
           return false;
       }

       var go = ResLoader.Instance.Instantiate(cfg.ResName, BoardView.Instance.TowerRoot);
       tower = go.GetComponent<BaseTower>();
       tower.Init(cfg, cell);
       cell.Tower = tower;
       EventDispatcher.TriggerEvent(EventName.RefreshPathEvent);   // ★ 重算路径
       EventDispatcher.TriggerEvent<BaseTower>(EventName.BuildTowerSuccess, tower);
       return true;
   }
   ```
   > **注意顺序**：v1.0 是先占位校验再建，但没有扣费校验；新顺序为「占位校验 → 扣费 → 实例化」，任何一步失败都完整回滚。**这比"先扣费再校验"更安全。**
3. 改造 `HudView` 的塔按钮：`onPointerDown` 进入待放置状态，`onPointerUp` 或点击格子确认建造
4. 建造成功后 `CombatSystem.RegisterTower(tower)`；拆除时 `Unregister`

**验收**（DoD 5、8）：非法格/已占用/堵死路径三种情况都有红色提示且不扣费；金币不足按钮置灰；建造成功扣除对应金币且路径立即重算。

---

#### P0-8　单回合流程 + 经济/生命闭环　`2.0d`　🟠

**依赖**：P0-6、P0-7

**步骤**
1. 新建 `Assets/Scripts/Core/Manager/PlayerDataManager.cs`（§6.6）
2. 新建 `Assets/Scripts/Round/WaveManager.cs`（取代 `RoundCountManager` 的波次职责，**删除或清空 `RoundCountManager`**）
   - `PlayRound(int roundId)`：读 `TBRound.waveIds` → 逐 `TBWave` 展开时间轴 → 单个累加计时器驱动生成
   - **不使用递归 Timer**（v1.0 的 `RecycleGenerateEnemy` 递归写法有索引错位 Bug，应废弃）
   - 存活数查询：`CombatSystem.AliveEnemyCount`
3. 改造 `GameFlowManager`：`InitLevel → Prepare → RoundRunning → RoundComplete`
   - `Prepare`：显示「点击开始」按钮
   - `RoundRunning`：调 `WaveManager.PlayRound`
   - 所有怪生成完毕 && 存活 == 0 → `RoundComplete` → `TipsView` 显示「回合完成」→ **M0 结束**
   - 监听 `GameOverEvent(false)` → `TipsView` 显示「失败」
4. `EventName.cs` 补事件：`EnemyKilledEvent`、`EnemyReachedEndEvent`、`GoldChangeEvent`、`GameOverEvent`、`RoundCompleteEvent`、`WaveStartEvent`
5. 在 `Launcher.managerList` 注册 `PlayerDataManager`
6. **修正 v1.0 的两处逻辑错误**（§6.3）：死亡发奖励、到终点扣玩家血
7. `EnemyManager` 修复池化字典键硬编码 Bug（用真实 `type`）

**验收**（DoD 9、10）：怪死亡金币增加；漏怪扣血；生命归零提示失败；本波清空提示回合完成。

---

#### P0-9　HUD 与提示　`1.0d`　🟠

**依赖**：P0-8

**步骤**
1. 新建 `Assets/Scripts/UI/HudView.cs`（`BaseView` 子类）：
   - 节点：`GoldTxt`、`HpTxt`、`RoundTxt`、`BtnStartWave`、`BtnTower_Normal`
   - 监听 `GoldChangeEvent`/`PlayerHpChangeEvent`/`WaveStartEvent`/`RoundCompleteEvent`
   - 金币/生命变化时数值跳动 + 颜色闪烁（DOTween）
2. 新建 `Assets/Scripts/UI/TipsView.cs`：`Show(string msg, float duration)`，队列化避免覆盖
3. 制作 UI prefab，**节点名与代码 `transform.Find` 严格一致**
4. 把 v1.0 中被注释掉的 `PlayerHpChangeEvent` / `PlayerRoundCountChange` 监听接回来（`MainView.cs:42`、`92-93`）
5. `MainView` 已废弃 → 由 `HudView` 取代（或直接改造 `MainView`，二选一）

**验收**：HUD 三项数值实时刷新；提示能正常弹出；按钮状态随金币变化。

---

#### P0-10　收尾　`1.0d`　🟡

1. **修 Build Settings**：`ProjectSettings/EditorBuildSettings.asset` 只保留 `Assets/Scenes/main.unity`（**统一大小写**，建议重命名为 `Main.unity`）
2. 修 `MainView.OnClickBtnReturn()` 的 `SceneManager.LoadScene("Start")` → 改为直接 `OpenView<StartView>`
3. **寻路加固**（§6.7）：迭代上限、最长行补齐、越界保护
4. **清理 3D 残留**：`Assets/PopMain.cs`、`Assets/TestTileMap.cs`、`Assets/Scripts/AStarWrapper/Scenes/`、`Assets/Editor/MapGenerator.cs`
5. **删除废弃脚本**：`Tower/Tower/Targetter.cs`、`Round/RoundCountManager.cs`、`Node/*`、`Obstacle/*`、`Core/ResourcesManager.cs`（保留 `[Obsolete]` 一个版本更稳妥）
6. **重命名**（技术债 T6）：`TowerCofig` → `TowerConfig`。~~`Luaban` → `Luban`~~ **✅ 已完成**（提交 `8ab496b1d`，含 `gen_code_json.bat` 健壮化重写与过期生成残留清理）
7. 补 `.gitignore`：`Luban/Config/Datas/~$*.xlsx`、`/Assets/StreamingAssets/AssetBundles/`
   （注意 `Assets/ConfigJson/` 是**源数据**，必须入库，不要加进忽略列表）

**验收**（DoD 14）：能打出 PC 包并启动到主场景。

### 7.4 建议排期（2 人并行，约 10 个工作日）

| 天 | 开发 A（配置 / 2D 化 / 战斗） | 开发 B（AB / 素材 / 场景 / UI） |
|---|---|---|
| D1 | **P0-1** 配置表链路（改表 + 导出 + DataTables） | **P0-0** IResLoader 接口 + 编辑器实现；**P0-4** 塔转 `SpriteRenderer` + 清物理组件 |
| D2 | P0-1 续 + `Cfg` 安全读取 + 配置自检 | **P0-3** AB 系统（Manifest + 依赖 + 异步） |
| D3 | **P0-5** 2D 化：BaseEnemy 重写 | P0-3 续 + 构建脚本 |
| D4 | **P0-5** 2D 化：BaseBullet / BaseTower / Node 清理 | **P0-2** main.unity 层级 + BoardView |
| D5 | **P0-6** EnemyGrid + CombatSystem | P0-2 续（AStarManager 2D 化 + Point 改造） |
| D6 | **P0-6** 索敌/命中改造 + 去物理 | **P0-3** 验证（FORCE_AB 跑通）+ ABNameSetter |
| D7 | **P0-6** 性能验证（Profiler 达标） | **P0-7** TowerPlacement + TowerManager 重写 |
| D8 | **P0-8** PlayerDataManager + WaveManager | P0-7 续 + **P0-9** HudView prefab |
| D9 | **P0-8** GameFlowManager 回合流程 | **P0-9** HudView/TipsView 接线 |
| D10 | **P0-10** 收尾（清理、加固、Build Settings） | 联调协助 + **M0 验收**（14 项 DoD 逐条过） |

---

## 8. 后续阶段概要

### M1　完整关卡流程与怪物资源接入

| 项 | 内容 |
|---|---|
| 多波次 / 多回合 | `WaveManager` 状态机（`Prepare/Spawning/Fighting/Interval/Finished`）；回合间布塔窗口 `TBLevel.waveIntervalMs` |
| 回合结算 | `RoundResultView`（击杀数、剩余生命、用时）；胜利/失败分支 |
| 路径重算精确化 | 建塔后所有敌人的 `_pathIndex` 按世界位置重新映射（§5.7 第 4 点） |
| **怪物战斗 prefab 批量化** | Editor 脚本：为 `_UIAssets/Monsters` 下的 119 个 prefab 批量生成"附加 `BaseEnemy` + 血条子节点 + 移除物理组件"的战斗 prefab（输出到 `Assets/Prefabs/Enemy/`，不改动原素材包），并同步写入 `TBEnemy` 表 |
| **动画状态机参数确认与统一** | 打开一个 `.controller` 确认状态驱动方式（参数/Trigger vs 直接 `Play` 具名状态），统一 `BaseEnemy` 的动画调用 |
| 路径可视化完善 | 世界空间 `SpriteRenderer` 箭头池完整实现，含转向与排序 |
| 射程预览圈 | 拖塔时显示半透明圆形射程 |
| 提前召唤下一波 | 玩家可提前召唤，奖励额外金币（原作经典设计） |
| 倍速 | 1× / 2×（`Time.timeScale`） |

### M2　内容扩展与手感　✅ **已交付**（2026-09-30，见 §Z.7）

| 项 | 内容 | 状态 |
|---|---|---|
| 多塔型 | 补齐 `TBTower.type` 的 5 类：单体 / AOE / 减速 / 穿透 / 激光；各自独立特效与音效 | ✅ 5 类全部落地；**减速塔于 M3 后改为范围光环**（见 §Z.9）；穿透/激光的外观暂复用普通塔（美术待补，换皮只改表 + ResTable） |
| 塔升级与出售 | 接 `TBTower.upgradeTo` / `sellPrice`；`TowerInfoView` 接线；点击已建塔的入口 | ✅ 含"换实例"升级、原地两段式出售确认、DPS 展示 |
| 子弹特性 | `TBBullet` 的 `pierce` / `aoeRadius` / `effectType`（减速、持续伤害） | ✅ 同时修掉了"穿透完全失效"与"AOE 每次命中都 GC"两个真实缺陷 |
| 怪物扩展 | 接入更多 `TBEnemy` 行；护甲、飞行（`isFlying`）、Boss | ✅ 新增 3 Boss + 1 高护甲精英（type=5 从 0 行变为 3 行），并编入第 10/11/12 波 |
| 飞行单位 | 单独 grid 或直线寻路；塔增加 `canAttackAir` | ✅ 取"直线寻路"方案；`isFlying` 原有 5 行数据终于被代码接上 |
| 音效系统 | 新增 `AudioManager` + `TBAudio` 配置表 | ✅ 系统/表/调用点齐备；**工程内 0 个音频文件**，属"系统先行"（见 §Z.7 假设 D-F） |
| 打击感 | 伤害数字、屏幕震动、命中闪白、死亡消散 | ✅ 四项全部落地，参数进 `Global.xlsx` |
| 数值平衡 | 建立 DPS vs 血量曲线，跑模拟脚本验证难度 | ✅ `.workbuddy/tools/balance_sim.py`；据此修掉"激光塔被严格压制"与"升级边际性价比为负" |

### M3　关卡与元进度　✅ **已交付**（2026-10-02，见 §Z.8）

| 项 | 内容 | 状态 |
|---|---|---|
| 多关卡 | `TBLevel` / `TBLevelMap` 扩充到 8 关；难度曲线 | ✅ 8 张棋盘（可建造格 142→70 递减）+ 40 波/40 回合；单回合有效血量 1.9k→94k 严格单调 |
| 关卡选择 | `SelectView` 强化：解锁状态、星级评价、难度标签 | ✅ 按钮按 `TBSceneInfo` **运行时生成**，加关卡 = 加配置行 |
| 地图编辑工具 | 可视化棋盘编辑器：刷格子、标起终点、一键导出 cells 字符串 | ✅ `LevelMapEditorWindow`（含 BFS 连通性自检）+ `apply_levelmap_export.py` 回写 xlsx |
| 存档系统 | 新建 `SaveManager`（与编辑器 API 完全解耦）；关卡解锁、星级、设置 | ✅ 零 UnityEditor 依赖；损坏/版本不符一律降级为新档 |
| 局内快照 | 金币/生命/已建塔/回合进度持久化，支持"退出后继续" | ✅ 回合边界存盘；恢复走 `RestoreTower`（复用同一套建塔流程，不扣钱） |
| 暂停与设置 | `PauseView` / `SettingView` | ✅ 暂停用 `Time.timeScale`，`OnDisable` 无条件恢复；设置持久化并即时推给音频 |

### M4　表现打磨　🟡 **代码部分已交付；美术部分待资源**（2026-10-02，见 §Z.8）

| 项 | 内容 | 状态 |
|---|---|---|
| 美术统一 | 塔/怪/背景/UI 全套 2D 资源；风格统一为纸片/扁平风 | ⬜ **需美术**，不是代码能解决的 |
| 动画 | 塔旋转与开火后坐、怪物行走/死亡、UI 转场 | 🟡 程序性部分已做：开火后坐（`TickRecoil`）、UI 淡入（`UIFader`）。怪物行走/死亡帧动画**需美术帧序列** |
| UI 适配 | 多分辨率（16:9 / 19.5:9 / iPad）、安全区、横屏锁定 | ✅ `SafeAreaFitter`（由 `UIManager` 自动补挂，**无需重建场景**）；横屏锁定在 `Launcher.Awake` |
| 相机 | 正交相机平移/缩放/边缘拖拽 | ✅ 中键拖拽 / WASD·方向键 / 边缘自动平移 + 边界夹取（放置或选中塔时自动禁用边缘平移） |
| 氛围 | 背景视差、粒子特效 | 🟡 视差已做（`BackgroundParallax`）；粒子**需美术资源** |

### M5　性能与发布　🟡 **代码部分已交付；打包 / 压测 / 瘦身需你执行**（2026-10-02，见 §Z.8）

| 项 | 内容 | 状态 |
|---|---|---|
| **AB 优化** | 包体分析、按关卡拆包、压缩格式调优（LZ4）、冗余资源去重、依赖关系可视化检查 | ⬜ **需 Unity 实际打包 + 真机包体数据**才有意义 |
| UGUI 优化 | SpriteAtlas 全覆盖、DrawCall 合批验证、Canvas 分层重建优化 | ⬜ SpriteAtlas 是 Unity 资产；合批必须看真机 Frame Debugger |
| 性能压测 | 低端机 200 怪 + 50 塔稳定 60fps | 🟡 **度量工具已交付**：`PerfProbe`（F3 打印 p50/p95/p99/最差帧/托管堆增量）。真机跑一局按键即得数据，但**设备不在我这边** |
| 对象池统一 | 替换各自的 Dictionary 池，统一用 `Core/ObjectPool` | ✅ **核查后确认早已统一**：EnemyManager / BulletManager 均用 `ObjectPool<T>`。PathArrowView 用的是"定长索引渲染器数组"，不是竞争实现，强行改反而退化 |
| 热更取舍 | 决策 HybridCLR 是否接入 | ✅ **决策：不接，并已移除**。`Assets` 内零引用却带来 798MB 的 `HybridCLRData/`，已从 `Packages/manifest.json` 删除 |
| 打包 | PC（Windows）+ Android；图标、启动图、签名、版本号 | ⬜ 需 Unity 构建 + 签名，且 Unity 在用户手里 |
| 质量 | 崩溃上报（Reporter 已内置）、关键路径埋点、完整回归用例 | ✅ 崩溃上报已内置；新增 `PerfProbe` 埋点；**回归用例见操作指南 §14** |
| 仓库 | 清理冗余；`.gitignore` 完善；视需要 `git filter-repo` 瘦身历史（2.17GB → 100MB） | 🟡 已做：`.gitignore` 补 `/.workbuddy/backup/`。**`git filter-repo` 是破坏性操作（重写全部 commit hash、需所有人重新克隆），按文档规定须你明确确认后才执行** |

---

## 9. 风险登记册

| # | 风险 | 概率 | 影响 | 应对 |
|---|---|---|---|---|
| **R1** | **塔与怪物的渲染体系不统一**（塔 = UGUI `Image`，怪 = 世界空间 `SpriteRenderer`） | ~~高~~ 中 | 高 | 塔仅 **1 个** prefab，转 `SpriteRenderer` 成本≈0（步骤见 §6.2 开头）。**M0 的 P0-4 必须先完成此转换**，否则"塔怪按 Y 互相遮挡"与坐标换算无法统一 |
| **R1b** | **怪物 `Animator` 状态驱动方式未知** | 中 | 中 | 30 个 `.controller` 由美术包提供，State 可能用参数/Trigger 驱动也可能直接 `Play("Walk")`。**P0-4 阶段先打开 1 个 `.controller` 确认**，再定 `BaseEnemy` 的动画调用；若为参数驱动，需在配置表加 `animParamType` |
| **R2** | **AB 系统的"编辑器能跑、真机丢资源"** | 高 | 高 | ①`ResPathUtil` 与 `ABNameSetter` **共用同一份映射规则**；②M0 验收项 13 强制切 `FORCE_AB` 验证；③严禁 `Unload(true)` |
| **R3** | 去物理后自实现的判定有 Bug（漏判/误判） | 中 | 高 | ①M0 用"追踪目标 + 距离判定"最简形态；②自检日志统计空放/命中次数；③启动时校验 `speed × dt < hitRadius`；④写 EditMode 单元测试覆盖 `EnemyGrid.QueryCircle` 与 `FindTarget` |
| **R4** | 路径重算后 `PathProgress` 错乱，索敌策略失效 | 中 | 中 | M0 简化处理（重算后置 0）；M1 做精确映射并补测试 |
| **R5** | 配置表字段改动与 `Assets/Gen` 生成物冲突 | 中 | 中 | `Assets/Gen/` 视为生成物，**禁止手改**；改表必重导并提交 |
| **R6** | UGUI 大量 Image 导致 DrawCall 过高 | 中 | 中 | 战斗资源全进 SpriteAtlas；**棋盘格子绝对定位，不用 `LayoutGroup`**；分 Canvas 层减少重建 |
| ~~**R7**~~ | ~~`Luaban` → `Luban` 重命名牵动大量路径引用~~ **✅ 已解决** | — | — | 已于提交 `8ab496b1d` 完成：253 文件 `git mv` 保留历史，`gen_code_json.bat` 改用 `%~dp0` 不再依赖工作目录，并清理了 7 个过期生成残留 |
| **R8** | Excel 表结构改动导致策划已填数据丢失 | 中 | 高 | 改表结构前**先提交一次备份**；只增列不删列；删列先在 `__tables__.xlsx` 保留兼容 |
| **R9** | `StreamingAssets` 下的 json **不会被导入成 TextAsset**（实测踩中，比"不会进 AB"更严重） | 高 | **已发生** | Luban 的 `--output_data_dir` 直接指向 `Assets/ConfigJson/`（普通 Assets 目录），编辑器直读与 AB 打包共用；不再有第二份副本 |
| **R10** | 单场景架构下 UI 生命周期混乱 | 中 | 中 | 统一由 `GameFlowManager` 管理 UI 开关，禁止散落的 `OpenView` |
| **R11** | 移除物理组件不彻底，残留触发回调 | 中 | 中 | 写批量清理 Editor 工具；Play 时校验 `Physics/Physics2D` Profiler 分区为 0（DoD 11） |
| R12 | 仓库体积（历史 2.17GB）影响协作 | 高 | 中 | 已完成 `.gitignore` 整改（跟踪文件 28932 → 2876）；历史瘦身需 `git filter-repo`，单独评估 |

---

## 10. 附录

### 10.1 关键常量迁移对照表

| 现有常量 | 位置 | 迁移目标 |
|---|---|---|
| `GlobalConst.PlayerHp = 10` | 玩家生命 | → **`TBLevel.initialHp`** |
| `GlobalConst.GoldCoin = 100` | 初始金币 | → **`TBLevel.initialGold`** |
| `GlobalConst.EnemyHp = 6` | 怪物血量 | → **`TBEnemy.hp`** |
| `GlobalConst.EnemySpeed = 12` | 怪物速度 | → **`TBEnemy.speed`**（单位改像素/秒） |
| `GlobalConst.FireInterval = 0.2` | 塔攻击间隔 | → **`TBTower.CD / 1000`** |
| `GlobalConst.BulletSpeed = 25` | 子弹速度 | → **`TBBullet.speed`**（单位改像素/秒） |
| `GlobalConst.EnemyScale = 1.2` | 怪物缩放 | → **`TBEnemy.scale`** |
| `GlobalConst.RoundCount = 10` | 回合数 | → `TBLevel.roundIds.Count` |
| `GlobalConst.EnemyGenerateInterval = 1.0` | 生成间隔 | → **`TBWave.spawnIntervalMs / 1000`** |
| `GlobalConst.RoundEnemyNumber = 10` | 每波数量 | → `TBWave.enemyIds.Count` |
| `GlobalConst.BuildDistance` / `UnbuildYPosition` / `BuildYVector3` / `PointScale` / `PointVector3` | 3D 建造参数 | → **2D 下作废**；格子尺寸改用 `TBGlobal.cellSize` |
| `TowerCofig.Radius = 6` | 塔射程 | → **`TBTower.radius`**（单位改格） |
| `TowerCofig.RotateSpeed = 60` | 塔转向速度 | → **`TBTower.rotateSpeed`** |
| `TowerCofig.BulletSpeed = 20` | 子弹速度 | → `TBBullet.speed` |
| `TowerCofig.cs` 整体 | — | 文件删除，改名 `TowerConfig` 前先在 M0 后段处理 |
| `AssetData.AssetDictionary` | 资源路径字典 | → **`ResTable`**（bundle + asset） |

### 10.2 建议新增 / 删除文件清单

**新增**
```
Assets/Scripts/Core/Res/IResLoader.cs               ★ §4.4
Assets/Scripts/Core/Res/ResLoader.cs                ★ 静态门面 + 平台切换
Assets/Scripts/Core/Res/EditorResLoader.cs          ★ 编辑器直读实现
Assets/Scripts/Core/Res/BundleResLoader.cs          ★ 真 AB 实现（P0-3）
Assets/Scripts/Core/Res/ResTable.cs                 ★ 逻辑名 → (bundle, asset)
Assets/Scripts/Core/Res/ResPathUtil.cs              ★ 逻辑名 → 编辑器路径（与 ABNameSetter 共用规则）
Assets/Scripts/Core/Combat/EnemyGrid.cs             ★ §5.3.1
Assets/Scripts/Core/Combat/CombatSystem.cs          ★ §5.5
Assets/Scripts/Core/Cfg.cs                          ★ 配置安全读取工具 §3.5
Assets/Scripts/Core/Manager/PlayerDataManager.cs    ★ §6.6
Assets/Scripts/Game/BoardView.cs                    ★ §6.1.3 棋盘视图
Assets/Scripts/Game/CellView.cs                     ★ 单格视图
Assets/Scripts/Game/CellData.cs                     ★ 格子数据（纯数据）
Assets/Scripts/Game/GameFlowManager.cs              ★ §6.5 关卡流程
Assets/Scripts/Round/WaveManager.cs                 ★ §6.5 波次调度
Assets/Scripts/Data/TowerConfig.cs                  ★ 塔配置封装（替代 TowerCofig）
Assets/Scripts/Data/EnemyConfig.cs                  ★ 怪物配置封装
Assets/Scripts/Data/BulletConfig.cs                 ★ 子弹配置封装
Assets/Scripts/UI/HudView.cs                        ★ §6.8
Assets/Scripts/UI/TipsView.cs                       ★ §6.8
Assets/Scripts/UI/RoundResultView.cs                （M1）
Assets/Editor/BuildAssetBundles.cs                  ★ §4.6
Assets/Editor/ABNameSetter.cs                       ★ §4.6 自动打 AB 标记
Assets/Editor/PhysicsComponentCleaner.cs            ★ 批量清理物理组件（P0-4）
Assets/Editor/ConfigValidator.cs                    ★ 配置自检菜单
```

**删除 / 废弃**
```
Assets/Scripts/Tower/Tower/Targetter.cs             ✗ 被 CombatSystem + EnemyGrid 取代
Assets/Scripts/Round/RoundCountManager.cs           ✗ 被 WaveManager 取代
Assets/Scripts/Node/**                              ✗ 格子改 CellData + CellView
Assets/Scripts/Obstacle/**                          ✗ 合并进格子类型
Assets/Scripts/Core/ResourcesManager.cs             ✗ 被 IResLoader 取代（先 [Obsolete]）
Assets/Scripts/Data/AssetData.cs                    ✗ 被 ResTable 取代
Assets/Scripts/Config/TowerCofig.cs                 ✗ 被 TBTower + TowerConfig 取代
Assets/Scripts/Config/GlobalConst.cs                ◐ 数值迁表后仅保留极少数表现常量
Assets/Scripts/Json/JsonDataManager.cs              ◐ 修 using UnityEditor 后交 SaveManager（M3）
Assets/PopMain.cs / Assets/TestTileMap.cs           ✗ 遗留测试代码
Assets/Editor/MapGenerator.cs                       ✗ 3D 地图生成器作废（M3 换成 2D 棋盘编辑器）
Assets/Scripts/AStarWrapper/Scenes/**               ✗ 示例场景
Assets/StreamingAssets/Map/**                       ✗ ASCII 地图方案作废（需求 2）
```

### 10.3 关键代码骨架

**A. 棋盘生成（`BoardView`）**

```csharp
public void Build(TBLevelMap map, float cellSize)
{
    _cellSize = cellSize;                       // 世界单位，建议 1.0（PPU=100 对齐）
    _rows = map.Rows; _cols = map.Cols;
    _cells = new CellView[_rows, _cols];
    _root.position = Vector3.zero;              // 世界空间原点（棋盘左上角）

    for (int r = 0; r < _rows; r++)
    {
        string line = map.Cells[r];                 // 第 r 行字符串
        for (int c = 0; c < _cols; c++)
        {
            char ch = c < line.Length ? line[c] : '.';
            CellType type = ParseCell(ch);
            var data = new CellData { Row = r, Col = c, Type = type,
                                      Center = CellCenter(r, c),
                                      IsWall = (type == CellType.Obstacle || type == CellType.Hole) };
            var view = CreateCellView(data, _root);  // SpriteRenderer，直接设 transform.position
            _cells[r, c] = view;
            if (type == CellType.Spawn) _spawnCell = data;
            if (type == CellType.End)   _endCell   = data;
        }
    }
}

/// 格子中心（世界坐标），左上角为原点、y 向下为负
public Vector2 CellCenter(int row, int col)
    => new Vector2((col + 0.5f) * _cellSize, -(row + 0.5f) * _cellSize) + (Vector2)_root.position;

public Vector3 CellCenter3(int row, int col)
{
    Vector2 v = CellCenter(row, col);
    return new Vector3(v.x, v.y, 0f);
}

/// 世界坐标 → 格子索引（纯数学除法，无物理）
public bool WorldToCell(Vector2 worldPos, out int row, out int col)
{
    Vector2 local = worldPos - (Vector2)_root.position;
    col = Mathf.FloorToInt(local.x / _cellSize);
    row = Mathf.FloorToInt(-local.y / _cellSize);
    return row >= 0 && row < _rows && col >= 0 && col < _cols;
}

/// 屏幕坐标 → 格子索引（正交相机下 z 需取 -camera.z 才落在 z=0 平面）
public bool ScreenToCell(Vector2 screenPos, out int row, out int col)
{
    Vector3 wp = Camera.main.ScreenToWorldPoint(
        new Vector3(screenPos.x, screenPos.y, -Camera.main.transform.position.z));
    return WorldToCell(wp, out row, out col);
}
```

**B. 集中式战斗 tick（`CombatSystem`）**

```csharp
private void OnUpdate()
{
    float dt = Time.deltaTime;

    // ① 怪物移动 + 网格同步（倒序，顺手清理失效引用）
    for (int i = _enemies.Count - 1; i >= 0; i--)
    {
        var e = _enemies[i];
        if (e == null || !e.IsAlive) { _enemies.RemoveAt(i); continue; }
        e.Tick(dt);
        Grid.Update(e, e.Position);
    }

    // ② 塔索敌与开火（节流在 Tower 内部）
    for (int i = _towers.Count - 1; i >= 0; i--)
    {
        var t = _towers[i];
        if (t == null) { _towers.RemoveAt(i); continue; }
        t.TickAttack(dt);
    }

    // ③ 子弹推进与命中判定
    for (int i = _bullets.Count - 1; i >= 0; i--)
    {
        var b = _bullets[i];
        if (b == null) { _bullets.RemoveAt(i); continue; }
        b.Tick(dt);
    }
}
```

**C. 波次时间轴展开（`WaveManager`，建议配单元测试）**

```csharp
/// 把一个回合展开为平铺的 (时刻, 怪物id) 时间轴
public static List<SpawnEntry> BuildTimeline(int roundId, TBRound tbRound, TBWave tbWave)
{
    var round = tbRound.Get(roundId);
    if (round == null) { Debug.LogError($"[Wave] TBRound 缺少 id={roundId}"); return new(); }

    var list = new List<SpawnEntry>();
    float cursor = 0f;                                  // 累计秒

    foreach (int waveId in round.WaveIds)
    {
        var wave = tbWave.Get(waveId);
        if (wave == null) { Debug.LogWarning($"[Wave] 跳过缺失的 TBWave id={waveId}"); continue; }

        float baseTime = cursor + wave.StartDelayMs / 1000f;
        float gap      = wave.SpawnIntervalMs / 1000f;

        for (int i = 0; i < wave.EnemyIds.Count; i++)
            list.Add(new SpawnEntry { TimeSec = baseTime + i * gap, EnemyId = wave.EnemyIds[i] });

        cursor = baseTime + Mathf.Max(0, wave.EnemyIds.Count - 1) * gap;
    }

    list.Sort((a, b) => a.TimeSec.CompareTo(b.TimeSec));
    return list;
}
```

**D. 塔索敌与开火（`BaseTower`）**

见 §5.3.2 完整实现。

**E. 建造校验（`TowerManager.TryBuild`）**

见 §7.3 P0-7 完整实现。

### 10.4 M0 验收自检清单（可直接勾选）

```
【环境与配置】
[ ]  1. Play 全程无 Exception / NullReference / Error
[ ]  2. Luban 导出成功，Console 打印 6 张表记录数与 Excel 一致
[ ]  3. 故意删除某个 json 时给出明确 error 而非崩溃
[ ]  4. 改 Excel 数值（怪物血量或塔攻击力）→ 重导 → 游戏内生效

【渲染路线统一（v2.1 重点）】
[ ]  5. `Tower_Normal.prefab` 已转为 `SpriteRenderer`（无 `RectTransform`/`CanvasRenderer`/`Image`）
[ ]  6. 塔与怪物的 `sortingOrder` 生效：塔（300）能正确盖住怪（200）
[ ]  7. `Transparency Sort Mode` 已设为 `Custom Axis (0,-1,0)`
[ ]  8. M0 用的怪物 prefab 上**无 `CapsuleCollider2D`**
[ ]  9. 怪物四态动画可切换（`Ready` / `Walk` / `Death`）

【2D 棋盘】
[ ] 10. 棋盘按 TBLevelMap 正确生成（行列数、起终点、障碍一致）
[ ] 11. 初始路径计算正确，Console 打印路径格子序列
[ ] 12. 相机 `orthographicSize` 与棋盘尺寸匹配，棋盘完整可见

【建造】
[ ] 13. 拖塔可放置，可建造格染绿
[ ] 14. 非法格 / 已占用 / 堵死路径 三种情况染红且不扣费
[ ] 15. 金币不足时按钮置灰 + 提示
[ ] 16. 建造成功扣除 TBTower.prices 对应金币，路径立即重算

【战斗判定（需求 8 重点）】
[ ] 17. 无目标时"空放次数"恒为 0
[ ] 18. 有目标时塔转向、开火、命中，伤害 = TBTower.power
[ ] 19. Profiler 中 Physics / Physics2D 分区恒为 0
[ ] 20. CombatSystem.OnUpdate 的 GC Alloc = 0 B
[ ] 21. 100 怪 + 30 塔单帧 CPU < 2ms（中端设备）

【经济与生命】
[ ] 22. 怪物死亡金币增加（= TBEnemy.reward）
[ ] 23. 怪物走到终点扣除玩家生命（= TBEnemy.damageToPlayer）
[ ] 24. 生命归零提示失败

【回合闭环】
[ ] 25. 点击开始后按 TBWave 定时出生怪物
[ ] 26. 本波怪物清空后提示「回合完成」

【资源加载（需求 7 重点）】
[ ] 27. 编辑器模拟模式下所有资源正常加载
[ ] 28. 切 FORCE_AB 宏后仍能正常跑通（真 AB 路径）
[ ] 29. 切关卡/退出后 AB 引用计数归零，无资源泄漏

【打包】
[ ] 30. Build Settings 无红色缺失项
[ ] 25. 能打出 PC 包并启动到主场景
[ ] 26. 连续运行 10 分钟无内存持续增长（Profiler 观察）
```

---

**文档结束**

> **变更记录**
> - **v2.0（2026-09-26）**：2D 重构版。按 8 项补充要求整体重写：
>   ① 3D → 2D（UGUI + 正交相机方案定案）；② 废弃 ASCII 地图文件，改配置表驱动棋盘；
>   ③ 明确配置表位于 `D:\FreedomTower\Luban` 并完整标注工具链；
>   ④ 新增 `TBBullet`/`TBLevel`/`TBLevelMap`/`TBGlobal` 表，经济/波次/怪物/塔全量配置化；
>   ⑤ M0 范围收窄为单回合闭环，缺失字段走默认值不阻塞；
>   ⑥ 明确在 `main.unity` 内实现并列出目标层级；
>   ⑦ 全新设计 AssetBundle 加载系统（含编辑器模拟模式）；
>   ⑧ 彻底移除物理触发器，改网格空间哈希 + 距离判定 + 集中式 tick。
>   新增 §1.4「2D 重构影响面」逐文件清单，避免漏改。
> - **v2.1（2026-09-26）**：**2D 技术路线修正版**。实测发现：
>   ① 原 120 个 **3D 怪物 prefab 已被删除**，全面替换为 **2D `SpriteRenderer` + `Animator`** 实现
>      （`_UIAssets/Monsters/**`：119 prefab / 122 Sprite（PPU=100）/ 120 `.anim` / 30 `.controller`，
>      每怪含 `Ready`/`Walk`/`Attack`/`Death` 四态动画，带 `SortingGroup` 与 `CapsuleCollider2D`）；
>   ② 而 `Tower_Normal.prefab` 仍是 UGUI（`RectTransform` + `Image`），与怪物不在同一渲染体系。
>   **因此 v2.0 定案的 UGUI 路线被推翻**，改为 **「世界空间 2D + `SpriteRenderer`（玩法对象）+ UGUI（HUD）」**，
>   并据资源反推出格子尺寸 `CellSize = 1` 世界单位、建议棋盘 16×9、需设 `Transparency Sort Mode = Custom Axis`。
>   同步修正：§0.1、§1.1、§1.3（B7）、§1.4、§2.3（整节重写）、§3.3.2（`animPrefix`→`animController`）、
>   §6.1、§6.2（新增塔转换步骤）、§6.3（新增动画集成）、§6.7、§6.8、§7（P0-2/P0-4/排期）、§9（R1/R1b）、§10.2–10.4。
>   另：`Luaban` → `Luban` 重命名已完成（提交 `8ab496b1d`）。
> - v1.0（2026-09-26）：首版（3D 方案），已被 v2.x 取代。
> - **v2.2（2026-09-26）**：**M0 实施纪要**。代码已按本方案落地，实施过程中对若干设计细节做了修正或收窄。
>   为避免文档与代码互相矛盾，实施结果以本节为准：

---

# 附录 Z · M0 实施纪要（v2.2）

> 本节记录 M0 实际落地的结果，包含**与 v2.1 方案的差异**与**实施中发现并修复的缺陷**。
> 文档其余章节描述的是设计意图；若有出入，**以本节为准**。

## Z.1 与 v2.1 方案的差异

| 项 | v2.1 方案 | 实际实现 | 原因 |
|---|---|---|---|
| UI 框架 | 沿用 `BaseView` / `AssetData` / `ResourcesManager` 那套"new 非 MonoBehaviour View" | **删除这四个类**，`UIManager` 直接管理 prefab 实例 | View 必须是 `new()` 可构造的普通类，就拿不到 MonoBehaviour 生命周期、也无法在 prefab 上序列化引用 |
| 关卡流程 | 新增 `GameSceneLauncher` 驱动 `GameFlowManager` | 保留，但 `GameSceneLauncher` 改为**组合根**：集中持有全部场景引用并在 `Awake` 里校验后注入 | 引用散落在各组件上时，漏连只会以随机时刻的 `NullReference` 暴露 |
| `Tower_Normal` 结构 | 未明确 | `Tower_Normal → barbette → Img_gun → BarrelPoint` | `BaseTower` 用 `transform.Find("barbette/Img_gun")` 取炮管、取 `BarrelPoint` 作为出膛点 |
| 格子缩放 | 未明确 | `CellView` 按 **精灵原生尺寸**折算：`scale = cellSize*0.94 / sprite.bounds.size` | 格子贴图 128px、PPU=100 → 原生 1.28 单位；直接写 `0.94` 会让格子重叠 |
| M0 回合数 | 单回合闭环 | 关卡 1 实际有 **10 个回合**，`GameFlowManager` 实现了完整的多回合链 | 成本几乎为零，且"打完 10 回合通关"是更好的验收场景 |
| AB 释放流程 | 切关整包释放 | `ReleaseBundle` 已实现，但 M0 只有单关卡，**未接入切关流程**（排 M1） | 无第二关卡可切 |
| 怪物尺寸 | 未定 | 约定为**最终缩放 = prefab 根节点缩放 × `EnemyData.scale`**；M0 默认 `scale = 0.5`（怪物约 1.6 格宽），`scale = 1` 表示保持美术在 prefab 里的授权缩放 | 美术在怪物 prefab 根节点设了 `scale 0.5`；代码若直接覆盖会放大 2 倍，故改为**相乘** |
| 配置表路径 | 单一 `EditorPath` | 仍是单一路径，但**位置从 `Assets/StreamingAssets/json/` 改为 `Assets/ConfigJson/`**（Luban 的 `--output_data_dir` 直接指向那里） | StreamingAssets 下的文件不会被导入成 `TextAsset`，编辑器读不到内容（详见 Z.2 第 16 条）。中途曾尝试"双路径 + 构建时同步副本"，但那是基于错误前提的过度设计，已回退 |

## Z.2 实施中发现并修复的缺陷

| # | 缺陷 | 症状 | 修复 |
|---|---|---|---|
| 1 | **建塔后怪物不改道** | 路径重算了但没人通知怪物，它们继续沿旧路径走 —— **塔摆了等于白摆**，《坚守阵地》的核心机制失效 | `CombatSystem` 订阅 `RefreshPathEvent`，遍历存活怪物逐只 `RefreshPath()` |
| 2 | 怪物 prefab 授权缩放被覆盖 | `transform.localScale = Vector3.one * cfg.Scale` 把美术的 `0.5` 冲掉，怪物突然大 2 倍 | 首次 `Init` 记下 `_baseScale`，之后 `_baseScale * cfg.Scale` |
| 3 | 血条用 `SpriteRenderer.size` 无效 | `size` 只在 `drawMode` 为 Sliced/Tiled 时生效，而 Sliced 要求精灵带九宫格边框 → 血条永远满格 | 改 `transform.localScale.x` + 中心左移对齐左边缘 |
| 4 | 命中判定漏算怪物体积 | 只用子弹 `hitRadius` 时判定面是"目标中心的小圆"，**怪物越大越难打中** | 判定半径改为 `hitRadius + target.BodyRadius` |
| 5 | 格子/箭头缩放写死 | 格子互相重叠；箭头尺寸与格子边长不匹配 | 一律按 `sprite.bounds.size` 折算 |
| 6 | **MonoBehaviour 类名 ≠ 文件名** | `BoardView`/`CellView` 写在 `Board.cs`、`NormalTower` 写在 `BaseTower.cs`、`ResLoaderRunnerBehaviour` 写在 `ResLoader.cs` → Unity 拿不到 `MonoScript`，**Editor 脚本无法把组件序列化进 prefab** | 全部拆成独立文件（Unity 硬性要求） |
| 7 | HUD 初值不刷新 | `PlayerStateInitEvent` 在 HUD 实例化之前已触发，HUD 一直显示 prefab 占位文案 | `HudView.RefreshAll()` 公开，建关后显式调用一次 |
| 8 | `EventSystem` 缺失导致点 UI 时误放塔 | `IsPointerOverGameObject()` 恒为 false | 场景搭建脚本必定创建 `EventSystem`；自检里也校验 |
| 9 | `gen_code_json.bat` 缺 `--` 分隔符 | `unknown argument: -d`，工具跑不起来 | 补 `--` + `DOTNET_ROLL_FORWARD=LatestMajor` + 产物自检 |
| 10 | `ResPathUtil.PlatformFolder` 误判平台 | 判断里含 `UNITY_EDITOR_OSX`，在 Mac 上给 Windows 打工会得到 `macOS` 目录 | 只判断**构建目标**相关宏 |
| 11 | **事件监听 arity 不匹配 → 编译不过** | `HudView` 把 `OnRoundClear(int)` 传给了 `AddEventListener(string, Action)` 重载 → `CS1503: cannot convert from 'method group' to 'Action'` | 显式写成 `AddEventListener<int>(...)` / `RemoveEventListener<int>(...)`。**同类风险已全量排查**（见 Z.6） |
| 12 | 配置表路径的设计前提是错的（第一版修法只是"换个地方失败"） | 原本把配置 JSON 登记在 `Assets/ConfigJson/`，但那个目录当时是"打包时才生成"的 → 编辑器直读它 → 8 张表全失败、关卡建不起来 | 第一版给 `ResAddress` 加了 `ABPath` 做"双路径 + 构建时同步副本"。**但第二版实测发现真正的病根是第 16 条**，于是回退双路径机制，把 Luban 的输出目录直接改成 `Assets/ConfigJson/` |
| 13 | **实例化时把 `localScale` 重置成 1，覆盖了美术的授权缩放** | `AttachTo` 里 `localScale = Vector3.one` 让怪物根节点从 0.5 变 1.0 → **怪物大 2 倍**（塔 0.8 → 1.0 也偏大）；更严重的是 `EnemyData.scale` 的"相乘"语义被破坏，调参完全不符合直觉 | 删掉 `AttachTo` 里的 `localScale` 赋值。`Instantiate` 已复制预制体变换，`SetParent(parent, false)` 本身保留 local 值，不需要归一化 |
| 14 | 池化对象在 **inactive** 状态下取子组件失败 | 对象池归还时 `SetActive(false)`，而 `Init` 发生在"取出后、激活前"；`GetComponentInChildren<T>()` 默认**跳过未激活的子物体** → 若 Animator/SpriteRenderer 挂在子节点上会取到 null，动画与子弹渲染静默失效 | 统一改为 `GetComponentInChildren<T>(true)`。同时给 AnimatorController 的替换加一次性标记，避免每次出生都重查表 |
| 15 | **枚举成员名写错 → CS0117** | `BuildAssetBundleOptions.Deterministic` 报 `CS0117: does not contain a definition for 'Deterministic'`（我按"直觉"写的名字）。该枚举里**根本没有**这个成员 | 正确名是 `UseContentHash`（Unity 2022.2+ 推荐；历史上的名字是已废弃的 `DeterministicAssetBundle`）。**已建工具把这类错误变成可静态检查的**（见 Z.6 的 `check_unity_api.py`） |
| 16 | **配置表放在 StreamingAssets 导致读不出来（真正的病根）** | 运行时报 8 条 `[Res] 文本资源「tbenemydata」加载失败…未被识别为 TextAsset`。**关键线索**：`[Res] 预加载自检通过，共 8 个资源全部就绪` 同时出现 | **`Assets/StreamingAssets/` 下的文件被 Unity 当作"原始文件"（DefaultAsset）处理，不会导入成 `TextAsset`** → `LoadAssetAtPath<Object>()` 返回非 null（所以"存在性自检"通过），而 `LoadAssetAtPath<TextAsset>()` 返回 null（所以读内容失败）。修法：Luban 的 `--output_data_dir` 改指 `Assets/ConfigJson/`（普通 Assets 目录），并删除 `StreamingAssets/json/`。同时把**自检与打包预检都改为用 `TextAsset` 类型去查**，并把 `EditorResLoader` 的 TextAsset 报错信息改成能直接指出这个坑 |
| **17** | **A\* 网格的两个轴语义同时反了（最隐蔽的一个）** | 表现为：地图正常生成，但**既没有路径箭头、也没有 HUD、也没有怪物**。Console 只有 `[Flow] 状态=Loading 回合=0/0`，**没有任何异常** | `AStarWrapper` 插件把 `Point.X` 当**横轴/列**（用 `mapWidth` 判边界）、`Point.Y` 当**纵轴/行**，并直接 `map[X, Y]`；而 `BuildGrid` 写的是 `new Point[rows, cols]` + `Point(row, col)`，**两个轴的语义同时反了**。后果：插件的边界判断 `point.X < mapWidth - 1` 实际变成 `row < 15`（恒真），于是 `map[row + 1, col]` 在最后一行越界 → `IndexOutOfRangeException`。修法：数组改为 `new Point[cols, rows]`、`X=col / Y=row`、`Map[col, row]`，并加"数组维度 vs 声明维度"自检 |
| **18** | **事件系统静默吞掉异常，让第 17 条隐形** | 第 17 条的越界异常发生在 `GameFlowManager.OnConfigLoaded` 里，而它是被 `EventDispatcher.TriggerEvent(ConfigLoadedEvent)` 调起来的 | `EventController` 的 5 处 `catch (Exception e) { string.Format(e.Message); }` 是**空操作**——表达式结果未被使用，异常被彻底吃掉。修法：改为 `Debug.LogException(exception)`。**这条不改，任何"事件回调里抛异常"的 bug 都会表现为"什么都没发生"** |
| 19 | **日志被心跳刷屏，掩盖真正的错误** | `CombatSystem` 每 5 秒打一条战斗统计，空闲期也打，把 Editor.log 刷到 3.7MB（3000+ 行 `[Combat] 怪=0…`），导致真正的错误被冲走 | 加"场上什么都没有就不打"的短路；并把「无目标开火」这个**正确性不变量**的检查从 `showDebugLog` 开关里移出来（它必须永远生效） |

### Z.6 编译验证方法与已知限制

M0 交付时**无法在本机编译**（安全策略明确禁止调用 `csc`，`error CS` 只能在 Unity 里拿到）。
因此采用了下面的替代验证，并在拿到用户的实际编译日志后修复了 2 个 `CS1503`：

| 验证手段 | 覆盖的问题类别 | 结果 |
|---|---|---|
| 解析 `Editor.log` 的 `error CS` 行 | 真实编译错误 | 修复后归零 |
| `.workbuddy/tools/check_code.py` | 括号平衡 / 类型重名（CS0101）/ **MonoBehaviour 类名≠文件名** / `EventName` 使用 vs 定义 / `ResTable` 逻辑名使用 vs 登记 | PASS |
| `.workbuddy/tools/check_events.py` | 事件监听器参数个数 vs 泛型 arity（**arity 不匹配时 `TriggerEvent` 的 `as Action<T>` 会返回 null，监听器静默不触发**）；同一事件名 Trigger/Add arity 一致性 | PASS |
| `.workbuddy/tools/check_usings.py` | 缺 `using` 导致 CS0246 | 3 条经人工核对均为误报 |
| `.workbuddy/tools/check_members.py` | 跨程序集成员引用（CS0117/CS1061） | PASS |
| `.workbuddy/tools/check_unity_api.py` | **`UnityType.Member` 静态/枚举访问是否存在**（CS0117/CS1061）。做法：解析 Unity 安装目录里每个托管程序集旁边的官方 API 文档 XML（`UnityEditor.xml`/`UnityEngine.xml`/`UnityEngine/*.xml`，共 86 份、2832 个类型、52830 条成员签名），逐条比对 | PASS |
| 对 Unity 2022.3.62f3 的托管程序集做名字存在性比对 | 调用了不存在的 Unity API | 全部存在（`UnityEngine.UI.dll` 取自 `Library/ScriptAssemblies`） |
| 直接读取 `ProjectSettings/*.asset` | 序列化字段名写错（`m_TransparencySortMode` / `m_TransparencySortAxis` / `m_AutoSimulation` / `tags`） | 全部存在 |

> **关于 `check_unity_api.py` 的用法坑**
> ① Unity 的 XML 文档**只覆盖 Unity 自己的 API，不含 BCL**（`System.IO.File` 之类），
>    因此纯 BCL 类型要单独放行；
> ② XML **不含继承信息**，所以判定分两级：先查该类型自身名单，再查"该成员名是否存在于任何
>    Unity 类型上"（视为继承成员）；
> ③ XML **未收录全部公开 API**，少数成员（如 `Resources.GetBuiltinResource`、
>    `GameObject.FindGameObjectWithTag`）需要显式放行，且须用"直接对程序集做
>    字符串确证"的方式确认存在，不能凭感觉放行；
> ④ 形如 `Grid.QueryCircle` 的 `Grid` 可能是**我方属性名**而非 `UnityEngine.Grid` 类型，
>    必须用"本文件声明的成员名"集合排除，否则误报很多。

**限制（需要用户在编辑器里确认）**：以上手段能覆盖结构、命名、引用、API 存在性、成员名与常量字段名，
但**覆盖不到类型推导、重载选择、参数类型/个数**这一层。所以合入后仍应在 Unity 里触发一次编译，
若还有 `error CS`，请把 Console 的完整错误列表贴出来。


## Z.3 M0 交付物清单

**运行时（`Assets/Scripts/`，31 个文件）**

| 模块 | 文件 |
|---|---|
| 资源 | `Core/Res/`：`ResTable`(唯一寻址源) / `ResBundle` / `ResAddress` / `ResPathUtil` / `IResLoader` / `ResLoader` / `EditorResLoader` / `BundleResLoader` / `ResLoaderRunner(+Behaviour)` |
| 战斗 | `Core/Combat/CombatSystem.cs` / `Core/Combat/EnemyGrid.cs` |
| 实体 | `Enemy/BaseEnemy.cs` / `Enemy/EnemyManager.cs` / `Tower/BaseTower.cs` / `Tower/NormalTower.cs` / `Tower/TowerPlacement.cs` / `Bullet/BaseBullet.cs`(含 `BulletManager`) |
| 棋盘与流程 | `Game/Board.cs`(几何/数据) / `Game/BoardView.cs` / `Game/CellView.cs` / `Game/GameFlowManager.cs` / `Game/PathArrowView.cs` / `Round/WaveManager.cs` |
| 数据 | `Data/Configs.cs` + `EnemyConfig`/`TowerConfig`/`BulletConfig`/`GlobalConfig`/`LevelConfig`/`WaveConfig` |
| 基础设施 | `Core/ObjectPool.cs` / `Core/Event/*` / `Core/Manager/*` / `Core/UI/UIManager.cs` / `UI/HudView.cs` / `UI/TipsView.cs` / `Camera/CameraController.cs` / `Launcher.cs` / `GameSceneLauncher.cs` / `AStarWrapper/*` |

**数据（生成脚本，`.workbuddy/tools/`）**
`gen_monster_catalog.py` → `Assets/Scripts/Data/MonsterCatalog.cs`（119 个怪物的清单，生成代码）
`gen_wave_data.py` → 重写 `EnemyData`（128 行）/ `EnemyList`（15 个波次编组）/ `RoundData`（12 个回合）

**编辑器工具（`Assets/Editor/`，12 个）**
`EditorUtil` / `PlaceholderArtGenerator` / `TowerPrefabConverter` / `BattlePrefabBuilder` /
`PhysicsComponentCleaner` / `UIPrefabBuilder` / `ProjectSettingsConfigurator` / `SceneMainBuilder` /
`ABNameSetter` / `BuildAssetBundles` / `MonsterPrefabBuilder` / `M0SetupWizard`（含 6 类 20+ 项自检）

全部入口在 **`Tools ▸ 塔防`** 菜单下。**正常流程只需点「一键完成 M0 资源准备」+「0. 自检」两步。**

**文档**
`Docs/Unity_Editor_Operation_Guide.md` —— 面向编辑器的分步操作指南（含 16 项验收清单与故障速查表）

## Z.4 M0 已实现的机制（对照原作核心玩法）

| 原作机制 | M0 状态 |
|---|---|
| 自由布塔、改变敌人行进路线 | ✅ 已实现（建塔 → 路径重算 → **怪物立即改道**） |
| 不能完全堵死敌人路径 | ✅ 已实现（建造前临时设墙跑 A*，不可达则回滚并拒绝） |
| 塔自动索敌并攻击射程内单位 | ✅ 已实现（空间哈希 + 节流索敌 + 目标锁定 + 炮管转向） |
| 无目标不开火 | ✅ 已实现，且有「空放次数」自检计数器保证恒为 0 |
| 怪物沿路径行进、被击杀获得资源 | ✅ 已实现（奖励走 `TBEnemyData.reward`） |
| 漏怪扣玩家生命、生命归零失败 | ✅ 已实现（v1.0 是直接回收不扣血，玩家永不失败） |
| 多回合推进、通关判定 | ✅ 已实现（关卡 1 共 10 回合） |
| 塔升级 / 出售 | ⚠️ 数据与 `TowerManager.Sell()` 已就绪，缺 UI 接线（M2） |
| 多塔型（AOE / 减速 / 激光） | ⚠️ 配置字段已留（`effectType` / `effectValue` / `aoeRadius` / `pierce`），实现排 M2 |
| **119 种怪物 + 递进波次** | ✅ 已实现。`Assets/_UIAssets/Monsters/**` 下 119 个怪物全部转成战斗预制体（去物理 / BaseEnemy / 自适应血条），
  `EnemyData` 128 行（9 个梯度档 + 119 个具体怪）、`EnemyList` 15 个波次编组（6→20 只、2→20 种、间隔 0→35s）、
  `RoundData` 12 个回合（波次数 2→14 递进）；怪物**按家族分包**（`enemy_<家族>`，只加载本关用到的家族） |
| 金币经济闭环 | ✅ 已实现（建塔扣费 / 击杀奖励 / 回合奖励 / 出售返还） |

## Z.5 M0 之后的第一优先级

1. **美术尺寸标定**：跑一次「一键资源准备」，根据脚本打印的实测包围盒宽度，调 `EnemyData.scale`
2. 接入切关时的 AB 整包释放（`ReleaseBundle`），并做一次 `HasLeak()` 自检
3. 塔升级 / 出售 UI（`TowerInfoView` 重做，世界空间版）
4. ~~把剩余 118 个怪物 prefab 批量接入~~ **已完成**（见 `MonsterCatalog` + `gen_wave_data.py`）；
   后续只需在 `EnemyList` 里按关卡需要挑选编组
5. 伤害飘字、击杀特效、音效；结算界面


---

## Z.7　M2 实施记录（2026-09-30）

> 本轮依据 `Docs/Tower_Interaction_Dev_Plan_v2.md` 与 `Docs/Unity_Editor_Operation_Guide.md`，
> 在 Wave 0~7 的分波计划下完成 M2 全部 8 项。以下是**决策与实测事实**，
> 供后续接手者判断"为什么是这样写的"。

### Z.7.1 关键决策（实现时照此办，不再二次决策）

| # | 决策 | 理由 |
|---|---|---|
| D-A | 塔型编号沿用文档：1 单体 / 2 AOE / 3 减速 / 4 穿透 / 5 激光。type=2「Power/强力」的**行为**就是 AOE | 实测 xlsx 里 type=2 的 `effectType=2`，与文档编号天然对齐；改编号会动已上线的 9 行数据与美术命名 |
| D-B | type=4/5 无美术 → `resName` 暂指向 `Tower_Normal` | 行为完全由配置驱动；美术到位后只改 `TowerInfo.xlsx` 一格 + `ResTable` 两行，**零代码** |
| D-C | 激光 = **hitscan**（`effectType=4`），不生成弹体 | 做成"速度极高的子弹"会引入高速穿透漏判；且激光本就该立即结算 |
| D-D | 飞行单位走 **起点→终点直线**，不入 A* 网格 | 文档给的两个选项里对现有 A* 零侵入 |
| D-E | `canAttackAir` 作为 `TowerInfo.xlsx` **新增列** | 文档明确要求；该列**每行都必须填**（空单元格 Luban 给 0 = 不可攻空） |
| D-F | 音效只交付"系统 + 表 + 调用点"，无文件时**静默 no-op** | 工程内 0 个音频文件；符合 §3.5「功能缺失不应阻塞」 |
| D-G | 打击感参数（飘字开关/节流、震动幅度/时长）进 `Global.xlsx` | 该表注释明确"全工程唯一的常数配置表" |
| D-H | 打击感走 **Manager 直调**，不走事件总线 | 每次命中都派发事件在 200 怪下不可接受；且要守住"CombatSystem 是 UpdateEvent 唯一订阅者" |

### Z.7.2 本轮修掉的真实缺陷（都是"能编译、能跑，但结果是错的"）

| # | 缺陷 | 症状 |
|---|---|---|
| 1 | **升级失败会永久丢塔** | `TryUpgrade` 原先"先拆旧塔、后建新塔"，新塔资源加载失败时旧塔已归还对象池 → 玩家花了钱，格子上什么都不剩。改为**先建后拆** |
| 2 | **穿透完全无效** | 原实现在 `_pierce>0` 时把 `_target` 置 null 后 return，而命中判定要求 `_target != null` → 子弹此后再也不命中 |
| 3 | **AOE 每次命中都 GC** | `OnHit` 里 `new List<BaseEnemy>(16)` → 改为实例字段复用 |
| 4 | **`TowerUpgradeSuccess` 契约与注释相反** | 注释写 `(BaseTower, int)`，实际无参触发、无参订阅。已统一为带参（新实例） |
| 5 | **"下一级"两处口径分叉** | UI 用 `type + level+1`、逻辑用 `upgradeTo`。已收敛到 `Configs.GetNextLevel` |
| 6 | **选中高亮清不掉** | `Select()` 先 `ClearSelectionHighlight()` 再赋 `_selected`，清理方法读到的永远是"新塔" |
| 7 | **`CellView` 选中色缺失** | `CellHighlight` 只有 None/Buildable/Blocked |
| 8 | **升级会搅乱 HUD** | `TryUpgrade` 复用 `BuildTowerSuccess` → HudView 误以为"新建了一座塔"而退出放置态 |
| 9 | **生成器会把手工按钮冲掉** | `UIPrefabBuilder.BuildInternal` 无条件 DeleteAsset；新增 `EnsureMissing` 只补缺失，向导改调它 |
| 10 | **激光塔被严格压制** | 性价比 0.700 vs 穿透 2.500，没有任何理由建它。调 power 后 1.200 |
| 11 | **所有塔的 L1→L2 升级都是坏选择** | 边际性价比 0.889/0.812/0.167/0.948/0.200，全部低于各自 L1。重排 power 后回到 0.59~1.60 |

### Z.7.3 本机环境的关键突破（对后续工作价值很高）

**本机**没有可用的 C# 编译器、Unity 也无法在沙箱里启动 —— 但本轮找到了三条替代路径：

1. **真实编译验证**：Unity 已经生成了 `Assembly-CSharp-Editor.csproj`，
   直接调用 Visual Studio 的 MSBuild 即可**真正编译**运行时 + 编辑器三个程序集：
   `"C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe" Assembly-CSharp-Editor.csproj /t:Build /p:Configuration=Debug`
   → 这比"括号配平 + 符号核对"强得多，本轮靠它当场抓出 3 个 CS 错误（枚举名被同名属性遮蔽、字段被误删等）。
   **注意**：新增 `.cs` 文件后 Unity 才会把它写进 csproj；未重新生成 csproj 前，
   需手工往 csproj 里补一行 `<Compile Include="..." />` 才能参与编译。
2. **Luban 可脱离 Unity 单独跑**：`Luban.ClientServer.exe` 是自包含 .NET 程序，
   设 `DOTNET_ROLL_FORWARD=LatestMajor` 后可直接命令行导出，
   于是"改 xlsx → 导出 → 编译 → 校验"整条链路都能在无人值守下完成。
3. **配置表脚本化**：见 `.workbuddy/tools/apply_m2_*.py` —— 表结构变更一律走脚本 + 自动备份，
   不再手改 Excel（手改最容易出"改漏一行/列错位"）。

### Z.7.4 M2 的遗留（不阻塞交付，明确交给后续）

| 项 | 说明 |
|---|---|
| 穿透/激光塔的美术 | 暂复用普通塔外观。换皮 = 改 `TowerInfo.xlsx` 的 `resName` 一格 + `ResTable` 两行 |
| 音效文件 | 0 个。丢进 `Assets/Audio/` + 跑 `gen_audio_catalog.py` 即自动生效，**无需改代码** |
| 面板正式美术 | `TowerInfoView` 目前是程序生成的纯色占位 |
| 后期难度曲线 | 顶演显示第 6~8 回合余量充裕（8~9 倍）；建造位用尽后回落。整体经济调优属 M3 |
| 飞行单位的表现 | 目前是"贴地直线飞行"，没有高度/影子等表现层 |


---

## Z.8　M3 / M4 / M5 实施记录（2026-10-02）

> 本轮完成 M3 全部 6 项，以及 M4、M5 中所有**不依赖美术资源、真机设备与 Unity 编辑器交互**的部分。
> 下面记录决策、实测事实，以及**明确没有做、为什么没做**的部分 —— 后者同样重要。

### Z.8.1 关键决策

| # | 决策 | 理由 |
|---|---|---|
| E-A | **重排全部 40 波**，而不是只补 13~40 | 实测两代波次数据强度互相穿插（波 10 = 53586，波 13 = 3281，波 21 = 8326）。根因是 M1 的 1~12 波为"**累积引用**的回合"设计（回合 r 重放 1..r 波），单看每一波就已经很大；新波次是"一波一回合"。两套口径混在一起，关卡怎么切都是非单调 |
| E-B | 难度曲线改为**目标血量法**：先定几何递增的目标有效血量，再按目标"填"敌人 | 让曲线是**构造出来**的，而不是"填完再看运气"。出怪数也因此自然随强度变化（强怪少、弱怪多） |
| E-C | **每关独立经济**，initialGold 随关卡增长（100→2400） | 每关从头攒钱且不跨关继承。金币若还是 100 出头，玩家在第 5 关之后连 4 座塔都买不起 —— 实测正是这一点让 3~8 关**数学上无解** |
| E-D | 关卡 1 由 10 回合改为 **12 回合**（原 1~12 全部用上） | 回合 11/12 原本无任何关卡引用（孤儿），而 M2 给波次 11/12 加的 Boss 会因此永远打不到 |
| E-E | 存档只用 `persistentDataPath` + `JsonUtility` | 设计文档硬约束：`SaveManager` 不得引用 UnityEditor。本项目历史上就踩过 `JsonDataManager` 顶层 `using UnityEditor` 导致打包必炸的坑 |
| E-F | 快照粒度 = **回合边界** | 只有此刻状态自洽（场上无残留怪物、金币与塔已结算）。半途存盘要额外记录每只怪的位置/血量/波次进度，复杂度与收益不成比例 |
| E-G | 暂停热键用 **P**，不用 ESC | ESC 已被 `TowerPlacement` 用作取消放置/取消选中，同帧抢同一个键会"按一下既取消选中又暂停" |
| E-H | 安全区适配**运行时自动补挂**，不要求重建场景 | `UICanvas` 是按 Tag 在运行时找到的；在那里补挂 `SafeAreaFitter` 不需要改场景，老场景立刻生效 |
| E-I | UI 淡入**跳过自带 CanvasGroup 的界面** | `TipsView` 用 CanvasGroup 自己管淡入淡出，UIManager 再插一脚会两边抢 alpha（表现为提示一闪一闪） |
| E-J | **不做** `git filter-repo` 仓库瘦身 | 破坏性：重写全部 commit hash + 要求所有人重新克隆。文档明确规定须用户确认 |

### Z.8.2 本轮修掉/发现的问题

| # | 问题 | 症状与处置 |
|---|---|---|
| 1 | **3~8 关数学上无解** | balance_sim 报出余量 0.81→0.09。根因：敌人按几何曲线加难，初始金币却留在 100 出头。→ 金币随关卡增长 |
| 2 | **M8 地图 S→E 不可达** | 我第一版把相邻障碍行的缺口列错开（一行留 4/7/10/13、下一行留 0/3/6/9…），上下就断了。地图生成脚本的 BFS 自检当场拦下，未写文件 |
| 3 | **M8 可建造位被路径长度吃掉** | "起终点同排"把路径压到 15 格，半径内可覆盖路径的格子从 74 掉到 44 —— 塔数上限砍掉四成，余量 0.09。→ 改回全长路径，难度交给障碍密度与敌人强度 |
| 4 | **C# 字符串里的 \n 变成了真换行** | 我在生成代码时把 TS 模板串的 `\n` 直接写进了 C# 字符串字面量，编译报 CS1010「常量中有换行符」。MSBuild 当场指出行号，比肉眼找快得多 |
| 5 | **GameFlowManager 出现两个 Update** | 新增暂停热键时没注意到已有 Update，CS0111。→ 合并进原有 Update |
| 6 | **SelectView 结构被替换破坏** | 修上一个问题时替换块少了一个 `{`，导致后续方法全部"顶级语句"。编译错误直接指到行，修复后独立复核了按钮结构 |

### Z.8.3 环境方法的补充（接 §Z.7.3）

- **MSBuild 真编译**这一轮又抓出 3 个错误（CS1010 / CS0111 / CS1031），全部是"肉眼很难发现、但编译必炸"的类型。
  **新增 .cs 文件后必须手工往 `.csproj` 补一行 `<Compile Include="..." />`** —— csproj 是 Unity 生成的，
  在 Unity 刷新之前不会包含新文件（csproj 已被 `.gitignore` 忽略，随便改）。
- **配置表变更一律走脚本 + 自动备份**（`.workbuddy/tools/gen_m3_*.py`）：
  这一轮又踩到"列号写死"（把 `EnemyIndexs` 当成 `interval`，拿一串敌人 id 去转 float）。
  脚本一律按**列名**定位，不按列号。
- **棋盘/波次这类数据必须有自检**：地图用 BFS 验连通性，难度用 balance_sim 验单调性。
  这一轮两个真问题（M8 不可达、3~8 关无解）都是自检发现的，不是靠看。

### Z.8.4 M3 / M4 / M5 的交付边界（重要）

**已交付（代码 + 数据 + 工具）**
- M3 全部 6 项；
- M4：安全区适配、多分辨率（CanvasScaler Match 0.5，沿用）、横屏锁定、相机平移/缩放/边缘拖拽/边界夹取、开火后坐、UI 淡入、背景视差；
- M5：对象池核查（确认早已统一）、HybridCLR 取舍并移除、性能探针（F3）、回归用例清单。

**未交付 —— 以及为什么**

| 项 | 卡在哪 |
|---|---|
| M4 美术统一、怪物帧动画、粒子特效 | **需要美术资源**。代码侧接口/占位已就位，资源到位后按既有"换皮零代码"口径接入 |
| M5 AB 优化（拆包/压缩/去重） | 需要 Unity 实际打包 + 真机包体数据。没有真实包体，"优化"就是盲调 |
| M5 UGUI 优化（SpriteAtlas / 合批） | SpriteAtlas 是 Unity 资产；合批效果必须在真机 Frame Debugger 里看 |
| M5 性能压测 | **度量工具已交付**（PerfProbe）。但"低端机 200 怪 60fps"必须真机跑，我这里没有设备 |
| M5 打包 PC / Android | 需要 Unity 构建 + 签名，且 Unity 正在用户手里开着 |
| M5 仓库瘦身 | `git filter-repo` 破坏性，文档规定须用户确认 |

> 这六项**不是"没来得及做"，而是"在不越权/不假装的前提下做不到"**。
> 把它们标成完成才是真正的问题。

---

## Z.9　减速塔改为范围光环（2026-10-07）

### Z.9.1 需求与动机

原实现：减速塔发射一颗减速弹，命中**单个**敌人后施加 2s 减速。
问题：单体减速在怪群压力下几乎无价值 —— 一次只能影响一只，且子弹飞行期间目标可能已死。
改为：**不发射子弹，持续把射程内的所有敌人减速**（典型的"冰霜塔/光环塔"模型）。

### Z.9.2 关键决策

| # | 决策 | 理由 |
|---|---|---|
| F-A | 判定用 `TowerType.Slow(=3)`，**不用** `effectType` | 塔表里仍保留 `effectType=1` 仅为 UI 分类与图例口径一致；光环塔的差异是**塔型级**的（有无索敌/开火/转向），不是命中效果。混用会让"给了减速弹的普通塔"也变成光环 |
| F-B | `TickAttack` 里开一条**独立支路**，不塞进单目标流程 | 光环与"锁单目标→转向→开火"是两套语义，硬塞 if 会让两条流程互相污染 |
| F-C | 按**冷却间隔**（CD）施加，时长 = `CD + 0.3s` | 若每帧刷 `ApplySlow`，怪的减速时长会被顶满，**离开光环后多久恢复取决于帧率**。按 CD 结算 + 固定余量，恢复时间是确定的 |
| F-D | 不过滤 `canAttackAir`、不用 `targetMode` | 光环没有"选谁"的概念，射程内一律减速（飞行单位也吃减速）。`targetMode` 对光环无意义 |
| F-E | `bulletId` 由 4 改为 **0** | 语义正确（不发射），且 `Configs` 的交叉引用自检会跳过 bulletId≤0 —— 少一条"引用了不该引用的子弹"的隐性依赖 |
| F-F | 表现复用 `Range_Ring.png`，**不新增贴图** | 与 `LaserBeamView` 同一考量：新增贴图必须先在 Unity 里跑占位美术生成器；换色即可表达"光环"。零新增资产 |
| F-G | 光环表现**挂在塔的 transform 下**，不是全局单例 | 同屏可能多座减速塔，各要一个圈；挂塔下可随塔自动销毁与跟随 |
| F-H | 结算（`TickSlowAura`）与表现（`TickVisual`）**分两个节拍** | 结算每 CD 一次，脉冲渐隐必须每帧推进，否则脉冲会"跳"没 |
| F-I | 光环子节点缩放要**除回父级 lossyScale** | 塔根节点有 0.8 缩放，子节点若直接套公式，光环会比实际射程小 20%，与 `Config.RadiusWorld` 的判定对不上 |

### Z.9.3 改动清单

| 文件 | 改动 |
|---|---|
| `Assets/Scripts/Tower/BaseTower.cs` | `TickAttack` 增加光环支路；新增 `TickSlowAura`（结算，遍历空间哈希逐个 `ApplySlow`）与 `TickVisual`（脉冲渐隐）；`Init` 里为减速塔挂/更新光环；`MarkDestroyed` 清引用 |
| `Assets/Scripts/Tower/SlowAuraView.cs` | **新增**。纯表现：常亮射程圈（浅蓝）+ 命中脉冲；挂塔下；缩放除回父级 |
| `Assets/Scripts/Tower/RetardTower.cs` | 类注释更新为新语义 |
| `Assets/Scripts/Data/TowerConfig.cs` | 新增 `IsSlowAura`；`FiresBullet` 排除光环塔 |
| `Assets/Scripts/Core/Combat/CombatSystem.cs` | `TickTowers` 加 `t.TickVisual(dt)` |
| `Assets/Scripts/Core/Enum/EnumFile.cs` | `EffectType` 注释补"减速塔是例外"说明 |
| `Luban/Config/Datas/TowerInfo.xlsx` | id 7/8/9 的 `bulletId` 4→0；表头注释行同步为光环口径 |
| `Assets/ConfigJson/tbtowerinfo.json` | Luban 重导产物（已同步） |

### Z.9.4 未改动的部分与理由

- **减速塔的 `power` 列未清零**：光环塔不造成伤害，该列目前不参与运行。保留原值是为了将来若要做"冰霜伤害"时数据还在，且清零会让"塔的强度"在表面上看不出层级。已在表头注明"减速塔=光环，本列不参与运行"。
- **`TBBulletData` 的 id=4"减速弹"未删**：它仍是合法的子弹定义（将来可能有"命中减速"的普通塔想用它）。删行会牵动 id 稳定性，收益为零。

