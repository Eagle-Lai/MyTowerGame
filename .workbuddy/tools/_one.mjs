import {loadTables,runLevel,DEFAULTS} from './balance_sim.mjs';
const t=loadTables('../../Library/BalanceStage/all_profiles_v2/D01/ConfigJson');
const x=runLevel(1,t,{...DEFAULTS,dt:0.05});
console.log(JSON.stringify(x,null,2).slice(0,20000));
