# 3 级普通塔对空伤害 +10%（其余数值不变）—— 2026-10-29

## 需求

> 「让 3 级普通塔的对空伤害增加 10%，其余数值保持不变。」

## 为什么不能直接改 power

`TowerInfo.power` 是**同一条伤害值**，地面和空中共用（`BaseTower.HurtEnemy(target, Config.Power, ...)`）。
把 13 改成 14.3 会让地面伤害也涨 10%，违背"其余数值保持不变"。所以必须引入一个
**只对飞行单位生效**的倍率。

## 落地

| 层 | 改动 |
|---|---|
| 表 | `Luban/Config/Datas/TowerInfo.xlsx` 末尾新增列 `airDamageScale`（float）。9 行全部显式填 **1**，只有 **id=3（Normal Tower Lv3）填 1.1** |
| 生成 | Luban 导出后 `cfg.TowerInfo.AirDamageScale`（float）、JSON `tbtowerinfo.json` 同步带出 |
| 包装 | `Assets/Scripts/Data/TowerConfig.cs` 新增 `AirDamageScale`：`>0 取值，否则 1`（空单元格 Luban 给 0，等于"没配"） |
| 结算 | `Assets/Scripts/Tower/BaseTower.cs → HurtEnemy`：目标 `IsFlying` 时 `damage *= Config.AirDamageScale`。放在**伤害结算的唯一入口**，单体与 AOE 落点共用一条口径 |
| 测试 | `Assets/Tests/BalanceCombat/CombatTargetingAndSlowTests.cs` 里手工构造 `cfg.TowerInfo(...)` 补第 20 个参数 `1f`（否则 `CS7036`） |

改动前后（普通塔）：

| id | 塔 | level | power | airDamageScale | canAttackAir |
|---|---|---|---|---|---|
| 1 | Normal | 1 | 6 | 1 | 1 |
| 2 | Normal | 2 | 9 | 1 | 1 |
| **3** | **Normal** | **3** | **13** | **1.1** | 1 |
| 4–6 | Blast | 1–3 | 16/24/33 | 1 | 0 |
| 7–9 | Frost | 1–3 | 0 | 1 | 1 |

地面伤害、攻速、射程、造价、售出返还、对空资格（`canAttackAir`）全部未动。

## 验证

| 项 | 结果 |
|---|---|
| 编译 | `scriptCompilationFailed=false`，无 `error CS`（首轮被测试构造签名卡住，补参后通过） |
| Luban 导出 | 导出×2（asmdef 两次被删，均已 `git checkout` 恢复） |
| runtimeContentHash | **2a41a166b62b0f341e9026b19c3146937f7b85f518593ef8ca87468afb9d80c3**（30 关重封） |
| Play Mode | `[Rating] Runtime configuration SHA256 verified: 2a41a166…`，运行期 0 error |
| 运行时读数 | `power=13 airScale=1.1` |
| **实测伤害** | 同一座 L3 普通塔、同一发 10 点伤害：**空军扣 11（×1.1）**、**地面扣 10（不变）** |

实测是用 `HurtEnemy`（反射调用）对 `5000205 Bat`（飞行）与 `5000200 Chicken`（地面）各打 10 点，读 `CurrentHp` 差值得到的，不是只读配置。

## 注意

- 这是**全局表**：`TowerInfo` 只有一份，所以 L01–L30 的 3 级普通塔对空都变成 ×1.1。
- 评级/星级不读塔伤害，只读 EHP 与漏怪，所以本次改动不影响已有关卡评级，但会改变实际可打性（对空强了约 10%）。
- 表里新增列后，任何**手工构造** `cfg.TowerInfo` 的地方都要补参数 —— 目前只有那个 EditMode 测试，已补。
