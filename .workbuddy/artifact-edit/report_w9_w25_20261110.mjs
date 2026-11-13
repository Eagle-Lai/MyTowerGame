import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root='D:/FreedomTower_1';
const stage=`${root}/Library/BalanceStage/w9-w25-design-20261110`;
const out=`${root}/outputs/01a1bda2-a06a-7052-baa3-dda18ad77d19`;
await fs.mkdir(out,{recursive:true});
const d=JSON.parse(await fs.readFile(`${stage}/calculation.json`,'utf8'));
const inp=JSON.parse(await fs.readFile(`${stage}/inputs.json`,'utf8'));
const old=JSON.parse(await fs.readFile(`${stage}/summary.json`,'utf8'));
const wb=Workbook.create();
const overview=wb.worksheets.add('波次方案');
const detail=wb.worksheets.add('逐怪计算');
const econ=wb.worksheets.add('经济与参数');
const species=['Chicken','Larva','Crawler','Scarab','Rat','Bat'];
const rowById=new Map(d.rows.map((r,i)=>[r.id,i+7]));
const wr=n=>n-2;
const er=n=>n+2;
const detailedEnd=d.rows.length+6;
for(const s of [overview,detail,econ]){
  s.showGridLines=false;
  s.getRange(`A1:U${s===detail?detailedEnd:50}`).format.font={name:'Arial',size:10,color:'#172433'};
  s.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:'#172433'};
  s.tabColor=s===overview?'#233D57':s===econ?'#758A9C':'#ADC0CE';
}
const header=(s,range)=>{
  s.getRange(range).format={fill:'#233D57',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',rowHeight:32,wrapText:true};
};
overview.getRange('A2').values=[['L02 W9–W25 数值候选']];
overview.getRange('A4').values=[['计算方案，尚未写入源表。只调整 HP、数量和出怪名单；W1–W8 及其他关卡保持。']];
overview.getRange('A6:R6').values=[['波次','roundId','Chicken HP','数量','Larva HP','数量','Crawler HP','数量','Scarab HP','数量','Rat HP','数量','Bat HP','数量','地面总数','空中总数','间隔 ms','波次奖 金']];
header(overview,'A6:R6');
overview.getRange('A:R').format.columnWidth=13;
overview.getRange('A:B').format.columnWidth=10;
for(const c of ['D','F','H','J','L','N','O','P'])overview.getRange(`${c}:${c}`).format.columnWidth=8;
overview.getRange('C7:M23').setNumberFormat('#,##0.00');
for(const c of ['D','F','H','J','L'])overview.getRange(`${c}7:${c}23`).setNumberFormat('#,##0');
overview.getRange('N7:R23').setNumberFormat('#,##0');
overview.getRange('Q7:Q23').setNumberFormat('0.0');
overview.freezePanes.freezeRows(6);

detail.getRange('A2').values=[['逐怪旧值、新值与计算依据']];
detail.getRange('A4').values=[['HP = L01 同怪 HP × 经济与密度校正；数量 = L01 同怪数量 × W8 锚点比例，新增地面种类使用 627/286。']];
detail.getRange('A6:T6').values=[['波次','roundId','敌人ID','怪种','是否空中','当前 HP','L01 HP','最终 HP倍率','新 HP','HP 变化','当前数量','L01 数量','数量倍率','新数量','数量变化','单只金币','当前击杀金币','新击杀金币','源表 HP单元格','源表名单单元格']];
header(detail,'A6:T6');
detail.getRange('A:T').format.columnWidth=13;
detail.getRange('A:B').format.columnWidth=9;
detail.getRange('C:C').format.columnWidth=12;
detail.getRange('D:D').format.columnWidth=14;
detail.getRange('S:T').format.columnWidth=20;
detail.getRange(`F7:I${detailedEnd}`).setNumberFormat('#,##0.000000');
detail.getRange(`H7:H${detailedEnd}`).setNumberFormat('0.000000');
detail.getRange(`J7:J${detailedEnd}`).setNumberFormat('0.0%');
detail.getRange(`O7:O${detailedEnd}`).setNumberFormat('0.0%');
detail.getRange(`M7:M${detailedEnd}`).setNumberFormat('0.000000');
detail.getRange(`P7:R${detailedEnd}`).setNumberFormat('#,##0.000000');
detail.freezePanes.freezeRows(6);
detail.freezePanes.freezeColumns(4);
const sourceRowById=new Map(inp['2'].EnemyData.map((e,i)=>[e.id,i+4]));
const groupRowById=new Map(inp['2'].EnemyList.map((e,i)=>[e.id,i+4]));

econ.getRange('A2').values=[['经济递推与模型参数']];
econ.getRange('A4:B7').values=[['L01锚点金币',d.anchor.preWaveEarnedL01],['L02锚点金币',d.anchor.preWaveEarnedL02],['L02 W8后金币',d.anchor.earnedAfterW8],['当前全关金币',d.oldTotalEconomy]];
econ.getRange('B4:B7').setNumberFormat('#,##0.000000');
econ.getRange('D4').values=[['累计金币含已投入防御的历史金币，不是钱包余额；本波击杀只进入下一波累计值。']];
econ.getRange('D5').values=[['经济修正 = (L02累计/L02 W8累计) ÷ (L01累计/L01 W8累计)。初始金币固定100。']];
econ.getRange('D6').values=[['结构系数来自54组AOE密度/减速/普通塔分工假设；是设计敏感性，不是实测火力。']];
econ.getRange('D7').values=[['地面 HP不低于上一波；普通波空中 HP不低于上一普通波，困难空中峰值不永久传递。']];
econ.getRange('A10:R10').values=[['波次','roundId','波前累计金','L01波前金','经济修正','本波击杀金','波次奖','波后累计金','地面结构系数','空中结构系数','地面 HP下限倍率','空中 HP下限倍率','地面最终倍率','空中最终倍率','地面下限增压','空中下限增压','出生间隔 ms','波型']];
header(econ,'A10:R10');
econ.getRange('A:R').format.columnWidth=15;
econ.getRange('A:B').format.columnWidth=17;
econ.getRange('C11:D27').setNumberFormat('#,##0.00');
econ.getRange('E11:E27').setNumberFormat('0.000000');
econ.getRange('F11:H27').setNumberFormat('#,##0.00');
econ.getRange('I11:N27').setNumberFormat('0.000000');
econ.getRange('O11:P27').setNumberFormat('0.0%');
econ.getRange('Q11:Q27').setNumberFormat('0.0');
econ.freezePanes.freezeRows(10);

// The count/income branch does not depend on HP, so the economic recursion is acyclic.
for(let i=0;i<d.rows.length;i++){
  const r=d.rows[i], row=i+7, ew=er(r.wave);
  const type=r.enemy.replace('Enemy_','');
  const ratio=d.anchor.countRatios[`${"('"+r.enemy+"', "+(r.isFlying?'True':'False')+")"}`] ?? d.anchor.newGroundSpeciesCountRatio;
  const values=[r.wave,r.roundId,r.id,type,r.isFlying,r.oldHp,r.trustedL01Hp,null,null,null,r.oldCount,r.trustedL01Count,ratio,null,null,
    inp['2'].EnemyData.find(e=>e.id===r.id).reward,null,null,`Sheet!D${sourceRowById.get(r.id)}`,`Sheet!C${groupRowById.get(r.roundId)}`];
  detail.getRange(`A${row}:T${row}`).values=[values];
  detail.getRange(`H${row}:J${row}`).formulas=[[`='经济与参数'!${r.isFlying?'N':'M'}${ew}`,`=ROUND(G${row}*H${row},6)`,`=I${row}/F${row}-1`]];
  detail.getRange(`N${row}:O${row}`).formulas=[[`=ROUND(L${row}*M${row},0)`,`=N${row}/K${row}-1`]];
  detail.getRange(`Q${row}:R${row}`).formulas=[[`=K${row}*P${row}`,`=N${row}*P${row}`]];
}
let previousGround=new Map(inp['2'].EnemyData.filter(e=>d.rows.some(r=>r.wave===9&&r.enemy===e.resName)&&[6000070,6000071,6000072].includes(e.id)).map(e=>[e.resName,{literal:e.hp}]));
let previousNormalAir=new Map([['Enemy_Bat',{literal:372.082872}]]);
for(const w of d.waves){
  const n=w.wave,row=wr(n),ew=er(n);
  econ.getRange(`A${ew}:R${ew}`).values=[[n,w.roundId,null,w.preWaveReferenceEarned,null,null,w.roundReward,null,w.unflooredGroundScale/w.economyCorrection,w.unflooredAirScale/w.economyCorrection,null,null,null,null,null,null,w.intervalMs,w.waveType===2?'困难':'普通']];
  econ.getRange(`C${ew}`).formulas=[[n===9?'=$B$6':`=H${ew-1}`]];
  econ.getRange(`E${ew}:F${ew}`).formulas=[[`=(C${ew}/$B$5)/(D${ew}/$B$4)`,`=SUMIFS('逐怪计算'!$R$7:$R$${detailedEnd},'逐怪计算'!$A$7:$A$${detailedEnd},A${ew})`]];
  econ.getRange(`H${ew}`).formulas=[[`=C${ew}+F${ew}+G${ew}`]];
  const floor=(flying,previous)=>{
    const terms=w.roster.filter(e=>Boolean(e.isFlying)===flying&&previous.has(e.resName)).map(e=>{
      const p=previous.get(e.resName),r=rowById.get(e.id);
      return `${p.row?`'逐怪计算'!I${p.row}`:p.literal}/'逐怪计算'!G${r}`;
    });
    return terms.length?`=MAX(${terms.join(',')})`:'=0';
  };
  econ.getRange(`K${ew}:P${ew}`).formulas=[[floor(false,previousGround),floor(true,previousNormalAir),`=MAX(I${ew}*E${ew},K${ew})`,`=MAX(J${ew}*E${ew},L${ew})`,`=M${ew}/(I${ew}*E${ew})-1`,`=N${ew}/(J${ew}*E${ew})-1`]];
  for(const e of w.roster){
    if(!e.isFlying)previousGround.set(e.resName,{row:rowById.get(e.id)});
    else if(w.waveType===1)previousNormalAir.set(e.resName,{row:rowById.get(e.id)});
  }
  overview.getRange(`A${row}:R${row}`).values=[[n,w.roundId,...Array(12).fill(null),null,null,w.intervalMs,w.roundReward]];
  for(let j=0;j<species.length;j++){
    const e=w.roster.find(e=>e.resName===`Enemy_${species[j]}`);
    const col=String.fromCharCode(67+j*2),next=String.fromCharCode(68+j*2);
    if(e){const r=rowById.get(e.id);overview.getRange(`${col}${row}:${next}${row}`).formulas=[[`='逐怪计算'!I${r}`,`='逐怪计算'!N${r}`]];}
    else overview.getRange(`${col}${row}:${next}${row}`).values=[['—','—']];
  }
  overview.getRange(`O${row}:P${row}`).formulas=[[`=SUMIFS('逐怪计算'!$N$7:$N$${detailedEnd},'逐怪计算'!$A$7:$A$${detailedEnd},A${row},'逐怪计算'!$E$7:$E$${detailedEnd},0)`,`=SUMIFS('逐怪计算'!$N$7:$N$${detailedEnd},'逐怪计算'!$A$7:$A$${detailedEnd},A${row},'逐怪计算'!$E$7:$E$${detailedEnd},1)`]];
  if(w.waveType===2)overview.getRange(`A${row}:R${row}`).format.fill='#E9EFF5';
}
overview.getRange('A26').values=[['注意：W21–W25 实际 roundId 为2401–2405；所有 HP显示2位小数，实际候选保留6位。']];
overview.getRange('A27').values=[['W12、W15、W17、W18、W24、W25触发地面HP下限。困难空中峰值与新地面种类需要重点体验。']];
overview.getRange('A28').values=[['未进行Play Mode、战斗模拟或末端压力验证。设计代理量不能证明零漏怪或所有购买选择等效。']];
econ.getRange('A30:B32').values=[['候选全关累计金币',null],['增加金币',null],['固定初始金币',100]];
econ.getRange('B30:B31').formulas=[['=H27'],['=B30-B7']];
econ.getRange('B30:B31').setNumberFormat('#,##0.000000');
econ.getRange('A34').values=[['来源与口径']];
econ.getRange('A34').format.font={bold:true};
const sourceNotes=[
  'L01参考：Luban/Config/Datas/Levels/L01/EnemyData.xlsx、EnemyList.xlsx、RoundData.xlsx、SceneInfo.xlsx。',
  'L02现值：Luban/Config/Datas/Levels/L02/EnemyData.xlsx、EnemyList.xlsx、RoundData.xlsx、SceneInfo.xlsx；只读。',
  '塔系：L01/L02 TowerInfo.xlsx、BulletData.xlsx；攻击、冷却、价格、AOE半径、减速参数已比对。',
  '地图：L02 LevelMap.xlsx，16×9开放地图不变；已认可波次吸收地图与可选路线差异，不再乘面积倍率。',
  'W5–W7来自用户实测认可；W8为已确认落表值，尚无用户提供的W8实战结论。',
  '54种结构敏感性：AOE半径0.75/0.90/1.05；覆盖系数0.5/1；驻留系数1/1.4/2；普通塔地面分工0/25%/50%。',
  '金币到火力采用同类合理策略下的近似线性边际购买力；不保证任意塔组合和任意布局收益相同。',
  'AOE密度已含驻留变化，不再重复叠加同一减速收益；普通塔对空占用与地面分工共用攻击时间。',
  '完整推导、旧新值及不确定项：Artifacts/L02_W9_W25_20261110_design.md；候选出怪名单保存在只读stage清单。',
];
sourceNotes.forEach((s,i)=>econ.getRange(`A${35+i}`).values=[[s]]);
for(const s of [overview,detail,econ]){
  const end=s===detail?detailedEnd:s===overview?23:27;
  const start=s===econ?11:7;
  s.getRange(`A${start}:${s===detail?'T':'R'}${end}`).format.rowHeight=24;
  s.getRange(`A${start}:${s===detail?'T':'R'}${end}`).format.verticalAlignment='center';
  s.getRange(`${s===detail?'E':'C'}${start}:${s===detail?'R':'R'}${end}`).format.horizontalAlignment='right';
}
wb.recalculate();
// Independent comparisons cover every output HP/count and the complete economic recursion.
let maxHpError=0,maxGoldError=0;
for(let i=0;i<d.rows.length;i++){
  const r=d.rows[i],row=i+7;
  const hp=detail.getRange(`I${row}`).values[0][0],count=detail.getRange(`N${row}`).values[0][0];
  if(typeof hp!=='number'||typeof count!=='number')throw new Error(`Non-numeric ${row}: ${hp},${count}`);
  maxHpError=Math.max(maxHpError,Math.abs(hp-r.newHp));
  if(count!==r.newCount)throw new Error(`Count mismatch ${r.id}: ${count} != ${r.newCount}`);
}
for(const w of d.waves){
  maxGoldError=Math.max(maxGoldError,Math.abs(econ.getRange(`C${er(w.wave)}`).values[0][0]-w.preWaveCumulativeEarned));
  const r=wr(w.wave),vals=overview.getRange(`A${r}:R${r}`).values[0];
  if(vals[0]!==w.wave||vals[1]!==w.roundId||vals[14]!==w.groundCount||vals[15]!==w.airCount)throw new Error(`Overview mapping mismatch W${w.wave}`);
}
if(maxHpError>0.000002||maxGoldError>0.000001)throw new Error(`Mismatch: HP ${maxHpError}, gold ${maxGoldError}`);
const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'Formula error scan'});
await fs.writeFile(`${stage}/workbook-inspect.json`,JSON.stringify({maxHpError,maxGoldError,scan},null,2));
console.log('VERIFIED',JSON.stringify({rows:d.rows.length,maxHpError,maxGoldError,scan:scan.ndjson}));
for(const [s,range,name] of [[overview,'A1:R15','overview'],[econ,'A1:H18','economy']]){
  const png=await wb.render({sheetName:s.name,range,scale:1.4,format:'png'});
  await fs.writeFile(`${stage}/${name}.png`,new Uint8Array(await png.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(`${out}/L02_W9-W25_候选值_20261110.xlsx`);
console.log('EXPORTED',`${out}/L02_W9-W25_候选值_20261110.xlsx`);

// Human-readable candidate report, with old/new values and explicit assumptions.
const f=(x,n=2)=>Number(x).toLocaleString('en-US',{minimumFractionDigits:n,maximumFractionDigits:n});
const cell=(w,s)=>{const e=w.roster.find(e=>e.resName===`Enemy_${s}`);return e?`${f(e.hp)} / ${e.count}`:'—';};
const md=[
  '# L02 W9–W25 数值重算候选',
  '', '日期：2026-11-10。状态：仅计算与候选文件；未修改配置源表，未执行Luban导出，未进行Unity战斗或模拟。',
  '', '## 已确认的本轮边界',
  '', '- 只计算L02 W9–W25的HP、数量与出怪名单；速度、护甲、间隔、单只击杀奖励及波次奖励使用现值。',
  '- W1–W8及其他关卡不改；不做全部关卡应用；初始金币恒为100。',
  '- 新增击杀收入进入后续波次的累计经济，不再受早期7106等总额目标约束。',
  '- 实际roundId：W9–W20为2009–2020，W21–W25为2401–2405。不得按波号猜ID。',
  '', '## 可信输入',
  '', 'W5、W6、W7具有用户明确的实测认可。W8采用已确认并落表的HP/数量作为最后锚点，但没有收到W8实测通过结论。旧W9–W25的HP和数量仅用于旧新对照，不用作难度基准；其他字段按本轮明确确认保持。',
  '', '参考来自当前可信L01 EnemyData/EnemyList/RoundData/SceneInfo/TowerInfo/BulletData及WaveTuning。L02地图16×9保持不变，认可波次已包含该地图与自由路线的实际影响，不再重复乘地图面积比。两关塔/子弹攻击参数一致，普通/困难波HP等倍率为1、护甲和波次奖加成为0。',
  '', '## 历次调整的经验教训',
  '', '1. 旧L02基准曾过低；W6最初按正常成长仍明显偏弱，不能从旧表直接乘小倍率。现在从已确认W8统一锚定。',
  '2. AOE攻击使总HP与怪物数量不是线性难度。压低单只HP、用数量补总HP会降低命中次数门槛，甚至更容易；HP、密度、护甲和出生结构需共同看。',
  '3. 新增金币必须折算为塔系购买力；升级只计新旧输出之差、建造使用完整累计成本。普通塔对地/对空共享射击时间，减速只增加接触机会且重叠取最强。',
  '4. 不绑定截图坐标或指定升级对象，比较同类合理策略的容量变化。自由建造不意味着所有随意花钱方式都有相同效果。',
  '5. 新增数量带来的额外击杀金币必须逐波入账；累计已赚金币包括已变成塔的部分，不是剩余钱包，也不能再把已结算金币重复加一遍。',
  '6. “后半波积压、少量残血冲出火力区”属于吞吐/持续射击余量问题；需要小步调整HP，不能无依据同时猛增HP和数量。',
  '7. W5合适并不代表后续直接按一个倍率递增即可。困难空中峰值、新地面怪、出生间隔变化需要保留各自结构。',
  '8. 设计计算、导表、Unity实际加载和用户实战是不同验收；静态指标不能宣称已经匹配最后3格压力或零漏怪。',
  '', '## 计算关系',
  '', '数量首先按同怪种W8锚点映射：`N2(w,j)=round(N1(w,j)×N2(8,j)/N1(8,j))`。Chicken/Larva/Crawler/Bat的比例分别为314/147、192/84、121/55、39/20。新地面Scarab、Rat用地面总数比例627/286，不从旧L02残留数量取倍率。',
  '', '`B(l,w)=100+Σ(v<w)[Σj N(l,v,j)×reward(l,v,j)+roundReward(l,v)]`。只计波前已到账收入，不预支本波结算；本波击杀产出在下一波累计值出现。',
  '', '`rho(w)=[B(2,w)/B(2,8)]/[B(1,w)/B(1,8)]`。这个修正只补偿相对L01参考成长之外的购买力，不把金币比直接乘两遍HP，也不重新乘地图比。',
  '', '`T=(ΣN−1)×interval`，`LG=Σground N×HP/(1−armor)/T`，`LA=Σair N×HP/(1−armor)/T`。这里T是出生跨度，用于吞吐换算，不要求两关通关用时相等。',
  '', '`M=1+d×2r×(NG/T)/vH×u`，其中vH是地面调和平均速度，d为队列有效覆盖系数，u为密度中的驻留系数。`RG=LG×[q+(1−q)/M]`，`RA=LA`；q为由普通塔承担的地面伤害份额。',
  '', '在54种明确的AOE/减速/分工假设下，求各通道统一HP倍率：',
  '', '`Kx(w,c)= [R2x(8,c)/R2x(w,c;HP=可信L01同波HP)] × [R1x(w,c)/R1x(8,c)] × rho(w)`',
  '', '`HP2(w,j)=HP1(w,j)×median_c(Kx(w,c))`，再执行下述HP下限。地面/空中分开求，不把普通塔同时当作满额地面和满额空中输出。',
  '', '该式隐含“同类合理策略下，每累计投入金币的有效容量与锚点相近”的近似。塔价和边际输出用于支持量级；由于没有逐波真实投资结构、覆盖、目标切换及末端遥测，不能声称它是唯一解或精确实测模型。',
  '', '敏感性参数：r=0.75/0.90/1.05；d=0.5/1；u=1/1.4/2；q=0/25%/50%，共54组。中位解是设计取舍，不是统计置信区间。驻留系数已计入密度，不再把同一减速收益额外乘一次。',
  '', '## AOE个体血量下限',
  '', '地面同怪种HP不低于上一波，使用共同地面倍率保持同波物种相对HP。空中HP不低于上一普通波；困难波空中临时峰值允许在下个普通波回落，但不得低于普通波基线。数量沿用可信L01结构，因此个别怪种可因新种类接替或困难波结束而减少，不机械要求每一物种数量单调。',
  '', '| 波次 | 地面下限额外增压 | 空中下限额外增压 |', '|---|---:|---:|',
  ...d.waves.filter(w=>w.floorExtraPressure.ground>1e-6||w.floorExtraPressure.air>1e-6).map(w=>`| W${w.wave} | ${f(w.floorExtraPressure.ground*100)}% | ${f(w.floorExtraPressure.air*100)}% |`),
  '', '上述下限让部分候选高于原始参考模型，偏差已明示，不能再把候选描述成与L01完全等效。',
  '', '## 完整逐波候选', '', '每格为“HP / 数量”；此处HP展示2位，候选清单保留6位。',
  '', '| 波次 | Chicken | Larva | Crawler | Scarab | Rat | Bat |', '|---|---:|---:|---:|---:|---:|---:|',
  ...d.waves.map(w=>`| W${w.wave} | ${species.map(s=>cell(w,s)).join(' | ')} |`),
  '', '## 经济递推结果',
  '', '| 波次 | 波前累计可得金 | 新击杀金 | 结算奖 | 波后累计金 | 经济修正rho |', '|---|---:|---:|---:|---:|---:|',
  ...d.waves.map(w=>`| W${w.wave} | ${f(w.preWaveCumulativeEarned)} | ${f(w.newKillIncome)} | ${w.roundReward} | ${f(w.preWaveCumulativeEarned+w.newWaveTotalIncome)} | ${f(w.economyCorrection,6)} |`),
  '', `当前全关理论累计 ${f(d.oldTotalEconomy,6)} 金；候选 ${f(d.newTotalEconomy,6)} 金，增加 ${f(d.extraTotalEconomy,6)} 金。均为初始100金加全击杀和全部结算、无出售收入的累计获得，不是最终余金。`,
  '', '## 逐怪旧新值', '', '| 波次 | ID | 怪种 | 当前HP | 候选HP | 当前数量 | 候选数量 |', '|---|---:|---|---:|---:|---:|---:|',
  ...d.rows.map(r=>`| W${r.wave} | ${r.id} | ${r.enemy.replace('Enemy_','')} | ${f(r.oldHp,6)} | ${f(r.newHp,6)} | ${r.oldCount} | ${r.newCount} |`),
  '', '## 不确定项与后续体验重点',
  '', '- W10困难空中、W11引入Scarab、W15/W20困难波、W25引入Rat及长出生间隔需要重点观察；W25不应仅按总HP判断。',
  '- 新增地面怪分散补到可信L01序列间隙，不把高血量怪原有连续段直接成倍复制；所有原始出生条目的相对顺序保持。',
  '- 已检查10秒滚动出生EHP峰值与均值，仅用于暴露出生结构差异；未模拟战斗，不等同最后3格存活量、累计EHP或最小击杀余量。',
  '', '| 波次 | 地面峰均比：候选 / L01 | 空中峰均比：候选 / L01 |', '|---|---:|---:|',
  ...d.waves.filter(w=>[9,10,11,15,20,25].includes(w.wave)).map(w=>`| W${w.wave} | ${f(w.rolling10sArrival.ground.peakToMean,3)} / ${f(w.referenceRolling10sArrival.ground.peakToMean,3)} | ${f(w.rolling10sArrival.air.peakToMean,3)} / ${f(w.referenceRolling10sArrival.air.peakToMean,3)} |`),
  '',
  '- 未来每一波配置落表后仍由用户体验。若后续实测改变W9等锚点，后面的候选应从新锚点重新计算，不继续叠加旧修正。',
  '- 波内新增击杀可以被玩家即时用于补强；主方案未假定即时消费。已花多少、如何花、覆盖效率与持续积压可能改变实际压力。',
  '', '## 本轮只读核对',
  '', `- ${d.sourceCount}个源表哈希与改前一致，配置源表零修改；Assets/ConfigJson和Assets/Gen没有由本脚本写入。`,
  '- 候选84条HP、17条名单全部按实际SceneInfo→RoundData→EnemyList引用定位；各波敌人ID未在其他波复用。',
  '- 候选保留可信L01的地面类型顺序骨架，扩展地面数量、分散新增空中怪。按isFlying展开L02完整25波，跨编组及跨波边界无空中相邻。',
  '- 本轮未修改源表，所以未触发新一轮Luban/Unity验证；不将候选计算称为已应用工程。',
  '', `候选审阅工作簿：${out}/L02_W9-W25_候选值_20261110.xlsx。完整精确清单及原始输入保存在Library/BalanceStage/w9-w25-design-20261110/。`,
];
await fs.writeFile(`${root}/Artifacts/L02_W9_W25_20261110_design.md`,md.join('\n')+'\n','utf8');
console.log('REPORT_EXPORTED');
