# 《自由人塔防》· Unity 编辑器操作指南

> 适用工程：本工程　|　主场景：`Assets/Scenes/main.unity`
> 配置表目录：`Luban/`
> 目标：**M0~M3 全部可跑通并验收**
> 本指南按「照着点就能跑起来」组织。每一步都写了：**在哪点 → 设什么 → 应该看到什么 → 出问题怎么办**。

---

## 0. 总览：正常流程只有 4 步

```
① Luban 导出配置表          （双击一个 .bat）
② Unity 菜单：一键补齐资源   （点一次，等它跑完）
③ Unity 菜单：自检           （点一次，看有没有 ✘）
④ 打开 main.unity → Play     （按 M0 基线 + M2 + M3 验收清单过一遍）
```

> **M3 起开机流程变了**：Play 之后先出现**关卡选择界面**，点关卡才进对局。
> 调试时想跳过选关：在场景 `GameFlow` 对象的 `GameFlowManager` 上，把 `startLevelId` 填成关卡号即可。

只有第 ⑤ 步以后（验证真 AB / 出包）才需要额外操作。

菜单全部集中在 Unity 顶部菜单栏的 **`Tools ▸ 塔防`** 下：

> v2.2 更新（2026-09-29）：菜单已按"安全 / 危险"重新分层。
> **一级菜单只保留安全的日常入口**；破坏性的"删除+重建"式单步工具全部收进
> `Tools ▸ 塔防 ▸ 高级（单步重建）`，且一律带警告或需要确认。

**一级菜单（日常用）**

| 菜单项 | 作用 | 何时用 |
|---|---|---|
| `0. 自检（先跑这个）` | 检查全部前提条件，给出 ✘/! 报告 | 每次改完资源都跑 |
| `一键补齐 M0 资源（安全：只补缺失）` | 按正确顺序检查并补齐缺失产物；**已就绪的一律跳过，不覆盖手工成果** | **正常流程只需要点这一个** |
| `2. 配置工程设置` | Tag / 渲染排序 / Build Settings / 物理 | 向导会自动跑 |
| `3. 导出配置表（Luban）` | 把 `Luban/Config/Datas/*.xlsx` 导出为 `Assets/Gen` + `Assets/ConfigJson` | 改完 Excel 后 |
| `4. 按 ResTable 打 AssetBundle 标记` | 按唯一数据源自动打标 | 向导会自动跑 |
| `5. 打包 AssetBundle` | 构建 AB 到 StreamingAssets | 验证真 AB / 出包前 |

**高级（单步重建）—— 会删除并重建，慎用**

| 菜单项 | 作用 | 风险 |
|---|---|---|
| `生成占位美术` | 程序生成格子/箭头/血条/子弹贴图 | 覆盖 `Art/Generated` |
| `转换防御塔预制体` | UGUI → 世界空间 SpriteRenderer（三塔循环；**已合规的塔会跳过**） | 重建不合规的塔 prefab |
| `生成战斗预制体` | 子弹 + **全部 119 个怪物** | 覆盖子弹/怪物 prefab |
| `清理选中预制体的物理组件` | 手动清理指定预制体 | 改选中资源 |
| `清理全部战斗预制体的物理组件` | 批量清理 | 批量改 119 个 |
| `补缺 UI 预制体（安全：只补缺失）` | 只生成**不存在**的 UI prefab | 无（已存在的一律跳过） |
| `生成 UI 预制体（全量重建）` | HUD + 提示层 + 塔面板 + **关卡选择 / 暂停 / 设置** | **重建 UI prefab**；若含生成器不认识的节点会**中止** |
| `重建 main 场景（危险：会清空重建）` | 清空 main.unity 全部根对象后重建 | **抹掉场景里的手工接线**（原文件先备份到 `Assets/Scenes/_Backup/`） |
| `清除 ResTable 范围内的 AssetBundle 标记` | 重新规划分包时用 | 只清 `ResTable` 登记的资源，不再清全工程 |
| `5b. 严格模式打包（引用缺失即失败）` | 引用缺失即构建失败 | 出正式包前 |

**地图编辑（M3 新增）**

| 菜单项 | 作用 |
|---|---|
| `地图编辑器（可视化刷格子）` | 刷格子 / 标起终点 / 实时 BFS 连通性校验 / 导出 cells 字符串 |

---

## 1. 第 ① 步：导出配置表（Luban）

### 操作

在文件资源管理器中进入工程根目录下的：

```
Luban\
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

1. 打开本 Unity 工程（Unity 2022.3 LTS）。
2. 等首次编译完成。**Console 没有红色 Error 才继续**。
3. 菜单栏 → **`Tools ▸ 塔防 ▸ 一键补齐 M0 资源（安全：只补缺失）`**。
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
| `HudView 缺少子节点「GoldText」` | 执行「高级（单步重建）▸ 生成 UI 预制体」 |
| `场景中缺少对象「BattleRoot」` | 执行「高级（单步重建）▸ 重建 main 场景」 |
| `场景里没有任何对象带 Tag「UICanvas」` | 执行 `6. 配置工程设置`，再执行「高级（单步重建）▸ 重建 main 场景」 |
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

### 验收清单 · M0 基线（23 项，逐条勾）

**【启动与配置】**
- [ ] 1. Play 全程 Console 无 `Exception` / `NullReferenceException`
- [ ] 2. Console 打印 **9** 张表的记录数，与 Excel 行数一致（M2 起新增 `TBAudio`）
- [ ] 3. 棋盘行列数（16×9）、起终点位置与 `TBLevelMap` 配置一致

**【配置驱动验证（关键）】**
- [ ] 4. 打开 `Luban/Config/Datas/EnemyData.xlsx`，把 id=1 的 `hp` 从 `100` 改成 `50` → 保存 → 重跑 `gen_code_json.bat` → 回 Unity 等导入 → Play：怪物明显更快被打死

**【棋盘与建造】**
- [ ] 5. 点底部**塔按钮之一**（M2 起共 5 颗：普通/强力/减速/穿透/激光）→ 鼠标移动时有半透明的塔跟随，并显示**射程圈**
- [ ] 6. 移到可建造格 → 该格**变绿**；移到障碍格 → 该格**变红**
- [ ] 7. 点「普通」按钮后在绿格上左键 → 塔落位，金币从 100 减到 **80**（＝ `TBTowerInfo.id=1` 的 `prices`）
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

### 验收清单 · M2 新增项（20 项，逐条勾）

> 覆盖 M2 的 8 个目标（多塔型 / 升级出售 / 子弹特性 / 怪物扩展 / 飞行 / 音效 / 打击感 / 平衡）。
> 上面 23 项仍然要全过 —— M2 不应让 M0 的任何一条回退。

**【多塔型 5 类】**
- [ ] M1. 底部有 **5 颗塔按钮**（普通 / 强力 / 减速 / 穿透 / 激光），金币不足的那颗**自动置灰**
- [ ] M2. 5 种塔都能建出来；每种的伤害/射程/攻速与 `TowerInfo.xlsx` 对应行一致
- [ ] M3. 点不同按钮能**切换**塔型；已有塔的格子不能再建

**【子弹特性】**
- [ ] M4. **AOE（强力塔）**：一次开火能同时打到相邻的多只怪（子弹 `aoeRadius=1.2`）
- [ ] M5. **穿透（穿透塔）**：一发子弹能连续命中 ≥2 只怪（`pierce=3`）
- [ ] M6. **减速（减速塔）**：被命中的怪明显变慢，约 2 秒后恢复原速
- [ ] M7. **激光（激光塔）**：瞬发命中，**看不到弹体**，只有一条一闪而过的光束
- [ ] M8. 腐蚀弹（`effectType=2`）的持续伤害生效，且**能靠 DOT 打死怪**并正常给金币

**【升级与出售】**
- [ ] M9. **左键点已建塔** → 该格变**暖黄**、塔身提亮、显示**射程圈**，并弹出塔信息面板
- [ ] M10. 面板数值（攻击/射程/攻速/DPS）与所选塔的配置行一致
- [ ] M11. 点「升级」→ 数值变为下一级、金币按下一级 `prices` 扣除、**怪物不会因为升级而改道**
- [ ] M12. 点「出售」→ 按钮变「**确认出售？**」；**再点一次**才真正卖出，返还 = `sellPrice × sellRefundRate`
- [ ] M13. 「确认出售？」出现后等 3 秒不动 → 自动复位回「出售 (+N)」
- [ ] M14. `ESC` 分层：面板打开时关面板；放置中取消放置；否则取消选中

**【怪物扩展与飞行】**
- [ ] M15. 第 10 回合左右能看到 **Boss**（鼠王 / 虫后 / 苔藓女王），血量明显厚于普通怪
- [ ] M16. **飞行怪**（`isFlying=1` 的 5 种）**直线飞向终点**，不受塔墙阻挡
- [ ] M17. 飞行怪经过的格子上**仍然可以建塔**（它不该占住地面）

**【打击感】**
- [ ] M18. 命中时弹出**伤害数字**（致命一击是红色）；同一只怪的数字不会糊成一片
- [ ] M19. 受击有一次**闪白**；死亡时**淡出**；漏怪时**屏幕震动**（越疼的怪震得越明显）

**【音效（系统先行）】**
- [ ] M20. Console **没有** `[Audio]` 报错刷屏（当前工程 0 个音频文件，属预期的静默降级）。
  想让它发声：把 `.wav/.ogg` 丢进 `Assets/Audio/` → 跑 `python .workbuddy/tools/gen_audio_catalog.py` → **不用改任何代码**。

> M5 / M7 / M12 / M16 是最能证明"这轮真的接上线了"的四条，建议重点看。

### 验收清单 · M3 新增项（关卡与元进度）

**【关卡选择与解锁】**
- [ ] N1. Play 后**先出现关卡选择界面**（不是直接进第 1 关），能看到 8 个关卡按钮
- [ ] N2. 第 1 关可点；第 2~8 关初始显示「未解锁」，点了提示「先通关上一关才能解锁」
- [ ] N3. 每个按钮显示关卡名 / 星级（☆☆☆）/ 难度标签
- [ ] N4. 通关第 1 关后返回选关，**第 2 关变为可点**，且第 1 关显示获得的星级

**【8 关与难度曲线】**
- [ ] N5. 8 关的棋盘**各不相同**（障碍布局不同，可建造格从 142 递减到 70）
- [ ] N6. 每关的初始金币不同（100 → 2400），越后面的关给得越多
- [ ] N7. 第 4 关起每关最后一回合会遇到 **Boss**（鼠王 / 虫后 / 苔藓女王）

**【地图编辑器】**
- [ ] N8. `Tools ▸ 塔防 ▸ 地图编辑器` 打开后能载入当前关卡棋盘
- [ ] N9. 左键刷、右键擦；点「校验连通性」对故意堵死的地图报「S 到 E 不可达」
- [ ] N10. 点「一键写入 xlsx」后回 Unity，跑一次 Luban 导出，改动生效

**【暂停与设置】**
- [ ] N11. 对局中按 `P` 暂停（时间停住、弹出暂停面板）；再按 `P` 或点「继续」恢复
- [ ] N12. 暂停面板的「重新开始本关」能重开且**不会被卡在暂停**（时间已恢复）
- [ ] N13. 设置界面能调音量 / 静音；**关掉游戏再进，设置还在**（存档生效）
- [ ] N14. 「重置存档」后回到选关界面，8 关全部回到未解锁状态

**【存档与局内快照】**
- [ ] N15. 打到第 3 回合，用暂停面板「返回关卡选择」，再进同一关 → **从第 3 回合继续**，金币/生命/已建的塔都还在
- [ ] N16. 存档文件位于 `%USERPROFILE%\AppData\LocalLow\lzyfreedomtower\freedomtower\freetower_save.json`（Console 报错时会打印完整路径）
      ⚠️ 路径取自 Player Settings 的 `companyName` / `productName`；**存档文件名本身是 `freetower_*`（英文名，与中文游戏名无关）**，所以改中文名不会让老存档失效。

**【M4 表现】**
- [ ] N17. 相机可用中键拖拽 / WASD 平移，且**拖不出棋盘边界**；按空格回正
- [ ] N18. 塔开火时炮管有轻微后坐
- [ ] N19. 打开任意界面时有淡入（不是硬切）
- [ ] N20. 背景随相机移动得比棋盘慢（视差）

> N4 / N15 是最能证明"元进度真的通了"的两条；N1 是这轮最大的行为变化（开机先到选关）。



### 调试快捷键

| 按键 | 作用 |
|---|---|
| `F1` | 打印完整状态（流程 / 玩家 / 波次 / 战斗 / 空间哈希） |
| `F2` | 直接获胜（省去打完一整关的时间） |
| `F3` | **性能报告**（M5）：p50 / p95 / p99 / 最差帧 / 托管堆增量 / 战斗计数。**真机压测就靠它** |
| `P` | **暂停 / 继续**（M3）。不用 ESC 是因为 ESC 已被"取消放置 / 取消选中"占用 |
| `空格` | 相机回到自适应视野（同时把平移偏移归零） |
| `滚轮` | 缩放（自适应尺寸的 0.5× ~ 2.5×） |
| `中键拖拽` | 平移相机（M4） |
| `WASD / 方向键` | 平移相机（M4） |
| `鼠标贴屏幕边缘` | 边缘自动平移（M4）；放置或选中塔时自动禁用，避免拖塔时把镜头带走 |
| `右键` / `ESC`（未在放置时） | **取消选中 / 关闭塔面板**（M2 变更：出售不再走右键，改到塔面板里） |
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
<工程根>\
├── Luban\                              ★ 配置表工具链与源表（唯一配置来源）
│   ├── Config\Datas\*.xlsx               策划编辑的源表（9 张数据表 + 3 张定义表）
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
│   ├── Audio\                          ★ 音效文件放这里（M2；当前为空 → 静默无音效）
│   ├── Prefabs\
│   │   ├── Tower\Tower_Normal/Power/Retard.prefab   世界空间 SpriteRenderer
│   │   ├── Bullet\Bullet_Normal.prefab
│   │   ├── Enemy\Enemy_<怪名>.prefab   ★ 119 个战斗怪物（由「导入全部怪物」生成）
│   │   └── UI\HudView / TipsView / TowerInfoView / SelectView / PauseView / SettingView .prefab
│   ├── _UIAssets\                       美术资源（塔贴图 / 怪物包 / 背景）
│   └── Scripts\
│       ├── Core\Res\                   ★ AB 资源系统（ResTable 是唯一寻址源）
│       ├── Core\Combat\                ★ 去物理战斗系统（EnemyGrid + CombatSystem）
│       ├── Core\Manager\               管理器基类 + 玩家数据 + 音效 + **存档(SaveManager)** + 性能探针
│       ├── Data\                       配置读取层（Configs + 包装类 + 生成清单 + **SaveData**）
│       ├── Game\                       棋盘 / 关卡流程 / 路径渲染 / **背景视差**
│       ├── Round\WaveManager.cs        波次时间轴
│       ├── Enemy\  Tower\  Bullet\     战斗实体（含 RangeIndicatorView / LaserBeamView）
│       ├── UI\  Core\UI\               HUD / 提示 / 塔面板 / 伤害飘字 / **选关 / 暂停 / 设置 / 安全区 / 淡入**
│       ├── Camera\CameraController.cs  2D 正交相机（震动 + **平移/边缘拖拽/边界夹取**）
│       └── AStarWrapper\               A* 寻路（只建数据，不生成物件）
│
├── .workbuddy\tools\                   ★ 无 Unity 时的替代验证与生成脚本
│   ├── check_*.py                       5 个静态校验（括号/事件/成员/using/Unity API）
│   ├── gen_*_catalog.py                 怪物 / 音频清单生成
│   ├── gen_m3_levelmaps.py              ★ 8 张关卡棋盘生成（含 BFS 连通性自检）
│   ├── gen_m3_waves_rounds.py           ★ 40 波/40 回合战役编排（目标血量法）
│   ├── apply_m2_*.py                    M2 的配置表变更脚本（带自动备份）
│   ├── apply_levelmap_export.py         ★ 地图编辑器导出 → 回写 LevelMap.xlsx
│   ├── gen_m3_ui_prefabs.py             ★ 离线生成 M3 三个 UI prefab（克隆 Unity 模板）
│   └── balance_sim.py                   ★ 数值平衡顶演（只读，逐关）
│
└── Docs\
    ├── TowerDefense_Design_and_Implementation.md   ★ 设计与实施文档（v2.1 + §Z.7 M2 记录）
    ├── Tower_Interaction_Dev_Plan_v2.md            塔交互计划（M2 依据）
    ├── HudView_Sync_and_TowerUI_Plan.md            UI 命名契约
    ├── Progress_Sync_Report.md                     进度同步报告
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
| 塔面板 / 升级 / 出售 | `UI/TowerInfoView.cs`（只发事件）+ `Tower/BaseTower.cs` 里的 `TowerManager` |
| **选关 / 解锁 / 星级** | `UI/SelectView.cs`（展示）+ `Core/Manager/SaveManager.cs`（规则） |
| **暂停 / 设置** | `UI/PauseView.cs` / `UI/SettingView.cs`；暂停热键在 `GameFlowManager.Update` |
| **关卡切换 / 清场** | `GameFlowManager.TeardownLevel`（顺序：怪→弹→塔→界面） |
| **局内快照** | `GameFlowManager.SaveSnapshotNow` / `TryRestoreSnapshot` |
| **地图数据** | `Luban/Config/Datas/LevelMap.xlsx`；用菜单「地图编辑器」画，别手写字符串 |
| **性能度量** | `Core/Manager/PerfProbe.cs`（F3 打印报告） |
| 子弹行为（穿透/爆炸/减速/DOT） | `Bullet/BaseBullet.cs`；参数全在 `BulletData.xlsx` |
| 状态效果（减速/持续伤害） | `Enemy/BaseEnemy.cs` 的 `ApplySlow` / `ApplyDot` |
| 飞行单位 | `Enemy/BaseEnemy.cs` 的 `SetupFlyingPath` / `MoveStraight`；开关是 `EnemyData.isFlying` |
| 射程圈 | `Tower/RangeIndicatorView.cs`（贴图由占位生成器产出） |
| 伤害飘字 / 震动 | `UI/FloatingTextManager.cs` / `Camera/CameraController.cs`；参数在 `Global.xlsx` |
| 音效 | `Core/Manager/AudioManager.cs` + `Data/AudioName.cs`；参数在 `TBAudio` |

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
| `[Flow] boardView 未连线` | 场景是手工搭的、引用没连 | 菜单「高级（单步重建）▸ 重建 main 场景」 |
| 画面全黑 / 看不到棋盘 | 相机不是 `MainCamera` Tag，或 `Camera.main` 为空 | 选中 Camera → Inspector → Tag 设为 `MainCamera`；或重跑「高级（单步重建）▸ 重建 main 场景」 |
| 按钮点了没反应 | 场景没有 `EventSystem` | 重跑「高级（单步重建）▸ 重建 main 场景」 |
| Console 刷 `AnimationEvent 'SetHead' … has no receiver!` | 美术包的 Attack/Death 动画内置了 AnimationEvent，但包里没提供接收脚本 | 已补 `MonsterAnimEventReceiver`（挂在 Animator 所在节点，并预填 正常/愤怒/死亡 三个头部贴图）；重新执行「9. 导入全部怪物」即可消除。缺了它不影响移动与战斗，只是头部贴图不会随状态变化 |
| **怪物出现了但不会移动、只待在起点** | **管理器被实例化了两份**：`Launcher` 用 `new` 创建管理器，而其它代码走 `.Instance`（懒创建）→ 一份被 tick、另一份承载数据 | 已在代码里修好；`BaseManager<T>` 现在会在检测到直接 `new` 时立刻报 Error。若再出现，看 Console 有没有 `[Manager] 检测到直接 new` |
| **没有任何怪物出现** | ① 没点「开始」按钮 ② 或 HUD 根本没打开（见上一行） ③ 或 A* 路径不可达 | 先确认左上角有 `金币/生命` 文字；Console 应打印 `[Wave] 回合 1 开始：N 个波次 / M 只怪`；若打印 `[AStar] 起点到终点不可达` 就检查 `LevelMap.xlsx` |
| 点 HUD 按钮时顺手把塔放下去了 | `EventSystem` 缺失导致 `IsPointerOverGameObject()` 永远 false | 重跑「高级（单步重建）▸ 重建 main 场景」 |
| 塔和怪的前后遮挡不对 | `Transparency Sort Mode` 没设 | 菜单 `6. 配置工程设置` |
| 棋盘生成但**没有路径箭头** | `Path_Arrow` 贴图缺失 | 菜单 `1. 生成占位美术`（箭头缺失不影响玩法，只是看不到路径） |
| 怪物不动 | 起点 `S` 或终点 `E` 不在 `LevelMap.cells` 里 | 检查 `LevelMap.xlsx`；Console 会打印 `[AStar] 网格缺少起点(S)或终点(E)` |
| 怪物穿墙 / 卡在障碍里 | `cells` 每行字符数 ≠ `cols` | 检查 `LevelMap.xlsx`；Console 会打印 `[Board]` 或 `[Flow] 棋盘配置校验未通过` |
| `[AStar] 起点到终点不可达` | 障碍把地图完全阻断 | 用 `LevelMap.xlsx` 改回一条通路 |
| 塔一直不开火 | 目标在射程外 / 怪物已被打光 | 属正常表现；Console 每 5 秒打印一次战斗统计（`TBGlobal.showDebugLog = 1` 时） |
| `[Combat] 检测到 N 次「无目标开火」` | 逻辑 bug | 这是自检告警，正常应恒为 0。请把该日志连同场景一起反馈 |
| AB 模式启动报 `包文件不存在` | 没打包 AB，或打的是别的平台的包 | 先切好 Build Target，再执行 `8b. 打包 AssetBundle` |
| AB 模式下某些资源丢失 | ResTable 的 `Bundle`/`Asset` 与真实资源不一致 | 执行 `8a. 按 ResTable 打 AssetBundle 标记`，再看它有没有报 ✘ |
| **塔面板怎么点都不出来** | `Assets/Prefabs/UI/TowerInfoView.prefab` **不存在** | 菜单「高级（单步重建）▸ **补缺 UI 预制体（安全：只补缺失）**」。注意别用「生成 UI 预制体（全量重建）」——它会把手工调过的 HudView 一起覆盖 |
| **Console 报 `[HUD] 缺少按钮节点「Btn_Tower_xxx」`** | HudView.prefab 还是旧的 3 按钮版本 | 同上，先跑「补缺 UI 预制体」；若仍缺，用「生成 UI 预制体（全量重建）」重建 |
| 跑完一键向导后手工改的 HudView / 塔 prefab 被覆盖了 | 用了「全量重建」入口 | M2 起向导已改调 `EnsureMissing`（只补缺失）。重建类入口都在「高级（单步重建）」下，用前请先备份 |
| **升级之后塔不见了 / 格子空了** | 旧版本 `TryUpgrade` 会先拆旧塔再建新塔，新塔加载失败就什么都没了 | M2 已改为**先建后拆**：失败时退还金币且原塔保持不变。若仍复现请反馈 |
| Console 刷 `[Audio] 「sfx_xxx」找不到音频资源` | 工程内没有音频文件（预期） | 属静默降级，不影响玩法。要消除：把音频丢进 `Assets/Audio/` 并跑 `gen_audio_catalog.py`（见 `.workbuddy/tools/`） |
| **穿透塔打不到第二只怪** | 旧版本穿透逻辑失效 | M2 已修；若复现请反馈（命中判定改用空间哈希找"最近且未打过"的敌人） |
| 伤害数字不显示 | 配置表开关关了 | `Global.xlsx` 的 `showDamageText` 置 1（同时确认 `damageTextThrottleMs` 不过大） |
| 屏幕震动停不下来 / 相机偏了 | 震动期间调用了 `FitBoard` | 已在 `FitBoard` 与空格归位里清 `_shakeOffset`；若仍复现请反馈 |
| **飞行怪还是沿着地面路径走** | `EnemyData.isFlying` 为 0 | 该怪的行改成 1 → 重跑 Luban 导出。飞行单位走"起点→终点"直线，不参与 A* 与堵路判定 |
| **Play 后一直停在空白 / 没有选关界面** | `SelectView.prefab` 缺失或损坏 | 三个 M3 界面的 prefab **已随仓库提供**，正常不需要生成。若缺失/被改坏，跑「补缺 UI 预制体（安全：只补缺失）」重建；或用 `python .workbuddy/tools/gen_m3_ui_prefabs.py` 离线重建。**不会卡死**：代码有降级，选关打不开时直接进第 1 关，Console 会有 `[Flow] SelectView 打开失败…降级` |
| **按 P 没反应 / 暂停后回不来** | 暂停热键读的是 `GetKeyDown`，不受 `timeScale` 影响，正常一定能恢复 | 若真的回不来，看 Console 有没有 `[UI] UICanvas 下缺少子节点`。暂停面板挂在 NormalPanel 上，缺层就打不开 |
| **暂停后游戏一直卡住** | `Time.timeScale` 没被恢复 | `PauseView.OnDisable` 里无条件恢复；若仍复现请反馈。**注意**：不要在暂停状态下用 Console 手动改 timeScale 调试，会和面板状态打架 |
| **切关后出现"幽灵塔" / 空引用** | 上一关的塔/怪/弹没清干净 | 切关走 `GameFlowManager.TeardownLevel`（先清怪→弹→塔，再关界面）。若复现请反馈 |
| **进关卡后从一半继续，但我想从头打** | 局内快照生效了（这是特性） | 暂停面板点「重新开始本关」；或删掉 `freetower_save.json`（Console 报错时会打印完整路径） |
| **选关界面里第 2 关点不动** | 第 1 关还没通关（解锁规则：前一关至少通关一次） | 先通第 1 关。调试时可在 `GameFlow` 的 `startLevelId` 里直接填关卡号跳过解锁 |
| **地图编辑器改了但游戏里没变** | 忘了跑 Luban 导出 | 窗口「一键写入 xlsx」只写到 Excel。之后必须再跑 `3. 导出配置表（Luban）` |
| **地图编辑器「一键写入 xlsx」报找不到 python** | 本机 Python 不在 PATH | 手工执行 `python .workbuddy/tools/apply_levelmap_export.py`。该脚本自带备份与连通性复检 |

---

## 12. 已知遗留与后续阶段

### M0 刻意未做的（不阻塞验收）

| 项 | 说明 |
|---|---|
| ~~选关界面~~ | ✅ **M3 已完成**（`SelectView`，含解锁/星级/难度标签）。开机先进选关；调试可填 `GameFlowManager.startLevelId` 跳过 |
| ~~塔升级 / 出售 UI~~ | ✅ **M2 已完成**（`TowerInfoView` + 换实例升级 + 两段式出售确认） |
| ~~伤害飘字 / 击杀特效 / 音效~~ | ✅ **M2 已完成**（飘字/闪白/消散/震动；音效为"系统先行"，等音频文件） |
| ~~多塔型 / AOE / 减速~~ | ✅ **M2 已完成**（5 类齐备；穿透/激光外观待美术） |
| 结算界面 | 仍用 `TipsView` 文本代替（原计划 M3） |
| 切关时的 AB 整包释放 | `ReleaseBundle` 已实现，但只有一关，未接入流程 |
| 塔面板 / 穿透 / 激光的正式美术 | 目前：面板是纯色占位、穿透与激光复用普通塔外观。换皮 = 改 `resName` + `ResTable`，零代码 |
| 音频文件 | 工程内 0 个。丢进 `Assets/Audio/` + 跑生成器即生效 |
| 后期难度曲线 | 顶演显示第 6~8 回合余量 8~9 倍偏宽裕；整体经济调优属 M3 |
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
  Tools ▸ 塔防 ▸ 一键补齐 M0 资源（安全：只补缺失）
  → Tools ▸ 塔防 ▸ 0. 自检
  → Play

【首次跑起来】
  ① gen_code_json.bat
  ② Tools ▸ 塔防 ▸ 一键补齐 M0 资源（安全：只补缺失）
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

---

## 14. 回归用例清单（M5-3）

> 用途：**每次改完代码或配置表，按这份清单过一遍**。它比"逐条验收"短，但覆盖了所有"改一处会连带弄坏别处"的耦合点。
> 建议固定用同一关卡走完：**关卡 1**（棋盘最开阔、回合最短，5 个回合能跑完）。

### 14.1 冒烟（每次改动后必跑，约 5 分钟）

| # | 步骤 | 期望 |
|---|---|---|
| 1 | Play | 出现**选关界面**，Console 无 `Exception` / `NullReferenceException` |
| 2 | 点关卡 1 | 棋盘按配置生成，Console 打印 `[Flow] 关卡 1「…」就绪` 与 9 张表的记录数 |
| 3 | 按 `F3` | Console 打印 `[Perf]` 报告，且其中**「空放」必须为 0** |
| 4 | 建 1 座普通塔 | 金币按配置扣减；路径箭头实时改道 |
| 5 | 点「开始」，打完第 1 回合 | 顶部显示「回合 1 完成」，金币收到回合奖励 |
| 6 | 点已建的塔 | 弹出塔面板，数值与 `TowerInfo.xlsx` 一致 |
| 7 | 按 `P` 暂停再恢复 | 时间停住/恢复，游戏不卡死 |
| 8 | 暂停面板 →「返回关卡选择」 | 回到选关；再进关卡 1 → **从第 2 回合继续**，塔还在 |
| 9 | 暂停面板 →「重新开始本关」 | 回到第 1 回合，塔与金币重置为关卡初始值 |

### 14.2 耦合点专项（改到相关模块时跑）

| 改了什么 | 必须额外验证 |
|---|---|
| `TowerInfo.xlsx` / `BulletData.xlsx` | 5 种塔都能建出来；AOE 一次打多只；穿透连打 ≥2 只；减速怪变慢；激光无弹体 |
| `EnemyData.xlsx` | 改过的那只怪属性在游戏里生效；`isFlying=1` 的怪走直线且不挡建塔 |
| `LevelMap.xlsx` | 每张图 S→E 可达；`cells` 每行长度 = `cols`（否则 Console 报 `[Flow] 棋盘配置校验未通过`） |
| `EventName.cs` | 跑 `python .workbuddy/tools/check_events.py`（校验 Trigger/Add 的 arity 一致） |
| `ResTable.cs` | 跑菜单 `0. 自检`，② 资源地址表必须全 ✔ |
| `UIPrefabBuilder.cs` | 跑「生成 UI 预制体（全量重建）」后 Play：HUD 7 个直接子节点齐备、5 颗塔按钮都在 |
| `BaseTower.cs` | 建塔/升级/出售三条路径都试一遍；升级后塔仍在原格且能开火；**升级失败时塔不丢** |
| `SaveManager.cs` | 改设置 → 退出 → 重进，设置仍在；删存档后 8 关回到未解锁 |
| `CameraController.cs` | 缩放/平移/空格回正都正常；暂停时相机不动 |
| 新增 `.cs` 文件 | **手工往 `Assembly-CSharp.csproj` 补 `<Compile Include="…" />`**，否则 MSBuild 编译看不到它（Unity 刷新后会自动补） |

### 14.3 出包前（真机 / AB）

| # | 步骤 | 期望 |
|---|---|---|
| 1 | 菜单 `4. 按 ResTable 打 AssetBundle 标记` | 无 ✘ |
| 2 | 菜单 `5. 打包 AssetBundle` | 每个包都有产物；`tower_power` / `tower_retard` 不再缺失 |
| 3 | 加 `FORCE_AB` 宏跑一局 | 与编辑器直读表现一致；Console 无 `[Res] 包「xxx」尚未加载` |
| 4 | 撤掉 `FORCE_AB` | —— |
| 5 | 真机跑一关（尽量多怪）→ 按 `F3` | p95 ≤ 16.7ms；托管堆增量接近 0；空放为 0 |
| 6 | 真机按 `P` 暂停（后台切走再回来） | 不卡死、不丢进度 |

> 第 5 条就是设计文档 M5 的"低端机 200 怪 + 50 塔 60fps"验收 ——
> **它必须在真机上跑**，编辑器里的数字不作数（PC 与手机差一个数量级）。
