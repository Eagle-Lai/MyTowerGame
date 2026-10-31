from finalize import *
DOC.mkdir(parents=True,exist_ok=True)
r=json.loads((DOC/'selected-result.json').read_text(encoding='utf-8'));m=r['metrics'];ops=r['operations']
names={1:'普通',2:'火力（群攻）',3:'减速'}
def tower(tid):
    t=table[tid];return names[t['type']]+str(t['level'])+'级'
rows=all_rows();dump(DOC/'trial-index.json',rows)
text=f'''# 第3关：当前模型S型阵地与完整操作

## 结果

当前正式模型：25波，5082只怪，其中1180只飞行；初始100金币，12生命，击杀奖励按原值80%累计结算。未改任何关卡、怪物、塔、金币和评级数值。

已验证方案：完成{m['completedWaveCount']}/25波，击杀{m['killed']}/5082，漏怪{m['leaked']}，生命{m['hp']}/12，实际评级{r['stars']}星，评级有效={r['valid']}。战斗{m['combatElapsedSeconds']:.2f}秒，关卡总时{m['levelElapsedSeconds']:.2f}秒，剩余{r['finalGold']}金币。记录ID：{m['runId']}。

## 为什么当前不能五星

各波最后一只怪的计划出生时间合计1345.28秒（保守扣除每波一帧20毫秒仍至少1344.78秒），已超过五星870秒和四星1000.5秒。正常流程逐波清场后再开下一波，因此即使瞬间全灭全部怪，仍无法满足五星时间条件。当前满血零漏实际最多三星；本报告不把三星称作五星。

唯一评级入口实测原因：{', '.join(r['reasons'])}。

## 阵型

![最终阵型](最终布阵图.png)

最终{len(r['towerContributions'])}座塔；地面合法路径{len(r['finalPathCells'])-1}步。多次折返的S型走廊使群攻和减速反复覆盖；中央第8、9列负责直线空袭。飞行怪不会跟地面S路绕行。

## 玩家操作说明

- 坐标用（行,列），从0开始；左上角（0,0），入口（0,8），出口（8,8）。
- 使用普通关卡3开局，初始100金币；不要使用调试胜利、加钱、回血或跳波。
- “波前”指该波准备/上一波结算阶段。后续自动开波只有2.5秒，建议清波后立即按P暂停，按顺序完成该组交易后继续；游戏暂停时放置和升级入口仍可用。
- “波内x秒”从该波开始计时；如按金币操作，等金币达到该笔花费即可执行。相同时刻保持序号顺序。波内也可用正常P暂停按钮完成点击。
- 放置：点塔型按钮→点指定格；升级：点现有塔→升级。卖塔不是本方案必要操作。
- 表中余额为真实结算后余额；整数金币不足时不能提前购买，小数奖励自动累计。完整机器回放使用同目录best-operations.json。

## W1—W25完整操作

|序号|波次|时机|动作|坐标（行,列）|目标塔|花费|操作后余额|
|---:|---:|---|---|---|---|---:|---:|
'''
for i,o in enumerate(ops,1):
    timing='波前' if o['timeMs']==0 else '波内'+f"{o['timeMs']/1000:.2f}"+'秒'
    act={'build':'建造','upgrade':'升级','sell':'出售'}[o['action']]
    text+=f"|{i}|{o['waveOrdinal']}|{timing}|{act}|({o['row']},{o['col']})|{tower(o['towerId'])}|{o['cost']}|{o['balanceAfter']}|\n"
text+='\n## 逐波成绩\n\n|波|出生|击杀|漏怪|生命|波内战斗秒|击杀金币|清波金币|结算金币|\n|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n'
for w in m['waves']:
    text+=f"|{w['ordinal']}|{w['successfulSpawned']}|{w['killed']}|{w['leaked']}|{w['hp']}|{w['combatEndSeconds']-w['combatStartSeconds']:.2f}|{w['killGold']}|{w['clearGold']}|{w['gold']}|\n"
text+='\n## 最终逐塔清单\n\n|行|列|塔|总伤害|对空命中|减速应用|\n|---:|---:|---|---:|---:|---:|\n'
for t in sorted(r['towerContributions'],key=lambda t:(t['row'],t['col'])):
    text+=f"|{t['row']}|{t['col']}|{tower(t['towerId'])}|{t['damage']:.1f}|{t['airHits']}|{t['slowApplications']}|\n"
text+=f'''\n## 搜索与复核范围

截至本报告生成，已有{len(rows)}次实际Unity回放记录（含失败、拒绝和筛选）；细节见trial-index.json。另有4292次纯几何布局检查，只证明路线合法性与长度，不算游戏通关。比较了旧参考、增补防空、左右镜像及不同墙距S形、升级比例等策略。有限搜索不是全部合法局面的数学穷举，不声称全局最优。

当前选定记录固定步长{r['stepSeconds']}秒、速度1，加载正式Assets/ConfigJson，没有candidateDirectory。每笔交易调用正常TryBuild/TryUpgrade，资金来自开局、击杀和清波。隔离测试存档路径：{r['storagePath']}；不覆盖玩家正式存档。

输入runtimeContentHash：{r['profile']['runtimeContentHash']}；planHash：{r['profile']['planHash']}。

证据：selected-result.json保存唯一评级和完整指标；operations-with-cash.json保存每笔花费余额；final-layout.json保存实际地面路径和所有塔位；完整操作流水.csv为可筛选流水。最终严格复跑记录会在reproducibility.json另行保存。
'''
(DOC/'完整操作与测试报告.md').write_text(text,encoding='utf-8-sig')
print('report lines',len(text.splitlines()))
