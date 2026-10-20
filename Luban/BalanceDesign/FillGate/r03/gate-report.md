# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 2 | 100% | fill | 59 | 59 | 71 | 0 | 20/20 | 1.223 | 1020 | — |
| 3 | 100% | fill | 52 | 52 | 56 | 20 | 0/20 | 1.307 | 1275 | — |
| 4 | 100% | fill | 59 | 59 | 71 | 0 | 20/20 | 1.375 | 1110 | — |
| 5 | 100% | fill | 52 | 52 | 56 | 5 | 14/20 | 1.368 | 1445 | — |
| 7 | 100% | fill | 55 | 55 | 65 | 7 | 13/20 | 1.309 | 1530 | — |
| 11 | 100% | fill | 48 | 48 | 68 | 8 | 11/20 | 1.310 | 2135 | — |
| 12 | 100% | fill | 48 | 48 | 68 | 15 | 5/20 | 1.277 | 2215 | — |
| 14 | 100% | fill | 59 | 59 | 56 | 1 | 16/20 | 1.168 | 1960 | — |
| 17 | 100% | fill | 49 | 49 | 56 | 1 | 16/20 | 1.150 | 2560 | — |
| 18 | 100% | fill | 56 | 56 | 71 | 0 | 20/20 | 1.109 | 2385 | — |
| 27 | 100% | fill | 60 | 60 | 60 | 0 | 20/20 | 0.996 | 3015 | ★ |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 2 | — | — | — | ✗ | — | FAIL G4 |
| 3 | — | — | — | ✗ | — | FAIL G4 |
| 4 | — | — | — | ✗ | — | FAIL G4 |
| 5 | — | — | — | ✗ | — | FAIL G4 |
| 7 | — | — | — | ✗ | — | FAIL G4 |
| 11 | — | — | — | ✗ | — | FAIL G4 |
| 12 | — | — | — | ✗ | — | FAIL G4 |
| 14 | — | — | — | ✗ | — | FAIL G4 |
| 17 | — | — | — | ✗ | — | FAIL G4 |
| 18 | — | — | — | ✗ | — | FAIL G4 |
| 27 | — | — | — | ✓ | — | PASS  |

## 明细

- L2 G4: full maze (59/59): clear=True policy=True budget=True time=False ratio=1.223 leaked=0
- L3 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.307 leaked=20
- L4 G4: full maze (59/59): clear=True policy=True budget=True time=False ratio=1.375 leaked=0
- L5 G4: full maze (52/52): clear=False policy=True budget=True time=False ratio=1.368 leaked=5
- L7 G4: full maze (55/55): clear=False policy=True budget=True time=False ratio=1.309 leaked=7
- L11 G4: full maze (48/48): clear=False policy=True budget=True time=False ratio=1.310 leaked=8
- L12 G4: full maze (48/48): clear=False policy=True budget=True time=False ratio=1.277 leaked=15
- L14 G4: full maze (59/59): clear=False policy=True budget=True time=False ratio=1.168 leaked=1
- L17 G4: full maze (49/49): clear=False policy=True budget=True time=False ratio=1.150 leaked=1
- L18 G4: full maze (56/56): clear=True policy=True budget=True time=False ratio=1.109 leaked=0
- L27 G4: full maze (60/60): clear=True policy=True budget=True time=True ratio=0.996 leaked=0
