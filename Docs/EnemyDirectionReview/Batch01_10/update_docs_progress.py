"""Docs-only progress. Evidence is not promoted before final installed-resource validation."""
from pathlib import Path
import json,datetime
HERE=Path(__file__).resolve().parent
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
approved=HERE.parent/'AdvancedHen/progress.json'
data=json.loads(approved.read_text(encoding='utf-8'))
if not data.get('approved'):
    archive=approved.with_name('progress_before_batch01_approval.json')
    if not archive.exists():archive.write_bytes(approved.read_bytes())
    data['approved']=True;data['review_gate']='explicit_user_approved_revision_03'
    data['approval']={'recorded_at':now,'user_instruction':'通过。继续按照规则处理后续的10个预制体。','revision':3,'batch_scope':'Bat through BoarMounted; exactly 10'}
    data['items'][0]['status']='approved'
    data['open_review_points']=[s for s in data.get('open_review_points',[]) if s!='R3 user art approval pending']
    data['updated_at']=now
    approved.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
path=HERE/'progress.json';data=json.loads(path.read_text(encoding='utf-8'))
data['updated_at']=now
data['editor_access']='explicit_freeze_by_parallel_balance_task; Docs only until explicit handoff'
for item in data['items']:
    base=HERE/item['name']
    item['generated_views']=[v for v in ['Up','Down'] if (base/'generation'/v/'raw.png').exists()]
    item['status']='art_preparation' if item['generated_views'] else 'reference_prepared'
    item['staged_atlas']=(base/'staged_art'/(item['name']+'_Directions.png')).exists()
    item['installed']=False;item['runtime_verified']=False
path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for p in HERE.glob('*/generation/Up/prompt.txt'):
    if p.with_name('request.json').exists():continue
    text=p.read_text(encoding='utf-8')
    if 'BACK SURFACES OF EARS' not in text:
        text+='\nBACK SURFACES OF EARS: rear head ears show only outer fur/skin backs. Absolutely no light inner-ear triangles, no ear canal, no inner ridges or front-facing ear folds. Rear feet show heels, not frontal toes.\n'
        p.write_text(text,encoding='utf-8')
print('Docs approval/progress updated; pending prompts strengthened; no production files changed.')
