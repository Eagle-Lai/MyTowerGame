# FillGate 闸门工具使用说明

目的：用离线模拟器证明"必须把参考迷宫修完才能五星"，并给出可复跑的收敛流程。

## 核心概念

- **C**：`capacity(cells)['capacity'] = B − q`，本地图在保留一条合法通路时最多能建的塔数。
- **参考迷宫（snake_walls）**：确定性生成的蛇形墙位（支持横向/竖向/反向 S→E，逐格做连通性修复，再补盲覆盖飞行直线与折返缺口）。它**不写进地图数据**，只作为"塔数标尺"。
- **档位**：`fraction` 是"参考迷宫建成比例"，不是地图占有率。1.0 = 整条迷宫修完。

## 命令

```bash
# 结构体检（不跑仿真）
python .workbuddy/tools/balance_fill_gate.py preflight --skip-export --out <dir>

# 跑闸门：30 关 × 5 档（0.5/0.7/0.85/1.0 + 不升级）
python .workbuddy/tools/balance_fill_gate.py run --levels all --ladder gate --workers 7 --out <dir>

# 只重跑上一轮失败的关（resume 用 combatBasisHash 判新旧，Par 标定后仍然有效）
python .workbuddy/tools/balance_fill_gate.py run --levels all --only-failing <prevRun> --out <newRun>

# Par 写入后重算 ratio/五星，不必重跑仿真
python .workbuddy/tools/balance_fill_gate.py rescore --run <dir> --recipe Luban/BalanceDesign/balance_design.json

# 看紧凑表格
python .workbuddy/tools/balance_converge.py report --run <dir>

# 调某几关的 EHP（自动做跨关单调修复）
python .workbuddy/tools/balance_converge.py adjust --out <roundDir>/recipe.json \
  --mult "6:0.95,18:0.93" --write

# Par 标定（数值冻结后才跑；内部会断言 30/30 parCalibrationCurrent）
python .workbuddy/tools/balance_par.py calibrate --run <dir> --out <newRecipe.json> --write
```

## 闸门定义

| 闸门 | 档位 | 通过条件 |
|---|---|---|
| G1 | 0.50 | 失败：漏≥6 或 HP≤10 |
| G2 | 0.70 | 失败：漏≥4 或 HP≤16 |
| G3 | 0.85 | 不得结构五星（漏 0 + 满血 + 全杀） |
| G4 | **1.00** | 结构五星 + 建满目标塔 + 升级≥0.25×满迷宫成本 + 战斗/Par∈[0.90,1.05] |
| G5 | 1.00 禁升级 | 不得结构五星 |

L1–L5 豁免 G1/G2，L1–L14 豁免 G5。

## 两阶段升级预算

低档位容易"省下建塔钱全砸升级"，看起来比满迷宫还强。`run` 默认
`--upgrade-budget uniform`：先跑 1.0 档记录实际升级花费，低档位用这个数作上限。
`--upgrade-budget none` 可关闭（旧行为）。

## 注意

- `seed` **不参与**模拟（只写进结果），不要用它做随机性论证。
- 每次改任何数值都会改变 `combatBasisHash`，旧的 `gate-row.json` 会被判为陈旧并重跑；这是预期行为。
- 仿真单关约 40–60 秒（25 波、100ms 步长），30 关 × 5 档约 40 分钟（7 并行）。
