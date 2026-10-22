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
- ★新增一关 = 四表齐全：LevelMap(id) + SceneInfo(mapId、RoundList) + RoundData + EnemyList。现役 20 关 × 20 波。
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
