# 《自由人塔防》品牌视觉形象手册（Brand Guide v1.0）

> 英文名：**FREEDOM TOWER**　|　工程：`D:\FreedomTower_1`（Unity 2022.3.62f3c1 / Built-in RP）
> 交付目录：`BrandKit\`　|　生成器：`BrandKit\_tools\build_brandkit.py`（矢量几何精确绘制，可重跑复现）
> 日期：2026-10-15　|　字体源：`Assets\Font\SiYuanSongTi.ttf`（工程自带）

---

## 一、项目分析（定风格之前）

| 维度 | 结论 | 依据 |
|---|---|---|
| 项目类型 | **单机 2D 塔防手游**（Android），对标 Fieldrunners 核心机制 | `Docs\GameDesign_自由人塔防_v3.md` §1 |
| 核心玩法 | **自由布塔塑造路径**：棋盘全开阔，建塔实时重算 A* 路径；禁止完全堵路；去物理战斗 | 同上 §1.2「灵魂机制」 |
| 结构 | 8 关 × 5 回合，星级评定、3 塔型（普通/火力/减速）、飞行+行走双目标 | 同上 §2、§3 |
| 美术基调 | **深空科幻 · 冷色科技感**：近黑星域底 + 深板岩面板 + 青蓝霓虹 + 水晶能量核心 + 索敌框 | `Docs\ArtDesign_自由人塔防_补全策划案_v1.md` §2 |
| 既有色板 | 主色 青 `#35E0FF`；功能 金 `#FFC94D` / 红 `#FF4D5E` / 橙 `#FF7A29`；面板 `#2A3444→#1B2330`；底 `#080B12` | 同上 §2.1（源自 `UISkinArtGenerator.cs`） |
| 既有效果图 | SplashView 占位标志 = 六边形 + 青水晶 + 四角索敌框 + 金色星点 | `Docs\ui_mockups\15_SplashView.svg` |

**关键判断**：游戏已具备一套成熟、严格的视觉令牌（配色/字号/九宫格/发光半径），因此品牌形象**不是从零另立一套**，而是把既有的"六边形水晶核心 + 索敌框 + 星域底"从**占位符号**升格为**正式品牌标记**，并补齐图标、主视觉、游戏内装饰、辅助规范四大场景。这样品牌与游戏本体天然同源，零割裂。

---

## 二、标志设计思路

### 2.1 概念：**"核心壁垒 / CORE CITADEL"**

| 元素 | 形态 | 语义 |
|---|---|---|
| **六边形** | 尖顶正六边形底板 | 棋盘格网 + 塔基座 →「自由布防的战场」 |
| **棱面水晶** | 五面切割宝石，青蓝渐变 + 台面高光 | 能量核心 →「自由之力 / 核心」 |
| **索敌框** | 四角 L 形括号 | 目标锁定 / 防御 → 塔防的"索敌"语言 |
| **金色星点** | 顶部四芒星 | 星级评定 / 荣耀 → 呼应游戏 3 星结算 |
| **内嵌细线** | 钢色内六边形 + 青光细圈 | 科技层次，大尺寸才显现（小尺寸自动消失） |

### 2.2 造型原则

1. **极简优先**：核心辨识体只有「六边形 + 水晶」两笔，48px 下仍清晰——刻意排除细线、杂点、渐变噪。
2. **阈值化设计**：细节（棱面线、内圈线、索敌框）只在 ≥128px 呈现；≤64px 自动退化为实心水晶 + 粗描边六边形（`symbol` 变体）。
3. **纯几何矢量**：全部由数学坐标生成，**不使用 AI 生成位图**，从根本上杜绝锯齿、水印残留与文字幻觉（这是图标类资产的硬要求）。
4. **轴向对称 + 中心发光**：视觉重心稳，适合圆形/方形/圆角各种遮罩裁切。

### 2.3 标志家族

| 变体 | 用途 | 最小尺寸 |
|---|---|---|
| `full`（含索敌框 + 星点） | 主视觉、Splash、Marketing、≥128px | 128px |
| `symbol`（六边+水晶+星点） | APP 图标、加载徽记、一般场景 | 48px |
| `icon_core`（无索敌框，紧凑） | APP 图标专用（边缘留白更小） | 32px |
| `mono_white` / `mono_black` | 单色印刷、深/浅底反白、水印 | 32px |
| 横版 / 竖版 lockup | 中英组合排版 | 高度 ≥ 96px |

---

## 三、配色选择理由

主色不是"挑一个好看的蓝"，而是**直接继承游戏内视觉令牌**，保证品牌与游戏零色差：

| 角色 | 色值 | 命名 | 理由 |
|---|---|---|---|
| **主色** | `#35E0FF` | Core Cyan 科技青 | 游戏全局强调色，代表能量/可交互/科技感；在深底上对比强、小尺寸可辨 |
| 主色亮 | `#DFFAFF` | Cyan Light | 水晶台面高光，制造体积感 |
| 主色深 | `#0E6E93` | Cyan Deep | 水晶暗部，深空纵深感 |
| **辅助色** | `#FFC94D` | Glory Gold 荣耀金 | 星级/胜利/奖励，与青色形成冷暖对冲，让标志有"点睛"记忆点 |
| 冰白 | `#7DE8FF` | Ice | 次级发光、水感 |
| 钢灰 | `#9FB3C8` / `#5E7396` | Steel / SteelDark | 次要文字、金属结构线 |
| 功能红 | `#FF4D5E` | Alert Red | 生命/失败/危险 |
| 功能橙 | `#FF7A29` | Fire | 火焰塔/警示 |
| 底色 | `#080B12` / `#0D1119` | Void / L0 | 近黑星域底，让青色发光"跳"出来 |

**配色纪律**：主色使用面积 ≥ 70%，金色仅作 ≤ 8% 的点缀，避免"花"。所有资源色值均已对齐 `UISkinArtGenerator` 令牌，可直接进 Unity 而不需再校色。

---

## 四、字体选择理由

| 用途 | 字体 | 理由 |
|---|---|---|
| **中文标准字** | **思源宋体（Source Han Serif SC / 工程内 `SiYuanSongTi.ttf`）Bold** | ① 工程已在用（`Assets/Font/SiYuanSongTi SDF.asset`），品牌与游戏同字；② 宋体衬线自带"正式/厚重/古典科技"气质，比黑体更耐看、更有品牌感；③ 配合青色外发光即得科幻调性 |
| **英文标准字** | **几何无衬线 全大写 + 宽字距**（生产推荐 Rajdhani / Orbitron / Chakra Petch；本包栅格化用 Segoe UI Bold 代理） | 全大写宽字距是电竞/科幻通用语言，与中文宋体形成"人文 + 机械"的对比张力 |
| **技术标号 / 版本号** | **等宽字体**（Consolas / JetBrains Mono） | 与游戏内 `FREEDOM TOWER`、`v1.0.0` 标注口径一致 |
| 正文 | 思源宋体 Regular | 与标题同族，保证整站一致 |

> 注：SVG 母版中的文字使用 `font-family` 引用，需目标环境装有对应字体；**权威字型以 PNG 栅格为准**。

---

## 五、品牌元素与应用

- **索敌框（Reticle）**：可作为界面四角装饰、加载态、扫描动效的母题。
- **六边格网（Hex Grid）**：所有背景的低透明度底纹，统一视觉语言。
- **能量条 / 分割线（Divider）**：以六边形节点为轴的横向分割装饰。
- **星点（Spark）**：星级、胜利、解锁提示的图形符号。

---

## 六、各场景输出图片清单

> 全部为 **PNG-32（含 Alpha）**；标注"不透明"者 Alpha 全 255。所有带透明通道的资源边缘均已 4× 超采样抗锯齿，无白边/黑边。

### ① APP 图标 `01_AppIcon\`

| 文件 | 尺寸 | 格式 | 透明 | 说明 |
|---|---|---|---|---|
| `Icon_Master_1024.png` | 1024×1024 | PNG | 否 | **母版**，满幅方形，用于通用/Android 传统图标 |
| `Icon_Master_512.png` | 512×512 | PNG | 否 | Google Play 商店图标 |
| `Icon_iOS_1024_Squircle.png` | 1024×1024 | PNG | 四角透明 | iOS，已套 squircle 圆角遮罩 |
| `Icon_Android_Round_512.png` | 512×512 | PNG | 圆形外透明 | Android 圆形遮罩 |
| `Icon_Android_Square_512.png` | 512×512 | PNG | 圆角外透明 | Android 圆角方形（radius≈22.5%） |
| `Icon_Adaptive_Foreground_432.png` | 432×432 | PNG | 是 | 自适应图标**前景层**（内容居中于安全区） |
| `Icon_Adaptive_Background_432.png` | 432×432 | PNG | 是 | 自适应图标**背景层**（星域+格网） |
| `Icon_Adaptive_Monochrome_432.png` | 432×432 | PNG | 是 | 自适应**单色层**（Android 13+ 主题图标） |
| `Icon_Transparent_Symbol_512.png` | 512×512 | PNG | 是 | 透明底主视觉（无底板） |
| `Sizes\iOS_180/167/152/144/120/114.png` | 对应尺寸 | PNG | 否 | iOS AppIcon 全套 |
| `Sizes\Android_192/144/96/72/48.png` | 对应尺寸 | PNG | 否 | Android mipmap 全套 |
| `Sizes\Web_48/32/16.png` | 对应尺寸 | PNG | 否 | 网页/收藏夹图标 |
| `Sizes\Symbol_48_Transparent.png` | 48×48 | PNG | 是 | **极小尺寸验证版**（简化符号） |

### ② 主场景图片 `02_KeyVisual\`

| 文件 | 尺寸 | 格式 | 透明 | 说明 |
|---|---|---|---|---|
| `KV_Splash_1920x1080.png` / `KV_Splash_1080x1920.png` | 横/竖 | PNG | 否 | 启动页（标志 + 中文 + 英文 + 标语） |
| `KV_Splash_Background_Only_*.png` | 横/竖 | PNG | 否 | 启动页**纯背景**（无文字，可复用/接动效） |
| `KV_Login_*.png` | 横/竖 | PNG | 否 | 登录/主菜单主视觉（含战术棋盘装饰） |
| `KV_Loading_*.png` | 横/竖 | PNG | 否 | 加载页背景（含简化标记） |

### ③ 游戏内常用图片 `03_InGame\`（**全部透明底**）

| 文件 | 尺寸 | 格式 | 说明 |
|---|---|---|---|
| `InGame_LogoPlate_1400x520.png` / `_700x260.png` | 1400×520 / 700×260 | PNG | 启动画面 **Logo 标牌**（面板 + 顶部色条 + 中英组合） |
| `InGame_LoadingEmblem_512.png` | 512×512 | PNG | 加载提示图（六边环 + 核心，可旋转做 loading） |
| `InGame_Divider_Cyan_1600.png` | 1600×120 | PNG | 通用六边节点分割装饰 |
| `InGame_PauseDecoration_1200x900.png` | 1200×900 | PNG | 暂停界面装饰（品牌化暂停符 + 四角索敌框） |
| `InGame_Result_Win_1400x420.png` | 1400×420 | PNG | **胜利**结算装饰（金，含 3 星） |
| `InGame_Result_Lose_1400x420.png` | 1400×420 | PNG | **失败**结算装饰（红，空星） |
| `InGame_Watermark_640x200.png` | 640×200 | PNG | 水印（单色白，自带 62% 透明度） |
| `InGame_CornerBadge_320.png` | 320×320 | PNG | 角标（六边徽章 + 核心） |

### ④ 辅助资源 `04_Auxiliary\`

| 文件 | 尺寸 | 格式 | 透明 | 说明 |
|---|---|---|---|---|
| `Logo_Horizontal_OnDark.png` | 高 360 | PNG | 是 | 横版组合（深底用：青标 + 浅字） |
| `Logo_Horizontal_OnLight.png` | 高 360 | PNG | 是 | 横版组合（浅底用：深字） |
| `Logo_Vertical_OnDark.png` / `_OnLight.png` | 高 360 基准 | PNG | 是 | 竖版组合（含标语） |
| `Logo_Horizontal_OnDark_WithBg_1920x540.png` | 1920×540 | PNG | 否 | 横版**带背景** |
| `Logo_Vertical_OnDark_WithBg_1080.png` | 1080×1080 | PNG | 否 | 竖版**带背景** |
| `Logo_Monochrome_White.png` / `_Black.png` | 900×900 | PNG | 是 | 单色/反白版 |
| `Logo_Symbol_Cyan_1024.png` | 1024×1024 | PNG | 是 | 主视觉简化符号 |
| `Brand_Palette_1920x1200.png` | 1920×1200 | PNG | 否 | **品牌色板**（含 HEX） |
| `Brand_Typography_1920x1200.png` | 1920×1200 | PNG | 否 | **字体规范**（中/英/标语/标号/正文） |
| `Logo_ClearSpace_MinSize_1400.png` | 1400×1000 | PNG | 否 | **安全边距 + 最小尺寸**规范图 |

### ⑤ 矢量母版 `05_Vector_SVG\`（无损缩放）

`logo_mark_full.svg`、`logo_mark_symbol.svg`、`logo_mark_monochrome_white.svg`、`logo_mark_monochrome_black.svg`、`logo_lockup_horizontal.svg`、`logo_lockup_vertical.svg`

---

## 七、使用规范

1. **安全边距**：标志四周留白 ≥ 水晶核心宽度 X（见 `Logo_ClearSpace_MinSize_1400.png`），留白区内不得放任何元素。
2. **最小尺寸**：完整版 `full` ≥ 128px；简化版 `symbol` ≥ 48px；< 48px 仅用符号，禁用文字与索敌框。
3. **禁止**：拉伸变形、改色（尤其把青改成其他蓝）、加描边/阴影、倾斜、置于低对比背景、在标志上叠加文字。
4. **深/浅底**：深底用 `OnDark`（青标 + 浅字），浅底用 `OnLight`（深字），单色场景用 `Monochrome`。
5. **游戏内落地**：
   - APP 图标 → `ProjectSettings` 的 Icon 槽 / Android mipmap / iOS AppIcon Set（用 `Sizes\` 对应尺寸）。
   - 自适应图标 → Android `mipmap-anydpi-v26` 的 `foreground` + `background` + `monochrome` 三层。
   - Splash/Loading/Login → 放进 AB 包（资源需 AB 打包才可在真机热更侧加载）。
6. **重跑生成**：`python BrandKit\_tools\build_brandkit.py`（改尺寸/配色只需改脚本常量，可完全复现）。

---

## 八、与既有资产的对应关系

| 既有 | 品牌升级后 |
|---|---|
| `15_SplashView.svg` 占位标志（六边形+青水晶+索敌框） | 升格为正式标记 `logo_mark_full.svg` |
| `UISkinArtGenerator.cs` 色板 | 品牌主/辅色直接继承，零色差 |
| `Assets/Font/SiYuanSongTi.ttf` | 中文标准字，品牌与游戏同字 |
| 游戏 3 星结算 | 标志金色星点 / 结算装饰 3 星 |
