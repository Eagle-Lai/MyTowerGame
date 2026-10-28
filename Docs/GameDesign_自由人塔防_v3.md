# 《自由人塔防》策划案（v3.0）

> 本文保留玩法、交互与界面设计。运行时及存档契约见 [`LevelRating_Runtime_And_Save.md`](LevelRating_Runtime_And_Save.md)。

> 项目：单机 2D 塔防手游（对标 Fieldrunners 核心机制）　|　平台：Android  
> 工程：本工程（Unity 2022.3.62f3c1）　|　主场景：`Assets/Scenes/Main.unity`  
> 配套文档：`Docs/ProgramDesign_自由人塔防_v3.md`（程序案）  
> 版本说明：本文以历史工程实现为基线；实际行为以当前代码与配置表为准。

---

## 1. 核心玩法循环

### 1.1 总循环（局外 → 局内 → 局外）

```
选关（SelectView，含星级/解锁/继续快照）
  → 关卡加载（Loading：资源 → 配置 → 建棋盘 → 相机取景）
  → 备战（Preparing：初始金币布塔，自由摆放塑造路径）
  → 回合战（RoundRunning：出怪 → 塔索敌开火 → 击杀得金/漏怪扣血）
  → 回合结算（RoundComplete：回合奖励 → 升级/出售/补塔 → 自动/手动开下一回合）
  → 配置的全部回合完成 → 结算（GameOver：评级 → 写存档 → 解锁下一关）
  → 返回选关 / 重打 / 下一关
```

### 1.2 灵魂机制（不可妥协的三条规则）

| # | 机制           | 规则                                                                                           |
| - | ------------ | -------------------------------------------------------------------------------------------- |
| 1 | **自由布塔塑造路径** | 棋盘全开阔格（除障碍格/出生点 S/终点 E），玩家在任意空地建塔，怪物走 A* 最短路径；**建塔即重算路径，场上怪物立即改道**                           |
| 2 | **禁止完全堵路**   | 建造前临时把目标格设为墙并跑 A* 校验，若 S→E 不可达则**回滚建造**（格子变红 + Tips 提示），不扣费                                  |
| 3 | **去物理战斗**    | 不用 Collider/Rigidbody/OnTriggerEnter；索敌用空间哈希网格，命中用距离判定，全战斗由 CombatSystem 集中 tick（怪→塔→子弹固定顺序） |

### 1.3 单回合闭环（M0 验证过的最小循环）

```
点「开始」→ WaveManager 展开 (时刻,怪id) 时间轴 → 按 enemyInterval 逐只出怪
→ 怪沿 PathArrow 路径移动 → 塔节流索敌（searchIntervalMs=100ms）→ 开火/子弹命中
→ 怪死：+金币、播死亡动画、600ms 后回收对象池
→ 怪到终点：-生命、播漏怪反馈
→ 时间轴清空且场上无怪 → 回合奖励 → 回合结束
```



---

## 6. UI 规范（清单 / 逐界面规格 / 跳转流程 / 世界层）

> 效果图目录：`Docs/ui_mockups/`（**14 张 SVG 正式版·深色科幻风**，1920×1080 高保真，几何与 prefab 实测数值一致）。
> 若文档查看器不显示图片，请直接打开对应 SVG 文件。
> **深色科幻视觉令牌**（正式版效果图统一规范）：底色 `#0B0E14` / 战场 `#10141D`；面板 `#2A3444→#1B2330→#222C3B` 渐变 + 45° 切角（大件 16px / 按钮 10~12px）+ 描边 `#3A4A63`；功能色——主青 `#35E0FF`（主按钮/路径/射程/传送门）、金 `#FFC94D`（货币/星级/普通伤害飘字）、红 `#FF4D5E`（危险/致命/敌方瞳光/失败主题）、绿 `#3DFFA8`（可建格/满血条）、橙火 `#FF7A29`（Power 火焰）、冰 `#7DE8FF`（Retard 控场）、紫 `#7C5CFF`/`#B18CFF`（备用点缀色，原 Pierce/Laser 标识已随三塔型收敛退役）；发光=DropShadow 霓虹 + Bloom 模糊叠加，世界层加暗角 vignette。塔形依据 `Assets/_UIAssets/Tower` 真实美术（四联炮/火焰箱/八边基座蓝水晶），怪物=钢骨红瞳 faction；三塔总览见 [14 塔图鉴](ui_mockups/14_TowerCodex.svg)。
> **UGUI 布局常量**（实现依据，与视觉风格解耦）：弹窗遮罩纯黑 55%（TowerInfoView 特例 35%）；按钮统一 320×72（LevelClearView 主按钮 420×72），Label 32 号居中；界面标题 38 号；星级行 76 号；禁用态 (0.5,0.5,0.5,0.6)。主 Canvas：Overlay、参考分辨率 1920×1080、Match=0.5，SafeAreaFitter 收刘海屏安全区。

### 6.1 界面清单（7 个已存在 prefab + 1 个新增元素）

| 界面 | prefab/脚本 | 层级 | 内容元素 | 效果图 |
|---|---|---|---|---|
| 选关（兼主菜单） | `SelectView` | Normal | 关卡按钮按 tbsceneinfo 运行时克隆：关卡名/难度/历史星级/锁态；设置入口 | [01](ui_mockups/01_SelectView_Normal.svg) / [01b 锁定态](ui_mockups/01b_SelectView_Locked.svg) |
| 战斗 HUD | `HudView` | Normal | 金币/生命/回合进度；塔建造栏（5 塔按钮，不足置灰）；「开始/下一回合/倒计时」按钮；**倍速按钮（×1/×2/×3，新增，见 §7.3）** | [02](ui_mockups/02_HudView_Normal.svg) / [02b 建造模式](ui_mockups/02b_HudView_BuildMode.svg) |
| 建造预览 | 无独立 prefab（BoardView 高亮 + RangeIndicatorView） | 世界层 | 可建=绿色高亮/不可建=红色高亮；射程圈预览；跟随塔影 | [02b](ui_mockups/02b_HudView_BuildMode.svg) |
| 升级/出售面板 | `TowerInfoView` | Normal | 选中塔：等级/攻击/攻速/射程/DPS；「升级(费用)」「出售(+返还)，两段确认」「关闭」 | [07](ui_mockups/07_TowerInfoView_Normal.svg) / [07b 出售确认](ui_mockups/07b_TowerInfoView_SellConfirm.svg) |
| 暂停 | `PauseView` | Normal | timeScale=0 + 半透明遮罩；继续/重开本关/设置/回选关 | [03](ui_mockups/03_PauseView.svg) |
| 设置 | `SettingView` | Normal | 语言切换、重置存档、关闭 | 以当前 Unity SettingView.prefab 为准 |
| 结算 | `LevelClearView`(+`LevelClearInfo`) | Normal | 胜/败标题；星级（1–3）与"新纪录"标记；剩余生命/击杀/漏怪；下一关/重打/回选关 | [05 胜利](ui_mockups/05_LevelClearView_Win.svg) / [05b 失败](ui_mockups/05b_LevelClearView_Lose.svg) |
| 浮动提示 | `TipsView` | Tips | 队列式浮字（金币不足/禁堵路/回合倒计时等） | [06](ui_mockups/06_TipsView.svg) |
| 塔图鉴（美术参考，无 prefab） | `Assets/_UIAssets/Tower` | — | 三塔竖卡（2026-10-14 收敛）：塔形大图 220×220 / 定位 / Lv.1 数值 | [14](ui_mockups/14_TowerCodex.svg) |

### 6.2 逐界面规格（元素级）

> 坐标为 Unity anchoredPosition（中心锚时：SVG x=960+X，y=540−Y）；「顶中锚」= anchor(0.5,1) 相对 Panel 顶边。

#### 6.2.1 SelectView（选关/主菜单）— Panel 1120×640 居中

| 元素 | 类型 | 位置/尺寸 | 文案/规则 |
|---|---|---|---|
| Bg | Image | 全屏 | 遮罩黑 55% |
| Title | TMP | 顶中 (0,-36)，1060×56 | "选择关卡"，38 号 |
| Summary | TMP | 顶中 (0,-92)，1000×44 | 运行时 "已通关 {c}/{levelCount}　★ {s}/{maxStars}"，32 号 |
| List | 容器 | 顶中 (0,-130)，1040×400 | 无 ScrollRect，纯手排 |
| LevelButtonTemplate | Button | 240×96，4 列 GapX24/GapY20 | 按 tbsceneinfo 克隆 `LevelButton_{id}`；三行：关卡名/★☆/难度 Ⅰ–Ⅲ 或"未解锁" |
| CloseBtn | Button | 中心 (0,-270)，320×72 | "返回" |

状态变体：未解锁=置灰+第三行"未解锁"，点击弹 Tips"先通关上一关才能解锁"（效果图 01b）；有局内快照的关卡点击直接续玩。

#### 6.2.2 HudView（战斗 HUD）

| 元素 | 位置/尺寸 | 文案/规则 |
|---|---|---|
| GoldText | 左上锚 (40,-30)，520×52 | "金币 {n}"，32 号左对齐 |
| HpText | 左上锚 (40,-84)，520×52 | "生命 {hp}/{maxHp}" |
| RoundText | 顶中 (0,-30)，700×56 | "准备中"/"回合 {n}/{total}"/"第 {n} 波"/"回合 {n} 完成"，38 号居中 |
| Btn_Tower_{Normal,Power,Retard} | 中心锚，128×128，间距 274，y=-427 | 底图+炮管子图（Retard 水晶偏移 (0,31)）；type 缺配置则隐藏；买不起/放置模式置灰；PriceText 子节点（预留）（原 Pierce/Laser 两颗已随三塔型收敛删除） |
| StartButton | 底中 (140,60)，220×72 | 文案流："开始"→"进行中"(置灰)→"下一回合"→"下一回合({倒计时})"→"已通关/已失败" |
| 倍速按钮（**新增**） | 底中 (-140,60)，220×72（P2b 落地） | "×1/×2/×3"循环，见 §7.3；速度经 `GameClock.Speed` 参数驱动（非 timeScale） |

状态变体：建造模式（效果图 02b）= 选中按钮金色描边+其余置灰，世界层绿/红格+射程圈+塔影；StartButton 转"进行中"。

#### 6.2.3 PauseView — Panel 560×520 居中

| 元素 | 位置/尺寸 | 文案 |
|---|---|---|
| Title | 顶中 (0,-36)，500×56 | "暂停" |
| ResumeBtn / RestartBtn / SettingsBtn / QuitBtn | 中心锚 320×72，y = 60 / -30 / -120 / -210（间距 90） | "继续"/"重新开始本关"/"设置"/"返回关卡选择" |

实现约束：OnEnable `timeScale=0`，OnDisable 无条件恢复 1；重开/返回前先恢复 timeScale；按钮走 unscaled。

#### 6.2.4 SettingView — Panel 620×560 居中

| 元素 | 位置/尺寸 | 文案/规则 |
|---|---|---|
| Title | 顶中 (0,-36)，560×56 | "设置" |
| LanguageText | 中心 (0,95)，520×56 | 当前语言的语言标签 |
| LanguageDropdown | 中心 (0,20)，320×72 | 切换语言并持久化 |
| ResetBtn | 中心 (0,-90)，320×72 | "重置存档" → Tips"存档已重置" |
| CloseBtn | 中心 (0,-178)，320×72 | "关闭"（按来源原路返回） |

#### 6.2.5 LevelClearView — Panel 640×680 居中

| 元素 | 位置/尺寸 | 文案/规则 |
|---|---|---|
| Title | 顶中 (0,-36)，580×56 | 胜"通关完成！"（金）/ 败"防御失败"（红） |
| LevelName | 中心 (0,210)，560×48 | "第 {n} 关" |
| Stars | 中心 (0,118)，560×96 | 76 号大星行；胜=本次评价，败=☆☆☆ |
| StarDetail | 中心 (0,42)，560×44 | 胜"本次 {★}　历史最高 {★}"；败仅"历史最高 {★}" |
| RecordTip | 中心 (0,-6)，560×40 | 仅新纪录显示："★ 新纪录！刷新了本关最高星级" |
| Stats | 中心 (0,-66)，560×46 | "剩余生命 {hp}/{max}　击杀 {n}　漏怪 {a}/{b}" |
| NextBtn | 中心 (0,-136)，420×72（特例） | 胜："下一关：{名}"；末关"已是最后一关"；**败=隐藏** |
| RetryBtn | 中心 (0,-216)，320×72 | 胜"重玩本关"/败"重新挑战" |
| SelectBtn | 中心 (0,-290)，320×72 | "返回关卡选择" |

#### 6.2.6 TipsView — 挂 TipsPanel 顶层

TipText：anchor(0.5,0.3)，1100×60，38 号居中；队列最多 3 条（超出丢最旧），每条 1.2s，淡入淡出各 0.15s；CanvasGroup `blocksRaycasts=false`（不挡操作）。典型消息：金币不足 / 禁堵路 / "下一回合 (n)" / "存档已重置" / "先通关上一关才能解锁"。

#### 6.2.7 TowerInfoView — Panel 560×460 居中（遮罩 35% 特例，点遮罩关闭）

| 元素 | 位置/尺寸 | 文案/规则 |
|---|---|---|
| Title | 顶中 (0,-34)，500×52 | "{塔名}  Lv.{等级}" |
| Stats | 顶中 (0,-100)，500×44 | "攻击 {0:0.#}　射程 {0:0.#} 格　攻速 {0.00}s　DPS {0:0.#}" |
| UpgradeBtn | 中心 (0,-20)，320×72 | "升级 ({费用})"/"已满级"/"无下一级"；金币不足置灰 |
| SellBtn | 中心 (0,-110)，320×72 | "出售 (+{返还})" → 两段确认"确认出售？"（红色，3s 超时还原，unscaled 计时） |
| CloseBtn | 中心 (0,-200)，320×72 | "关闭" |

### 6.3 跳转流程

```
启动 → SelectView（默认页）
  ├─ 点关卡 → Loading → 战斗 HUD（Preparing）
  │    ├─ 点塔按钮 → 建造预览 → 点棋盘格落塔（回 HUD）
  │    ├─ 点已建塔 → TowerInfoView → 升级/出售/关闭（回 HUD）
  │    ├─ 暂停按钮 → PauseView
  │    │    ├─ 继续 → HUD
  │    │    ├─ 重开 → Loading（同关）
  │    │    ├─ 设置 → SettingView → 返回 PauseView
  │    │    └─ 回选关 → SelectView（存局内快照）
  │    └─ 胜负 → LevelClearView
  │         ├─ 下一关 → Loading（下一关）
  │         ├─ 重打 → Loading（同关）
  │         └─ 回选关 → SelectView
  └─ 设置 → SettingView → 返回 SelectView
```

**返回栈规则**：SettingView 记录来源（SelectView/PauseView）原路返回；LevelClearView 与 PauseView 互斥（结算时不可暂停）；Android 返回键 = 当前界面等效「返回/暂停」按钮。

### 6.4 战斗场景世界层规格（非 UGUI）

效果图：[08 棋盘与路径](ui_mockups/08_WorldLayer_Board.svg) / [09 战斗实况](ui_mockups/09_WorldLayer_Combat.svg)（未显示请直接打开对应 SVG 文件）。

| 元素 | 实现 | 规格 |
|---|---|---|
| 棋盘 | `BoardView` 逐格 SpriteRenderer | 格子四态：Cell_Ground 空地（可建可走）/ Cell_Blocked 障碍（不可建不可走）/ Cell_Spawn 出生点 S（不可建）/ Cell_End 终点 E（不可建）；布局来自 tblevelmap；cellSize=1（tbglobal） |
| 路径 | `PathArrowView` | A* 最短路径逐格渲染 Path_Arrow；建塔即重算、全怪立即改道（§1.2 灵魂机制） |
| 塔 | 基座+炮管双件 Sprite | 炮管朝目标旋转（rotateSpeed=360）；选中显示射程圈 `RangeIndicatorView`；减速塔常驻光环 `SlowAuraView` |
| 怪物 | 8 部件骨骼式 SpriteRenderer + Animator | 四态动画 Ready/Walk/Attack/Death；血条 HP_Bar_Bg+Fill（满绿/低血橙）；飞行怪直线 S→E 不受地面堵路约束 |
| 子弹 | `BaseBullet` | 追踪弹/AOE 落点爆/减速/持续伤害；2026-10-14 起穿透与激光（LaserBeamView）已随三塔型收敛移除 |
| 伤害飘字 | `FloatingTextManager` | 世界空间 Canvas，池化 24 个 TMP：普通淡黄 (1,0.95,0.6)/致命红 (1,0.42,0.32)，0.7s 上浮 1.4 单位淡出，按怪节流 120ms |
| 背景 | Paper.png + `BackgroundParallax` | 视差滚动；P6 替换为各关专属背景 |
| 相机 | `CameraController` | 2D 正交，平移/缩放/自适应取景（按关卡 CameraPosition/Rotration 配置） |

建塔交互（§7.1）的视觉反馈以本节与效果图 02b 为准。

---

## 7. 交互逻辑与游戏状态机

### 7.1 建塔交互（以现 TowerPlacement 纯数学拾取为准）

1. 点 HUD 塔按钮 → 进入建造模式（按钮高亮，跟随手指/鼠标显示塔影+射程圈）；
2. 点/拖到棋盘格：`ScreenToWorldPoint → WorldToCell` 换算；
3. 校验链：空地？→ 金币够？→ **A* 堵路校验**（临时设墙→S→E 可达？）→ 通过则扣费建塔、全怪改道；任一失败则红格+Tips，不扣费；
4. 右键/再次点塔按钮/点空白 UI 取消建造模式。

### 7.2 选中与升级/出售

点已建塔 → 抛 `TowerSelectedEvent` → GameFlowManager 惰性打开 TowerInfoView → 升级（`TowerUpgradeRequestEvent`，换实例）/出售（`TowerSellRequestEvent`，返还+回收）。战斗中任意时刻可操作（含回合进行中）。

### 7.3 暂停与倍速

| 功能         | 规则                                                                                                                                 | 现状                     |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 暂停         | `Time.timeScale=0` + PauseView 遮罩；UI 走 unscaled 时间；热键轮询用 `unscaledDeltaTime`                                                       | ✅ 已实现                  |
| 倍速         | ×1/×2/×3 三档循环按钮，实现为**单一速度参数 `GameClock.Speed`（float，默认 1）**——`Time.timeScale` 恒为 1，**绝不参与倍速**（timeScale 语义收窄为暂停开关，仅允许 0/1）；全部模拟系统统一消费 `GameClock.DeltaTime`（每帧由 `GameClock.Tick()` 缓存一次 `Time.deltaTime × Speed`，同帧同值，消费清单见 7.3.1）；HUD 同步按钮文案；PerfProbe 统计走 unscaled 不受影响 | ❌ **未实现，列入程序案 P2b 新增** |
| 快捷键（调试/PC） | 空格=暂停/继续；右键=取消建造；滚轮=缩放；F1/F2 调试；F3 性能报告                                                                                            | ✅ 已实现                  |

#### 7.3.1 速度参数消费清单（P2b 迁移范围，所有与运行速度相关的内容必须使用 `GameClock.Speed` / `GameClock.DeltaTime`）

| 类别 | 系统 | 处理 |
| --- | --- | --- |
| 必须改用 `GameClock.DeltaTime` | WaveManager 出怪时间轴（interval / enemyInterval 累计） | 替换时间源 |
| 同上 | BaseEnemy 移动 / 攻击 CD / ms 计时 | 替换时间源 |
| 同上 | BaseTower 攻击 CD / searchInterval / 炮管旋转 rotateSpeed | 替换时间源 |
| 同上 | BaseBullet 弹道位移与追踪 | 替换时间源 |
| 同上 | SlowAuraView / 减速 Buff 剩余时长 | 按模拟时间衰减 |
| 同上 | FloatingTextManager 飘字上浮/淡出（0.7s） | 替换时间源 |
| 同上 | 回合倒计时（RoundComplete 5s 自动开波）与 StartButton 倒计时显示 | 替换时间源 |
| 同上 | BackgroundParallax 视差滚动（表现层，×3 时世界观感同步加速） | 替换时间源 |
| Animator | BaseEnemy / Boss 动画机 | `animator.speed = GameClock.Speed`（初始化与切档时同步；回收时还原 1，防对象池残留） |
| 保持实时（不用参数） | Tips 队列（1.2s/条）、出售确认 3s（unscaledDeltaTime）、全部 UI 动画、PerfProbe | 实时 / unscaled，倍速不影响 |

**硬性约束**：① `Time.timeScale` 全工程仅允许 0（暂停）/ 1（运行）两个值，禁止任何系统把倍速写入 timeScale；② 同帧内所有系统必须使用同一份 `GameClock.DeltaTime` 缓存值，禁止各自再乘 Speed；③ 倍速档位在 GameOver / 重开 / 回选关 / 进 Loading 时重置为 ×1；④ 暂停期间倍速请求无效（PauseView 遮罩挡按钮 + GameFlowManager 校验双保险）；⑤ 降档扩展（如 ×2.5）只需改 Speed 值，无需改结构。

### 7.4 游戏状态机（对齐 `GameFlowState`，暂停为正交叠加态）

| 状态           | 进入条件        | 行为                                  | 迁移                                         |
| ------------ | ----------- | ----------------------------------- | ------------------------------------------ |
| None         | 启动前         | —                                   | →Loading（点选关卡）                             |
| Loading      | 选中关卡/重开/下一关 | 加载资源→配置→建棋盘→寻路网格→相机→预加载             | 完成→Preparing                               |
| Preparing    | 建关完成        | 自由布塔；HUD「开始」可用                      | 点开始（`StartRoundRequestEvent`）→RoundRunning |
| RoundRunning | 回合开始        | WaveManager 时间轴出怪；战斗 tick；随时可建/升/售塔 | 时间轴清空且场上无怪→RoundComplete；生命≤0→GameOver(败)  |


| RoundComplete | 回合清空 | 发回合奖励；存局内快照；5s 自动/手动开下一回合 | 下一回合→RoundRunning；已是末回合→GameOver(胜) |
| GameOver | 胜/败 | 胜：评星→RecordClear→解锁下一关；派 `GameOverEvent` → LevelClearView | 弹窗按钮→Loading/SelectView |
| （叠加）Paused | 任意局中状态 + 暂停请求 | timeScale=0，战斗 tick 停摆（与倍速解耦：暂停走 timeScale、倍速走 GameClock.Speed，互不写入对方通道；Speed 保持原档位，恢复后立即生效） | 继续→回到原状态 |

事件总线关键事件（实现侧直接复用，禁止新造平行事件）：`ConfigLoadedEvent / SelectLevelRequestEvent / StartRoundRequestEvent / RoundClearEvent / GameOverEvent / TowerSelectedEvent / TowerUpgradeRequestEvent / TowerSellRequestEvent / PauseToggleRequestEvent / PauseRequestEvent / ResumeRequestEvent / RestartLevelRequestEvent / QuitToSelectRequestEvent / OpenSettingsRequestEvent / CloseSettingsRequestEvent / LevelClearEvent`。

> 2026-10-18 语义划分：`PauseToggleRequestEvent` = 暂停/继续开关（HUD `Btn_Pause`、热键 P，不弹窗）；`PauseRequestEvent` = 只打开暂停菜单弹窗（HUD `Btn_Intro` 文案已改为 `Menu`），**不再暂停**；`PauseStateChangedEvent(bool)` 是"暂停状态已变化"的广播（供暂停菜单标题等跟随）。暂停的唯一写入口是 `GameClock.SetPaused`。

### 7.5 胜负判定与星级

| 结果 | 条件 | 后续 |
|---|---|---|
| 胜利 | 配置的全部回合完成（RoundComplete 时回合游标越界） | 评级→写存档→解锁下一关→结算弹窗 |
| 失败 | 生命 ≤ 0（任意时刻，立即结算，场上战斗停止） | 不写星级、不解锁；结算弹窗（仅重打/回选关） |

---

## 8. 外部资源需求清单（不阻塞代码，按 P6 阶段接入）

| 类别 | 数量 | 规格 | 挂接点 |
|---|---|---|---|
| 塔美术 | ~~Pierce/Laser 两型 ×3 级~~ | 已作废（2026-10-14 三塔型收敛，无需新美术）；三塔各自 128px PNG，基座+炮管分件 | `Assets/_UIAssets/Tower/` → prefab 转换工具 |
| 战斗背景 | 8 张（每关 1 张） | 2048×1152 PNG，替换 Paper.png 复用现状 | `Assets/_UIAssets/Backgrounds/` |
| 打击粒子 | 命中/死亡/AOE 爆炸 3 组 | ParticleSystem prefab，MaxParticles ≤50 | 事件已抛出，挂到 Bullet/Enemy 表现层 |
| 怪物帧动画 | 119 怪的 Ready/Walk/Attack/Death | 沿用分部件骨骼式 Animator 方案 | `MonsterAnimEventReceiver` 已挂接 |

当前版本为无声游戏：不接入声音资源、声音表或音量设置。历史迭代记录与旧界面示意图仅用于追溯，界面以当前 Unity prefab 为准。
