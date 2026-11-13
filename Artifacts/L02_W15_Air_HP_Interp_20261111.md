# L02 W15 空中 hp 插值到 1050.35 + 「同波空中血条不一致」核查

时间：2026-11-11 08:59
实体工程：`D:\FreedomTower_1`（Unity 2022.3.62f3c1 / MCP 10.3.0 / 实例 FreedomTower_1@520e2c6d / 端口 6400）

## 一、数值改动

| 项 | 值 |
|---|---|
| 目标 | `Luban/Config/Datas/Levels/L02/EnemyData.xlsx` → **D58**（`6000145` / Bat / isFlying=1） |
| 旧值 → 新值 | `700.006935` → **`1050.350185`** |
| 口径 | W14 `794.606043` 与 W16 `1306.094327` 的线性中点：(794.606043+1306.094327)/2 |

改后空中曲线恢复单调：W13 683.81 → W14 794.61 → **W15 1050.35** → W16 1306.09。
W15 空中 EHP：94 × 1050.350185 = **98,732.92**（较 700 时 +29,932.27）。
W15 总 EHP：607,561.32 → **637,493.59**。

未改动：地面四怪、数量、speed、reward、isFlying、其他 29 关与其他 24 波。

## 二、「同波空中怪血量不一致」核查结论

用户反馈：游戏内 W15 同波空中怪血条不一致。逐层核查后**未发现配置或代码层面的同波血量差异**：

1. **配置层**：W15（roundId 2015）的 EnemyList 只有一段序列，1043 只中空中 **94 只，全部是 `6000145` 一个 ID**，整波只有这一行配置。
2. **波型缩放**：`TBWaveTuning` 中 L02 困难波（id=4）的 `groundHpScale` / `airHpScale` / 速度 / 护甲 / 金币倍率全部为 1.0，不产生分段差异。
3. **代码层**：`EnemyConfig.Hp = EnemyData.Hp × airHpScale`（`EnemyConfig.cs:63`），无按批次/时间段递增逻辑。
4. **对象池**：`BaseEnemy.Init()` 每次出生都重设 `TotalHp = cfg.Hp`、`CurrentHp = cfg.Hp` 并 `UpdateHpBar()`；`OnRecycle()` 清空全部跨帧状态（`BaseEnemy.cs:166-232 / 328-358`）。
5. **血条绘制**：`UpdateHpBar()` 用 `ratio = CurrentHp / TotalHp` 缩放 Fill，总宽 `_hpBarWidth` 为固定值，与最大血量绝对值无关（`BaseEnemy.cs:865-886`）。
6. **波次推进**：`WaveManager.IsRoundFinished(aliveCount)` 要求「全部出生 且 场上存活为 0」才结束回合，不存在相邻波同屏。

**因此血条长度差异只能来自「当前血量比例不同」——即被打过与没被打过。** 若确认满血状态下的血条长度也不同，需要一张截图或具体时间点，再按池化复用 / 显示链路继续定位。

## 三、验证

- 源表：回读 `D58=1050.350185`；全表 220×17 仅 1 格变化，白名单外零改动。备份 `EnemyData.xlsx.bak_20261111_before_l02w15_air_to1050`。
- 导出：菜单 `Tools/塔防/3. 导出配置表（Luban）`，`== succ ==`，11 张表，仅 `tbenemydata.json` override（08:59:01）。
- 导出 JSON：6000135=794.606 / **6000145=1050.3502** / 6000155=1306.0944，单调递增。
- `FTProject.Gen.asmdef` 保留；空中不相邻自检 750 波 / 24,399 只空中，相邻对 0，PASS。
- 编辑器 idle、未播放、未编译、`ready_for_tools=true`。

## 四、未做

- 未进 Play Mode 实测 W15 的血条表现（结论基于配置与代码静态核查）。
