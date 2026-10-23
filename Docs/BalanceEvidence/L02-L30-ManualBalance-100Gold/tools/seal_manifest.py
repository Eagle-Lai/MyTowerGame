"""Record an explicitly supplied campaign seal as 30 source-cell edits."""
from formal_tools import *
import sys,openpyxl
value=sys.argv[1];assert len(value)==64 and all(c in '0123456789abcdef' for c in value)
out=REPORT/sys.argv[2];edits=[]
for level in range(1,31):
    p=ROOT/f'Luban/Config/Datas/Levels/L{level:02}/LevelRating.xlsx'
    old=openpyxl.load_workbook(p,read_only=True)['data']['T4'].value
    if old!=value:edits.append(dict(path=p.relative_to(ROOT).as_posix(),sheet='data',cell='T4',before=old,after=value,reason='正规Luban导出后按Configs.CalculateRuntimeContentHash原文算法计算的全战役封印；不改玩法'))
out.write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8');print(out,len(edits))
