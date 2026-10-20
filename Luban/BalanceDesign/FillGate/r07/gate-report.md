# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 3 | 100% | fill | 52 | 52 | 56 | 1 | 18/20 | 1.298 | 1530 | — |
| 5 | 100% | fill | 52 | 52 | 56 | 1 | 18/20 | 1.361 | 1700 | — |
| 6 | 100% | fill | 58 | 58 | 57 | 0 | 20/20 | 1.153 | 1530 | — |
| 26 | 100% | fill | 59 | 59 | 49 | 11 | 0/20 | 1.054 | 2995 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 3 | — | — | — | ✗ | — | FAIL G4 |
| 5 | — | — | — | ✗ | — | FAIL G4 |
| 6 | — | — | — | ✗ | — | FAIL G4 |
| 26 | — | — | — | ✗ | — | FAIL G4 |

## 明细

- L3 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.298 leaked=1
- L5 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.361 leaked=1
- L6 G4: full maze (58/58): clear=True policy=True budget=True time=False ratio=1.153 leaked=0
- L26 G4: full maze (59/59): clear=False policy=True budget=True time=False ratio=1.054 leaked=11
