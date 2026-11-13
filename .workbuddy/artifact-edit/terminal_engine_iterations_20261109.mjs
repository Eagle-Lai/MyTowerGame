import fs from 'node:fs';
import path from 'node:path';
import {ENGINE,request,l02Data,writeCandidate,replayRun,planL02} from './engine_terminal_design_20261109.mjs';
import {L02,sourceTables,protectedOpeningWave,makeWave,purchasePlan,cost,layoutCost} from './terminal_balance_20261109.mjs';
import {buildGrid} from '../tools/balance_sim.mjs';

// A topology alternative for the purchase search. It is an ordinary paid queue,
// not a gameplay override: the Unity verifier waits for actual earned money.
export function topologyPlan(parameters, columns=[1,3], pathWeight=.7, airWeight=1, prepOnly=false) {
 let levels=L02.map(()=>0),cash=100,operations=[],cursor=0;
 const grid=buildGrid(sourceTables().maps.get(2)),prefix=[];
 const add=(y,x,lv=1)=>{const i=L02.findIndex(t=>t.x===x&&t.y===y);if(i<0)throw Error('Not a screenshot slot');prefix.push([i,lv]);};
 const wall=col=>{for(const {t} of L02.map(t=>({t})).filter(o=>o.t.x===col).sort((a,b)=>Math.abs(a.t.y-4)-Math.abs(b.t.y-4)||a.t.y-b.t.y))add(t.y,t.x);};
 add(4,3);add(4,5);
 if(columns==='paired-walls'||columns==='maze-guns'){
  if(columns==='paired-walls'){
   add(4,3,2);add(4,3,3);add(4,7);add(4,7,2);add(4,7,3);
   add(4,5,2);add(4,5,3);add(2,3);add(2,3,2);add(2,3,3);
  }
  wall(1);wall(3);
  add(4,3,2);add(4,3,3);add(4,7);add(4,7,2);add(4,7,3);
  add(4,11);add(4,11,2);add(4,11,3);
  add(4,5,2);add(4,5,3);add(2,3,2);add(2,3,3);
  add(4,9);add(4,9,2);add(4,9,3);add(2,9);add(2,9,2);add(2,9,3);
  wall(5);wall(7);wall(9);wall(11);wall(13);wall(15);
 } else if(columns==='maze-staged'){
  wall(1);wall(3);
  add(4,3,2);add(4,3,3);
  add(4,7);add(4,7,2);add(4,7,3);
  add(4,5,2);add(4,5,3);
  add(2,3,2);add(2,3,3);
  wall(5);wall(7);
  add(4,9);add(4,9,2);add(4,9,3);
  add(4,11);add(4,11,2);add(4,11,3);
  wall(9);wall(11);
  add(4,13);add(4,13,2);add(4,13,3);
  wall(13);wall(15);
 } else if(columns==='wall-fire'){
  add(4,3,2);add(4,3,3);
  for(const y of [4,3,5,2,6,1,7,8])add(y,1);
  add(4,5,2);add(4,5,3);
  add(4,7);add(4,7,2);add(4,7,3);
  add(4,11);add(4,11,2);add(4,11,3);
  add(2,1,2);add(2,1,3);
 } else if(columns==='fire-first'){
  add(4,3,2);add(4,3,3);
  add(2,3);add(2,3,2);add(2,3,3);
  add(4,7);add(4,7,2);add(4,7,3);
  add(4,5,2);add(4,5,3);
  add(4,11);add(4,11,2);add(4,11,3);
  add(2,9);add(2,9,2);add(2,9,3);
  add(4,9);add(4,9,2);add(4,9,3);
 } else for(const col of columns) {
  const slots=L02.map((t,i)=>({t,i})).filter(o=>o.t.x===col).sort((a,b)=>Math.abs(a.t.y-4)-Math.abs(b.t.y-4)||a.t.y-b.t.y);
  for(const {t} of slots)add(t.y,t.x);
 }
 if(!['fire-first','wall-fire','maze-staged','paired-walls','maze-guns'].includes(columns)){
  add(4,3,2);add(4,3,3);add(4,7);add(4,7,2);add(4,7,3);
  add(4,5,2);add(4,5,3);
 }
 const push=(i,lv,w)=>{
  const t=L02[i];operations.push({waveOrdinal:w,timeMs:0,row:t.y,col:t.x,towerId:2000+(t.type-1)*3+lv,action:lv===1?'build':'upgrade'});
 };
 for(let w=1;w<=25;w++) {
  const wave=w<=4?protectedOpeningWave(w):makeWave(w,{level:2,...parameters[w-5]});
  let available=cash+(prepOnly&&w<25?0:wave.kill);
  while(cursor<prefix.length){
   const [i,lv]=prefix[cursor];if(levels[i]>=lv){cursor++;continue;}
   if(lv!==levels[i]+1)throw Error('Noncontiguous prefix upgrade');
   const price=cost(L02[i].type,lv)-cost(L02[i].type,levels[i]);
   if(price>available+1e-7)break;
   available-=price;levels[i]=lv;push(i,lv,w);cursor++;
  }
  if(cursor===prefix.length){
   const p=purchasePlan(L02,levels,available,grid,wave,{pathWeight,airWeight,completeTarget:w>=22});
   for(const op of p.ops)push(op.i,op.level,w);
   levels=p.levels;available=p.remaining;
   if(levels.every((lv,i)=>lv>=L02[i].cap)){
    const q=purchasePlan(L02,levels,available,grid,wave,{pathWeight,airWeight,extraUpgrades:true});
    for(const op of q.ops)push(op.i,op.level,w);levels=q.levels;available=q.remaining;
   }
  }
  cash=available+wave.reward+(prepOnly&&w<25?wave.kill:0);
 }
 return {operations,levels,cash,spent:layoutCost(L02,levels)};
}
export function createIteration(name,parameters,{columns=null,pathWeight=.7,airWeight=1,limit=25,prepOnly=false}={}){
 const {data,edits}=l02Data(parameters),scene=data.tbsceneinfo.find(x=>x.id===2);
 scene.initialHp=1000000;scene.RoundList=scene.RoundList.slice(0,limit);
 const dir=writeCandidate(name+'-data',data);
 const plan=columns?topologyPlan(parameters,columns,pathWeight,airWeight,prepOnly):planL02(parameters,pathWeight,airWeight);
 fs.writeFileSync(path.join(ENGINE,name+'-parameters.json'),JSON.stringify(parameters,null,2));
 fs.writeFileSync(path.join(ENGINE,name+'-manifest.json'),JSON.stringify({edits},null,2));
 const run=replayRun(2,dir,plan.operations.filter(o=>o.waveOrdinal<=limit),name);
 return {run,plan};
}
if(process.argv[2]==='opening-topology'){
 const ps=Array.from({length:21},()=>({countScale:1.5,hpGround:1.5,hpAir:3,speedGround:1.05,speedAir:1.05,gapScale:1}));
 const runs=[[1,3],[3,5],[1,3,5]].map(cols=>createIteration('topology-'+cols.join('-'),ps,{columns:cols,limit:5}).run);
 const r=request('opening-topology',runs),req=JSON.parse(fs.readFileSync(r.file));req.stepsPerUpdate=25;
 fs.writeFileSync(r.file,JSON.stringify(req,null,2));console.log(r);
}
if(process.argv[2]==='opening-fire'){
 const runs=[1,1.5,2].map(hp=>{
  const ps=Array.from({length:21},()=>({countScale:1.5,hpGround:hp,hpAir:3,speedGround:1.05,speedAir:1.05,gapScale:1}));
  return createIteration('fire-first-hp'+hp,ps,{columns:'fire-first',limit:5}).run;
 });
 const r=request('opening-fire',runs);console.log(r);
}
if(process.argv[2]==='prep-fire'){
 const runs=[.8,1,1.25].map(hp=>{
  const ps=Array.from({length:21},()=>({countScale:1.5,hpGround:hp,hpAir:2,speedGround:1.05,speedAir:1.05,gapScale:1}));
  return createIteration('prep-fire-hp'+hp,ps,{columns:'fire-first',limit:10,prepOnly:true}).run;
 });
 console.log(request('prep-fire',runs));
}
if(process.argv[2]==='full-r2'){
 const ps=Array.from({length:21},(_,i)=>{
  const w=i+5;
  return {countScale:1.5,hpGround:w===5?.74:w<15?.65:w<20?.8:w<25?1:1.5,
   hpAir:w===5?2:w<10?2.5:w===10?1.7:w<15?2:w<20?2.3:w<25?2.5:2.8,
   speedGround:1.05,speedAir:1.05,gapScale:1};
 });
 const item=createIteration('full-r2',ps,{columns:'fire-first',prepOnly:true});
 console.log(request('full-r2',[item.run]));console.log({cost:item.plan.spent,cash:item.plan.cash,levels:item.plan.levels});
}
if(process.argv[2]==='wall-check'){
 const runs=[1,1.5].map(hp=>{
  const ps=Array.from({length:21},()=>({countScale:1.5,hpGround:hp,hpAir:2.5,speedGround:1.05,speedAir:1.05,gapScale:1}));
  return createIteration('wall-check-hp'+hp,ps,{columns:'wall-fire',limit:5,prepOnly:true}).run;
 });
 console.log(request('wall-check',runs));
}
if(process.argv[2]==='throughput-opening'){
 const runs=[1,1.2,1.4].map(hp=>{
  const ps=Array.from({length:21},()=>({countScale:1,hpGround:hp,hpAir:2.2,speedGround:1.05,speedAir:1.05,gapScale:1.6}));
  return createIteration('throughput-opening-hp'+hp,ps,{columns:'fire-first',limit:5,prepOnly:true}).run;
 });
 console.log(request('throughput-opening',runs));
}
if(process.argv[2]==='full-r3'){
 const ps=Array.from({length:21},(_,i)=>{
  const w=i+5;
  return {countScale:1.5,hpGround:w===5?.74:w<15?.65:w<20?.5:w<25?.5:.5,
   hpAir:w===5?2:w<10?2.5:w===10?1.7:w<15?2:w<20?1.7:w===20?1.4:w<25?1.5:1.4,
   speedGround:1.05,speedAir:1.05,gapScale:1};
 });
 const item=createIteration('full-r3',ps,{columns:'fire-first',prepOnly:true});
 console.log(request('full-r3',[item.run]));
}
if(process.argv[2]==='summary'){
 const name=process.argv[3],dir=path.join(ENGINE,name);
 const status=JSON.parse(fs.readFileSync(path.join(dir,'status.json')));console.log(status);
 if(fs.existsSync(path.join(dir,'unity-results.json'))){
  const results=JSON.parse(fs.readFileSync(path.join(dir,'unity-results.json')));
  const pressure=JSON.parse(fs.readFileSync(path.join(dir,'pressure.json')));
  for(const result of results){
   console.log(JSON.stringify({profile:result.profileId,state:result.state,leaks:result.metrics.leaked,completed:result.metrics.completedWaveCount,finalGold:result.finalGold,pending:result.pendingOperations?.length,
    waves:pressure.find(r=>r.runId===result.metrics.runId)?.waves},null,2));
  }
 }
}
if(process.argv[2]==='throughput-r4'){
 const runs=[1,1.25,1.5].map(hp=>{
  const ps=Array.from({length:21},(_,i)=>{
   const w=i+5;
   return {countScale:1,hpGround:hp,hpAir:w<10?2.5:w<20?2:1.8,
    speedGround:1.05,speedAir:1.05,gapScale:1.6,
    incomeDelta:w===5?400:-20,roundRewardOverride:w===5?50:null};
  });
  return createIteration('throughput-r4-hp'+hp,ps,{columns:'fire-first',prepOnly:false}).run;
 });
 console.log(request('throughput-r4',runs));
}
if(process.argv[2]==='throughput-r5'){
 const variants=[{n:.4,hp:1,gap:1.6},{n:.6,hp:1,gap:1.8},{n:.6,hp:1.3,gap:2.2}];
 const runs=variants.map((v,j)=>{
  const ps=Array.from({length:21},(_,i)=>{
   const w=i+5;
   return {countScale:v.n,hpGround:v.hp,hpAir:w<10?2.5:w<20?2.4:2.2,
    speedGround:1.05,speedAir:1.05,gapScale:v.gap,
    incomeDelta:w===5?500:-25,roundRewardOverride:w===5?30:null};
  });
  return createIteration('throughput-r5-v'+j,ps,{columns:'fire-first',prepOnly:false}).run;
 });
 console.log(request('throughput-r5',runs));
}
if(process.argv[2]==='maze-opening-r6'){
 const runs=[];
 for(const columns of [[1,3],[1,3,5]])for(const hp of [1,1.5,2]){
  const ps=Array.from({length:21},(_,i)=>({countScale:1,hpGround:hp,hpAir:2.5,speedGround:1.05,speedAir:1.05,gapScale:1,
   incomeDelta:i===0?500:-25,roundRewardOverride:i===0?30:null}));
  runs.push(createIteration('maze-r6-'+columns.join('-')+'-hp'+hp,ps,{columns,limit:5}).run);
 }
 console.log(request('maze-opening-r6',runs));
}
if(process.argv[2]==='maze-staged-r7'){
 const runs=[1,1.5,2].map(hp=>{
  const ps=Array.from({length:21},(_,i)=>({countScale:1,hpGround:hp,hpAir:2.5,speedGround:1.05,speedAir:1.05,gapScale:1,
   incomeDelta:i===0?500:-25,roundRewardOverride:i===0?30:null}));
  return createIteration('maze-staged-r7-hp'+hp,ps,{columns:'maze-staged'}).run;
 });
 console.log(request('maze-staged-r7',runs));
}
if(process.argv[2]==='spaced-r8'){
 const runs=[2.5,3.5,5].map(gap=>{
  const ps=Array.from({length:21},(_,i)=>({countScale:1.15,hpGround:1.05,hpAir:2.5,speedGround:1.05,speedAir:1.05,gapScale:gap,
   incomeDelta:i===0?500:-25,roundRewardOverride:i===0?30:null}));
  return createIteration('spaced-r8-gap'+gap,ps,{columns:'fire-first',limit:gap===3.5?25:5}).run;
 });
 console.log(request('spaced-r8',runs));
}
if(process.argv[2]==='purchase-r9'){
 const runs=[];
 for(const columns of ['paired-walls','maze-guns'])for(const hp of [1,1.2,1.4]){
  const ps=Array.from({length:21},(_,i)=>({countScale:1.5,hpGround:hp,hpAir:2,speedGround:1.05,speedAir:1.05,gapScale:1,
   incomeDelta:i===0?500:-25,roundRewardOverride:i===0?30:null}));
  runs.push(createIteration('purchase-r9-'+columns+'-hp'+hp,ps,{columns,limit:5}).run);
 }
 console.log(request('purchase-r9',runs));
}
if(process.argv[2]==='frontloaded-r10'){
 const runs=[];
 for(const columns of ['paired-walls','maze-guns'])for(const hp of [1.2,1.5,1.8]){
  const ps=Array.from({length:21},(_,i)=>({countScale:1.5,hpGround:hp,hpAir:2.5,speedGround:1.05,speedAir:1.05,gapScale:1,
   incomeDelta:i===0?1000:-50,roundRewardOverride:i===0?30:Math.min(30,makeWave(i+5,{level:2}).reward)}));
  runs.push(createIteration('frontloaded-r10-'+columns+'-hp'+hp,ps,{columns,limit:5}).run);
 }
 console.log(request('frontloaded-r10',runs));
}
if(process.argv[2]==='full-r11'){
 const ps=Array.from({length:21},(_,i)=>{const w=i+5;return {countScale:.6,hpGround:1,hpAir:w<15?2.5:2.8,speedGround:1.05,speedAir:1.05,gapScale:3.5,
  incomeDelta:w===5?800:-40,roundRewardOverride:w===5?30:null};});
 const item=createIteration('full-r11',ps,{columns:'maze-guns',prepOnly:false});
 console.log(request('full-r11',[item.run]));
}
if(process.argv[2]==='full-r12'){
 const runs=[.6,1].map(n=>{
  const ps=Array.from({length:21},(_,i)=>{const w=i+5;return {countScale:n,hpGround:w===5?1.1:w<15?1.5:w<20?1.3:1.15,
   hpAir:w===5?3.2:w<15?6:w<20?5.5:4.5,speedGround:w<20?1.05:.65,speedAir:1.05,gapScale:4,
   incomeDelta:w===5?800:-40,roundRewardOverride:w===5?30:null};});
  return createIteration('full-r12-n'+n,ps,{columns:'maze-guns'}).run;
 });console.log(request('full-r12',runs));
}
