# 《坚守阵地》美术与效果图补全策划案（v1.0）

> 项目：单机 2D 塔防手游（对标 Fieldrunners 核心机制）　|　平台：Android
> 工程：本工程（Unity 2022.3.62f3c1，Built-in RP）
> 主场景：`Assets/Scenes/Main.unity`（单场景 + 常驻根节点架构）
> 配套文档：`Docs/GameDesign_坚守阵地_v3.md`（策划案）、`Docs/ProgramDesign_坚守阵地_v3.md`（程序案）
> 效果图：`Docs/ui_mockups/`（14 张，本策划案新增 8 张）
> **本策划案定位：可直接交付 AI 执行的全流程实施蓝图。每一节都给出节点树 / 坐标 / 配色 / 字号 / 验收标准，无需二次追问。**

---

## 0. 交付说明（给 AI 的元指令）

本文档是**执行型**策划案，不是设计参考。阅读者（AI 或开发者）应当：

1. **严格按 §2 视觉令牌**施工，不得自创颜色。所有色值均为 `Assets/Editor/UISkinArtGenerator.cs` 中已定义的令牌或其直接派生。
2. **严格按 §3 生成器接口**写代码。新增界面一律走 `UIPrefabBuilder` 的 `CreateDialogShell` 骨架，**不得手搓 prefab**（手搓会在下次全量重建时被 `IsSafeToRebuild` 判为"陌生节点"而中止）。
3. **每完成一个界面，必须跑 §6 的四道校验**，全 PASS 才算完成。
4. **坐标一律用"画布中心为原点"描述**（与 `UIPrefabBuilder` 现有口径一致）。`x=960+X`、`y=540−Y` 是效果图 SVG 的换算关系，**不要混用**。
5. **禁止事项**见 §7，违反其中任一条都会导致返工。

---

## 1. 现状与缺口总览

### 1.1 已有界面（8 个，全部已实现且可用）

| 界面 | LogicalName | 层级 | 说明 |
|---|---|---|---|
| 关卡选择 | `SelectView` | NormalPanel | 整页全屏横向画廊 |
| 战斗 HUD | `HudView` | NormalPanel | 金币/生命/回合/塔栏/开始/倍速 |
| 暂停 | `PauseView` | NormalPanel | 居中弹窗 |
| 设置 | `SettingView` | NormalPanel | 居中弹窗 |
| 结算 | `LevelClearView` | NormalPanel | 胜败共用 |
| 提示条 | `TipsView` | TipsPanel | 顶部滚动提示 |
| 塔操作 | `TowerInfoView` | NormalPanel | 升级/出售 |
| 关卡卡片 | `SelectLevelItem` | — | 独立资产，非运行时加载 |

### 1.2 待补全清单（本策划案覆盖范围）

| # | 界面/组件 | 类型 | 优先级 | 是否阻塞上线 |
|---|---|---|---|---|
| A1 | `SplashView` 开屏页 | 新增界面 | P0 | 否（体验必需） |
| A2 | `LoadingView` 资源加载进度 | 新增界面 | P0 | 否（体验必需） |
| A3 | `HotUpdateView` 热更新下载 | 新增界面 | P0 | **是** |
| B1 | `MainMenuView` 主菜单 | 新增界面 | P1 | 否 |
| B2 | `TowerCodexView` 塔图鉴 | 新增界面 | P1 | 否 |
| B3 | `MonsterCodexView` 怪物图鉴 | 新增界面 | P2 | 否 |
| B4 | `LevelDetailView` 关卡详情 | 新增界面 | P2 | 否 |
| C1 | `SellConfirmView` 出售确认 | 新增界面 | P1 | 否 |
| C2 | `ConfirmView` 通用确认弹窗 | 新增界面 | P1 | 否 |
| C3 | 屏幕震动反馈 | 组件 | P1 | 否 |
| C4 | 切关 Loading 遮罩 | 组件 | P2 | 否 |

---

## 2. 视觉令牌（唯一配色源，不得自创）

### 2.1 基础色板

直接从 `Assets/Editor/UISkinArtGenerator.cs` 提取。**任何新增界面必须使用以下色值。**

```csharp
// ---- 面板与描边 ----
PanelTop   = #2A3444   // 面板渐变顶
PanelMid   = #1B2330   // 面板渐变中
PanelBot   = #222C3B   // 面板渐变底
StrokeC    = #3A4A63   // 通用描边
SlateDeep  = #1C2532   // 深板岩（芯片底、次级底）

// ---- 主题强调色 ----
Cyan       = #35E0FF   // 主色（青）—— 通用强调、可交互
Gold       = #FFC94D   // 金 —— 金币、胜利、星级
Red        = #FF4D5E   // 红 —— 生命、失败、危险
Fire       = #FF7A29   // 橙 —— 火焰塔、警示
Ice        = #7DE8FF   // 冰白 —— 水晶、减速
Purple     = #7C5CFF   // 紫 —— Pierce/Laser 塔型标识
Steel      = #9FB3C8   // 钢 —— 次要文字、金属件
SteelDark  = #5E7396   // 暗钢 —— 金属阴影、次级描边

// ---- 辅助 ----
BaseBlue   = #2E4A66   // 塔基座
DotLight   = #C9D6E8   // 高光点
BoxDark    = #2A3138   // 机械箱体
BoxRib     = #55627A   // 箱体棱线

// ---- 文字 ----
TextPrimary   = #E8F0FA   // 主文字（近白）
TextSecondary = #9FB3C8   // 次文字（钢）
TextTertiary  = #5E7396   // 三级文字（暗钢）
TextOnAccent  = #DFFAFF   // 青色按钮上的文字
```

### 2.2 三级明度阶梯（**新增，用于拉开层级**）

当前工程所有面板挤在同一明度，导致"弹窗糊在 HUD 上"。新增界面**必须**遵循以下阶梯：

| 层级 | 用途 | 色值 | 说明 |
|---|---|---|---|
| L0 战场底 | 棋盘最底层 | `#0D1119` | 最暗 |
| L1 遮罩 | 弹窗背后的压暗层 | `rgba(6,9,14,0.72)` | 原为 `0.55`，加深 |
| L2 全屏页底 | Splash/Loading/MainMenu 的整页底 | `#080B12` | 近黑，带星空 |
| L3 面板 | 弹窗主体 | `#1E2939` | 比按钮亮 |
| L4 卡片 | 面板内的子卡片 | `#252F40` | 最亮 |

### 2.3 字号规范（1920×1080 基准）

现有 `UIPrefabBuilder` 已有 `BigFontSize`（标题）、`FullScreenTitleFontSize`（整页标题）。统一口径：

| 用途 | 字号 | 字重（TMP） | 色 |
|---|---|---|---|
| 整页大标题（主菜单 Logo 副标题） | 96 | Bold | Cyan + 外发光 |
| 整页标题（选择关卡 / 图鉴） | 64 | Bold | TextPrimary |
| 弹窗标题 | 48 | Bold | TextPrimary |
| 卡片标题 | 40 | SemiBold | Cyan |
| 正文 / 按钮 | 32 | Regular | TextPrimary |
| 数值（金币、伤害、价格） | 34 | Bold | Gold |
| 次要说明 | 26 | Regular | TextSecondary |
| 极小标注（版本号、版权） | 22 | Regular | TextTertiary |

> ⚠️ **数值一律加 2px 深色描边**：`SiYuanSongTi SDF - Outline.mat`（`Assets/Font/`）已存在，挂上即可。深色背景上无描边的细体宋体数字清晰度不足。

### 2.4 九宫格与切角

| 资产 | 尺寸 | 切角 | 发光 | border | 消费方式 |
|---|---|---|---|---|---|
| `UI_Panel_Cyan/Gold/Red` | 64×64 | 14 | 6 | 22 | `Image.type = Sliced` |
| `UI_Btn_Primary/Secondary` | 48×48 | 12 | 5/3 | 17 | Sliced |
| `UI_Chip_Gold/HP/Neutral` | 40×40 | 8 | 4 | 12 | Sliced |
| `UI_Tip_Bar` | 48×48 | 10 | 5 | 16 | Sliced |
| `UI_TowerBtn_Frame` | 48×48 | 10 | 3 | 16 | Sliced |

⚠️ **硬约束**：`border ≥ 切角 + 发光半径`，否则四角在拉伸时变形。

### 2.5 面板顶部色条（**新增规范**）

为让玩家一眼区分弹窗性质，所有弹窗在 Panel 顶部加一条 **4px 高、铺满面板宽、圆角 2px** 的色条：

| 弹窗性质 | 色条颜色 |
|---|---|
| 普通 / 信息 | Cyan `#35E0FF` |
| 成功 / 胜利 / 解锁 | Gold `#FFC94D` |
| 失败 / 危险 / 删除 | Red `#FF4D5E` |
| 警示 / 确认 | Fire `#FF7A29` |

---

## 3. 新增界面详细规格

> **通用骨架**：以下所有新增界面，除 A1/A2/A3/B1 为整页口径外，其余均走 `CreateDialogShell(rootName, title, panelSize, report, out panel, stretchInset)`。
> - 整页口径：`stretchInset = 0f`，Panel 铺满屏幕，标题 64 号
> - 弹窗口径：`stretchInset = -1f`，Panel 居中，标题 48 号

---

### A1 · SplashView 开屏页

**用途**：启动后 1.5 秒品牌过场。当前工程启动直接黑屏，本界面消除"第一印象空白"。

**类型**：整页（`stretchInset = 0f`）

**节点树**：

```
SplashView                     [RectTransform, 铺满, +SplashView.cs]
├─ Bg                          [Image, 铺满, #080B12]
│  └─ Starfield                [RawImage, 铺满, 星点纹理, α=0.35]
├─ Vignette                    [Image, 铺满, 径向暗角, 中心透明→边缘#0B0E14 0.66]
├─ Logo                        [Image, 居中, 480×480, y=+60]
├─ Title                       [TMP, 居中, 900×120, y=-160, 96号, Cyan, Bold]
│                             内容："坚守阵地"
├─ Subtitle                    [TMP, 居中, 900×48, y=-260, 28号, TextSecondary]
│                             内容："FREEDOM TOWER"
├─ Version                     [TMP, 右下, anchor(1,0), offset(-40,40), 320×36, 22号, TextTertiary]
│                             内容："v1.0.0 (Build 20261009)"
└─ LoadingDots                 [TMP, 居中, y=-380, 400×40, 26号, Steel]
                              内容："正在启动..."（文字用省略号动画，不用转圈图）
```

**动画**（用 DOTween，时长见括号）：
1. `Bg` α 从 0 → 1（0.4s，EaseOut）
2. `Logo` scale 从 0.85 → 1.0 且 α 0 → 1（0.6s，EaseOutBack）
3. `Title` α 0 → 1（0.5s，延迟 0.3s）
4. `Subtitle` / `Version` α 0 → 1（0.5s，延迟 0.5s）
5. **常驻 1.5s 后**自动进 LoadingView（由 `Launcher` 控制，不由此界面自己切）

**验收**：
- [ ] 启动后立刻可见，无黑屏帧
- [ ] 1.5s ± 0.2s 后自动切换到 LoadingView
- [ ] `Version` 文字从 `Application.version` 读取（**不得硬编码**）

---

### A2 · LoadingView 资源加载进度

**用途**：显示 `ResLoader.Init` + `Configs.LoadAsync` 的真实进度。当前这段是异步的黑屏静默期。

**类型**：整页（`stretchInset = 0f`）

**节点树**：

```
LoadingView                    [RectTransform, 铺满, +LoadingView.cs]
├─ Bg                          [Image, 铺满, #080B12]
│  └─ Starfield                [RawImage, 铺满, 星点, α=0.25]
├─ Vignette                    [Image, 铺满, 径向暗角]
├─ Logo                        [Image, 居中, 240×240, y=+160]
├─ StatusText                  [TMP, 居中, 1200×56, y=-40, 32号, TextPrimary, Center]
│                             内容：动态，如"正在加载配置表..."
├─ ProgressBar                 [RectTransform, 居中, 900×24, y=-140]
│  ├─ Track                    [Image, Sliced(UI_Chip_Neutral), 铺满, #131A26]
│  ├─ Fill                     [Image, Sliced(UI_Btn_Primary), anchor(0,0.5),
│  │                           pivot(0,0.5), 宽度随进度 0→900, 色 Cyan]
│  └─ Glow                     [Image, Sliced(UI_Btn_Primary), 同 Fill, α=0.4, 用于发光尾]
├─ PercentText                 [TMP, 居中, 400×48, y=-190, 34号, Gold, Bold, 描边]
│                             内容："0%"（整数，无小数）
└─ TipText                     [TMP, 居中, 1400×44, y=-300, 26号, TextSecondary]
                              内容：随机游戏提示（见下方提示池）
```

**进度映射规则**（`Launcher` 需要改造，见 §5.1）：

| 阶段 | 权重 | StatusText |
|---|---|---|
| `ResLoader.Init` 开始 | 0% | "正在初始化资源系统..." |
| 资源系统就绪 | 30% | "正在加载配置表..." |
| `Configs.LoadAsync` 完成 | 90% | "正在准备关卡数据..." |
| 进入下一界面 | 100% | "准备完成" |

⚠️ **进度条必须补间平滑**：真实进度是跳变的（0 → 30 → 90），直接赋值会"啪"地跳。用 DOTween 把 `Fill` 宽度做 0.3s `EaseOut` 补间，让数字滚动自然。

**游戏提示池**（`TipText` 随机取一条）：

```
"可以在任意空地建塔，路径会实时重算"
"塔没有目标时绝不会浪费火力"
"出售塔可退回 70% 的累计投入"
"减速塔能大幅提升周围所有塔的输出"
"飞行怪会无视地面路径，注意覆盖对空"
"回合之间有 5 秒布防时间，也可以立即开始"
"穿透塔能一次打穿一整列敌人"
```

**验收**：
- [ ] 进度条与真实加载阶段对应，不早于/晚于实际完成
- [ ] 进度数字为整数，滚动平滑无跳变
- [ ] 加载失败时 `StatusText` 变 Red 并显示错误原因，**不得静默卡住**

---

### A3 · HotUpdateView 热更新下载 ⚠️ 上线阻塞项

**用途**：YooAsset 的版本比对与资源下载。**当前工程完全没有实现**（`YooAssetResLoader` 只做到 `LoadPackageManifestAsync`）。

**类型**：整页（`stretchInset = 0f`）

**节点树**：

```
HotUpdateView                  [RectTransform, 铺满, +HotUpdateView.cs]
├─ Bg                          [Image, 铺满, #080B12]
│  └─ Starfield                [RawImage, 铺满, α=0.25]
├─ Vignette                    [Image, 铺满, 径向暗角]
├─ Title                       [TMP, 居中, 900×80, y=+220, 56号, TextPrimary, Bold]
│                             内容："资源更新"
├─ PhaseText                   [TMP, 居中, 1200×56, y=+100, 32号, TextPrimary]
│                             内容：见下方阶段表
├─ ProgressBar                 [RectTransform, 居中, 900×28, y=0]
│  ├─ Track                    [Image, Sliced(UI_Chip_Neutral), 铺满]
│  ├─ Fill                     [Image, Sliced(UI_Btn_Primary), anchor(0,0.5), Cyan]
│  └─ Glow                     [Image, 同 Fill, α=0.4]
├─ PercentText                 [TMP, 居中, 400×56, y=-60, 40号, Cyan, Bold, 描边]
│                             内容："0%"
├─ SizeText                    [TMP, 居中, 1200×40, y=-120, 26号, TextSecondary]
│                             内容："已下载 0.0 MB / 0.0 MB"
├─ SpeedText                   [TMP, 居中, 1200×40, y=-160, 24号, TextSecondary]
│                             内容："速度 0.0 MB/s　剩余约 --:--"
├─ DetailText                  [TMP, 居中, 1200×40, y=-206, 22号, TextTertiary]
│                             内容："文件 0/0　失败 0"
├─ BtnGroup                    [RectTransform, 居中, 900×88, y=-300]
│  ├─ PauseBtn                 [Button, 240×80, x=-160, "暂停"]
│  ├─ ResumeBtn                [Button, 240×80, x=-160, "继续", 默认隐藏]
│  └─ RetryBtn                 [Button, 240×80, x=+160, "重试", 默认隐藏]
└─ FailText                    [TMP, 居中, 1400×60, y=-390, 26号, Red, 默认隐藏]
                              内容："下载失败：<原因>" + "网络异常，请检查网络后重试"
```

**阶段状态机**（`HotUpdateView.cs` 必须实现）：

| 阶段 | PhaseText | 进度条 | 按钮 |
|---|---|---|---|
| `RequestVersion` | "正在检查更新..." | 不确定态（左右滑动动画） | 全隐藏 |
| `CompareVersion` | "正在比对资源版本..." | 不确定态 | 全隐藏 |
| `NoUpdateNeeded` | "资源已是最新" | 100% | 显示"进入游戏"（复用 RetryBtn，文案改） |
| `Downloading` | "正在下载资源..." | 0→100% 实测 | 显示"暂停" |
| `Paused` | "已暂停" | 保持 | 显示"继续" |
| `DownloadFailed` | "下载失败" | 保持 | 显示"重试"，红色 FailText |
| `Verifying` | "正在校验文件..." | 不确定态 | 全隐藏 |
| `Done` | "更新完成" | 100% | 自动进游戏（0.5s 后） |

**必须实现的 YooAsset API**（`YooAssetResLoader.cs` 新增方法）：

```csharp
// ① 版本比对
public IEnumerator CheckUpdateCo(Action<bool> onDone);   // 返回"是否需要更新"

// ② 下载器
public IEnumerator DownloadCo(
    Action<int, int> onProgress,        // (已下载数, 总数)
    Action<long, long> onBytes,         // (已下载字节, 总字节)
    Action<string> onError,
    Action onDone);

// ③ 暂停/恢复（YooAsset 的 DownloaderOperation 自带）
public void PauseDownload();
public void ResumeDownload();
```

⚠️ **三步初始化契约不可破坏**：`InitializePackageAsync` → `RequestPackageVersionAsync` → `LoadPackageManifestAsync`（**最后才 `SetActiveManifest`**）。新增的版本比对必须在 `RequestPackageVersionAsync` 之后、`LoadPackageManifestAsync` **之前**插入。

**验收**：
- [ ] 有更新时：进度条走满 → 自动进游戏；无更新时：立刻跳转
- [ ] 断网时：`RetryBtn` 可点，重试后能恢复
- [ ] 下载中按"暂停"：网络请求停止，进度保持；按"继续"能续传
- [ ] 下载字节数与真实文件大小一致（±1%）
- [ ] ⚠️ **不出现 `Active package manifest not found.`**（三步契约的验证点）

---

### B1 · MainMenuView 主菜单

**用途**：开机入口页。当前直接进选关，没有"游戏标题 + 功能入口"的门面。

**类型**：整页（`stretchInset = 0f`）

**节点树**：

```
MainMenuView                   [RectTransform, 铺满, +MainMenuView.cs]
├─ Bg                          [Image, 铺满, #080B12]
│  └─ Starfield                [RawImage, 铺满, α=0.4]
├─ Vignette                    [Image, 铺满, 径向暗角]
├─ Deco                        [RectTransform, 铺满]  ← 装饰层，若干细线/圆环
│  ├─ Line_H                   [Image, 1920×2, 居中, α=0.15, Cyan]
│  └─ Ring                     [Image, 700×700, 右侧 x=+520, α=0.08, Cyan, 圆环图]
├─ Logo                        [Image, 居中, 380×380, y=+270]
├─ Title                       [TMP, 居中, 1000×130, y=-70(=470基线), 88号, Cyan, Bold, 发光]
│                             内容："坚守阵地"
├─ Subtitle                    [TMP, 居中, 1000×44, y=-16(=524基线), 26号, TextSecondary]
│                             内容："FREEDOM TOWER · 单机塔防"
├─ BtnGroup                    [RectTransform, 居中, 560×446, y=-80]  ← 组区 y 560..1006
│  ├─ StartBtn                 [Button, 480×92, y_top=560,  "开始游戏", Primary]
│  ├─ CodexBtn                 [Button, 480×92, y_top=678,  "防御塔图鉴", Secondary]
│  ├─ SettingBtn               [Button, 480×92, y_top=796,  "设置", Secondary]
│  └─ QuitBtn                  [Button, 480×92, y_top=914,  "退出游戏", Secondary]
├─ PlayerStat                  [RectTransform, 左上, anchor(0,1), offset(48,-120), 416×112]
│  ├─ StatBg                   [Image, Sliced(UI_Panel_Cyan), 铺满, α=0.85]
│  ├─ StarText                 [TMP, 360×40, y=+30, 30号, Gold]
│  │                          内容："12/24"
│  └─ ClearText                [TMP, 360×40, y=-30, 28号, TextSecondary]
│                             内容："已通关 4/8"
└─ Version                     [TMP, 右下, anchor(1,0), offset(-48,38), 240×32, 22号, TextTertiary]
```

> ⚠️ **v2 版式修正**：v1 版把按钮组中心放在 y=-140（组底 y_svg=1072），第 4 颗按钮距画布底仅 8px 且被底部标注带压住；现已整体上移，**组区固定 y_svg 560..1006**，底部留 74px 安全边距。修改版式时必须保证 `QuitBtn` 底边 ≤ 1006。

**行为**：
- `StartBtn` → 关闭主菜单，进入 `SelectView`
- `CodexBtn` → 打开 `TowerCodexView`
- `SettingBtn` → 打开 `SettingView`
- `QuitBtn` → 打开 `ConfirmView` 二次确认后 `Application.Quit()`

**启动流程改造**（`GameFlowManager.OnConfigLoaded`）：
```
现在：配置加载完 → 直接 OpenSelect()
改为：配置加载完 → 打开 MainMenuView（首次）
      MainMenuView 点"开始游戏" → OpenSelect()
```
⚠️ 保留 `startLevelId > 0` 的调试直进逻辑（它跳过选关，是 F5 快速调试通路）。

**验收**：
- [ ] 四个按钮均可点，点击音效自动生效（`UiClickSfx` 代管）
- [ ] 星级/通关数从 `SaveManager` 实时读取，**不得硬编码**
- [ ] 退出前有二次确认

---

### B2 · TowerCodexView 塔图鉴

**用途**：展示 5 种塔的定位、形态、Lv.1~Lv.3 数值。⚠️ **设计稿 `Docs/ui_mockups/14_TowerCodex.svg` 已存在**，本策划案将其落为可执行规格。

**类型**：整页（`stretchInset = 0f`），横向 5 张竖卡，复用 `LoopListView2`（与 `SelectView` 同款）

**节点树**：

```
TowerCodexView                 [RectTransform, 铺满, +TowerCodexView.cs]
├─ Bg                          [Image, 铺满, #080B12]
├─ Vignette                    [Image, 铺满, 径向暗角]
├─ Panel                       [Image, Sliced(UI_Panel_Cyan), 铺满(inset=0)]
│  ├─ Title                    [TMP, 居中顶, y=-64, 64号, "防御塔图鉴"]
│  ├─ List                     [RectTransform, 1300×640, y=+10, +RectMask2D +ScrollRect]
│  │  └─ Viewport              [RectTransform, 视口宽 460, pivot.x=0]  ← 见下方几何约束
│  │     └─ Content            [RectTransform, +LoopListView2, 无 LayoutGroup]
│  ├─ LeftBtn                  [Button, 132×160, x=-860, y=+10, "<"]   ← 中心 x_svg=100
│  ├─ RightBtn                 [Button, 132×160, x=+860, y=+10, ">"]   ← 中心 x_svg=1820
│  ├─ PageDot                  [TMP, 居中, y=-330, 600×44, 28号, Steel]
│  │                          内容："1 / 5"
│  └─ CloseBtn                 [Button, 340×84, 居中, y=-430, "返回"]
└─ TowerCodexItem              [独立 prefab: Assets/Prefabs/UI/TowerCodexItem.prefab]
```

> ⚠️ **箭头位置硬约束（v2 修正）**：卡片列几何为 `step 530`，中卡 730..1190，两张邻卡 peek 至 **200..660** 与 **1260..1720**。
> 因此左右箭头**必须**落在 peek 区之外 —— 即 `x_svg ≤ 200` 或 `x_svg ≥ 1720`。
> v1 把箭头放在 1680..1840，正好压住右邻卡（"水晶塔"标题与数值被挡），已改为 **34..166 / 1754..1886**。
> 排版检查：`python .workbuddy/tools/check_svg_layout.py 19`

**条目卡片规格**（`TowerCodexItem.prefab`，460×640）：

```
TowerCodexItem                 [RectTransform, 460×640, +TowerCodexItem.cs]
├─ Body                        [RectTransform, 铺满]  ← 缩放/淡化挂这里，不挂根节点
│  ├─ CardBg                   [Image, Sliced(UI_Panel_Cyan), 铺满, #1E2939]
│  ├─ TopBar                   [Image, 铺满宽×4, 顶部, 塔型主题色]
│  ├─ Icon                     [Image, 300×300, 居中, y=+170]
│  ├─ TypeName                 [TMP, 400×52, y=-10, 40号, Cyan, Bold, Center]
│  ├─ Role                     [TMP, 400×40, y=-68, 26号, TextSecondary, Center]
│  ├─ Divider                  [Image, 360×1, y=-104, α=0.3, StrokeC]
│  ├─ StatGroup                [RectTransform, 400×200, y=-210]
│  │  ├─ DpsRow                 [TMP, 380×36, y=+60, 26号]
│  │  │                        "伤害　 12"
│  │  ├─ RangeRow              [TMP, 380×36, y=+20, 26号]
│  │  │                        "射程　 3.0 格"
│  │  ├─ SpeedRow              [TMP, 380×36, y=-20, 26号]
│  │  │                        "攻速　 0.4 秒"
│  │  └─ PriceRow              [TMP, 380×36, y=-60, 26号, Gold]
│  │                           "造价　 25 金币"
│  └─ DescText                 [TMP, 380×80, y=-380, 24号, TextSecondary, 自动换行]
│                             一段 30 字以内的定位描述
└─ PageDot                     [TMP, 卡片底部页码小字]
```

**5 塔数据映射**（从 `tbtowerinfo` L1 行读取，**不得硬编码**）：

| 卡位 | 塔型 | 主题色 | 图标资产 | 定位文案 |
|---|---|---|---|---|
| 1 | Normal | Cyan `#35E0FF` | `UI_TowerIcon_Normal` | 单体速射，性价比基准 |
| 2 | Power | Fire `#FF7A29` | `UI_TowerIcon_Power` | 范围爆炸，清群核心 |
| 3 | Retard | Ice `#7DE8FF` | `UI_TowerIcon_Retard` | 减速光环，增益全队 |
| 4 | Pierce | Purple `#7C5CFF` | `UI_TowerIcon_Pierce` | 直线穿透，一列贯穿 |
| 5 | Laser | Purple `#7C5CFF` | `UI_TowerIcon_Laser` | 高单伤，专克重甲 |

**几何约束**（复用 `SelectView` 踩过的坑，**必须照抄参数**）：
- 条目宽 **必须 ≡ 视口宽**（460），否则首/末卡永远偏心
- **视口比可视区窄**：可视区 1300，视口 460 → 邻卡可见
- **`Viewport.pivot.x` 预置为 0**（`AdjustPivot` 会强改，用 `offsetMin/offsetMax` 描述矩形）
- `InitListView` 只能调一次 → `_listInited` 守护
- 点击回调**只在 `IsInitHandlerCalled` 首次为 false 时挂**
- 首次居中延后到第一帧 `LateUpdate`

**验收**：
- [ ] 5 张卡横向可滑，首卡（Normal）与末卡（Laser）均**精确居中**（偏差 0px）
- [ ] 卡片数据与 `tbtowerinfo` 一致
- [ ] 左右箭头到头自动置灰
- [ ] 滚动一圈后点击，事件仍只触发 1 次

---

### B3 · MonsterCodexView 怪物图鉴

**用途**：展示怪物属性与弱点。`EnemyConfig` 已有 `Desc` / `Speed` / `Hp` / `Armor` / `IsFlying` 字段，数据齐备。

**类型**：整页网格（`stretchInset = 0f`），**用 Grid + 分页**（怪物数量多，不适合横向画廊）

**节点树**：

```
MonsterCodexView               [RectTransform, 铺满, +MonsterCodexView.cs]
├─ Bg / Vignette / Panel       [同 TowerCodexView]
├─ Title                       [TMP, 居中, y_svg=88 基线, 64号, "怪物图鉴"]      ← Zone A 40..120
├─ FilterBar                   [RectTransform, 居中, 736×76, y_svg=152..228]   ← Zone B
│  ├─ AllBtn                   [Button, 160×68, x=-360, "全部"]   ← 已被选中态
│  ├─ GroundBtn                [Button, 160×68, x=-180, "地面"]
│  ├─ AirBtn                   [Button, 160×68, x=0,    "飞行"]
│  ├─ HeavyBtn                 [Button, 160×68, x=+180, "重甲"]
│  └─ CountText                [TMP, 200×40, x=+430, 26号, "共 63 种"]
├─ Grid                        [RectTransform, 1560×552, y_svg=266..818, +GridLayoutGroup]
│                             cellSize=(236,252), spacing=(24,24), constraint=FixedColumn(6)
│                             ⚠ 底衬外扩 12：x 192..1752（不改卡片坐标）
├─ PrevBtn                     [Button, 132×160, x=-860, y_svg 中心=530, "<"]  ← 34..166
├─ NextBtn                     [Button, 132×160, x=+860, y_svg 中心=530, ">"]  ← 1754..1886
├─ PageText                    [TMP, 居中, 600×44, y_svg=858 基线, 28号, "1 / 4"]  ← Zone E
└─ CloseBtn                    [Button, 340×84, 居中, y_svg=890..974, "返回"]      ← Zone F
```

> ⚠️ **竖向 Zones 硬划分（v2 修正）**：本界面元素最多，必须按 y_svg 分段，跨段即重叠：
> `标题 40..120` ｜ `筛选 152..228` ｜ `网格底衬 266..818` ｜ `分页 830..880` ｜ `返回 890..974`
> v1 用 6×4=24 格，网格底 1058 顶到画布边缘还压住了筛选栏与返回键；**已改为 6×2=12 格**，每页 12 只。
> 排版检查：`python .workbuddy/tools/check_svg_layout.py 20`

**条目卡片**（`MonsterCodexItem.prefab`，236×252）：

```
MonsterCodexItem               [236×252, +MonsterCodexItem.cs]
└─ Body                        [铺满]
   ├─ CardBg                   [Image, Sliced(UI_Chip_Neutral), 铺满]
   ├─ Icon                     [Image, 124×124, 居中, y=+50]
   ├─ NameText                 [TMP, 216×40, y=-34, 28号, TextPrimary, Center]
   ├─ TagRow                   [TMP, 216×30, y=-66, 22号, Cyan]
   │                           "地面" / "飞行" / "重甲"
   └─ StatRow                  [TMP, 216×30, y=-96, 22号, TextSecondary]
                               "HP 95  速 1.6"
```

**交互**：点卡片 → 弹出详情浮层（复用 `ConfirmView` 的骨架，显示 `Desc` 全文 + 完整数值）

**验收**：
- [ ] 筛选按钮过滤生效
- [ ] 分页正确，**每页 6×2=12 张**
- [ ] 所有卡片、筛选按钮、返回键、翻页箭头**两两零重叠**（`check_svg_layout.py` 通过）
- [ ] 数据全部来自 `EnemyConfig`，无硬编码

---

### B4 · LevelDetailView 关卡详情

**用途**：在选关界面点关卡时，先展示"几回合、什么怪、多少波、历史最佳"，再确认进入。

**类型**：弹窗（`stretchInset = -1f`，panelSize `1000×900`）

**节点树**：

```
LevelDetailView                [RectTransform, 铺满, +LevelDetailView.cs]
├─ Bg                          [Image, 铺满, rgba(6,9,14,0.72)]
└─ Panel                       [Image, Sliced(UI_Panel_Gold), 1000×900]  ← y_svg 90..990
   ├─ TopBar                   [Image, 1000×24, 顶部(y_svg 90..114), 状态色条]  ← 已通关=Gold
   ├─ InnerStroke              [Image, 980×860, inset, α=0.2, Cyan 描边]
   ├─ Title                    [TMP, 940×64, y_svg=146 基线, 48号, "第 3 关"]
   ├─ LevelName                [TMP, 940×48, y_svg=196 基线, 30号, TextSecondary, Center]
   ├─ StarRow                  [RectTransform, 400×80, y_svg 218..285]  ← 3 星 + "历史最佳 2 星"
   │  ├─ Star1/2/3             [Image, 62×62, x=860/960/1060, UI_Star_On/Off]
   ├─ Divider1                 [Image, 880×1, y_svg=302, α=0.3]
   ├─ InfoGrid                 [RectTransform, 880×174, y_svg 322..496, +GridLayoutGroup]
   │                          cellSize=(430,50), spacing=(20,12), 2列×3行
   │                          「回合数 5」「波次 5」「初始金币 380」「初始生命 20」
   │                          「难度 ★☆☆」「最佳用时 --:--」
   ├─ Divider2                 [Image, 880×1, y_svg=522, α=0.3]
   ├─ EnemyPreview             [RectTransform, 880×110, y_svg 540..650]
   │  ├─ Label                 [TMP, 880×32, y_svg=556, 24号, TextSecondary, "本关出现怪物"]
   │  └─ IconRow               [RectTransform, 880×64, y_svg 570..634]
   │                          最多 7 个小图标，64×64，间距 12
   ├─ Divider3                 [Image, 880×1, y_svg=660, α=0.3]
   ├─ PlayBtn                  [Button, 560×88, 居中, y_svg 690..778, "开始挑战", Primary]
   ├─ ReplayBtn                [Button, 300×76, x=-160, y_svg 790..866, "从头重打", Secondary]
   └─ CloseBtn                 [Button, 300×76, x=+160, y_svg 790..866, "返回", Secondary]
```

> ⚠️ **尺寸修正历史**：v1 写 `1000×760` → 实测容不下（InfoGrid 第 3 行超底 52px）→ 改 `1000×860` → 最终定稿 **`1000×900`**（y_svg 90..990）。
> **AI 执行时以本节的 y_svg 分段为准**：`TopBar 90..114` ｜ `标题 130..206` ｜ `星级 218..285` ｜ `分割 302`
> ｜ `信息格 322..496` ｜ `分割 522` ｜ `怪物预览 540..650` ｜ `分割 660` ｜ `按钮 690..866`。
> 最底按钮 y_svg=866 < 面板底 990，留 124px 余量。排版检查：`python .workbuddy/tools/check_svg_layout.py 21`

**触发改造**（`SelectView`）：
```
现在：点居中卡片 → 直接 StartLevel
改为：点居中卡片 → 打开 LevelDetailView → 点"开始挑战" → StartLevel
      （非居中卡片仍是"先滑到中间"，滑到位后再开详情）
```
⚠️ 保留一个跳过开关（`SelectView.skipDetail = true`）供调试。

**验收**：
- [ ] 数据全部来自 `tbsceneinfo` / `tbsround` / `SaveManager`，无硬编码
- [ ] 未解锁关卡不显示"开始挑战"，只显示"返回"
- [ ] 从详情进关后，返回选关时详情已关闭

---

### C1 · SellConfirmView 出售确认

**用途**：⚠️ `GameFlowManager.cs:1011` 明写"二次确认由面板负责（美术补齐后加）；这里直接执行出售"。**当前点出售直接卖掉，无法反悔。**

**类型**：弹窗（`stretchInset = -1f`，panelSize `800×620`）

**节点树**：

```
SellConfirmView                [RectTransform, 铺满, +SellConfirmView.cs]
├─ Bg                          [Image, 铺满, rgba(6,9,14,0.72)]
└─ Panel                       [Image, Sliced(UI_Panel_Red), 800×620]  ← y_svg 230..850
   ├─ TopBar                   [Image, 800×24, 顶部(y_svg 230..254), Fire #FF7A29]
   ├─ Title                    [TMP, 740×56, y_svg=316 基线, 48号, "确认出售？"]
   ├─ TowerIcon                [Image, 多节点组合 100×100, 居中, y_svg=382]
   ├─ TowerName                [TMP, 740×44, y_svg=462 基线, 32号, TextPrimary, Center]
   ├─ WarnText                 [TMP, 700×72, y_svg 528..562, 27号, Fire, 自动换行, Center]
   │                          "出售后将退回 70% 的累计投入\n且无法撤销"
   ├─ RefundRow                [RectTransform, 480×56, y_svg=630 基线]
   │  ├─ RefundLabel           [TMP, 240×56, x=-100, 30号, TextSecondary, "退回金币"]
   │  └─ RefundValue           [TMP, 240×56, x=+80,  34号, Gold, Bold, Center]
   ├─ ConfirmBtn               [Button, 240×88, x=-260, y_svg 706..794, "确认出售", Primary(Danger)]
   └─ CancelBtn                [Button, 240×88, x=+260, y_svg 706..794, "取消", Secondary]
```

> ⚠️ **布局硬约束（v2 修正）**：两按钮**并排同 y**，`ConfirmBtn x=-260`、`CancelBtn x=+260`。
> 两按钮区必须完整落在面板内：`按钮底 y_svg=794 < 面板底 850`。
> v1 用 `800×480` 面板且按钮放在 `y=-300`（y_svg=810），**越过面板底 30px**；现已把面板加高到 **620**。
> "取消"在右（正向位置）以降低误触。排版检查：`python .workbuddy/tools/check_svg_layout.py 22`

**接入**（`GameFlowManager.OnTowerSellRequest`）：
```csharp
private void OnTowerSellRequest(BaseTower tower)
{
    // 改为打开确认弹窗，而不是直接 Sell
    SellConfirmView view = UIManager.Instance.Open<SellConfirmView>(
        SellConfirmView.LogicalName, UILayout.NormalPanel);
    view.Show(tower);
}
// SellConfirmView 确认后 → 发 TowerSellConfirmEvent → 这里才真正 TowerManager.Sell(tower)
```

**验收**：
- [ ] 点出售**不再立即卖出**，必须先经过确认
- [ ] 退回金额与 `SellRefundRate`（0.7）× 累计投入一致
- [ ] 点取消后塔完好无损

---

### C2 · ConfirmView 通用确认弹窗

**用途**：承载所有危险操作的二次确认（重置存档、退出游戏、删除等）。避免每个界面各写一套。

**类型**：弹窗（`stretchInset = -1f`，panelSize `760×560`，**高随正文行数自适应**）

**节点树**：

```
ConfirmView                    [RectTransform, 铺满, +ConfirmView.cs]
├─ Bg                          [Image, 铺满, rgba(6,9,14,0.72)]
└─ Panel                       [Image, Sliced(UI_Panel_Cyan), 760×560]  ← y_svg 260..820
   ├─ TopBar                   [Image, 760×24, 顶部(y_svg 260..284), 按 ConfirmType 变色]
   ├─ Title                    [TMP, 700×56, y_svg=356 基线, 44号, TextPrimary, Center]
   ├─ BodyText                 [TMP, 660×120, y_svg 444..488, 28号, TextSecondary, 自动换行, Center]
   ├─ DangerIcon               [Image, 96×96, 居中, y_svg=556]
   ├─ ConfirmBtn               [Button, 240×88, x=-220, y_svg 664..752, "确定", Primary]
   └─ CancelBtn                [Button, 240×88, x=+220, y_svg 664..752, "取消", Secondary]
```

> ⚠️ **面板高度自适应规则**：`panelSize.y = 400 + BodyText.实际行数 × 44`，再向上取整到 20 的倍数；最小 480、最大 700。
> 两按钮与面板底的间距固定 ≥ 68px。v1 定 `760×440` 时按钮区压出面板（越界 30px），已统一到 **560**。
> 顶部色条联动：`Info #35E0FF` / `Success #FFC94D` / `Danger #FF4D5E` / `Warning #FF7A29`。
> 排版检查：`python .workbuddy/tools/check_svg_layout.py 22`

**对外 API**（关键：做成通用组件，而不是一次性的）：

```csharp
public enum ConfirmType { Info, Success, Danger, Warning }

public static void Show(
    string title,
    string body,
    ConfirmType type,
    Action onConfirm,
    string confirmLabel = "确定",
    string cancelLabel = "取消");
```

**接入点**（改造现有逻辑）：
| 位置 | 现状 | 改为 |
|---|---|---|
| `SettingView.ResetBtn` 重置存档 | 直接重置 | `ConfirmView.Show("重置存档", "将清空所有关卡进度与星级，此操作不可撤销。", Danger, doReset)` |
| `MainMenuView.QuitBtn` 退出游戏 | 无 | `ConfirmView.Show(...)` |
| `LevelDetailView` 未解锁点进入 | Tips 提示 | 保持 Tips（信息量小，无需弹窗） |

**验收**：
- [ ] 重置存档前必须确认
- [ ] `type` 切换时顶部色条与按钮色正确联动
- [ ] 弹窗关闭后 `onConfirm` 只执行一次

---

### C3 · 屏幕震动反馈

**用途**：⚠️ `GlobalConfig.ShakeAmplitude` / `ShakeDurationSec` **已定义但全工程无消费方**。

**实现位置**：`Assets/Scripts/Camera/CameraController.cs` 新增震动叠加层。

**触发时机**：

| 事件 | 振幅系数 | 说明 |
|---|---|---|
| 怪物漏怪到终点 | `ShakeAmplitude × 1.0` | 最需要"惩罚感" |
| 玩家生命归零 | `ShakeAmplitude × 1.5` | 失败 |
| 高等级塔（L3）开火命中 | `ShakeAmplitude × 0.15` | 轻微，不能烦 |
| Power 塔爆炸命中 | `ShakeAmplitude × 0.3` | 中 |

**实现要点**：
- 震动是**相机局部位移**，不是改 `transform.position` 的世界值（那会被 `FitBoard` 覆盖）
- 用 `unscaledDeltaTime` 衰减（暂停时不应继续抖）
- **必须与 `CameraController.FitBoard` 的相机位置叠加**，不能互相覆盖
- 震动幅度受 `GlobalConfig.ShakeAmplitude == 0` 短路（关掉时零开销）

**验收**：
- [ ] 漏怪时画面轻微抖动，0.2s 内衰减到 0
- [ ] 连续漏怪不产生"抖动叠加失控"
- [ ] `ShakeAmplitude = 0` 时完全无抖动

---

### C4 · 切关 Loading 遮罩

**用途**：`InitLevel` 是同步的，大关卡建棋盘时可能卡顿一两帧。需要一个轻量遮罩。

**类型**：覆盖层（层 `NormalPanel` 之上，但**不新增 UILayout 枚举**，用一个高 `Canvas.sortingOrder` 的独立 Canvas）

**规格**：
- 全屏黑底 `#080B12`，α 从 0 → 0.9（0.15s）
- 中央一个细环形进度（或用 `LoadingDots` 三点动画）
- 文案："正在进入第 N 关..."
- **必须是 `unscaled` 时间驱动**（切关时 `timeScale` 可能为 0）
- 在 `InitLevel` 首帧显示、末帧隐藏

**验收**：
- [ ] 切关过程无"白屏/黑屏闪帧"
- [ ] 遮罩在关卡就绪后 0.2s 内消失
- [ ] 不与 `TipsView` 抢层级

---

## 4. 效果图规范（SVG）

### 4.1 坐标换算（**与既有 14 张效果图一致**）

```
SVG 坐标 = 画布坐标 + 偏移
  x_svg = 960 + X      （X 为以画布中心为原点的横坐标）
  y_svg = 540 − Y      （Y 为以画布中心为原点的纵坐标，Y 向上为正）
```

### 4.2 SVG 模板结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- NN_ViewName.svg — 说明【正式版·深色科幻】
     几何与 prefab 实测一致（勿改坐标）；数据源: UIPrefabBuilder.cs
     坐标换算 x=960+X, y=540−Y -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
  <defs>
    <linearGradient id="ds-panel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#2A3444"/><stop offset="0.5" stop-color="#1B2330"/><stop offset="1" stop-color="#222C3B"/>
    </linearGradient>
    <linearGradient id="ds-gold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFC94D"/><stop offset="1" stop-color="#E8912B"/>
    </linearGradient>
    <radialGradient id="ds-vig" cx="0.5" cy="0.5" r="0.75">
      <stop offset="0.62" stop-color="#0B0E14" stop-opacity="0"/><stop offset="1" stop-color="#0B0E14" stop-opacity="0.66"/>
    </radialGradient>
    <filter id="ds-neon" x="-60%" y="-60%" width="220%" height="220%">
      <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#35E0FF" flood-opacity="0.85"/>
    </filter>
    <pattern id="ds-stars" width="220" height="220" patternUnits="userSpaceOnUse">
      <circle cx="30" cy="40" r="1.2" fill="#E8F0FA" fill-opacity="0.4"/>
      <circle cx="130" cy="22" r="0.8" fill="#E8F0FA" fill-opacity="0.28"/>
      <circle cx="186" cy="104" r="1.4" fill="#35E0FF" fill-opacity="0.3"/>
      <circle cx="74" cy="150" r="0.9" fill="#E8F0FA" fill-opacity="0.22"/>
    </pattern>
  </defs>
  <!-- 世界层 / 界面内容 -->
  <!-- 暗角层：<rect width="1920" height="1080" fill="url(#ds-vig)"/> -->
  <!-- 标注层（font-family="Consolas,monospace"，交付实现时可删） -->
</svg>
```

### 4.3 本策划案需新增的效果图

| 文件名 | 对应界面 | 说明 |
|---|---|---|
| `15_SplashView.svg` | A1 | 开屏页 |
| `16_LoadingView.svg` | A2 | 加载进度 |
| `17_HotUpdateView.svg` | A3 | 热更新 |
| `18_MainMenuView.svg` | B1 | 主菜单 |
| `19_TowerCodexView.svg` | B2 | 塔图鉴（扩展已有 `14_TowerCodex.svg`） |
| `20_MonsterCodexView.svg` | B3 | 怪物图鉴 |
| `21_LevelDetailView.svg` | B4 | 关卡详情 |
| `22_ConfirmView.svg` | C1+C2 | 出售确认 + 通用确认 |

---

## 5. 程序侧配套改造清单

> 美术界面不是孤立的，以下代码必须同步改造，否则界面打开也是空壳。

### 5.1 启动流程（A1/A2/A3/B1 的支撑）

**`Launcher.cs`** —— 新增启动阶段回调：

```csharp
// 阶段枚举
public enum BootPhase { Splash, Loading, HotUpdate, Ready }

// 在 BootResAndConfig 中，把当前的单次异步拆成带进度的链：
//   SplashView 显示 1.5s
//   → LoadingView 显示，ResLoader.Init（0%→30%）
//   → HotUpdateView 显示（新增），版本比对 + 下载（30%→100%）
//   → Configs.LoadAsync（90%→100%）
//   → ConfigLoadedEvent → GameFlowManager 开 MainMenuView
```

⚠️ **顺序不可颠倒**：热更新必须在 `ResLoader.Init` **之后**（它依赖包裹已初始化）、`Configs.LoadAsync` **之前**（配置表本身也可能是热更内容）。

### 5.2 界面注册（所有新增界面）

**`ResTable.cs`** ⚠️ 每个新 prefab 都要登记逻辑名：

```csharp
// 新增登记（与既有 UI 登记写在一起）
Add("SplashView",      "ui_splash",      "Assets/Prefabs/UI/SplashView.prefab");
Add("LoadingView",     "ui_loading",     "Assets/Prefabs/UI/LoadingView.prefab");
Add("HotUpdateView",   "ui_hotupdate",   "Assets/Prefabs/UI/HotUpdateView.prefab");
Add("MainMenuView",    "ui_mainmenu",    "Assets/Prefabs/UI/MainMenuView.prefab");
Add("TowerCodexView",  "ui_towercodex",  "Assets/Prefabs/UI/TowerCodexView.prefab");
Add("MonsterCodexView","ui_monstercodex","Assets/Prefabs/UI/MonsterCodexView.prefab");
Add("LevelDetailView", "ui_leveldetail", "Assets/Prefabs/UI/LevelDetailView.prefab");
Add("SellConfirmView", "ui_sellconfirm", "Assets/Prefabs/UI/SellConfirmView.prefab");
Add("ConfirmView",     "ui_confirm",     "Assets/Prefabs/UI/ConfirmView.prefab");
// 条目资产不需要登记（靠 prefab 引用进包）
// TowerCodexItem.prefab / MonsterCodexItem.prefab
```

⚠️ **`check_code.py` 只扫 `Get("字面量")`，不扫 `Configs.ConfigKeys`** → 加表后必须**手工同步**。

### 5.3 UIPrefabBuilder 扩展

新增 9 个 `BuildXXX` 方法，全部复用 `CreateDialogShell` 骨架。**必须加入 `EnsureMissing` 的补缺列表**，并更新 `Assets/Prefabs/UI/` 的资产常量。

⚠️ **重建前必查**：`isCompiling == false && isPlaying == false`，否则会用旧程序集静默生成旧结果。

### 5.4 事件清单新增

`EventName.cs` 需新增：

```csharp
// 启动链路
SplashFinishedEvent        // Splash → Loading
LoadingProgressEvent       // (string phase, float progress)
HotUpdateProgressEvent     // (int cur, int total, long bytes, long totalBytes)
HotUpdateFailedEvent       // (string reason)
HotUpdateFinishedEvent

// 界面流转
OpenMainMenuRequestEvent
StartGameRequestEvent      // 主菜单 → 选关
OpenCodexRequestEvent      // (bool isTower)
OpenLevelDetailRequestEvent// (int levelId)
TowerSellConfirmEvent      // 确认出售（真正执行）
```

### 5.5 层级与代码约定（**不得违反**）

- 新界面一律 `UILayout.NormalPanel`（除 `TipsView` 用的 `TipsPanel`）
- `UiClickSfx` 由 `UIManager.Open` 自动挂 → **新界面不用写点击音**
- `EnsureFadeIn` 自动加淡入 → **prefab 自带 `CanvasGroup` 的界面会跳过**（如需要自定义淡入则自带 `CanvasGroup`）
- View 一律挂在 prefab 上的 `MonoBehaviour`
- ⚠️ **节点名契约**：`View` 的 `Find("Panel/X")` 与生成器无映射层，写岔只静默打「缺少节点」→ 成对改 + 跑 `check_ui_contract.py`

---

## 6. 验收标准（每界面必跑）

| # | 校验 | 命令 | 期望 |
|---|---|---|---|
| 1 | 代码静态检查 | `python .workbuddy/tools/check_code.py` | PASS |
| 2 | UI 节点契约 | `python .workbuddy/tools/check_ui_contract.py` | PASS |
| 3 | 事件完整性 | `python .workbuddy/tools/check_events.py` | PASS |
| 4 | 成员引用 | `python .workbuddy/tools/check_members.py` | PASS |
| 5 | 参数元数 | `python .workbuddy/tools/check_arity.py` | PASS（`_CHANGED` 补新文件） |
| 6 | using 检查 | `python .workbuddy/tools/check_usings.py` | PASS |
| 7 | Unity 编译 | Unity MCP `read_console` | 零 error |
| 8 | 实机截图 | Unity MCP `screenshot` | 与效果图一致 |
| 9 | **效果图排版** | `python .workbuddy/tools/check_svg_layout.py` | **PASS（0 重叠 / 0 越界）** |
| 10 | 效果图 XML | `python .workbuddy/tools/check_svg_layout.py`（内含 parse） | 全部可解析 |

⚠️ **`check_arity.py` 的 `_CHANGED` 不许留已删文件**。
⚠️ shell 跑 Python 时别用 `\s`/`\b`/`\w`（会被 shell 转义）。

### 6.1 效果图排版校验器（`check_svg_layout.py`）

**为什么要它**：本策划案的效果图是用绝对坐标手写的 SVG，极易出现"按钮压住卡片/超出面板/跑出画布"这类**肉眼在缩略图上不易察觉**的错误。该脚本把版面变成可回归的几何断言。

**判定逻辑**（三分类，避免误报）：
- **NAV** 导航/操作元素：`polygon` 芯片、以及文字含 `返回/取消/确定/开始/重试/出售/升级` 的短文本
- **BODY** 内容实体：卡片内框（fill ∈ `#252F40/#1E2939/#22303F/#2A3444`）、无填充大矩形（面板）
- **NOTE** 注解层：`y ≥ 1000` 的文字、整页底（≥1900×1040）、大底色块（≥1400×700）
- 只对 **NAV×BODY / NAV×NAV** 报错（重叠率 ≥15%）；`BODY×BODY` 仅在高重叠且**无包含关系**时报可疑
- 处于 `opacity ≤ 0.5` 的"压暗战场示意"组内的元素一律跳过（它们本来就在弹窗下面）
- 额外报告**越界**：任何元素超出 `0..1920 / 0..1080`

**用法**：
```
python .workbuddy/tools/check_svg_layout.py          # 全部 22 张
python .workbuddy/tools/check_svg_layout.py 20 21 22 # 只查这几张
```

**配套**：`fix_svg_comments.py` 批量修正 SVG 注释里的非法 `--`（XML 不允许注释体含连续 `--`，也不允许以 `-` 结尾；这是本套效果图最常踩的坑）。

---

## 7. 禁止事项（违反即返工）

| # | 禁止 | 原因 |
|---|---|---|
| 1 | 手搓 prefab 而不走 `UIPrefabBuilder` | 下次全量重建时 `IsSafeToRebuild` 判为陌生节点 → 中止生成 |
| 2 | 新增 UGUI `Text` | 全工程统一 TMP；UGUI Text 中文会缺字形 |
| 3 | 自创颜色 | 必须用 §2 令牌，否则整套皮肤不一致 |
| 4 | 新增 `PlayerPrefs` | 存档只走 `SaveManager`（例外：`KeyProvider`） |
| 5 | 直接读写 SQL / `IDatabase` | 同上，只走 `SaveManager` |
| 6 | 往 `BoardRoot` 等常驻节点 new 东西不清空 | 必须自带清空并登记（见 `TeardownLevel`） |
| 7 | 破坏 YooAsset 三步初始化契约 | 会导致 `Active package manifest not found.` |
| 8 | 缩放入口条目**根节点** | 根节点 `pivot=(0,0.5)`，缩它会偏心；缩放挂 `Body` 子节点 |
| 9 | 用 `mOnSnapItemFinished` 判断"滑到位" | 该回调的索引只在容器移动帧才重算，会提前触发 |
| 10 | 新增生僻字不验证字体图集 | `SiYuanSongTi SDF.asset` 必须"动态+多图集"，否则新字渲染空白且不报错 |
| 11 | 塔按钮锚点写左下 | 必须 `(0.5,0.5)`，否则整排塔按钮出屏 |
| 12 | 改 `ResTable` 后不跑 `check_code.py` | 该脚本扫不到 `ConfigKeys`，必须手工同步 |

---

## 8. 执行顺序（AI 照此推进）

```
阶段一（上线阻塞，先做）
  1. A3 热更新的资源层（YooAssetResLoader 加 CheckUpdateCo / DownloadCo）
  2. A1 SplashView + A2 LoadingView + A3 HotUpdateView（三个界面 + Launcher 改造）
  3. 跑 §6 全部校验

阶段二（门面与内容）
  4. B1 MainMenuView（+ GameFlowManager 启动流程改造）
  5. B2 TowerCodexView（+ TowerCodexItem + SelectView 几何复用）
  6. B4 LevelDetailView（+ SaveManager 读历史数据）

阶段三（打磨）
  7. C1 SellConfirmView + C2 ConfirmView（+ 改造 SettingView / MainMenuView 接入）
  8. C3 屏幕震动（+ CameraController）
  9. C4 切关遮罩
  10. B3 MonsterCodexView
```

**每个阶段结束必须**：
- 跑 §6 的 8 项校验
- 在 Unity 里实际打开界面截图
- 追加 `.workbuddy/memory/YYYY-MM-DD.md` 记录

---

## 附录 A · 现有生成器接口速查

```csharp
// 骨架（弹窗/整页通用）
private static GameObject CreateDialogShell(
    string rootName,            // prefab 名，如 "MainMenuView"
    string title,               // 标题文字
    Vector2 panelSize,          // 弹窗尺寸；整页时传 Vector2.zero
    EditorUtil.Report report,
    out GameObject panel,       // 输出 Panel 节点，后续往它下面挂子节点
    float stretchInset = -1f);  // >=0 走整页口径（Panel 四边内缩该值铺满）

// 按钮
private static void CreatePanelButton(
    Transform parent, string name, string label,
    Vector2 anchoredPos,
    float width = 340f,
    bool primary = false,
    float height = 84f,
    float fontSize = 32f);

// 文字（统一 TMP）
private static void CreateText(
    Transform parent, string name, string content,
    Vector2 anchor, Vector2 anchoredPos, Vector2 size,
    TextAnchor align, int fontSize, Color? color = null);

// 图片
private static void ApplySlicedSkin(Image img, string spriteName, Color fallbackColor);

// 上报
EditorUtil.Report report = new EditorUtil.Report();
report.Head("..."); report.Ok("..."); report.Warn("..."); report.Error("...");
int errCount = report.Errors;  // 属性
```

## 附录 B · 菜单入口速查

```
Tools ▸ 塔防 ▸ 高级（单步重建） ▸ 生成 UI 皮肤美术            ← UISkinArtGenerator
Tools ▸ 塔防 ▸ 高级（单步重建） ▸ 补缺 UI 预制体（安全）      ← UIPrefabBuilder.EnsureMissing
Tools ▸ 塔防 ▸ 高级（单步重建） ▸ 生成 UI 预制体（全量重建）  ← UIPrefabBuilder.Build
Tools ▸ 塔防 ▸ 自动化（无弹窗） ▸ 生成 UI 皮肤美术            ← 自动化专用，不弹窗
Tools ▸ 塔防 ▸ 自动化（无弹窗） ▸ 生成 UI 预制体（全量重建）  ← 自动化专用，不弹窗
Tools ▸ 塔防 ▸ 搭建 main 场景                                 ← SceneMainBuilder
Tools ▸ 塔防 ▸ 3.导出配置表                                   ← LubanExporter
```

⚠️ **跑生成类菜单前必须确认 `isCompiling == false && isPlaying == false`**，否则用旧程序集静默生成旧结果。

---

*文档版本：v1.0　|　编制日期：2026-10-09　|　基线：工程实测 + `.workbuddy/memory/2026-10-09.md`*
