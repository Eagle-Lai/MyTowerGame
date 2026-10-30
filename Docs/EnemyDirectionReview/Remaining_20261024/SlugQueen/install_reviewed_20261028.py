from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,subprocess,sys
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='SlugQueen'
b=read(D/'incremental_before_20261028.json');current={p.relative_to(R).as_posix():sha(p) for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (R/f).rglob('*') if p.is_file()}
assert current==b['files'],'Production drift before install'
assert not (D/'installed_manifest.json').exists()
alpha={}
for p in (D/'staged_art').glob('*.png'):
    a=np.asarray(Image.open(p).convert('RGBA'));alpha[p.name]=dict(size=list(a.shape[:2][::-1]),transparent=int((a[:,:,3]==0).sum()),opaque=int((a[:,:,3]==255).sum()),magenta_foreground=int(((a[:,:,0]>200)&(a[:,:,2]>150)&(a[:,:,1]<80)&(a[:,:,3]>128)).sum()))
assert all(v['magenta_foreground']==0 for v in alpha.values())
write(D/'offline_review_20261028.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),accepted_for_install=True,viewed=['reference/source_prefab_offline.png','reference/SlugQueen.png','reference/battle_prefab_offline.png','generation/Up/raw.png','generation/Down/raw.png','parts_clean.png','offline_layout_revision_01/offline_rig_proof.png','offline_rig_proof.png','offline_Down.png'],observation='One gold crown on head per direction, plain rear, gold normal/angry/dead front expressions; three overlapping legless olive-brown lobes, short tapered rump. First Down collar was too exposed; layout revision02 buries upper rim behind larger head. Up collar root is fully hidden behind head. All roots solid, no magenta holes or ground shadow seen. Final proportions more axial than source side; user art approval pending.',alpha=alpha,staging_files={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},raw_sha256={d:sha(D/'generation'/d/'raw.png') for d in ['Up','Down']},layout_adjustments_sha256=sha(D/'layout_adjustments.json')))
subprocess.run([sys.executable,str(H/'install_character.py'),'SlugQueen'],check=True)
p=read(H/'progress.json');item=next(x for x in p['items'] if x['name']=='SlugQueen');item.update(installed_manifest='SlugQueen/installed_manifest.json');write(H/'progress.json',p)
c.update(current_stage='installed_pending_side_contract_and_two_Play_rounds',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/SlugQueen/installed_manifest.json');write(H/'conversation_chain.json',c)
