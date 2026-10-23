"""Render final report reasoning from authored design and actual same-version evidence."""
from formal_tools import *
from evidence_accounting import reconcile
import sys,math,collections
source=pathlib.Path(sys.argv[1]);rows=json.loads(source.read_text(encoding='utf-8'));t=tables();tc={x['id']:x for x in t['tbtowerinfo']};h=runtime_hash()
authored=json.loads((REPORT/'audit/reference-authored-notes.json').read_text(encoding='utf-8'));calibrations={x['level']:x for x in json.loads((REPORT/'audit/final-calibration-decisions.json').read_text(encoding='utf-8'))['levels']};targets=json.loads((REPORT/'audit/economy-targets.json').read_text(encoding='utf-8'))
allactual=[]
for f in (REPORT/'raw-trials').glob('*/unity-results.json'):
 if not trial_inputs_match_current(f):continue
 for index,r in enumerate(json.loads(f.read_text(encoding='utf-8'))):
  if r['profile']['runtimeContentHash']==h:allactual.append((f,index,r))
def board(r):return{(x['row'],x['col']):x['towerId']for x in r['towerContributions']}
def delta(a,b):
 x,y=board(a),board(b);return sum(x.get(k)!=y.get(k)for k in x.keys()|y.keys())
def cash_threshold(r,target):
 """First observed cash threshold while the target tower's preceding grade exists."""
 cfg=tc[target['towerId']];previous=next(x['id']for x in tc.values()if x['upgradeTo']==cfg['id']);cash=100;layout={};point=target['row'],target['col']
 def ready():return layout.get(point)==previous and cash>=cfg['prices']
 for w in r['metrics']['waves']:
  wave=w['ordinal'];start=round(w['combatStartSeconds']*1000)
  if ready():return dict(wave=wave,timeMs=0,phase='准备开始',cash=cash)
  events=[(e['combatMs']-start,0,i,e)for i,e in enumerate(r['enemyOutcomes'])if e['waveOrdinal']==wave]
  ops=[(o['timeMs'],1,i,o)for i,o in enumerate(r['operations'])if o['waveOrdinal']==wave]
  for time,kind,_,e in sorted(events+ops,key=lambda x:x[:3]):
   if kind==0:
    if not e['leaked']:cash+=e['rewardOrDamage']
   else:
    if e is target:return dict(wave=wave,timeMs=time,phase='实际升级前',cash=cash)
    cash-=e['cost'];p=e['row'],e['col']
    if e['action']=='sell':layout.pop(p)
    else:layout[p]=e['towerId']
   if ready():return dict(wave=wave,timeMs=max(0,time),phase='现金阈值首次达到',cash=cash)
  cash+=w['clearGold']
  if ready():return dict(wave=wave,timeMs=round((w['combatEndSeconds']-w['combatStartSeconds'])*1000),phase='本波清波奖励到账后',cash=cash)
 raise AssertionError('Upgrade cash threshold missing')
chosen=json.loads((REPORT/'audit/selected-final-proofs.json').read_text(encoding='utf-8'))['levels'];accepted={x['level']for x in chosen if (REPORT/x['results']).resolve()==source.resolve()}
for level in sorted({r['levelId']for r in rows if r['strategy'].startswith('final-reference-')} & accepted):
 r=next(r for r in rows if r['levelId']==level and r['strategy'].startswith('final-reference-'));assert r['stars']==5 and not r['metrics']['leaked'];account=reconcile(r);m=r['metrics'];scene=next(s for s in t['tbsceneinfo']if s['id']==level);mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId']);ends={ch:(col,row)for row,line in enumerate(mp['cells'])for col,ch in enumerate(line)if ch in'SE'};dist=math.dist(ends['S'],ends['E']);free=sum(ch=='.'for line in mp['cells']for ch in line);history=authored[str(level)];ops=r['operations'];counts=collections.Counter(tc[x['towerId']]['type']for x in r['towerContributions']);timed=sorted({(o['waveOrdinal'],o['timeMs'])for o in ops if o['timeMs']})
 current=[(f,i,x)for f,i,x in allactual if x['levelId']==level];wins=[(f,i,x)for f,i,x in current if x['valid']and x['victory']and x['state']=='finished'and x['metrics']['completedWaveCount']==25 and not x['pendingOperations']and delta(r,x)>=2];assert wins,level
 wins.sort(key=lambda p:(-delta(r,p[2]),p[2]['metrics']['leaked'],len(p[2]['operations'])));af,ai,alt=wins[0];altaccount=reconcile(alt)
 index=json.loads((REPORT/f'L{level:02}/trial-index.json').read_text(encoding='utf-8'));bybatch=collections.Counter(x['batch']for x in index);timedcount=sum(o['timeMs']>0 for o in ops)
 geometry=f"地图{mp['rows']}行×{mp['cols']}列，{free}个普通建造格。S=(行{ends['S'][1]},列{ends['S'][0]})，E=(行{ends['E'][1]},列{ends['E'][0]})；空中直达几何距离{dist:.3f}格，减速后的真实飞行结算以事件记录为准。最终合法地面路线{len(r['finalPathCells'])-1}步，{len(r['towerContributions'])}座塔（普通{counts[1]}、群攻{counts[2]}、减速{counts[3]}）；路线来自Unity寻路。"
 pressure=' '.join(f"W{w}:出生{m['waves'][w-1]['successfulSpawned']}、战斗{account['waves'][w-1]['seconds']:.2f}秒、开战金{account['waves'][w-1]['afterPreparing']}。"for w in [5,15,25])
 thresholds=[]
 selected_upgrades=[]
 for kind in [1,2,3]:
  o=next((o for o in ops if o['action']=='upgrade'and tc[o['towerId']]['type']==kind),None)
  if o:
   selected_upgrades.append(o)
  for grade in [2,3]:
   o=next((o for o in ops if o['action']=='upgrade'and tc[o['towerId']]['type']==kind and tc[o['towerId']]['level']==grade),None)
   if o is not None and all(o is not x for x in selected_upgrades):selected_upgrades.append(o)
 for o in ops:
  if o['action']=='upgrade'and o['timeMs']>0 and all(o is not x for x in selected_upgrades):selected_upgrades.append(o)
 for o in selected_upgrades:
  q=cash_threshold(r,o);thresholds.append(dict(towerType=tc[o['towerId']]['type'],towerGrade=tc[o['towerId']]['level'],operationOrdinal=ops.index(o)+1,upgrade=o,cashThreshold=q))
 first_type_thresholds=[next((x for x in thresholds if x['towerType']==kind),None)for kind in [1,2,3]]
 affordability=' '.join(f"{'普通/对空'if x['towerType']==1 else'群攻'if x['towerType']==2 else'减速'}首次升级成本{x['upgrade']['cost']}，原轨迹在W{x['cashThreshold']['wave']} {x['cashThreshold']['timeMs']/1000:.2f}s（{x['cashThreshold']['phase']}）首次观察到前置等级已存在且现金足够；实际在W{x['upgrade']['waveOrdinal']} {x['upgrade']['timeMs']/1000:.2f}s升级。"for x in first_type_thresholds if x is not None)
 bounds='、'.join(f'{k} {v}次'for k,v in sorted(bybatch.items()))
 controls=[(f,i,x)for f,i,x in current if 'no-slow-same-geometry'in x['strategy']or x['strategy'].startswith('final-control-')]
 # Paths are relative to the individual level directory.
 controltext='；'.join(f"`{x['strategy']}`：{x['metrics']['completedWaveCount']}波、漏{x['metrics']['leaked']}、生命{x['metrics']['hp']}、{x['stars']}星、状态{x['state']}、未完成操作{len(x['pendingOperations'])}（[原始](../{f.relative_to(REPORT).as_posix()})索引{i}）"for f,i,x in controls)
 windows=[]
 for wave,time in timed:
  w=m['waves'][wave-1];start=round(w['combatStartSeconds']*1000);air=[e['combatMs']-start for e in r['enemyOutcomes']if e['waveOrdinal']==wave and e['isFlying']];windows.append(f"W{wave} {time/1000:.2f}s，{sum(o['waveOrdinal']==wave and o['timeMs']==time for o in ops)}笔顺序交易；该波最后空中结算{max(air)/1000 if air else 0:.2f}s，距本波结束{w['combatEndSeconds']-w['combatStartSeconds']-time/1000:.2f}s")
 timing='；'.join(windows)if windows else'本方案没有波中交易，全部建造与升级在各波准备阶段按编号完成。'
 lo,hi,lo25,hi25,why=targets[str(level)];w25=account['waves'][24];cal=calibrations[level];actualmargin=r['profile']['parCombatTimeMs']/1000-m['combatElapsedSeconds']
 notes=dict(mapAnalysis=geometry+' '+pressure,bottleneck='开发阶段的瓶颈与旧参考分析：'+history[0]+' '+history[1]+' 这些文字保留开发候选语境；最终推荐的实际布局、交易和成绩以下方三次正式记录为准。',selectionReason=f"最终方案按已完成的同封印五星候选比较：优先较少波中交易，再比较总交易数与战斗时间。当前轨迹{len(ops)}笔交易，其中{timedcount}笔波中交易，战斗{m['combatElapsedSeconds']:.2f}秒；首次与两次严格复跑使用固定时刻和相同顺序。有限候选中的推荐不等于全局最优。",searchBounds=f"本关已归档{len(index)}次真实试验，按批次为：{bounds}。全部实际候选含失败、非法、取消或超时，见候选索引；这些状态不计为成功。搜索包括折返/短路、三塔配比、升级顺序、一次合法出售改造和实测资金再投资，未穷举无限塔位/逐帧操作空间。当前封印另有保留几何去减速、地面专用火力、减少六处低级路墙三类对照；早期normal/power分别只买最多8塔，mistake只买1塔，只是受限投资对照，不能代表全部玩家。 "+controltext,timingWindows=timing+' 已认证的是这些离散时刻与顺序；没有把最后空中结算和本次操作之间的间隔冒充连续安全窗口。',economyAnalysis=f"逐关复核目标：W5开战{lo}～{hi}金，W25开战{lo25}～{hi25}金。{why} 当前实测W5开战{account['waves'][4]['afterPreparing']}，W25准备前{w25['beforePreparing']}、开战{w25['afterPreparing']}、结算{r['finalGold']}；最小交易后余额{account['totals']['minBalanceAfterOperation']}。区间以开发观察为基础确定，属于复核目标，不冒充事前预测。{affordability} 该阈值只说明原轨迹上现金和前置塔等级，不证明提前购买后其他施工仍可完成；更早投资需要另一条真实回放。替代与对照可能保留更多现金，不能仅凭终局金币证明紧凑或宽松。",alternativeAnalysis=f"同最终封印的实质替代：[实际完整结果](../{af.relative_to(REPORT).as_posix()})索引{ai}，runId `{alt['metrics']['runId']}`。与推荐方案有{delta(r,alt)}处最终塔位/等级差异，路线{len(alt['finalPathCells'])-1}步，{len(alt['operations'])}笔交易，完成25波，漏{alt['metrics']['leaked']}、生命{alt['metrics']['hp']}、实际{alt['stars']}星、战斗{alt['metrics']['combatElapsedSeconds']:.2f}秒；全部{altaccount['totals']['operationPrefixesChecked']}笔现金前缀已对账。这证明至少两类具体合法投资可通关；替代有漏怪时不称零漏五星。",limitations='验证为Unity2022.3.62f3c1编辑器内0.02秒固定步长、真实GameClock、正式数据与正常现金的隔离PlayMode。未验证Android实际帧率、手动鼠标/触控照做或连续时机容错范围。暂停与建造输入路径已有静态代码边界记录，未做人工暂停交易认证。不能从同一模拟时刻脚本顺序执行推断玩家无需暂停就能完成集中交易。',calibrationReason=f"Par={r['profile']['parCombatTimeMs']}ms为逐关确定的字面目标；校准依据为开发参考runId `{cal['sourceRunId']}` 的{cal['observedCombatSeconds']:.2f}秒，原余量{cal['marginSeconds']:.2f}秒。最终推荐实际余量{actualmargin:.2f}秒，评级由唯一LevelRatingEvaluator真实给出5星；没有修改战斗时钟、开局金或L01门槛。")
 notes['searchBounds']=notes['searchBounds'].replace('保留几何去减速','保留几何改变减速配资')
 decision=next(x for x in json.loads((REPORT/'audit/final-suite-decisions.json').read_text(encoding='utf-8'))['levels']if x['level']==level)
 notes['economyAnalysis']+='\n\n关键升级现金阈值还覆盖各类型首次到达三级以及全部波中升级，完整观测见[关键升级可负担阈值](evidence/upgrade-cash-thresholds.json)。\n\n|操作|坐标(行,列)|目标塔/级|实际升级|首次前置等级与现金足够|成本/当时现金|\n|---:|---|---|---|---|---:|'
 for x in thresholds:
  o=x['upgrade'];q=x['cashThreshold'];kind={1:'普通',2:'群攻',3:'减速'}[x['towerType']]
  notes['economyAnalysis']+=f"\n|#{x['operationOrdinal']}|({o['row']},{o['col']})|{kind}{x['towerGrade']}|W{o['waveOrdinal']} {o['timeMs']/1000:.2f}s|W{q['wave']} {q['timeMs']/1000:.2f}s，{q['phase']}|{o['cost']} / {q['cash']}|"
 notes['searchBounds']+=' 三类对照按本批最初参考的坐标与投资构造，原参考来源是 '+decision['reference']['source']+' 索引'+str(decision['reference']['sourceIndex'])+'；若比较后改选其他候选为主推荐，此处保留这些对照的实际原参照对象。'
 wall=decision['controls']['fewerWalls']
 notes['searchBounds']+=f" 减少路墙对照实际删除{len(wall['removedCells'])}处稳定{wall['removedGrade']}级塔位：{wall['removedCells']}。"
 if wall['removedGrade']!=1:notes['searchBounds']+='该参考没有稳定一级普通/群攻塔，删除最低可选等级也会减少升级火力，不能把结果单独归因于路线变短。'
 notes['searchBounds']=notes['searchBounds'].replace('减少六处低级路墙','减少稳定路墙')
 notes['searchBounds']+=' 本关减速配资对照的实际请求规则：'+('将原减速建造替换为普通1并省去减速升级，保留差额现金。'if decision['controls']['slowAllocation'].startswith('Replace every')else'将三处稳定普通核心改为同等级减速，保留实际费用差额；不是重复无减速主方案。')
 out=REPORT/f'L{level:02}/evidence/final-authored-notes.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf-8');(out.parent/'upgrade-cash-thresholds.json').write_text(json.dumps(thresholds,ensure_ascii=False,indent=2),encoding='utf-8')
 evidence=dict(runtimeContentHash=h,referenceRunId=m['runId'],alternative=dict(source=af.relative_to(REPORT).as_posix(),sourceIndex=ai,runId=alt['metrics']['runId'],differentFinalCells=delta(r,alt),account=altaccount),controls=[dict(source=f.relative_to(REPORT).as_posix(),sourceIndex=i,runId=x['metrics']['runId'],strategy=x['strategy'],state=x['state'],completedWaves=x['metrics']['completedWaveCount'],leaked=x['metrics']['leaked'],pendingOperations=len(x['pendingOperations']),finalPathSteps=len(x['finalPathCells'])-1)for f,i,x in controls])
 (out.parent/'alternative-and-controls.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8');print(level,'final notes grounded in actual records')
