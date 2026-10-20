# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 5 | 50% | fill | 26 | 26 | 24 | 15 | 0/20 | 0.532 | 1410 | — |
| 5 | 70% | fill | 36 | 36 | 40 | 13 | 0/20 | 1.128 | 1625 | — |
| 5 | 85% | fill | 44 | 44 | 42 | 13 | 0/20 | 1.375 | 1620 | — |
| 5 | 100% | fill | 52 | 52 | 56 | 1 | 18/20 | 1.361 | 1700 | — |
| 5 | 100% | no_upgrade | 52 | 52 | 56 | 1 | 18/20 | 1.312 | 0 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 5 | — | — | ✓ | ✗ | — | FAIL G4 |

## 明细

- L5 G1: 50% maze (26 towers): leaked=15 hp=0
- L5 G2: 70% maze (36 towers): leaked=13 hp=0
- L5 G3: 85% maze (44 towers): structural_clear=False leaked=13
- L5 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.361 leaked=1
- L5 G5: full maze, no upgrades: structural_clear=False leaked=1
