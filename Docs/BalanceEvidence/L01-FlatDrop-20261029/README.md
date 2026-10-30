# L01 击杀掉落改为「小数 + 累加进位」—— 2026-10-29

## 需求（用户原话）

> 「请调整当前游戏的第一关关卡的经济数值……按照当前关卡的金币基准，金币掉落可以是 float 值，
> 累计到了 1 以上后，在增加。」

## 问题定位（改前）

用户试玩 L01 到 W5 起就「击杀不掉金币」。运行时日志实证：

```
[Player] 关卡初始化：金币 100，生命 10
[Flow] 本局结束：失败\n[Player] 金币=23 生命=0/10 击杀=3517 漏怪=10
```

- 表侧：L01 的 100 个 W5-25 变体里 **92 个 reward=0**，按出场次数算 **8868/9820 = 90.3% 零掉落**；
  W10-W23、W25 整波击杀金 = 0，唯一大头是 W24 一波 1932 金（局部搜索把预算全塞给了一波）。
- 代码侧：`EnemyConfig.Reward` 当天已改为「如实返回 0、不回退 `Global.DefaultReward`」，
  `PlayerDataManager.AddGold(0)` 直接 early-return（连飘字都不弹）→ 表现就是「杀了完全没反应」。
- L02-L30 不受影响：30 关里只有 L01 存在 0 值变体，L05 每只 1-4 金、2675 只全程有掉落。

## 落地方案

**总量不动、单价变小数、每只都给、满 1 进账。**

| 项 | 改前 | 改后 |
|---|---|---|
| 变体 reward 类型 | int | **float**（`Luban/Config/Datas/EnemyData.xlsx` 的 `reward` 列 `##type int → float`，该基表定义 TBEnemyData 全表） |
| 单价 | 0（93%）或 1~7（少数），W24 独吞 1932 | 按角色：normal **0.20** / swarm **0.16** / medium **0.32** / air **0.36** / heavy **0.52** / elite **1.40** |
| W5-25 击杀金 | 2448（分布畸形） | **2448.00（精确相等，分布平滑）** |
| W1-4 击杀金 | 294 | 294（不变） |
| 整关总收入 | 3667 = 100 + 2742 + 825 | **3667（一分未增）** |
| 零掉落出场次数 | 8868 | **0** |
| W24 击杀金 | 1932 | 175.20 |

逐波对比（击杀金）：

```
W1  62→62.00    W2  74→74.00    W3  74→74.00    W4  84→84.00
W5  60→47.68    W6  80→53.28    W10  0→76.00    W15  0→118.40
W20  0→150.24   W24 1932→175.20 W25  0→200.64
合计 2742 → 2742.00
```

## 代码改动（4 个文件）

| 文件 | 改动 |
|---|---|
| `Assets/Scripts/Core/Manager/PlayerDataManager.cs` | 新增 `float _goldCarry` 取整余数；`AddGold(int)` → **`AddGold(float)`**：累加后 `Floor(carry)` 才真正加 Gold 并发 `GoldChangeEvent`；`OnInit/InitFromLevel/RestoreState` 清零余数 |
| `Assets/Scripts/Data/EnemyConfig.cs` | `Reward`：`int` → **`float`**，不再回退 `Global.DefaultReward` |
| `Assets/Scripts/Enemy/BaseEnemy.cs` | `Die()` 里 `float reward`，`EnemyKilledEvent` 载荷 `int` → **`float`** |
| `Assets/Scripts/Game/GameFlowManager.cs`、`Assets/Scripts/Audio/AudioRuntime.cs`、`Assets/Scripts/Data/LevelRating.cs` | 跟随事件载荷改 `float`；`WaveRunMetrics.killGold` `int` → `float`（只用于报表，不参与评级） |
| `Assets/Scripts/UI/MonsterCodexView.cs` | 图鉴金币显示格式 `"0"` → `"0.##"`（否则 0.2 会显示成 0） |

设计取舍：
- **零头不落存档**：`_goldCarry < 1`，跨局沿用会让同一关的复现收入随上一局残留漂移，故每次 Init/Restore 清零。
- **退款不受影响**：塔的退款/出售走整数值，加进 carry 后不会丢金（整数部分立即结算）。
- **表结构只改 1 个单元格**：TBEnemyData 的定义取自基表 `Datas/EnemyData.xlsx`，30 个分表的表头仍写 int、值仍是整数，实测 Luban 可正常导出（若只改 L01 分表头仍会报 `int` 解析失败，已验证）。

## 验证

| 项 | 结果 |
|---|---|
| Luban 导出 | 导出×2 成功（每次都会删 `Assets/Gen/FTProject.Gen.asmdef`，已两次 `git checkout` 恢复） |
| `Reward` 生成类型 | `Assets/Gen/EnemyData.cs` → `public float Reward` |
| 运行时哈希 | `runtimeContentHash` = **2157cb7d7de70550ba5f08f6e01f5421322a371edcfbb15086c3c9d5df137e14**（30 关重封；Python 复算与 C# 算法逐位一致，改前先用旧值 c544b196… 对过） |
| Play Mode 自检 | `[Rating] Runtime configuration SHA256 verified: 2157cb7d…`，控制台 0 error，`scriptCompilationFailed=false` |
| 运行时断言（execute_code） | `reward(5000230)=0.2`、`reward(5000244)=1.4`；`5×0.20 → 金币 100→101`；`7×0.16(=1.12) → 100→101` |
| 表侧复核 | W5-25 击杀金 2448.00、零掉落 0 次；W1-4 = 294 |

## 已知影响 / 未做

- **L01 仍是「极限压力基准」**：W5 就是 220 只 / 9808 EHP，开局约 500 金，仍然打不过。
  本次只修「击杀反馈 + 经济分布」，没有动数量/血量/波奖，也没有做可通关性重平衡。
- 真机（Android）未验，仅编辑器 Play Mode + 配置链路验证。
- W25 出怪间隔 215ms、initialHp=10、initialGold=100 均未改。

## 回滚

1. 表：`Luban/Config/Datas/EnemyData.xlsx` 的 reward 列 `##type float → int`；
   `Levels/L01/EnemyData.xlsx` 的 100 个变体 reward 恢复为整数（备份见本次会话临时目录，或按
   `l01_kill_gold_20.py` 重放）；`Levels/L01/LevelRating.xlsx` 的 planHash/balanceRevision 复位。
2. 代码：`git checkout -- Assets/Scripts/Core/Manager/PlayerDataManager.cs Assets/Scripts/Data/EnemyConfig.cs
   Assets/Scripts/Enemy/BaseEnemy.cs Assets/Scripts/Game/GameFlowManager.cs
   Assets/Scripts/Audio/AudioRuntime.cs Assets/Scripts/Data/LevelRating.cs Assets/Scripts/UI/MonsterCodexView.cs`
3. 重新导出 + 重封哈希（`tools/l01_flat_drop.py reseal`）。

工具：`tools/l01_flat_drop.py`（`values` / `reseal` / `verify` 三段；`values` 有防重入护栏：
基线必须 W5 敌数 = 220 且表内无 `flatdrop-20261029` 标记）。
