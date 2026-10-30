from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,subprocess,sys
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='Sheep' and c['dispatch_token']=='scarabmounted-to-sheep-fd7d7a5afb264ca7a1691363ab276f5f'
b=read(D/'incremental_before_20261028.json');assert all(sha(R/p)==s for p,s in b['files'].items())
current={p.relative_to(R).as_posix() for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (R/f).rglob('*') if p.is_file()};assert current==set(b['files'])
assert not (D/'installed_manifest.json').exists()
layout=read(D/'staged_art/Sheep_Directions.layout.json');assert layout['anatomy']['legs']==4 and layout['anatomy']['tails']==0
alpha={}
for p in (D/'staged_art').glob('*.png'):
    a=np.asarray(Image.open(p).convert('RGBA'));alpha[p.name]=dict(size=list(a.shape[:2][::-1]),transparent=int((a[:,:,3]==0).sum()),opaque=int((a[:,:,3]==255).sum()),magenta_foreground=int(((a[:,:,0]>200)&(a[:,:,2]>150)&(a[:,:,1]<80)&(a[:,:,3]>128)).sum()))
assert all(x['magenta_foreground']==0 for x in alpha.values())
for d in ['Up','Down']:
    a=np.asarray(Image.open(D/'staged_art'/(d+'_Tail.png')).convert('RGBA'));assert a[:,:,3].max()==0
write(D/'offline_review_20261028.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),accepted_for_install=True,viewed=['reference/source_prefab_offline.png','reference/Sheep.png','generation/Up/raw.png','generation/Down/raw.png','local_raster_revision_01/repair_preview.png','local_raster_revision_02/repair_preview.png','parts_clean.png','offline_layout_revision_01/offline_rig_proof.png','offline_layout_revision_02/offline_rig_proof.png','offline_rig_proof.png'],observation='Selected local raster revision_02 closes hollow Up neck and uses continuous rear-facing heel leg. Default and second layouts rejected for long/exposed or disconnected roots. Final layout revision_03 has four short hoof nodes with roots connected under wool. Up no eyes/mouth or tail, Down three original expressions, original colors and no shadow. More axial perspective than source side; final art approval remains with user.',alpha=alpha,staging_files={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},layout_adjustments_sha256=sha(D/'layout_adjustments.json'),raw_sha256={d:sha(D/'generation'/d/'raw.png') for d in ['Up','Down']}))
subprocess.run([sys.executable,str(H/'install_character.py'),'Sheep'],check=True)
p=read(H/'progress.json');i=next(x for x in p['items'] if x['name']=='Sheep');i.update(status='staged_pending_visual_check',installed_manifest='Sheep/installed_manifest.json');p['current']='Sheep';write(H/'progress.json',p)
c.update(current_stage='Sheep_installed_pending_side_contract_and_two_Play_rounds',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Sheep/installed_manifest.json',updated_at=datetime.now(timezone(timedelta(hours=8))).isoformat());write(H/'conversation_chain.json',c)
