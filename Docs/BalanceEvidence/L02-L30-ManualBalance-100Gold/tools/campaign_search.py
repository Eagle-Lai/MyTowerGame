"""Bounded offline player-action search only; no workbook/export writes."""
from formal_tools import *
import sys,subprocess,concurrent.futures
def search(level):
    target=REPORT/f'L{level:02}/search-campaign-r1/request.json'
    if target.exists():return dict(level=level,status='existing')
    proc=subprocess.run([sys.executable,str(REPORT/'tools/player_search.py'),str(level),'campaign-r1'],capture_output=True,text=True,encoding='utf-8')
    return dict(level=level,exit=proc.returncode,output=proc.stdout,error=proc.stderr)
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(search,range(5,31)):
        results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
        (REPORT/'audit/offline-search-r1.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
