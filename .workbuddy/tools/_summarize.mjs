import fs from 'node:fs';
import {loadTables,runLevel,DEFAULTS} from './balance_sim.mjs';
const base=loadTables();
const dirs=['D01','D02','D03','D04','D05','D06','D07','D08'];
for(const d of dirs){const t=loadTables(`Library/BalanceStage/all_profiles_v2/${d}/ConfigJson`);let pass=0,fail=0,first=[];for(let l=1;l<=30;l++){let x=runLevel(l,t,{...DEFAULTS,dt:0.05}); if(x.pass)pass++; else {fail++;first.push(`${l}:W${x.failWave??x.lastWave??'?'}:${x.reason??x.failReason??x.status??'fail'}`)}} console.log(d,{pass,fail,first:first.slice(0,8)});}
