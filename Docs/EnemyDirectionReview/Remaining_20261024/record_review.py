from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,sys,subprocess
HERE=Path(__file__).resolve().parent
name,note=sys.argv[1:3]
runtime=json.loads((HERE/name/'runtime_summary.json').read_text(encoding='utf-8'))
if runtime['failures'] or runtime['passes']!=168:raise ValueError('Expected two successful 84-check actual runtime reviews')
progress=json.loads((HERE/'progress.json').read_text(encoding='utf-8'))
item=next(i for i in progress['items'] if i['name']==name)
item.update(status='completed_pending_user_art_review',runtime=runtime['runtime'],actual_frames=runtime['actual_frames'],visual_reviewed=True,visual_note=note,user_approved=False)
remaining=[i for i in progress['items'] if i['status']!='completed_pending_user_art_review']
progress.update(updated_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),completed_count=len(progress['items'])-len(remaining),current=remaining[0]['name'] if remaining else None,status='in_progress' if remaining else 'completed_pending_user_art_review')
(HERE/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(HERE/'collect_gifs.py')],check=True)
print(json.dumps({'name':name,'completed':progress['completed_count'],'remaining':len(remaining),'next':progress['current']},ensure_ascii=False))
