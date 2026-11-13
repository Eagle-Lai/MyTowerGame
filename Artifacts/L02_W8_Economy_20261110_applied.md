# L02 W8 定点落表与 Luban 导出记录

后续验证补记（2026-11-10）：W9应用时原生unityMCP连接已恢复，选择FreedomTower_1@520e2c6d并核对当前D盘工程后，通过正常Configs.ReloadForNewRunAsync加载全部配置，FailedTables为空。W8四种怪物HP和314/192/121/39数量、231ms间隔、74金波奖及roundId=2008均已从编辑器内存回读，与本轮源表和导出一致。至此本记录原先缺失的编辑器加载确认已补齐；未进行战斗验证。证据位于 `Library/BalanceStage/w9-candidate-apply-20261110/unity-w8-unchanged.json`。下文保留此前导出及连接故障的历史经过。

日期：2026-11-10。用户已确认“按此候选仅修改 L02 W8 并导出”。

状态：源表定点修改、回读、正式 Luban 导出、JSON 内容与范围核对已完成。Unity 编辑器 `[Config]` 加载汇总未确认，未运行实战验证。

## 实际改动

仅 L02 W8（roundId=2008），源表共五个单元格：

| 源表 / 单元格 | ID / 字段 | 修改前 | 修改后 |
|---|---|---:|---:|
| EnemyData.xlsx / Sheet!D22 | 6000070 / hp | 126.40151615 | 445.918103 |
| EnemyData.xlsx / Sheet!D23 | 6000071 / hp | 82.1609854 | 289.846731 |
| EnemyData.xlsx / Sheet!D24 | 6000072 / hp | 232.57879125000002 | 820.489343 |
| EnemyData.xlsx / Sheet!D25 | 6000075 / hp | 270.22275 | 372.082872 |
| EnemyList.xlsx / Sheet!C11 | 2008 / EnemyIndexs | Chicken221、Larva127、Crawler81、Bat30 | Chicken314、Larva192、Crawler121、Bat39 |

W8 总数量 459→666，地面 429→627，空中 30→39。名单以可信 L01 W8 为顺序骨架扩展，新增空中怪分散到地面间隙。

保持 W8 速度、护甲、231ms 出怪间隔、各怪单只奖励及 74 金波次结算奖励不变。W7、其他波次及其他关卡均未被本次修改，不做全部关卡应用。

## 导出及检查证据

- 源表通过唯一 ID 与字段定位，修改前旧值及哈希匹配；四个 HP 和一格名单回读通过。
- 修改时仅替换获授权的 OOXML 单元格，其余 worksheet XML、工作簿包内容、公式与格式保持不变。已保存改前工作簿。
- 正式 Luban 命令返回退出码 0，日志最后为 `== succ ==`。2026-11-10 09:34:04（上海时间）实际更新 `Assets/ConfigJson/tbenemydata.json`、`Assets/ConfigJson/tbenemylist.json`。
- 与本轮改前基准比对全部 250 个源表、11 个 JSON：仅两个获授权源表及两个对应 JSON 内容变化，白名单之外零变化。JSON 行数、其余 ID 及字段保持不变。
- 导出 JSON 的 HP 按 System.Single 精度与源表相符；数量精确为 314/192/121/39。
- 改前、改后均运行 L02 XLSX 与导出 JSON 空中出生顺序检查，25 波无相邻空中、无源表/导出差异、无缺失或重复引用错误。跨编组及跨波边界通过。
- 30 关 `initialGold` 全部为 100。
- 58 个生成目录文件与本轮改前完全一致。Luban 删除的 `FTProject.Gen.asmdef` 已从本轮改前副本恢复，保留用户原有内容；无本次 C# 修改。
- Git 确认两个对应 JSON 为 `M`。Git 工作区原本已有多项变更，因此范围结论使用本轮改前哈希与字段基准，不把全部累计 Git diff 归于本次。

正式命令：

```text
Luban/Tools/Luban.ClientServer/Luban.ClientServer.exe -j cfg -c Luban/.cache.meta -- -d Luban/Config/Defines/__root__.xml --input_data_dir Luban/Config/Datas --output_code_dir Assets/Gen --output_data_dir Assets/ConfigJson --gen_types code_cs_unity_json,data_json -s all
```

## 编辑器确认边界

当前工作区身份核对为 `D:/FreedomTower_1`、Unity 2022.3.62f3c1、MCP 插件 v10.3.0。用户随后明确确认本次实际传输为 **stdio、Unity 端口 6400**；本机 `.unity-mcp/unity-mcp-status-520e2c6d.json` 也显示 `project_path=D:/FreedomTower_1/Assets`、`unity_port=6400`、`reason=ready`、版本匹配。该文件核对不能代替 MCP 实例选择与 `project/info` 核对。

通过正式 MCP `resources/list` 建连时，客户端在 `initialize` 握手阶段关闭，原始错误为：`MCP startup failed: handshaking with MCP server failed: connection closed: initialize response`。未取得实例列表或执行任何 Unity 编辑器工具。CLI 的 `mcp-for-unity --help` 可以正常返回。

为恢复已有服务，只调整了 `C:/Users/78296/.codex/config.toml` 的 `mcp_servers.unityMCP.command` 与 `args`，从直接调用 uvx 改为使用本机已有的 `unity_mcp_launcher.py` stdio 启动器。服务包仍为 mcpforunityserver 10.3.0，未切换传输、未改 Unity 端口。原配置已保存在 `C:/Users/78296/.codex/config.toml.before-unity-stdio-20261110-093940.bak`，解析比对确认其余配置零变化。重连一次仍返回相同握手错误，因此当前会话并未恢复 MCP，需要客户端重新加载服务配置后再核对。

未猜测或扫描端口，未使用 shell 直连 MCP 端点，也未用其他工程验证。电脑控制工具将客户端窗口标题返回为 ChatGPT，但包 ID 为 `OpenAI.Codex_2p2nqsd0c76g0!App`，与当前已确认的 Codex 应用一致。按该包 ID 选定唯一窗口后，首次截图报 `FrameArrived timed out: timed out waiting on channel`；重新选定并激活窗口后的一次恢复尝试仍报 `window capture timed out: timed out waiting on channel`。无法观察服务重连控件，未发送点击或键盘输入；客户端重连需用户手动完成。

因此 Luban 成功不等于 Unity `[Config]` 加载汇总已经通过。该编辑器确认仍待当前工程的 MCP 连接恢复后补做。没有进入 Play Mode 或进行战斗测试；实际难度由用户体验确认。

审计文件：`Library/BalanceStage/w8-economy-apply-20261110/`，包含改前基准、逐格清单、改前副本、导出日志、源表/JSON 范围报告和改前/改后空中顺序报告。
