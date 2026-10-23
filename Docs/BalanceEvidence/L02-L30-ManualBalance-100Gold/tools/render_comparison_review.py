"""Describe actual bounded comparisons without promoting development evidence."""
from formal_tools import *
from evidence_accounting import reconcile
import collections

tag = 'comparisons-r4-u'
source = REPORT / 'raw-trials' / tag / 'unity-results.json'
rows = json.loads(source.read_text(encoding='utf-8'))
assert len(rows) == 77
closed = json.loads((REPORT / f'audit/{tag}-completion.json').read_text(encoding='utf-8'))
assert closed['inputsUnchanged'] and not closed['errors']
accounts = []
for i, r in enumerate(rows):
    if r['victory'] and r['state'] == 'finished' and not r['pendingOperations']:
        a = reconcile(r)
        accounts.append(dict(sourceIndex=i, runId=r['metrics']['runId'], totals=a['totals']))
lines = ['# 77次比较的实际决策复核', '',
         '本批绑定最终数值封印，但发生在十角色美术接入之前，仅作为候选选择依据。'
         '各关最终认证必须使用交回后的代码、资源和meta集合重新运行；本文件不宣称已完成最终认证。', '',
         '范围固定为44条替代投资、3条L28分阶段投资、29条保留几何去减速对照和1条L01严格基准。'
         '77条均实际运行并闭合，没有把准备但未执行的请求计入结果。', '',
         f"封印：`{closed['runtimeContentHash']}`；峰值同屏{closed['maxObservedAlive']}，"
         f"出生暂缓{closed['spawnDeferredCount']}。", '',
         f'其中{len(accounts)}条完整合法胜利逐笔独立对账；其他失败、漏怪、未执行完的操作照实保留。', '',
         '|索引|关|方案|完成波|漏怪|生命|星|交易/波中|战斗秒|未完成操作|',
         '|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|']
for i, r in enumerate(rows):
    m = r['metrics']
    lines.append(f"|{i}|L{r['levelId']:02}|{r['strategy']}|{m['completedWaveCount']}|"
                 f"{m['leaked']}|{m['hp']}|{r['stars']}|{len(r['operations'])}/"
                 f"{sum(o['timeMs'] > 0 for o in r['operations'])}|"
                 f"{m['combatElapsedSeconds']:.2f}|{len(r['pendingOperations'])}|")
lines += ['', '去减速并不预设必败。L02去减速仍为真实五星：83笔交易、20笔波中交易；'
          '原参考87笔、19笔波中交易，减少总操作与增加波中操作存在取舍。'
          '最终选择先比较波中交易，再比较总交易和时间，后续严格复跑仍是必要条件。', '',
          'L28分阶段追加投资中的零漏长路线候选实际为4星，不能因零漏或路线更长就替代五星候选。'
          '完整失败窗口见[实测诊断](comparisons-r4-u-实测诊断.md)。', '',
          '[77条完整原始结果](../raw-trials/comparisons-r4-u/unity-results.json) · '
          '[前后冻结审计](comparisons-r4-u-completion.json) · '
          '[完整资金对账汇总](comparisons-r4-u-victory-accounting.json)', '']
(REPORT / f'audit/{tag}-victory-accounting.json').write_text(
    json.dumps(accounts, ensure_ascii=False, indent=2), encoding='utf-8')
(REPORT / f'audit/{tag}-decision-review.md').write_text('\n'.join(lines), encoding='utf-8')
print(len(rows), 'actual trials;', len(accounts), 'complete victory cash accounts')
