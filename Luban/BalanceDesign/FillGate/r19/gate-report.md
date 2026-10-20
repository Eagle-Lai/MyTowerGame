# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 6 | 50% | fill | 27 | 27 | 39 | 12 | 0/20 | 0.836 | 1205 | — |
| 6 | 70% | fill | 38 | 38 | 41 | 12 | 0/20 | 0.852 | 1030 | — |
| 6 | 85% | fill | 46 | 46 | 57 | 1 | 18/20 | 1.112 | 1105 | — |
| 6 | 100% | fill | 54 | 54 | 57 | 0 | 20/20 | 1.081 | 765 | — |
| 6 | 100% | no_upgrade | 54 | 54 | 57 | 1 | 18/20 | 1.072 | 0 | — |
| 24 | 50% | fill | 27 | 27 | 38 | 14 | 0/20 | 0.864 | 3165 | — |
| 24 | 70% | fill | 38 | 38 | 38 | 13 | 0/20 | 0.663 | 1795 | — |
| 24 | 85% | fill | 46 | 46 | 46 | 14 | 0/20 | 0.906 | 2590 | — |
| 24 | 100% | fill | 54 | 54 | 54 | 0 | 20/20 | 0.881 | 2310 | ★ |
| 24 | 100% | no_upgrade | 54 | 54 | 54 | 6 | 6/20 | 0.873 | 0 | — |
| 30 | 50% | fill | 26 | 26 | 41 | 15 | 0/20 | 0.915 | 3835 | — |
| 30 | 70% | fill | 37 | 37 | 53 | 0 | 20/20 | 0.916 | 3405 | ★ |
| 30 | 85% | fill | 45 | 45 | 57 | 0 | 20/20 | 0.890 | 3120 | ★ |
| 30 | 100% | fill | 53 | 53 | 57 | 0 | 20/20 | 0.887 | 2830 | ★ |
| 30 | 100% | no_upgrade | 53 | 53 | 57 | 5 | 8/20 | 0.888 | 0 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 6 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 24 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 30 | ✓ | ✗ | ✗ | ✗ | ✓ | FAIL G2,G3,G4 |

## 明细

- L6 G1: 50% maze (27 towers): leaked=12 hp=0
- L6 G2: 70% maze (38 towers): leaked=12 hp=0
- L6 G3: 85% maze (46 towers): five_star=False leaked=1 ratio=1.112
- L6 G4: full maze (54/54 towers): five_star=False ratio=1.081 upgrade=765/475
- L6 G5: full maze, no upgrades: five_star=False leaked=1 ratio=1.072
- L24 G1: 50% maze (27 towers): leaked=14 hp=0
- L24 G2: 70% maze (38 towers): leaked=13 hp=0
- L24 G3: 85% maze (46 towers): five_star=False leaked=14 ratio=0.906
- L24 G4: full maze (54/54 towers): five_star=True ratio=0.881 upgrade=2310/475
- L24 G5: full maze, no upgrades: five_star=False leaked=6 ratio=0.873
- L30 G1: 50% maze (26 towers): leaked=15 hp=0
- L30 G2: 70% maze (37 towers): leaked=0 hp=20
- L30 G3: 85% maze (45 towers): five_star=True leaked=0 ratio=0.890
- L30 G4: full maze (53/53 towers): five_star=True ratio=0.887 upgrade=2830/466
- L30 G5: full maze, no upgrades: five_star=False leaked=5 ratio=0.888
