import test from 'node:test';
import assert from 'node:assert/strict';
import {L01,L02,sourceTables,layoutCost,makeWave,simulateWave,L01_TOTAL,L02_FIRST4,stateFor} from './terminal_balance_20261109.mjs';
import {normalizeTowerRows,towerAct,stepOnce,makeRunState,buildGrid,runtimePath} from '../tools/balance_sim.mjs';
test('confirmed screenshot inventories and current source cumulative prices reconcile',()=>{
 assert.equal(L01.length,38);assert.equal(L02.length,64);assert.equal(layoutCost(L01),4010);assert.equal(layoutCost(L02),6887);
 assert.ok(Math.abs(L01_TOTAL-4138)<.001);assert.ok(Math.abs(L02_FIRST4-897.91032)<.00001);
});
test('source-only full layouts preserve both endpoint connections',()=>{
 for(const [level,layout] of [[1,L01],[2,L02]]){let g=buildGrid(sourceTables().maps.get(level)),occ=new Uint8Array(g.N);layout.forEach(t=>occ[t.y*g.cols+t.x]=1);assert.ok(runtimePath(g,occ).length>1);}
});
test('missing optional simulator overrides do not turn final-wave HP into NaN',()=>{
 let w=makeWave(5),t=w.tables,g=buildGrid(t.maps.get(1));
 const st=makeRunState({levelId:1,name:'test',grid:g,scene:t.scenes.get(1),slots:[],layout:{}},t,{operationScript:[]});
 stepOnce(st);assert.ok(st.enemies.length>0);assert.ok(Number.isFinite(st.enemies[0].hp));assert.equal(st.opts.ehpScale,1);
});
test('L01 normal tower level 3 uses its actual 1.1 air damage multiplier',()=>{
 let w=makeWave(5),s=stateFor(L01,L01.map(()=>0),0,w,1),row=normalizeTowerRows(w.tables).get(1003);
 let e={alive:true,flying:true,hp:100,armor:0,id:1,x:0,y:0,travelled:0};s.enemies.push(e);
 towerAct(s,{row,x:0,y:0,searchTimer:0,fireTimer:row.cdSec-.05,target:e});
 assert.ok(Math.abs(e.hp-(100-13*1.1))<1e-9);
});
test('resampling always uses isFlying and isolates flights, including wave boundaries',()=>{
 for(const countScale of [1,1.15,1.3,1.5,1.75]){
  let previousAir=false;
  for(let n=5;n<=25;n++){let w=makeWave(n,{level:2,countScale});for(const id of w.sequence){let air=w.tables.enemies.get(id).isFlying!==0;assert.ok(!(air&&previousAir));previousAir=air;}}
 }
});
test('combat accounting pays only earned cash and records every enemy outcome',()=>{
 let w=makeWave(5,{level:2,countScale:1.15,hpGround:.5,hpAir:.5});let r=simulateWave(L02,L02.map(()=>0),897.91032,w,2,{pathWeight:2});
 assert.ok(r.completed);assert.equal(r.spawned,w.n);assert.equal(r.killed+r.leaks,w.n);
 for(const op of r.operations){assert.ok(op.goldBefore+1e-5>=op.price);assert.ok(op.goldAfter>=0);}
 for(const m of Object.values(r.metrics)){assert.ok(Number.isFinite(m.maxEhp));if(m.minMargin!==null)assert.ok(Number.isFinite(m.minMargin));}
});
