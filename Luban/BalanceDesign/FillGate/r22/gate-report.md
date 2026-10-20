# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 18 | 50% | fill | 26 | 26 | 39 | 14 | 0/20 | 0.880 | 2185 | — |
| 18 | 70% | fill | 37 | 37 | 55 | 9 | 8/20 | 1.192 | 2415 | — |
| 18 | 85% | fill | 45 | 45 | 63 | 11 | 6/20 | 1.187 | 2135 | — |
| 18 | 100% | fill | 53 | 53 | 71 | 10 | 10/20 | 1.159 | 1790 | — |
| 18 | 100% | no_upgrade | 53 | 53 | 71 | 14 | 6/20 | 1.137 | 0 | — |
| 24 | 50% | fill | 27 | 27 | 38 | 14 | 0/20 | 0.971 | 2985 | — |
| 24 | 70% | fill | 38 | 38 | 38 | 14 | 0/20 | 0.780 | 1795 | — |
| 24 | 85% | fill | 46 | 46 | 46 | 15 | 0/20 | 1.067 | 2590 | — |
| 24 | 100% | fill | 54 | 54 | 54 | 1 | 16/20 | 1.059 | 2310 | — |
| 24 | 100% | no_upgrade | 54 | 54 | 54 | 12 | 0/20 | 1.044 | 0 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 18 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 24 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |

## 明细

- L18 G1: 50% maze (26 towers): leaked=14 hp=0
- L18 G2: 70% maze (37 towers): leaked=9 hp=8
- L18 G3: 85% maze (45 towers): five_star=False leaked=11 ratio=1.187
- L18 G4: full maze (53/53 towers): five_star=False ratio=1.159 upgrade=1790/466
- L18 G5: full maze, no upgrades: five_star=False leaked=14 ratio=1.137
- L24 G1: 50% maze (27 towers): leaked=14 hp=0
- L24 G2: 70% maze (38 towers): leaked=14 hp=0
- L24 G3: 85% maze (46 towers): five_star=False leaked=15 ratio=1.067
- L24 G4: full maze (54/54 towers): five_star=False ratio=1.059 upgrade=2310/475
- L24 G5: full maze, no upgrades: five_star=False leaked=12 ratio=1.044
