import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildGrid, runtimePath, normalizeTowerRows, makeRunState, stepOnce, DEFAULTS, isLegalPlacement} from '../tools/balance_sim.mjs';

export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
export const OUT=path.join(ROOT,'Library/BalanceStage/trusted-terminal-design-20261109');
const audit=JSON.parse(fs.readFileSync(path.join(ROOT,'Library/BalanceStage/trusted-input-audit-20261109/trusted-inputs.json'),'utf8'));
export const rows=(o,n)=>o[n].sheets.flatMap(s=>s.rows.map(r=>structuredClone(r.values)));
const list=v=>Array.isArray(v)?v:String(v).split(',').filter(Boolean).map(Number);
export function sourceTables(){
  const o=audit.trustedSources;
  const byId=a=>new Map(a.map(x=>[x.id,x]));
  const scenes=rows(o,'SceneInfo'); for(const s of scenes)s.RoundList=list(s.RoundList);
  const rounds=rows(o,'RoundData');for(const r of rounds)r.EnemyIndexs=list(r.EnemyIndexs);
  const groups=rows(o,'EnemyList');for(const g of groups)g.EnemyIndexs=list(g.EnemyIndexs);
  const maps=rows(o,'LevelMap').concat(rows(o,'L02Map'));for(const m of maps)m.cells=m.cells.split('|');
  return {global:{autoNextRoundDelayMs:rows(o,'LevelRules')[0].autoNextRoundDelayMs},scenes:byId(scenes),rounds:byId(rounds),groups:byId(groups),enemies:byId(rows(o,'EnemyData')),towers:byId(rows(o,'TowerInfo')),bullets:byId(rows(o,'BulletData')),maps:new Map(maps.map(m=>[m.levelId,m]))};
}
export const L01=audit.L01ConfirmedLayout.map(t=>({x:t.col,y:t.row,type:t.type,cap:t.levelHypothesis})).sort((a,b)=>a.y-b.y||a.x-b.x);
export const L02=[
 [0,3,3,1],[0,7,3,1],[0,11,3,1],[0,15,3,3],
 [1,1,3,1],[1,3,3,3],[1,5,3,3],[1,7,3,3],[1,9,3,3],[1,11,3,3],[1,13,3,3],[1,15,3,3],
 [2,1,3,3],[2,3,3,3],[2,5,3,3],[2,7,3,3],[2,9,3,3],[2,11,3,3],[2,13,3,3],[2,15,3,3],
 [3,1,1,3],[3,3,1,3],[3,5,1,3],[3,7,1,3],[3,9,1,3],[3,11,1,3],[3,13,1,3],[3,15,3,3],
 [4,1,1,3],[4,3,2,3],[4,5,1,3],[4,7,2,3],[4,9,1,3],[4,11,2,3],[4,13,1,3],
 [5,1,1,3],[5,3,1,3],[5,5,1,3],[5,7,1,3],[5,9,1,3],[5,11,1,3],[5,13,1,3],[5,14,1,3],[5,15,1,3],
 [6,1,3,3],[6,3,3,3],[6,5,3,3],[6,7,3,3],[6,9,3,3],[6,11,3,3],[6,13,3,3],[6,14,1,3],[6,15,1,3],
 [7,1,3,3],[7,3,3,3],[7,5,3,3],[7,7,3,3],[7,9,3,3],[7,11,3,3],[7,13,3,3],
 [8,1,3,1],[8,5,3,1],[8,9,3,1],[8,13,3,1],
].map(([y,x,type,cap])=>({x,y,type,cap}));
const T=sourceTables();
const norm=normalizeTowerRows(T);
const tower=(type,level)=>[...norm.values()].find(r=>r.family===type-1&&r.level===level);
export const cost=(type,lv)=>Array.from({length:lv},(_,i)=>tower(type,i+1).prices).reduce((a,b)=>a+b,0);
export const layoutCost=(layout,levels)=>layout.reduce((s,t,i)=>s+cost(t.type,levels?levels[i]:t.cap),0);
export function wavesFromTables(tables,level=1){return tables.scenes.get(level).RoundList.map((rid,w)=>{let round=tables.rounds.get(rid);let groups=round.EnemyIndexs.map(id=>tables.groups.get(id));let ids=groups.flatMap(g=>g.EnemyIndexs);return {w:w+1,round:structuredClone(round),groups:structuredClone(groups),ids,kill:ids.reduce((s,id)=>s+tables.enemies.get(id).reward,0),reward:round.rewardGold};});}
export const BASE=wavesFromTables(T);
const sum=a=>a.reduce((s,x)=>s+x,0);
export const L01_TOTAL=100+sum(BASE.map(w=>w.kill+w.reward));
const protectedTables=audit.protectedCurrentL02NotDesignInput;
const protectedE=new Map(rows(protectedTables,'EnemyData').map(x=>[x.id,x]));
const protectedG=new Map(rows(protectedTables,'EnemyList').map(x=>[x.id,x]));
const protectedR=new Map(rows(protectedTables,'RoundData').map(x=>[x.id,x]));
const protectedScene=rows(protectedTables,'SceneInfo')[0];
const protectedRoundIds=list(protectedScene.RoundList);
export const L02_FIRST4=100+sum(protectedRoundIds.slice(0,4).map(rid=>{const r=protectedR.get(rid);return r.rewardGold+sum(list(r.EnemyIndexs).flatMap(gid=>list(protectedG.get(gid).EnemyIndexs)).map(id=>protectedE.get(id).reward));}));
const NEW_INCOME_FACTOR=(7106.01-L02_FIRST4)/sum(BASE.slice(4).map(w=>w.kill+w.reward));
export function protectedOpeningWave(w){
 if(w<1||w>4)throw new Error('Protected L02 data may only model the unchanged W1-W4 opening');
 const t=sourceTables(),round=structuredClone(protectedR.get(protectedRoundIds[w-1]));round.EnemyIndexs=list(round.EnemyIndexs);
 const groups=round.EnemyIndexs.map(id=>{let g=structuredClone(protectedG.get(id));g.EnemyIndexs=list(g.EnemyIndexs);return g;});
 const sequence=groups.flatMap(g=>g.EnemyIndexs),es=new Map([...new Set(sequence)].map(id=>[id,structuredClone(protectedE.get(id))]));
 t.enemies=es;t.rounds=new Map([[round.id,round]]);t.groups=new Map(groups.map(g=>[g.id,g]));
 t.scenes=new Map([[2,{...t.scenes.get(1),id:2,mapId:2,initialHp:1000000,RoundList:[round.id]}]]);
 return {tables:t,sequence,n:sequence.length,nAir:0,reward:round.rewardGold,kill:sum(sequence.map(id=>es.get(id).reward)),parameters:{protectedOpening:true}};
}

export function makeWave(w, {level=1,countScale=1,hpGround=1,hpAir=1,speedGround=1,speedAir=1,gapScale=1,incomeDelta=0,roundRewardOverride=null}={}){
 const src=BASE[w-1], t=sourceTables();
 let sequence=src.ids.slice();
 if(level===2&&countScale!==1){
  // Preserve order separately within each layer, then distribute flights with a non-air slot between.
  const resample=a=>{const n=Math.max(1,Math.round(a.length*countScale));return Array.from({length:n},(_,i)=>a[Math.min(a.length-1,Math.floor(i*a.length/n))]);};
  const ground=resample(sequence.filter(id=>!t.enemies.get(id).isFlying));
  const air0=sequence.filter(id=>t.enemies.get(id).isFlying),air=air0.length?resample(air0):[];
  const n=ground.length+air.length, positions=new Set(air.map((_,i)=>Math.floor((i+.5)*n/air.length)));
  let gi=0,ai=0;sequence=Array.from({length:n},(_,i)=>positions.has(i)?air[ai++]:ground[gi++]);
 }
 const nAir=sequence.filter(id=>t.enemies.get(id).isFlying).length;
 if(sequence.some((id,i)=>i&&t.enemies.get(id).isFlying&&t.enemies.get(sequence[i-1]).isFlying))throw new Error('Air adjacency');
 const rawKill=sum(sequence.map(id=>t.enemies.get(id).reward));
 const desired=level===1?src.kill+src.reward:(src.kill+src.reward)*NEW_INCOME_FACTOR+incomeDelta;
 const roundReward=level===1?src.reward:roundRewardOverride??Math.round(src.reward*NEW_INCOME_FACTOR);
 if(desired<roundReward)throw Error('Wave reward exceeds allocated income');
 const rewardScale=level===1?1:(desired-roundReward)/rawKill;
 const es=new Map();
 for(const id of new Set(sequence)){
  const e=structuredClone(t.enemies.get(id));let air=e.isFlying!==0;
  e.hp*=air?hpAir:hpGround;e.speed*=air?speedAir:speedGround;e.reward*=rewardScale;
  for(const f of ['hp','speed','armor','reward'])if(!Number.isFinite(e[f]))throw new Error('Nonfinite '+id+' '+f);
  es.set(id,e);
 }
 let originalGroup=src.groups[0];
 if(src.groups.length!==1)throw new Error('Multiple groups need explicit implementation');
 t.groups=new Map([[originalGroup.id,{...originalGroup,EnemyIndexs:sequence,enemyInterval:Math.round(originalGroup.enemyInterval*gapScale)}]]);
 t.rounds=new Map([[src.round.id,{...src.round,rewardGold:roundReward}]]);
 t.enemies=es;t.scenes=new Map([[level,{...t.scenes.get(1),id:level,mapId:level,initialGold:100,initialHp:1000000,RoundList:[src.round.id]}]]);
 return {tables:t,sequence,n:sequence.length,nAir,reward:roundReward,kill:sum(sequence.map(id=>es.get(id).reward)),parameters:{countScale,hpGround,hpAir,speedGround,speedAir,gapScale,incomeDelta,roundRewardOverride}};
}

function routeFor(layout,levels,grid){const occ=new Uint8Array(grid.N);layout.forEach((t,i)=>{if(levels[i])occ[t.y*grid.cols+t.x]=1;});return {occ,route:runtimePath(grid,occ)};}
function exposure(layout,levels,grid,wave,airWeight=1,pathWeight=0){
 const {route}=routeFor(layout,levels,grid);if(route.length===0)return -Infinity;
 const towers=layout.flatMap((t,i)=>levels[i]?[{...t,row:tower(t.type,levels[i])}]:[]);
 let g=0,a=0;
 const evaluate=(x,y,air)=>{let slow=0,dps=0;for(const t of towers){if(air&&!t.row.canAttackAir)continue;if((t.x-x)**2+(t.y-y)**2>t.row.radius**2)continue;
  if(t.row.effectType===1)slow=Math.max(slow,t.row.effectValue);else dps+=t.row.power/t.row.cdSec*(air?t.row.airDamageScale:(t.row.effectType===3?2:1));}
  return dps/(1-slow);
 };
 for(let i=1;i<route.length;i++){let p=route[i-1],q=route[i];g+=evaluate((grid.xOf[p]+grid.xOf[q])/2,(grid.yOf[p]+grid.yOf[q])/2,false);}
 const sx=grid.xOf[grid.start],sy=grid.yOf[grid.start],ex=grid.xOf[grid.end],ey=grid.yOf[grid.end];
 let len=Math.hypot(ex-sx,ey-sy);for(let s=.25;s<len;s+=.5)a+=.5*evaluate(sx+(ex-sx)*s/len,sy+(ey-sy)*s/len,true);
 // This score only ranks candidate purchases; combat validation uses the time-step model.
 const es=wave.tables.enemies;let eg=0,ea=0;for(const id of wave.sequence){let e=es.get(id);if(e.isFlying)ea+=e.hp/(1-e.armor);else eg+=e.hp/(1-e.armor);}
 let completion=0;for(const col of new Set(layout.map(t=>t.x))){let ids=layout.map((t,i)=>t.x===col?i:-1).filter(i=>i>=0);if(ids.length>=4)completion+=(ids.filter(i=>levels[i]).length/ids.length)**2/(1+col/4);}
 return Math.log1p(g/Math.max(1,eg/Math.max(1,wave.n-wave.nAir)))* (1-wave.nAir/wave.n)+Math.log1p(a/Math.max(1,ea/Math.max(1,wave.nAir)))*(wave.nAir/wave.n)*airWeight+pathWeight*(Math.log(route.length)+completion*.2);
}

export function purchasePlan(layout,initialLevels,budget,grid,wave,{airWeight=1,pathWeight=0,extraUpgrades=false,completeTarget=false}={}){
 let levels=initialLevels.slice(),remaining=budget;const ops=[];
 for(let iter=0;iter<layout.length*3;iter++){
  const baseline=exposure(layout,levels,grid,wave,airWeight,pathWeight), candidates=[];
  const add=changes=>{
   let next=levels.slice(),price=0;for(const [i,to] of changes){if(to<=next[i])continue;price+=cost(layout[i].type,to)-cost(layout[i].type,next[i]);next[i]=to;}
   if(price<=0||price>remaining+1e-8)return;
   const value=exposure(layout,next,grid,wave,airWeight,pathWeight);if(!Number.isFinite(value))return;
   candidates.push({changes,next,price,gain:(value-baseline)/price,value});
  };
  for(let i=0;i<layout.length;i++){
   const cap=extraUpgrades?3:layout[i].cap;
   if(levels[i]<cap){add([[i,levels[i]+1]]);if(levels[i]+1<cap)add([[i,cap]]);}
  }
  for(const col of new Set(layout.map(t=>t.x))){let changes=[];layout.forEach((t,i)=>{if(t.x===col&&!levels[i])changes.push([i,1]);});if(changes.length>1)add(changes);}
  if(!candidates.length)break;
  candidates.sort((a,b)=>b.gain-a.gain||a.price-b.price);
  let best=candidates[0];if(best.gain<=0&&!completeTarget)break;
  // A macro is expanded into ordinary, paid build/upgrade operations.
  for(const [i,to] of best.changes){for(let lv=levels[i]+1;lv<=to;lv++){let t=layout[i];ops.push({i,x:t.x,y:t.y,family:t.type-1,type:lv===1?'build':'upgrade',level:lv,price:tower(t.type,lv).prices});}}
  levels=best.next;remaining-=best.price;
 }
 return {levels,ops,remaining,spent:budget-remaining};
}

export function stateFor(layout,levels,cash,wave,level,dt=.05){
 const t=wave.tables,grid=buildGrid(t.maps.get(level));
 const slots=layout.map((v,i)=>({...v,idx:v.y*grid.cols+v.x,family:v.type-1,state:'pending',tower:null,index:i}));
 const prep={levelId:level,name:'source-only',grid,scene:t.scenes.get(level),slots,layout:{}};
 const s=makeRunState(prep,t,{...DEFAULTS,dt,runtimeWaypoints:true,operationScript:[],maxSimSec:1800});s.gold=cash;
 for(let i=0;i<layout.length;i++)if(levels[i]){
  const sl=slots[i],row=tower(sl.type,levels[i]);
  if(!isLegalPlacement(grid,s.occ,sl.idx))throw new Error('Illegal confirmed layout '+JSON.stringify(sl));
  s.occ[sl.idx]=1;let tw={slot:sl,row,x:sl.x,y:sl.y,fireTimer:0,searchTimer:0,target:null};sl.tower=tw;sl.state='built';s.towers.push(tw);s.builtOrder.push(sl);
 }
 s.wallVersion++;s.routeCache.clear();return s;
}
export function simulateWave(layout,initialLevels,cash,wave,level,{dt=.05,plan=true,airWeight=1,pathWeight=0,extraUpgrades=false,fixedPurchasePlan=null}={}){
 let s=stateFor(layout,initialLevels,cash,wave,level,dt);
 const p=fixedPurchasePlan??(plan?purchasePlan(layout,initialLevels,cash+wave.kill,s.grid,wave,{airWeight,pathWeight,extraUpgrades}):{ops:[]});
 let oi=0;const metrics={ground:{maxAlive:0,maxEhp:0,minMargin:null,leaks:0},air:{maxAlive:0,maxEhp:0,minMargin:null,leaks:0}};
 let lastLeaks=0;
 while(s.k<Math.round(1800/dt)&&!s.done&&!s.lost){
  let funds=s.gold;
  while(oi<p.ops.length&&p.ops[oi].price<=Math.floor(funds+1e-5)){
   const op=p.ops[oi++];s.opts.operationScript.push({...op,timeSec:(s.k+1)*dt});funds-=op.price;
  }
  // Capture enemies about to reach the end, before stepOnce filters leaked units.
  const aliveBefore=s.enemies.slice();
  stepOnce(s);
  if(s.leaksTotal>lastLeaks){for(const e of aliveBefore)if(!e.alive&&e.hp>0)metrics[e.flying?'air':'ground'].leaks++;lastLeaks=s.leaksTotal;}
  let gs=0,as=0,ge=0,ae=0;
  for(const e of s.enemies){if(!Number.isFinite(e.hp)||!Number.isFinite(e.x)||!Number.isFinite(e.y))throw new Error('Nonfinite combat state');
   let remaining=e.flying?e.total-e.travelled:e.route.length-1-e.s;
   if(remaining<=3){if(e.flying){as++;ae+=e.hp/(1-e.armor);}else{gs++;ge+=e.hp/(1-e.armor);}}
  }
  metrics.ground.maxAlive=Math.max(metrics.ground.maxAlive,gs);metrics.ground.maxEhp=Math.max(metrics.ground.maxEhp,ge);
  metrics.air.maxAlive=Math.max(metrics.air.maxAlive,as);metrics.air.maxEhp=Math.max(metrics.air.maxEhp,ae);
 }
 for(const kill of s.kills){let m=metrics[kill.kind];m.minMargin=m.minMargin===null?kill.remaining:Math.min(m.minMargin,kill.remaining);}
 const finalLevels=s.slots.map(sl=>sl.tower?.row.level??0);
 if(s.scriptFailures.length)throw new Error('Purchase replay failed '+JSON.stringify(s.scriptFailures));
 return {metrics,leaks:s.leaksTotal,killed:s.killedTotal,spawned:s.spawnedTotal,completed:s.done,simSec:s.k*dt,
  startCash:cash,endCash:s.gold,spent:layoutCost(layout,finalLevels)-layoutCost(layout,initialLevels),levels:finalLevels,
  operations:s.operations,plannedPending:p.ops.length-oi,groundPath:runtimePath(s.grid,s.occ).length-1};
}

fs.mkdirSync(OUT,{recursive:true});
export const defenseScore=r=>r.leaks*1e9+(r.metrics.ground.maxAlive+r.metrics.air.maxAlive)*1e5+r.metrics.ground.maxEhp+r.metrics.air.maxEhp-10*Math.min(r.metrics.ground.minMargin??100,r.metrics.air.minMargin??100);
export function bestDefense(layout,levels,cash,wave,level,weights=[0,.5,2,8]){
 let best=null;
 for(const pathWeight of weights)for(const airWeight of [1,4]){
  let result=simulateWave(layout,levels,cash,wave,level,{airWeight,pathWeight});
  if(!best||defenseScore(result)<defenseScore(best)){best={...result,policy:{airWeight,pathWeight}};}
 }
 return best;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 let levels=L01.map(()=>0),cash=100,results=[];
 for(let w=1;w<=25;w++){
  const wave=makeWave(w);const result=bestDefense(L01,levels,cash,wave,1);
  levels=result.levels;cash=result.endCash;results.push({w,...result});
  console.log(JSON.stringify({w,leaks:result.leaks,ground:result.metrics.ground,air:result.metrics.air,spent:result.spent,cash,built:levels.filter(Boolean).length,path:result.groundPath}));
 }
 fs.writeFileSync(path.join(OUT,'l01-new-source-baseline.json'),JSON.stringify({sourceHashes:Object.fromEntries(Object.entries(audit.trustedSources).map(([k,v])=>[k,v.sha256])),layout:L01,cost:layoutCost(L01),L01_TOTAL,L02_FIRST4,results},null,2));
}
