# Update 函数集中化改造方案

> 版本：v1.0（2026-10-15）｜状态：待评审
> 范围：将全部第一方 MonoBehaviour 的 `Update` / `LateUpdate` 收起，改由统一的 `UpdateManager` 集中调度；
> 本文档只做分析与方案，不含任何已落地的代码改动。

---

## 0. 结论摘要（TL;DR）

| 维度 | 结论 |
|---|---|
| 技术可行性 | ✅ 可行，无阻断性障碍。全部 21 处回调（19 个文件）已在热更程序集内，几乎所有宿主组件都已有可用的 OnEnable/OnDisable 生命周期 |
| 性能收益 | ⚠️ **当前规模下可忽略**（估计 < 0.05 ms/帧，占 60fps 帧预算 < 0.3%）。不要以"提帧率"为动机做这次改造 |
| 真正收益 | 调度顺序**确定化**、生命周期**可控**（可暂停/跳过/度量）、与既有 `CombatSystem` 集中调度模式**收敛统一** |
| 主要风险 | ①"忘注册"导致静默失效（本项目最忌讳的故障模式）；②顺序语义变化引发的交互回归（HUD 手势 / 选关吸附 / 切关遮罩）；③异常隔离需自建（Unity 原生 Update 逐回调异常隔离，集中循环会一键全断） |
| 建议 | 若为架构统一：**做，但按 6 阶段分步落地**，每阶段独立提交可回退；若纯为性能：**不做或只做低成本子集**（见 §2.4、§9 备选方案） |

---

## 1. 现状扫描（全量清单）

### 1.1 扫描口径

- 全量扫描 `Assets/**` 的 `.cs`（含 AOT 程序集、Editor 目录、Gen 生成代码）。
- 正则匹配 `void Update()` / `void LateUpdate()` / `void FixedUpdate()` 声明。
- AOT 侧（`Assets/AOTAssembly/`）**零命中**——启动链（BootLoader/BootServerSelection）不参与帧循环，无改造面。

### 1.2 第一方回调总览

**21 处回调，分布在 19 个文件**：17 个 `Update` + 4 个 `LateUpdate`（其中 GameFlowManager / CameraController 各兼有两相）。

| # | 文件（相对路径） | 类 | 方法（当前行号） | 职责 | 改造动作 |
|---|---|---|---|---|---|
| 1 | `Assets/Scripts/Launcher.cs` | Launcher | Update (354) | 驱动 TimerManager + 广播 UpdateEvent | **保留为全工程唯一 Update（调度入口）**，改调 UpdateManager；新增 LateUpdate 调 LateTick |
| 2 | `Assets/Scripts/Game/GameFlowManager.cs` | GameFlowManager | Update (1221) | GameClock.Tick + P 暂停热键 + F1/F2/F3 调试键 | Update→OnUpdate；**GameClock.Tick 上移至管理器** |
| 3 | 同上 | 同上 | LateUpdate (525) | 自动回合倒计时 + 波次推进 + 回合完成判定（**须晚于战斗 tick**） | LateUpdate→OnLateUpdate（Late 桶） |
| 4 | `Assets/Scripts/Camera/CameraController.cs` | CameraController | Update (162) | 滚轮缩放 + 中键/键盘/边缘平移 | Update→OnUpdate |
| 5 | 同上 | 同上 | LateUpdate (96) | 屏幕震动偏移，**必须最后施加**（不被 FitBoard/缩放覆盖） | LateUpdate→OnLateUpdate（Late 桶） |
| 6 | `Assets/Scripts/Tower/TowerPlacement.cs` | TowerPlacement | Update (477) | 放置态 ghost 跟随/悬停校验；非放置态右键/ESC 取消、选中点击 | Update→OnUpdate |
| 7 | `Assets/Scripts/UI/HudView.cs` | HudView | Update (358) | 塔按钮长按/位移判定（拖拽建造触发）+ 吞 click 窗口（1 帧） | Update→OnUpdate |
| 8 | `Assets/Scripts/UI/FloatingTextManager.cs` | FloatingTextManager | Update (231) | 伤害飘字池推进（GameClock.DeltaTime，0 GC） | Update→OnUpdate |
| 9 | `Assets/Scripts/UI/HotUpdateView.cs` | HotUpdateView | Update (349) | 进度条 SmoothDamp + 不确定态滑动 | Update→OnUpdate |
| 10 | `Assets/Scripts/UI/LoadingView.cs` | LoadingView | Update (114) | 进度条 SmoothDamp + 提示轮播（unscaled） | Update→OnUpdate |
| 11 | `Assets/Scripts/UI/LevelLoadingMask.cs` | LevelLoadingMask | Update (159) | 切关遮罩淡入淡出；淡出完自动 SetActive(false) | Update→OnUpdate |
| 12 | `Assets/Scripts/UI/TipsView.cs` | TipsView | Update (86) | 提示队列出队 + 淡入淡出（scaled dt） | Update→OnUpdate |
| 13 | `Assets/Scripts/UI/SplashView.cs` | SplashView | Update (78) | 开屏动画时间轴，结束派 SplashFinishedEvent | Update→OnUpdate |
| 14 | `Assets/Scripts/Core/UI/SafeAreaFitter.cs` | SafeAreaFitter | Update (36) | 每帧比较 safeArea 变化，变了才 Apply（防 Canvas 重建） | Update→OnUpdate |
| 15 | `Assets/Scripts/Core/UI/UiClickSfx.cs` | UiClickSfx | Update (58) | 每 0.4s 重扫界面按钮挂点击音 | Update→OnUpdate |
| 16 | `Assets/Scripts/Game/BackgroundParallax.cs` | BackgroundParallax | Update (56) | 背景视差跟随相机 | Update→OnUpdate |
| 17 | `Assets/Scripts/Core/Manager/PerfProbe.cs` | PerfProbe | Update (69) | 帧时间采样（unscaled，环形缓冲 0 GC） | Update→OnUpdate |
| 18 | `Assets/Scripts/Core/Manager/AudioFadeDriver.cs` | AudioFadeDriver | Update (103) | BGM 交叉淡化系数推进（unscaled） | Update→OnUpdate |
| 19 | `Assets/Scripts/UI/SelectView.cs` | SelectView | LateUpdate (132) | 列表首帧初始化 + 定位 + 吸附/箭头状态（**依赖 Canvas 排版时序**） | LateUpdate→OnLateUpdate（Late 桶） |
| 20 | `Assets/Scripts/UI/TowerCodexView.cs` | TowerCodexView | LateUpdate (139) | 图鉴列表首帧定位 + 卡片缩放/淡化（**依赖 Canvas 排版时序**） | LateUpdate→OnLateUpdate（Late 桶） |
| 21 | `Assets/TestNull.cs` | TestNull | Update (14) | Unity 模板空文件，无逻辑 | **删除**（属兜底集 Assembly-CSharp，见 §7.5） |

### 1.3 已经"集中化"的存量（重要背景）

本工程**并非从零开始**——集中调度模式已有一条成熟先例，本次改造是把它推广到剩余组件：

| 存量机制 | 现状 | 与本次改造的关系 |
|---|---|---|
| `CombatSystem` | 全局**唯一**的 `UpdateEvent` 订阅者；每帧由 `Launcher.Update` 触发事件 → `OnUpdate()` → 固定顺序 Tick 怪→塔→弹（v1.0 曾是每个实体各自订阅，已收敛） | **模板与先例**。终局可并入 UpdateManager（§3.6 阶段 5） |
| `TimerManager` | 纯 C#，由 `Launcher.Update` 直接驱动 `Update(dt)` | 不动；与 UpdateManager 并列于 Launcher.Update |
| `GameClock` | 惰性帧缓存（谁先取谁算，顺序不敏感） | Tick 上移至 UpdateManager 头部，语义不变 |
| `UIFader` | 协程驱动淡入（非 Update） | 不在本次范围（可选后续统一） |
| 战斗实体 `BaseEnemy/BaseTower/BaseBullet` | **无各自 Update**，由 CombatSystem 统一 Tick | 已完成，无需再动 |
| DOTween | 自带 `DOTweenComponent` 更新循环 | 不动 |

### 1.4 明确不动的第三方（纪律线）

| 文件 | 机制 | 为什么不动 |
|---|---|---|
| `Assets/Plugins/iTween/iTween.cs` | Update+FixedUpdate+LateUpdate | 插件内部迭代语义（tween 逐帧求值）；改它= 升级维护灾难 |
| `Assets/Reporter/Reporter.cs` | Update | 调试控制台，仅开发期存在；保持原版可整体升级 |
| `Assets/SuperScrollView/Scripts/LoopListView2.cs` | Update | 列表插件自带更新；我们的 View 只通过其公开 API 交互 |
| `Assets/Reporter/Editor/ReporterEditor.cs` | static Update（编辑器） | 编辑器专属，不进包体 |

> 纪律：**第一方全量收敛，第三方一律不碰**。第三方 Update 的存在不破坏"单一入口"的目标——目标口径是"第一方业务代码只留一个 MonoBehaviour Update"。

---

## 2. 性能分析（本改造的核心问题）

### 2.1 Unity 原生 Update 的成本模型

IL2CPP 下，每个启用中的含 Update 的 MonoBehaviour 会在原生玩家循环中被**逐个调用**，成本构成：

1. **原生→托管调用点**（每次回调一次）：C++ 侧经缓存的方法指针进入托管世界，含少量状态检查与栈切换。单次量级约 **0.1–1 µs**（设备差异大，低端机取上限）。
2. **回调体本身**：本例多为轻量 UI 逻辑（SmoothDamp 一个数、比较一个 Rect、写一个浮点），本身纳秒~微秒级。
3. **启用/禁用维护**：SetActive/enabled 切换时原生更新表的增删，摊薄后基本可忽略。

要点：这 0.1–1 µs 是**每次回调**的固定税，与回调体做了什么无关。空 Update 也要交。

### 2.2 本工程的量级测算

- 第一方回调数：**约 20 个/帧**（19 文件，其中 UiClickSfx 随同时打开的界面数可能 ×2~4，其余全是单实例）。
- 加上第三方（Reporter 1 个 + iTween 活动期按 tween 数 + LoopListView2 按打开的列表数），高峰总量约 **25~35 个/帧**。
- 即：原生调用税合计 ≈ 20 × 0.5 µs ≈ **10 µs/帧**（悲观 40 µs）。

对比帧预算：60fps = 16.7 ms。**占 0.06% ~ 0.24%。**

集中化后的净变化：

- 减：约 19 个原生回调税（≈ 3–20 µs）
- 增：1 个管理器 tick + 19 次纯托管接口调用（≈ 1–2 µs，含快照遍历）
- **净收益：约 2~18 µs/帧，即 < 0.02 ms。**

> 结论（量化）：**Profiler 上基本不可见；既救不了任何低端机，也不值得为它冒回归风险。**
> 本项目的性能敏感区在别处（见 §2.4）。

### 2.3 集中化真正的（非性能）收益

1. **顺序确定化**：现在 `Launcher.Update`（战斗）与 `TowerPlacement.Update`、`HudView.Update`、`CameraController.Update` 的相对顺序**由 Unity 未定义**（工程无自定义 Script Execution Order）。集中后同帧顺序=注册顺序表，可写死可审查。HUD 注释里"Update 先于/后于事件系统都可能"的不确定性、Camera→Parallax 可能的 1 帧滞后，都随之消失。
2. **可控性**：批量暂停/跳过（如未来低电量模式跳过纯表现）、按系统级埋点统计耗时、统一异常隔离与日志。
3. **架构收敛**：与 `CombatSystem` 既有模式对齐，"帧驱动只有一条链路"成为可写进规范的不变量（可扩展为审计项）。
4. **戒除隐式依赖**：今后新增系统必须显式登记顺序，不再赌 Unity 的偶然顺序。

### 2.4 如果目标是性能，这些才值得做（排序）

1. **UI 重建与 TMP**：本工程 UI 面大（HUD/选关/图鉴），Canvas 重建、TMP 重建的优化量级是**毫秒级**，远超调度的微秒级。可查：HUD 数值刷新是否本就事件驱动（已事件化）、文本是否有每帧改 `text` 的漏网。
2. **空闲期停摆**：给"只在特定状态下有活干"的组件 `enabled=false`（Unity 自动不调度，零代码风险）——如关闭中的遮罩、无 tween 的 iTween、暂停时不需要的组件。
3. **战斗热路径**（已有）：CombatSystem 已建快照遍历 + 空间哈希 + 0 GC，继续保持。
4. **本改造**：如上所述，性能价值 ≈ 0，列在最后。

---

## 3. 目标架构设计

### 3.1 新增接口（1 个文件）

`Assets/Scripts/Core/Update/IUpdatable.cs`：

```csharp
namespace FTProject
{
    /// <summary>帧驱动契约（Update 相）。实现方在 OnEnable 注册 / OnDisable 注销。</summary>
    public interface IUpdatable { void OnUpdate(); }

    /// <summary>帧驱动契约（Late 相）。用于必须晚于其他系统推进的逻辑。</summary>
    public interface ILateUpdatable { void OnLateUpdate(); }
}
```

**设计取舍：`OnUpdate()` 不带 `float dt` 参数。**
理由：现有 21 处回调对时间口径**各不相同**（scaled / unscaled / GameClock / 不取时间），传参必然引发"统一用哪个 dt"的语义变更——那才是真正的高危动作。不带参 = 回调体**逐字保留**，时间语义零变化。
（GameClock.Tick 由管理器在 Tick 开头统一调用一次，等价于现状且更早、更确定。）

### 3.2 新增管理器（1 个文件）

`Assets/Scripts/Core/Update/UpdateManager.cs`：

```csharp
/// <summary>集中式帧调度器。纯 C#（BaseManager 风格），由 Launcher 驱动。</summary>
public class UpdateManager : BaseManager<UpdateManager>
{
    public void Register(IUpdatable target, int order);
    public void RegisterLate(ILateUpdatable target, int order);
    public void Unregister(IUpdatable target);        // 双桶移除，幂等
    public void UnregisterLate(ILateUpdatable target);

    public void Tick();       // Launcher.Update 调用：GameClock.Tick() → 遍历 Update 桶
    public void LateTick();   // Launcher.LateUpdate 调用：遍历 Late 桶
}
```

关键实现要求（每一条都对应本项目真实踩过的坑）：

1. **快照遍历**：Tick 内先拷贝到预分配数组再回调（参考 `CombatSystem._tickSnapshot`——那里因为"遍历中列表被改"真实崩过）。
2. **延迟增删**：tick 进行中的 Register/Unregister 进 pending 队列，tick 结束统一结算。
   - 注册发生在 tick 中 → **下一帧生效**（与 Unity"中途实例化的组件当帧不跑 Update"行为一致）；
   - 注销发生在 tick 中 → 标记移除，若尚未轮到其回调则**跳过**（与 Unity"本帧销毁后不再回调"一致）。
3. **Unity-null 判定**：接口引用不触发 UnityEngine.Object 的 `==` 重载，必须 `(obj as UnityEngine.Object) == null` 判定销毁，否则场景卸载后遍历会踩已销毁对象。
4. **重复注册**：warning 并忽略（对齐 CombatSystem 的 `_inited` 幂等保护的思路），不静默。
5. **异常隔离（必做）**：每个 `OnUpdate()` 单独 try/catch。Unity 原生 Update 对每个回调是**独立异常隔离**（一个组件抛异常不影响其他组件）；集中循环若不包 try/catch，**一个异常会打断整帧所有后续系统**——这是与原生行为最大的隐性差异，必须补上。catch 中 LogError（带组件名）+ 可选的"熔断计数"（同一组件连续报错 N 次自动注销并提示）。
6. **静态复位**：`[RuntimeInitializeOnLoadMethod]` 清空注册表（防止编辑器关掉域重载时的残留状态）。
7. **填充式排序**：按 (order, 注册序号) 稳定排序，保证同 order 内也确定性。

### 3.3 调度顺序表（冻结，集中在 `UpdateOrder` 常量类）

| 桶 | order | 系统 | 依据 |
|---|---|---|---|
| Update | （0）| `GameClock.Tick()` | 管理器头部固定调用，不占注册表 |
| Update | 10 | HudView | 手势判定：帧内最早，保证拖拽触发及时 |
| Update | 20 | CameraController | 相机先动 |
| Update | 30 | TowerPlacement | 依赖相机换算（ScreenToWorld），必须在相机后 |
| Update | 60 | BackgroundParallax | 跟随相机，必须在相机后（消除 1 帧滞后） |
| Update | 100 | （预留）CombatSystem | 战斗统一入口位；阶段 5 前仍走 UpdateEvent |
| Update | 200 | FloatingTextManager | 纯表现，顺序无依赖，取固定值求确定性 |
| Update | 210 | LevelLoadingMask | 同上 |
| Update | 220 | SplashView / 230 LoadingView / 240 HotUpdateView / 250 TipsView | 同上 |
| Update | 300 | SafeAreaFitter / 310 UiClickSfx | 低频检查类 |
| Update | 900 | PerfProbe（采样收尾） / 910 AudioFadeDriver | 统计与音频，无依赖 |
| ~~Late~~ | 10 | CameraController（震动） | **必须最后施加**于 transform |
| Late | 100 | GameFlowManager（波次/回合） | **必须晚于战斗 tick**（读 AliveEnemyCount 最新值） |
| Late | 200 | SelectView / 210 TowerCodexView | 依赖 Canvas 排版（保持 Late 相语义） |

> 注：所有"无依赖"项也给了固定序号——本表的目的不是排序正确，而是**顺序确定且可审查**。

**相（Phase）语义保持**：Update 桶在 `Launcher.Update` 中执行、Late 桶在 `Launcher.LateUpdate` 中执行——与 Unity 原生 Update/LateUpdate 两个相位的相对关系一致。SelectView/TowerCodexView 依赖的"Canvas 在上一帧渲染阶段完成排版、本帧 LateUpdate 可见"的时序**不变**。

### 3.4 生命周期契约（每个组件统一模式）

```csharp
public class Xxx： MonoBehaviour, IUpdatable
{
    private void OnEnable()  { /* 原有逻辑（如有） */ UpdateManager.Instance.Register(this, UpdateOrder.Xxx); }
    private void OnDisable() { /* 原有逻辑（如有） */ UpdateManager.Instance.Unregister(this); }
    public void OnUpdate()   { /* 原 Update 函数体，一字不改 */ }
    // 需要 Late 相的组件改用 ILateUpdatable + RegisterLate/UnregisterLate
}
```

- 注册绑 `OnEnable`/`OnDisable`，**恰好复刻 Unity 语义**：`enabled && activeInHierarchy` 才跑；SetActive(false)/enabled=false/销毁，全部自动注销，无需特判。
- 已占用 OnEnable/OnDisable 的组件（TowerPlacement、UiClickSfx、LoadingView、HotUpdateView、SelectView、TowerCodexView、GameFlowManager）：**合并**，不覆盖原有逻辑。
- 需要**新增** OnEnable/OnDisable 的组件：HudView、SplashView、TipsView、CameraController、BackgroundParallax、PerfProbe、AudioFadeDriver、SafeAreaFitter、FloatingTextManager、LevelLoadingMask（后两者目前无任何生命周期方法）。
- `LevelLoadingMask` 的自停机制（淡出后 `SetActive(false)`）天然触发 OnDisable → 注销，行为与现状一致。

### 3.5 Launcher 的最终形态

```csharp
private void Update()
{
    TimerManager.Instance.Update(Time.deltaTime);
    UpdateManager.Instance.Tick();          // 头部先 GameClock.Tick()，再分桶调度
    EventDispatcher.TriggerEvent(EventName.UpdateEvent);  // 阶段 5 前保留：CombatSystem 仍由此驱动
}

private void LateUpdate()                   // 新增（Launcher 现在没有 LateUpdate）
{
    UpdateManager.Instance.LateTick();
}
```

### 3.6 与既有 `UpdateEvent` 机制的终局（两个选项）

- **选项 A（推荐，分两步）**：阶段 1–4 中 `UpdateEvent` 原样保留（CombatSystem 继续订阅，零风险）；阶段 5 再决定是否迁移。
- **选项 B（终局，可后置）**：CombatSystem 改为 `Register(this, Order.Combat)`，删除 `TriggerEvent(UpdateEvent)` 与订阅。
  收益：机制真正唯一化；成本：需同步修改 **3 处引用了"唯一订阅者"约定的注释**（`CombatSystem.cs`、`Launcher.cs`、`FloatingTextManager.cs`）。

> 无论 A/B，本方案对 19 个改造文件的行为面**完全一致**；B 只是清理存量机制，可单独决策。

---

## 4. 逐文件改动清单（19 文件 = 18 改 + 1 删）

> 全部位于 `FTProject.Runtime`（热更程序集），**无需重出 APK**（不涉及 AOT 侧）。唯一例外见 #19。

| # | 文件 | 具体改动 | 特殊风险/备注 |
|---|---|---|---|
| 1 | `Scripts/Launcher.cs` | Update 改调 `UpdateManager.Tick()`；新增 LateUpdate 调 `LateTick()`；把 UpdateManager 加进 `_managers` 注册表（生命周期随管理器组走） | 保持"唯一 Update"注释并更新措辞 |
| 2 | `Scripts/Game/GameFlowManager.cs` | Update→OnUpdate（只留热键；**GameClock.Tick 删除**，上移管理器）；LateUpdate→OnLateUpdate；已有 OnEnable/OnDisable 合并注册 | 热键必须**不受 timeScale 影响**（保持）；Late 相必须晚于战斗（顺序表保证） |
| 3 | `Scripts/Camera/CameraController.cs` | Update→OnUpdate；LateUpdate→OnLateUpdate；新增 OnEnable/OnDisable | 暂停时 HandleZoom 仍工作（管理器**不做暂停门控**，语义保持） |
| 4 | `Scripts/Tower/TowerPlacement.cs` | Update→OnUpdate；已有 OnEnable/OnDisable 合并注册 | 与 EventSystem/Button 的时序容忍设计不变；须在相机后执行 |
| 5 | `Scripts/UI/HudView.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | `_suppressTowerClick` 一帧窗口跨组件（与 TowerPlacement/EventSystem）——冒烟必测拖拽建造与点按 |
| 6 | `Scripts/UI/FloatingTextManager.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | 懒创建单例；注释里引用了"CombatSystem 唯一订阅者"约定，若走选项 B 需同步 |
| 7 | `Scripts/UI/HotUpdateView.cs` | Update→OnUpdate；已有 OnEnable/OnDisable 合并 | 启动链界面，真机/模拟器验证热更进度 |
| 8 | `Scripts/UI/LoadingView.cs` | Update→OnUpdate；已有 OnEnable/OnDisable 合并 | 同上 |
| 9 | `Scripts/UI/LevelLoadingMask.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | **自停机制照旧**（SetActive(false) → OnDisable → 注销）；tick 中自注销路径必须走延迟移除（鲁棒性测试点） |
| 10 | `Scripts/UI/TipsView.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | 事件绑定仍在 Awake（不动），避免时序变化 |
| 11 | `Scripts/UI/SplashView.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | 开屏结束派事件 → Launcher 同步关界面（**回调中销毁自身**路径，鲁棒性测试点） |
| 12 | `Scripts/Core/UI/SafeAreaFitter.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | 每帧 Rect 比较的开销保留（变更驱动改造不在本方案内） |
| 13 | `Scripts/Core/UI/UiClickSfx.cs` | Update→OnUpdate；已有 OnEnable/OnDisable 合并 | 重扫节流不变；多个界面实例 = 多个注册（管理器必须支持多实例同类） |
| 14 | `Scripts/Game/BackgroundParallax.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | 必须在相机后（消除潜在 1 帧滞后，需实测视觉确认） |
| 15 | `Scripts/Core/Manager/PerfProbe.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | **改造自测的工具本身**：先改造它，才能用它测后续阶段 |
| 16 | `Scripts/Core/Manager/AudioFadeDriver.cs` | Update→OnUpdate；新增 OnEnable/OnDisable | unscaled 语义保持不变 |
| 17 | `Scripts/UI/SelectView.cs` | LateUpdate→OnLateUpdate；OnEnable 合并注册；**新增 OnDisable** | ★ 最敏感的界面：吸附/首帧定位/箭头锁定，真机划卡必测 |
| 18 | `Scripts/UI/TowerCodexView.cs` | LateUpdate→OnLateUpdate；OnEnable 合并注册；**新增 OnDisable** | 卡片缩放/首帧定位，必测 |
| 19 | `Assets/TestNull.cs` | **删除** | 属兜底集 Assembly-CSharp（非 asmdef）。删后须按工程规程 **重跑 生成▸All + 拷贝**（否则 dll 清单与新代码不同步） |

**另需新建 2 个文件**：`Scripts/Core/Update/IUpdatable.cs`、`Scripts/Core/Update/UpdateManager.cs`（+ 可选 `UpdateOrder` 常量类，也可并入 Manager 内嵌静态类）。

**总计**：21 个文件进入变更集（18 改 + 1 删 + 2 新增）。

---

## 5. 实施步骤（6 阶段，每阶段可独立提交/回退）

> 全程适用工程既有规程：改脚本 → 等编译 → 菜单重编热更 dll（生成/All 或 9a）→ 模拟器 `pm clear` → 部署冒烟。
> 所有被改脚本都在热更集，**不需要重出 APK**（TestNull 删除也只需重跑 dll 生成）。

| 阶段 | 内容 | 验证点 | 回退方式 |
|---|---|---|---|
| **0. 基建** | 新建 IUpdatable/UpdateManager/UpdateOrder；Launcher 接入（Tick/LateTick 驱动空管理器）；不改任何组件 | 空跑 1 帧无异常；打印注册数=0；启动链完整 | git revert 单提交 |
| **1. 低风险组** | PerfProbe、AudioFadeDriver、SafeAreaFitter、UiClickSfx（4 个，无交互、无顺序依赖） | F3 报告正常；BGM 淡入淡出正常；安全区正常；点击音正常 | 同上 |
| **2. 交互/相机组** | CameraController（含 Late 震动）、TowerPlacement、HudView、BackgroundParallax（4 个） | **模拟器**：缩放/平移/震屏；点按建塔+拖拽建造+取消+选中；视差无跳动 | 同上 |
| **3. 界面组** | SplashView、LoadingView、HotUpdateView、LevelLoadingMask、TipsView、FloatingTextManager（6 个） | 完整启动链（开屏→加载→热更→进菜单）；切关遮罩；伤害飘字；提示队列 | 同上 |
| **4. 流程/列表组** | GameFlowManager（Update+Late 双相）、SelectView、TowerCodexView（3 个）+ GameClock.Tick 上移 | 选关滑动/吸附/箭头/进关；回合推进与完成判定；暂停恢复（P/F2/F3 热键）；倍速切换 | 同上 |
| **5.（可选）战斗收敛** | CombatSystem 迁入 UpdateManager；删 UpdateEvent 触发/订阅；同步 3 处注释与规范 | 压测：PerfProbe p95 前后对比；怪/塔/弹行为无差异 | revert 该提交即恢复事件路径 |
| **6. 收尾** | 删除 TestNull；新增"注册审计"编辑器菜单（扫场景/预制体实现 IUpdatable 但未注册的组件）；更新记忆文档 | 审计工具在故意漏注册的测试组件上能报出 | — |

**性能对比验收（贯穿）**：每阶段完成后，在模拟器同一关卡、同一规模下跑 F3 两次（改造前基线 vs 改造后），记录 p50/p95；**验收线：不劣化**（差异在噪声内即通过——因为本就不指望提升）。

---

## 6. 风险清单与缓解

| 等级 | 风险 | 说明 | 缓解 |
|---|---|---|---|
| ● 高 | **静默失效** | 漏注册/OnDisable 误注销 → 系统"不干活但无报错"（本项目真实发生过同类："new 管理器 vs Instance"静默故障） | 阶段 6 审计菜单 + Manager 对"注册后从未 tick"可加警告；每阶段冒烟覆盖各系统存在感检查 |
| ● 高 | **顺序语义回归** | HUD 手势↔EventSystem 帧窗口、SelectView 首帧定位、遮罩自停等对时序敏感 | 顺序表冻结（§3.3）；Late 相保持独立；重点项列入冒烟矩阵（§8） |
| ● 高 | **异常隔离缺失** | 集中循环一个异常打断全部后续系统（原生 Update 是逐回调隔离） | 管理器内 per-entry try/catch（P0 必做项） |
| ○ 中 | tick 中增删注册表 | 遮罩自停、开屏回调关界面、飘字等会在回调中触发注销 | 快照 + pending 队列 + 已移除跳过（实现规格已入 §3.2） |
| ○ 中 | Unity-null 陷阱 | 接口引用不触发 Unity 的 == 重载 | 强制 `as UnityEngine.Object` 判定（代码评审检查项） |
| ○ 中 | 时间口径被"顺手统一" | 有人看到 OnUpdate() 不给 dt，误改成统一 dt | 文档 + 代码注释双声明："时间源各守各的，禁止在改造中变更" |
| ○ 中 | 热更工作流不同步 | 改完不重编 dll / 模拟器不清持久化 → 旧 dll"存在即跳过"导致测了个寂寞 | 每阶段按规程：重编 dll → `pm clear` → 部署 |
| ○ 中 | TestNull 删除的兜底集影响 | Assembly-CSharp 是 6 热更 dll 之一 | 删除后重跑 生成▸All + 拷贝；核对 dll 大小变化 |
| ▼ 低 | 编辑器残留状态 | 域重载关闭场景下的静态注册表残留 | RuntimeInitializeOnLoadMethod 复位 |
| ▼ 低 | 第三方误伤 | iTween/Reporter/LoopListView2 | §1.4 纪律线；代码评审确认三文件零 diff |
| ▼ 低 | 性能体感"变坏"的错觉 | 理论收益微秒级，心理预期错误 | §2 数据先行；以 F3/Profiler 实测为准，不以体感争论 |

---

## 7. 注意事项（制度级）

1. **注释与规范的同步**：`CombatSystem.cs` / `Launcher.cs` / `FloatingTextManager.cs` 三处注释明确写着"CombatSystem 是 UpdateEvent 的唯一订阅者（工程约定）"。若走到阶段 5，须同步改写为"UpdateManager 是唯一帧调度器"；若止步于阶段 4，则保留原文。
2. **顺序表的唯一性**：所有 order 常量集中在 `UpdateOrder`，禁止在业务代码里散落魔法数字；新增系统的默认 order 由评审时指定。
3. **第三方纪律**：iTween / Reporter / SuperScrollView / DOTween / UIFader（协程）一律不动；后续若升级这些库，不受本改造影响。
4. **`OnUpdate` 命名纪律**：接口方法叫 `OnUpdate`，但 **Unity 不会魔法调用它**——必须注册才跑。代码评审需把"实现了 IUpdatable 但没注册"当作缺陷。
5. **TestNull 删除规程**：删除 `Assets/TestNull.cs` 后必须重跑 生成▸All + 拷贝（兜底集成员变化）。
6. **保留 UpdateEvent 兼容期**：阶段 5 之前，`EventName.UpdateEvent` 的触发与订阅原样保留，避免与 CombatSystem 双跑（**绝不能同时订阅+v 注册**——会导致每帧双 tick，这类症状本项目已见过：OnInit 重复调用致怪物速度翻倍）。
7. **不引入编译期双通道**（如 `#if FT_CENTRAL_UPDATE`）：双路径 = 测试面翻倍，且违背"消灭静默分支"的项目价值观（参见 FT_HOTUPDATE 宏之痛的教训）。回退靠 git revert + 分阶段提交。
8. **文档路径规范**：本文档及衍生物不写盘符（工程文档约定）。

---

## 8. 验收清单（真机/模拟器冒烟矩阵）

| # | 场景 | 覆盖组件 | 通过标准 |
|---|---|---|---|
| 1 | 冷启动全链：开屏→加载→热更（故意断网点重试一次）→主菜单 | SplashView/LoadingView/HotUpdateView | 各界面动效/进度正常；无卡死 |
| 2 | 选关：左右滑动、点箭头、点卡片进关 | SelectView | 吸附到位、箭头锁定、进关正确、**首帧不为空/不卡第1张** |
| 3 | 图鉴：打开、滑动、（若有）点选 | TowerCodexView | 卡片缩放/淡化、首帧定位正确 |
| 4 | 进关：HUD 打开、建塔（点按 + 长按拖拽 + 拖回取消 + 拖到不可建格）+ 选中 + 升级/出售 | HudView/TowerPlacement/TipsView | 四类手势全对；无"点了没反应"；tips 正常 |
| 5 | 战斗：开回合、倍速×2/×3、暂停/恢复（P 键）、F1/F2/F3 | GameFlowManager/CombatSystem/PerfProbe | 回合正常推进与结算；热键暂停中有效；报告可出 |
| 6 | 切关/重开：主菜单→进关→退关→再进 | LevelLoadingMask/GameFlowManager/UIManager 链路 | 遮罩淡入淡出；无旧关残留；HUD 正常重开 |
| 7 | 暂停中：点击音、F3、暂停界面淡入 | UiClickSfx/PerfProbe | unscaled 链路在 timeScale=0 下全部正常 |
| 8 | 刘海/分辨率：改模拟器分辨率/横竖切换 | SafeAreaFitter | 安全区即时生效 |
| 9 | Reporter 回归：画圈/双击调出调试面板 | Reporter（未改） | 面板正常（确认未误伤） |
| 10 | 性能：同关卡压测 F3 ×2（前/后） | PerfProbe | p95 不劣化（噪声内） |

---

## 9. 备选方案（若决策为"暂不全量改造"）

**低成本子集（半天内完成，零架构风险）**：

1. `TestNull.cs` 删除（清垃圾）。
2. `SafeAreaFitter` 改为事件/低频（如每 30 帧检查一次）或仅分辨率变化事件触发——省掉其每帧 Rect 比较。
3. `UiClickSfx` 重扫间隔从 0.4s 放宽，或改为"界面 OnEnable + 按钮创建点"驱动。
4. 给空闲期的重组件（遮罩、关闭的列表）补 `enabled=false` 停摆（Unity 原生零风险）。

**维持现状的理由（同样成立）**：战斗热路径已集中（真正的性能大头已解决）；其余 20 个回调的调度税在 10 µs/帧量级，收益不可测量；集中化引入的是**架构清晰度**，而非性能。

**最终建议**：以"架构统一与顺序确定"为立项理由推进 §5 的 6 阶段方案；在此过程中把 §2.4 的性能项作为平行任务处理——那才是帧率真正的朋友。

---

## 附录 A：建议代码骨架（供评审）

```csharp
// UpdateManager 核心循环（示意，非最终代码）
public void Tick()
{
    GameClock.Tick();                    // 全工程时间源，集中在此提前算好

    _snapshot.Clear();
    _snapshot.AddRange(_entries);
    for (int i = 0; i < _snapshot.Count; i++)
    {
        Entry e = _snapshot[i];
        if (e.Removed || e.Target == null) { continue; }        // Removed=已标记移除
        if ((e.Target as UnityEngine.Object) == null) { continue; } // Unity-null（已销毁）
        try
        {
            e.Target.OnUpdate();
        }
        catch (System.Exception ex)
        {
            Debug.LogError(string.Format("[Update] {0}.OnUpdate 抛出异常：{1}",
                e.Target.GetType().Name, ex));                  // 不回抛：保持逐回调隔离
        }
    }
    ApplyPending();                      // tick 中发生的注册/注销在此结算
}
```

## 附录 B：复核用扫描命令（可随时重跑）

```bash
# 全量确认第一方 Update 面（应只剩 Launcher 一处）
grep -rn "void Update\|void LateUpdate\|void FixedUpdate" Assets/Scripts Assets/AOTAssembly Assets/Gen

# 第三方基线（应始终保持 4 处不变）
grep -rn "void Update\|void LateUpdate\|void FixedUpdate" Assets/Plugins Assets/Reporter Assets/SuperScrollView
```

---

*本文档由项目全量代码扫描（2026-10-15）得出；所有行号基于当时工作区状态。*
