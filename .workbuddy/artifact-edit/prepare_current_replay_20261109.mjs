import fs from 'node:fs';
const prefix='D:/FreedomTower_1/Library/BalanceStage/trusted-terminal-design-20261109/';
const baseline=JSON.parse(fs.readFileSync(prefix+'l01-new-source-baseline.json','utf8'));
const ops=baseline.results.flatMap(r=>r.operations.map(o=>({waveOrdinal:r.w,timeMs:Math.max(0,Math.round((o.timeSec-.05)*1000)),row:o.y,col:o.x,towerId:o.towerId,action:o.type})));
fs.writeFileSync(prefix+'l01-new-source-operations.json',JSON.stringify(ops,null,2));
fs.writeFileSync(prefix+'l01-editor-request.json',JSON.stringify({output:prefix+'l01-editor-validation',stepSeconds:.05,stepsPerUpdate:100,keepPlaying:false,runs:[{profileId:'current-source',levelId:1,strategy:'replay',speed:1,waitForFunds:true,captureStages:false,screenshots:false,operationsPath:prefix+'l01-new-source-operations.json',wallTimeoutSeconds:600}]},null,2));
fs.writeFileSync('D:/FreedomTower_1/Library/BalanceStage/unity-mcp-20261109/start-l01-replay-args.json',JSON.stringify({action:'execute',code:`FTProject.EditorTools.BalancePlayModeVerifier.StartBatch("${prefix}l01-editor-request.json"); return "Started new L01 source-only replay";`}));
console.log(JSON.stringify({operations:ops.length,modelLeaks:baseline.leaks}));
