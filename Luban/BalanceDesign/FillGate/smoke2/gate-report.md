# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 24 | 50% | fill | 27 | 27 | 38 | 13 | 0/20 | 0.926 | 2265 | — |
| 24 | 85% | fill | 46 | 46 | 46 | 15 | 0/20 | 1.079 | 2230 | — |
| 24 | 100% | fill | 54 | 54 | 54 | 1 | 16/20 | 1.067 | 2310 | — |
| 24 | 100% | no_upgrade | 54 | 54 | 54 | 13 | 0/20 | 1.045 | 0 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 24 | ✓ | — | ✓ | ✗ | ✓ | FAIL G4 |

## 明细

- L24 G1: 50% maze (27 towers): leaked=13 hp=0
- L24 G3: 85% maze (46 towers): structural_clear=False leaked=15
- L24 G4: full maze (54/54): clear=False policy=True budget=True time=False ratio=1.067 leaked=1
- L24 G5: full maze, no upgrades: structural_clear=False leaked=13
