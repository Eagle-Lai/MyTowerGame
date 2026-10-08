# 《坚守阵地》策划案（v3.0）

> 项目：单机 2D 塔防手游（对标 Fieldrunners 核心机制）　|　平台：Android  
> 工程：`G:\MyTowerGame`（Unity 2022.3.62f3c1）　|　主场景：`Assets/Scenes/Main.unity`  
> 配套文档：`Docs/ProgramDesign_坚守阵地_v3.md`（程序案）  
> 版本说明：本文档以 **2026-10-08 工程实测**为基线重新编制，取代 `TowerDefense_Design_and_Implementation.md`（v2.1，保留为历史档案）。数值体系为**重新设计版**，与现配置的差异在各表「差异对照」列标出，落地步骤见程序案 §6。

---

## 1. 核心玩法循环

### 1.1 总循环（局外 → 局内 → 局外）

```
选关（SelectView，含星级/解锁/继续快照）
  → 关卡加载（Loading：资源 → 配置 → 建棋盘 → 相机取景）
  → 备战（Preparing：初始金币布塔，自由摆放塑造路径）
  → 回合战（RoundRunning：出怪 → 塔索敌开火 → 击杀得金/漏怪扣血）
  → 回合结算（RoundComplete：回合奖励 → 升级/出售/补塔 → 自动/手动开下一回合）
  → 5 回合打完 → 结算（GameOver：星级评定 → 写存档 → 解锁下一关）
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

## 2. 关卡与波次节奏

### 2.1 关卡总表（8 关，每关 5 回合，共 40 回合/40 波）

| 关卡 | 地图特征           | 初始金币 | 初始生命 | 难度档 | 回合链         |
| -- | -------------- | ---- | ---- | --- | ----------- |
| 1  | 全开阔，路径完全由玩家塑造  | 100  | 20   | 1   | Round 1–5   |
| 2  | 双障碍夹出中段窄口      | 220  | 20   | 1   | Round 6–10  |
| 3  | 厚横墙，好建位变少      | 380  | 20   | 1   | Round 11–15 |
| 4  | 双交错横墙，S 形走位    | 600  | 18   | 2   | Round 16–20 |
| 5  | 中央大块障碍，贴路可建位稀缺 | 900  | 18   | 2   | Round 21–25 |
| 6  | 井字街区，内侧位置差     | 1300 | 15   | 2   | Round 26–30 |
| 7  | 密集障碍，可建位少、容错低  | 1800 | 15   | 3   | Round 31–35 |
| 8  | 终盘：障碍最密，可建位最少  | 2400 | 12   | 3   | Round 36–40 |

> 与现配置（tbsceneinfo）**一致，无改动**。初始金币递增是为了让后期关卡开局即可布置成型防线（关卡 8 开局约可铺 8–10 座中级塔）。

### 2.2 波次节奏规则

- **每回合 = 1 个波次编组**（RoundData.EnemyIndexs → EnemyList.id 一一对应）。
- **回合间隔**：`waveIntervalMs = 3000`（关卡内波次衔接）；回合完成后 5 秒自动开下一回合（`autoNextRoundDelayMs = 5000`，HUD 倒计时，玩家可点按钮立即开）。
- **波内出怪**：单怪间隔 `enemyInterval` 从第 1 波 **560ms** 逐波递减约 8ms，第 40 波约 **250ms**（密度即压力）。
- **波次规模**：第 1 波 5 只 → 每波 +0~2 只 → 第 40 波约 25 只；单波血量预算按 `HP(w) = 1400 × 1.10^(w-1)`（w 为全局波序 1–40）递增：
  - w=1：1400　w=10：≈3300　w=20：≈8560　w=30：≈22200　w=40：≈57600
- **每关第 5 回合（5/10/15/20/25/30/35/40 波）为高压波**：编组中重甲/Boss 档占比 ≥40%，其余波次以杂兵+快速混编（比例约 6:4），第 3 关起每波至少混入 1 只飞行怪（强制玩家覆盖对空）。
- **压力曲线**：单关内 1→4 波线性爬升，第 5 波跳升 1.6 倍（Boss 波）；跨关难度由敌人梯度档（§4.2）整体抬升承担。

### 2.3 波次编组模板（策划填表规则）

| 回合位置     | 编组公式               | 示例（第 1 关）              |
| -------- | ------------------ | ---------------------- |
| 回合 1     | 纯杂兵 ×5             | Rat×5                  |
| 回合 2     | 杂兵 60% + 快速 40% ×7 | Rat×4 + Bat×3          |
| 回合 3     | 混编 ×8 + 首只重甲       | Rat×5 + Bat×2 + Pig×1  |
| 回合 4     | 混编 ×9 + 飞行 2       | Rat×5 + Wasp×2 + Bat×2 |
| 回合 5（高压） | 重甲 40% + 杂兵 60% ×8 | Pig×3 + Rat×5          |

---

## 3. 防御塔数值表（重新设计）

### 3.1 设计原则

1. **DPS/金币效率随升级递增**（鼓励升级优于铺量，但铺量有堵路塑形价值）；
2. **5 塔型定位互补**：Normal 性价比基准、Power 范围清群、Retard 控制增益全队、Pierce 直线穿透、Laser 高单伤对重甲/Boss；
3. 售价 = **累计投入 × 0.7**（四舍五入），与现规则一致；
4. 所有数值**不改表结构**，仅改字段值（字段含义见程序案 §4.3）。

### 3.2 全字段数值表

**NormalTower（type=1，单体速射，子弹 id=1）**

| 等级 | id | radius | power | CD(ms) | prices | upgradeTo | sellPrice | DPS   | DPS/累计金    |
| -- | -- | ------ | ----- | ------ | ------ | --------- | --------- | ----- | ---------- |
| L1 | 1  | 3      | 12    | 400    | 25     | 2         | 18        | 30.0  | 1.20       |
| L2 | 2  | 4      | 20    | 350    | 40     | 3         | 46        | 57.1  | 0.88→1.43* |
| L3 | 3  | 5      | 32    | 300    | 60     | 0         | 88        | 106.7 | 0.85→1.78* |

**PowerTower（type=2，AOE 爆炸，子弹 id=2，effectType=3）**

| 等级 | id | radius | power | CD(ms) | prices | upgradeTo | sellPrice | 单体DPS | 备注          |
| -- | -- | ------ | ----- | ------ | ------ | --------- | --------- | ----- | ----------- |
| L1 | 4  | 3      | 30    | 900    | 45     | 5         | 32        | 33.3  | 落点 1.2 格内全伤 |
| L2 | 5  | 4      | 50    | 800    | 70     | 6         | 81        | 62.5  |             |
| L3 | 6  | 5      | 80    | 700    | 105    | 0         | 158       | 114.3 | 清群核心        |

**RetardTower（type=3，减速光环，子弹 id=4，effectType=1，effectValue=减速比例）**

| 等级 | id | radius | power | CD(ms) | prices | upgradeTo | sellPrice | 减速  |
| -- | -- | ------ | ----- | ------ | ------ | --------- | --------- | --- |
| L1 | 7  | 4      | 6     | 500    | 30     | 8         | 21        | 30% |
| L2 | 8  | 5      | 12    | 450    | 50     | 9         | 56        | 40% |
| L3 | 9  | 6      | 20    | 400    | 75     | 0         | 109       | 50% |

**PierceTower（type=4，直线穿透，子弹 id=3，pierce=3 共穿 4 目标）**

| 等级 | id | radius | power | CD(ms) | prices | upgradeTo | sellPrice | 单目标DPS |
| -- | -- | ------ | ----- | ------ | ------ | --------- | --------- | ------ |
| L1 | 10 | 4      | 8     | 350    | 35     | 11        | 25        | 22.9   |
| L2 | 11 | 5      | 13    | 300    | 55     | 12        | 63        | 43.3   |
| L3 | 12 | 6      | 20    | 250    | 80     | 0         | 119       | 80.0   |

**LaserTower（type=5，hitscan 瞬发，无弹体 bulletId=0，effectType=4）**

| 等级 | id | radius | power | CD(ms) | prices | upgradeTo | sellPrice | DPS   |
| -- | -- | ------ | ----- | ------ | ------ | --------- | --------- | ----- |
| L1 | 13 | 4      | 30    | 800    | 50     | 14        | 35        | 37.5  |
| L2 | 14 | 5      | 55    | 700    | 80     | 15        | 91        | 78.6  |
| L3 | 15 | 6      | 90    | 600    | 120    | 0         | 182       | 150.0 |

\* DPS/累计金第二列为按累计投入（含本级）计算的效率。

公共字段（全塔通用）：`targetMode=0`（最先接近终点者优先）、`searchIntervalMs=100`、`rotateSpeed=360`、`canAttackAir=1`（全塔可对空）。

### 3.3 与现配置差异对照（tbtowerinfo 15 行）

| 塔            | 项              | 现值 → 新值                                                                                  |
| ------------ | -------------- | ---------------------------------------------------------------------------------------- |
| Normal L1–L3 | power          | 10/14/15 → **12/20/32**                                                                  |
| Normal L1–L3 | CD             | 300/200/100 → **400/350/300**（原 L3 攻速过快、DPS 150 失控）                                      |
| Normal L1–L3 | prices         | 20/30/50 → **25/40/60**；sellPrice 14/35/70 → **18/46/88**                                |
| Normal L3    | radius         | 6 → **5**                                                                                |
| Power L1–L3  | power          | 25/38/50 → **30/50/80**；CD 600/500/400 → **900/800/700**                                 |
| Power L1–L3  | prices         | 35/55/85 → **45/70/105**；sellPrice 24/62/122 → **32/81/158**                             |
| Retard L1–L3 | 减速 effectValue | 0.5/0.6/0.7 → **0.30/0.40/0.50**（原 70% 减速过强）                                             |
| Retard L1–L3 | power          | 8/17/27 → **6/12/20**；prices 30/45/70 → **30/50/75**                                     |
| Retard L1–L3 | bulletId       | 0 → **4**（挂减速弹，修复 L1 无弹体不发减速的问题）                                                         |
| Pierce L1–L3 | power          | 6/10/14 → **8/13/20**；CD 200/170/140 → **350/300/250**                                   |
| Laser L1–L3  | power          | 24/50/78 → **30/55/90**；CD 500/450/400 → **800/700/600**；prices 40/60/80 → **50/80/120** |
| 全部           | resName        | Pierce/Laser 现复用 `Tower_Normal0`（占位），**保持不变**，新美术在 P6 阶段接入                               |

**子弹表（tbbulletdata）差异**：仅 id=2 爆炸弹 `aoeRadius 1.2 → 1.5`；其余不变。

---

## 4. 敌人数值表（重新设计）

### 4.1 字段语义（沿用现表结构）

`speed`(格/秒) · `hp` · `armor`(减伤比例 0–1，实际伤害=power×(1−armor)) · `reward`(击杀金币) · `damageToPlayer`(漏怪扣血) · `isFlying`(1=飞行，不受地面障碍改道约束，直线飞 S→E) · `type`(1=普通 2=快速 3=重甲)

### 4.2 五档原型 × 8 梯度（T=关卡序号 1–8）

| 原型                | type | 基础值（T1）                  | 递推公式（T≥2）     | reward  | 扣血 | 飞行    |
| ----------------- | ---- | ------------------------ | ------------- | ------- | -- | ----- |
| 杂兵（Rat/Chicken 等） | 1    | hp 180 · 速 1.4 · 甲 0.05  | hp×1.32^(T−1) | 6+T     | 1  | 否     |
| 快速（Bat 等）         | 2    | hp 110 · 速 3.0 · 甲 0     | hp×1.30^(T−1) | 8+T     | 1  | 部分    |
| 飞群（Wasp 等）        | 2    | hp 200 · 速 4.0 · 甲 0     | hp×1.30^(T−1) | 10+T    | 1  | **是** |
| 重甲（Pig/Giant 等）   | 3    | hp 600 · 速 0.8 · 甲 0.35  | hp×1.35^(T−1) | 18+2T   | 2  | 否     |
| Boss（每关压轴）        | 3    | hp 4000 · 速 0.6 · 甲 0.20 | hp×1.40^(T−1) | 100+10T | 5  | 否     |

查表示例（hp）：杂兵 T4 = 180×1.32³ ≈ **414**；重甲 T8 = 600×1.35⁷ ≈ **4890**；Boss T8 = 4000×1.4⁷ ≈ **42150**。

### 4.3 梯度落地规则

- 现 `tbenemydata` 132 行 = 具体怪（119 种美术各 1 行）+ 梯度档行。新方案**保留该结构**：具体怪行按所属原型与梯度档回填 hp/armor/reward，描述列注明「原型/梯度」。
- **与现配置差异**：现梯度基准（T1 杂兵 hp 220 / 快速 130 / 重甲 700 / Boss 无独立档）→ 新基准（180 / 110 / 200飞群 / 600 / 4000 Boss）；现 reward 固定值 → 新「基础+T」随关卡递增。逐行映射表由程序案 P2 阶段脚本生成（规则见程序案 §6-P2）。

---

## 5. 经济系统

| 项      | 数值/公式                                                                    | 说明                           |
| ------ | ------------------------------------------------------------------------ | ---------------------------- |
| 初始金币   | 按关卡表 §2.1（100→2400）                                                      | 关卡配置 `initialGold`           |
| 初始生命   | 20/20/20/18/18/15/15/12                                                  | 关卡配置 `initialHp`             |
| 击杀奖励   | 敌人表 `reward`（基础+T）                                                       | 直接入账                         |
| 回合奖励   | `rewardGold = 30 + 4×(回合序−1)`（30/34/38/42/46…）                           | 沿用现 tbrounddata 规律，全局回合序连续递增 |
| 出售返还   | 累计投入 × 0.7（查 `sellPrice` 字段）                                             | 含全部升级费用                      |
| 建塔扣费   | 建造时一次性扣 `prices`；金币不足按钮置灰                                                |                              |
| 升级扣费   | 扣目标等级 `prices`，塔实例替换                                                     |                              |
| 平衡约束 1 | 关卡 1 开局 100 金 = 4 座 Normal L1，第 1 波总血量 1400 ÷（4 塔×30 DPS）≈ 12 秒清完，可无漏怪开局 |                              |
| 平衡约束 2 | 每回合收入（击杀+回合奖）≥ 该回合推荐新增战力成本的 60%，保证"边打边建"而非纯攒金                            |                              |
| 平衡约束 3 | 漏 1 只 Boss（扣 5 血）即失去 3 星评价（见 §7），高压波容错 = 生命余量                            |                              |

---

## 6. UI 规范（清单 / 逐界面规格 / 跳转流程 / 世界层）

> 效果图目录：`Docs/ui_mockups/`（**14 张 SVG 正式版·深色科幻风**，1920×1080 高保真，几何与 prefab 实测数值一致）。
> 若文档查看器不显示图片，请直接打开对应 SVG 文件。
> **深色科幻视觉令牌**（正式版效果图统一规范）：底色 `#0B0E14` / 战场 `#10141D`；面板 `#2A3444→#1B2330→#222C3B` 渐变 + 45° 切角（大件 16px / 按钮 10~12px）+ 描边 `#3A4A63`；功能色——主青 `#35E0FF`（主按钮/路径/射程/传送门）、金 `#FFC94D`（货币/星级/普通伤害飘字）、红 `#FF4D5E`（危险/致命/敌方瞳光/失败主题）、绿 `#3DFFA8`（可建格/满血条）、橙火 `#FF7A29`（Power 火焰）、冰 `#7DE8FF`（Retard 控场）、紫 `#7C5CFF`/`#B18CFF`（Pierce/Laser 新形态）；发光=DropShadow 霓虹 + Bloom 模糊叠加，世界层加暗角 vignette。塔形依据 `Assets/_UIAssets/Tower` 真实美术（四联炮/火焰箱/八边基座蓝水晶），怪物=钢骨红瞳 faction；五塔总览见 [14 塔图鉴](ui_mockups/14_TowerCodex.svg)。
> **UGUI 布局常量**（实现依据，与视觉风格解耦）：弹窗遮罩纯黑 55%（TowerInfoView 特例 35%）；按钮统一 320×72（LevelClearView 主按钮 420×72），Label 32 号居中；界面标题 38 号；星级行 76 号；禁用态 (0.5,0.5,0.5,0.6)。主 Canvas：Overlay、参考分辨率 1920×1080、Match=0.5，SafeAreaFitter 收刘海屏安全区。

### 6.1 界面清单（7 个已存在 prefab + 1 个新增元素）

| 界面 | prefab/脚本 | 层级 | 内容元素 | 效果图 |
|---|---|---|---|---|
| 选关（兼主菜单） | `SelectView` | Normal | 8 关按钮（按 tbsceneinfo 运行时克隆）：关卡名/难度/历史星级/锁态；设置入口 | [01](ui_mockups/01_SelectView_Normal.svg) / [01b 锁定态](ui_mockups/01b_SelectView_Locked.svg) |
| 战斗 HUD | `HudView` | Normal | 金币/生命/回合进度；塔建造栏（5 塔按钮，不足置灰）；「开始/下一回合/倒计时」按钮；**倍速按钮（×1/×2/×3，新增，见 §7.3）** | [02](ui_mockups/02_HudView_Normal.svg) / [02b 建造模式](ui_mockups/02b_HudView_BuildMode.svg) |
| 建造预览 | 无独立 prefab（BoardView 高亮 + RangeIndicatorView） | 世界层 | 可建=绿色高亮/不可建=红色高亮；射程圈预览；跟随塔影 | [02b](ui_mockups/02b_HudView_BuildMode.svg) |
| 升级/出售面板 | `TowerInfoView` | Normal | 选中塔：等级/攻击/攻速/射程/DPS；「升级(费用)」「出售(+返还)，两段确认」「关闭」 | [07](ui_mockups/07_TowerInfoView_Normal.svg) / [07b 出售确认](ui_mockups/07b_TowerInfoView_SellConfirm.svg) |
| 暂停 | `PauseView` | Normal | timeScale=0 + 半透明遮罩；继续/重开本关/设置/回选关 | [03](ui_mockups/03_PauseView.svg) |
| 设置 | `SettingView` | Normal | 音量 ±10%、静音开关、重置存档、关闭 | [04](ui_mockups/04_SettingView.svg) |
| 结算 | `LevelClearView`(+`LevelClearInfo`) | Normal | 胜/败标题；星级（1–3）与"新纪录"标记；剩余生命/击杀/漏怪；下一关/重打/回选关 | [05 胜利](ui_mockups/05_LevelClearView_Win.svg) / [05b 失败](ui_mockups/05b_LevelClearView_Lose.svg) |
| 浮动提示 | `TipsView` | Tips | 队列式浮字（金币不足/禁堵路/回合倒计时等） | [06](ui_mockups/06_TipsView.svg) |
| 塔图鉴（美术参考，无 prefab） | `Assets/_UIAssets/Tower` | — | 五塔竖卡：塔形大图 220×220 / 定位 / Lv.1 数值；Pierce/Laser 标注新形态设计稿 | [14](ui_mockups/14_TowerCodex.svg) |

### 6.2 逐界面规格（元素级）

> 坐标为 Unity anchoredPosition（中心锚时：SVG x=960+X，y=540−Y）；「顶中锚」= anchor(0.5,1) 相对 Panel 顶边。

#### 6.2.1 SelectView（选关/主菜单）— Panel 1120×640 居中

| 元素 | 类型 | 位置/尺寸 | 文案/规则 |
|---|---|---|---|
| Bg | Image | 全屏 | 遮罩黑 55% |
| Title | TMP | 顶中 (0,-36)，1060×56 | "选择关卡"，38 号 |
| Summary | TMP | 顶中 (0,-92)，1000×44 | 运行时 "已通关 {c}/8　★ {s}/24"，32 号 |
| List | 容器 | 顶中 (0,-130)，1040×400 | 无 ScrollRect，纯手排 |
| LevelButtonTemplate | Button | 240×96，4 列 GapX24/GapY20 | 按 tbsceneinfo 克隆 `LevelButton_{id}`；三行：关卡名/★☆/难度 Ⅰ–Ⅲ 或"未解锁" |
| CloseBtn | Button | 中心 (0,-270)，320×72 | "返回" |

状态变体：未解锁=置灰+第三行"未解锁"，点击弹 Tips"先通关上一关才能解锁"（效果图 01b）；有局内快照的关卡点击直接续玩。

#### 6.2.2 HudView（战斗 HUD）

| 元素 | 位置/尺寸 | 文案/规则 |
|---|---|---|
| GoldText | 左上锚 (40,-30)，520×52 | "金币 {n}"，32 号左对齐 |
| HpText | 左上锚 (40,-84)，520×52 | "生命 {hp}/{maxHp}" |
| RoundText | 顶中 (0,-30)，700×56 | "准备中"/"回合 {n}/5"/"第 {n} 波"/"回合 {n} 完成"，38 号居中 |
| Btn_Tower_{Normal,Power,Retard,Pierce,Laser} | 中心锚，128×128，间距 274，y=-427 | 底图+炮管子图（Retard 水晶偏移 (0,31)）；type 缺配置则隐藏；买不起/放置模式置灰；PriceText 子节点（预留） |
| StartButton | 底中 (140,60)，220×72 | 文案流："开始"→"进行中"(置灰)→"下一回合"→"下一回合({倒计时})"→"已通关/已失败" |
| 倍速按钮（**新增**） | 底中 (-140,60)，220×72（P2b 落地） | "×1/×2/×3"循环，见 §7.3；速度经 `GameClock.Speed` 参数驱动（非 timeScale） |

状态变体：建造模式（效果图 02b）= 选中按钮金色描边+其余置灰，世界层绿/红格+射程圈+塔影；StartButton 转"进行中"。

#### 6.2.3 PauseView — Panel 560×520 居中

| 元素 | 位置/尺寸 | 文案 |
|---|---|---|
| Title | 顶中 (0,-36)，500×56 | "暂停" |
| ResumeBtn / RestartBtn / SettingsBtn / QuitBtn | 中心锚 320×72，y = 60 / -30 / -120 / -210（间距 90） | "继续"/"重新开始本关"/"设置"/"返回关卡选择" |

实现约束：OnEnable `timeScale=0`，OnDisable 无条件恢复 1；重开/返回前先恢复 timeScale；按钮走 unscaled。

#### 6.2.4 SettingView — Panel 620×600 居中

| 元素 | 位置/尺寸 | 文案/规则 |
|---|---|---|
| Title | 顶中 (0,-36)，560×56 | "设置" |
| VolumeText | 中心 (0,120)，520×56 | "音量 {n}%"，步长 ±10% |
| VolDownBtn / VolUpBtn | 中心 (±170,40)，320×72 | "音量 −/＋" |
| MuteBtn | 中心 (0,-50)，320×72 | "静音"⇄"取消静音" |
| ResetBtn | 中心 (0,-140)，320×72 | "重置存档" → Tips"存档已重置" |
| CloseBtn | 中心 (0,-230)，320×72 | "关闭"（按来源原路返回） |

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
| 子弹 | `BaseBullet` + `LaserBeamView` | 追踪弹/AOE 落点爆/穿透/减速/持续伤害五型；激光 hitscan 无弹体 |
| 伤害飘字 | `FloatingTextManager` | 世界空间 Canvas，池化 24 个 TMP：普通淡黄 (1,0.95,0.6)/致命红 (1,0.42,0.32)，0.7s 上浮 1.4 单位淡出，按怪节流 120ms |
| 背景 | Paper.png + `BackgroundParallax` | 视差滚动；P6 替换为 8 关专属背景 |
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
| 倍速         | ×1/×2/×3 三档循环按钮，实现为**单一速度参数 `GameClock.Speed`（float，默认 1）**——`Time.timeScale` 恒为 1，**绝不参与倍速**（timeScale 语义收窄为暂停开关，仅允许 0/1）；全部模拟系统统一消费 `GameClock.DeltaTime`（每帧由 `GameClock.Tick()` 缓存一次 `Time.deltaTime × Speed`，同帧同值，消费清单见 7.3.1）；HUD 同步按钮文案；**音效 pitch 不随倍速变化**（避免尖锐化）；PerfProbe 统计走 unscaled 不受影响 | ❌ **未实现，列入程序案 P2b 新增** |
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
| 保持实时（不用参数） | Tips 队列（1.2s/条）、出售确认 3s（unscaledDeltaTime）、全部 UI 动画、音效、PerfProbe | 实时 / unscaled，倍速不影响 |

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

事件总线关键事件（实现侧直接复用，禁止新造平行事件）：`ConfigLoadedEvent / SelectLevelRequestEvent / StartRoundRequestEvent / RoundClearEvent / GameOverEvent / TowerSelectedEvent / TowerUpgradeRequestEvent / TowerSellRequestEvent / PauseRequestEvent / ResumeRequestEvent / RestartLevelRequestEvent / QuitToSelectRequestEvent / OpenSettingsRequestEvent / CloseSettingsRequestEvent / LevelClearEvent`。

### 7.5 胜负判定与星级

| 结果 | 条件 | 后续 |
|---|---|---|
| 胜利 | 5 回合全部完成（RoundComplete 时回合游标越界） | 评星→写存档→解锁下一关→结算弹窗 |
| 失败 | 生命 ≤ 0（任意时刻，立即结算，场上战斗停止） | 不写星级、不解锁；结算弹窗（仅重打/回选关） |
| 3 星 | 剩余生命 = 初始生命（满血通关） | 存档只升不降 |
| 2 星 | 剩余生命 ≥ 初始生命 × 50% | |
| 1 星 | 其余胜利情况 | |

---

## 8. 外部资源需求清单（不阻塞代码，按 P6 阶段接入）

| 类别 | 数量 | 规格 | 挂接点 |
|---|---|---|---|
| 音效 | 16 项（tbaudio 已配好逻辑名） | wav/ogg，≤1.5s（UI 与开火类 ≤0.5s），44.1kHz | `Assets/Audio/` → 跑 gen_audio_catalog → AudioManager 三段式查找自动生效 |
| BGM | 2 首（战斗/选关，循环） | ogg，码率 ≤128kbps | tbaudio 增 2 行（loop=1） |
| 塔美术 | Pierce/Laser 两型 ×3 级 | 128px PNG，基座+炮管分件，风格对齐现有 Normal/Power/Retard | `Assets/_UIAssets/Tower/` → prefab 转换工具 |
| 战斗背景 | 8 张（每关 1 张） | 2048×1152 PNG，替换 Paper.png 复用现状 | `Assets/_UIAssets/Backgrounds/` |
| 打击粒子 | 命中/死亡/AOE 爆炸 3 组 | ParticleSystem prefab，MaxParticles ≤50 | 事件已抛出，挂到 Bullet/Enemy 表现层 |
| 怪物帧动画 | 119 怪的 Ready/Walk/Attack/Death | 沿用分部件骨骼式 Animator 方案 | `MonsterAnimEventReceiver` 已挂接 |
