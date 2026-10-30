from pathlib import Path
from PIL import Image
import json,math,hashlib
root=Path(__file__).resolve().parent
layout=json.loads((root/'staged_art/Ram_Directions.layout.json').read_text(encoding='utf-8'))
sprites={s['name']:s for s in json.loads((root/'staged_art/Ram_Directions.sprites.json').read_text(encoding='utf-8'))['sprites']}
checks=[]
def opaque_at(part,x,y):
 s=sprites[part['sprite']];im=Image.open(root/'staged_art'/(part['sprite']+'.png')).convert('RGBA')
 scale=min(part['width']/im.width,part['height']/im.height)
 px=(x-part['x'])/scale+s['pivotX']*im.width
 py=(part['y']-y)/scale+(1-s['pivotY'])*im.height
 return 0<=px<im.width and 0<=py<im.height and im.getpixel((int(px),int(py)))[3]>200
for v in layout['views']:
 body=next(p for p in v['parts'] if p['role']=='body')
 head=next(p for p in v['parts'] if p['role']=='head')
 for p in v['parts']:
  if p['role']=='leg':
   ok=opaque_at(body,p['x'],p['y']) or (head['order']>p['order'] and opaque_at(head,p['x'],p['y']))
   checks.append({'check':v['direction']+'/'+p['name']+' opaque root occlusion','pass':ok})
 checks.append({'check':v['direction']+' four leg count','pass':sum(p['role']=='leg' for p in v['parts'])==4})
 checks.append({'check':v['direction']+' single tail node','pass':sum(p['role']=='tail' for p in v['parts'])==1})
report={'name':'Ram','revision':'staging_r02','basis':'Geometric alpha/root checks after inspecting rejected r01; final image review still required. Not runtime evidence.','checks':checks,'pass':all(c['pass'] for c in checks),'proof_sha256':hashlib.sha256((root/'offline_rig_proof.png').read_bytes()).hexdigest()}
(root/'staging_r02_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
if not report['pass']:raise SystemExit(1)
