# L01 血量微调（W5-25 地面 ×1.25 / 空中 ×1.05）—— 2026-10-30

## 需求与基线

在 308a339c（另一会话：按关拆分 + L01 数值 + 失败续局 + ground5-20261030 加怪 5%）之后的当前态上，
W5-25 地面怪血量 +25%、空中怪 +5%，其余全部不动。

## 修改的配置项

| 文件 | 内容 |
|---|---|
| `Levels/L01/EnemyData.xlsx` | 100 个 W5-25 变体 hp：地面 ×1.25、空中 ×1.05（desc 追加 `hp-20261030` 标注）；数量/奖励/出怪/W1-4 不动 |
| `Levels/L01/EnemyList.xlsx` | W5-25 共 21 行 desc 更新（EHP 新值） |
| `Levels/L01/LevelRating.xlsx` | planHash / balanceRevision(hp-25-5-20261030-v1) 更新；expectedEnemyCount 10236 与 par 不变 |
| `Levels/L02..L30/LevelRating.xlsx` | 仅 runtimeContentHash 重封 |
| `Assets/ConfigJson/*.json` | 导出产物 |

调整后规模：W5 EHP 10,281→12,716；W15 105,348→128,657；**W25 410,396→501,459**。
W5 普通怪 hp 39.538654 → **49.42332**（Play Mode 运行时实测读取一致）。

## 链路验证

- verify-layout passed=true；Luban 导出 ×2（asmdef 每次被删均已恢复）
- runtimeContentHash = `cd01f9d8…` → 重算后 **`3e6a6b25323d…`**（30 关重封）
- **Unity Play Mode：`[Rating] Runtime configuration SHA256 verified: 3e6a6b25…`，0 错误**

## 重要发现与修复：哈希公式已含新表 `tblevelrules`

首次导出后 Play Mode 报 `content hash mismatch`。反射调用 C# `CalculateRuntimeContentHash`
实算 `3e6a6b25…` ≠ 我重放的 `cd01f9d8…`；逐段差分定位：**评分行 30 行完全一致**，
分叉在 8-JSON 部分——提交 308a339c 新增了 `TBLevelRules` 表（失败续局），并把
`Configs.cs:463` 的哈希 keys 数组扩成 **9 键（+`tblevelrules`）**，而
`reseal_hash.py` 仍用旧 8 键列表。已同步更新 `reseal_hash.py`（9 键），重封后与 C#
实算逐字符一致。

**后续所有重封必须使用 9 键版 `reseal_hash.py`**（已更新至
`Docs/BalanceEvidence/L01-DiagramRedesign-20261028/tools/reseal_hash.py`）。

## 备注

- 本轮未动：奖励（含 gold20 的 0 掉落分配）、数量（W5=231）、出怪间隔、W1-4、三塔、SceneInfo。
- 关卡维持"极限压力基准"形态（W25 EHP 50.1 万），配合 308a339c 的失败续局功能游玩；
  零漏怪通关在该数值下不可达成（对空容量天花板 + 前期金收缺口，见前两轮探针）。
- 工具：`tools/l01_hp_tune.py`（防重入护栏：基线必须是 ground5-20261030 态，W5 N=231）。

## 【追加】血量第二轮：地面 ×1.55 / 空中 ×1.05（已验证）

- 需求：在上轮（×1.25/×1.05）之上继续：地面 +55%、空中 +5%，其余不动。
- 落地（`tools/l01_hp_tune2.py`，护栏=基线必须是 hp-20261030 层）：100 个 W5-25 变体 hp 再乘
  （desc 追加 `hp2-20261030` 标注）；数量/奖励/出怪/W1-4/三塔/par/expectedEnemyCount 全部不动。
- 规模（EHP）：W5 12,716→**19,355**；W10 47,506→**70,708**；W15 128,657→**191,470**；
  W20 216,711→**320,946**；W25 501,459→**746,979**。W5 普通怪 hp 49.42332→**76.60614**
  （Play Mode 运行时实测一致）。W1-4 不变。
- 链路：export×2（asmdef 又删又恢复）→ hash **`7f2214ce536d…`**（30 关重封，9 键版 reseal）→
  Play Mode `[Rating] verified 7f2214ce…` 0 错误。
- 累计口径（自初版迷宫重设计起）：地面 hp 累计 ×2.8125×1.55=**×4.359**；空中 ×4.2×1.05=**×4.41**。

## 【追加】范围修正：第 10 波并入（地面 ×0.85，已验证）

- 用户追加："第10波次也是" → −15% 范围修正为 **W10–25**（地面怪；空中仍不动）。
- 落地（`tools/l01_hp_tune3b_w10.py`）：W10 的 3 个地面变体 hp ×0.85；LevelRating planHash/修订
  （hp3-ground85-20261030-v2）更新。W10 波 EHP 70,708→**61,023**（-13.7%，混合空军后）。
- 链路：export×2 → hash **`2f5efb13e61d…`**（30 关重封，9 键版）→ Play Mode
  `[Rating] verified 2f5efb13…` 0 错误；运行时抽查 W13 普通怪 hp=128.9477（×0.85 态）。
- 最终口径：**W10-25 地面 hp 为上一轮的 0.85 倍，空中不变；W1-9 不动。**

## 【追加】血量第四轮：W15-25（含 15）地面 ×0.9（已验证）

- 需求：第 15 波（含）后到 25 波，地面怪血量 −10%，其余不动（空中不变）。
- 落地（`tools/l01_hp_tune4_w15.py`，护栏=基线必须是 hp3 层 + W15 N=481）：45 个 W15-25 地面
  变体 hp ×0.9（desc 追加 `hp4-20261030` 标注）；数量/奖励/出怪/W1-14/空中/三塔/par 全不动。
- EHP：W15 128,657×(地面 -10% 稀释后) → 波总降幅约 -8%；W25 644,471→约 -7%（地面占比稀释）。
- 链路：export×2 → hash **`59fb1660283a…`**（30 关重封，9 键版）→ Play Mode
  `[Rating] verified 59fb1660…` 0 错误；运行时抽查 W15 普通怪 hp=219.152（×0.9 态）。
- 踩坑：护栏里的 W15 敌数凭记忆写死 460 被盘上实际值 481（另一会话 ground+5% 所致）拦截——
  **护栏数字必须实测盘上值，不要凭记忆**。

## 【追加】血量第五轮：W15-25 地面再 ×0.95（已验证）

- 需求：上轮 −10% 基础上再降 5%。落地（`tools/l01_hp_tune5_w15.py`，护栏=hp4 层 + W15 N=481）：
  45 个 W15-25 地面变体 hp ×0.95（desc 追加 `hp5-20261030` 标注）；其余全部不动。
- 链路：export×2 → hash **`cc53b07447d7…`**（30 关重封，9 键版）→ Play Mode
  `[Rating] verified cc53b074…` 0 错误；运行时抽查 W15 普通怪 hp=208.1944（=219.152×0.95 ✓）。
- 累计（W15-25 地面，自初版起）：×4.359×0.9×0.95=**×3.727**。
