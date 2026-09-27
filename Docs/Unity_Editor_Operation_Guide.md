# FreeTower M0 · Unity 编辑器操作指南

> 适用工程：`D:\FreedomTower`　|　主场景：`Assets/Scenes/main.unity`
> 配置表目录：`D:\FreedomTower\Luban`　|　目标：**单回合闭环可跑通并验收**
> 本指南按「照着点就能跑起来」组织。每一步都写了：**在哪点 → 设什么 → 应该看到什么 → 出问题怎么办**。

---

## 0. 总览：正常流程只有 4 步

```
① Luban 导出配置表          （双击一个 .bat）
② Unity 菜单：一键资源准备   （点一次，等它跑完）
③ Unity 菜单：自检           （点一次，看有没有 ✘）
④ 打开 main.unity → Play     （按 16 项验收清单过一遍）
```

只有第 ⑤ 步以后（验证真 AB / 出包）才需要额外操作。

菜单全部集中在 Unity 顶部菜单栏的 **`Tools ▸ 塔防`** 下：

| 菜单项 | 作用 | 何时用 |
|---|---|---|
| `0. 自检（先跑这个）` | 检查全部前提条件，给出 ✘/! 报告 | 每次改完资源都跑 |
| `一键完成 M0 资源准备` | 按正确顺序跑完 1~8 步 | **正常流程只需要点这一个** |
| `1. 生成占位美术` | 程序生成格子/箭头/血条/子弹贴图 | 向导会自动跑 |
| `2. 转换防御塔预制体` | UGUI → 世界空间 SpriteRenderer | 向导会自动跑 |
| `3. 生成战斗预制体` | 子弹 + **全部 119 个怪物**（去物理 / 挂 BaseEnemy / 自适应血条） | 向导会自动跑 |
| `4. 清理选中预制体的物理组件` | 手动清理指定预制体 | 美术包更新后用 |
| `4b. 清理全部战斗预制体的物理组件` | 批量清理 | 向导会自动跑 |
| `5. 生成 UI 预制体` | HUD + 提示层 | 向导会自动跑 |
| `6. 配置工程设置` | Tag / 渲染排序 / Build Settings / 物理 | 向导会自动跑 |
| `7. 搭建 main 场景` | 在 main.unity 里建层级并接线 | 向导会自动跑 |
| `8a. 按 ResTable 打 AssetBundle 标记` | 按唯一数据源自动打标 | 向导会自动跑 |
| `8b. 打包 AssetBundle` | 构建 AB 到 StreamingAssets | 验证真 AB / 出包前 |
| `8b-严格模式 打包` | 引用缺失即构建失败 | 出正式包前 |
| `8c. 清除全部 AssetBundle 标记` | 重新规划分包时用 | 慎用 |
| `9. 导入全部怪物` | 单独重跑"导入全部怪物"（美术包更新后用） | 向导已包含 |

---

## 1. 第 ① 步：导出配置表（Luban）

### 操作

在文件资源管理器中进入：

```
D:\FreedomTower\Luban\
```

**双击 `gen_code_json.bat`**（不要用“以管理员身份运行”，也不需要先 cd 到某目录 —— 脚本已用 `%~dp0` 以自身路径为基准）。

### 预期输出

命令行窗口先打印前置校验，最后出现：

```
== succ ==
--- 产物自检 ---
  OK  tbenemydata.json
  OK  tbtowerinfo.json
  ...（共 8 项）
```

### 产物去向

| 产物 | 位置 |
|---|---|
| C# 配置类 | `Assets/Gen/*.cs`（命名空间 `cfg`） |
| JSON 数据 | `Assets/ConfigJson/*.json` |

### 出问题怎么办

| 现象 | 原因 | 处理 |
|---|---|---|
| `You must install .NET to run this application` / 提示需要 .NET 6 | 本机只有更高版本运行时 | 脚本已内置 `DOTNET_ROLL_FORWARD=LatestMajor`。若仍报错，说明 .NET 运行时完全没装 → 装一个 .NET 6/7/8 Desktop Runtime |
| `unknown argument: -d` | 旧版脚本漏了 `--` 分隔符 | 本仓库的脚本已修好；若你手上有旧副本，用本仓库的版本覆盖 |
| `== succ ==` 但自检报某个 json `MISSING` | 对应 xlsx 被移动/改名 | 检查 `Luban/Config/Datas/` 下 8 个 xlsx 是否都在 |
| 导出的数据里 `~$xxx.xlsx` 报错 | Office 锁文件被当成源表 | 关闭 Excel 后删除 `Luban/Config/Datas/~$*.xlsx`（此规则已加入 `.gitignore`） |

> ⚠️ **每次改完 xlsx 都要重跑这个 bat**，然后回到 Unity 等它自动重新导入（Console 会看到 `[Config] 配置加载完成`）。

---

## 2. 第 ② 步：一键资源准备（Unity 内）

### 操作

1. 打开 Unity 工程 `D:\FreedomTower`（Unity 2022.3 LTS）。
2. 等首次编译完成。**Console 没有红色 Error 才继续**。
3. 菜单栏 → **`Tools ▸ 塔防 ▸ 一键完成 M0 资源准备`**。
4. 弹窗列出将要执行的 8 个步骤，点 **「开始执行」**。
5. 中途会弹出「保存当前场景」的提示 → 点 **「保存」**（这一步会重建 `main.unity`）。
6. 等进度条走完（约 10~60 秒，取决于机器）。

### 它会做什么（以及为什么是这个顺序）

| 序 | 动作 | 为什么必须先做 |
|---|---|---|
| 1 | 配置工程设置 | 后面要给 Canvas 打 `UICanvas` Tag，**Tag 不存在时赋值会直接抛异常** |
| 2 | 生成占位美术 | 怪物血条要用生成的 `HP_Bar_*` 贴图 |
| 3 | 转换防御塔预制体 | 场景要引用转换后的塔；原 UGUI 版自动备份 |
| 4 | 生成战斗预制体 | 场景不引用 prefab 本体，但后面的物理清理要扫到它们 |
| 5 | 清理物理组件 | 需求 8：彻底去物理化 |
| 6 | 生成 UI 预制体 | 关卡流程要加载 `HudView` / `TipsView` |
| 7 | 搭建 main 场景 | 前面所有产物作为引用目标 |
| 8 | 打 AssetBundle 标记 | 需要在所有资源都就位之后 |

### 预期结果

弹窗显示 **「全部完成」**，并提示下一步。Console 里有一条 `[M0] 一键资源准备完成：` 开头的分级报告，格式：

```
── 配置工程设置 ──
  ✔ 已添加 Tag「UICanvas」
  ✔ Transparency Sort Mode = Custom Axis (0,-1,0)（Y 越小越靠前，实现前后遮挡）
  ✔ Build Settings 已设为仅 Assets/Scenes/main.unity
  ✔ 已关闭 Physics2D 自动模拟（战斗判定不依赖物理，Profiler 的 Physics2D 分区将为 0）
  ...
── 转换防御塔预制体 → Assets/Prefabs/Tower/Tower_Normal.prefab ──
  ✔ 原 UGUI 版已备份到 Assets/Prefabs/Tower/_UI_Source/Tower_Normal_UI.prefab
  ✔ 已生成世界空间版（根 scale 0.8，barbette 300 / Img_gun 301）
  ✔ 实测显示尺寸：宽 1.02 × 高 1.02 世界单位（格子 1.0）
  ...
── 生成战斗预制体 → Assets/Prefabs/Enemy/Enemy_Rat.prefab ──
  ✔ 已移除 1 个物理组件（Collider2D / Rigidbody2D）
  ✔ 已挂 HpBar（Bg + Fill，本地 y=2.8）
  ✔ Enemy_Rat.prefab 实测显示尺寸：宽 x.xx × 高 y.yy 世界单位（格子 1.0）
  ! 若宽 x.xx 与格子 1.0 比例不合适，改 Luban/Config/Datas/EnemyData.xlsx 的 scale 列...
```

### ⚠️ 两个必须留意的点

**① 怪物显示尺寸需要你目视确认一次。**
怪物美术是分部件 2D 骨骼式结构（`Rat.png` 是 960×640 图集，Body 精灵 640×320 像素，PPU=100），
prefab 根节点自带 `scale = 0.5`。M0 的配置默认值是 `scale = 0.5`，
即最终 `0.5 × 0.5 = 0.25`，怪物约 **1.6 世界单位宽 ≈ 1.6 个格子**。

- 如果**看起来过大**：打开 `Luban/Config/Datas/EnemyData.xlsx`，把 `scale` 列改小（例如 `0.5` → `0.3`），
  保存 → 重跑 `gen_code_json.bat` → 回 Unity 等导入。**不需要改任何代码。**
- 如果**看起来过小**：同上，把 `scale` 调大。
- 语义：**最终缩放 = prefab 根节点的缩放 × 配置表的 scale**。
  所以 `scale = 1` 表示"保持美术在 prefab 里授权的原始缩放"（那样怪物约 3.2 格宽，偏大）。
- 脚本在生成怪物预制体时会打印实测包围盒宽度，可以据此精确标定。

**② 如果 HUD 里的中文显示成方块**，见本文 §9「字体」。

---

## 3. 第 ③ 步：自检

### 操作

菜单栏 → **`Tools ▸ 塔防 ▸ 0. 自检（先跑这个）`**

### 预期结果

弹窗：**「错误 0 · 警告 0」**，Console 报告里全是 ✔。



自检覆盖 6 类：

| 检查项 | 内容 |
|---|---|
| ① 配置表 | 8 个 json 是否存在、能否解析、各有多少条记录 |
| ② 资源地址表 | `ResTable` 登记的每一条资源路径是否真实存在 |
| ③ 关键预制体 | 塔是否已转世界空间、怪物有无物理组件、HUD/Tips 节点名是否与代码一致 |
| ④ 主场景 | 16 个必需对象是否齐备、`UICanvas` 的 Tag 是否正确写入 |
| ⑤ 工程设置 | Tag / 渲染排序 / Build Settings |
| ⑥ AssetBundle | 已打包时列出各包体积；未打包则给出提醒（不影响编辑器试跑） |

### 常见 ✘ 与处理

| ✘ 内容 | 处理 |
|---|---|
| `xxx.json 缺失 —— 请执行 Luban/gen_code_json.bat` | 回到第 ① 步 |
| `「Enemy_Rat」指向的文件不存在` | 执行 `3. 生成战斗预制体`（或直接再跑一次一键向导） |
| `Tower_Normal.prefab 仍是 UGUI（带 RectTransform）` | 执行 `2. 转换防御塔预制体` |
| `Enemy_Rat.prefab 上仍有物理组件` | 执行 `4b. 清理全部战斗预制体的物理组件` |
| `HudView 缺少子节点「GoldText」` | 执行 `5. 生成 UI 预制体` |
| `场景中缺少对象「BattleRoot」` | 执行 `7. 搭建 main 场景` |
| `场景里没有任何对象带 Tag「UICanvas」` | 执行 `6. 配置工程设置`，再执行 `7. 搭建 main 场景` |
| `Tag「UICanvas」缺失` | 执行 `6. 配置工程设置` |

---

## 4. 第 ④ 步：Play 试跑与验收

### 操作

1. 在 Project 窗口双击打开 **`Assets/Scenes/main.unity`**。
2. 确认 Hierarchy 里能看到（脚本自动搭好的）：
   ```
   Camera                （Tag = MainCamera，正交）
   EventSystem
   Launcher
   UICanvas              （Tag = UICanvas）
     ├── BgPanel
     ├── NormalPanel
     └── TipsPanel
   BattleRoot
     ├── Background
     ├── BoardRoot
     ├── PathRoot
     ├── TowerRoot
     ├── EnemyRoot
     └── BulletRoot
   GameFlow
   GameSceneLauncher
   ```
3. 点顶部 **▶ Play**。

### 启动后应该看到

**Console（按顺序）**：

```
[Res] 使用编辑器直读模式（EditorResLoader）。如需验证真 AB 链路，请在 Player Settings 的 Scripting Define Symbols 中加入 FORCE_AB。
[Res] 预加载自检通过，共 8 个资源全部就绪。
[Config] 配置加载完成
  TBEnemyData  : 9 条 ...（共 8 张表）
[Config] 交叉引用自检通过。
[Combat] 空间哈希已按配置重建：EnemyGrid: cells=0, enemies=0, cellSize=2
[Flow] 关卡 1「关卡 1」就绪：棋盘 16×9，格子 1 世界单位，回合 10 个
  路径 25 格：(0,0) → (0,1) → ... → (8,15)
```

**画面**：

- 一块 16×9 的棋盘铺在中央（深色格线）；
- 起点格偏绿（左上角），终点格偏红（右下角）；
- 一条由白色小三角组成的路径箭头，从起点连到终点；
- 左上角两行字：`金币 100` / `生命 10`；顶部中央 `准备中`；
- 底部两个按钮：`建塔`（左）与 `开始`（右）。

### 验收清单（16 项，逐条勾）

**【启动与配置】**
- [ ] 1. Play 全程 Console 无 `Exception` / `NullReferenceException`
- [ ] 2. Console 打印 8 张表的记录数，与 Excel 行数一致
- [ ] 3. 棋盘行列数（16×9）、起终点位置与 `TBLevelMap` 配置一致

**【配置驱动验证（关键）】**
- [ ] 4. 打开 `Luban/Config/Datas/EnemyData.xlsx`，把 id=1 的 `hp` 从 `100` 改成 `50` → 保存 → 重跑 `gen_code_json.bat` → 回 Unity 等导入 → Play：怪物明显更快被打死

**【棋盘与建造】**
- [ ] 5. 点 `建塔` → 鼠标移动时有一个半透明的塔跟随鼠标
- [ ] 6. 移到可建造格 → 该格**变绿**；移到障碍格 → 该格**变红**
- [ ] 7. 在绿格上左键 → 塔落位，金币从 100 减到 **80**（＝ `TBTowerInfo.id=1` 的 `prices`）
- [ ] 8. 在已有塔的格上尝试 → 变红 + 提示「该位置已有防御塔」，不扣钱
- [ ] 9. **堵路测试**：在路径必经的窄口两旁连续建塔，最后一下会提示「不能完全阻断怪物路径」，且**金币没有变化**
- [ ] 10. 建塔后路径箭头**实时改道**（绕开新塔）—— 这是《坚守阵地》的核心机制

**【战斗判定（需求 8 重点）】**
- [ ] 11. 点 `开始` → 怪物从起点出现并沿路径走向终点
- [ ] 12. 塔会**转向**瞄准怪物，到达射程后开火，子弹飞向怪物
- [ ] 13. 怪物头顶血条随受击**从左向右缩短**
- [ ] 14. **无目标时塔不开火**：把塔建在离路径很远的地方（射程外），观察它完全不发射子弹
- [ ] 15. 打开 **Window ▸ Analysis ▸ Profiler** → 勾选 `Physics` 与 `Physics2D` → Play：两个分区**恒为 0**

**【经济与生命】**
- [ ] 16. 怪物死亡时金币增加（默认 +5）
- [ ] 17. 让怪物走到终点：**生命值减少**（默认 −1/只）
- [ ] 18. 反复漏怪直到生命归零 → 顶部提示「防御失败……」，`开始` 按钮变「已失败」

**【回合闭环】**
- [ ] 19. 本回合（一波）怪物清空后 → 顶部显示「回合 N 完成」，`开始` 按钮变「下一回合」，再次点击可进入下一回合
- [ ] 20. 打完关卡 1 的全部 10 个回合 → 提示「恭喜通关！」

**【资源加载（需求 7 重点）】**
- [ ] 21. 编辑器模拟模式下所有资源正常加载（上面的表现即为通过）
- [ ] 22. 加 `FORCE_AB` 宏后重跑仍正常（见 §6）
- [ ] 23. 切关卡/退出后 Console 无 `[Res] 包「xxx」尚未加载` 的警告

> 验收 4 / 9 / 14 / 15 是最能证明"做对了"的四条，建议重点看。

### 调试快捷键

| 按键 | 作用 |
|---|---|
| `F1` | 打印完整状态（流程 / 玩家 / 波次 / 战斗 / 空间哈希） |
| `F2` | 直接获胜（省去打完 10 回合的时间） |
| `F3` | （已移除）朝向由常数表 `Global.artFaceLeft` 决定；若朝向不对改这一列并重跑导出 |
| `空格` | 相机回到自适应视野 |
| `滚轮` | 缩放（自适应尺寸的 0.5× ~ 2.5×） |
| `右键`（未在放置时） | **售卖鼠标下的防御塔**（M0 简化交互；返还金额见 `Global.sellRefundRate`） |
| `右键` / `ESC`（放置中） | 取消建塔放置 |

---

## 5. 调参：一切数值都在 Excel 里

**改数值不需要碰代码。** 全部走配置表：

| 想改什么 | 改哪张表的哪一列 |
|---|---|
| 怪物血量/速度/护甲/奖励/漏怪伤害/显示大小 | `EnemyData.xlsx` 的 `hp` / `speed` / `armor` / `reward` / `damageToPlayer` / `scale` |
| 塔的攻击力/射程/冷却/价格/索敌策略 | `TowerInfo.xlsx` 的 `power` / `radius` / `CD` / `prices` / `targetMode` |
| 子弹速度/命中半径/存活时间/穿透/爆炸 | `BulletData.xlsx` 的 `speed` / `hitRadius` / `lifeTimeMs` / `pierce` / `aoeRadius` |
| 关卡初始金币与生命、回合数量 | `SceneInfo.xlsx` 的 `initialGold` / `initialHp` / `RoundList` |
| 每波出什么怪、间隔多久 | `EnemyList.xlsx` 的 `EnemyIndexs`（怪物 id 列表）/ `interval` / `enemyInterval` |
| 每个回合包含哪些波次 | `RoundData.xlsx` 的 `EnemyIndexs` |
| 棋盘布局 | `LevelMap.xlsx` 的 `cells`（每行一个字符串，**字符数必须等于 `cols`**）|
| 格子尺寸、同屏怪物上限、调试日志开关 | `Global.xlsx` 的 `cellSize` / `maxEnemyAlive` / `showDebugLog` |
| **回合节奏与玩法常数** | `Global.xlsx` 的 `autoNextRoundDelayMs`（回合完成后自动开下一回合的毫秒数，0=不自动）、
  `autoStartRoundDelayMs`（关卡就绪后自动开第一回合，0=需手动点）、`sellRefundRate`（卖塔返还比例）、
  `artFaceLeft`（怪物美术默认朝向是否朝左，用来修正水平翻转） |

### 棋盘字符集（`LevelMap.cells`）

| 字符 | 含义 | 怪物可通行 | 可建塔 |
|---|---|---|---|
| `S` | 起点 | ✅ | ❌ |
| `E` | 终点 | ✅ | ❌ |
| `.` | 普通地砖 | ✅ | ✅ |
| `#` | 障碍 | ❌ | ❌ |
| `X` | 空洞 | ❌ | ❌ |
| `P` | 装饰地砖 | ✅ | ❌ |

### `targetMode` 索敌策略

| 值 | 含义 |
|---|---|
| `0` | **路径进度最靠前（最危险）优先** — 塔防标准策略，默认 |
| `1` | 距离自身最近优先 |
| `2` | 当前血量最高优先 |

### 改完必须做的事

```
改 xlsx → 保存 → 双击 Luban/gen_code_json.bat → 回 Unity 等自动导入 → Play
```

---

## 6. 玩法交互说明（自动回合 / 卖塔 / 地图）

### 自动回合
回合完成后会**自动开始下一回合**，间隔由常数表 `Global.autoNextRoundDelayMs`（默认 5000ms）决定。
期间「下一回合」按钮会显示剩余秒数（`下一回合(3)`），点一下可立即开始。
设为 `0` 则恢复为手动推进。

> **`Global.xlsx` 是全工程唯一的常数配置表**（单行，id 固定 1）。
> 以后所有全局常数都加在这张表上——新增一列即可，`GlobalConfig.cs` 里补一个只读属性，
> 然后重跑 `gen_code_json.bat`。**不要再新建第二张常数表**，否则会出现两张表互相竞争。

### 卖塔（右键）
右键点击已建造的防御塔即直接出售，返还 `TBTowerInfo.sellPrice × Global.sellRefundRate`，
同时释放格子、把该格从"墙"还原、触发路径重算。放置预览中右键仍是取消放置。
后续做"选中塔 → 弹菜单 → 确认"交互时，只需替换 `TowerPlacement.TrySellUnderCursor`。

### 地图没有障碍物
`LevelMap.xlsx` 的棋盘已改为**全开阔**（只有 `S` 和 `E`），与原版《坚守阵地》一致：
路径完全由玩家的塔塑造。字符集里的 `#`/`X`/`P` 仍受支持，需要做关卡设计时随时可以用回来。

---

## 7. 验证真 AssetBundle 链路（需求 7 验收）

编辑器默认走 **AssetDatabase 直读**（改一张图立刻生效，不用打包）。要验证真机才走的 AB 路径：

### 操作

1. 菜单 → **`Tools ▸ 塔防 ▸ 8b. 打包 AssetBundle`**。
   预期 Console 输出各包体积，例如：
   ```
   ✔ 成功产出 7 个包：
     · config             12.3 KB
     · core_art           45.6 KB
     · tower_normal       18.9 KB
     · bullet_normal       1.2 KB
     · enemy_common      320.4 KB
     · ui_hud              9.8 KB
     · Windows            （主清单）
   ✔ 主清单包就绪：Windows
   ```
2. 菜单 → **`Edit ▸ Project Settings ▸ Player`** → 展开 **`Other Settings`** → 找到 **`Scripting Define Symbols`** → 添加一行 **`FORCE_AB`** → 点空白处确认。
3. 等 Unity 重新编译完成。
4. 打开 `main.unity` → Play。

### 预期结果

Console 首行变为：

```
[Res] AssetBundle 模式初始化完成。平台=Windows，已加载包 2 个，常驻包 2 个。
```

> ⚠️ **平台目录名要对得上**。AB 会被构建到
> `Assets/StreamingAssets/AssetBundles/<平台>/`，其中 `<平台>` 由**当前 Build Target** 决定
> （`Windows` / `Android` / `iOS` / `macOS` / `Linux` / `WebGL`）。
> 所以：**先切好 Build Target，再打包 AB**。切了平台必须重新打一次 AB。

### 验证完记得撤掉 `FORCE_AB`

否则开发期每次改资源都要重新打包 AB，效率会崩。撤掉后 Unity 会切回直读模式。

### 模拟"引用计数归零、无资源泄漏"

切到 AB 模式后，`BundleResLoader` 会做包级引用计数。可以在 Console 里观察：

- 进关卡时会调用 `Preload`，涉及的包引用计数 +1；
- 退出/切关时对不再需要的包调用 `ReleaseBundle`，计数归零后 `Unload(false)`。

> 注意：`Unload(false)` 不会销毁仍在场景中使用的对象 —— 这是刻意的，
> 传 `true` 会把还在用的贴图一起销毁导致花屏。M0 只有单关卡，尚未接入"切关整包释放"流程，M1 补。

### 关于配置表的位置（重要）

配置表 JSON 只有一个位置：**`Assets/ConfigJson/`**，由 `Luban/gen_code_json.bat` 直接产出。
它同时满足两个需求：
- 编辑器直读（走 `AssetDatabase`，改完重导即可 Play，不用打 AB）
- 真机从 `config` 资源包读（`ABNameSetter` 会把这一目录标进 `config` 包）

> ⚠️ **为什么不用 `Assets/StreamingAssets/json/`？** 我最初把它放在那里（Luban 的默认习惯），
> 结果启动时 8 张表全部读取失败。原因是 **StreamingAssets 下的文件被 Unity 当作"原始文件"
> （DefaultAsset）处理，不会导入成 `TextAsset`** —— 于是出现一种很隐蔽的现象：
> `LoadAssetAtPath<Object>()` 能拿到（"资源存在"自检会通过），
> 但 `LoadAssetAtPath<TextAsset>()` 返回 null，读内容必失败。
> 配置表要能被编辑器读、又要能打进 AB，就必须放在普通 Assets 目录下。
>
> 如果你看到类似的 `[Res] 文本资源「xxx」加载失败` 错误，报错信息里会直接指出这一点。

> 动手改配置数据时，**永远改 `Luban/Config/Datas/*.xlsx`**（然后重跑 bat）。
> 不要手改 `ConfigJson/` 下的 JSON —— 它们是导出产物，下次导出会被覆盖。

---

## 8. 打包 PC 版

1. 菜单 → `Tools ▸ 塔防 ▸ 8b. 打包 AssetBundle`（务必先做）。
2. 菜单 → `File ▸ Build Settings` → Platform 选 **Windows / Mac / Linux** → `Build`。
3. 首次打包建议在 **Player Settings ▸ Other Settings** 里确认：
   - `Scripting Backend`：Mono 或 IL2CPP 都可以（M0 不需要 HybridCLR）
   - `Api Compatibility Level`：`.NET Standard 2.1`
   - `Scripting Define Symbols`：**已移除 `FORCE_AB`**（打包后自动走 AB，不需要这个宏）

---

## 9. 目录与关键文件地图

```
D:\FreedomTower\
├── Luban\                              ★ 配置表工具链与源表（唯一配置来源）
│   ├── Config\Datas\*.xlsx               策划编辑的源表（10 张）
│   ├── Config\Defines\__root__.xml       Luban 表定义根
│   ├── Tools\Luban.ClientServer\         Luban CLI
│   └── gen_code_json.bat                 ★ 双击导出
│
├── Assets\
│   ├── Gen\                            Luban 生成的 C# 配置类（勿手改）
│   ├── LubanLib\                       Bright.Serialization + SimpleJSON（勿手改）
│   ├── Scenes\main.unity               ★ 唯一主场景
│   ├── Editor\                         ★ Editor 工具（菜单 Tools ▸ 塔防）
│   ├── Art\Generated\                  程序生成的占位美术
│   ├── ConfigJson\                     ★ Luban 导出的配置 json（编辑器直读 + 进 config 包）
│   ├── Prefabs\
│   │   ├── Tower\Tower_Normal.prefab    世界空间 SpriteRenderer（原 UGUI 版在 _UI_Source\）
│   │   ├── Tower\_UI_Source\            原 UGUI 版备份（不要放进 AB）
│   │   ├── Bullet\Bullet_Normal.prefab
│   │   ├── Enemy\Enemy_<怪名>.prefab   ★ 119 个战斗怪物（由「9. 导入全部怪物」生成）
│   │   └── UI\HudView.prefab, TipsView.prefab
│   ├── _UIAssets\                       美术资源（塔贴图 / 怪物包 / 背景）
│   └── Scripts\
│       ├── Core\Res\                   ★ AB 资源系统（ResTable 是唯一寻址源）
│       ├── Core\Combat\                ★ 去物理战斗系统（EnemyGrid + CombatSystem）
│       ├── Core\Manager\               管理器基类 + 玩家数据
│       ├── Data\                       配置读取层（Configs + 6 个包装类）
│       ├── Game\                       棋盘 / 关卡流程 / 路径渲染
│       ├── Round\WaveManager.cs        波次时间轴
│       ├── Enemy\  Tower\  Bullet\     战斗实体
│       ├── UI\  Core\UI\               HUD / 提示 / UI 框架
│       ├── Camera\CameraController.cs  2D 正交相机
│       └── AStarWrapper\               A* 寻路（只建数据，不生成物件）
│
└── Docs\
    ├── TowerDefense_Design_and_Implementation.md   ★ 设计与实施文档（v2.1）
    └── Unity_Editor_Operation_Guide.md             ★ 本文件
```

### 需要改代码时看哪儿

| 想改 | 文件 |
|---|---|
| 新增/删除逻辑资源名 | `Assets/Scripts/Core/Res/ResTable.cs`（**唯一寻址数据源**） |
| 调整分包 | `Assets/Scripts/Core/Res/ResBundle.cs` |
| 索敌/开火/命中逻辑 | `BaseTower.cs` / `EnemyGrid.cs` / `CombatSystem.cs` / `BaseBullet.cs` |
| 关卡流程 | `Game/GameFlowManager.cs` |
| 波次时间轴 | `Round/WaveManager.cs` |
| 棋盘与坐标换算 | `Game/Board.cs`（`BoardGeometry` 是**唯一**坐标换算入口） |
| HUD 显示 | `UI/HudView.cs`（节点名与 `Editor/UIPrefabBuilder.cs` 必须成对改） |

---

## 10. 字体：如果 HUD 中文显示成方块

M0 的 HUD 使用 Unity **内置动态字体**（`LegacyRuntime.ttf`）。

| 平台 | 表现 |
|---|---|
| Windows / macOS 编辑器 | ✅ 正常（会回退到系统字体） |
| Windows / macOS 独立包 | ✅ 正常 |
| **Android / iOS** | ❌ 会显示成方块（包内没有系统字体可回退） |

### 出移动包前的处理

1. 准备一个含中文字形的 TTF（如思源黑体 `SourceHanSansSC-Regular.otf`，注意授权）。
2. 拖进 `Assets/_UIAssets/Fonts/`。
3. 选中它 → Inspector 顶部 **`Font Size`** 设 `16`，`Character` 选 **`Unicode`**（或自定义只勾常用字，控制包体），点 Apply。
4. 打开 `Assets/Prefabs/UI/HudView.prefab` 与 `TipsView.prefab` → 选中里面每个带 `Text` 的节点 → **Font** 换成刚导入的字体。
5. 如果导入的是 OTF，也可以改用 TextMeshPro（需另做 TMP Font Asset）。

---

## 11. 故障排查速查表

| 现象 | 可能原因 | 处理 |
|---|---|---|
| Console 大量 `The type or namespace name 'X' could not be found` | Unity 还没编译完 / 有编译错误 | 看 Console 第一条红色错误；`Assets/Editor` 里的脚本会编进 `Assembly-CSharp-Editor`，能引用 `Assets/Scripts` 的类型 |
| `[Res] 资源地址表中找不到逻辑名「xxx」` | `ResTable` 没登记 | 在 `ResTable.cs` 加一条，并让 EditorPath 与真实路径一致 |
| `[Res] 加载失败：逻辑名「Cell_Ground」` | 占位美术没生成 | 菜单 `1. 生成占位美术` |
| `[Res] 资源「xxx」是图片，但未以 Sprite 形式导入` | 贴图 Import 设置不对 | 选中该 png → Inspector → `Texture Type` = **Sprite (2D and UI)** → Apply。`EditorResLoader` 的报错里会直接给出这条修复指引 |
| `[Config] 读取失败：tbenemydata.json` | 没跑 Luban 导出，或文件不在 `Assets/ConfigJson/` | 第 ① 步；确认 Luban 的输出目录是 `Assets/ConfigJson` |
| `[Res] 文本资源「xxx」加载失败` 且路径含 `StreamingAssets` | StreamingAssets 下的文件不会导入成 TextAsset | 把配置表移到普通 Assets 目录（本工程用 `Assets/ConfigJson/`） |
| `[Flow] boardView 未连线` | 场景是手工搭的、引用没连 | 菜单 `7. 搭建 main 场景` |
| 画面全黑 / 看不到棋盘 | 相机不是 `MainCamera` Tag，或 `Camera.main` 为空 | 选中 Camera → Inspector → Tag 设为 `MainCamera`；或重跑 `7. 搭建 main 场景` |
| 按钮点了没反应 | 场景没有 `EventSystem` | 重跑 `7. 搭建 main 场景` |
| Console 刷 `AnimationEvent 'SetHead' … has no receiver!` | 美术包的 Attack/Death 动画内置了 AnimationEvent，但包里没提供接收脚本 | 已补 `MonsterAnimEventReceiver`（挂在 Animator 所在节点，并预填 正常/愤怒/死亡 三个头部贴图）；重新执行「9. 导入全部怪物」即可消除。缺了它不影响移动与战斗，只是头部贴图不会随状态变化 |
| **怪物出现了但不会移动、只待在起点** | **管理器被实例化了两份**：`Launcher` 用 `new` 创建管理器，而其它代码走 `.Instance`（懒创建）→ 一份被 tick、另一份承载数据 | 已在代码里修好；`BaseManager<T>` 现在会在检测到直接 `new` 时立刻报 Error。若再出现，看 Console 有没有 `[Manager] 检测到直接 new` |
| **没有任何怪物出现** | ① 没点「开始」按钮 ② 或 HUD 根本没打开（见上一行） ③ 或 A* 路径不可达 | 先确认左上角有 `金币/生命` 文字；Console 应打印 `[Wave] 回合 1 开始：N 个波次 / M 只怪`；若打印 `[AStar] 起点到终点不可达` 就检查 `LevelMap.xlsx` |
| 点 HUD 按钮时顺手把塔放下去了 | `EventSystem` 缺失导致 `IsPointerOverGameObject()` 永远 false | 重跑 `7. 搭建 main 场景` |
| 塔和怪的前后遮挡不对 | `Transparency Sort Mode` 没设 | 菜单 `6. 配置工程设置` |
| 棋盘生成但**没有路径箭头** | `Path_Arrow` 贴图缺失 | 菜单 `1. 生成占位美术`（箭头缺失不影响玩法，只是看不到路径） |
| 怪物不动 | 起点 `S` 或终点 `E` 不在 `LevelMap.cells` 里 | 检查 `LevelMap.xlsx`；Console 会打印 `[AStar] 网格缺少起点(S)或终点(E)` |
| 怪物穿墙 / 卡在障碍里 | `cells` 每行字符数 ≠ `cols` | 检查 `LevelMap.xlsx`；Console 会打印 `[Board]` 或 `[Flow] 棋盘配置校验未通过` |
| `[AStar] 起点到终点不可达` | 障碍把地图完全阻断 | 用 `LevelMap.xlsx` 改回一条通路 |
| 塔一直不开火 | 目标在射程外 / 怪物已被打光 | 属正常表现；Console 每 5 秒打印一次战斗统计（`TBGlobal.showDebugLog = 1` 时） |
| `[Combat] 检测到 N 次「无目标开火」` | 逻辑 bug | 这是自检告警，正常应恒为 0。请把该日志连同场景一起反馈 |
| AB 模式启动报 `包文件不存在` | 没打包 AB，或打的是别的平台的包 | 先切好 Build Target，再执行 `8b. 打包 AssetBundle` |
| AB 模式下某些资源丢失 | ResTable 的 `Bundle`/`Asset` 与真实资源不一致 | 执行 `8a. 按 ResTable 打 AssetBundle 标记`，再看它有没有报 ✘ |

---

## 12. 已知遗留与后续阶段

### M0 刻意未做的（不阻塞验收）

| 项 | 说明 |
|---|---|
| 选关界面 | 启动直接进关卡 1（`GameFlowManager.startLevelId = 0` → 取 `TBSceneInfo` 第一行）。想固定某关就在 `GameFlow.startLevelId` 填 id |
| 塔升级 / 出售 UI | `TowerManager.Sell()` 与 `TBTowerInfo.upgradeTo` 已就绪，缺 UI 接线（M2） |
| 伤害飘字 / 击杀特效 / 音效 | M2 |
| 结算界面 | M0 用 `TipsView` 文本代替 |
| 切关时的 AB 整包释放 | `ReleaseBundle` 已实现，但 M0 只有一关，未接入流程（M1） |
| 多塔型 / AOE / 减速 | `TBTowerInfo.effectType` 与 `TBBulletData` 字段已留好，实现留 M2 |
| 其余 118 个怪物 prefab 的战斗接入 | M0 只接了 `Enemy_Rat`；`ResTable` 加条目 + `EnemyData.resName` 指向即可扩展 |
| `Common/Animations` 下其余家族 | 同上，`EnemyData.animController` 填家族名即可 |

### 代码层面的已知遗留（不影响运行）

1. **`Assets/Scripts/Core/UIEventListenerManager.cs`** —— 里面还带着一个旧版 `MonoBehaviour UIEventListener`（已无人使用）。它不影响编译，但如果将来要用，建议删掉或改名，别让两个 UI 事件系统并存。
2. **`Assets/Scripts/AStarWrapper/AStarWrapper.cs` / `Singleton.cs`** —— 上游 A* 插件的原始文件，保持原样未动。
3. **`SuperScrollView/`（14MB）与 `Luban/Tools/`（25MB）** 仍在版本控制内，属必要依赖，保留。
4. **仓库历史体积仍是 2.17 GiB** —— `.gitignore` 已阻止继续增长，但历史提交里的大文件对象还在。要真正瘦身需 `git filter-repo` 重写历史 + force push，属破坏性操作，需要你确认后单独执行。
5. **`.gitattributes` 仍是 `* text=auto`**，会产生大量 CRLF 警告。建议补 Unity 专用配置，但可能触发一次大规模 renormalize diff，属于独立的一次提交。

---

## 13. 一页速查

```
【每次改配置表】
  改 Luban/Config/Datas/*.xlsx
  → 双击 Luban/gen_code_json.bat
  → 回 Unity 等导入
  → Tools ▸ 塔防 ▸ 0. 自检
  → Play

【每次改美术/预制体结构】
  Tools ▸ 塔防 ▸ 一键完成 M0 资源准备
  → Tools ▸ 塔防 ▸ 0. 自检
  → Play

【首次跑起来】
  ① gen_code_json.bat
  ② Tools ▸ 塔防 ▸ 一键完成 M0 资源准备
  ③ Tools ▸ 塔防 ▸ 0. 自检
  ④ 打开 Assets/Scenes/main.unity → Play

【验证真 AB】
  Tools ▸ 塔防 ▸ 8b. 打包 AssetBundle
  → Player Settings 加 FORCE_AB
  → Play（Console 应显示 BundleResLoader）
  → 验证完撤掉 FORCE_AB

【出包】
  切 Build Target
  → Tools ▸ 塔防 ▸ 8b. 打包 AssetBundle
  → File ▸ Build Settings ▸ Build
```
