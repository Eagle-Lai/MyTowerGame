import fs from 'node:fs';
import path from 'node:path';
import {L01,OUT,makeWave,simulateWave,defenseScore,layoutCost,L01_TOTAL,L02_FIRST4} from './terminal_balance_20261109.mjs';
let beam=[{levels:L01.map(()=>0),cash:100,leaks:0,results:[]}];
for(let w=1;w<=25;w++){
 let pool=[],seen=new Set();const wave=makeWave(w);
 for(const state of beam)for(const pathWeight of [0,.5,2,8,40])for(const airWeight of [.25,1,4,16]){
  const r=simulateWave(L01,state.levels,state.cash,wave,1,{airWeight,pathWeight});
  const key=r.levels.join(',');let leaks=state.leaks+r.leaks;
  const candidate={levels:r.levels,cash:r.endCash,leaks,results:[...state.results,{w,...r,policy:{airWeight,pathWeight}}]};
  // Deduplicate below after sorting so no weaker path can crowd out an affordable one.
  pool.push({key,candidate,score:leaks*1e10+defenseScore(r)});
 }
 pool.sort((a,b)=>a.score-b.score||b.candidate.cash-a.candidate.cash);
 beam=[];for(const p of pool){if(seen.has(p.key))continue;seen.add(p.key);beam.push(p.candidate);if(beam.length>=10)break;}
 console.log(JSON.stringify({w,states:beam.length,bestLeaks:beam[0].leaks,waveLeaks:beam[0].results.at(-1).leaks,cash:beam[0].cash,path:beam[0].results.at(-1).groundPath}));
 fs.writeFileSync(path.join(OUT,'l01-purchase-search-progress.json'),JSON.stringify({w,beam},null,2));
}
fs.writeFileSync(path.join(OUT,'l01-new-source-baseline.json'),JSON.stringify({layout:L01,cost:layoutCost(L01),L01_TOTAL,L02_FIRST4,leaks:beam[0].leaks,results:beam[0].results,method:'Beam search, 10 states, 20 geometry-ranked purchase policies; actual sequential affordability and combat evaluation; not a proof of global optimum.'},null,2));
