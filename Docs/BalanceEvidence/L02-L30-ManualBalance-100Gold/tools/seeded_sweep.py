"""Parallel independent player-action predictions using observed real openings."""
from formal_tools import *
import sys,subprocess,concurrent.futures
levels=list(map(int,sys.argv[1:]))
def run(level):
    result=subprocess.run([sys.executable,'-X','utf8',str(REPORT/'tools/seeded_search.py'),str(level)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
    print(level,result.returncode,result.stdout[-5500:],result.stderr[-1000:],flush=True)
    return dict(level=level,exit=result.returncode,stdout=result.stdout,stderr=result.stderr)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(run,levels))
(REPORT/f'audit/seeded-r3-offline-L{min(levels):02}-L{max(levels):02}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
