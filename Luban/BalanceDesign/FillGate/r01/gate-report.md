# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 1 | 50% | fill | 15 | 15 | 24 | 14 | 0/20 | 0.955 | 1325 | — |
| 1 | 70% | fill | 21 | 21 | 30 | 8 | 6/20 | 0.981 | 1300 | — |
| 1 | 85% | fill | 26 | 26 | 36 | 2 | 16/20 | 1.043 | 1295 | — |
| 1 | 100% | fill | 30 | 30 | 42 | 0 | 20/20 | 0.849 | 1370 | ★ |
| 1 | 100% | no_upgrade | 30 | 30 | 42 | 0 | 20/20 | 0.860 | 0 | ★ |
| 2 | 50% | fill | 28 | 28 | 39 | 19 | 0/20 | 0.802 | 425 | — |
| 2 | 70% | fill | 39 | 39 | 53 | 16 | 0/20 | 1.401 | 425 | — |
| 2 | 85% | fill | 48 | 48 | 63 | 13 | 7/20 | 1.342 | 425 | — |
| 2 | 100% | fill | 56 | 56 | 71 | 5 | 15/20 | 1.462 | 425 | — |
| 2 | 100% | no_upgrade | 56 | 56 | 71 | 6 | 14/20 | 1.451 | 0 | — |
| 3 | 50% | fill | 24 | 24 | 24 | 17 | 0/20 | 0.358 | 0 | — |
| 3 | 70% | fill | 34 | 27 | 18 | 15 | 0/20 | 0.355 | 0 | — |
| 3 | 85% | fill | 42 | 33 | 18 | 16 | 0/20 | 0.424 | 0 | — |
| 3 | 100% | fill | 49 | 27 | 18 | 16 | 0/20 | 0.350 | 0 | — |
| 3 | 100% | no_upgrade | 49 | 27 | 18 | 16 | 0/20 | 0.350 | 0 | — |
| 4 | 50% | fill | 28 | 28 | 39 | 16 | 0/20 | 0.935 | 425 | — |
| 4 | 70% | fill | 39 | 39 | 53 | 16 | 0/20 | 1.269 | 510 | — |
| 4 | 85% | fill | 48 | 48 | 63 | 20 | 0/20 | 1.219 | 510 | — |
| 4 | 100% | fill | 56 | 56 | 71 | 8 | 12/20 | 1.370 | 510 | — |
| 4 | 100% | no_upgrade | 56 | 56 | 71 | 8 | 12/20 | 1.371 | 0 | — |
| 5 | 50% | fill | 24 | 24 | 24 | 16 | 0/20 | 0.329 | 90 | — |
| 5 | 70% | fill | 34 | 25 | 20 | 16 | 0/20 | 0.281 | 0 | — |
| 5 | 85% | fill | 42 | 39 | 22 | 14 | 0/20 | 0.543 | 0 | — |
| 5 | 100% | fill | 49 | 49 | 56 | 20 | 0/20 | 0.671 | 170 | — |
| 5 | 100% | no_upgrade | 49 | 49 | 56 | 20 | 0/20 | 0.671 | 0 | — |
| 6 | 50% | fill | 27 | 27 | 39 | 12 | 0/20 | 0.889 | 685 | — |
| 6 | 70% | fill | 38 | 38 | 41 | 11 | 0/20 | 0.994 | 690 | — |
| 6 | 85% | fill | 46 | 46 | 57 | 7 | 6/20 | 1.434 | 765 | — |
| 6 | 100% | fill | 54 | 54 | 57 | 5 | 13/20 | 1.412 | 765 | — |
| 6 | 100% | no_upgrade | 54 | 54 | 57 | 7 | 9/20 | 1.400 | 0 | — |
| 7 | 50% | fill | 26 | 26 | 33 | 20 | 0/20 | 0.556 | 255 | — |
| 7 | 70% | fill | 37 | 37 | 49 | 20 | 0/20 | 0.867 | 255 | — |
| 7 | 85% | fill | 45 | 45 | 49 | 20 | 0/20 | 0.895 | 255 | — |
| 7 | 100% | fill | 53 | 53 | 65 | 20 | 0/20 | 0.919 | 255 | — |
| 7 | 100% | no_upgrade | 53 | 53 | 65 | 20 | 0/20 | 0.916 | 0 | — |
| 8 | 50% | fill | 27 | 27 | 28 | 14 | 0/20 | 0.735 | 860 | — |
| 8 | 70% | fill | 38 | 38 | 38 | 12 | 0/20 | 0.862 | 860 | — |
| 8 | 85% | fill | 46 | 46 | 44 | 14 | 0/20 | 1.263 | 935 | — |
| 8 | 100% | fill | 54 | 54 | 54 | 1 | 18/20 | 1.313 | 935 | — |
| 8 | 100% | no_upgrade | 54 | 54 | 54 | 6 | 8/20 | 1.296 | 0 | — |
| 9 | 50% | fill | 27 | 27 | 28 | 16 | 0/20 | 0.734 | 940 | — |
| 9 | 70% | fill | 38 | 38 | 44 | 13 | 0/20 | 1.173 | 935 | — |
| 9 | 85% | fill | 46 | 46 | 50 | 17 | 0/20 | 1.382 | 1020 | — |
| 9 | 100% | fill | 54 | 54 | 60 | 1 | 18/20 | 1.328 | 1020 | — |
| 9 | 100% | no_upgrade | 54 | 54 | 60 | 2 | 16/20 | 1.320 | 0 | — |
| 10 | 50% | fill | 26 | 26 | 35 | 13 | 0/20 | 0.778 | 1025 | — |
| 10 | 70% | fill | 37 | 37 | 41 | 11 | 0/20 | 1.095 | 1030 | — |
| 10 | 85% | fill | 45 | 45 | 53 | 17 | 0/20 | 1.385 | 1105 | — |
| 10 | 100% | fill | 53 | 53 | 57 | 3 | 15/20 | 1.261 | 1105 | — |
| 10 | 100% | no_upgrade | 53 | 53 | 57 | 6 | 9/20 | 1.251 | 0 | — |
| 11 | 50% | fill | 23 | 23 | 38 | 16 | 0/20 | 0.503 | 435 | — |
| 11 | 70% | fill | 32 | 32 | 40 | 20 | 0/20 | 0.540 | 510 | — |
| 11 | 85% | fill | 39 | 39 | 54 | 20 | 0/20 | 0.727 | 510 | — |
| 11 | 100% | fill | 46 | 46 | 68 | 20 | 0/20 | 0.715 | 510 | — |
| 11 | 100% | no_upgrade | 46 | 46 | 68 | 20 | 0/20 | 0.707 | 0 | — |
| 12 | 50% | fill | 23 | 23 | 38 | 14 | 0/20 | 0.550 | 655 | — |
| 12 | 70% | fill | 32 | 32 | 40 | 20 | 0/20 | 0.393 | 340 | — |
| 12 | 85% | fill | 39 | 39 | 54 | 20 | 0/20 | 0.782 | 680 | — |
| 12 | 100% | fill | 46 | 46 | 68 | 20 | 0/20 | 0.759 | 680 | — |
| 12 | 100% | no_upgrade | 46 | 46 | 68 | 20 | 0/20 | 0.702 | 0 | — |
| 13 | 50% | fill | 28 | 28 | 39 | 13 | 0/20 | 0.971 | 1205 | — |
| 13 | 70% | fill | 40 | 40 | 53 | 2 | 15/20 | 1.144 | 1275 | — |
| 13 | 85% | fill | 48 | 48 | 55 | 0 | 20/20 | 0.998 | 1275 | ★ |
| 13 | 100% | fill | 57 | 57 | 71 | 0 | 20/20 | 1.081 | 1275 | — |
| 13 | 100% | no_upgrade | 57 | 57 | 71 | 0 | 20/20 | 1.080 | 0 | — |
| 14 | 50% | fill | 27 | 27 | 40 | 13 | 0/20 | 0.874 | 1375 | — |
| 14 | 70% | fill | 38 | 38 | 40 | 13 | 0/20 | 0.853 | 1280 | — |
| 14 | 85% | fill | 46 | 46 | 48 | 20 | 0/20 | 1.175 | 1450 | — |
| 14 | 100% | fill | 54 | 54 | 56 | 7 | 10/20 | 1.239 | 1450 | — |
| 14 | 100% | no_upgrade | 54 | 54 | 56 | 12 | 2/20 | 1.203 | 0 | — |
| 15 | 50% | fill | 28 | 28 | 39 | 12 | 0/20 | 0.975 | 1465 | — |
| 15 | 70% | fill | 38 | 38 | 39 | 14 | 0/20 | 1.013 | 1470 | — |
| 15 | 85% | fill | 47 | 47 | 47 | 16 | 0/20 | 1.115 | 1535 | — |
| 15 | 100% | fill | 55 | 55 | 55 | 1 | 16/20 | 1.165 | 1535 | — |
| 15 | 100% | no_upgrade | 55 | 55 | 55 | 2 | 14/20 | 1.139 | 0 | — |
| 16 | 50% | fill | 28 | 28 | 39 | 17 | 0/20 | 0.960 | 1545 | — |
| 16 | 70% | fill | 38 | 38 | 39 | 14 | 0/20 | 1.011 | 1560 | — |
| 16 | 85% | fill | 47 | 47 | 47 | 17 | 0/20 | 1.107 | 1615 | — |
| 16 | 100% | fill | 55 | 55 | 55 | 0 | 20/20 | 1.169 | 1615 | — |
| 16 | 100% | no_upgrade | 55 | 55 | 55 | 1 | 16/20 | 1.133 | 0 | — |
| 17 | 50% | fill | 23 | 23 | 24 | 14 | 0/20 | 0.473 | 995 | — |
| 17 | 70% | fill | 32 | 32 | 40 | 20 | 0/20 | 0.452 | 765 | — |
| 17 | 85% | fill | 39 | 39 | 42 | 20 | 0/20 | 0.590 | 935 | — |
| 17 | 100% | fill | 46 | 46 | 56 | 20 | 0/20 | 0.688 | 1020 | — |
| 17 | 100% | no_upgrade | 46 | 46 | 56 | 20 | 0/20 | 0.685 | 0 | — |
| 18 | 50% | fill | 26 | 26 | 39 | 13 | 0/20 | 0.761 | 1735 | — |
| 18 | 70% | fill | 37 | 37 | 55 | 20 | 0/20 | 1.053 | 1785 | — |
| 18 | 85% | fill | 45 | 45 | 63 | 19 | 0/20 | 1.223 | 1705 | — |
| 18 | 100% | fill | 53 | 53 | 71 | 12 | 8/20 | 1.201 | 1790 | — |
| 18 | 100% | no_upgrade | 53 | 53 | 71 | 18 | 2/20 | 1.178 | 0 | — |
| 19 | 50% | fill | 28 | 28 | 29 | 11 | 0/20 | 0.599 | 1120 | — |
| 19 | 70% | fill | 38 | 38 | 45 | 16 | 0/20 | 1.181 | 1795 | — |
| 19 | 85% | fill | 47 | 47 | 61 | 0 | 20/20 | 1.104 | 1795 | — |
| 19 | 100% | fill | 55 | 55 | 61 | 0 | 20/20 | 1.035 | 1870 | — |
| 19 | 100% | no_upgrade | 55 | 55 | 61 | 1 | 16/20 | 1.036 | 0 | — |
| 20 | 50% | fill | 28 | 28 | 39 | 13 | 0/20 | 0.865 | 1905 | — |
| 20 | 70% | fill | 38 | 38 | 51 | 3 | 14/20 | 1.126 | 1965 | — |
| 20 | 85% | fill | 47 | 47 | 55 | 13 | 0/20 | 1.275 | 1955 | — |
| 20 | 100% | fill | 55 | 55 | 71 | 0 | 20/20 | 1.002 | 1965 | — |
| 20 | 100% | no_upgrade | 55 | 55 | 71 | 0 | 20/20 | 0.986 | 0 | ★ |
| 21 | 50% | fill | 26 | 26 | 43 | 13 | 0/20 | 0.927 | 1995 | — |
| 21 | 70% | fill | 37 | 37 | 57 | 16 | 0/20 | 1.210 | 1965 | — |
| 21 | 85% | fill | 45 | 45 | 59 | 0 | 20/20 | 1.090 | 1965 | — |
| 21 | 100% | fill | 53 | 53 | 75 | 0 | 20/20 | 1.018 | 2050 | — |
| 21 | 100% | no_upgrade | 53 | 53 | 75 | 0 | 20/20 | 1.003 | 0 | — |
| 22 | 50% | fill | 26 | 26 | 35 | 15 | 0/20 | 0.689 | 2085 | — |
| 22 | 70% | fill | 36 | 36 | 47 | 18 | 0/20 | 1.216 | 2145 | — |
| 22 | 85% | fill | 44 | 44 | 51 | 15 | 0/20 | 1.065 | 2220 | — |
| 22 | 100% | fill | 52 | 52 | 65 | 0 | 20/20 | 1.143 | 2220 | — |
| 22 | 100% | no_upgrade | 52 | 52 | 65 | 5 | 15/20 | 1.135 | 0 | — |
| 23 | 50% | fill | 27 | 27 | 27 | 13 | 0/20 | 0.488 | 1045 | — |
| 23 | 70% | fill | 38 | 38 | 41 | 14 | 0/20 | 1.017 | 2190 | — |
| 23 | 85% | fill | 46 | 46 | 43 | 13 | 0/20 | 1.032 | 2225 | — |
| 23 | 100% | fill | 54 | 54 | 59 | 0 | 20/20 | 0.997 | 2245 | ★ |
| 23 | 100% | no_upgrade | 54 | 54 | 59 | 3 | 12/20 | 1.006 | 0 | — |
| 24 | 50% | fill | 27 | 27 | 38 | 13 | 0/20 | 0.926 | 2265 | — |
| 24 | 70% | fill | 38 | 38 | 38 | 13 | 0/20 | 0.787 | 1795 | — |
| 24 | 85% | fill | 46 | 46 | 46 | 15 | 0/20 | 1.079 | 2230 | — |
| 24 | 100% | fill | 54 | 54 | 54 | 1 | 16/20 | 1.067 | 2310 | — |
| 24 | 100% | no_upgrade | 54 | 54 | 54 | 13 | 0/20 | 1.045 | 0 | — |
| 25 | 50% | fill | 26 | 26 | 38 | 14 | 0/20 | 0.790 | 2355 | — |
| 25 | 70% | fill | 37 | 37 | 48 | 14 | 0/20 | 0.968 | 2355 | — |
| 25 | 85% | fill | 45 | 45 | 48 | 15 | 0/20 | 1.052 | 2355 | — |
| 25 | 100% | fill | 53 | 53 | 54 | 2 | 14/20 | 1.064 | 2395 | — |
| 25 | 100% | no_upgrade | 53 | 53 | 54 | 14 | 0/20 | 1.044 | 0 | — |
| 26 | 50% | fill | 26 | 26 | 37 | 14 | 0/20 | 0.875 | 2460 | — |
| 26 | 70% | fill | 37 | 37 | 37 | 14 | 0/20 | 0.705 | 1795 | — |
| 26 | 85% | fill | 45 | 45 | 37 | 13 | 0/20 | 0.702 | 1705 | — |
| 26 | 100% | fill | 53 | 53 | 49 | 1 | 16/20 | 0.996 | 2490 | — |
| 26 | 100% | no_upgrade | 53 | 53 | 49 | 13 | 0/20 | 0.966 | 0 | — |
| 27 | 50% | fill | 28 | 28 | 44 | 14 | 0/20 | 0.951 | 2445 | — |
| 27 | 70% | fill | 38 | 38 | 50 | 15 | 0/20 | 1.040 | 2425 | — |
| 27 | 85% | fill | 47 | 47 | 50 | 14 | 0/20 | 1.104 | 2410 | — |
| 27 | 100% | fill | 55 | 55 | 60 | 7 | 5/20 | 1.119 | 2475 | — |
| 27 | 100% | no_upgrade | 55 | 55 | 60 | 14 | 0/20 | 1.089 | 0 | — |
| 28 | 50% | fill | 27 | 27 | 40 | 14 | 0/20 | 0.882 | 2625 | — |
| 28 | 70% | fill | 38 | 38 | 54 | 0 | 20/20 | 0.884 | 2595 | ★ |
| 28 | 85% | fill | 46 | 46 | 56 | 0 | 20/20 | 0.964 | 2575 | ★ |
| 28 | 100% | fill | 54 | 54 | 70 | 0 | 20/20 | 0.983 | 2660 | ★ |
| 28 | 100% | no_upgrade | 54 | 54 | 70 | 0 | 20/20 | 0.976 | 0 | ★ |
| 29 | 50% | fill | 26 | 26 | 38 | 14 | 0/20 | 0.875 | 2745 | — |
| 29 | 70% | fill | 37 | 37 | 38 | 15 | 0/20 | 0.846 | 2725 | — |
| 29 | 85% | fill | 45 | 45 | 38 | 14 | 0/20 | 0.891 | 2725 | — |
| 29 | 100% | fill | 53 | 53 | 52 | 0 | 20/20 | 0.965 | 2755 | ★ |
| 29 | 100% | no_upgrade | 53 | 53 | 52 | 2 | 14/20 | 0.950 | 0 | — |
| 30 | 50% | fill | 26 | 26 | 41 | 14 | 0/20 | 0.917 | 2805 | — |
| 30 | 70% | fill | 37 | 37 | 53 | 13 | 0/20 | 1.076 | 2775 | — |
| 30 | 85% | fill | 45 | 45 | 57 | 0 | 20/20 | 1.065 | 2760 | — |
| 30 | 100% | fill | 53 | 53 | 57 | 1 | 16/20 | 1.046 | 2830 | — |
| 30 | 100% | no_upgrade | 53 | 53 | 57 | 14 | 0/20 | 1.040 | 0 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 1 | — | — | ✓ | ✗ | — | FAIL G4 |
| 2 | — | — | ✓ | ✗ | — | FAIL G4 |
| 3 | — | — | ✓ | ✗ | — | FAIL G4 |
| 4 | — | — | ✓ | ✗ | — | FAIL G4 |
| 5 | — | — | ✓ | ✗ | — | FAIL G4 |
| 6 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 7 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 8 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 9 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 10 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 11 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 12 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 13 | ✓ | ✓ | ✗ | ✗ | — | FAIL G3,G4 |
| 14 | ✓ | ✓ | ✓ | ✗ | — | FAIL G4 |
| 15 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 16 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 17 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 18 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 19 | ✓ | ✓ | ✗ | ✓ | ✓ | FAIL G3 |
| 20 | ✓ | ✓ | ✓ | ✓ | ✗ | FAIL G5 |
| 21 | ✓ | ✓ | ✗ | ✓ | ✗ | FAIL G3,G5 |
| 22 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 23 | ✓ | ✓ | ✓ | ✓ | ✓ | PASS  |
| 24 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 25 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 26 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 27 | ✓ | ✓ | ✓ | ✗ | ✓ | FAIL G4 |
| 28 | ✓ | ✗ | ✗ | ✓ | ✗ | FAIL G2,G3,G5 |
| 29 | ✓ | ✓ | ✓ | ✓ | ✓ | PASS  |
| 30 | ✓ | ✓ | ✗ | ✗ | ✓ | FAIL G3,G4 |

## 明细

- L1 G1: 50% maze (15 towers): leaked=14 hp=0
- L1 G2: 70% maze (21 towers): leaked=8 hp=6
- L1 G3: 85% maze (26 towers): structural_clear=False leaked=2
- L1 G4: full maze (30/30): clear=True policy=True budget=True time=False ratio=0.849 leaked=0
- L1 G5: full maze, no upgrades: structural_clear=True leaked=0
- L2 G1: 50% maze (28 towers): leaked=19 hp=0
- L2 G2: 70% maze (39 towers): leaked=16 hp=0
- L2 G3: 85% maze (48 towers): structural_clear=False leaked=13
- L2 G4: full maze (56/56): clear=False policy=True budget=False time=False ratio=1.462 leaked=5
- L2 G5: full maze, no upgrades: structural_clear=False leaked=6
- L3 G1: 50% maze (24 towers): leaked=17 hp=0
- L3 G2: 70% maze (27 towers): leaked=15 hp=0
- L3 G3: 85% maze (33 towers): structural_clear=False leaked=16
- L3 G4: full maze (27/49): clear=False policy=False budget=False time=False ratio=0.350 leaked=16
- L3 G5: full maze, no upgrades: structural_clear=False leaked=16
- L4 G1: 50% maze (28 towers): leaked=16 hp=0
- L4 G2: 70% maze (39 towers): leaked=16 hp=0
- L4 G3: 85% maze (48 towers): structural_clear=False leaked=20
- L4 G4: full maze (56/56): clear=False policy=True budget=True time=False ratio=1.370 leaked=8
- L4 G5: full maze, no upgrades: structural_clear=False leaked=8
- L5 G1: 50% maze (24 towers): leaked=16 hp=0
- L5 G2: 70% maze (25 towers): leaked=16 hp=0
- L5 G3: 85% maze (39 towers): structural_clear=False leaked=14
- L5 G4: full maze (49/49): clear=False policy=True budget=False time=False ratio=0.671 leaked=20
- L5 G5: full maze, no upgrades: structural_clear=False leaked=20
- L6 G1: 50% maze (27 towers): leaked=12 hp=0
- L6 G2: 70% maze (38 towers): leaked=11 hp=0
- L6 G3: 85% maze (46 towers): structural_clear=False leaked=7
- L6 G4: full maze (54/54): clear=False policy=True budget=True time=False ratio=1.412 leaked=5
- L6 G5: full maze, no upgrades: structural_clear=False leaked=7
- L7 G1: 50% maze (26 towers): leaked=20 hp=0
- L7 G2: 70% maze (37 towers): leaked=20 hp=0
- L7 G3: 85% maze (45 towers): structural_clear=False leaked=20
- L7 G4: full maze (53/53): clear=False policy=True budget=False time=True ratio=0.919 leaked=20
- L7 G5: full maze, no upgrades: structural_clear=False leaked=20
- L8 G1: 50% maze (27 towers): leaked=14 hp=0
- L8 G2: 70% maze (38 towers): leaked=12 hp=0
- L8 G3: 85% maze (46 towers): structural_clear=False leaked=14
- L8 G4: full maze (54/54): clear=False policy=True budget=True time=False ratio=1.313 leaked=1
- L8 G5: full maze, no upgrades: structural_clear=False leaked=6
- L9 G1: 50% maze (27 towers): leaked=16 hp=0
- L9 G2: 70% maze (38 towers): leaked=13 hp=0
- L9 G3: 85% maze (46 towers): structural_clear=False leaked=17
- L9 G4: full maze (54/54): clear=False policy=True budget=True time=False ratio=1.328 leaked=1
- L9 G5: full maze, no upgrades: structural_clear=False leaked=2
- L10 G1: 50% maze (26 towers): leaked=13 hp=0
- L10 G2: 70% maze (37 towers): leaked=11 hp=0
- L10 G3: 85% maze (45 towers): structural_clear=False leaked=17
- L10 G4: full maze (53/53): clear=False policy=True budget=True time=False ratio=1.261 leaked=3
- L10 G5: full maze, no upgrades: structural_clear=False leaked=6
- L11 G1: 50% maze (23 towers): leaked=16 hp=0
- L11 G2: 70% maze (32 towers): leaked=20 hp=0
- L11 G3: 85% maze (39 towers): structural_clear=False leaked=20
- L11 G4: full maze (46/46): clear=False policy=True budget=True time=False ratio=0.715 leaked=20
- L11 G5: full maze, no upgrades: structural_clear=False leaked=20
- L12 G1: 50% maze (23 towers): leaked=14 hp=0
- L12 G2: 70% maze (32 towers): leaked=20 hp=0
- L12 G3: 85% maze (39 towers): structural_clear=False leaked=20
- L12 G4: full maze (46/46): clear=False policy=True budget=True time=False ratio=0.759 leaked=20
- L12 G5: full maze, no upgrades: structural_clear=False leaked=20
- L13 G1: 50% maze (28 towers): leaked=13 hp=0
- L13 G2: 70% maze (40 towers): leaked=2 hp=15
- L13 G3: 85% maze (48 towers): structural_clear=True leaked=0
- L13 G4: full maze (57/57): clear=True policy=True budget=True time=False ratio=1.081 leaked=0
- L13 G5: full maze, no upgrades: structural_clear=True leaked=0
- L14 G1: 50% maze (27 towers): leaked=13 hp=0
- L14 G2: 70% maze (38 towers): leaked=13 hp=0
- L14 G3: 85% maze (46 towers): structural_clear=False leaked=20
- L14 G4: full maze (54/54): clear=False policy=True budget=True time=False ratio=1.239 leaked=7
- L14 G5: full maze, no upgrades: structural_clear=False leaked=12
- L15 G1: 50% maze (28 towers): leaked=12 hp=0
- L15 G2: 70% maze (38 towers): leaked=14 hp=0
- L15 G3: 85% maze (47 towers): structural_clear=False leaked=16
- L15 G4: full maze (55/55): clear=False policy=True budget=True time=False ratio=1.165 leaked=1
- L15 G5: full maze, no upgrades: structural_clear=False leaked=2
- L16 G1: 50% maze (28 towers): leaked=17 hp=0
- L16 G2: 70% maze (38 towers): leaked=14 hp=0
- L16 G3: 85% maze (47 towers): structural_clear=False leaked=17
- L16 G4: full maze (55/55): clear=True policy=True budget=True time=False ratio=1.169 leaked=0
- L16 G5: full maze, no upgrades: structural_clear=False leaked=1
- L17 G1: 50% maze (23 towers): leaked=14 hp=0
- L17 G2: 70% maze (32 towers): leaked=20 hp=0
- L17 G3: 85% maze (39 towers): structural_clear=False leaked=20
- L17 G4: full maze (46/46): clear=False policy=True budget=True time=False ratio=0.688 leaked=20
- L17 G5: full maze, no upgrades: structural_clear=False leaked=20
- L18 G1: 50% maze (26 towers): leaked=13 hp=0
- L18 G2: 70% maze (37 towers): leaked=20 hp=0
- L18 G3: 85% maze (45 towers): structural_clear=False leaked=19
- L18 G4: full maze (53/53): clear=False policy=True budget=True time=False ratio=1.201 leaked=12
- L18 G5: full maze, no upgrades: structural_clear=False leaked=18
- L19 G1: 50% maze (28 towers): leaked=11 hp=0
- L19 G2: 70% maze (38 towers): leaked=16 hp=0
- L19 G3: 85% maze (47 towers): structural_clear=True leaked=0
- L19 G4: full maze (55/55): clear=True policy=True budget=True time=True ratio=1.035 leaked=0
- L19 G5: full maze, no upgrades: structural_clear=False leaked=1
- L20 G1: 50% maze (28 towers): leaked=13 hp=0
- L20 G2: 70% maze (38 towers): leaked=3 hp=14
- L20 G3: 85% maze (47 towers): structural_clear=False leaked=13
- L20 G4: full maze (55/55): clear=True policy=True budget=True time=True ratio=1.002 leaked=0
- L20 G5: full maze, no upgrades: structural_clear=True leaked=0
- L21 G1: 50% maze (26 towers): leaked=13 hp=0
- L21 G2: 70% maze (37 towers): leaked=16 hp=0
- L21 G3: 85% maze (45 towers): structural_clear=True leaked=0
- L21 G4: full maze (53/53): clear=True policy=True budget=True time=True ratio=1.018 leaked=0
- L21 G5: full maze, no upgrades: structural_clear=True leaked=0
- L22 G1: 50% maze (26 towers): leaked=15 hp=0
- L22 G2: 70% maze (36 towers): leaked=18 hp=0
- L22 G3: 85% maze (44 towers): structural_clear=False leaked=15
- L22 G4: full maze (52/52): clear=True policy=True budget=True time=False ratio=1.143 leaked=0
- L22 G5: full maze, no upgrades: structural_clear=False leaked=5
- L23 G1: 50% maze (27 towers): leaked=13 hp=0
- L23 G2: 70% maze (38 towers): leaked=14 hp=0
- L23 G3: 85% maze (46 towers): structural_clear=False leaked=13
- L23 G4: full maze (54/54): clear=True policy=True budget=True time=True ratio=0.997 leaked=0
- L23 G5: full maze, no upgrades: structural_clear=False leaked=3
- L24 G1: 50% maze (27 towers): leaked=13 hp=0
- L24 G2: 70% maze (38 towers): leaked=13 hp=0
- L24 G3: 85% maze (46 towers): structural_clear=False leaked=15
- L24 G4: full maze (54/54): clear=False policy=True budget=True time=False ratio=1.067 leaked=1
- L24 G5: full maze, no upgrades: structural_clear=False leaked=13
- L25 G1: 50% maze (26 towers): leaked=14 hp=0
- L25 G2: 70% maze (37 towers): leaked=14 hp=0
- L25 G3: 85% maze (45 towers): structural_clear=False leaked=15
- L25 G4: full maze (53/53): clear=False policy=True budget=True time=False ratio=1.064 leaked=2
- L25 G5: full maze, no upgrades: structural_clear=False leaked=14
- L26 G1: 50% maze (26 towers): leaked=14 hp=0
- L26 G2: 70% maze (37 towers): leaked=14 hp=0
- L26 G3: 85% maze (45 towers): structural_clear=False leaked=13
- L26 G4: full maze (53/53): clear=False policy=True budget=True time=True ratio=0.996 leaked=1
- L26 G5: full maze, no upgrades: structural_clear=False leaked=13
- L27 G1: 50% maze (28 towers): leaked=14 hp=0
- L27 G2: 70% maze (38 towers): leaked=15 hp=0
- L27 G3: 85% maze (47 towers): structural_clear=False leaked=14
- L27 G4: full maze (55/55): clear=False policy=True budget=True time=False ratio=1.119 leaked=7
- L27 G5: full maze, no upgrades: structural_clear=False leaked=14
- L28 G1: 50% maze (27 towers): leaked=14 hp=0
- L28 G2: 70% maze (38 towers): leaked=0 hp=20
- L28 G3: 85% maze (46 towers): structural_clear=True leaked=0
- L28 G4: full maze (54/54): clear=True policy=True budget=True time=True ratio=0.983 leaked=0
- L28 G5: full maze, no upgrades: structural_clear=True leaked=0
- L29 G1: 50% maze (26 towers): leaked=14 hp=0
- L29 G2: 70% maze (37 towers): leaked=15 hp=0
- L29 G3: 85% maze (45 towers): structural_clear=False leaked=14
- L29 G4: full maze (53/53): clear=True policy=True budget=True time=True ratio=0.965 leaked=0
- L29 G5: full maze, no upgrades: structural_clear=False leaked=2
- L30 G1: 50% maze (26 towers): leaked=14 hp=0
- L30 G2: 70% maze (37 towers): leaked=13 hp=0
- L30 G3: 85% maze (45 towers): structural_clear=True leaked=0
- L30 G4: full maze (53/53): clear=False policy=True budget=True time=True ratio=1.046 leaked=1
- L30 G5: full maze, no upgrades: structural_clear=False leaked=14
