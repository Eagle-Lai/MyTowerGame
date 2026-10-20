# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 3 | 100% | fill | 52 | 52 | 56 | 1 | 18/20 | 1.332 | 1530 | — |
| 5 | 100% | fill | 52 | 52 | 56 | 1 | 18/20 | 1.396 | 1700 | — |
| 6 | 100% | fill | 58 | 58 | 57 | 1 | 18/20 | 1.197 | 1530 | — |
| 8 | 100% | fill | 59 | 59 | 54 | 0 | 20/20 | 1.251 | 1705 | — |
| 9 | 100% | fill | 59 | 59 | 60 | 0 | 20/20 | 1.270 | 1785 | — |
| 11 | 100% | fill | 48 | 48 | 68 | 0 | 20/20 | 1.290 | 2295 | — |
| 24 | 100% | fill | 59 | 59 | 54 | 0 | 20/20 | 1.043 | 3010 | — |
| 26 | 100% | fill | 59 | 59 | 49 | 13 | 0/20 | 1.066 | 2995 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 3 | — | — | — | ✗ | — | FAIL G4 |
| 5 | — | — | — | ✗ | — | FAIL G4 |
| 6 | — | — | — | ✗ | — | FAIL G4 |
| 8 | — | — | — | ✗ | — | FAIL G4 |
| 9 | — | — | — | ✗ | — | FAIL G4 |
| 11 | — | — | — | ✗ | — | FAIL G4 |
| 24 | — | — | — | ✓ | — | PASS  |
| 26 | — | — | — | ✗ | — | FAIL G4 |

## 明细

- L3 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.332 leaked=1
- L5 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.396 leaked=1
- L6 G4: full maze (58/58): clear=False policy=True budget=True time=False ratio=1.197 leaked=1
- L8 G4: full maze (59/59): clear=True policy=True budget=True time=False ratio=1.251 leaked=0
- L9 G4: full maze (59/59): clear=True policy=True budget=True time=False ratio=1.270 leaked=0
- L11 G4: full maze (48/48): clear=True policy=True budget=True time=False ratio=1.290 leaked=0
- L24 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=1.043 leaked=0
- L26 G4: full maze (59/59): clear=False policy=True budget=True time=False ratio=1.066 leaked=13
