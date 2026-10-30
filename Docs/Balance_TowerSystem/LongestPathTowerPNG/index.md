# 最长路径布局图（按手绘形态：标准蛇形 · 间距 2）

## 形态

- 竖手指蛇形，间距 2 格；路径占偶数列、塔列夹在中间
- S 出发沿所在列下行/上行，到底后横移一格，再反向折回
- 路径避开地图障碍格

## 口径

| 项 | 定义 |
|---|---|
| 路径 | 敌人实际最短路径步数 |
| 塔位 | 路径以外、非障碍、距路径 ≤2 格（塔打得到） |
| 死角 | 路径以外、非障碍、距路径 >2 格（塔打不到） |

| 关卡 | PNG | 路径 | 参考图 | 一致 | 塔位 | 死角 | 塔位(含死角) |
|---:|---|---:|---:|:---:|---:|---:|---:|
| L01 | [PNG](L01_longest_path_towers.png) | **42** | 42 | ✓ | 46 | 2 | 48 |
| L02 | [PNG](L02_longest_path_towers.png) | **71** | 71 | ✓ | 70 | 2 | 72 |
| L03 | [PNG](L03_longest_path_towers.png) | **56** | 56 | ✓ | 84 | 12 | 96 |
| L04 | [PNG](L04_longest_path_towers.png) | **71** | 71 | ✓ | 70 | 2 | 72 |
| L05 | [PNG](L05_longest_path_towers.png) | **56** | 56 | ✓ | 84 | 12 | 96 |
| L06 | [PNG](L06_longest_path_towers.png) | **57** | 57 | ✓ | 77 | 5 | 82 |
| L07 | [PNG](L07_longest_path_towers.png) | **65** | 65 | ✓ | 69 | 5 | 74 |
| L08 | [PNG](L08_longest_path_towers.png) | **54** | 54 | ✓ | 74 | 11 | 85 |
| L09 | [PNG](L09_longest_path_towers.png) | **60** | 60 | ✓ | 71 | 8 | 79 |
| L10 | [PNG](L10_longest_path_towers.png) | **57** | 57 | ✓ | 77 | 5 | 82 |
| L11 | [PNG](L11_longest_path_towers.png) | **68** | 68 | ✓ | 75 | 0 | 75 |
| L12 | [PNG](L12_longest_path_towers.png) | **68** | 68 | ✓ | 75 | 0 | 75 |
| L13 | [PNG](L13_longest_path_towers.png) | **71** | 71 | ✓ | 66 | 6 | 72 |
| L14 | [PNG](L14_longest_path_towers.png) | **56** | 56 | ✓ | 84 | 9 | 93 |
| L15 | [PNG](L15_longest_path_towers.png) | **55** | 55 | ✓ | 77 | 8 | 85 |
| L16 | [PNG](L16_longest_path_towers.png) | **55** | 55 | ✓ | 77 | 8 | 85 |
| L17 | [PNG](L17_longest_path_towers.png) | **56** | 56 | ✓ | 81 | 12 | 93 |
| L18 | [PNG](L18_longest_path_towers.png) | **71** | 71 | ✓ | 67 | 2 | 69 |
| L19 | [PNG](L19_longest_path_towers.png) | **61** | 61 | ✓ | 70 | 9 | 79 |
| L20 | [PNG](L20_longest_path_towers.png) | **71** | 71 | ✓ | 68 | 2 | 70 |
| L21 | [PNG](L21_longest_path_towers.png) | **75** | 75 | ✓ | 72 | 0 | 72 |
| L22 | [PNG](L22_longest_path_towers.png) | **65** | 65 | ✓ | 74 | 9 | 83 |
| L23 | [PNG](L23_longest_path_towers.png) | **59** | 61 | 差-2 | 77 | 12 | 89 |
| L24 | [PNG](L24_longest_path_towers.png) | **54** | 54 | ✓ | 82 | 11 | 93 |
| L25 | [PNG](L25_longest_path_towers.png) | **54** | 54 | ✓ | 84 | 10 | 94 |
| L26 | [PNG](L26_longest_path_towers.png) | **56** | 56 | ✓ | 80 | 11 | 91 |
| L27 | [PNG](L27_longest_path_towers.png) | **60** | 62 | 差-2 | 81 | 7 | 88 |
| L28 | [PNG](L28_longest_path_towers.png) | **70** | 70 | ✓ | 74 | 4 | 78 |
| L29 | [PNG](L29_longest_path_towers.png) | **52** | 52 | ✓ | 84 | 12 | 96 |
| L30 | [PNG](L30_longest_path_towers.png) | **57** | 57 | ✓ | 70 | 21 | 91 |

**28/30 关与手绘截图完全一致**，2 关差 2 步（L23、L27，手指开口方向不同）。