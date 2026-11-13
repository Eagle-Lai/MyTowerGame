import fs from 'node:fs';
import path from 'node:path';
import {L01,L02,OUT,BASE,makeWave,protectedOpeningWave,sourceTables,rows,purchasePlan} from './terminal_balance_20261109.mjs';
import {buildGrid} from '../tools/balance_sim.mjs';
export const ENGINE=path.join(OUT,'engine');fs.mkdirSync(ENGINE,{recursive:true});
const audit=JSON.parse(fs.readFileSync('Library/BalanceStage/trusted-input-audit-20261109/trusted-inputs.json','utf8'));
const root='Assets/ConfigJson';
const names=fs.readdirSync(root).filter(n=>n.endsWith('.json')&&n.startsWith('tb'));
export function transportBase(){
 const data=Object.fromEntries(names.map(n=>[n.slice(0,-5),JSON.parse(fs.readFileSync(path.join(root,n),'utf8').replace(/^\uFEFF/,''))]));
 // Untrusted other levels are copied only as untouched transport dependencies.
 for(const name of ['SceneInfo','LevelMap','EnemyData','EnemyList','RoundData','TowerInfo','BulletData','LevelRules']){
  let key='tb'+name.toLowerCase(), original=new Map(data[key].map(r=>[r.id,r]));
  const fresh=rows(audit.trustedSources,name).map(r=>{
   let out={...original.get(r.id)};
   for(const [f,v] of Object.entries(r)){
    if(v===null)continue;
    if(Array.isArray(out[f]))out[f]=String(v).split(f==='cells'?'|':',').filter(Boolean).map(x=>f==='cells'?x:Number(x));
    else if(out[f]&&typeof out[f]==='object')out[f]=Object.fromEntries(['x','y','z'].map((k,i)=>[k,Number(String(v).split(',')[i])]));
    else out[f]=v;
   }return out;
  });
  const ids=new Set(fresh.map(r=>r.id));data[key]=data[key].filter(r=>!ids.has(r.id)).concat(fresh);
 }
 return data;
}
export function writeCandidate(name,data){const dir=path.join(ENGINE,name);fs.mkdirSync(dir,{recursive:true});for(const [k,v]of Object.entries(data))fs.writeFileSync(path.join(dir,k+'.json'),JSON.stringify(v));return path.resolve(dir).replaceAll('\\','/');}
export function request(name,runs){
 const out=path.resolve(ENGINE,name).replaceAll('\\','/');fs.mkdirSync(out,{recursive:true});
 const req={output:out,stepSeconds:.05,stepsPerUpdate:200,keepPlaying:false,capturePressure:true,captureOutcomes:true,maxLevelSeconds:10000,suppressPresentation:true,batchTimeoutSeconds:7200,runs};
 const file=path.resolve(ENGINE,name+'-request.json').replaceAll('\\','/');fs.writeFileSync(file,JSON.stringify(req,null,2));
 const args={action:'execute',code:`FTProject.EditorTools.TerminalPressureProbe.Arm("${out}/pressure.json"); FTProject.EditorTools.BalancePlayModeVerifier.StartBatch("${file}"); return "Started ${name}";`};
 fs.writeFileSync(path.join(ENGINE,name+'-start.json'),JSON.stringify(args));return {file,out};
}
export function runPolicy(levelId,layout,dir,pw,aw,profile){return {profileId:profile,levelId,strategy:'terminal-search',speed:1,candidateDirectory:dir,layout,pathWeight:pw,airWeight:aw,captureStages:false,screenshots:false,wallTimeoutSeconds:1200};}
export function replayRun(levelId,dir,operations,profile){
 const operationsPath=path.resolve(ENGINE,profile+'-operations.json').replaceAll('\\','/');
 fs.writeFileSync(operationsPath,JSON.stringify(operations,null,2));
 return {profileId:profile,levelId,strategy:'replay',speed:1,candidateDirectory:dir,operationsPath,waitForFunds:true,carryOperations:true,captureStages:false,screenshots:false,wallTimeoutSeconds:3600};
}
export function planL02(parameters,pw=2,aw=1){
 let levels=L02.map(()=>0),cash=100,ops=[];
 const grid=buildGrid(sourceTables().maps.get(2));
 for(let w=1;w<=25;w++){
  let wave=w<=4?protectedOpeningWave(w):makeWave(w,{level:2,...parameters[w-5]});
  let p=purchasePlan(L02,levels,cash+wave.kill,grid,wave,{pathWeight:pw,airWeight:aw,completeTarget:true});
  if(p.levels.every((lv,i)=>lv>=L02[i].cap)){
   const q=purchasePlan(L02,p.levels,p.remaining,grid,wave,{pathWeight:pw,airWeight:aw,extraUpgrades:true});
   p.ops.push(...q.ops);p.levels=q.levels;p.remaining=q.remaining;
  }
  ops.push(...p.ops.map(o=>({waveOrdinal:w,timeMs:0,row:o.y,col:o.x,towerId:2000+o.family*3+o.level,action:o.type})));
  levels=p.levels;cash=p.remaining+wave.reward;
 }
 return {operations:ops,levels,cash};
}
export function l02Data(parameters){
 let data=transportBase();const p=audit.protectedCurrentL02NotDesignInput;
 const l2scene=data.tbsceneinfo.find(x=>x.id===2), roundIds=l2scene.RoundList;
 const oldE=new Map(data.tbenemydata.map(x=>[x.id,x]));let edits=[];
 for(let w=5;w<=25;w++){
  const config=makeWave(w,{level:2,...parameters[w-5]}),rid=roundIds[w-1],round=data.tbrounddata.find(x=>x.id===rid),gid=round.EnemyIndexs[0],group=data.tbenemylist.find(x=>x.id===gid);
  if(round.EnemyIndexs.length!==1)throw Error('Expected one group');
  const existing=[...new Set(group.EnemyIndexs)].map(id=>oldE.get(id));
  const map=new Map();for(const e of config.tables.enemies.values()){
   const old=existing.find(x=>x.resName===e.resName&&x.isFlying===e.isFlying&&x.type===e.type);
   if(!old)throw Error('No matching existing L02 variant '+e.id+' '+w+' '+e.resName);
   map.set(e.id,old.id);for(const f of ['hp','speed','armor','reward']){edits.push({table:'EnemyData',id:old.id,field:f,old:old[f],value:e[f]});old[f]=e[f];}
  }
  const g=config.tables.groups.values().next().value;
  edits.push({table:'EnemyList',id:gid,field:'EnemyIndexs',old:group.EnemyIndexs.slice(),value:config.sequence.map(id=>map.get(id))});group.EnemyIndexs=config.sequence.map(id=>map.get(id));
  edits.push({table:'EnemyList',id:gid,field:'enemyInterval',old:group.enemyInterval,value:g.enemyInterval});group.enemyInterval=g.enemyInterval;
  edits.push({table:'RoundData',id:rid,field:'rewardGold',old:round.rewardGold,value:config.reward});round.rewardGold=config.reward;
 }
 return {data,edits};
}
if(process.argv[2]==='l01'){
 let data=transportBase();data.tbsceneinfo.find(x=>x.id===1).initialHp=1000000;
 const dir=writeCandidate('l01-diagnostic-only',data),runs=[];
 // HP-only diagnostic override keeps the run observable after leakage. Source tables and rewards stay unchanged.
 for(const [pw,aw] of [[2,1],[2,8],[8,1]])runs.push(runPolicy(1,L01,dir,pw,aw,`L01-p${pw}-a${aw}`));
 console.log(request('l01-search-v2',runs));
}
if(process.argv[2]==='l02-seed'){
 const parameters=Array.from({length:21},()=>({countScale:1.3,hpGround:1.8,hpAir:2.5,speedGround:1.15,speedAir:Math.sqrt(15/12),gapScale:.85}));
 const {data,edits}=l02Data(parameters);
 data.tbsceneinfo.find(x=>x.id===2).initialHp=1000000; // diagnostic only, never a source-table change
 const dir=writeCandidate('l02-seed-diagnostic-only',data);
 fs.writeFileSync(path.join(ENGINE,'l02-seed-parameters.json'),JSON.stringify(parameters,null,2));
 fs.writeFileSync(path.join(ENGINE,'l02-seed-edit-preview.json'),JSON.stringify(edits,null,2));
 console.log(request('l02-seed',[runPolicy(2,L02,dir,2,1,'L02-seed-p2-a1'),runPolicy(2,L02,dir,8,1,'L02-seed-p8-a1')]));
}
if(process.argv[2]==='l01-replay'){
 let data=transportBase();data.tbsceneinfo.find(x=>x.id===1).initialHp=1000000;
 const dir=writeCandidate('l01-diagnostic-only',data);
 const beam=JSON.parse(fs.readFileSync(path.join(OUT,'l01-purchase-search-progress.json'),'utf8')).beam;
 const runs=[0].map(i=>{
  const ops=beam[i].results.flatMap(r=>r.operations.map(o=>({waveOrdinal:r.w,timeMs:0,row:o.y,col:o.x,towerId:o.towerId,action:o.type})));
  return replayRun(1,dir,ops,'L01-queue-'+i);
 });
 for(const [pw,aw] of [[2,8],[8,1]]){
  let levels=L01.map(()=>0),cash=100,ops=[];const grid=buildGrid(sourceTables().maps.get(1));
  for(let w=1;w<=25;w++){
   const wave=makeWave(w),p=purchasePlan(L01,levels,cash+wave.kill,grid,wave,{pathWeight:pw,airWeight:aw});
   ops.push(...p.ops.map(o=>({waveOrdinal:w,timeMs:0,row:o.y,col:o.x,towerId:1000+o.family*3+o.level,action:o.type})));
   levels=p.levels;cash=p.remaining+wave.reward;
  }
  runs.push(replayRun(1,dir,ops,`L01-queue-p${pw}-a${aw}`));
 }
 console.log(request('l01-queue-search',runs));
}
if(process.argv[2]==='l02-replay'){
 const parameters=Array.from({length:21},()=>({countScale:1.5,hpGround:1.5,hpAir:3,speedGround:1.05,speedAir:1.05,gapScale:1}));
 const {data}=l02Data(parameters);data.tbsceneinfo.find(x=>x.id===2).initialHp=1000000;
 const dir=writeCandidate('l02-seed-diagnostic-only',data);
 fs.writeFileSync(path.join(ENGINE,'l02-seed-parameters.json'),JSON.stringify(parameters,null,2));
 const runs=[[0,1]].map(([pw,aw])=>replayRun(2,dir,planL02(parameters,pw,aw).operations,`L02-seed-queue-p${pw}-a${aw}`));
 console.log(request('l02-queue-seed',runs));
}
if(process.argv[2]==='queue-l02'){
 const file=path.resolve(ENGINE,'l02-queue-seed-request.json').replaceAll('\\','/');
 const code=`var t = typeof(FTProject.EditorTools.BalancePlayModeVerifier);
 var f = t.GetField("Runs", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic);
 var runs = (System.Collections.Generic.List<SimpleJSON.JSONNode>)f.GetValue(null);
 if(runs.Count != 3) return "Unexpected run count";
 runs.RemoveRange(1,2);
 var req = SimpleJSON.JSON.Parse(System.IO.File.ReadAllText("${file}"));
 runs.Add(req["runs"][1]); runs.Add(req["runs"][2]);
 return "Kept current L01 reference, queued two L02 candidates";`;
 fs.writeFileSync(path.join(ENGINE,'queue-l02-now.json'),JSON.stringify({action:'execute',code}));
}
if(process.argv[2]==='probe-cost'){
 const code=`var t=typeof(FTProject.EditorTools.BalancePlayModeVerifier);
 var f=t.GetField("StepCosts",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);
 var steps=(System.Collections.Generic.List<double>)f.GetValue(null);
 double total=0; int n=System.Math.Min(steps.Count,1000);
 for(int i=steps.Count-n;i<steps.Count;i++)total+=steps[i];
 return new { count=steps.Count, meanLast1000Ms=n>0?total/n:0, reentry=FTProject.BaseTower.EvidenceTrackReentry, memory=System.GC.GetTotalMemory(false), logTrace=UnityEngine.Application.GetStackTraceLogType(UnityEngine.LogType.Log).ToString() };`;
 fs.writeFileSync(path.join(ENGINE,'probe-cost.json'),JSON.stringify({action:'execute',code}));
}
if(process.argv[2]==='l01-resume'){
 const previous=JSON.parse(fs.readFileSync(path.join(ENGINE,'l01-queue-search/unity-results.json'),'utf8'))[0];
 const context=previous.storagePath.replaceAll('\\','/').split('/').at(-2);
 if(!/^replay-[0-9a-f]{32}$/.test(context))throw Error('Invalid isolated storage context');
 const planned=JSON.parse(fs.readFileSync(path.join(ENGINE,'L01-queue-0-operations.json'),'utf8'));
 const done=new Set(previous.operations.map(o=>o.sourceIndex));
 const pending=planned.filter((o,i)=>!done.has(i));
 const run=replayRun(1,path.resolve(ENGINE,'l01-diagnostic-only').replaceAll('\\','/'),pending,'L01-resume-W24');run.resumeSaved=true;
 const res=request('l01-current-session-resume',[run]);
 const req=JSON.parse(fs.readFileSync(res.file,'utf8'));req.resumeStorageContext=context;
 fs.writeFileSync(res.file,JSON.stringify(req,null,2));console.log(res);
}
if(process.argv[2]==='l01-finish'){
 const prior=JSON.parse(fs.readFileSync(path.join(ENGINE,'l01-current-session-resume/unity-results.json'),'utf8'))[0];
 const planned=JSON.parse(fs.readFileSync(path.join(ENGINE,'L01-resume-W24-operations.json'),'utf8'));
 const done=new Set(prior.operations.map(o=>o.sourceIndex));
 const pending=planned.filter((o,i)=>!done.has(i));
 const run=replayRun(1,path.resolve(ENGINE,'l01-diagnostic-only').replaceAll('\\','/'),pending,'L01-resume-W25');run.resumeSaved=true;
 const res=request('l01-current-session-finish',[run]);const req=JSON.parse(fs.readFileSync(res.file,'utf8'));
 req.resumeStorageContext=prior.storagePath.replaceAll('\\','/').split('/').at(-2);req.maxLevelSeconds=1000000;
 fs.writeFileSync(res.file,JSON.stringify(req,null,2));console.log(res);
}
if(process.argv[2]==='combined'){
 const l1request=JSON.parse(fs.readFileSync(path.join(ENGINE,'l01-queue-search-request.json'),'utf8'));
 const l2request=JSON.parse(fs.readFileSync(path.join(ENGINE,'l02-queue-seed-request.json'),'utf8'));
 const r=request('engine-source-calibration',[l1request.runs[0],l2request.runs[0]]);
 const req=JSON.parse(fs.readFileSync(r.file,'utf8'));req.stepSeconds=.1;req.stepsPerUpdate=25;fs.writeFileSync(r.file,JSON.stringify(req,null,2));console.log(r);
}
if(process.argv[2]==='l02-opening-search'){
 const parameters=JSON.parse(fs.readFileSync(path.join(ENGINE,'l02-seed-parameters.json'),'utf8'));
 const {data}=l02Data(parameters);let scene=data.tbsceneinfo.find(x=>x.id===2);scene.initialHp=1000000;scene.RoundList=scene.RoundList.slice(0,5);
 const dir=writeCandidate('l02-opening-search-diagnostic',data);
 const runs=[];
 for(const pw of [.05,.15,.35,.7,1]){
  const plan=planL02(parameters,pw,1);runs.push(replayRun(2,dir,plan.operations.filter(o=>o.waveOrdinal<=5),`L02-opening-p${pw}`));
 }
 const r=request('l02-opening-search',runs);const req=JSON.parse(fs.readFileSync(r.file,'utf8'));req.stepsPerUpdate=25;
 fs.writeFileSync(r.file,JSON.stringify(req,null,2));console.log(r);
}
