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
  - 时长权威 = `BaseBullet.SlowDurationSec` / `DotDurationSec`。
- ★建造交互 v3：点按 = 放置态；长按 0.25s 或位移 30px = 拖拽（ghost 跟手、松手校验、拖回按钮或拖出棋盘静默取消）。
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
