"""Verify saved native Unity readback and publish the authorized application record."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Library/BalanceStage/w10-w25-apply-20261110'
DESIGN = ROOT / 'Library/BalanceStage/w9-w25-design-20261110'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
calc = read(DESIGN / 'calculation.json')
manifest = read(OUT / 'manifest.json')
scope = read(OUT / 'scope-after.json')
actual = read(OUT / 'unity-runtime-actual.json')
waves = [w for w in calc['waves'] if 10 <= w['wave'] <= 25]
rows = [r for r in calc['rows'] if 10 <= r['wave'] <= 25]
assert len(waves) == 16 and len(rows) == 80
assert actual['project'].replace('\\', '/').rstrip('/') == 'D:/FreedomTower_1/Assets'
assert actual['loaded'] and actual['failed'] == []
assert actual['isPlaying'] is False and actual['compilationFailed'] is False
assert actual['loader'] == 'FTProject.YooAssetResLoader'
assert [w['roundId'] for w in actual['waves']] == [w['roundId'] for w in waves]
lists = {e['id']: e['value'] for e in manifest['edits'] if e['table'] == 'EnemyList'}
hp = {e['id']: e['value'] for e in manifest['edits'] if e['table'] == 'EnemyData'}
assert len(hp) == 80 and len(lists) == 16
checked = 0
for expected, current in zip(waves, actual['waves']):
    rid = expected['roundId']
    seq = lists[rid]
    counts = Counter(seq)
    roster = {r['id']: r for r in expected['roster']}
    loaded = {r['id']: r for r in current['enemies']}
    assert len(loaded) == len(current['enemies']) and loaded.keys() == roster.keys()
    assert current['total'] == expected['total'] == len(seq)
    assert current['interval'] == expected['intervalMs']
    assert current['reward'] == expected['roundReward']
    signature = hashlib.sha256(','.join(map(str, seq)).encode('utf-8')).hexdigest()
    assert signature == current['sequenceSha256'], (rid, 'sequence mismatch')
    for enemy_id, enemy in roster.items():
        assert hp[enemy_id] == enemy['hp']
        assert struct.pack('<f', loaded[enemy_id]['hp']) == struct.pack('<f', hp[enemy_id]), (rid, enemy_id, 'HP mismatch')
        assert loaded[enemy_id]['count'] == counts[enemy_id] == enemy['count']
        checked += 1
assert checked == 80
assert struct.pack('<f', actual['w9Hp']) == struct.pack('<f', 537.084089)
assert actual['w9Count'] == 720
assert scope['sourceCellsVerified'] == 96
assert scope['outsideWhitelistSourceChanges'] == scope['outsideWhitelistJsonChanges'] == 0
assert scope['W1ThroughW9Unchanged'] and scope['otherLevelsUnchanged']
assert scope['all30InitialGold100'] and scope['airBeforeAndAfterPassed']
git = subprocess.run(['git', 'status', '--short', '--',
    'Luban/Config/Datas/Levels/L02/EnemyData.xlsx',
    'Luban/Config/Datas/Levels/L02/EnemyList.xlsx',
    'Assets/ConfigJson/tbenemydata.json', 'Assets/ConfigJson/tbenemylist.json'],
    cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True).stdout.rstrip()
assert len(git.splitlines()) == 4 and all(line[:3].strip() == 'M' for line in git.splitlines())
result = {
    'verified': True, 'project': actual['project'], 'loader': actual['loader'],
    'runtimeWavesVerified': 16, 'runtimeHpFloat32Verified': checked,
    'runtimeEnemyCountsVerified': checked, 'runtimeSequenceHashesVerified': 16,
    'intervalsAndRoundRewardsUnchanged': True, 'failedTables': [],
    'isPlaying': False, 'compilationFailed': False,
    'W9ChickenHpAndTotalPreserved': True,
    'sourceScopeEvidence': 'scope-after.json', 'gitStatus': git.splitlines(),
}
(OUT / 'unity-runtime-verified.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

lines = [
    '# L02 W10–W25 定点落表、导出与 Unity 实际加载记录', '',
    '日期：2026-11-10。状态：已完成源表定点修改、Luban 导出、白名单核对与当前 Unity 正常配置内存回读；未进行战斗测试。', '',
    '用户已实测认可 W9，并授权将已公布的算法候选应用到 W10–W25。本次原样应用既有候选，没有追加临时倍率。W9 及 W1–W8 保持。', '',
    '## 实际修改范围', '',
    '- `Luban/Config/Datas/Levels/L02/EnemyData.xlsx`：`Sheet!D30:D109`，80 个 hp 单元格。',
    '- `Luban/Config/Datas/Levels/L02/EnemyList.xlsx`：`Sheet!C13:C28`，16 个 EnemyIndexs 单元格；数量由名单表达。',
    '- W10–W20 的 roundId 为 2010–2020，W21–W25 为 2401–2405。',
    '- 速度、护甲、出怪间隔、单只击杀奖励及波次奖励保持；W1–W9、其他关卡未改，不是全部关卡应用。',
    '- 所有 30 关 initialGold 均为 100。', '',
    '## 应用的计算口径', '',
    '完整推导见 [原计算记录](L02_W9_W25_20261110_design.md)。本次以用户认可的 W9 作为已实测落地确认，延续同一候选算法到后续波次；没有从旧 L02 的低 HP 重新起算。', '',
    '数量按可信 L01 的同怪种波次结构及 W8 已应用数量锚点换算；HP 分地面、空中求解，考虑护甲、出生密度、AOE 多目标收益、减速驻留和普通塔地空分工。新增击杀收入只在后续波次计入累计金币，再按相对 L01 的购买力成长修正，避免重复计算金币或地图放大。地面同怪种设置 HP 下限；空中保留原波型峰值，峰值后的正常波允许回落至正常基线。', '',
    '金币折算有效火力仍依赖同类合理投资策略的容量近似，不能保证任意花钱方法或任意路线都等效。此次配置读回证明数值已经生效，不能代替 W10–W25 的用户实战验收。', '',
    '## 各波实际数量和主要 HP', '',
    '| 波次 | roundId | 地面 | 空中 | 总数：旧→新 | Chicken HP | Bat HP |',
    '|---|---:|---:|---:|---:|---:|---:|',
]
for w in waves:
    wr = [r for r in rows if r['wave'] == w['wave']]
    byname = {r['enemy']: r for r in wr}
    lines.append(f"| W{w['wave']} | {w['roundId']} | {w['groundCount']} | {w['airCount']} | {sum(r['oldCount'] for r in wr)}→{w['total']} | {byname['Enemy_Chicken']['newHp']:.6f} | {byname['Enemy_Bat']['newHp']:.6f} |")
lines += ['', '## 全部 80 条怪物修改前后对照', '',
    'HP 为源表精度；Unity / JSON 使用 float32，回读按 float32 位值核对。数量对应实际 EnemyIndexs 中该 ID 的出现次数。', '',
    '| 波次 | 怪物 | ID | HP：修改前→修改后 | 数量：修改前→修改后 |',
    '|---|---|---:|---:|---:|']
for r in rows:
    old = format(r['oldHp'], '.15g')
    lines.append(f"| W{r['wave']} | {r['enemy'].removeprefix('Enemy_')} | {r['id']} | {old}→{r['newHp']:.6f} | {r['oldCount']}→{r['newCount']} |")
lines += ['', '精确旧值与完整出怪顺序保存在审计目录的 manifest.json；上表对旧 HP 采用 15 位有效数字显示。', '',
    '## 经济结果', '',
    f"L02 初始 100 金，加上 W1–W25 全部击杀与波次结算后，理论累计收入为 **{calc['newTotalEconomy']:,.6f} 金**（约 **{calc['newTotalEconomy']:,.2f} 金**）；按导出 float32 奖励汇总为 {scope['L02TotalEarnedFromExport']:,.6f} 金。", '',
    '这是全清累计获得的资源，包含已经用于建塔或升级的部分，并非通关时钱包余额，也不包含卖塔返还的重复流转。单只奖励和结算奖励未改，新增收入来自新增怪物数量；不再受早期总额目标约束。', '',
    '## 实际导出和应用证据', '',
    '- 改前核对唯一 ID、字段、旧值及源表哈希，保留两个原始工作簿；正式源表只替换 96 个授权 OOXML 单元格，其余包成员、公式、格式和结构保持。写后 96 格回读通过。',
    '- 对比本轮改前的 250 个源表、11 个导出 JSON：白名单外零变化。只有本次两个源表与 `tbenemydata.json`、`tbenemylist.json` 内容改变；58 个 Assets/Gen 文件字节不变。',
    '- 通过当前工程原生 unityMCP 调用 `FTProject.EditorTools.LubanExporter.ExportInternal`；真实 Luban 进程成功、日志 `== succ ==`，返回 ok=true。11 个 JSON 产物检查通过。',
    '- 导出产物实际更新时间：2026-11-10 11:24:58（上海时间）。两个源表和两个 JSON 均由 git status 确认为 M。',
    '- 空中顺序在改前/改后分别检查 XLSX 和 JSON，包含跨编组、跨波边界，通过；判定只按 EnemyData.isFlying。',
    '- 当前 Unity 正常配置加载返回 IsLoaded=true、FailedTables=[]，Console 具有 `[Config] 配置加载完成` 汇总。',
    '- 编辑器实际回读 16 波、80 个 HP、80 个数量、16 个完整出生序列的 SHA256，全部匹配源表候选及导出；间隔、波奖、总数全部匹配。W9 Chicken HP 与总数 720 再次确认保持。', '',
    '当前工程 D:/FreedomTower_1，Unity 2022.3.62f3c1，MCP 插件 v10.3.0；当次选择实例 FreedomTower_1@520e2c6d 并核对 project/info。当前客户端服务 unityMCP，stdio 桥接 6400 为用户当次确认值，不作为未来默认端口。', '',
    '资产刷新后，在非 Play 状态调用工程正常 `Configs.ReloadForNewRunAsync`，加载器为 `FTProject.YooAssetResLoader`；没有候选注入、冻结保护绕过或战斗模拟。scriptCompilationFailed=false。', '',
    '## 保留的既有问题与验收边界', '',
    'Console 仍保留既有 Unity Remote requirements check failed 异常，以及 L02 敌人 levelId 元数据引起的关卡归属交叉引用告警；本次没有扩大范围修改这些问题。配置加载无失败表不表示所有既有告警已解决。', '',
    '本次已证明源表、Luban JSON、当前 Unity 正常配置内存一致；W10–W25 的实际难度是否合适，仍由用户逐波体验判断。', '',
    '审计目录：`Library/BalanceStage/w10-w25-apply-20261110/`。关键文件：manifest.json、source-authoring/committed.json、scope-after.json、unity-luban-export.json、luban-console.json、unity-runtime-actual.json、unity-runtime-verified.json、config-console-summary.json。', '',
    'Git 定点状态：', '', '```text', git, '```', '',
]
(ROOT / 'Artifacts/L02_W10_W25_20261110_applied.md').write_text('\n'.join(lines), encoding='utf-8')

report_path = ROOT / 'Artifacts/L02_W9_W25_20261110_design.md'
report = report_path.read_text(encoding='utf-8')
old = '执行状态更新：2026-11-10，用户随后明确确认仅应用W9。本轮已完成W9五个源表单元格修改、Luban导出及Unity正常配置内存回读；W10–W25仍为未应用候选。详见 `L02_W9_20261110_applied.md`。下文保留原计算时点的方案与改前值，不表示其余波次已落表。'
new = '执行状态更新：2026-11-10，用户实测认可 W9 后，进一步授权应用 W10–W25。现 W9–W25 均已完成源表定点修改、Luban 导出与当前 Unity 正常配置内存回读。详见 [W9 应用记录](L02_W9_20261110_applied.md) 和 [W10–W25 应用记录](L02_W10_W25_20261110_applied.md)。下文保留原计算时点的方案、假设与改前值；后续落地状态以两份应用记录为准。'
assert old in report or new in report
report = report.replace(old, new, 1)
report = report.replace('日期：2026-11-10。状态：仅计算与候选文件；未修改配置源表，未执行Luban导出，未进行Unity战斗或模拟。', '原计算日期：2026-11-10。以下为当时仅计算候选的历史内容；其后落表与导出已完成，见上方状态更新。未进行 Unity 战斗或模拟。', 1)
report_path.write_text(report, encoding='utf-8')

memory = ROOT / '.workbuddy/memory/VOL_07_工具与UnityMCP.md'
note = '''

## 2026-11-10 Codex L02 W10–W25 应用后续连接核对

- 本轮重新选择 FreedomTower_1@520e2c6d，project/info 与工作区 D:/FreedomTower_1、Unity 2022.3.62f3c1、manifest 插件 v10.3.0 一致。原生客户端服务 unityMCP，stdio 桥接 6400 为用户本会话确认线索；没有扫描、猜测或改端口，下次仍须现场确认。
- 经原生 MCP 调用工程 LubanExporter.ExportInternal 成功（11:24:58 上海时间），刷新资产后用正常 Configs.ReloadForNewRunAsync 加载。FailedTables=[]；实际内存 16 波、80 个 HP/数量、16 个完整出生序列签名全部匹配。非 Play，未战斗模拟；既有归属告警与 Unity Remote 异常保留。
- 审计：Library/BalanceStage/w10-w25-apply-20261110/；报告：Artifacts/L02_W10_W25_20261110_applied.md。本条只作当次线索，不是默认端口或跨工程结论。
'''
text = memory.read_text(encoding='utf-8-sig')
if '## 2026-11-10 Codex L02 W10–W25 应用后续连接核对' not in text:
    with memory.open('a', encoding='utf-8') as f:
        f.write(note)
print(json.dumps(result, ensure_ascii=False, indent=2))
