"""Run a bounded read-only player-action search; never modifies game data."""
from formal_tools import *
import concurrent.futures,subprocess,sys,time

levels=[8,9,10,14,15,16,18,19,20,21,22,23,24,25,27,28,29,30]
started=time.time()
def run(level):
    dest=REPORT/f'L{level:02}/search-refined-r2'
    if (dest/'index.json').exists():return dict(level=level,status='existing')
    assert not dest.exists(),f'Preserve unfinished search first: {dest}'
    proc=subprocess.run([sys.executable,'-X','utf8',str(REPORT/'tools/refined_search.py'),str(level)],capture_output=True,text=True,encoding='utf-8',timeout=850)
    (REPORT/f'audit/refined-r2-L{level:02}.log').write_text(proc.stdout+proc.stderr,encoding='utf-8')
    row=dict(level=level,exitCode=proc.returncode,elapsedSeconds=round(time.time()-started,2))
    if proc.returncode==0:
        rows=json.loads((dest/'index.json').read_text(encoding='utf-8'))
        row['predictions']=[{k:r[k]for k in ['name','waves','leaked','result']}for r in rows]
    print(json.dumps(row,ensure_ascii=False),flush=True)
    return row
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        rows=list(pool.map(run,levels))
    (REPORT/'audit/refined-r2-offline.json').write_text(json.dumps(dict(maxConcurrent=3,policiesPerLevel=6,predictionOnly=True,levels=rows),ensure_ascii=False,indent=2),encoding='utf-8')
