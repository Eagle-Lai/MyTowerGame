# HUD「重试本波」实施与验收（2026-11-07）

> 后续更新：新增支持连续回退至第一波准备态的“回到上波”，右上角现为四颗按钮。最新行为与完整数据验证见 [回到上波实施记录](previous-wave/README.md)，本文保留第一阶段记录。

当前实体工程：`D:/FreedomTower_1`，Unity `2022.3.62f3c1`，MCP 插件 `10.3.0`。用户当次明确指定使用 stdio，桥接端口 `6400`；已通过 MCP 实例列表及 project/info 核对 `FreedomTower_1@520e2c6d` 的路径与版本。该连接信息仅为当次实测线索。

## 玩家行为

- HUD 右上角从左到右为：暂停 / **重试本波** / 菜单。节点名 `Btn_RestartWave`，保留现有 HUD prefab GUID。
- “本波”指 HUD 上的正式第 N 波（RoundData 对应的一整波），包括其中的全部出怪编组。
- 只在波次进行中、且本局存在该波开打前的检查点时可用。准备阶段和已结算状态禁用。
- 点击后打开现有 ConfirmView，提示塔、金币、生命将恢复到本波开始时的状态，并暂停模拟。
- 取消或点击背景：不回滚对局，恢复打开确认框之前的暂停状态；确认框内按 P 不会解除暂停。
- 确认：清理本波敌人、塔和临时表现，恢复开波前的塔型、等级、格位、实际投入、金币、小数奖励余数、生命、击杀、漏怪、前面已完成波次的统计和计时。取消自动开波倒计时，回到准备状态，允许重新布防，然后点击“开始”重打同一波。保留倍速档位。
- 原来的菜单“重新开始”仍然重开整关。

## 同步维护的位置

- `Assets/Prefabs/UI/HudView.prefab`：真实按钮、静态本地化组件与编辑态坐标。
- `HudView`、`EventName`、`GameFlowManager`：按钮绑定、请求事件、检查点和确认/取消链路。
- `ConfirmView`：可选取消回调、打开成功结果、销毁时的取消收尾。确认和取消回调都只消费一次。
- `LevelLayoutStore.CaptureCurrentLevel`：从原有保存逻辑提取只读捕获能力，检查点本身只在本局内存中。
- `PlayerDataManager`：恢复小数金币余数，避免重试丢掉上一波累计的零头。
- 重试时用恢复后的边界状态覆盖本波内出售塔产生的即时存档，避免卖塔交易被撤销后仍留在续局记录里；存档中的计时同步为开波检查点的计时。不更改存档 schema 或星级规则。
- `UIPrefabBuilder`：重建名单、创建按钮和补缺入口。
- `TacticalForgePrefabBuilder`：保留 GUID 的定点同步菜单及常规更新链；同时显式保存角落锚点，避免 Prefab Mode 因根 Canvas 尺寸为零而出现重叠。
- `TacticalForgeLayout`：三按钮排列及状态栏避让。
- `TacticalForgePreview`：HUD 和确认框的 `wave-retry` 三语言预览状态。
- `TacticalSans.asset`：Unity 为新提示补入“和、恢、复、状、復、狀”六个缺失字形及图集，三语言渲染未出现缺字。
- `Assets/Tests/BalanceCombat/WaveRestartCheckpointTests.cs`：资源恢复和检查点深拷贝回归测试。

## 多语言源表与导出边界

仅新增 `Luban/Config/Datas/Localization.xlsx` 的 `Localization!B392:F393`，改前这些单元格均为空：

| 英文主键/英文 | 简体中文 | 繁体中文 |
| --- | --- | --- |
| Retry Wave | 重试本波 | 重試本波 |
| Retry this wave? Towers, gold and HP will return to their wave-start state. | 重新开始本波？防御塔、金币和生命将恢复到本波开始时的状态。 | 重新開始本波？防禦塔、金幣和生命將恢復到本波開始時的狀態。 |

`B/C` 为主键/英文，`D/E` 为简/繁体，`F` 为维护注释，共新增 10 个单元格。改前基准为 `Localization.before.xlsx`，逐格与包内容比对见 `localization-whitelist.json`：原有单元格零改动，除 sheet1.xml 新增行外其它 OOXML 部件逐字节不变。

数据经过 `LubanExporter.ExportInternal` 标准导出。导出前后 SHA256 比对：只有 `Assets/ConfigJson/tblocalization.json` 变化，240 份关卡 XLSX 与其它 JSON 均保持本次开始时的状态，详见 `scope-verification.json`。工程原本已有的 L01 敌人表和其导出改动未被覆盖。

## 验证记录

- Unity 强制刷新并请求编译，等待编译、域重载和资产更新结束；`EditorUtility.scriptCompilationFailed=false`。
- EditMode 两项回归测试通过，覆盖小数奖励及资源/统计恢复、已完成波次统计的独立副本。
- Play Mode 使用独立 `BalanceTests/wave-retry-20261107` 存档和手动模拟。为验证保留此前进度，测试预置已完成第一波的统计，再以第二波配置生成真实敌人；这不是一次完整通关测试。23 项检查通过（包括恢复后存档的计时），见 `runtime-verification.jsonl`。
- 实际按钮 onClick、确认框标题/正文及语言切换：英文、简中、繁中三种语言通过，见 `runtime-localization-and-config.jsonl`。所有测试写入独立测试存档。
- `[Config]` 汇总成功读取 `TBLocalization: 385 条`，未出现失败表。现有交叉引用自检仍报告 16069 处告警（例如 L02 波次引用 L01 怪物），与本次按钮和多语言改动无关，保留日志且未扩范围修表。
- Console 保留会话开始前已经存在的 `CommandInvokationFailure: Unity Remote requirements check failed`；本次验证未新增 C# 编译错误或运行异常。
- 三语言 1920×1080 HUD/确认框，以及英文 1280×800 HUD 预览位于 `evidence/`。文字边界审计无截断、越界或背景遮挡。
- 最终已退出测试 Play Mode。尚未执行 Android 真机触控验收或出包。

## 手工验收

1. 进入任一关，布置防御塔并开始一波，确认右上角顺序是暂停 / 重试本波 / 菜单。
2. 点击“重试本波”，确认怪物暂停。取消应继续；如果此前已经暂停，取消后仍应暂停。
3. 本波内建造、升级或出售塔、获得金币或受到漏怪伤害后，再确认重试；应恢复开波前的局面，波号不跳回第一波。
4. 重新布防并点击“开始”，应从同一波的第一只怪重新出怪，之后可正常推进下一波。
5. 在设置中切换简中、繁中、英文，检查按钮及确认框；检查手机安全区、实际点击范围和小屏显示。
