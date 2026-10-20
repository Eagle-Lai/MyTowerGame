# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 1 | 50% | fill | 15 | 15 | 24 | 10 | 5/20 | 0.738 | 1885 | — |
| 1 | 70% | fill | 21 | 21 | 30 | 0 | 20/20 | 0.719 | 1650 | ★ |
| 1 | 85% | fill | 26 | 26 | 36 | 0 | 20/20 | 0.773 | 1545 | ★ |
| 1 | 100% | fill | 30 | 30 | 42 | 0 | 20/20 | 0.635 | 1370 | ★ |
| 1 | 100% | no_upgrade | 30 | 30 | 42 | 0 | 20/20 | 0.640 | 0 | ★ |
| 6 | 50% | fill | 27 | 27 | 39 | 2 | 16/20 | 0.825 | 1725 | — |
| 6 | 70% | fill | 38 | 38 | 41 | 0 | 20/20 | 0.784 | 1370 | ★ |
| 6 | 85% | fill | 46 | 46 | 57 | 0 | 20/20 | 0.889 | 1105 | ★ |
| 6 | 100% | fill | 54 | 54 | 57 | 0 | 20/20 | 0.851 | 765 | ★ |
| 6 | 100% | no_upgrade | 54 | 54 | 57 | 0 | 20/20 | 0.850 | 0 | ★ |
| 15 | 50% | fill | 28 | 28 | 39 | 3 | 14/20 | 0.813 | 2445 | — |
| 15 | 70% | fill | 38 | 38 | 39 | 1 | 16/20 | 0.774 | 2100 | — |
| 15 | 85% | fill | 47 | 47 | 47 | 0 | 20/20 | 0.802 | 1790 | ★ |
| 15 | 100% | fill | 55 | 55 | 55 | 0 | 20/20 | 0.833 | 1535 | ★ |
| 15 | 100% | no_upgrade | 55 | 55 | 55 | 0 | 20/20 | 0.834 | 0 | ★ |
| 30 | 50% | fill | 26 | 26 | 41 | 14 | 0/20 | 0.922 | 3745 | — |
| 30 | 70% | fill | 37 | 37 | 53 | 1 | 16/20 | 0.922 | 3405 | — |
| 30 | 85% | fill | 45 | 45 | 57 | 0 | 20/20 | 0.903 | 3120 | ★ |
| 30 | 100% | fill | 53 | 53 | 57 | 0 | 20/20 | 0.894 | 2830 | ★ |
| 30 | 100% | no_upgrade | 53 | 53 | 57 | 7 | 4/20 | 0.891 | 0 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 1 | — | — | ✗ | ✗ | — | FAIL G3,G4 |
| 6 | ✗ | ✗ | ✗ | ✗ | — | FAIL G1,G2,G3,G4 |
| 15 | ✗ | ✓ | ✗ | ✗ | ✗ | FAIL G1,G3,G4,G5 |
| 30 | ✓ | ✓ | ✗ | ✗ | ✓ | FAIL G3,G4 |

## 明细

- L1 G1: 50% maze (15 towers): leaked=10 hp=5
- L1 G2: 70% maze (21 towers): leaked=0 hp=20
- L1 G3: 85% maze (26 towers): five_star=True leaked=0 ratio=0.773
- L1 G4: full maze (30/30 towers): five_star=True ratio=0.635 upgrade=1370/264
- L1 G5: full maze, no upgrades: five_star=True leaked=0 ratio=0.640
- L6 G1: 50% maze (27 towers): leaked=2 hp=16
- L6 G2: 70% maze (38 towers): leaked=0 hp=20
- L6 G3: 85% maze (46 towers): five_star=True leaked=0 ratio=0.889
- L6 G4: full maze (54/54 towers): five_star=True ratio=0.851 upgrade=765/475
- L6 G5: full maze, no upgrades: five_star=True leaked=0 ratio=0.850
- L15 G1: 50% maze (28 towers): leaked=3 hp=14
- L15 G2: 70% maze (38 towers): leaked=1 hp=16
- L15 G3: 85% maze (47 towers): five_star=True leaked=0 ratio=0.802
- L15 G4: full maze (47/47 towers): five_star=True ratio=0.802 upgrade=1790/414
- L15 G5: full maze, no upgrades: five_star=True leaked=0 ratio=0.834
- L30 G1: 50% maze (26 towers): leaked=14 hp=0
- L30 G2: 70% maze (37 towers): leaked=1 hp=16
- L30 G3: 85% maze (45 towers): five_star=True leaked=0 ratio=0.903
- L30 G4: full maze (53/53 towers): five_star=True ratio=0.894 upgrade=2830/466
- L30 G5: full maze, no upgrades: five_star=False leaked=7 ratio=0.891
