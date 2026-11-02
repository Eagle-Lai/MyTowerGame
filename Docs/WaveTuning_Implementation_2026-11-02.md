# WaveTuning 波型数值调节 —— 实施记录

> 执行日期：2026-11-02
> 依据：`Docs/prompts/2026-11-02-wave-tuning-executable-prompt.md`
> 工程：`D:\FishTestGame`（Unity 2022.3.62f3c1）

---

## 1. 做了什么（一句话）

新增 `WaveTuning` 表，按「关卡 × 波型（普通/困难）」提供怪物属性倍率与金币加成；
`RoundData` 显式写死 `waveType`（1 普通 / 2 困难，每 5 波一次困难）；
倍率在生成链路注入，金币在 `FinishRound` 以加法叠加。
**本次只加机制，不改任何现有数值**：60 行全部为默认值（倍率 1、加成 0）。

---

## 2. 覆盖完整性（实测数字）

| # | 指标 | 期望 | 实测 |
|---|---|---|---|
| 1 | `WaveTuning.xlsx` 数据行 | 60 | **60**（id 1..60，levelId 1..30 每关 2 行，waveType 1/2） |
| 2 | `RoundData.xlsx` 已加列 | 30 | **30**（git status 恰好 30 个文件） |
| 3 | `waveType` 取值 | 750 行全 ∈ {1,2} | **750 行，非法值 0** |
| 4 | 困难波行数 | 150（每关 5） | **150 困难 / 600 普通** |
| 5 | `tbrounddata.json` | 750 条带 waveType | **750 / 750** |
| 6 | `tbwavetuning.json` | 60 条 | **60** |

**关键抽查**：L01 的 `id=401`（name「第 21/25 波」）`waveType=1`，未被表行位置（表内第 16 行）误判为困难波。

---

## 3. 配置表改动

| 文件 | 动作 |
|---|---|
| `Luban/Config/Datas/WaveTuning.xlsx` | 新建：三层表头 + 60 行数据 |
| `Luban/Config/Datas/__tables__.xlsx` | 第 15 行登记 `TBWaveTuning`（备份 `__tables__.xlsx.bak_20261102_wavetuning`） |
| `Levels/L01..L30/RoundData.xlsx` | 追加第 7 列 `waveType`（备份 `RoundData.xlsx.bak_20261102_wavetype`） |
| `Tools/fill_round_wavetype.py` | 新建一次性填表工具（`--dry-run` / `--apply` / `--verify` / `--every`） |

**波次序号口径**：`SceneInfo.RoundList` 的位置 + `RoundData.name`（`第 N/25 波`）双向交叉校验，
不使用表行号。实测 L01/L02 表内行顺序与播放顺序不一致，其余 28 关一致；30 关全部通过校验。

**授权边界**：本次批量写表是用户 2026-11-02 单次授权，只写 `waveType` 一列；
脚本头注释已写明与 `AGENTS.md`「禁止脚本批量改写关卡表」的关系。`--verify` 逐格比对
`.bak`，除该列外 0 处差异。

---

## 4. 代码改动（C1–C11）

| # | 文件 | 改动 |
|---|---|---|
| C1 | `Scripts/Core/Res/ResTable.cs` | 登记 `tbwavetuning` |
| C2 | `Scripts/Data/Configs.cs` | 表实例 / `ConfigKeys` / `LoadAsync` 加载 / `WaveTuningByKey` 索引 / `RebuildWaveTuningIndex()` / `GetWaveTuning(levelId,isHard)` / `GetEnemy(id,isHard=false)` / `LogSummary` 加一行 / 交叉自检补「每关两行」检查 |
| C3 | `Scripts/Data/WaveConfig.cs` | `RoundConfig.WaveType` |
| C4 | `Scripts/Data/EnemyConfig.cs` | 双构造（看表值不缩放 / 战斗按波型缩放）；`Hp/Speed/Armor/Reward` 缩放；`BaseDamageToPlayer` + `DamageToPlayer` |
| C5 | `Scripts/Enemy/EnemyManager.cs` | `Spawn(id, isHardWave = false)` |
| C6 | `Scripts/Round/WaveManager.cs` | `BeginRound(round, isHardWave = false)` + `_isHardWave` 透传 `Spawn` |
| C7 | `Scripts/Game/GameFlowManager.cs` | `IsHardWave(round)`；`BeginRound` 传波型；回合奖励 `rewardGold + waveGoldBonus`；`clearGold` 记实际到账 |
| C8 | `Scripts/Enemy/BaseEnemy.cs` | 漏怪震幅改用 `BaseDamageToPlayer`（不随 `leakDamageBonus` 放大） |
| C9 | `Editor/LubanExporter.cs` | 自检列表加 `tbwavetuning` |
| C10 | `Editor/M0SetupWizard.cs` | 同上 |
| C11 | `Scripts/Data/Configs.EditorCandidates.cs` | 缺 json 回退当前表（含 `tbwavetuning`）+ 构造/接管/回滚 + `RebuildWaveTuningIndex()` |

**口径落实**：倍率按 `isFlying` 选地/空；倍率 null 或 ≤0 按 1；护甲加法后 `Clamp01`；
波次金币加法；击杀金币乘法；`waveType` 只认 2 为困难；图鉴仍用无缩放构造。

---

## 5. 生成物

`Assets/Gen/WaveTuning.cs`、`Assets/Gen/TBWaveTuning.cs`、`Assets/Gen/RoundData.cs`（多 `WaveType`）、
`Assets/Gen/Tables.cs`（多 `TBWaveTuning`）、`Assets/ConfigJson/tbwavetuning.json`、`Assets/ConfigJson/tbrounddata.json`。

> **注意**：`gen_code_json.bat` 每次导出都会删掉 `Assets/Gen/FTProject.Gen.asmdef`（Luban 清理非生成文件），
> 导出后必须 `git checkout -- Assets/Gen/FTProject.Gen.asmdef` 恢复，否则程序集划分会变。

---

## 6. 未做 / 有意不做

- `EnemyList.desc` 的 `tuning-20261102` 标注**未加**：提示词第 9 节把它列为风险处置，但第 2.4 节明确
  「`EnemyList` 的任何现有值不改」，且本次 60 行全为 1/0，EHP 不存在失真，故不加。
- `LevelRules` 一个字段未动；存档结构 / SQLite schema / UI 预制体 / 震屏规则均未改。

---

## 7. Unity 编译验证（已通过）

- `refresh_unity(mode="force", scope="all", compile="request", wait_for_ready=true)` → 返回成功；
  `mcpforunity://editor/state`：`is_compiling=false`、`is_domain_reload_pending=false`、`assets.is_updating=false`、`advice.ready_for_tools=true`。
- `execute_code` 取 `UnityEditor.EditorUtility.scriptCompilationFailed` = **false**。
- `read_console(types=["error"], count=50)`：只有 1 条与本次无关的 `Assert: On demand scheduler protocol error`（MCP 客户端侧）；
  `filter_text="error CS"` → **0 条**。
- `Library/ScriptAssemblies/FTProject.Runtime.dll` 493568 → 496128 字节（11:59:53），`FTProject.Editor.dll` / `FTProject.Gen.dll` 同步更新。

> 踩坑：执行期间按 `AGENTS.md` 写的 8084 找不到 MCP —— 本工程插件实际用 **8088**（截图确认 `HTTP URL=http://127.0.0.1:8088`）。
> 另外，外部编辑器改完 .cs 后 Unity 不会在后台重编译，`ScriptAssemblies` 时间戳不动 ≠ 编译失败，把编辑器切到前台才会触发。

---

## 8. 运行时验收（未做）

提示词第 7 节第 4–12 条（单波型/单关隔离、地空分离、波次金币、击杀金币、护甲 clamp、缺行防御、图鉴、震屏）
需要进 Play 模式逐项测，本次未执行。默认值全为 1/0，预期与改动前逐项一致。

---

## 9. 回滚

- **只回滚数值**：把 `WaveTuning.xlsx` 60 行改回 1/0 → 重跑 Luban，行为立刻复原（代码不用动）。
- **彻底移除**：删表 + 删登记行 + 删 json，回退 C1–C11 的提交；`RoundData.waveType` 列可保留（代码只认 2）。
