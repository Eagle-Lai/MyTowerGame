# 占用阶梯闸门报告

> 离线模拟器预测；"100% 迷宫"指参考蛇形墙位全部建成，不是地图每个格子。
> 五星口径已镜像，最终仍由 C# `LevelRatingEvaluator` 判定。

| 关 | 迷宫份数 | 模式 | 目标塔 | 实建 | 路径 | 漏怪 | HP | 战斗/Par | 升级花费 | 五星 |
|---|--:|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 1 | 50% | fill | 16 | 16 | 24 | 3 | 15/20 | 0.909 | 1915 | — |
| 1 | 70% | fill | 23 | 23 | 30 | 0 | 20/20 | 1.068 | 1935 | — |
| 1 | 85% | fill | 28 | 28 | 36 | 0 | 20/20 | 0.974 | 1905 | ★ |
| 1 | 100% | fill | 33 | 33 | 42 | 0 | 20/20 | 0.944 | 1980 | ★ |
| 1 | 100% | no_upgrade | 33 | 33 | 42 | 0 | 20/20 | 0.963 | 0 | ★ |
| 2 | 50% | fill | 30 | 30 | 39 | 14 | 0/20 | 0.840 | 950 | — |
| 2 | 70% | fill | 41 | 41 | 51 | 0 | 20/20 | 0.946 | 1020 | ★ |
| 2 | 85% | fill | 50 | 50 | 55 | 0 | 20/20 | 1.011 | 1020 | — |
| 2 | 100% | fill | 59 | 59 | 71 | 0 | 20/20 | 0.944 | 1020 | ★ |
| 2 | 100% | no_upgrade | 59 | 59 | 71 | 0 | 20/20 | 0.931 | 0 | ★ |
| 3 | 50% | fill | 26 | 26 | 24 | 16 | 0/20 | 0.354 | 1020 | — |
| 3 | 70% | fill | 36 | 36 | 40 | 11 | 0/20 | 0.833 | 1455 | — |
| 3 | 85% | fill | 44 | 44 | 42 | 14 | 0/20 | 0.929 | 1450 | — |
| 3 | 100% | fill | 52 | 52 | 56 | 0 | 20/20 | 0.943 | 1530 | ★ |
| 3 | 100% | no_upgrade | 52 | 52 | 56 | 1 | 18/20 | 0.923 | 0 | — |
| 4 | 50% | fill | 30 | 30 | 39 | 12 | 0/20 | 0.702 | 1040 | — |
| 4 | 70% | fill | 41 | 41 | 51 | 0 | 20/20 | 0.846 | 1110 | ★ |
| 4 | 85% | fill | 50 | 50 | 55 | 0 | 20/20 | 0.927 | 1035 | ★ |
| 4 | 100% | fill | 59 | 59 | 71 | 0 | 20/20 | 0.943 | 1110 | ★ |
| 4 | 100% | no_upgrade | 59 | 59 | 71 | 0 | 20/20 | 0.938 | 0 | ★ |
| 5 | 50% | fill | 26 | 26 | 24 | 14 | 0/20 | 0.404 | 2840 | — |
| 5 | 70% | fill | 36 | 36 | 40 | 13 | 0/20 | 0.806 | 2845 | — |
| 5 | 85% | fill | 44 | 44 | 42 | 9 | 3/20 | 0.963 | 2850 | — |
| 5 | 100% | fill | 52 | 52 | 56 | 0 | 20/20 | 0.944 | 2920 | ★ |
| 5 | 100% | no_upgrade | 52 | 52 | 56 | 1 | 18/20 | 0.920 | 0 | — |
| 6 | 50% | fill | 29 | 29 | 39 | 13 | 0/20 | 0.704 | 1470 | — |
| 6 | 70% | fill | 41 | 41 | 41 | 11 | 0/20 | 0.979 | 1455 | — |
| 6 | 85% | fill | 49 | 49 | 41 | 14 | 0/20 | 1.046 | 1460 | — |
| 6 | 100% | fill | 58 | 58 | 57 | 0 | 20/20 | 0.943 | 1530 | ★ |
| 6 | 100% | no_upgrade | 58 | 58 | 57 | 1 | 18/20 | 0.934 | 0 | — |
| 7 | 50% | fill | 28 | 28 | 33 | 14 | 0/20 | 0.668 | 1470 | — |
| 7 | 70% | fill | 38 | 38 | 47 | 14 | 0/20 | 0.888 | 1455 | — |
| 7 | 85% | fill | 47 | 47 | 49 | 13 | 0/20 | 1.010 | 1450 | — |
| 7 | 100% | fill | 55 | 55 | 65 | 0 | 20/20 | 0.943 | 1530 | ★ |
| 7 | 100% | no_upgrade | 55 | 55 | 65 | 0 | 20/20 | 0.929 | 0 | ★ |
| 8 | 50% | fill | 30 | 30 | 26 | 15 | 0/20 | 0.521 | 1660 | — |
| 8 | 70% | fill | 41 | 41 | 30 | 14 | 0/20 | 0.588 | 1465 | — |
| 8 | 85% | fill | 50 | 50 | 38 | 13 | 0/20 | 0.904 | 1625 | — |
| 8 | 100% | fill | 59 | 59 | 54 | 0 | 20/20 | 0.943 | 1705 | ★ |
| 8 | 100% | no_upgrade | 59 | 59 | 54 | 1 | 18/20 | 0.939 | 0 | — |
| 9 | 50% | fill | 30 | 30 | 28 | 14 | 0/20 | 0.552 | 1775 | — |
| 9 | 70% | fill | 41 | 41 | 40 | 13 | 0/20 | 0.812 | 1710 | — |
| 9 | 85% | fill | 50 | 50 | 44 | 13 | 0/20 | 0.881 | 1700 | — |
| 9 | 100% | fill | 59 | 59 | 60 | 0 | 20/20 | 0.943 | 1785 | ★ |
| 9 | 100% | no_upgrade | 59 | 59 | 60 | 1 | 18/20 | 0.930 | 0 | — |
| 10 | 50% | fill | 29 | 29 | 35 | 15 | 0/20 | 0.594 | 1460 | — |
| 10 | 70% | fill | 41 | 41 | 39 | 13 | 0/20 | 0.774 | 1705 | — |
| 10 | 85% | fill | 49 | 49 | 41 | 12 | 0/20 | 0.818 | 1620 | — |
| 10 | 100% | fill | 58 | 58 | 57 | 0 | 20/20 | 0.944 | 1710 | ★ |
| 10 | 100% | no_upgrade | 58 | 58 | 57 | 0 | 20/20 | 0.911 | 0 | ★ |
| 11 | 50% | fill | 24 | 24 | 38 | 15 | 0/20 | 0.493 | 1790 | — |
| 11 | 70% | fill | 34 | 34 | 40 | 13 | 0/20 | 0.864 | 2250 | — |
| 11 | 85% | fill | 41 | 41 | 54 | 1 | 18/20 | 0.919 | 2230 | — |
| 11 | 100% | fill | 48 | 48 | 68 | 0 | 20/20 | 0.944 | 2295 | ★ |
| 11 | 100% | no_upgrade | 48 | 48 | 68 | 1 | 18/20 | 0.939 | 0 | — |
| 12 | 50% | fill | 24 | 24 | 38 | 13 | 0/20 | 0.454 | 1430 | — |
| 12 | 70% | fill | 34 | 34 | 40 | 6 | 7/20 | 0.786 | 2160 | — |
| 12 | 85% | fill | 41 | 41 | 54 | 1 | 16/20 | 0.957 | 2130 | — |
| 12 | 100% | fill | 48 | 48 | 68 | 0 | 20/20 | 0.943 | 2215 | ★ |
| 12 | 100% | no_upgrade | 48 | 48 | 68 | 0 | 20/20 | 0.933 | 0 | ★ |
| 13 | 50% | fill | 30 | 30 | 39 | 13 | 0/20 | 0.950 | 1800 | — |
| 13 | 70% | fill | 41 | 41 | 51 | 0 | 20/20 | 0.966 | 1790 | ★ |
| 13 | 85% | fill | 50 | 50 | 55 | 0 | 20/20 | 0.804 | 1790 | ★ |
| 13 | 100% | fill | 59 | 59 | 71 | 0 | 20/20 | 0.943 | 1870 | ★ |
| 13 | 100% | no_upgrade | 59 | 59 | 71 | 0 | 20/20 | 0.940 | 0 | ★ |
| 14 | 50% | fill | 30 | 30 | 40 | 13 | 0/20 | 0.705 | 1890 | — |
| 14 | 70% | fill | 41 | 41 | 40 | 15 | 0/20 | 0.812 | 1880 | — |
| 14 | 85% | fill | 50 | 50 | 40 | 14 | 0/20 | 0.843 | 1890 | — |
| 14 | 100% | fill | 59 | 59 | 56 | 0 | 20/20 | 0.944 | 1960 | ★ |
| 14 | 100% | no_upgrade | 59 | 59 | 56 | 1 | 16/20 | 0.925 | 0 | — |
| 15 | 50% | fill | 30 | 30 | 39 | 13 | 0/20 | 0.797 | 1990 | — |
| 15 | 70% | fill | 42 | 42 | 39 | 14 | 0/20 | 0.889 | 1980 | — |
| 15 | 85% | fill | 51 | 51 | 39 | 13 | 0/20 | 0.853 | 1990 | — |
| 15 | 100% | fill | 60 | 60 | 55 | 0 | 20/20 | 0.944 | 2045 | ★ |
| 15 | 100% | no_upgrade | 60 | 60 | 55 | 0 | 20/20 | 0.930 | 0 | ★ |
| 16 | 50% | fill | 30 | 30 | 39 | 13 | 0/20 | 0.856 | 2080 | — |
| 16 | 70% | fill | 42 | 42 | 39 | 15 | 0/20 | 0.887 | 2065 | — |
| 16 | 85% | fill | 51 | 51 | 39 | 13 | 0/20 | 0.850 | 2080 | — |
| 16 | 100% | fill | 60 | 60 | 55 | 0 | 20/20 | 0.943 | 2135 | ★ |
| 16 | 100% | no_upgrade | 60 | 60 | 55 | 0 | 20/20 | 0.930 | 0 | ★ |
| 17 | 50% | fill | 24 | 24 | 24 | 14 | 0/20 | 0.372 | 1610 | — |
| 17 | 70% | fill | 34 | 34 | 40 | 9 | 4/20 | 0.870 | 2760 | — |
| 17 | 85% | fill | 42 | 42 | 42 | 14 | 0/20 | 0.944 | 2760 | — |
| 17 | 100% | fill | 49 | 49 | 56 | 0 | 20/20 | 0.943 | 2820 | ★ |
| 17 | 100% | no_upgrade | 49 | 49 | 56 | 1 | 16/20 | 0.918 | 0 | — |
| 18 | 50% | fill | 28 | 28 | 39 | 14 | 0/20 | 0.821 | 2355 | — |
| 18 | 70% | fill | 39 | 39 | 53 | 1 | 16/20 | 1.009 | 2310 | — |
| 18 | 85% | fill | 48 | 48 | 63 | 0 | 20/20 | 0.992 | 2305 | ★ |
| 18 | 100% | fill | 56 | 56 | 71 | 0 | 20/20 | 0.944 | 2385 | ★ |
| 18 | 100% | no_upgrade | 56 | 56 | 71 | 0 | 20/20 | 0.932 | 0 | ★ |
| 19 | 50% | fill | 28 | 28 | 29 | 15 | 0/20 | 0.559 | 1830 | — |
| 19 | 70% | fill | 40 | 40 | 45 | 14 | 0/20 | 1.050 | 2415 | — |
| 19 | 85% | fill | 48 | 48 | 45 | 14 | 0/20 | 1.030 | 2395 | — |
| 19 | 100% | fill | 57 | 57 | 61 | 0 | 20/20 | 0.943 | 2475 | ★ |
| 19 | 100% | no_upgrade | 57 | 57 | 61 | 0 | 20/20 | 0.929 | 0 | ★ |
| 20 | 50% | fill | 29 | 29 | 39 | 14 | 0/20 | 0.830 | 2465 | — |
| 20 | 70% | fill | 41 | 41 | 51 | 0 | 20/20 | 0.858 | 2400 | ★ |
| 20 | 85% | fill | 49 | 49 | 55 | 0 | 20/20 | 0.882 | 2400 | ★ |
| 20 | 100% | fill | 58 | 58 | 71 | 0 | 20/20 | 0.943 | 2475 | ★ |
| 20 | 100% | no_upgrade | 58 | 58 | 71 | 0 | 20/20 | 0.934 | 0 | ★ |
| 21 | 50% | fill | 28 | 28 | 43 | 15 | 0/20 | 0.998 | 2625 | — |
| 21 | 70% | fill | 39 | 39 | 55 | 1 | 16/20 | 0.957 | 2590 | — |
| 21 | 85% | fill | 48 | 48 | 59 | 1 | 16/20 | 0.937 | 2565 | — |
| 21 | 100% | fill | 56 | 56 | 75 | 0 | 20/20 | 0.943 | 2645 | ★ |
| 21 | 100% | no_upgrade | 56 | 56 | 75 | 0 | 20/20 | 0.942 | 0 | ★ |
| 22 | 50% | fill | 28 | 28 | 35 | 14 | 0/20 | 0.867 | 2735 | — |
| 22 | 70% | fill | 39 | 39 | 47 | 7 | 6/20 | 1.031 | 2690 | — |
| 22 | 85% | fill | 48 | 48 | 51 | 0 | 20/20 | 1.048 | 2665 | — |
| 22 | 100% | fill | 56 | 56 | 65 | 0 | 20/20 | 0.943 | 2735 | ★ |
| 22 | 100% | no_upgrade | 56 | 56 | 65 | 0 | 20/20 | 0.946 | 0 | ★ |
| 23 | 50% | fill | 30 | 30 | 27 | 20 | 0/20 | 0.454 | 1500 | — |
| 23 | 70% | fill | 41 | 41 | 37 | 14 | 0/20 | 0.873 | 2655 | — |
| 23 | 85% | fill | 50 | 50 | 43 | 0 | 20/20 | 0.852 | 2675 | ★ |
| 23 | 100% | fill | 59 | 59 | 59 | 0 | 20/20 | 0.944 | 2685 | ★ |
| 23 | 100% | no_upgrade | 59 | 59 | 59 | 0 | 20/20 | 0.953 | 0 | ★ |
| 24 | 50% | fill | 30 | 30 | 38 | 15 | 0/20 | 0.776 | 2970 | — |
| 24 | 70% | fill | 41 | 41 | 38 | 7 | 8/20 | 0.802 | 2960 | — |
| 24 | 85% | fill | 50 | 50 | 40 | 17 | 0/20 | 0.896 | 2975 | — |
| 24 | 100% | fill | 59 | 59 | 54 | 0 | 20/20 | 0.944 | 3010 | ★ |
| 24 | 100% | no_upgrade | 59 | 59 | 54 | 1 | 16/20 | 0.932 | 0 | — |
| 25 | 50% | fill | 29 | 29 | 38 | 16 | 0/20 | 0.846 | 2915 | — |
| 25 | 70% | fill | 41 | 41 | 48 | 0 | 20/20 | 0.871 | 2860 | ★ |
| 25 | 85% | fill | 49 | 49 | 48 | 5 | 9/20 | 0.927 | 2935 | — |
| 25 | 100% | fill | 58 | 58 | 54 | 0 | 20/20 | 0.943 | 2935 | ★ |
| 25 | 100% | no_upgrade | 58 | 58 | 54 | 3 | 12/20 | 0.923 | 0 | — |
| 26 | 50% | fill | 25 | 25 | 24 | 15 | 0/20 | 0.556 | 3450 | — |
| 26 | 70% | fill | 35 | 35 | 40 | 0 | 20/20 | 0.922 | 4115 | ★ |
| 26 | 85% | fill | 42 | 42 | 42 | 0 | 20/20 | 0.972 | 4150 | ★ |
| 26 | 100% | fill | 50 | 50 | 56 | 0 | 20/20 | 0.944 | 4170 | ★ |
| 26 | 100% | no_upgrade | 50 | 50 | 56 | 0 | 20/20 | 0.961 | 0 | ★ |
| 27 | 50% | fill | 30 | 30 | 44 | 16 | 0/20 | 0.959 | 2970 | — |
| 27 | 70% | fill | 42 | 42 | 50 | 3 | 12/20 | 0.951 | 2950 | — |
| 27 | 85% | fill | 51 | 51 | 50 | 1 | 16/20 | 1.031 | 3015 | — |
| 27 | 100% | fill | 60 | 60 | 60 | 0 | 20/20 | 0.944 | 3015 | ★ |
| 27 | 100% | no_upgrade | 60 | 60 | 60 | 1 | 16/20 | 0.953 | 0 | — |
| 28 | 50% | fill | 28 | 28 | 40 | 15 | 0/20 | 0.846 | 3165 | — |
| 28 | 70% | fill | 40 | 40 | 52 | 0 | 20/20 | 0.958 | 3120 | ★ |
| 28 | 85% | fill | 48 | 48 | 56 | 0 | 20/20 | 0.935 | 3105 | ★ |
| 28 | 100% | fill | 57 | 57 | 70 | 0 | 20/20 | 0.943 | 3175 | ★ |
| 28 | 100% | no_upgrade | 57 | 57 | 70 | 0 | 20/20 | 0.952 | 0 | ★ |
| 29 | 50% | fill | 29 | 29 | 38 | 15 | 0/20 | 0.841 | 3270 | — |
| 29 | 70% | fill | 41 | 41 | 38 | 15 | 0/20 | 0.880 | 3275 | — |
| 29 | 85% | fill | 49 | 49 | 38 | 15 | 0/20 | 0.704 | 2415 | — |
| 29 | 100% | fill | 58 | 58 | 52 | 0 | 20/20 | 0.944 | 3275 | ★ |
| 29 | 100% | no_upgrade | 58 | 58 | 52 | 1 | 16/20 | 0.925 | 0 | — |
| 30 | 50% | fill | 29 | 29 | 41 | 17 | 0/20 | 0.907 | 3260 | — |
| 30 | 70% | fill | 41 | 41 | 53 | 0 | 20/20 | 1.019 | 3210 | — |
| 30 | 85% | fill | 49 | 49 | 57 | 0 | 20/20 | 0.897 | 3200 | ★ |
| 30 | 100% | fill | 58 | 58 | 57 | 0 | 20/20 | 0.943 | 3280 | ★ |
| 30 | 100% | no_upgrade | 58 | 58 | 57 | 4 | 10/20 | 0.963 | 0 | — |

## 闸门汇总

| 关 | G1 半迷宫必败 | G2 七成必败 | G3 八成半不五星 | G4 满迷宫五星 | G5 不升级不五星 | 结论 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| 1 | — | — | ✗ | ✓ | — | FAIL G3 |
| 2 | — | — | ✗ | ✓ | — | FAIL G3 |
| 3 | — | — | ✓ | ✓ | — | PASS  |
| 4 | — | — | ✗ | ✓ | — | FAIL G3 |
| 5 | — | — | ✓ | ✓ | — | PASS  |
| 6 | ✓ | ✓ | ✓ | ✓ | — | PASS  |
| 7 | ✓ | ✓ | ✓ | ✓ | — | PASS  |
| 8 | ✓ | ✓ | ✓ | ✓ | — | PASS  |
| 9 | ✓ | ✓ | ✓ | ✓ | — | PASS  |
| 10 | ✓ | ✓ | ✓ | ✓ | — | PASS  |
| 11 | ✓ | ✓ | ✓ | ✓ | — | PASS  |
| 12 | ✓ | ✓ | ✓ | ✓ | — | PASS  |
| 13 | ✓ | ✗ | ✗ | ✓ | — | FAIL G2,G3 |
| 14 | ✓ | ✓ | ✓ | ✓ | — | PASS  |
| 15 | ✓ | ✓ | ✓ | ✓ | ✗ | FAIL G5 |
| 16 | ✓ | ✓ | ✓ | ✓ | ✗ | FAIL G5 |
| 17 | ✓ | ✓ | ✓ | ✓ | ✓ | PASS  |
| 18 | ✓ | ✓ | ✗ | ✓ | ✗ | FAIL G3,G5 |
| 19 | ✓ | ✓ | ✓ | ✓ | ✗ | FAIL G5 |
| 20 | ✓ | ✗ | ✗ | ✓ | ✗ | FAIL G2,G3,G5 |
| 21 | ✓ | ✓ | ✓ | ✓ | ✗ | FAIL G5 |
| 22 | ✓ | ✓ | ✗ | ✓ | ✗ | FAIL G3,G5 |
| 23 | ✓ | ✓ | ✗ | ✓ | ✗ | FAIL G3,G5 |
| 24 | ✓ | ✓ | ✓ | ✓ | ✓ | PASS  |
| 25 | ✓ | ✗ | ✓ | ✓ | ✓ | FAIL G2 |
| 26 | ✓ | ✗ | ✗ | ✓ | ✗ | FAIL G2,G3,G5 |
| 27 | ✓ | ✓ | ✓ | ✓ | ✓ | PASS  |
| 28 | ✓ | ✗ | ✗ | ✓ | ✗ | FAIL G2,G3,G5 |
| 29 | ✓ | ✓ | ✓ | ✓ | ✓ | PASS  |
| 30 | ✓ | ✗ | ✗ | ✓ | ✓ | FAIL G2,G3 |

## 明细

- L1 G1: 50% maze (16 towers): leaked=3 hp=15
- L1 G2: 70% maze (23 towers): leaked=0 hp=20
- L1 G3: 85% maze (28 towers): structural_clear=True leaked=0
- L1 G4: full maze (33/33): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L1 G5: full maze, no upgrades: structural_clear=True leaked=0
- L2 G1: 50% maze (30 towers): leaked=14 hp=0
- L2 G2: 70% maze (41 towers): leaked=0 hp=20
- L2 G3: 85% maze (50 towers): structural_clear=True leaked=0
- L2 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L2 G5: full maze, no upgrades: structural_clear=True leaked=0
- L3 G1: 50% maze (26 towers): leaked=16 hp=0
- L3 G2: 70% maze (36 towers): leaked=11 hp=0
- L3 G3: 85% maze (44 towers): structural_clear=False leaked=14
- L3 G4: full maze (52/52): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L3 G5: full maze, no upgrades: structural_clear=False leaked=1
- L4 G1: 50% maze (30 towers): leaked=12 hp=0
- L4 G2: 70% maze (41 towers): leaked=0 hp=20
- L4 G3: 85% maze (50 towers): structural_clear=True leaked=0
- L4 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L4 G5: full maze, no upgrades: structural_clear=True leaked=0
- L5 G1: 50% maze (26 towers): leaked=14 hp=0
- L5 G2: 70% maze (36 towers): leaked=13 hp=0
- L5 G3: 85% maze (44 towers): structural_clear=False leaked=9
- L5 G4: full maze (52/52): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L5 G5: full maze, no upgrades: structural_clear=False leaked=1
- L6 G1: 50% maze (29 towers): leaked=13 hp=0
- L6 G2: 70% maze (41 towers): leaked=11 hp=0
- L6 G3: 85% maze (49 towers): structural_clear=False leaked=14
- L6 G4: full maze (58/58): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L6 G5: full maze, no upgrades: structural_clear=False leaked=1
- L7 G1: 50% maze (28 towers): leaked=14 hp=0
- L7 G2: 70% maze (38 towers): leaked=14 hp=0
- L7 G3: 85% maze (47 towers): structural_clear=False leaked=13
- L7 G4: full maze (55/55): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L7 G5: full maze, no upgrades: structural_clear=True leaked=0
- L8 G1: 50% maze (30 towers): leaked=15 hp=0
- L8 G2: 70% maze (41 towers): leaked=14 hp=0
- L8 G3: 85% maze (50 towers): structural_clear=False leaked=13
- L8 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L8 G5: full maze, no upgrades: structural_clear=False leaked=1
- L9 G1: 50% maze (30 towers): leaked=14 hp=0
- L9 G2: 70% maze (41 towers): leaked=13 hp=0
- L9 G3: 85% maze (50 towers): structural_clear=False leaked=13
- L9 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L9 G5: full maze, no upgrades: structural_clear=False leaked=1
- L10 G1: 50% maze (29 towers): leaked=15 hp=0
- L10 G2: 70% maze (41 towers): leaked=13 hp=0
- L10 G3: 85% maze (49 towers): structural_clear=False leaked=12
- L10 G4: full maze (58/58): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L10 G5: full maze, no upgrades: structural_clear=True leaked=0
- L11 G1: 50% maze (24 towers): leaked=15 hp=0
- L11 G2: 70% maze (34 towers): leaked=13 hp=0
- L11 G3: 85% maze (41 towers): structural_clear=False leaked=1
- L11 G4: full maze (48/48): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L11 G5: full maze, no upgrades: structural_clear=False leaked=1
- L12 G1: 50% maze (24 towers): leaked=13 hp=0
- L12 G2: 70% maze (34 towers): leaked=6 hp=7
- L12 G3: 85% maze (41 towers): structural_clear=False leaked=1
- L12 G4: full maze (48/48): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L12 G5: full maze, no upgrades: structural_clear=True leaked=0
- L13 G1: 50% maze (30 towers): leaked=13 hp=0
- L13 G2: 70% maze (41 towers): leaked=0 hp=20
- L13 G3: 85% maze (50 towers): structural_clear=True leaked=0
- L13 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L13 G5: full maze, no upgrades: structural_clear=True leaked=0
- L14 G1: 50% maze (30 towers): leaked=13 hp=0
- L14 G2: 70% maze (41 towers): leaked=15 hp=0
- L14 G3: 85% maze (50 towers): structural_clear=False leaked=14
- L14 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L14 G5: full maze, no upgrades: structural_clear=False leaked=1
- L15 G1: 50% maze (30 towers): leaked=13 hp=0
- L15 G2: 70% maze (42 towers): leaked=14 hp=0
- L15 G3: 85% maze (51 towers): structural_clear=False leaked=13
- L15 G4: full maze (60/60): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L15 G5: full maze, no upgrades: structural_clear=True leaked=0
- L16 G1: 50% maze (30 towers): leaked=13 hp=0
- L16 G2: 70% maze (42 towers): leaked=15 hp=0
- L16 G3: 85% maze (51 towers): structural_clear=False leaked=13
- L16 G4: full maze (60/60): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L16 G5: full maze, no upgrades: structural_clear=True leaked=0
- L17 G1: 50% maze (24 towers): leaked=14 hp=0
- L17 G2: 70% maze (34 towers): leaked=9 hp=4
- L17 G3: 85% maze (42 towers): structural_clear=False leaked=14
- L17 G4: full maze (49/49): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L17 G5: full maze, no upgrades: structural_clear=False leaked=1
- L18 G1: 50% maze (28 towers): leaked=14 hp=0
- L18 G2: 70% maze (39 towers): leaked=1 hp=16
- L18 G3: 85% maze (48 towers): structural_clear=True leaked=0
- L18 G4: full maze (56/56): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L18 G5: full maze, no upgrades: structural_clear=True leaked=0
- L19 G1: 50% maze (28 towers): leaked=15 hp=0
- L19 G2: 70% maze (40 towers): leaked=14 hp=0
- L19 G3: 85% maze (48 towers): structural_clear=False leaked=14
- L19 G4: full maze (57/57): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L19 G5: full maze, no upgrades: structural_clear=True leaked=0
- L20 G1: 50% maze (29 towers): leaked=14 hp=0
- L20 G2: 70% maze (41 towers): leaked=0 hp=20
- L20 G3: 85% maze (49 towers): structural_clear=True leaked=0
- L20 G4: full maze (58/58): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L20 G5: full maze, no upgrades: structural_clear=True leaked=0
- L21 G1: 50% maze (28 towers): leaked=15 hp=0
- L21 G2: 70% maze (39 towers): leaked=1 hp=16
- L21 G3: 85% maze (48 towers): structural_clear=False leaked=1
- L21 G4: full maze (56/56): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L21 G5: full maze, no upgrades: structural_clear=True leaked=0
- L22 G1: 50% maze (28 towers): leaked=14 hp=0
- L22 G2: 70% maze (39 towers): leaked=7 hp=6
- L22 G3: 85% maze (48 towers): structural_clear=True leaked=0
- L22 G4: full maze (56/56): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L22 G5: full maze, no upgrades: structural_clear=True leaked=0
- L23 G1: 50% maze (30 towers): leaked=20 hp=0
- L23 G2: 70% maze (41 towers): leaked=14 hp=0
- L23 G3: 85% maze (50 towers): structural_clear=True leaked=0
- L23 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L23 G5: full maze, no upgrades: structural_clear=True leaked=0
- L24 G1: 50% maze (30 towers): leaked=15 hp=0
- L24 G2: 70% maze (41 towers): leaked=7 hp=8
- L24 G3: 85% maze (50 towers): structural_clear=False leaked=17
- L24 G4: full maze (59/59): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L24 G5: full maze, no upgrades: structural_clear=False leaked=1
- L25 G1: 50% maze (29 towers): leaked=16 hp=0
- L25 G2: 70% maze (41 towers): leaked=0 hp=20
- L25 G3: 85% maze (49 towers): structural_clear=False leaked=5
- L25 G4: full maze (58/58): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L25 G5: full maze, no upgrades: structural_clear=False leaked=3
- L26 G1: 50% maze (25 towers): leaked=15 hp=0
- L26 G2: 70% maze (35 towers): leaked=0 hp=20
- L26 G3: 85% maze (42 towers): structural_clear=True leaked=0
- L26 G4: full maze (50/50): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L26 G5: full maze, no upgrades: structural_clear=True leaked=0
- L27 G1: 50% maze (30 towers): leaked=16 hp=0
- L27 G2: 70% maze (42 towers): leaked=3 hp=12
- L27 G3: 85% maze (51 towers): structural_clear=False leaked=1
- L27 G4: full maze (60/60): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L27 G5: full maze, no upgrades: structural_clear=False leaked=1
- L28 G1: 50% maze (28 towers): leaked=15 hp=0
- L28 G2: 70% maze (40 towers): leaked=0 hp=20
- L28 G3: 85% maze (48 towers): structural_clear=True leaked=0
- L28 G4: full maze (57/57): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L28 G5: full maze, no upgrades: structural_clear=True leaked=0
- L29 G1: 50% maze (29 towers): leaked=15 hp=0
- L29 G2: 70% maze (41 towers): leaked=15 hp=0
- L29 G3: 85% maze (49 towers): structural_clear=False leaked=15
- L29 G4: full maze (58/58): clear=True policy=True budget=True time=True ratio=0.944 leaked=0
- L29 G5: full maze, no upgrades: structural_clear=False leaked=1
- L30 G1: 50% maze (29 towers): leaked=17 hp=0
- L30 G2: 70% maze (41 towers): leaked=0 hp=20
- L30 G3: 85% maze (49 towers): structural_clear=True leaked=0
- L30 G4: full maze (58/58): clear=True policy=True budget=True time=True ratio=0.943 leaked=0
- L30 G5: full maze, no upgrades: structural_clear=False leaked=4
