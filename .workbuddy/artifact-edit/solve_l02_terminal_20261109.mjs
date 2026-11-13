import fs from 'node:fs';
import path from 'node:path';
import {buildGrid,runtimePath} from '../tools/balance_sim.mjs';
import {L01,L02,OUT,BASE,sourceTables,layoutCost,makeWave,protectedOpeningWave,simulateWave,purchasePlan,bestDefense,defenseScore,L02_FIRST4} from './terminal_balance_20261109.mjs';
const baseline=JSON.parse(fs.readFileSync(path.join(OUT,'l01-new-source-baseline.json'),'utf8'));
if(baseline.results.length!==25)throw new Error('Incomplete new source baseline');
const routeLength=layout=>{const t=sourceTables(),g=buildGrid(t.maps.get(layout===L01?1:2)),o=new Uint8Array(g.N);layout.forEach(s=>o[s.y*g.cols+s.x]=1);return runtimePath(g,o).length-1;};
const mapRatio=routeLength(L02)/routeLength(L01);
const countSeed=Math.sqrt(layoutCost(L02)/layoutCost(L01));
const speedGround=Math.sqrt(mapRatio),speedAir=Math.sqrt(15/12);
const pressure=(m,mean)=> m.leaks?1e6+m.leaks*1e3:(m.maxAlive?m.maxAlive+ m.maxEhp/mean*.1+(3-(m.minMargin??3))/3:-(m.minMargin??100));
const allResults=[];
let levels=L02.map(()=>0),cash=100;
for(let w=1;w<=4;w++){
 let wave=protectedOpeningWave(w),r=bestDefense(L02,levels,cash,wave,2,[0,.5,2,8,40]);
 if(r.leaks)throw new Error('Protected opening not cleared by searched purchase policies');
 allResults.push({w,protected:true,...r});levels=r.levels;cash=r.endCash;
}
if(Math.abs(cash+layoutCost(L02,levels)-L02_FIRST4)>.001)throw new Error('Opening economy reconciliation failed');
for(let w=5;w<=25;w++){
 const reference=baseline.results[w-1],initialLevels=levels.slice(),initialCash=cash,candidates=[];
 const countChoices=[1.15,countSeed,1.5];
 for(const countScale of countChoices){
  const gapScale=Math.sqrt(mapRatio)/countScale;
  const p={level:2,countScale,speedGround,speedAir,gapScale,hpGround:.5,hpAir:.5};
  const seed=makeWave(w,p),grid=buildGrid(seed.tables.maps.get(2));
  let strongest=bestDefense(L02,initialLevels,initialCash,seed,2,[0,2,8]);
  let policy=strongest.policy;
  let plan=purchasePlan(L02,initialLevels,initialCash+seed.kill,grid,seed,policy);
  const mean={ground:0,air:0},cnt={ground:0,air:0};
  const baselineEnemies=sourceTables().enemies;
  for(const id of BASE[w-1].ids){let e=baselineEnemies.get(id),kind=e.isFlying?'air':'ground';mean[kind]+=e.hp/(1-e.armor);cnt[kind]++;}
  for(const kind of ['ground','air'])mean[kind]/=Math.max(1,cnt[kind]);
  const target={ground:pressure(reference.metrics.ground,mean.ground),air:pressure(reference.metrics.air,mean.air)};
  let hpGround=.25,hpAir=.25,r;
  const run=()=>simulateWave(L02,initialLevels,initialCash,makeWave(w,{...p,hpGround,hpAir}),2,{...policy,fixedPurchasePlan:plan});
  // Alternate the two target layers because air targeting consumes normal-tower fire from ground.
  for(let pass=0;pass<2;pass++)for(const kind of ['ground','air']){
   if(!cnt[kind])continue;
   let low=.01,high=12;
   for(let iter=0;iter<11;iter++){
    let mid=(low+high)/2;if(kind==='ground')hpGround=mid;else hpAir=mid;
    let rr=run();let q=pressure(rr.metrics[kind],mean[kind]);
    if(rr.metrics[kind].leaks===0&&q<=target[kind])low=mid;else high=mid;
   }
   if(kind==='ground')hpGround=low;else hpAir=low;
  }
  r=run();
  // If coupling created a leak, back off only until the hard zero-leak constraint is restored.
  for(let safe=0;r.leaks&&safe<30;safe++){
   if(r.metrics.ground.leaks)hpGround*=.98;if(r.metrics.air.leaks)hpAir*=.98;r=run();
  }
  if(r.leaks||!r.completed)continue;
  const errors={};let error=0;
  for(const kind of ['ground','air']){
   const a=r.metrics[kind],b=reference.metrics[kind];
   errors[kind]={count:a.maxAlive-b.maxAlive,ehp:a.maxEhp-b.maxEhp,margin:a.minMargin===null||b.minMargin===null?null:a.minMargin-b.minMargin};
   error+=Math.abs(a.maxAlive-b.maxAlive)+Math.abs(a.maxEhp-b.maxEhp)/Math.max(mean[kind],b.maxEhp,1)+Math.abs((a.minMargin??0)-(b.minMargin??0))/3;
  }
  // A close pressure match is primary. Quantity and HP growth break near ties only.
  candidates.push({w,countScale,hpGround,hpAir,gapScale,speedGround,speedAir,policy,result:r,errors,error,
   score:error-.01*Math.log(countScale*hpGround*hpAir),sequence:makeWave(w,{...p,hpGround,hpAir}).sequence,
   reward:seed.reward,kill:seed.kill,mean,referenceMetrics:reference.metrics});
 }
 candidates.sort((a,b)=>a.score-b.score);
 if(!candidates.length)throw new Error('No zero-leak candidate at W'+w);
 const chosen=candidates[0];levels=chosen.result.levels;cash=chosen.result.endCash;allResults.push(chosen);
 console.log(JSON.stringify({w,n:chosen.sequence.length,hpg:chosen.hpGround,hpa:chosen.hpAir,gap:BASE[w-1].groups[0].enemyInterval*chosen.gapScale,metrics:chosen.result.metrics,error:chosen.error,cash,path:chosen.result.groundPath}));
 fs.writeFileSync(path.join(OUT,'l02-solve-progress.json'),JSON.stringify({w,mapRatio,countSeed,results:allResults},null,2));
}
fs.writeFileSync(path.join(OUT,'l02-provisional-design.json'),JSON.stringify({mapRatio,countSeed,totalIncome:cash+layoutCost(L02,levels),cost:layoutCost(L02),results:allResults},null,2));
