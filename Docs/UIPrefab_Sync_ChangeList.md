# UI 预制体手工改动同步清单

> 本文档记录一次「手工改 prefab → 反向同步生成器 / 缓存 / 引用代码」的完整交付。
> 约定：所有路径均为**工程相对路径**（不写盘符，双版本 D: / E: 通用）。
> 生成器 = `Assets/Editor/UIPrefabBuilder.cs`（Editor 程序集）；预制体在 `Assets/Prefabs/UI/`。

---

## 1. 做了什么

用户手工修改了 `Assets/Prefabs/UI/` 下的预制体，本次把「磁盘上的预制体（事实）」与
「生成器代码 + 结构缓存 + 所有引用这些节点的脚本」三方对齐，确保再次跑生成器不会把手改冲掉。

同步链路：

```
手工改 prefab（事实）
   ├──► .workbuddy/cache/ui_prefabs.json        结构快照（节点树 + 几何 + 激活态）
   ├──► Assets/Editor/UIPrefabBuilder.cs         生成器（改回能产出同样结构）
   ├──► Assets/Editor/M0SetupWizard.cs           装配向导的 HudView 契约串
   └──► Assets/Scripts/UI/*.cs                   View 的 transform.Find 路径
```

---

## 2. 受影响的预制体与节点级改动

（`+` 新增节点 / `-` 删除节点 / `=` 几何或字段变化；几何格式：`锚点 位置 尺寸`）

### 2.1 HudView — HUD 塔按钮 5→3，血量/金币/回合文本改为芯片子节点

| 变动 | 节点 | 说明 |
|---|---|---|
| `+` | `Bg_Gold/GoldText` | 金币文本移到金币芯片**之下**（两段式路径） |
| `+` | `Bg_Hp/HpText` | 血量文本移到血量芯片之下 |
| `+` | `Bg_Round/RoundText` | 回合文本移到回合芯片之下 |
| `-` | `GoldText` `HpText` `RoundText` | 原为 HudView 直接子节点，已删除 |
| `-` | `Btn_Tower_Pierce` `Btn_Tower_Laser`（及其 `Image/PriceBg/PriceText`） | HUD 只保留 **3 个**塔按钮 |
| `=` | `Bg_Round` | 尺寸 `320×56 → 580×56`（容纳 "In Progress" 文案） |

> HUD 保留的 3 个塔按钮仍在**原 5 格的占位**上：`Btn_Tower_Normal` x=-548、`Btn_Tower_Power` x=-274、
> `Btn_Tower_Retard` x=0，y 均为 -427（视觉居中，后续想加回 4/5 号只需补节点名）。

### 2.2 ConfirmView — 标题改挂 TopBar 之下

| 变动 | 节点 | 说明 |
|---|---|---|
| `-` | `Panel/BodyTitle` | 原 panel 直挂 |
| `+` | `Panel/TopBar/BodyTitle` | 改为顶栏子节点（随栏居中），四边拉伸 geometry |
| `=` | `Panel` | `760×560 → 960×560` |
| `=` | `Panel/Title` | 尺寸 `700×56 → 700×100`（独立放大） |
| `=` | `Panel/TopBar` | 位置 y `0 → -24`；尺寸 `760×24 → 760×80` |

### 2.3 SellConfirmView — 标题改挂 TopBar 之下 + 整体放大

| 变动 | 节点 | 说明 |
|---|---|---|
| `-` | `Panel/SellTitle` | 原 panel 直挂 |
| `+` | `Panel/TopBar/SellTitle` | 改为顶栏子节点，四边拉伸 geometry |
| `=` | `Panel` | `800×620 → 1000×750` |
| `=` | `Panel/TopBar` | 位置 y `0 → -29`；尺寸 `800×24 → 800×102` |
| `=` | `Panel/TowerIcon` | y `158 → 132` |
| `=` | `Panel/TowerName` | y `89 → 63` |
| `=` | `Panel/WarnText` | y `-5 → -31` |
| `=` | `Panel/RefundLabel` | y `-80 → -106` |
| `=` | `Panel/RefundValue` | y `-78 → -104` |
| `=` | `Panel/ConfirmBtn` `CancelBtn` | y `-210 → -256` |

### 2.4 MainMenuView — 统计文本改挂 StatBg 之下

| 变动 | 节点 | 说明 |
|---|---|---|
| `-` | `Panel/StarText` `Panel/ClearText` | 原 panel 直挂 |
| `+` | `Panel/StatBg/StarText` `Panel/StatBg/ClearText` | 改为统计底衬子节点，随底一起动 |
| `=` | `Panel/StatBg` | 位置 x `48 → 91` |
| `=` | `Panel/Subtitle` | `active true → false`（隐藏，与 GameTitle 内容重复） |

### 2.5 TipsView — 提示文字改为横向拉伸

| 变动 | 节点 | 说明 |
|---|---|---|
| `=` | `TipText` | 锚点 `(0.5,0.3)→(0,0.5)/(1,0.5)`；位置 `(0,0)→(0,-12)`；尺寸 `1100×60 → 拉伸×(0,100)` |

### 2.6 LevelDetailView — 面板收窄、顶部色条改拉伸

| 变动 | 节点 | 说明 |
|---|---|---|
| `=` | `Panel` | `1000×900 → 900×900` |
| `=` | `Panel/TopBar` | 锚点 `(0.5,1)→(0,1)/(1,1)`（跟随面板宽，拉伸型）；尺寸 `1000×24 → 0×8` |

### 2.7 LevelClearView / TowerInfoView / SelectView / SelectLevelItem — 尺寸微调

| 预制体 | 节点 | 变化 |
|---|---|---|
| LevelClearView | `Panel` | `640×680 → 820×720` |
| TowerInfoView | `Panel` | `560×460 → 560×600`（给 3 行属性 + 按钮留空间） |
| SelectView | `Panel/List` | 改为**整页拉伸**（锚点 0,0/1,1、位置 0、尺寸 0） |
| SelectLevelItem | 根 | `900×440 → 1500×650`；`active false → true` |

### 2.8 SettingView — 仅滑动条位移（几何与 HEAD 一致，仅 fileID churn）

| 节点 | 变化 |
|---|---|
| `Panel/VolumeSlider` | 位置 y `40 → 55`；尺寸 `480×40 → 480×55` |

---

## 3. 对应代码位置

### 3.1 生成器 `Assets/Editor/UIPrefabBuilder.cs`

| 位置 | 改动 |
|---|---|
| `HudChildren` 常量 | 列表收敛为 3 塔按钮 + 3 芯片 + Start/Speed（删 GoldText/HpText/RoundText、Pierce/Laser） |
| `TowerButtons` 数组 | 3 项，占位 -548/-274/0，y=-427 |
| `BuildHud` | `CreateChip` 返回 `Transform`；文本改用新助手 `CreateChipText`（四边拉伸）；`Bg_Round` 宽 320→580 |
| 新助手 `CreateChipText(Transform chip, …)` | 生成"整块拉伸"的芯片文本子节点 |
| 新助手 `CreateTextStretched(parent, name, content, anchorMin, anchorMax, pos, size, align, fontSize)` | 通用拉伸文本框（TipText / BodyTitle / SellTitle 用） |
| `CreateDialogShell(…, Vector2? overrideTitleSize)` | 新增可选参数：允许个别弹窗覆盖标题尺寸（ConfirmView 700×100、LevelDetailView 940×56、SellConfirmView 740×56、LevelClearView 580×56） |
| `BuildMainMenu` | Subtitle `SetActive(false)`；`StatBg` x 48→91；StarText/ClearText 挂 `statBg` 下（y -18.5 / -64.1） |
| `BuildSellConfirm` | 面板 1000×750、TopBar 800×102 y=-29、SellTitle 挂 topBar（拉伸）、各子节点 y 重排 |
| `BuildConfirm` | 面板 960×560、TopBar 760×80 y=-24、BodyTitle 挂 topBar（拉伸）、Title 700×100 |
| `BuildLevelDetail` | 面板 900×900、TopBar 用新助手 `CreateStretchedBar`（拉伸 8 高） |
| `BuildLevelClear` | 面板 820×720 |
| `BuildTowerInfo` | 面板 560×600 |
| `BuildSelect` / `SelectItemW/H` | 卡 900×440→1500×650；新增 `SelectViewSideInset=200f`；Viewport 拉伸 offset ±200；List 整页 |
| `BuildSetting` | VolumeSlider y 40→55、尺寸 480×55 |
| 新助手 `CreateStretchedBar(parent, name, height, spriteName, fallback)` | 横向拉伸色条（锚点 x 0..1） |

### 3.2 引用脚本（`Assets/Scripts/UI/`）

| 文件 | 改动 |
|---|---|
| `HudView.cs` | `TowerNodeNames` 3 项；`TowerNodeTypes={1,2,3}`；`FindText("Bg_Gold/GoldText")`、`"Bg_Hp/HpText"`、`"Bg_Round/RoundText"` |
| `ConfirmView.cs` | `_title = FindText("Panel/TopBar/BodyTitle")` |
| `SellConfirmView.cs` | `_title = FindText("Panel/TopBar/SellTitle")` |
| `MainMenuView.cs` | `FindText("Panel/StatBg/StarText")`、`"Panel/StatBg/ClearText"` |
| `SelectView.cs` | `ItemWidth` 900→1500 |
| `M0SetupWizard.cs` | HudView 契约串改为 3 芯片子路径 + 3 塔按钮 |

### 3.3 工具与缓存

| 文件 | 作用 |
|---|---|
| `.workbuddy/cache/ui_prefabs.json` | 14 个预制体、198 个节点的结构快照（含几何 + 激活态） |
| `.workbuddy/tools/_prefab_tree.py` | 预制体 YAML 解析核心（正确解析 `m_Father`→父 RectTransform） |
| `.workbuddy/tools/gen_ui_prefab_cache.py` | 生成 / `--check` 核对缓存与磁盘一致性 |
| `.workbuddy/tools/diff_ui_prefabs.py` | 结构与**几何**差异比对（`--base <目录>`） |
| `.workbuddy/tools/check_ui_contract.py` | 扩展支持 `CreateTextStretched` 与"返回值为容器"模式 |

---

## 4. 验证方法与结论

### 4.1 静态校验（9 个）

```bash
python .workbuddy/tools/check_arity.py
python .workbuddy/tools/check_code.py
python .workbuddy/tools/check_events.py
python .workbuddy/tools/check_members.py
python .workbuddy/tools/check_native_symbols.py
python .workbuddy/tools/check_svg_layout.py
python .workbuddy/tools/check_ui_contract.py
python .workbuddy/tools/check_unity_api.py
python .workbuddy/tools/check_usings.py
```

结果：

| 校验 | 结果 |
|---|---|
| check_arity | PASS |
| check_code | PASS |
| check_events | PASS |
| check_members | PASS |
| check_native_symbols | PASS |
| check_svg_layout | PASS（22 个文件，0 待处理） |
| check_ui_contract | PASS（15 视图全部命中；负向测试仍能报错） |
| check_unity_api | PASS |
| check_usings | FAIL（**已知误报**：`BuildApk.cs` 的 `BuildResult` 属 `UnityEditor.Build.Reporting`，与本次无关，文件未改动） |

### 4.2 结构 / 几何一致性

```bash
# 1) 缓存与磁盘一致
python .workbuddy/tools/gen_ui_prefab_cache.py --check
# 期望：OK  缓存与磁盘一致

# 2) 重生成后与"手改版基线"逐节点比对
python .workbuddy/tools/diff_ui_prefabs.py --base <手改版备份目录>
# 期望：全部 OK（结构与几何一致）
```

实测：跑 **全量重建**（菜单 `Tools/塔防/自动化（无弹窗）/生成 UI 预制体（全量重建）`）后，
与手改版基线逐节点比对 —— 14 个预制体**全部结构与几何一致**。

> 唯一例外：`PauseView` 面板高度。手改版是 `560×6`（高 6），生成器产出 `560×520`。
> 高 6 会让 4 个按钮（y 从 +60 到 -210）全部落在面板外，经确认属**误改**，
> 生成器保持 520（正确值），不向手改版的 6 对齐。

### 4.3 Unity 实测

- **节点数核对**：14 个预制体的 `GetComponentsInChildren<Transform>(true).Length` 全部与缓存一致
  （HudView 23、ConfirmView 12、SellConfirmView 15、MainMenuView 19、SelectView 14、
  LevelDetailView 25、LevelClearView 15、TipsView 3、TowerInfoView 11、PauseView 12、
  SettingView 18、TowerCodexView 15、TowerCodexItem 13、SelectLevelItem 3）。
- **运行期路径解析**：把 View 脚本里所有 `transform.Find(...)` 路径在真实预制体上跑一遍，
  全部 `FOUND`（含 `Bg_Gold/GoldText`、`Panel/TopBar/BodyTitle`、`Panel/StatBg/StarText`、
  `Panel/TopBar`、`TipText` 等）。
- **HudView 子节点断言**：实际子节点恰为
  `Bg_Gold / Bg_Hp / Bg_Round / Btn_Tower_Normal / Btn_Tower_Power / Btn_Tower_Retard / SpeedButton / StartButton`
  —— Pierce / Laser 已删、文本已下沉，符合预期。

### 4.4 一句话结论

**生成器、缓存、引用代码三方与磁盘上的手改预制体完全对齐**；再跑一次全量重建不会冲掉任何手改，
静态校验除一个与本次无关的已知误报外全绿，Unity 侧节点数与运行期路径全部验证通过。

---

## 5. 第二轮同步（2026-10-12 晚）：SelectLevelItem 尺寸与激活态

用户再次手改 `Assets/Prefabs/UI/SelectLevelItem.prefab`。字段级比对后确认**仅 2 处改动**：

| 变动 | 节点 | 旧值 | 新值 | 说明 |
|---|---|---|---|---|
| `=` | `SelectLevelItem` | `1500×650` | **`1250×550`** | 卡片尺寸 |
| `=` | `SelectLevelItem` | `active: true` | **`false`** | 根节点禁用 |

### 5.1 连带改动：视口宽必须跟随卡片宽

卡片尺寸一变，**吸附硬约束「Viewport 宽 ≡ 卡片宽」**就要求视口同步收窄，否则居中/吸附全部错位。
`SelectViewportW` 定义为 `= SelectItemW`，所以视口自动跟随：

| 节点 | 字段 | 旧值 | 新值 |
|---|---|---|---|
| `SelectView/Panel/List/Viewport` | `sizeDelta` | `1500×500` | **`1250×500`** |
| `SelectView/Panel/List/Viewport` | `anchoredPosition.x` | `-750` | **`-625`**（= −1250/2） |

两条约束复核（可视区 List 仍是整页 1920）：步长 `1250+56 = 1306` ∈ `[视口宽 1250, 可视区宽 1920)` ✅
——既满足「首末条能精确居中」，也满足「邻卡可见」（左右邻卡各露约 279px）。

### 5.2 对应代码位置

| 文件 | 位置 | 改动 |
|---|---|---|
| `Assets/Editor/UIPrefabBuilder.cs` | `SelectItemW` / `SelectItemH` | `1500f/650f` → **`1250f/550f`** |
| 同上 | `SelectViewportW` | `= SelectItemW`，无需改（自动跟随） |
| 同上 | `BuildSelectItemPrefab()` | 保存前新增 `go.SetActive(false)`（复现根节点禁用） |
| `Assets/Scripts/UI/SelectView.cs` | `ItemWidth` | `1500f` → **`1250f`**（用于估算未实例化条目位置） |

> `ItemGap`（56）与 `FocusFalloff`（`= ItemWidth + ItemGap`，表达式）无需改。
> 三处尺寸清单必须成套改：`UIPrefabBuilder.SelectItemW/SelectItemH` ↔ `SelectView.ItemWidth` ↔ 条目登记名 `SelectLevelItem`。

### 5.3 关于根节点 `active=false`

经确认**原样同步**（非误改）。确认无害的依据：`LoopListView2.ItemPool.CreateItem()` 在实例化后
**无条件**执行 `go.SetActive(true)`（插件源码第 101 行），且 `ItemPool.Init()` 自己还会先把源 prefab
`SetActive(false)`。实测实例化出的条目 `activeInHierarchy=True` ✅。
已在生成器该行留注释：若日后改用不强制激活的池化实现，须删掉这一句。

### 5.4 验证结论

- **重生成保真**：全量重建后，新旧缓存差异**恰好 4 项**（卡片 `active`/`sizeDelta` + 视口 `sizeDelta`/`anchoredPosition`），
  其余 13 个预制体零变化 → 说明生成器已如实复现手改版，再跑生成器不会冲掉这次手改。
- **静态校验**：`gen_ui_prefab_cache.py --check` → OK（14 prefab / 198 节点）；`check_ui_contract.py` → PASS；
  6 项静态校验 PASS（`check_usings.py` 报的 `BuildApk.cs` 为**既有误报**，与本次无关）。
- **Unity 实测**（播放模式走 `GameFlowManager.OpenSelect()` 真实流程）：
  - 缓存视口 `c2 = (1250, 250)`（= 卡片宽，硬约束成立）
  - `shown = 3`、`total = 8`、`center = 2` 且 `distToSnapCenter = 0`
  - 卡片实测尺寸 `1250×550`，邻居距离 `±1306`（= 1250 + 56）
  - 左右箭头双向切换居中关（2 → 3 → 2）；`MovePanelToItemIndex(6)` 内容可横向平移
  - 点非居中卡片 → `target=1 / pendingEnter=2`（"先滑到正中、再进关"链路正常）
  - 运行期无任何 `[Select]` 相关错误或警告
