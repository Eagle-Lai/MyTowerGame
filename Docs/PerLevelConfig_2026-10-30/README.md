# 关卡配置「每关一组」改造 —— 进度与记录（2026-10-30）

> 影响面清单见 `Docs/PerLevelConfig_Impact_2026-10-30.md`。本文记录已落地的部分。

## 已确认的三项口径（用户 2026-10-30 拍板）

1. **物理下沉**：每关一个文件，不做"一张表加 levelId 列"。
2. **Global 只保留 7 个引擎常量**（池大小/帧率/死亡回收/离线检查/日志开关），其余 15 个下沉。
3. **工具链一起改**（`.workbuddy/tools` 与 `Assets/Editor/Balance/*`）。

## P0（数据骨架）—— 已完成

- 新增 30 套 `Levels/Lxx/TowerInfo.xlsx`（各 9 行）与 `Levels/Lxx/BulletData.xlsx`（各 6 行），
  末列新增 `levelId`（int）显式标明归属。
- ID 规则：
  - 塔 `id = levelId*1000 + 原 id`（L01 → 1001..1009，L30 → 30001..30009）；
  - 子弹 `id = levelId*100 + 原 id`（L01 → 101/102/104..107）；
  - `upgradeTo`、`bulletId` 同步重写成本关内 id，**跨关不会串**。
- `__tables__.xlsx`：`TBTowerInfo` / `TBBulletData` 的 input 从 1 个文件改为 30 个关卡文件。
  根目录旧的 `Datas/TowerInfo.xlsx`、`Datas/BulletData.xlsx` **保留但已不参与导出**（留作参照）。
- 导出结果：`tbtowerinfo.json` 270 行、`tbbulletdata.json` 180 行，`airDamageScale`（3 级普通塔 1.1）等现值全部保留。

## P1（代码作用域）—— 已完成

| 文件 | 改动 |
|---|---|
| `Assets/Scripts/Data/Configs.cs` | 新增 `ActiveLevelId` + `SetActiveLevel`；按关卡建 `TowerIndexByLevel`（key = type*10+level）与 `BulletIndexByLevel`（key = 原 id）；`GetTower*` / `GetBullet` 全部改为**当前关卡作用域**查询；`<1000` / `<100` 的旧式局部 id 自动补关前缀（兼容老工具） |
| `Assets/Scripts/Game/GameFlowManager.cs` | `InitLevel` 开头调用 `Configs.SetActiveLevel(levelId)`，保证 HUD 建塔按钮与后续建造都取本关数据 |
| `Assets/Scripts/UI/TowerCodexItem.cs` | 塔图鉴只列 `LevelId == ActiveLevelId` 的 9 行（否则会显示 30 关的 270 行） |
| `Assets/Tests/BalanceCombat/CombatTargetingAndSlowTests.cs` | 手工构造 `cfg.TowerInfo` / `cfg.BulletData` 补 `levelId` 参数 |

## 验证

| 项 | 结果 |
|---|---|
| Luban 导出 | 成功；`tbtowerinfo` 270 行 / `tbbulletdata` 180 行 |
| 编译 | `scriptCompilationFailed=false`，无 `error CS` |
| runtimeContentHash | **354be2b5cea754dd1b3995beedda6c0243d3f3269c861ae50f193923ef78ed0b**（30 关重封） |
| Play Mode | `[Rating] Runtime configuration SHA256 verified: 354be2b5…`，0 error |
| 运行时读数 | `L01 normal-L3: id=1003 power=13 air=1.1｜1001.upgradeTo=1002｜L01 bullet=101｜L02 normal-L3 id=2003｜L02 bullet=201` |
| 进关切换 | `StartLevel(1)` → `active=1`；`StartLevel(2)` → `active=2`、`normalL1.id=2001`、`upgradeTo=2002` |

## 尚未做的（按阶段）

| 阶段 | 内容 | 状态 |
|---|---|---|
| P2 | 图鉴/预览等"全表枚举"场景按关过滤（塔图鉴已改，怪物图鉴仍是全表） | 部分 |
| P3 | `Global` 拆分为「引擎常量（留全局）+ 每关 `LevelRules.xlsx`」 | 未开始 |
| P4 | 运行时哈希改**按关卡**重封（改 L01 不再需要 30 关全封） | 未开始 |
| P5 | 怪物基表 132 行 canonical 拆分到各关 | 未开始 |
| P6 | 工具链（`.workbuddy/tools` 12+ 脚本）与 `Assets/Editor/Balance/*` 验证器对齐 | 未开始 |

## 回滚

1. 恢复 `__tables__.xlsx`（`TBTowerInfo`/`TBBulletData` 的 input 改回单文件）；
2. 删除 `Levels/Lxx/TowerInfo.xlsx`、`Levels/Lxx/BulletData.xlsx`（30×2）；
3. 还原 `Configs.cs` / `GameFlowManager.cs` / `TowerCodexItem.cs` / 测试文件；
4. 重新导出 + 重封哈希。

备份：本次会话 `%TEMP%/perlevel_p0_backup/`（`__tables__.xlsx`、`TowerInfo.xlsx`、`BulletData.xlsx` 原件）。

---

## P3（Global 拆分）—— 已完成

### 数据

- 新增 **30 份** `Levels/Lxx/LevelRules.xlsx`（每份 1 行、14 个玩法/表现常量）：
  `cellSize / boardOriginPadding / defaultReward / defaultDamageToPlayer / defaultBodyRadius /
   defaultSearchIntervalMs / autoNextRoundDelayMs / autoStartRoundDelayMs / sellRefundRate /
   artFaceLeft / showDamageText / damageTextThrottleMs / shakeAmplitude / shakeDurationMs`
- `Global.xlsx` 裁剪为 **id + 7 个引擎常量**（`enemyPoolSize / bulletPoolSize / maxEnemyAlive /
  targetFrameRate / deathRecycleDelayMs / checkOfflinePerFrame / showDebugLog`）。
- `__tables__.xlsx` 新增 `TBLevelRules`（30 文件）。导出后 `tblevelrules.json` 30 行。

### 代码

| 文件 | 改动 |
|---|---|
| `GlobalConfig.cs` | 改为**门面**：构造入参 `(Global 引擎行, LevelRules 本关规则行)`；属性名全部保持不变（`Configs.Global.CellSize` 等 19 处调用点**一行没改**），只是数据来源换成本关规则；规则行缺失时退回内置默认值 |
| `Configs.cs` | 新增 `RulesTable` / `RulesByLevel` / `_globalRow`；`SetActiveLevel` 里重建 `Global`；`ConfigKeys` 与 `CalculateRuntimeContentHash` 的 keys 都加入 `tblevelrules` |
| `Configs.EditorCandidates.cs` | 候选表加载器同步加载 `tblevelrules`、重建索引与 Global，失败时还原 |
| `ResTable.cs` | 登记 `tblevelrules` 资源地址（**漏了会直接导致整张表加载失败、哈希校验不过**） |
| `LubanExporter.cs` / `M0SetupWizard.cs` | 产物自检表名清单加入 `tblevelrules` |
| `TacticalForgePreview.cs` | 两处读 `tbglobal.json` 的 `sellRefundRate` 改读 `tblevelrules.json`（字段已迁移） |

### 新增工具

`tools/reseal_hash.py` —— **唯一权威的重封实现**。此前工程里散着 5 份复制粘贴的 `compute_hash`
（flatdrop / w20-soften / wavegold-air / ground-plus5 / econ-neutral），这次哈希口径加了
`tblevelrules`，那 5 份已经过期，**再用会算出错误哈希**。以后统一用这个脚本（`print` / `write`）。

### 验证

| 项 | 结果 |
|---|---|
| 导出 | `tbglobal` 8 字段、`tblevelrules` 30 行 15 字段 |
| 编译 | `scriptCompilationFailed=false`，0 error |
| runtimeContentHash | **691f6cd0927b4df0ba3549c4276c981e8f6f8b03424bb9c317b1670ac22fca0a** |
| Play Mode | `[Rating] Runtime configuration SHA256 verified: 691f6cd0…`，0 error |
| 运行时读数 | `loaded=True L1 rulesId=1 cell=1 refund=1 next=2500ms pool=256 maxAlive=200`；切到 L7 → `rulesId=7` |
| 进关冒烟 | `state=Preparing level=1 active=1 board=13x7 towerCfg.id=1001 cell=1`，0 error |

### 踩坑记录

`ResTable.cs` 是"逻辑名 → 资源路径"的第二道登记。新增任何配置表，**只改 Luban 的 `__tables__.xlsx`
不够**：`Configs.ConfigKeys`、`ResTable`、`LubanExporter`/`M0SetupWizard` 的自检清单三处都要登记，
否则表现为「预加载发现未登记的逻辑名 → 该表读取失败 → 哈希校验失败 → IsLoaded=false」。

---

## P5（怪物表按关归属）—— 已完成

- 先做了实测：**基表 132 行 canonical（id 1..132）没有任何波次引用**（最小被引用 id = 3140136），
  纯属历史残留。
- 30 份 `Levels/Lxx/EnemyData.xlsx` 末尾加 `levelId`（int）；`__tables__.xlsx` 的 `TBEnemyData`
  input 改为 30 个关卡文件，基表不再参与导出。
- 导出后 `tbenemydata.json` **12,594 → 12,462 行**，每行都带 `levelId`（L01=1 … L30=30）。
- `Configs.ValidateCrossReferences` 增加**跨关引用检查**：某关的波次引用了别的关的怪物 id 直接报错，
  防止"改一关动全身"重新长出来。
- 手工构造 `cfg.EnemyData(...)` 的 3 个编辑器工具 + 1 个测试补 `levelId` 参数（加列会改生成类构造签名）。

### 踩坑：表定义只认"第一个输入文件"的表头

基表被摘掉后，**`Levels/L01/EnemyData.xlsx` 成了第一个输入文件**，而它的 `reward` 表头还写着 `int`，
于是导出直接报 `0.1903 不是正确格式`。把 30 份关卡表的 `reward` 表头统一改成 `float` 后通过。
→ 规律：`define_from_file=True` 的多人文件表，**schema 由 input 列表第一个文件决定**；换顺序 = 换 schema。

## P6（工具链对齐）—— 已完成

| 工具 | 改动 |
|---|---|
| `.workbuddy/tools/balance_pipeline.py` | `assert_tower_radius_type` 改为逐个校验 30 份关卡塔表（并断言 30 份齐备） |
| `.workbuddy/tools/balance_finalize_reports.mjs` | 输入指纹从"1 份 TowerInfo"改为 30 份 TowerInfo + 30 份 LevelRules |
| `Docs/.../l01_design.py` | 塔/子弹/规则改读 `Levels/L01/` 下的表 |
| `Docs/.../l01_verify.py` | 同上 |

验证：`assert_tower_radius_type()` 对 30 份全部通过；`l01_design.py` dry-run 正常输出 25 波设计表；
`py_compile` 与 `node --check` 通过。

**未动**：`append_tower_rows.py` / `apply_m2_*.py` / `add_monster_names_20261016.py` 等一次性迁移脚本
（历史产物，不再运行；它们指向的旧表已归档到 `Datas/_legacy/`，真跑会立刻 FileNotFound，不会静默读旧数据）。

## 公共表归档

`Luban/Config/Datas/` 根目录现在只剩：

```
Global.xlsx         （id + 7 个引擎常量）
Localization.xlsx   （多语言，跨关共用）
__tables__.xlsx / __beans__.xlsx / __enums__.xlsx
Levels/L01..L30/    （每关 9 张：SceneInfo / LevelMap / RoundData / EnemyList / EnemyData / LevelRating / TowerInfo / BulletData / LevelRules）
_legacy/            （TowerInfo.legacy / BulletData.legacy / EnemyData.legacy，已不参与导出）
```

## P4（按关卡重封哈希）—— 评估后暂缓

理由：P4 不消灭任何公共表（结构目标已由 P0/P1/P3/P5 达成），而它要求 **C# 与 Python 对同一份
per-level 摘要逐字节一致**（浮点格式化、字段顺序、文化区域都可能是坑；SimpleJSON 的 `ToString()`
在 Android 上还有 decimal separator 风险）。一旦两边漂移，表现是"改完表 Play Mode 直接说哈希不符"。
目前重封已经是 `reseal_hash.py write` 一条命令、1 秒完成，收益不足抵这个风险。

若仍要做，建议的干净做法：把重封搬到**编辑器 C# 菜单**（计算与写入同一语言），Python 只读校验。

---

## MCP 实机验证（2026-10-30 10:12，Unity 2022.3.62f3c1 / Play Mode）

| # | 验证项 | 结果 |
|---|---|---|
| 1 | 启动配置校验 | `[Rating] Runtime configuration SHA256 verified: 4771650a…`，控制台 0 error |
| 2 | 建塔 / 升级 / 出售（真实 API `TryBuild/TryUpgrade/Sell`） | `build.id=1001` 金币 100→68（价 32）；`upgrade.id=1002` →40（价 28）；出售返还 42 →82（`sellPrice 42 × LevelRules.SellRefundRate 1.0`） |
| 3 | 连续 3 波实战 | W1 31 杀 0 漏 → 自动接 W2/W3（说明 `LevelRules.autoNextRoundDelayMs=2500` 生效）；`killed=68 gold=216 towers=2`，0 error |
| 4 | 失败续局 | `LoseHp(99)` → GameOver，写入 `关卡1｜死于第1波｜金币24｜生命10/10｜塔2座`；退出重进后仍在；`ClearSnapshot`（模拟改表）后 `可续玩=True L1 W1`；恢复出 `[0,0 id=1001][0,2 id=1004] gold=24 hp=10/10 statsValid=False debug=True` |
| 5 | 关卡隔离 | L02：`tower.id=2001`、本关塔行数=9、画布 16×9；与 L01 数据互不串 |
| 6 | 画面 | 截图为 L01 棋盘 13×7，两座塔正常渲染、鸡群沿路径行进，无错位/黑屏 |

**设计行为提醒**：从 L1 失败后**切到别的关**会丢弃 L1 的续局点（`StartLevel` 里显式清理，避免进关被上一关残局劫持）；再回 L1 是全新局。若要改成"保留到该关再次进入为止"，改一行即可。

**未做视觉验证**：塔图鉴 / 怪物图鉴的 UI 只验了数据侧（按 `ActiveLevelId` 过滤后本关 9 行），没打开界面逐项核对。
