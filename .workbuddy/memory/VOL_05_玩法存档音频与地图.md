# VOL_05 玩法 / 生命周期 / 存档 / 音频 / 地图

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：关卡生命周期与拆卸入口、存档三项步骤、音频与倍速唯一源、塔型与攻击表现、建造交互 v3、地图链路、新增一关的四表要求、编辑器全解锁。

## 生命周期 / 存档 / 音频 / 玩法
- `LevelClearView` 胜败共用 `OnGameOver()`；唯一的拆卸入口是 `TeardownLevel()`。
- 存档只走 `SaveManager`（禁 SQL / PlayerPrefs）；改表三步：`CreateStatements` → `CurrentVersion + 1` → `RunMigrations`。
- 音频 = 丢文件 + `gen_audio_catalog.py`；BGM 2 源 + `AudioFadeDriver`；倍速唯一源 `Core/GameClock.cs`（`timeScale` 只取 0/1）。
- ★塔型：Normal1（打飞+走）/ Aoe2 火力仅打走 / Slow3 光环；Pierce4、Laser5 已删（编号不回收，别复用）；对空与否看塔表 `canAttackAir`。
- ★索敌对空优先（2026-10-21）：能打飞行单位的塔先选飞行怪，圈内无飞行才回落地面；层内仍按 `targetMode`。实现 = `BaseTower.PickBestTarget`（纯函数，两层打分）+ `TickAttack` 第③步「锁定地面时每索敌节拍复查并抢断」。**减速塔是光环，不参与该优先级**（用户 2026-10-21 明确：保持全覆盖，别加"有飞行就跳过地面"）。
- ★塔攻击表现：普通/火力塔不发子弹，开火 = 即时命中 + 序列帧。
  - `TowerFireFx`：枪口焰挂到炮管 `BarrelPoint` 子节点、local 置零；落点爆炸走对象池；帧由 `gen_tower_fire_frames.py` 生成。
  - ★散帧 meta 必须 `alignment: 9`(Custom) + `spritePivot y = 0.2`；写成 `alignment: 1` = TopLeft（底中应是 7）→ 焰会被甩到炮口右下角。
  - 时长权威 = `BaseTower.SlowDurationSec` / `DotDurationSec`（2026-10-31 随子弹系统删除从 `BaseBullet` 迁入）。
- ★建造交互 v3：点按 = 放置态；长按 0.25s 或位移 30px = 拖拽（ghost 跟手、松手校验、拖回按钮或拖出棋盘静默取消）。
- ★★建造交互 v4（2026-11-01，**第三条建造入口 + 圆盘即射程**，旧两路原样保留）：
  - 点**可建造空格**（非放置态）→ 弹建造圆盘（Kingdom Rush 式先选格子再选塔型）：事件 `BuildCellChosenEvent(row,col)`（`TowerPlacement.HandleSelectClick` 发，条件 = 空 + `IsBuildable` + `CellKeepsPathOpen`（只判定不画预览：`ComputePathWithExtraWall` 后立刻 ClearPreviewPath；A* 未就绪放行））→ `TowerBuildMenu`（HUD prefab 内，`TacticalForgePrefabBuilder.BuildTowerBuildMenu` 生成 Backdrop+三塔图标钮 BuildBtn_Normal/Power/Retard）。
  - 同格再点一次=收起；点图标=轻复查格子后 `TowerManager.TryBuild(type,1,row,col)`（成功收起、失败留盘换塔型）；买不起置灰价格变红；塔名/价格运行时按表填。
  - **塔动作菜单（TowerActionMenu）的暗色圆盘直径 = 选中塔的 `Config.RadiusWorld`**（UpdateRangeBackdrop：塔心与塔心+radius×相机右向量投 HUD 本地取距×2；减速塔即光环半径；取不到保持 388 默认）——用户定规"点已建塔时圆圈大小应与攻击/减速范围一致"。
  - 坑：退订 onClick 必须具名方法（匿名 delegate 匹配不上）；Backdrop 必须在 Configure **之前**建（Configure 按名抓引用序列化）；ApplyContentSurfaces 会重刷按钮皮肤、TowerBuildMenu 子树要排除；重建走专项菜单「更新 HUD 建造圆盘（2026-11-01）」避开全量重建三副作用。
- 地图链路：棋盘 → `levelmap_export.json` → `LevelMap.xlsx` → `tblevelmap.json` → `SceneInfo.xlsx`；日志前缀 `[Place]` / `[HUD]` / `[TowerInfoView]` / `[Audit]`。
- ★新增一关 = 四表齐全：LevelMap(id) + SceneInfo(mapId、RoundList) + RoundData + EnemyList。
- ★编辑器全解锁 = `SaveManager.UnlockAllLevelsInEditor`（真机仍逐关解锁）。
- ★★渲染层级契约（2026-10-21 改造，权威 = `Game/Board.cs` 的 `BoardSorting`）
  - 排序层只剩 4 个：`Default < Bg < Main < Pop`（TagManager 里删掉了 Top/Over；层优先级 > 层内 order）。
    Bg = 背景纸（序 0）；Main = 棋盘/路径/射程圈/塔/怪/子弹；Pop = 伤害飘字（序 0）。
  - Main 层内序：Cell 0 → PathArrow 10 → RangeIndicator 100 → **Tower 200 → Enemy 300** → Bullet 400。
  - ★★**永远怪压塔**（用户 2026-10-21 定案，不许塔盖怪）。塔根 SortingGroup = 200；怪根 SortingGroup = 300。
  - 塔组内：barbette 0 / Img_gun 1 / 枪口焰 2（都是**组内相对序**，`BaseTower.Init` 已删掉"<Tower 就抬到 Tower"的旧规则）。
  - 怪组内：血条 Bg 500 / Fill 501（同样是组内相对序，必须压过美术部件，实测最大 99：BugQueen/MossQueen；蝎子 40~70）。
  - ★血的教训：**SortingGroup 的子渲染器排序越不出组**，所以别再写"把血条设 500 就最上层"。
  - 资产落地/复查：菜单「高级（单步重建）▸ 标准化渲染层级（预置体+场景）」+「校验 ▸ 渲染层级体检（只读）」
    + 「0. 自检」第 ⑥ 步（AssetBundle 顺延 ⑦）：任何重建脚本把层级冲掉，自检直接报阻塞项，
    代码在 `Assets/Editor/SortingLayerNormalizer.cs`；怪物/塔生成器已内置同样规则，重跑不会回退。
  - 敌人美术源包（`_UIAssets/Monsters/**`）自带 SortingGroup 序不统一（0/1/2/3/4、100–104、201–204），
    所以 `MonsterPrefabBuilder` 克隆后必须 `NormalizeSortingGroup`，否则 31 个怪整组错位。
- ★★**存档口径：局内一律不落盘（2026-10-30 用户定规，最高优先级）**
  - 只有**通关**才写档：`SaveManager.RecordClear` → 星级 / 最快用时 / 最佳战斗用时 / 最佳剩余生命 / committedRunIds（`level_progress`）。
  - 塔阵 / 金币 / 生命**只存内存**：进关走 `PlayerDataManager.InitFromLevel`（初始金币、满血、0 塔、`_roundCursor=0`）；退出 / 失败 / 杀进程 = 本局作废，从第 1 波重打。
  - **不要**再恢复这些写法：`SaveSnapshotNow()`（开波前 / 每波结束 / 退出）、`SaveManager.SetSnapshot/TrySetSnapshot`、`CaptureFailedRunCheckpoint`（kv `checkpoint/failed-run`）。它们构成"反复重打同一波"的漏洞，已整体删除（`FailedRunCheckpoint.cs`、`LevelCheckpointValidator.cs` 一并删）。
  - 旧档清理：`SaveManager.PurgeLegacyRunState()` 在 `EnsureLoaded` 时"存在才清"（`LoadSnapshot().valid` 才写回空快照、kv 键存在才删），不给每次启动加写盘；表结构仍是 schema 4，`level_snapshot`/`snapshot_tower` 保留为遗留表。
  - 遗留件（无运行时调用点，仅单测/清理用）：`LevelSnapshot`/`TowerSnapshot` DTO、`ISaveStorage.LoadSnapshot/SaveSnapshot`、`BaseTower.CaptureCheckpointState/RestoreCheckpointState`。改表结构前先想清楚要不要连它们一起删。
  - UI 入口：主菜单 `ContinueBtn` 恒隐藏；`SelectView` 不再优先选"可续玩关"、格子无 `Continue`；`LevelDetailView` 按钮只判星级；`PauseView` 退出确认的兜底英文已改，但**词条 `Leave this battle?` 仍是旧说法**（配置表需人工改 + 重封）。
  - 验证工具：`BalanceCheckpointVerifier` 已改名 `BalanceSpeedComparison`（只做 ×1/×2/×3 一致性 + `finalTowerSignature`），`--kind checkpoints` 改名 `controls`；`checkpointScenario` / `checkpointWave` 参数现在无效。
  - 详见 `Docs/SavePolicy_2026-10-30.md`；`Docs/FailedRunResume_2026-10-29.md` 与 `Docs/LevelRating_Runtime_And_Save.md` 已加"被取代"横幅，里面的快照段落属历史。
- ★★**2026-10-31 增补：局内进度落盘 = 续玩快照恢复（实质推翻上一条）**
  - 口径（用户四轮收敛，以最后一轮为准）：**每通过一波**把 塔阵 + 金币 + 生命 + **波次游标** +
    **整份 `LevelRunMetrics`** 存一份（`FinishRound`）；整关通关再写一次，但那次是**重玩起点**
    （游标 0、不带统计）；重进该关**接着上一波继续**（资源覆盖、塔阵免费还原、评级统计继续累加）。
    （演进：只有通关才存 → 实测"打一波→退→再进"丢数据 → 每波通过都存 → 加金币/生命 →
    再加"存波次游标"，用户选"第二条"= 连进度一起存。）
  - ★**等于恢复了 10-30 废止的续玩快照**：行为上又能"从第 N 波继续 / 失败后重打当波"。
    差别只在形态：存 kv 单键 `layout/campaign`（密文），旧 `level_snapshot`/`snapshot_tower` **仍不写**，
    schema 仍 4。
  - ★**必须存整份 `LevelRunMetrics`**（不只是游标）：评级要核 `completedWaveCount`/`successfulSpawned`
    /每波明细/计时，缺了会被判 `Incomplete waves`、`Spawn count mismatch` → 星级不落库 → 下一关锁死。
    `_run.waves` 是 `Add` 追加，续玩后明细自然连续；`runId` 保留原值，结算不会算成两次通关。
  - ★**通关那一笔要写游标 0 + 无统计**，否则下次进关 `_roundCursor >= 波数` 会立刻又判一次通关。
  - ★**接管前四项校验**（`RestoreSavedLevelState`）：评级版本一致 / runId 未入档 / 0 < 游标 < 波数 /
    记录带统计；任一不满足 → 只还原塔与资源、从第 1 波开始（改过数值表时必须丢弃进度，否则两套数值
    混进同一份评级证据）。
  - 老记录兼容：`resourcesSaved`（缺省 0 会"0 血 0 金开局"）与 `runSaved`（游标 0 是合法值，不能当哨兵）
    两个开关必须保留。
  - 存哪：`Assets/Scripts/Data/LevelLayout.cs` 的 `LevelLayoutStore`；写点 `FinishRound` +
    `CompleteVictory`/`RetryPendingClearSave`；读点 `InitLevel` 第 ⑨.5 步（回合队列之后、HUD 刷新之前）。
  - ★**经济防线（改这块前必读）**：免费还原＋原价卖塔＝刷金币。`BaseTower.InvestedGold` 记账（还原=0），
    `TowerManager.RefundOf` = `min(配置售价, 实际投入) × SellRefundRate`；正常塔结果与旧实现完全一致，
    还原塔返还 0，还原后升级只返还升级费。公式只准存在 `RefundOf` 一处，UI 三处 + `Sell` 都必须调它。
  - 已知代价：失败后能无限重打当前波；`GameClock` 计时跨会话累加（"最快用时"含上次会话时间，
    想让时间榜只统计一口气打完的局，需要在续局时把 `timingValid` 置 false）。
  - 验证：`dotnet build` 四工程 0 error；**编辑器内未验证**（当时 WorkBuddy 的 unityMCP 未加载）。
    文档：`Docs/LevelLayoutPersistence_2026-10-31.md`。
- ★★放置规则 v4（2026-10-22 用户需求：路径预览 + 放置判定，权威代码 `Tower/TowerPlacement.cs`、`AStarWrapper/AStarManager.cs`、`Game/PathArrowView.cs`）
  - ① **预览只画不改**：悬停格变化 → `AStarManager.ComputePathWithExtraWall(row,col)` 临时置墙跑一次 A* →
    结果存 `PreviewPathWorld`，经 `EventName.PreviewPathEvent` 交给 `PathArrowView.RenderPreview`，
    画成**红色箭头（PreviewColor = RGBA(1,0.23,0.23,0.9)，order = PathArrow+1 = 11）**，与白色真实路径（0.75 alpha）分两套对象池。
    （2026-10-22 12:33 用户要求预览线路改红色；初版为青色 RGBA(0.55,0.95,1,0.85)，仅颜色不同。）
    贴图 `Assets/Art/Generated/Path_Arrow.png` 本身必须是**纯白**（生成为 `PlaceholderArtGenerator.PathArrowColor = Color.white`）：
    SpriteRenderer.color 与贴图色是**相乘**，青图会把红色压成暗红；白图才能让白色真实路径与红色预览都还原成设定值。
  - 关键约束：`ComputePathWithExtraWall` 用 try/finally 还原 IsWall，**不写 CurrentPathWorld / 不动 _lastPathHash /
    不置 _refreshRequested / 不发 RefreshPathEvent** → 玩家滑动期间怪物一步都不改道。
    落地（`TowerManager.TryBuildInternal`）才置墙 + `RequestRefresh()` → `RefreshPathEvent` → `CombatSystem.OnRefreshPath` 让怪改道。
  - ② **预览 == 实际**：落地做的是同一件事（该格 IsWall 置真后跑同一 A*、同一 StartPoint→TargetPoint），
    唯一差别是"算完是否还原墙"。实测（编辑器内存网格 6×5 双走廊）：preview 走上方绕行 10 格，落地后 CurrentPathWorld 与之逐点相同。
  - ③ 预览与真实路径**逐格相同则不画**（`PathArrowView.SamePath`，误差 1e-4）——否则两条箭头重叠成"重影"；
    此时看到白色真实路径即表示"这格建上去路线不变"。
  - ④ 清理：`ClearPreviewPath()` 挂在 `TowerPlacement.ClearHover()`，所以"悬停格消失 / 滑出棋盘 / 退出放置 / 落子成功"都会清掉。
  - ⑤ **怪物脚下可以建塔**（原 `CombatSystem.HasAliveEnemyNear` 已删除）：放置只剩 格子可建 → 无塔 → 金币够 → 不堵死路径。
    建好后 `CombatSystem.RerouteEnemiesThrough(row,col)`（v5 修订：原 `RerouteEnemiesNear(center, cellSize*0.5)` 已替换）
    把"正站在该格 / 剩余路径会经过该格"的地面怪逐个 `RefreshPath()`。两个原因：
    · 半格半径是几何漏洞 —— 格子是边长为 CellSize 的方块，格心到四角 0.707×CellSize，站在角上的怪会被漏掉；
    · 按格 + `BaseEnemy.RemainingPathTouches(row,col)` 才能覆盖"下一格就踏进新塔"的怪（旧实现完全管不到）。
    不能只靠 RefreshPathEvent：它按"起点→终点路径哈希"判重，主路径没变就不广播 → 脚下那只怪会穿塔而过。
    A* 的起点不受 IsWall 限制（`AStarWrapper.FindPath` 直接 openList.Add(start)），所以"从墙里迈第一步"是合法的（实测 4 格逃出）；
    但 `RefreshPath` 现在会丢掉 `newPath[0]`（== 自己站的墙格），否则怪会先走回塔心再出来 = 视觉穿塔。
  - ⑥ 连带清理：`FallbackBlockReason` 删掉 `"An enemy is on this tile, try another spot"` 分支；
    `tblocalization.json` 里那一行仍保留（导出产物，不影响）。
  - ⑦ 验收：编译 0 error；EditMode **67/67** 通过（新增 `Assets/Tests/BalanceCombat/PlacementPathPreviewTests.cs` 4 条：
    预览不改 CurrentPathWorld / 不发 RefreshPathEvent / 临时墙还原；预览逐点 == 落地路径且确实改道；
    堵死格返回 null 且回滚；RemainingPathTouches 只报未走过的格）。
    `PathArrowView` 预览层探针 = 9 个箭头、颜色 RGBA(0.55,0.95,1,0.85)、order 11、清预览后真实 9 个仍在。

## 真实子弹系统已整体删除（2026-10-31）

- **删除范围**：`Assets/Scripts/Bullet/BaseBullet.cs`（含 `BaseBullet`/`BulletManager`/`BulletState`）、
  `CombatSystem` 的 `_bullets`/`RegisterBullet`/`UnregisterBullet`/`TickBullets`/`CopyBullets`/`BulletCount`、
  `Launcher` 的 `BulletManager` 注册、`GameFlowManager`/`GameSceneLauncher` 的 `bulletRoot`、
  `Bullet_Normal.prefab`、`Bullet_Dot.png`、`ResTable` 两条登记、`ResBundle.BulletNormal` 与 `bullet_normal` 包、
  `Main.unity` 的 `BulletRoot` 空节点、`OutputCache` 里的旧 bundle 缓存。
- **为什么删**：自 2026-10-17「移除真实子弹、改即时命中」起 `BulletManager.Fire` **零调用点**，
  但 `BaseBullet.Explode` 仍无对空过滤、也不乘 `airDamageScale`，与在跑的 `DetonateAt` 规则冲突；
  留着就是“哪天有人接回子弹，火力塔会静默溅射飞机”的雷。
- **保留**：`tbbulletdata` 表、`TowerInfo.bulletId`、`BulletConfig`、`Configs.GetBullet` —— 火力塔的
  AOE 半径 / 命中效果 / 效果值仍从这张表取；`BoardSorting.Bullet=400` 仍给枪口焰/爆炸用；
  `Global.bulletPoolSize` 已成空配置（改表需手工，未动）。
- **改名**：`TowerConfig.FiresBullet` → `CanFire`（真实语义只剩“这塔会不会开火”）。
- **命中双计**（同日修）：删掉 `BaseTower.HurtEnemy` 里的 `AddHitCount(1)`，只在 `BaseEnemy.Hurt` 记一次；
  `StatHitCount` 原先恒为真实值两倍，只影响 `PerfProbe`/`[Combat]` 日志。
- **验证**：编译 0 error；`FTProject.BalanceCombat.EditModeTests` 29/29 通过；`Main.unity` diff 仅 34 行删除。
- 记录：`Docs/BulletSystemRemoval_2026-10-31.md`。**未跑 Play Mode**；AB 包清单变化，热更需按铁律重打。

## 出售返还改成"还原塔带投入入库"（2026-11-01，用户选方案 2）

**起因**：用户问"为什么现在出售防御塔没有返还了"。定位结论——不是 bug，是 `ed4fa097d`（2026-10-31 09:19
「每波落盘 + 续局还原」）把 `refund = round(cfg.SellPrice × rate)` 改成了
`min(cfg.SellPrice, InvestedGold) × rate`，而免费还原路径 `SetInvestedGold(0)`，于是还原塔卖出恒为 0。
配置侧已排除：`tbtowerinfo` 270 行 `sellPrice` 全 >0（普通 22/42/70、火力 30/58/97、减速 21/49/91），
30 关 `tblevelrules.sellRefundRate` 全 = 1。

**用户选择**：把 `InvestedGold` 随阵型一起存盘，卖还原塔也按投入返还（方案 2），不接受"还原塔卖 0"。

**改动（4 处代码契约 + 3 处注释口径）**：
- `LevelLayout.TowerLayoutEntry.investedGold`（新增 int）+ `hasInvested`（新增 bool）——
  "这座塔累计花了多少钱"与"这条记录到底存没存过这笔钱"。
  `SaveCurrentLevel` 采集 `tower.InvestedGold` 并置 `hasInvested = true`；
  `RestoreTowers` 按 `hasInvested ? Mathf.Max(0, entry.investedGold) : FallbackInvested(type, level)` 传值。
  **老档兜底**：`hasInvested=false` 时取 `Configs.GetTowerByTypeAndLevel(type,level).SellPrice`
  ——`min(售价, 售价) × 比例` 与正常塔返还额完全一致，老玩家不会少拿也不会多发；
  配置缺失返回 0（宁可少给，不可凭空造钱）。
  **为什么不用 `investedGold == 0` 当哨兵**：把"0 投入"和"不知道投入"压在一个数值上，
  将来出现合法 0（赠送塔/活动塔）时兜底会算错；显式开关与 `resourcesSaved`/`runSaved` 策略一致。
- `TowerManager.RestoreTower(type, level, row, col, investedGold)` →
  `TryBuildInternal(..., bool charge, bool quiet, int investedGold = 0)`；
  记账行改为 `SetInvestedGold(charge ? cfg.Prices : Mathf.Max(0, investedGold))`。
  `TryBuild`/`TryUpgrade` 的记账语义没变（升级仍是 `old.InvestedGold + nextCfg.Prices`）。
- `EventName.TowerSoldEvent`（新事件，参数 BaseTower）；`BaseTower.Sell` 在 `ReleaseInstance`
  **之前**触发（监听方要读塔字段，之后就是假 null）。
- `GameFlowManager.OnTowerSold` → 立即 `SaveCurrentLevel(Level.Id, _roundCursor, snapshot, null)`。
  三条守卫：① `State` 只允许 Preparing/RoundRunning/RoundComplete（结算后写会把"重玩起点"改成"续局"，
  下次进关立刻再判通关）；② `_roundCursor <= 0` 时 `snapshot = null`（没可续的进度，写 runSaved 只会被
  判"游标越界"刷警告）；③ RoundRunning 时把 `_run.waves` 末尾"未结算的那波"裁掉再存
  （否则续局 `StartRound` 会再 push 一条同序号记录，`completedWaveCount` 与 waves.Count 对不上）。
  `snapshot.Clone()` 是 JSON 深拷贝，改副本不污染本局统计。
- UI 注释同步：`SellConfirmView` / `TowerActionMenu` / `TowerInfoView` 里"还原塔投入 0 → 显示 +0/0%"
  的说法已不成立，改成"按阵型记录里的累计投入算"。

**★ FormatVersion 故意保持 1**：`investedGold` / `hasInvested` 都是增量字段，老档读成 `0 / false`，
配合开关可以精确走"按配置售价兜底"，语义没有歧义。升到 2 会让 `LoadBook` 把老玩家阵型整本作废。
判断标准：只有"老档字段值会被新代码误读成另一个意思"时才必须升版本。

**防刷金币论证（为什么这样不开口子）**：
1. 返还额 = `min(售价, 投入) × 比例`，永远 ≤ 投入 → 卖塔本身不可能增殖；
2. 还原塔的投入来自它自己的记录，卖它等于"退出前卖它"，不是白送钱；
3. 关键是"卖塔立刻落盘"：塔从记录里消失 + 金币进记录，成对持久化；不写这一笔，
   "卖完 → 退出 → 重进"会让塔带着投入额复活，同一座塔可反复卖 —— 那才是真漏洞。
4. 若卖完立刻崩溃/杀进程：金币和塔一起回滚，等于没卖，无收益。

**验证**：`refresh_unity(force/all/compile)` 后 `isCompiling=False`、`scriptCompilationFailed=False`、
`read_console(filter="error CS")` 0 条。`execute_code` 验 JSON 往返：新记录序列化为
`{"row":1,"col":2,"type":1,"level":1,"investedGold":32,"hasInvested":true}`，读回 `32/True`；
老记录 `{"row","col","type","level"}` 读出 `0/False`（走兜底）。数值口径已用 `tbtowerinfo` 静态核对：
type1 Lv1 `prices=32`、`sellPrice=22` → 新塔返还 `min(22,32)=22`，老档兜底 `min(22,22)=22`，两者相等。
**未跑 Play Mode 实测**（没做"建塔→过一波→退出→重进→卖塔看金币"的完整链路）。
Console 里残留的 3 条错误与本改动无关：`Unity Remote requirements check failed`（Android Remote）、
`EventController.cs:112/140` 的 `RemoveEventListener<T,U>` 类型不匹配（既有双参数退订 bug，本次只用了单参数事件）。
