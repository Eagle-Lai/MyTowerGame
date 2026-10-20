# VOL_05 玩法 / 生命周期 / 存档 / 音频 / 地图

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：关卡生命周期与拆卸入口、存档三项步骤、音频与倍速唯一源、塔型与攻击表现、建造交互 v3、地图链路、新增一关的四表要求、编辑器全解锁。

## 生命周期 / 存档 / 音频 / 玩法
- `LevelClearView` 胜败共用 `OnGameOver()`；唯一的拆卸入口是 `TeardownLevel()`。
- 存档只走 `SaveManager`（禁 SQL / PlayerPrefs）；改表三步：`CreateStatements` → `CurrentVersion + 1` → `RunMigrations`。
- 音频 = 丢文件 + `gen_audio_catalog.py`；BGM 2 源 + `AudioFadeDriver`；倍速唯一源 `Core/GameClock.cs`（`timeScale` 只取 0/1）。
- ★塔型：Normal1（打飞+走）/ Aoe2 火力仅打走 / Slow3 光环；Pierce4、Laser5 已删（编号不回收，别复用）；对空与否看塔表 `canAttackAir`。
- ★塔攻击表现：普通/火力塔不发子弹，开火 = 即时命中 + 序列帧。
  - `TowerFireFx`：枪口焰挂到炮管 `BarrelPoint` 子节点、local 置零；落点爆炸走对象池；帧由 `gen_tower_fire_frames.py` 生成。
  - ★散帧 meta 必须 `alignment: 9`(Custom) + `spritePivot y = 0.2`；写成 `alignment: 1` = TopLeft（底中应是 7）→ 焰会被甩到炮口右下角。
  - 时长权威 = `BaseBullet.SlowDurationSec` / `DotDurationSec`。
- ★建造交互 v3：点按 = 放置态；长按 0.25s 或位移 30px = 拖拽（ghost 跟手、松手校验、拖回按钮或拖出棋盘静默取消）。
- 地图链路：棋盘 → `levelmap_export.json` → `LevelMap.xlsx` → `tblevelmap.json` → `SceneInfo.xlsx`；日志前缀 `[Place]` / `[HUD]` / `[TowerInfoView]` / `[Audit]`。
- ★新增一关 = 四表齐全：LevelMap(id) + SceneInfo(mapId、RoundList) + RoundData + EnemyList。现役 20 关 × 20 波。
- ★编辑器全解锁 = `SaveManager.UnlockAllLevelsInEditor`（真机仍逐关解锁）。
