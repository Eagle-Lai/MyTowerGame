"""Truthful work-in-progress navigation based only on archived actual trials."""
from formal_tools import *
import datetime
audit=next(REPORT/f'audit/formal-integrity-{tag}.json' for tag in ['final','r4','r3','r2','r1'] if (REPORT/f'audit/formal-integrity-{tag}.json').exists())
integrity=json.loads(audit.read_text(encoding='utf-8'))
assert integrity['sourceExportMatch']and integrity['sealMatch']and not integrity['unexpectedProtectedChanges'],'Finish the current audit before publishing a consistent-version status'
now=datetime.datetime.now(datetime.timezone.utc).isoformat();hash=runtime_hash();levelstatus=[];allrows=[]
lines=['# L02—L30 数值设计与实测（实施中）','',f'更新时间：{now}。任务尚未完成。全部 29 关、725 波首版字面值已经写入正式 Excel，并经正规 Luban 导出和全战役封印。所有 30 关源表与导出初始金币均为 100。', '', f'当前正式配置封印：`{hash}`。源表/导出已核对 {integrity["checkedSourceCells"]:,} 个单元格，无差异；冻结范围无非预期变更。五星、两次严格复跑与最终交付按下表分别记录，不能由源表已落盘推断通关。', '', '用户已澄清“手工”为逐项策划字面数值，允许代码写具体单元格；本任务未使用公式或统一倍率生成战役。当前完全访问，无需审批。', '', '[29关设计意图](设计总表.md) · [完整725波正式数据](725波正式配置明细.md) · [源表与导出审计](audit/formal-integrity-r1.json) · [L01历史参考](L01-reference/测试报告.md)','', '|关卡|源表 / 正规导出|已归档实测|最好实测结果|最终图/报告/两次严格复跑|', '|---|---|---:|---|---|', '|L01|玩法与评级门槛冻结，仅同步封印|历史证据|历史4星，当前版本未重证|[保留原始格式参考](L01-reference/测试报告.md)|']
baseline=REPORT/'L01-current-check/result.json'
if baseline.exists():
    b=json.loads(baseline.read_text(encoding='utf-8'));scope='当前正式版本'if b['profile']['runtimeContentHash']==hash else '本任务较早封印版本'
    lines[-1]=f"|L01|玩法与评级门槛冻结，仅同步封印|真实InitLevel=100；25波2575全杀|{scope}已重放，实际{b['stars']}星|[当前基准核对](L01-current-check/当前基准重放.md) / [历史原始参考](L01-reference/测试报告.md)|"
for level in range(2,31):
    p=REPORT/f'L{level:02}/trial-index.json';rows=json.loads(p.read_text(encoding='utf-8'))if p.exists()else[]
    if isinstance(rows,dict):rows=rows.get('trials',[])
    allrows.extend(rows)
    best=min(rows,key=lambda x:(not x.get('victory',False),x.get('leaked',999999),-x.get('waves',0),-x.get('hp',0),x.get('combatSeconds',999999)))if rows else None
    if best:result=f"开发记录：{best.get('waves','?')}波 / 漏{best.get('leaked','?')} / {best.get('stars','?')}星；具体封印见原始结果"
    else:result='尚无已归档实测'
    complete=all((REPORT/f'L{level:02}'/f).exists()for f in ['最终布阵图.png','完整逐波操作与测试报告.md','reproducibility.json'])
    delivery=f'[最终报告](L{level:02}/完整逐波操作与测试报告.md)'if complete else '待最终校准、严格复跑和交付'
    link=f'[候选索引](L{level:02}/trial-index.json)'if rows else '—'
    lines.append(f'|[L{level:02}数据](L{level:02}/设计与725波明细.md)|25波首版已落盘并导出|{len(rows)} {link}|{result}|{delivery}|')
    levelstatus.append(dict(level=level,sourceDesigned=True,officialExported=True,archivedTrials=len(rows),best=best,finalArtifactsPresent=complete))
drafts=[(level,revision) for level in range(2,31)for revision in ['r1','r2','r3','r4']if(REPORT/f'L{level:02}/首次成功-{revision}/首次成功布阵图.png').exists()]
lines+=['','已保存首次成功图、完整逐波操作和资金账的开发记录：'+ '、'.join(f'[L{level:02} {revision}](L{level:02}/首次成功-{revision}/首次成功逐波记录.md)'for level,revision in drafts)+'。均保留各自原始封印；最终五星认证尚未完成。旧版本、失败、非法和取消的试验单独保留。L01原件未覆盖。','','验证器仅新增初始资金、敌人结算、最终路线和可选换塔阶段观测；没有改变战斗规则。新阶段记录在真实交易前后取得，截图按 run 区分，避免多个候选互相覆盖。','','尚需：每关参考/替代与对照策略、最终零漏五星、真实现金守恒、合理时间余量、最终数据首次成功及两次严格复跑、29套最终图和完整25波报告。']
if integrity.get('coordinatedExternalChanges'):
    lines+=['','[并行任务协调与代码变更归属](audit/并行任务协调.md)：保留原始保护基线，方向任务的精确冻结指纹另存 [外部变更登记](audit/coordinated-external-changes.json)。后续实测使用移交后的代码快照；旧实测不能自动代表新代码。']
lines=[line.replace('audit/formal-integrity-r1.json',audit.relative_to(REPORT).as_posix())for line in lines]
if (REPORT/'audit/runtime-initialGold-30-r1.json').exists():lines+=['','[所有30关真实新局100金币核对](audit/runtime-initialGold-30-r1.json)：初始资金观察已覆盖全部关卡；后续正式数据变更后的最终版本仍需复核。']
(REPORT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
referencefile=REPORT/'audit/development-reference-selections.json'
if referencefile.exists():
    references=json.loads(referencefile.read_text(encoding='utf-8'))['levels']
    with (REPORT/'README.md').open('a',encoding='utf-8')as f:
        f.write(f'\n当前玩法对应的已审计零漏开发参考：{len(references)}/29关。逐关来源、真实资金与未认证边界见[参考选择](audit/development-reference-selections.json)。\n')
        if (REPORT/'audit/final-calibration-decisions.json').exists():f.write('\n逐关Par已经写入、正规导出并封印；五星可达与严格复跑按实际证据记录，校准字段已写入不等于最终认证。\n')
        f.write('\n[逐关经济目标与真实预算](逐关经济目标与实测.md)；L21/L25/L26末段预算较宽，文档保留这项容错，不宣称全部关卡极限紧经济。\n')
pending=['same frozen code/art final alternatives and three controls per level','all final-data first success plus two strict reruns','29 complete final layout/report/evidence sets','all30 real InitLevel initialGold audit']
if not referencefile.exists()or len(references)!=29:pending.insert(0,'zero-leak reference for every later level')
if not(REPORT/'audit/final-calibration-decisions.json').exists():pending.insert(0,'final Par calibration and campaign reseal')
status=dict(timestamp=now,status='incomplete',sourceWaveDesigns=list(range(2,31)),sourceGold100=list(range(1,31)),lastExport=f'L02-L30 literal source data, identities and all30 runtime seals; official Luban; {audit.stem}',runtimeHash=hash,actualArchivedTrials=len(allrows),levels=levelstatus,pending=pending)
(REPORT/'audit/checkpoint.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
design=REPORT/'设计总表.md';text=design.read_text(encoding='utf-8');old='每关仍需补全：25波精确调整、预测预算、真实参考解/替代解/三类对照、最终校准、两次严格复跑、29张独立图和逐波报告。表中的开局是待验证的合法购买组合，不是生存证明。当前只完成L02首版设计，不能据此宣称全部725波已完成。'
new='全部29关的首版25波字面调整已经写入并正规导出，完整数值、出生顺序、源地址和改动理由见 [725波正式配置明细](725波正式配置明细.md)。每关仍需按实测完成参考解/替代解/三类对照、现金流、最终校准、两次严格复跑、独立最终图和完整逐波报告。开局候选是合法购买组合，生存和高星由对应版本实测决定。'
if old in text:design.write_text(text.replace(old,new),encoding='utf-8')
print(len(allrows),'archived trials; progress updated')

