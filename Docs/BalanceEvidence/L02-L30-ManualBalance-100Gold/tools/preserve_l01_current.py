"""Preserve the completed current-version baseline replay without touching L01 gameplay."""
from formal_tools import *
import sys,shutil
source=pathlib.Path(sys.argv[1]);rows=json.loads(source.read_text(encoding='utf-8'));r=next(x for x in rows if x['levelId']==1);m=r['metrics']
assert r['state']=='finished'and r['valid']and r['victory']and m['leaked']==0 and r['initialGold']==100
out=REPORT/'L01-current-check';out.mkdir(exist_ok=True)
(out/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
historical=json.loads((REPORT/'L01-reference/best-result.json').read_text(encoding='utf-8'))
fields=['completedWaveCount','successfulSpawned','killed','leaked','hp','maxHp','combatElapsedSeconds','levelElapsedSeconds']
comparison={k:dict(historical=historical['metrics'][k],current=m[k])for k in fields}
comparison.update(stars=dict(historical=historical['stars'],current=r['stars']),finalGold=dict(historical=historical['finalGold'],current=r['finalGold']))
baseline=json.loads((REPORT/'audit/current-source-records.json').read_text(encoding='utf-8'))['LevelRating']['1']['data'];current=next(x for x in tables()['tblevelrating']if x['id']==1)
diff={k:dict(before=v,current=current[k])for k,v in baseline.items()if k!='runtimeContentHash'and(v if v is not None else '')!=current[k]}
assert not diff,diff
evidence=dict(runId=m['runId'],source=str(source),sourceIndex=rows.index(r),runtimeContentHash=r['profile']['runtimeContentHash'],comparison=comparison,l01RatingChangesExceptRuntimeHash=diff,sourceGameplayAudit='../audit/formal-integrity-r1.json',batchInputs=f'../audit/batch-inputs/{source.parent.name}/input-manifest.json')
(out/'comparison.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# L01 当前正式版本基准重放','',f"runId：`{m['runId']}`；正式封印：`{r['profile']['runtimeContentHash']}`。",'',f"真实 InitLevel 初始金币{r['initialGold']}，初始生命{r['initialHp']}。25波、{m['successfulSpawned']}出生、{m['killed']}击杀、0漏怪，生命{m['hp']}/{m['maxHp']}，最终金币{r['finalGold']}，模拟战斗{m['combatElapsedSeconds']:.6f}秒，实际{r['stars']}星。",'','L01玩法、共享塔/子弹/全局/原型表和全部地图保持冻结。L01评级除全战役 runtimeContentHash 外字段与任务开始时源表逐项一致；未放宽原Par，零漏结果仍为4星。','', '|指标|历史参考|当前版本|','|---|---:|---:|']
for k,v in comparison.items():lines.append(f"|{k}|{v['historical']}|{v['current']}|")
lines+=['', '[当前完整结果](result.json) · [逐项比较与来源](comparison.json) · [历史原版参考](../L01-reference/测试报告.md)', '']
for s in r['waveBoundaries']+r['operationStages']:
    if s.get('screenshot'):
        name=pathlib.Path(s['screenshot']).name;image=source.parent/name;assert image.exists();shutil.copy2(image,out/name);lines.append(f'- [实际截图 {name}]({name})')
(out/'当前基准重放.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(comparison)
