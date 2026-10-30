from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,subprocess,sys
D=Path(__file__).resolve().parent;H=D.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='SlugQueen'
assert not (D/'staged_art').exists()
parts=read(D/'anatomy_plan.json')['parts'];rectangles={}
for direction,rects in [('Up',[[40,110,360,470],[410,110,740,470],[780,110,1100,470],[1140,110,1520,500],[20,555,385,930],[410,550,745,960]]),('Down',[[25,110,370,510],[400,110,750,510],[780,110,1120,510],[1140,100,1530,535],[5,600,380,955],[410,600,750,965]])]:
    for role,rect in zip(parts,rects):rectangles[direction+'_'+role]=rect
write(D/'art_selection.json',dict(Up='generation/Up/raw.png',Down='generation/Down/raw.png',rectangles=rectangles,selection_note='Both initial HTTP200 results actually viewed. Explicit bounds retain all crowns and body bottom that crosses nominal row boundary. No raster correction yet.'))
write(D/'generation/Down/review_20261028.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),accepted_for_staging=True,raw_sha256=sha(D/'generation/Down/raw.png'),viewed='Original 1536x1024 raw.png',observation='Axial gold eyes, short round snout, tooth mouth for angry, blank round gold eyes for dead. One crown integrated on each head state, no crown on three olive-brown soft body lobes. Ochre patches, no invented limbs, shell or ground shadow. Smooth shading differs slightly from original flat side sprite; keep for user art review.'))
adj={'layout':{'motion':{'legAngle':0.0,'legLift':0.0,'bodyBob':0.003,'bodyRoll':0.45,'tailSwing':0.0}},'parts':{},'reason':'Three legless soft lobes overlap continuously; front collar rim buried under one crowned head. Alternating lobe phase for gentle peristaltic scale waves.'}
for direction in ['Up','Down']:
    up=direction=='Up'
    values={'Body':dict(y=.43 if up else .61,width=.78,height=.68,order=20,phase=0),
            'Head':dict(y=.80 if up else .28,width=.64,height=.52,order=35,phase=0),
            'Segment':dict(y=.61 if up else .43,width=.69,height=.42,order=22,phase=1),
            'Rear':dict(y=.19 if up else .83,width=.55,height=.34,order=10,phase=.5)}
    for part,value in values.items():adj['parts'][direction+'/'+part]=value
write(D/'layout_adjustments.json',adj)
subprocess.run([sys.executable,str(H/'character_step.py'),'stage','SlugQueen'],check=True)
