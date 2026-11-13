import fs from 'node:fs';
import path from 'node:path';
import {makeWave,rows,L02,layoutCost,L02_FIRST4} from './terminal_balance_20261109.mjs';
const root='Library/BalanceStage/trusted-terminal-design-20261109';
const engine=path.join(root,'engine/full-r3');
const manifest=JSON.parse(fs.readFileSync(root+'/source-authoring/committed.json'));
const comparison=JSON.parse(fs.readFileSync(engine+'/comparison.json'));
const result=JSON.parse(fs.readFileSync(engine+'/unity-results.json'))[0];
const audit=JSON.parse(fs.readFileSync('Library/BalanceStage/trusted-input-audit-20261109/trusted-inputs.json'));
const params=JSON.parse(fs.readFileSync(root+'/engine/full-r3-parameters.json'));
const oldGroups=rows(audit.protectedCurrentL02NotDesignInput,'EnemyList');
const oldEnemies=new Map(rows(audit.protectedCurrentL02NotDesignInput,'EnemyData').map(e=>[e.id,e]));
const scope=JSON.parse(fs.readFileSync(root+'/scope-after.json'));
const loaded=JSON.parse(fs.readFileSync(root+'/unity-normal-load-verification.json'));
const waves=comparison.rows.map(r=>{
 const w=r.wave,old=oldGroups[w-1],ids=String(old.EnemyIndexs).split(',').map(Number),wave=makeWave(w,{level:2,...params[w-5]});
 const attributes=[...wave.tables.enemies.values()].map(e=>{let before=oldEnemies.get(ids.find(id=>oldEnemies.get(id).resName===e.resName&&oldEnemies.get(id).isFlying===e.isFlying));return {name:e.resName,isFlying:e.isFlying,oldHp:before.hp,hp:e.hp,oldSpeed:before.speed,speed:e.speed};});
 return {...r,oldCount:ids.length,oldIntervalMs:old.enemyInterval,newIntervalMs:[...wave.tables.groups.values()][0].enemyInterval,killGold:wave.kill,roundGold:wave.reward,attributes};
});
const total=L02_FIRST4+waves.reduce((s,w)=>s+w.killGold+w.roundGold,0);
const report={status:'user_playtest_build_not_final_balance',profile:'full-r3',reason:'User requested that a completed verified candidate be exported for playtesting before further balancing.',
 scope:'L02 W5-W25 only',targetLayoutCost:layoutCost(L02),totalTheoreticalGold:total,reserveIfNoLeak:total-layoutCost(L02),
 test:{completed:result.metrics.completedWaveCount,leaked:result.metrics.leaked,groundLeaks:149,airLeaks:0,pendingOperations:result.pendingOperations.length,
 actualFinalGold:result.finalGold,spent:result.operations.reduce((s,o)=>s+(o.cost||0),0),stepSeconds:.05,diagnosticHpOnly:true,
 note:'Million HP was used only in isolated replay to observe all 25 waves despite leakage; source scene HP was not changed. Actual player game can fail earlier. Purchase policy is a tested heuristic, not proven globally optimal.'},
 scopeVerification:scope,normalUnityLoad:loaded,waves};
fs.writeFileSync('Artifacts/L02_Playtest_20261109_review.json',JSON.stringify(report,null,2));
fs.copyFileSync(root+'/source-authoring/located-manifest.json','Artifacts/L02_Playtest_20261109_cell_changes.json');
fs.copyFileSync(engine+'/comparison.csv','Artifacts/L02_Playtest_20261109_pressure.csv');
const chosen=waves.filter(w=>[5,10,15,20,25].includes(w.wave));
const summary=chosen.map(w=>{const chicken=w.attributes.find(e=>e.name==='Enemy_Chicken'),bat=w.attributes.find(e=>e.name==='Enemy_Bat');return `| W${w.wave} | ${w.oldCount} → ${w.L02N} | ${w.oldIntervalMs} → ${w.newIntervalMs} | ${chicken.oldHp.toFixed(2)} → ${chicken.hp.toFixed(2)} | ${bat.oldHp.toFixed(2)} → ${bat.hp.toFixed(2)} |`;});
const md=`# L02 体验版交付记录（2026-11-09）

按用户要求暂停新增候选计算，落定已完成25波 Unity 回放的 full-r3，供人工体验。此版尚未达到最终平衡目标。

## 实际修改

仅 L02 W5–W25：EnemyData 的 hp、speed、reward；EnemyList 的 EnemyIndexs、enemyInterval；RoundData 的 rewardGold。共363格（300/42/21）。armor 实际未变。

W1–W4、地图、塔、子弹、规则、场景及其他关卡均未改变。30关 initialGold 均为100。精确旧值、新值及单元格见 L02_Playtest_20261109_cell_changes.json。

| 波次 | 数量（只） | 出怪间隔（毫秒） | Chicken HP | Bat HP |
|---|---:|---:|---:|---:|
${summary.join('\n')}

这些旧值仅用于说明写入差异，不作为设计可信输入。此版地面单只HP有明显降低，不能称为所有属性上调。设计输入仍为可信 L01 源表、L02 地图和确认截图塔阵。

## 经济

截图64塔成本6887金。理论总经济${total.toFixed(2)}金，零漏怪且只买截图等级时余量${(total-6887).toFixed(2)}金。模拟实际存在漏怪，击杀金损失，最终余134金，不能把理论219金当作每次必得余钱。

购买根据实际到账金币执行，限定截图塔位。该购买策略已测试，但没有全局最优证明。

## 已验证结果与限制

Unity 0.05秒固定步长回放完成25波，175笔购买均执行，最终64座达到截图等级。W1–W21零漏；W22/23/24/25地面分别漏6/46/17/80只，共149只；空中零漏。

回放使用隔离测试存储和仅用于观察的百万生命，以便漏怪后仍记录完25波。正式场景生命未改，所以正常体验可能提前失败。本版不满足固定布局零漏怪的最终要求，也未达到逐波末端压力完全等效。

## 生效验收

源表363格回读通过，白名单外零改动。Luban正式导出返回0并报告 == succ ==，三张JSON内容及mtime更新，git均为M。250张源表基准检查只发现获授权的三张L02表变化，其他关导出记录零变化。

空中相邻出生检查：源表与JSON均通过，包含波间边界，无缺失引用，源表与导出无差异。

Unity正常Boot启动加载11张表，FailedTables=0，scriptCompilationFailed=false，未使用候选覆盖或隔离测试存储。运行时三张表与正式导出JSON完全一致。

已存在的配置警告：L02敌人记录的levelId仍标为1，产生15364条交叉引用告警；该列未获本次修改授权，保持原值。现有运行按敌人全局ID取数，三张正式配置已读入。

后续以用户体验反馈决定是否继续调参，本次未继续投放未完成验证的候选。
`;
fs.writeFileSync('Artifacts/L02_Playtest_20261109_report.md',md);
console.log(JSON.stringify({totalGold:total,spent:report.test.spent,changedCells:manifest.edits.length,output:'Artifacts/L02_Playtest_20261109_report.md'}));
