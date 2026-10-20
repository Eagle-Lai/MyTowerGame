# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 6 | 50% | fill | 27 | 27 | 39 | 12 | 0/20 | 0.772 | 1115 | — |
| 6 | 70% | fill | 38 | 38 | 41 | 12 | 0/20 | 0.805 | 860 | — |
| 6 | 85% | fill | 46 | 46 | 57 | 2 | 16/20 | 1.144 | 1105 | — |
| 6 | 100% | fill | 54 | 54 | 57 | 1 | 18/20 | 1.115 | 765 | — |
| 6 | 100% | no_upgrade | 54 | 54 | 57 | 1 | 18/20 | 1.103 | 0 | — |
| 30 | 50% | fill | 26 | 26 | 41 | 13 | 0/20 | 0.855 | 3295 | — |
| 30 | 70% | fill | 37 | 37 | 53 | 7 | 5/20 | 0.950 | 3405 | — |
| 30 | 85% | fill | 45 | 45 | 57 | 0 | 20/20 | 0.944 | 3120 | ★ |
| 30 | 100% | fill | 53 | 53 | 57 | 1 | 16/20 | 0.926 | 2830 | — |
| 30 | 100% | no_upgrade | 53 | 53 | 57 | 15 | 0/20 | 0.921 | 0 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 6 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 30 | ✓ | ✓ | ✗ | ✓ | ✓ | FAIL G3 |

## 明细

- L6 G1: 50% maze (27 towers): leaked=12 hp=0
- L6 G2: 70% maze (38 towers): leaked=12 hp=0
- L6 G3: 85% maze (46 towers): five_star=False leaked=2 ratio=1.144
- L6 G4: full maze (54/54 towers): five_star=False ratio=1.115 upgrade=765/475
- L6 G5: full maze, no upgrades: five_star=False leaked=1 ratio=1.103
- L30 G1: 50% maze (26 towers): leaked=13 hp=0
- L30 G2: 70% maze (37 towers): leaked=7 hp=5
- L30 G3: 85% maze (45 towers): five_star=True leaked=0 ratio=0.944
- L30 G4: full maze (45/45 towers): five_star=True ratio=0.944 upgrade=3120/396
- L30 G5: full maze, no upgrades: five_star=False leaked=15 ratio=0.921
