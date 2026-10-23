"""Resolve individually reviewed Par literals to explicit existing rating cells."""
from formal_tools import *
import openpyxl
pars={2:1080000,3:870000,4:1060000,5:885000,6:1070000,7:1060000,8:1350000,9:1040000,10:1060000,11:1110000,12:1120000,13:1430000,14:1230000,15:1390000,16:1420000,17:1020000,18:1340000,19:1270000,20:1260000,21:1610000,22:1470000,23:1490000,24:1470000,25:1240000,26:1190000,27:1430000,28:1270000,29:1430000,30:1600000}
selected=json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels'];assert {x['level']for x in selected}==set(pars)
records=json.loads((REPORT/'audit/current-source-records.json').read_text(encoding='utf-8'))['LevelRating'];edits=[];reasons=[]
for x in selected:
 level=x['level'];par=pars[level];assert x['combatSeconds']*1000<par
 rec=records[str(level)];wb=openpyxl.load_workbook(ROOT/rec['path'],read_only=True)
 margin=par/1000-x['combatSeconds'];reason=f"L{level:02}已观察25波满血零漏参考runId {x['runId']}，战斗{x['combatSeconds']:.2f}秒；逐关确定Par为{par}ms，保留{margin:.2f}秒操作与路径余量。此项仅校准评分目标，未改变防守、收入或时钟。最终正式封印后仍须首次五星与两次严格复跑。"
 for field,value in dict(parCombatTimeMs=par,ratingRevision='manual-final-reference-20261022',calibrationStatus='unity_reference_calibrated').items():
  cell=rec['cells'][field];before=wb[rec['sheet']][cell].value
  if before!=value:edits.append(dict(path=rec['path'],sheet=rec['sheet'],cell=cell,before=before,after=value,reason=reason))
 wb.close();reasons.append(dict(level=level,parCombatTimeMs=par,observedCombatSeconds=x['combatSeconds'],marginSeconds=margin,marginPercent=100*margin/x['combatSeconds'],referenceSource=x['source'],sourceIndex=x['sourceIndex'],sourceRunId=x['runId'],waveTimeTransactions=x['waveTimeOperations'],reason=reason))
out=REPORT/'rating-calibration-final.cells.json';assert not out.exists();out.write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8');(REPORT/'audit/final-calibration-decisions.json').write_text(json.dumps(dict(status='reviewed_literals_pending_apply_and_final_replays',levels=reasons),ensure_ascii=False,indent=2),encoding='utf-8');print(len(edits),'explicit rating cells across29levels; L01 excluded')
