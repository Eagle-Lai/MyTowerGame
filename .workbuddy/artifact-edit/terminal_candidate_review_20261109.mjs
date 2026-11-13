import fs from 'node:fs';
import path from 'node:path';
import {ENGINE} from './engine_terminal_design_20261109.mjs';
import {BASE,L02,layoutCost,makeWave,rows} from './terminal_balance_20261109.mjs';

const name=process.argv[2]||'full-r2',dir=path.join(ENGINE,name);
const pressure=JSON.parse(fs.readFileSync(path.join(dir,'pressure.json')));
const reference=JSON.parse(fs.readFileSync(path.join(ENGINE,'consistent-reference-r1/l01-complete-reference-pressure.json')));
const params=JSON.parse(fs.readFileSync(path.join(ENGINE,name+'-parameters.json')));
let results=[];
if(fs.existsSync(path.join(dir,'unity-results.json')))results=JSON.parse(fs.readFileSync(path.join(dir,'unity-results.json')));
const candidate=results.length?pressure.find(x=>x.runId===results[0].metrics.runId):pressure.at(-1);
const lines=[];
for(let w=5;w<=25;w++){
 const a=reference.waves.find(x=>x.wave===w),b=candidate?.waves.find(x=>x.wave===w);
 if(!b)continue;
 const p=params[w-5],wave=makeWave(w,{level:2,...p});
 lines.push({wave:w,L01N:BASE[w-1].ids.length,L02N:wave.n,L02AirN:wave.nAir,...p,
  ...Object.fromEntries(['ground','air'].flatMap(k=>['maxAlive','maxEhp','minMargin','leaks'].flatMap(f=>[[`L01_${k}_${f}`,a[k][f]],[`L02_${k}_${f}`,b[k][f]]])))});
}
const completed=results[0]?.metrics.completedWaveCount;
console.log(JSON.stringify({name,completed,state:results[0]?.state,leaks:results[0]?.metrics.leaked,
 finalGold:results[0]?.finalGold,pending:results[0]?.pendingOperations?.length,
 cost:layoutCost(L02),waveRows:lines.map(r=>({w:r.wave,g:[r.L02_ground_maxAlive,Math.round(r.L02_ground_maxEhp),+r.L02_ground_minMargin.toFixed(2),r.L02_ground_leaks],
 a:[r.L02_air_maxAlive,Math.round(r.L02_air_maxEhp),+r.L02_air_minMargin.toFixed(2),r.L02_air_leaks]}))},null,2));
fs.writeFileSync(path.join(dir,'comparison.json'),JSON.stringify({name,completed,referenceRunId:reference.runId,candidateRunId:candidate?.runId,rows:lines},null,2));
if(lines.length){const cols=Object.keys(lines[0]);fs.writeFileSync(path.join(dir,'comparison.csv'),'\uFEFF'+[cols.join(','),...lines.map(r=>cols.map(c=>r[c]).join(','))].join('\r\n'));}
if(process.argv.includes('--manifest')){
 const source=JSON.parse(fs.readFileSync(path.join(ENGINE,name+'-manifest.json')));
 const audit=JSON.parse(fs.readFileSync('Library/BalanceStage/trusted-input-audit-20261109/trusted-inputs.json'));
 const tables=new Map(['EnemyData','EnemyList','RoundData'].map(n=>[n,new Map(rows(audit.protectedCurrentL02NotDesignInput,n).map(r=>[r.id,r]))]));
 for(const e of source.edits){
  const old=tables.get(e.table).get(e.id)[e.field];e.old=Array.isArray(e.value)?String(old).split(',').map(Number):old;
 }
 source.edits=source.edits.filter(e=>JSON.stringify(e.old)!==JSON.stringify(e.value));
 fs.writeFileSync(path.join(dir,'source-cell-manifest.json'),JSON.stringify(source,null,2));
 console.log({actualChangedCells:source.edits.length});
}
