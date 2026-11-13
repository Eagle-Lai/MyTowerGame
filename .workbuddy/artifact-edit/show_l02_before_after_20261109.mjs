import fs from 'node:fs';
const audit=JSON.parse(fs.readFileSync('Library/BalanceStage/trusted-input-audit-20261109/trusted-inputs.json'));
const manifest=JSON.parse(fs.readFileSync('Artifacts/L02_Playtest_20261109_cell_changes.json'));
const review=JSON.parse(fs.readFileSync('Artifacts/L02_Playtest_20261109_review.json'));
const rows=name=>audit.protectedCurrentL02NotDesignInput[name].sheets.flatMap(s=>s.rows.map(r=>r.values));
const index=name=>new Map(rows(name).map(r=>[r.id,r]));
const enemies=index('EnemyData'),groups=index('EnemyList'),rounds=index('RoundData'),scene=rows('SceneInfo')[0];
const list=v=>Array.isArray(v)?v:String(v).split(',').filter(Boolean).map(Number);
const ids=list(scene.RoundList),changed=new Map(manifest.edits.map(e=>[`${e.table}/${e.id}/${e.field}`,e]));
const value=(table,id,field)=>changed.get(`${table}/${id}/${field}`)?.value??({EnemyData:enemies,EnemyList:groups,RoundData:rounds}[table].get(id)[field]);
const f=(v,d=2)=>Number(v).toFixed(d),pair=(a,b,d=2)=>`${f(a,d)} → ${f(b,d)}`;
let oldTotal=100,newTotal=100;
const detailed=[],economy=[],hp=[],counts=[];
for(let w=1;w<=25;w++){
 const rid=ids[w-1],r=rounds.get(rid),gids=list(r.EnemyIndexs);
 const before=gids.flatMap(gid=>list(groups.get(gid).EnemyIndexs)),after=gids.flatMap(gid=>list(value('EnemyList',gid,'EnemyIndexs')));
 const oldKill=before.reduce((s,id)=>s+enemies.get(id).reward,0),newKill=after.reduce((s,id)=>s+value('EnemyData',id,'reward'),0);
 const oldRound=r.rewardGold,newRound=value('RoundData',rid,'rewardGold');oldTotal+=oldKill+oldRound;newTotal+=newKill+newRound;
 if(w<5)continue;
 const byName=new Map();
 for(const id of new Set(after)){
  const e=enemies.get(id),name=e.resName.replace('Enemy_','');
  const item={wave:w,id,name,isFlying:e.isFlying,oldHp:e.hp,hp:value('EnemyData',id,'hp'),oldSpeed:e.speed,speed:value('EnemyData',id,'speed'),oldReward:e.reward,reward:value('EnemyData',id,'reward'),armor:e.armor,
   oldCount:before.filter(x=>x===id).length,count:after.filter(x=>x===id).length};
  detailed.push(item);byName.set(name,item);
 }
 hp.push(`| W${w} | ${['Chicken','Larva','Crawler','Scarab','Rat','Bat'].map(n=>{let e=byName.get(n);return e?pair(e.oldHp,e.hp):'—';}).join(' | ')} |`);
 const gid=gids[0];
 economy.push(`| W${w} | ${before.length} → ${after.length} | ${pair(groups.get(gid).enemyInterval,value('EnemyList',gid,'enemyInterval'),1)} | ${oldRound} → ${newRound} | ${pair(oldKill,newKill)} | ${pair(oldKill+oldRound,newKill+newRound)} |`);
 counts.push(`| W${w} | ${['Chicken','Larva','Crawler','Scarab','Rat','Bat'].map(n=>{let e=byName.get(n);return e?`${e.oldCount} → ${e.count}`:'—';}).join(' | ')} |`);
}
const hpTable=['| 波次 | Chicken HP | Larva HP | Crawler HP | Scarab HP | Rat HP | Bat HP |','|---|---:|---:|---:|---:|---:|---:|',...hp].join('\n');
const economyTable=['| 波次 | 总数量（只） | 间隔（毫秒） | 波次奖励（金） | 击杀奖励合计（金） | 本波总产金 |','|---|---:|---:|---:|---:|---:|',...economy].join('\n');
const detailedTable=['| 波次 | 敌人/ID | HP（前→后） | 速度（格/秒，前→后） | 单只击杀金币（前→后） | 护甲（不变） | 数量（前→后） |','|---|---|---:|---:|---:|---:|---:|',...detailed.map(e=>`| W${e.wave} | ${e.name} / ${e.id} | ${pair(e.oldHp,e.hp,6)} | ${pair(e.oldSpeed,e.speed,6)} | ${pair(e.oldReward,e.reward,8)} | ${e.armor} | ${e.oldCount} → ${e.count} |`)].join('\n');
const countTable=['| 波次 | Chicken | Larva | Crawler | Scarab | Rat | Bat |','|---|---:|---:|---:|---:|---:|---:|',...counts].join('\n');
const md=`# L02 本次写表前后完整对照

基准：本轮写入前保存的源表，与本轮实际写入清单逐项比较。旧值仅用于改动审计，不作为设计可信基准。此次只读汇总，没有再次修改配置。对应体验版 full-r3。

## 全部波次血量

以下均为修改前 → 修改后，展示保留两位小数；— 表示该波没有这种怪物。所有原始精度见 L02_Playtest_20261109_cell_changes.json。

${hpTable}

## 出怪与经济

击杀奖励合计与本波总产金均假定本波怪物全部击杀，实际漏怪会减少收入。间隔越小，出生越密。

${economyTable}

全关理论总经济（含初始100金、W1–W25全部击杀和波次奖励）：${f(oldTotal,6)} → ${f(newTotal,6)}金。

## 每种怪物数量

${countTable}

## 全部怪物属性与奖励

速度均为原值的1.05倍。这里按六位小数显示HP/速度，按八位小数显示单只击杀金币，精确源表数值见原始修改清单。护甲未变。

${detailedTable}

## 保持不变的范围

W1–W4、其余关卡、地图、塔与子弹属性、规则、场景生命及初始金币均未变；初始金币仍为100。源表已正式导出，Unity正常加载核对通过。
`;
fs.writeFileSync('Artifacts/L02_Playtest_20261109_before_after.md',md);
fs.writeFileSync('Artifacts/L02_Playtest_20261109_before_after.json',JSON.stringify({baseline:'preserved source immediately before this write',oldTotal,newTotal,detailed,actualChangedCells:manifest.edits.length},null,2));
console.log(hpTable);console.log('\n'+economyTable);console.log(JSON.stringify({oldTotal,newTotal,enemyVariants:detailed.length,speedRatios:[...new Set(detailed.map(e=>(e.speed/e.oldSpeed).toFixed(8)))],hpDown:detailed.filter(e=>e.hp<e.oldHp).length,hpUp:detailed.filter(e=>e.hp>e.oldHp).length}));
