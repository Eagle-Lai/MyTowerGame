# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 3 | 100% | fill | 52 | 52 | 56 | 1 | 18/20 | 1.332 | 1530 | — |
| 5 | 100% | fill | 52 | 52 | 56 | 1 | 18/20 | 1.396 | 1700 | — |
| 6 | 100% | fill | 58 | 58 | 57 | 2 | 16/20 | 1.204 | 1530 | — |
| 8 | 100% | fill | 59 | 59 | 54 | 1 | 18/20 | 1.255 | 1705 | — |
| 9 | 100% | fill | 59 | 59 | 60 | 1 | 18/20 | 1.279 | 1785 | — |
| 11 | 100% | fill | 48 | 48 | 68 | 1 | 18/20 | 1.312 | 2295 | — |
| 17 | 100% | fill | 49 | 49 | 56 | 0 | 20/20 | 1.132 | 2820 | — |
| 24 | 100% | fill | 59 | 59 | 54 | 1 | 16/20 | 1.058 | 3010 | — |
| 26 | 100% | fill | 59 | 59 | 49 | 0 | 20/20 | 0.922 | 2995 | ★ |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 3 | — | — | — | ✗ | — | FAIL G4 |
| 5 | — | — | — | ✗ | — | FAIL G4 |
| 6 | — | — | — | ✗ | — | FAIL G4 |
| 8 | — | — | — | ✗ | — | FAIL G4 |
| 9 | — | — | — | ✗ | — | FAIL G4 |
| 11 | — | — | — | ✗ | — | FAIL G4 |
| 17 | — | — | — | ✗ | — | FAIL G4 |
| 24 | — | — | — | ✗ | — | FAIL G4 |
| 26 | — | — | — | ✓ | — | PASS  |

## 明细

- L3 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.332 leaked=1
- L5 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.396 leaked=1
- L6 G4: full maze (58/58): clear=False policy=True budget=True time=False ratio=1.204 leaked=2
- L8 G4: full maze (59/59): clear=False policy=True budget=True time=False ratio=1.255 leaked=1
- L9 G4: full maze (59/59): clear=False policy=True budget=True time=False ratio=1.279 leaked=1
- L11 G4: full maze (48/48): clear=False policy=True budget=True time=False ratio=1.312 leaked=1
- L17 G4: full maze (49/49): clear=True policy=True budget=True time=False ratio=1.132 leaked=0
- L24 G4: full maze (59/59): clear=False policy=True budget=True time=False ratio=1.058 leaked=1
- L26 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.922 leaked=0
