import fs from 'node:fs';
import path from 'node:path';
const dir=path.join('Library/BalanceStage/trusted-terminal-design-20261109/engine',process.argv[2]);
const read=n=>fs.existsSync(path.join(dir,n))?JSON.parse(fs.readFileSync(path.join(dir,n))):[];
const status=read('status.json'),results=read('unity-results.json'),pressure=read('pressure.json');
if(process.argv.includes('--compact')){
 console.log(JSON.stringify({phase:status.phase,completed:status.completed,total:status.total,round:status.round,profile:status.current?.profileId,elapsed:status.elapsedSeconds}));
 for(const r of results)console.log(JSON.stringify({profile:r.profileId,state:r.state,leaks:r.metrics?.leaked,gold:r.finalGold,pending:r.pendingOperations?.length}));
 const selected=process.argv[3]&&!process.argv[3].startsWith('--')?results.find(r=>r.profileId===process.argv[3]):null;
 const pr=selected?pressure.find(p=>p.runId===selected.metrics.runId):pressure.at(-1);
 for(const w of pr?.waves||[])if(w.wave>=5)console.log(w.wave,JSON.stringify([w.ground.maxAlive,Math.round(w.ground.maxEhp),+w.ground.minMargin.toFixed(2),w.ground.leaks]),JSON.stringify([w.air.maxAlive,Math.round(w.air.maxEhp),+w.air.minMargin.toFixed(2),w.air.leaks]));
 process.exit(0);
}
console.log(JSON.stringify({phase:status.phase,completed:status.completed,total:status.total,round:status.round,profile:status.current?.profileId,elapsed:status.elapsedSeconds,
 results:results.map(r=>({profile:r.profileId,state:r.state,leaks:r.metrics?.leaked,gold:r.finalGold,completed:r.metrics?.completedWaveCount,pending:r.pendingOperations?.length})),
 pressure:pressure.map(r=>({run:r.runId,waves:r.waves.filter(w=>w.wave>=5).map(w=>({w:w.wave,g:[w.ground.maxAlive,Math.round(w.ground.maxEhp),+w.ground.minMargin.toFixed(2),w.ground.leaks],a:[w.air.maxAlive,Math.round(w.air.maxEhp),+w.air.minMargin.toFixed(2),w.air.leaks]}))}))},null,2));
