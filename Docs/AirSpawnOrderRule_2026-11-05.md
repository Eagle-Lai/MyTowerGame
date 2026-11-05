# 空中怪出生顺序规则与检查

2026-11-05 用户确认：任意两只空中怪不得相邻出生。当前全部关卡适用该规则，未来改动仍须取得当次关卡范围授权。完整规范位于根目录 `AGENTS.md` 的「空中怪不得相邻出生」章节。

## 判定

空中属性只取 `EnemyData.isFlying != 0`。按 `SceneInfo.RoundList` 的实际顺序，展开 `RoundData.EnemyIndexs` 引用的每个 `EnemyList.EnemyIndexs`；检查同编组及跨编组、跨回合边界。不同 ID 的空中怪相邻也违规。间隔时间不会豁免相邻位置，没有额外规定最小秒数。

## 只读检查

在工程根目录运行（Python 3，仅使用标准库，无第三方依赖）：

```text
python -X utf8 .workbuddy/tools/check_air_spawn_order.py
```

默认检查 L01–L30 的当前源表和当前导出 JSON，并核对两者影响出怪顺序/空中判定的字段。退出码 `0` 表示所选范围没有相邻空中怪、输入错误或源表/导出差异；退出码 `1` 表示失败。详细输出包含关卡、关内波号、roundId、编组 ID、怪物 ID、出生位置和源单元格。

```text
python -X utf8 .workbuddy/tools/check_air_spawn_order.py --source xlsx --levels 3
python -X utf8 .workbuddy/tools/check_air_spawn_order.py --format json
python -X utf8 -m unittest discover -s .workbuddy/tools -p test_air_spawn_order.py -v
```

JSON 格式包含全部违规记录；文本默认展示前 20 处，可用 `--max-details` 调整。报告中的空中数量按实际出生次数统计。检查器不写任何文件，也不连接或改变 Unity。

## 修改与验收

用户于 2026-11-05 澄清：“手动改表”是利用程序代码精确定位并修改获授权的单元格，不要求 Excel/WPS 界面或电脑控制。允许逐项执行已授权的多单元格清单；写前核对旧值并保存基准，写后回读证明白名单外零改动。禁止未经授权扩范围、整表重建或擅自批量调平。完整规则以 `AGENTS.md`「配置表按授权定点维护」为准。

1. 核对当次工程身份、编辑器未运行，并确认具体关卡/波次和修改字段。
2. 保存改前基准；用代码定点调整获授权的 `EnemyList.xlsx` 中 `EnemyIndexs` 单元格的空中怪位置。每波 ID 多重集合、数量、属性、出生间隔保持不变；已合规波次不动。
3. 对调整后的当前源表运行只读检查，确认相邻空中怪为 0；逐波对照改前基准，保证构成和数量没有变化。
4. 通过标准 Luban 流程导出，保护 `Assets/Gen/FTProject.Gen.asmdef` 及其 GUID；禁止直接写导出 JSON。
5. 默认双源检查通过后，通过已核对身份的 Unity MCP 刷新、检查 Console 和 `[Config]` 汇总。未完成编辑器验证时明确标记未完成。

## 2026-11-05 实施结果

- 用户授权 L01–L30 全部应用，仅重排 `EnemyList.EnemyIndexs`；以改前配置为基准，保留每波怪物 ID 多重集合、数量、属性、出生间隔，不额外规定秒数。L01、L02 合规且未改。
- 实际修改 L03–L30 共 28 份 `EnemyList.xlsx` 的 296 个 `Sheet1!C*` 单元格，涉及 586 次相邻空中位置交换。逐项核对批准清单里的源文件 SHA-256 与原值后定点写入；回读证明 28 个工作簿除目标单元格所在 sheet XML 外，其它包内文件内容均不变。
- 源表检查：750 波、24,032 次空中怪出生、相邻空中怪 **0 对**、输入错误 0。
- 经 Unity 菜单 `Tools/塔防/3. 导出配置表（Luban）` 成功导出 11 张表。默认 XLSX/JSON 双源检查通过，750 波相邻空中怪 0 对、源表/JSON 差异 0。与导出前快照对照，仅 `Assets/ConfigJson/tbenemylist.json` 的 296 个 `EnemyIndexs` 字段有变化，其余 10 个 JSON 未变；`Assets/Gen/FTProject.Gen.asmdef` 与 `.meta` 均保留。
- 12 项只读检查器单元测试通过。每次交换、波次、编组、源单元格和位置详见本任务外部附件 `air_spawn_manual_swaps.csv`；296 格完整旧值与新值详见 `air_spawn_manual_proposal.json`。
- **Unity 编辑器运行态验收未完成**：Unity MCP 已核对工程 `D:/FreedomTower_1`、Unity `2022.3.62f3c1`、实例 `FreedomTower_1@520e2c6d`，Play Mode 关闭；Luban 菜单执行成功。但 Console 当前有编译错误 `Assets/AOTAssembly/RuntimeReloadService.cs:137`（CS1737，可选参数排在必需的 `out` 参数前），`EditorUtility.scriptCompilationFailed == true`。该文件为本轮期间出现的未跟踪文件，未由本次任务修改。Console 还有已知 L02 `levelId` 交叉引用警告；未将它归因于本次出怪顺序修改。
- 已在 Codex、Claude Code、Cursor、Copilot、WorkBuddy 共享规则中澄清“手动改表”含义：用程序代码精确定位并修改获授权的源表单元格，无需 Excel/WPS 桌面操作；不得超范围或直接改 Luban 导出物。
