import fs from 'node:fs';
import path from 'node:path';

// Prepare only the explicitly scoped W5 cell whitelist. No game, simulation, or source writes.
const out=process.argv[2];
if(!out)throw Error('A fresh stage directory is required');
const hpScale=Number(process.argv[3]||2),countScale=Number(process.argv[4]||2);
const trim=hpScale===1.6&&countScale===2;
if(!trim&&(hpScale!==2||countScale!==2))throw Error('Expected strengthening (2,2) or residual-based HP trim (1.6,2)');
const scope=JSON.parse(fs.readFileSync(path.join(out,'scope-before.json')));
const input=JSON.parse(fs.readFileSync(path.join(out,'current-source-inputs.json')));
const byId=rows=>new Map(rows.map(r=>[r.id,r]));
const l1=input.L01,l2=input.L02;
const e1=byId(l1.EnemyData.records),e2=byId(l2.EnemyData.records);
const oldSequence=l2.W5.sequence;
const count=(seq,id)=>seq.filter(i=>i===id).length;
const f3=l1.TowerInfo.records.find(t=>t.type===2&&t.level===3);
const l2f3=l2.TowerInfo.records.find(t=>t.type===2&&t.level===3);
if(!f3||f3.power!==33||f3.CD!==900||l2f3.power!==33||l2f3.CD!==900)throw Error('Unexpected strong-tower damage or cooldown');
const bullet=l1.BulletData.records.find(b=>b.id===f3.bulletId);
if(!bullet||bullet.aoeRadius<=0)throw Error('Strong-tower AOE not confirmed');
const edits=[],monsters=[],targets=new Map();
for(const id of new Set(l1.W5.sequence)){
 const source=e1.get(id);
 if(source.isFlying!==0)continue;
 const matches=[...new Set(oldSequence)].map(i=>e2.get(i)).filter(e=>e.isFlying===0&&e.resName===source.resName);
 if(matches.length!==1)throw Error('Ambiguous ground enemy match');
 const current=matches[0],hp=Number((source.hp*hpScale).toFixed(6));
 const sourceCount=count(l1.W5.sequence,id),oldCount=count(oldSequence,current.id),newCount=Math.round(sourceCount*countScale);
 if(trim){
  if(current.hp!==Number((source.hp*2).toFixed(6))||oldCount!==sourceCount*2)throw Error('HP trim requires the last tested HP x2 / count x2 baseline');
  if(hp!==Number((current.hp*0.8).toFixed(6))||newCount!==oldCount)throw Error('Only current HP x0.8 is authorized for this trim');
 }else if(hp<=current.hp||newCount<=oldCount)throw Error('Both HP and count must increase');
 const shots=(h,a)=>Math.ceil(h/(f3.power*(1-a)));
 const shotCounts={L01:shots(source.hp,source.armor),current:shots(current.hp,current.armor),new:shots(hp,current.armor)};
 if(!trim&&shotCounts.new<Math.ceil(shotCounts.current*1.5))throw Error('Per-enemy AOE shot threshold must increase at least 50%');
 targets.set(current.id,{oldCount,newCount,seen:0});
 edits.push({table:'EnemyData',id:current.id,field:'hp',old:current.hp,value:hp});
 monsters.push({id:current.id,name:current.name,resName:current.resName,L01Hp:source.hp,currentHp:current.hp,newHp:hp,
  L01Count:sourceCount,currentCount:oldCount,newCount,armor:current.armor,speed:current.speed,reward:current.reward,
  shotsAt33:shotCounts,hpIncreaseVsCurrent:hp/current.hp-1,countIncreaseVsCurrent:newCount/oldCount-1});
}
if(monsters.length!==3)throw Error('Exactly three ground types expected');
// Retain every old entry in order and insert only extra ground enemies of that type.
const newSequence=[];
for(const id of oldSequence){
 const t=targets.get(id);
 if(!t){newSequence.push(id);continue;}
 const before=Math.floor(t.seen*t.newCount/t.oldCount);
 t.seen++;
 const after=Math.floor(t.seen*t.newCount/t.oldCount);
 if(after-before<1)throw Error('Original sequence entry would be removed');
 for(let j=before;j<after;j++)newSequence.push(id);
}
const air=seq=>seq.filter(i=>e2.get(i).isFlying!==0);
if(JSON.stringify(air(oldSequence))!==JSON.stringify(air(newSequence)))throw Error('Air sequence changed');
if(newSequence.some((id,i)=>i&&e2.get(id).isFlying!==0&&e2.get(newSequence[i-1]).isFlying!==0))throw Error('Adjacent air');
for(const [id,t] of targets)if(count(newSequence,id)!==t.newCount)throw Error('Wrong count');
if(JSON.stringify(newSequence)!==JSON.stringify(oldSequence))edits.push({table:'EnemyList',id:2005,field:'EnemyIndexs',old:oldSequence,value:newSequence});
const list=s=>String(s).split(',').filter(Boolean).map(Number);
const rounds=byId(l2.RoundData.records),groups=byId(l2.EnemyList.records),scene=l2.SceneInfo.records[0];
let totalEconomy=scene.initialGold;
for(const rid of list(scene.RoundList)){
 const r=rounds.get(rid);totalEconomy+=r.rewardGold;
 for(const gid of list(r.EnemyIndexs))for(const id of list(groups.get(gid).EnemyIndexs))totalEconomy+=e2.get(id).reward;
}
const deltaGold=monsters.reduce((s,m)=>s+(m.newCount-m.currentCount)*m.reward,0);
const killGold=seq=>seq.reduce((s,id)=>s+e2.get(id).reward,0);
const l1map=l1.LevelMap.records[0],l2map=l2.LevelMap.records[0];
const evidence={profile:trim?'w5-ground-hp-trim-residual20':'w5-ground-strengthen-hp2-count2',
 scope:trim?'Only L02 W5 three ground HP fields; count unchanged':'Only L02 W5 three ground HP fields and ground counts',
 hpScaleVsL01:hpScale,countScaleVsL01:countScale,
 ...(trim?{hpScaleVsCurrent:0.8,observedTypicalResidualEstimate:0.2,calibrationRelation:'H_new = H_current * (1 - r_estimate); r_estimate=0.20. Typical observed residual is approximate, not a universal upper bound. Damage allocation can change after the edit; no guarantee of zero leaks.'}:{minimumIncreaseInAoeHitsVsCurrent:0.5}),
 maps:{L01:{cols:l1map.cols,rows:l1map.rows},L02:{cols:l2map.cols,rows:l2map.rows}},
 method:trim?'User reports early batches clear, late batches accumulate, and escapees typically have under 20% HP. Use a 20% HP correction based on that residual estimate, keep all enemy counts, timings, rewards, and all other fields unchanged. This isolates HP and avoids new economy or spawn-span changes. This is playtest-informed calibration, not a map-derived pressure-equivalence solution.':'User playtest says HP x1.25 and count x1.6 is still weak. Select L01 HP x2 and count x2 as a stronger trial, requiring at least 50% more 33-damage AOE hits per ground enemy than current. Extra ground entries extend the attack at unchanged spawn interval. Neither aggregate HP nor map size is treated as a linear AOE difficulty measure. No exact pressure-equivalence claim.',
 strongTower:{power:f3.power,cooldownMs:f3.CD,aoeRadius:bullet.aoeRadius},monsters,
 groundBefore:oldSequence.length-air(oldSequence).length,groundAfter:newSequence.length-air(newSequence).length,
 airBefore:air(oldSequence).length,airAfter:air(newSequence).length,totalBefore:oldSequence.length,totalAfter:newSequence.length,
 enemyIntervalMs:groups.get(2005).enemyInterval,additionalSpawnSpanSeconds:(newSequence.length-oldSequence.length)*groups.get(2005).enemyInterval/1000,
 additionalTheoreticalKillGold:deltaGold,waveKillGold:{before:killGold(oldSequence),after:killGold(newSequence)},
 theoreticalFullLevelEconomy:{before:totalEconomy,after:totalEconomy+deltaGold},
 unchanged:[...(trim?['all ground counts','entire spawn sequence','theoretical gold income']:[]),'air enemy attributes/count/order','speed','armor','enemyInterval','per-enemy reward','round reward','W1-W4','W6-W25','other levels','all initialGold=100'],
 battleSimulationPerformed:false};
const sourceHashes=Object.fromEntries([...new Set(edits.map(e=>e.table))].map(t=>[t,scope.sources[`Luban/Config/Datas/Levels/L02/${t}.xlsx`]]));
for(const name of ['manifest.json','calculation.json'])if(fs.existsSync(path.join(out,name)))throw Error('Preserve existing calculation: '+name);
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({sourceHashes,edits},null,2));
fs.writeFileSync(path.join(out,'calculation.json'),JSON.stringify(evidence,null,2));
console.log(JSON.stringify(evidence,null,2));
