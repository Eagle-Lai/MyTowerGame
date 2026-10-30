from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,subprocess,sys
D=Path(__file__).resolve().parent;H=D.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='Sheep'
assert not (D/'staged_art').exists()
selection=read(D/'art_selection.json');selection['Up']='local_raster_revision_02/Up_sheet.png'
selection['rectangles']={}
for direction,rects in [('Up',[[15,145,355,420],[395,145,740,420],[775,145,1117,420],[1135,80,1510,525],[97,605,277,875],[485,600,660,875],[0,0,1,1]]),('Down',[[15,165,367,510],[380,165,745,510],[765,165,1115,540],[1130,80,1510,535],[95,620,250,900],[450,620,630,900],[0,0,1,1]])]:
    for name,rect in zip(read(D/'anatomy_plan.json')['parts'],rects):selection['rectangles'][direction+'_'+name]=rect
selection['selection_note']='Up original rear heads and body plus local closure of hollow neck and same-sheet rear heel leg replacement, revision_02. Down original HTTP200 initial. Two raw results retained. No tail in original; transparent compatibility slices only.'
write(D/'art_selection.json',selection)
write(D/'generation/Down/review_20261028.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),accepted_for_staging=True,raw_sha256=sha(D/'generation/Down/raw.png'),viewed='raw.png',finding='Pale gold cream axial face, white normal eyes, narrowed angry eyes, empty dead eyes and small tongue, drooping ears and original wool crown. Cream wool torso with ochre ovals, one foreleg/one hindleg, no horns or tail, no ground shadow. Boundaries selected explicitly to preserve dead tongue crossing nominal grid line.'))
write(D/'local_raster_revision_02/review.json',dict(viewed='repair_preview.png',accepted_for_staging=True,observation='Closed cream wool connector with intact dark outer edge; continuous rear-facing cream leg with plain dark heel, no front cleft. Original failed revision_01 remains rejected.',derived_sha256=sha(D/'local_raster_revision_02/Up_sheet.png')))
subprocess.run([sys.executable,str(H/'character_step.py'),'stage','Sheep'],check=True)
