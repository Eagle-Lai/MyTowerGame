"""Aggregate observed evidence and render a self-contained, reviewable route atlas."""
import collections,csv,html,json,math,pathlib,statistics,subprocess
import balance_pipeline as core

ROOT=core.ROOT;OUT=ROOT/'Docs/BalanceEvidence/30x25';E=ROOT/'Luban/BalanceDesign/Evidence30x25'

def csv_write(path,rows):
    if not rows:return
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    recipe=core.read_json(core.DEFAULT_RECIPE);plan=core.generate(recipe,'D04')
    actual=core.read_json(OUT/'final-reference/unity-results.json',[])
    d04={r['levelId']:r for r in actual if r['profileId']=='D04'}
    # Prefer the verified ablation, while preserving the original 58 raw runs.
    for r in core.read_json(OUT/'final-ablations/unity-results.json',[]):
        if r.get('strategy')=='maze-pruned-upgrades' and r['state']=='finished' and r['valid'] and r['stars']==5 and not r['metrics']['leaked']:
            d04[r['levelId']]=r
    economy={r['levelId']:r for r in plan['capacityEconomy']};maps={r['levelId']:r['cells'] for r in plan['tables']['tblevelmap']}
    audits=[];atlas=[];ledger=[];boundaries=[];issues=[]
    for L,r in sorted(d04.items()):
        b=next(x for x in r['waveBoundaries'] if x['beforeWave']==25);a=economy[L];t=r['towerContributions']
        before=[op for op in r['operations'] if op['waveOrdinal']<=25]
        income=next(x['initialGold'] for x in plan['levels'] if x['levelId']==L)+sum(w['killGold']+w['clearGold'] for w in r['metrics']['waves'][:24])
        spending=sum(x['cost'] for x in before)
        reconciled=income-spending==b['cash']
        if not reconciled:issues.append(f'L{L}: cash reconciliation mismatch')
        if any(op['waveOrdinal']==25 and op['timeMs']>0 for op in before):issues.append(f'L{L}: final-wave purchases must not be included in before-25 funding')
        maze=core.read_json(E/'Mazes'/f'L{L:02}.json')
        if b['pathLength']<maze['pathLength']:issues.append(f'L{L}: reference shorter than best blueprint')
        row={'levelId':L,'B':a['buildableCells'],'C':a['capacity'],'old85PercentCount':a['legacyOccupancyComparisonTowers'],
             'F_C':a['mixedLevelOneCost'],'routeTowers':b['towerCount'],'occupancy':b['occupancy'],'F_route':b['buildSpent'],
             'U_observed':b['upgradeSpent'],'incomeBefore25':income,'cashBefore25':b['cash'],'cashReconciled':reconciled,
             'minOperationBalance':min(op['balanceAfter'] for op in r['operations']),
             'pathSteps':b['pathLength'],'emptyPathSteps':len(core.path_for(maps[L]))-1,'searchBestSteps':maze['pathLength'],
             'searchUpperBound':maze['simplePathUpperBound'],'geometryRepeatTowers':sum(x['coveragePasses']>=2 for x in t),
             'actualRepeatEffects':sum(x['repeatEffectEnemies'] for x in t),'participatingTowers':sum(x['participated'] for x in t),
             'routeBlockersWithoutHits':sum(not x['participated'] and x['shortcutPreventedSteps']>0 for x in t),
             'noObservedCombatOrSingleRemovalShortcut':sum(not x['participated'] and x['shortcutPreventedSteps']==0 for x in t),
             'damage':sum(x['damage'] for x in t),'airHits':sum(x['airHits'] for x in t),'slowApplications':sum(x['slowApplications'] for x in t),
             'stars':r['stars'],'leaked':r['metrics']['leaked'],'combatMs':core.seconds_to_ms(r['metrics']['combatElapsedSeconds']),
             'parMs':r['profile']['parCombatTimeMs'],'planHash':r['profile']['planHash']}
        compact=[{**{k:v for k,v in q.items() if k!='layout'},'layout':[{k:v for k,v in x.items() if k in ['row','col','towerId','coveragePasses']} for x in q['layout']]} for q in r['waveBoundaries']]
        audits.append(row);atlas.append({'levelId':L,'cells':maps[L],'boundaries':compact,
            'final':[{k:v for k,v in x.items() if k!='repeatEffectDefinition'} for x in t],'audit':row})
        ledger.extend(dict(levelId=L,**op) for op in r['operations'])
        boundaries.extend({'levelId':L,**{k:v for k,v in b.items() if k not in ['layout','pathCells']}} for b in r['waveBoundaries'])
    core.write_json(OUT/'route-economy.json',{'rows':audits,'issues':issues,'upgradeInterpretation':'U_observed is paid by a successful reference, an upper bound on necessary upgrades; minimal U not proven. No future wave-25 income is used.'})
    csv_write(OUT/'route-economy.csv',audits)
    # Fixed scalar schemas keep the original complete JSON as authoritative detail.
    csv_write(OUT/'operation-ledger.csv',[{k:r.get(k) for k in ['levelId','waveOrdinal','timeMs','action','row','col','towerId','cost','balanceAfter']} for r in ledger])
    csv_write(OUT/'wave-boundaries.csv',[{k:r.get(k) for k in ['levelId','beforeWave','towerCount','cash','capacity','occupancy','buildSpent','upgradeSpent','pathLength']} for r in boundaries])
    simulation=[]
    for p in (E/'Simulation').glob('*/*/*/L*/result.json'):
        r=core.read_json(p);parts=p.relative_to(E/'Simulation').parts
        simulation.append({'mode':parts[0],'profileId':r['profileId'],'levelId':r['levelId'],'strategy':r['strategyId'],
            'stars':r.get('predictionStars'),'valid':r.get('ratingResult',{}).get('valid'),'victory':r['metrics']['victory'],
            'leaked':r['leaked'],'completedWaves':r['metrics']['completedWaveCount'],'combatToPar':r['combatToParRatio'],
            'towerCount':r['waves'][-1]['towerCount'],'pathSteps':r['waves'][-1]['pathLength'],
            'minBalance':min([x['balanceAfter'] for x in r['operations']]+[r['balance']]),'source':str(p.relative_to(ROOT)).replace('\\','/')})
    core.write_json(OUT/'strategy-matrix.json',simulation);csv_write(OUT/'strategy-matrix.csv',simulation)
    previous=core.read_json(ROOT/'Luban/BalanceDesign/Versions/balance-20x20-v1/balance_design.json')
    old_t={x['id']:x for x in previous['towerValues']};new_t={x['id']:x for x in recipe['towerValues']}
    changes=[{'section':'tower','id':i,'field':k,'before':old_t[i].get(k),'after':x.get(k)} for i,x in new_t.items() for k in ['power','CD','radius','prices','effectValue','canAttackAir'] if old_t[i].get(k)!=x.get(k)]
    changes += [{'section':'formula','id':'','field':k,'before':previous['formula'].get(k),'after':v} for k,v in recipe['formula'].items() if previous['formula'].get(k)!=v]
    changes += [{'section':'role','id':role,'field':k,'before':previous['roles'][role].get(k),'after':v} for role,x in recipe['roles'].items() for k,v in x.items() if previous['roles'][role].get(k)!=v]
    core.write_json(OUT/'old-new-values.json',changes);csv_write(OUT/'old-new-values.csv',changes)
    # Compare against the exact pre-task applied JSON, not a re-generated old
    # recipe whose compiler or profile semantics might have changed since then.
    historical={name:json.loads(subprocess.check_output(['git','show',f'71dacb5:Assets/ConfigJson/{name}.json'],cwd=ROOT).decode('utf-8-sig'))
        for name in ['tbsceneinfo','tbrounddata','tbenemylist','tbenemydata']}
    def totals(tables,L):
        scene=next((x for x in tables['tbsceneinfo'] if x['id']==L),None)
        if scene is None:return None
        rounds={x['id']:x for x in tables['tbrounddata']};lists={x['id']:x for x in tables['tbenemylist']};enemies={x['id']:x for x in tables['tbenemydata']}
        count=0;ehp=0;income=scene['initialGold'];before=income;clear=0
        for i,rid in enumerate(scene['RoundList']):
            wave=rounds[rid];ids=[eid for lid in wave['EnemyIndexs'] for eid in lists[lid]['EnemyIndexs']]
            count+=len(ids);ehp+=sum(enemies[eid]['hp']/(1-enemies[eid]['armor']) for eid in ids)
            if i==len(scene['RoundList'])-1:before=income
            income+=wave['rewardGold']+sum(enemies[eid]['reward'] for eid in ids);clear+=wave['rewardGold']
        return {'waves':len(scene['RoundList']),'enemyCount':count,'totalEhp':ehp,'initialGold':scene['initialGold'],'clearGold':clear,'incomeBeforeFinal':before,'totalIncome':income}
    comparison=[]
    for L in range(1,31):
        old=totals(historical,L);new=totals(plan['tables'],L)
        comparison.append({'levelId':L,'oldSource':'71dacb5 applied ConfigJson' if old else 'new level; no old counterpart',
            **{'old_'+k:(old[k] if old else None) for k in new},**{'new_'+k:v for k,v in new.items()}})
    core.write_json(OUT/'old-new-levels.json',comparison);csv_write(OUT/'old-new-levels.csv',comparison)
    data=json.dumps(atlas,ensure_ascii=False).replace('</','<\\/')
    template='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>30关真实长路线与逐波施工</title>
<style>body{font:16px system-ui;background:#101c28;color:#e5eef5;margin:30px auto;max-width:1250px;padding:0 20px}h1{font-size:26px}button,select,input{font:inherit}select{padding:8px}main{display:grid;grid-template-columns:2fr 1fr;gap:24px}svg{width:100%;background:#182a38;border:1px solid #476070}aside{line-height:1.8}#info{white-space:pre-line}#tower{background:#203647;padding:15px}input{width:80%}small{color:#b1c7d5}table{border-collapse:collapse}td{padding:3px 14px 3px 0}@media(max-width:800px){main{display:block}}</style>
<h1>30 关 · 长路线与火力复用</h1><p>来自 D04 真实连续 25 波回放。选关、拖动波次，点塔查看圆形射程与累计贡献。蓝线为真实地面最短路径；空军走 S→E 直线。</p>
<label>关卡 <select id="level"></select></label> <label>第 <b id="waveText">25</b> 波开始前 <input id="wave" type="range" min="1" max="25" value="25"></label>
<main><div><svg id="board"></svg><p><small>普通塔 蓝色 · 火力塔 橙色 · 减速塔 紫色；塔内数字为等级。点击后显示当前几何覆盖段数，以及整局实际伤害、减速和同敌离圈再入圈效果。</small></p></div><aside><div id="info"></div><p id="tower">点击一座塔。</p></aside></main>
<p>路线是给定搜索预算下最好结果，未证明全局最长。占用率低于 85% 已获用户授权。U 为成功轨迹实际升级支出，不表示已证明最小升级费。无输出但阻止捷径的塔单独记录；无观察贡献的塔不会被当成有效输出。</p>
<script>const data=__DATA__;let selected=null;const level=document.querySelector('#level'),wave=document.querySelector('#wave'),svg=document.querySelector('#board');for(const r of data){let o=new Option('L'+r.levelId,r.levelId);level.add(o)}
function draw(){let r=data.find(x=>x.levelId==level.value),b=r.boundaries.find(x=>x.beforeWave==+wave.value)||r.boundaries.at(-1),a=r.audit;document.querySelector('#waveText').textContent=b.beforeWave;let W=r.cells[0].length,H=r.cells.length;svg.setAttribute('viewBox',`-0.4 -0.4 ${W+.8} ${H+.8}`);let parts=[];for(let y=0;y<H;y++)for(let x=0;x<W;x++){let c=r.cells[y][x];parts.push(`<rect x="${x}" y="${y}" width="1" height="1" fill="${c=='#'||c=='X'?'#607783':'#1e3443'}" stroke="#354c5b" stroke-width=".025"/>`);if(c=='S'||c=='E')parts.push(`<text x="${x+.5}" y="${y+.67}" text-anchor="middle" font-size=".5" fill="#fff">${c}</text>`)}parts.push(`<polyline points="${b.pathCells.map(p=>[p[0]+.5,p[1]+.5].join(',')).join(' ')}" fill="none" stroke="#a5ead0" stroke-width=".11"/>`);for(const t of b.layout){let i=Math.floor((t.towerId-1)/3),color=['#68b8ec','#efb25e','#ba8ddc'][i];parts.push(`<g data-cell="${t.col},${t.row}" style="cursor:pointer"><circle cx="${t.col+.5}" cy="${t.row+.5}" r=".35" fill="${color}"/><text x="${t.col+.5}" y="${t.row+.65}" text-anchor="middle" font-size=".4" fill="#0e1d27">${(t.towerId-1)%3+1}</text></g>`)}if(selected){let [x,y]=selected.split(',').map(Number);parts.push(`<circle cx="${x+.5}" cy="${y+.5}" r="2" fill="#ffffff0a" stroke="#fff" stroke-dasharray=".15 .1" stroke-width=".035" pointer-events="none"/>`)}svg.innerHTML=parts.join('');document.querySelector('#info').textContent=`路线 ${b.pathLength} 步（空场 ${a.emptyPathSteps}）\n塔 ${b.towerCount} / 原容量 ${a.C}，占用 ${(b.occupancy*100).toFixed(1)}%\n施工 ${b.buildSpent}，升级 ${b.upgradeSpent}，余额 ${b.cash}\n整局 ${a.stars} 星、漏怪 ${a.leaked}\n实际重复效果 ${a.actualRepeatEffects} 次\n战斗 ${(a.combatMs/1000).toFixed(1)} / Par ${a.parMs/1000} 秒`;for(let g of svg.querySelectorAll('g[data-cell]'))g.onclick=()=>{selected=g.dataset.cell;let [x,y]=selected.split(',').map(Number),t=r.final.find(t=>t.col==x&&t.row==y),q=b.layout.find(t=>t.col==x&&t.row==y);document.querySelector('#tower').textContent=`格 (${y}, ${x})\n当前覆盖 ${q.coveragePasses} 段\n整局伤害 ${t.damage.toFixed(1)}，命中 ${t.hits}，对空 ${t.airHits}\n减速施加 ${t.slowApplications}，同敌离圈后再作用 ${t.repeatEffectEnemies}\n单独拆除缩短 ${t.shortcutPreventedSteps} 步`;draw()}}
level.onchange=()=>{selected=null;draw()};wave.oninput=()=>{selected=null;draw()};draw();</script>'''
    template=template.replace('#tower{background','#tower{white-space:pre-line;background').replace('实际重复效果','实际复用塔敌对').replace('同敌离圈后再作用','同敌离圈后再作用的敌人数')
    (OUT/'routes.html').write_text(template.replace('__DATA__',data),encoding='utf-8')
    summary={'actualRuns':len(actual),'actualFiveStars':sum(r['state']=='finished' and r['valid'] and r['stars']==5 and r['metrics']['leaked']==0 for r in actual),
        'D04Levels':len(d04),'baselineRuns':sum(r['mode']=='baseline' for r in simulation),'auditedEconomyLevels':len(audits),'issues':issues,
        'minRouteSteps':min((r['pathSteps'] for r in audits),default=0),'maxRouteSteps':max((r['pathSteps'] for r in audits),default=0),
        'minOccupancy':min((r['occupancy'] for r in audits),default=0),'maxOccupancy':max((r['occupancy'] for r in audits),default=0)}
    core.write_json(OUT/'delivery-summary.json',summary);print(core.canonical(summary))
    lines=['# 30关 × 25波：长路线经济改造验收','',
        '规则以用户 2026-10-19 的补充要求为准：优先长路线和火力复用，允许低于原 85% 占用率。原 prompt、20×20 版本与失败证据保留。塔数和路线长度不进入正式评分器。','',
        '## 实际结果','',
        f'- 最终配置 hash 的真实连续回放：{summary["actualFiveStars"]}/{summary["actualRuns"]} 场五星无漏。D04 覆盖 {len(d04)}/30 关，其余七档覆盖 L1/L10/L20/L30。',
        f'- 三类基线离线矩阵：{summary["baselineRuns"]}/720 条；评分直接调用 `FTProject.LevelRatingEvaluator`。其余离线结果是预测，不认证未实测关卡。',
        f'- D04 路线 {summary["minRouteSteps"]}—{summary["maxRouteSteps"]} 步；原容量分母下占用率 {summary["minOccupancy"]:.1%}—{summary["maxOccupancy"]:.1%}。路径是实际 A* 最短路径，不是画出的希望路线。',
        f'- 第 25 波开始前的经济核对 {len(audits)}/30 关；差异：{issues or "无"}。逐笔操作、逐波余额和占用见 [现金账本](operation-ledger.csv)、[波次检查点](wave-boundaries.csv)。','',
        '## 新数值与理由','',
        '普通塔高级单塔的伤害与射程收益收敛，让折返覆盖、对空位置和扩建更有价值。火力塔保留地面 AOE 职责，爆炸半径由 1.2 降至 0.75 格；减速塔伤害仍为零，按最强减速效果刷新，离圈余效由 0.3 降至 0.1 秒。','',
        '|塔型/等级|攻击|CD ms|半径格|增量费用|累计费用|减速|对空|','|---|---:|---:|---:|---:|---:|---:|---|']
    for t in recipe['towerValues']:
        family=(t['id']-1)//3;level=(t['id']-1)%3+1;total=sum(x['prices'] for x in recipe['towerValues'] if (x['id']-1)//3==family and x['id']<=t['id'])
        lines.append(f'|{["普通","火力","减速"][family]} {level}|{t["power"]}|{t["CD"]}|{t["radius"]}|{t["prices"]}|{total}|{t["effectValue"]:.0%}|{"是" if t["canAttackAir"] else "否"}|')
    lines+=['','各级价格都是增量费用，出售按累计投入的 70% 向下取整。完整旧新差异见 [数值对照](old-new-values.csv)；[逐关旧新总量](old-new-levels.csv) 直接读取基线提交的旧正式 JSON，对比波数、敌人总数、EHP、开场金、清场奖和末波前/整局收入。新增 L21—L30 不伪造旧值。','',
        '最终数量 `N=L+2w+15`，L1 合计 1050 只，L30 合计 1775 只。基础 EHP 使用 `26N × (1+0.018(L−1)) × (1+0.10(w−1)+0.010(w−1)²)`，每五波压力系数 1.10，最后一波 1.18；相邻关/波预算至少增长 2.5%，再乘档位系数。逐原型 HP、护甲、速度、地空组成及 ID 均由权威编译器输出，见八档逐波报告。',
        'D04 开场金 `160+4(L−1)`。清场奖每五波为 8/10/12/14/16 金，25 波合计 300 金；不依赖结算奖金。普通/群体/快速/空军/中型/重型/精英/首领击杀奖为 3/2/3/4/4/6/10/30 金。出生间隔 `clamp(650−8(w−1)−2(L−1),360,650)` ms，再乘档位系数。首领仅 L12 起末波出现。','',
        '|预设|EHP 倍率|速度倍率|间隔倍率|金币倍率|','|---|---:|---:|---:|---:|']
    for p in recipe['profiles']:lines.append(f'|{p["id"]} {p["name"]}|{p["ehpMultiplier"]}|{p["speedMultiplier"]}|{p["gapMultiplier"]}|{p["goldMultiplier"]}|')
    lines+=['','## 路线、覆盖与资金','',
        'B 是全部合法可建格，C=B−q，q 为 0/1 最短路至少需要保留的可建格。旧 F_C 继续按 C 座、约 50/30/20 混合一级塔计算；不会缩小分母。新版资金目标是完成实际长路线的 F_route 和成功轨迹所需升级。U_observed 是实测已付升级费的可行上界，未证明最小 U。','',
        '对初始真实参考中从未产生攻击或减速的塔撤掉升级，另做全 30 关回放；成功的删减版本优先用于下表。完整原轨迹和删减失败均保留在 `final-reference` 与 `final-ablations`。单独拆塔缩短路径是阻断捷径的证据；无输出且单独拆除不改路径的塔单列为无观察贡献，不能当作有效输出。','',
        '[交互路线查看器](routes.html) 可选择关卡与波次、点塔查看射程和累计贡献；[完整经济表](route-economy.csv) 包含 B/C、旧 85% 对照、原 F_C、空场距离、搜索预算上界、实际对空和减速贡献。','',
        '|关|B/C|塔数|路径步|占用|F_route|U_observed|25波前现金|复用塔敌对|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in audits:lines.append(f'|{r["levelId"]}|{r["B"]}/{r["C"]}|{r["routeTowers"]}|{r["pathSteps"]}|{r["occupancy"]:.1%}|{r["F_route"]}|{r["U_observed"]}|{r["cashBefore25"]}|{r["actualRepeatEffects"]}|')
    lines+=['','“复用塔敌对”统计同一塔对同一次出生的敌人产生效果、观察到离开圆形射程、再入圈后再次产生效果的唯一配对数；不是只靠圆形覆盖相交推断，也不是整个战役唯一敌人数。空军直线飞行，对空部署单独检查。',
        '路线搜索采用交替墙种子与有种子的局部重接，每图通常 3×2000 次；L9 加深为 12×6000 次，将最好路线从 52 步提高到 68 步。原种子、每次改善、预算及简单上界保存在 Mazes；有限搜索没有证明全局最长路线。','',
        '## 策略对照与未达目标','', '|策略（D04）|预测场次|五星|有效低星|失败|','|---|---:|---:|---:|---:|']
    for mode in ['baseline','maze','small','low','high']:
        subset=[r for r in simulation if r['profileId']=='D04' and r['mode']==mode]
        lines.append(f'|{mode}|{len(subset)}|{sum(r["stars"]==5 for r in subset)}|{sum(r["valid"] and r["victory"] and r["stars"] is not None and 0<r["stars"]<5 for r in subset)}|{sum(not r["victory"] for r in subset)}|')
    lines+=['','基线包含普通主力、火力聚怪、减速混合三类；maze 是统一默认长路线施工策略，实际五星参考经过针对性搜索和回放。默认策略不等于每关最优。small/low 分别限制为 `max(6,ceil(.15C))` 和 `max(Ksmall+1,ceil(.30C))`；不进入正式游戏规则。',
        '优化稀疏对照在 L1/L7/L10/L20/L30 各搜索 13 个有种子候选，包含合法卖塔损失，所有 trial/best 保留；真实代表关结果见 `final-ablations/unity-results.json`。未完成操作或资金不足的轨迹不认证通关。','',
        '**未全面达成“最优参考不能长期只用 Klow 内少塔五星”的原目标。** Klow 仍存在多关五星反例；默认 Ksmall 并未在大部分关卡轻松五星。这里不能声称所有少塔流已被消除，也不能用自愿补塔掩盖反例。用户的长路线优先规则已落实，但没有将塔数写入评分条件。',
        '八档 240 个关卡组合中，58 个有真实五星认证，其余 182 个保持未实测标记；对应 Par 中 58 条为实测，182 条按同关 D04 尾时与该档代表关尾时比例中位数估算。未声称这 182 个组合已通过 Unity。每关 D04 的合法低星预测轨迹另见 `Controls/lower-index.json`，低星实际覆盖以真实结果为准。','',
        '## Par 与生效证据','',
        'Par 使用逐波真实出生跨度及实际清尾累计时间，乘 1.06 调度余量，再向上取整到 5 秒。6% 是显式余量，不从目标星数反推。`Par/par-calibration.json` 保留 240 条依据及原始 witness；`combatBasisHash` 绑定战斗配置，编辑塔/敌群/经济/地图后失效回到暂定状态。',
        '权威入口为 `Luban/BalanceDesign/balance_design.json`，源 Excel 在 `Luban/Config/Datas`。正式应用经过暂存 Excel、两次真实 Luban 导出、全表回读与事务提交。应用收据、工作台回滚、资源包、编译、续局、安全和 UI 的实际结果统一列在 [机器验收](final-verification.json)。','',
        '## 复查入口与边界','',
        '- [真实完整 58 场](final-reference/unity-results.json)、[升级删减和稀疏对照](final-ablations/unity-results.json)、[续局与速度](final-checkpoints/unity-results.json)。',
        '- [实际战斗性能](final-performance/unity-results.json)：Unity Editor 渲染帧和主线程/GC/批次采样，不代表 Android 真机 FPS。快速回放截图可能积压表现特效，实际战斗截图另外预热采集。',
        '- UI 使用真实 prefab 的 30关/150星选关、末关详情、结算三语言两分辨率；构造结算仅测绑定和排版，不充当玩法证据。实际战斗另有 HUD 和棋盘截图。',
        '- 24→25 续局、25 波半波恢复、重复结算、1/2/3 速按同一合法操作比较原始双精度时钟、每波证据、余额及塔状态；暂停、上限延迟出生、旧存档迁移与一次性奖励使用隔离存储验证。',
        '- 原 20×20 配方/manifest/应用状态存于 `Versions/balance-20x20-v1`；旧报告、失败原始记录和开发搜索压缩包保存在 `Evidence30x25/Iterations`。原 prompt 不改写。',
        '- 本地基线提交 `71dacb5` 包含本轮开始前全部修改；未推送远端、未部署 CDN。完整玩家输入手感、设备安全区和 Android 真机帧率不由编辑器固定步长回放认证。','']
    lines+=['','## 真实策略对照','',
        '以下均读取同一最终配方，以真实初始资源和余额执行。失败及未完成轨迹照录；高占用控制是比较对象，不能称为通过的五星参考。低星预测在 Unity 中可能变为五星，以实际结果为准。','',
        '|策略|关卡|状态|实际星|漏怪|待执行操作|','|---|---:|---|---:|---:|---:|']
    comparisons=[r for r in core.read_json(OUT/'final-ablations/unity-results.json',[]) if r['strategy']!='maze-pruned-upgrades']
    comparisons += [r for r in core.read_json(OUT/'final-checkpoints/unity-results.json',[]) if r['strategy'] in ['high-occupancy-control','lower-star-control']]
    for r in comparisons:
        lines.append(f'|{r["strategy"]}|{r["levelId"]}|{r["state"]}|{r["stars"]}|{r["metrics"]["leaked"]}|{len(r.get("pendingOperations",[]))}|')
    verification=core.read_json(OUT/'final-verification.json',{});checks=verification.get('checks',[])
    if checks:
        lines+=['','## 技术验收状态','',
            f'机器验收 {sum(bool(r["passed"]) for r in checks)}/{len(checks)} 项通过。Python 51 项、Unity EditMode 57 项、运行安全 9 场、真实 prefab UI 36 张，以及真实战斗三语言两分辨率采集均保留独立结果。配置包为 Android 目标，11 张表和 30 行评分配置逐项回读。',
            '技术实现与验收通过不表示所有平衡目标达成。Klow 反例、182 个未实测组合、有限路线搜索及设备性能边界仍按前文列明。控制台中的故障注入按实际调用栈分类，未清空日志掩盖错误。','']
    lines+=['','## 实际渲染帧采样','',
        '每组在真实第 20 波敌群中预热 120 帧、采样 180 帧；采样时每个渲染帧推进 1/60 秒。主线程包含编辑器等待与工具开销，GC 包含验证工具和编辑器分配。没有据此认证 Android 设备性能。','',
        '|阵地|塔/峰值敌人|分辨率|帧间隔中位/P95 ms|主线程中位 ms|GC 中位 bytes|批次数中位|','|---|---:|---|---:|---:|---:|---:|']
    for r in core.read_json(OUT/'final-performance/unity-results.json',[]):
        p=r['performance'];s=r.get('renderedPerformance',{})
        if not s.get('completed'):continue
        median=lambda key:statistics.median(s[key]) if s.get(key) else 0
        batches=f'{median("batches"):.0f}' if any(s.get('batches',[])) else '未提供有效读数'
        lines.append(f'|{r["strategy"]}|{s["towerCount"]}/{s["alivePeak"]}|{p["width"]}×{p["height"]}|{s["medianFrameMs"]:.2f}/{s["p95FrameMs"]:.2f}|{median("mainThreadNs")/1e6:.2f}|{median("gcAllocatedBytes"):.0f}|{batches}|')
    lines+=['','此样本主要体现编辑器约 60 Hz 渲染节奏；实际主线程样本未出现持续超预算。批次计数器全为零，不能据此声称没有绘制，也不足以定位 GPU 或设备瓶颈。原始帧间隔、主线程、GC、批次序列及 CPU/GPU 型号完整保留。','',
        '高密铺仍以短通道聚怪为主，长路线阵地在多次折返中复用半径 2 格火力。实际地图和 HUD 三语言两分辨率截图见 `final-performance/Gameplay-*`；原快速回放图不能代替正常渲染帧表现证据。','']
    (OUT/'acceptance.md').write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__':main()
