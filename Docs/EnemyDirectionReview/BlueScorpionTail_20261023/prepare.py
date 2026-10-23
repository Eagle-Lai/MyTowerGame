from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil,datetime,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REL='Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
if (HERE/'baseline.json').exists():raise RuntimeError('Do not replace a baseline')
prior=HERE.parent/'AnimationPolish_20261023'
old=json.loads((prior/'final_fingerprints.json').read_text())['files']
files={s:sha(ROOT/s) for s in old}
for folder in ['Assets','Packages','ProjectSettings','Luban']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and (folder!='Assets' or p.suffix in ['.cs','.meta','.prefab','.unity','.asset','.json','.anim','.controller','.png','.shader']):files[p.relative_to(ROOT).as_posix()]=sha(p)
backup=[p for p in (ROOT/REL).rglob('*') if p.is_file()]+[ROOT/'Assets/Prefabs/Enemy/Enemy_BlueScorpion.prefab']
for p in backup:
 dest=HERE/'before'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
(HERE/'source_snapshot.json').write_text(json.dumps([{'path':s,'sha256':h,'content':(ROOT/s).read_text(encoding='utf-8-sig')} for s,h in files.items() if s.endswith('.cs') and h],ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'baseline.json').write_text(json.dumps({'observed_at':datetime.datetime.now().astimezone().isoformat(),'files':files,'prior_polish_identity':{f:sha(prior/f) for f in ['implementation_manifest.json','final_fingerprints.json','progress.json']},'preexisting_drift':[s for s,h in old.items() if files[s]!=h],'note':'Current local disk is authoritative. No reset/restore of concurrent work.'},indent=2),encoding='utf-8')
layout=json.loads((ROOT/REL/'BlueScorpion_Directions.layout.json').read_text());manifest=json.loads((ROOT/REL/'BlueScorpion_Directions.sprites.json').read_text())
view=layout['views'][0];tail=next(p for p in view['parts'] if p['role']=='tail');body=next(p for p in view['parts'] if p['role']=='body')
tail.update(x=0,y=body['y']-body['height']*.40,angle=180,order=15,width=tail['width']*.8,height=tail['height']*.8)
sprite=next(s for s in manifest['sprites'] if s['name']=='Up_Tail');sprite.update(pivotX=.4,pivotY=.10)
stage=HERE/'staged';stage.mkdir()
for obj,ext in [(layout,'layout'),(manifest,'sprites')]:
 (stage/f'BlueScorpion_Directions.{ext}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
atlas=Image.open(ROOT/REL/'BlueScorpion_Directions.png').convert('RGBA')
original=json.loads((ROOT/REL/'BlueScorpion_Directions.layout.json').read_text());orig_manifest=json.loads((ROOT/REL/'BlueScorpion_Directions.sprites.json').read_text())
board=Image.new('RGB',(1500,900),(40,48,37));draw=ImageDraw.Draw(board)
for col,(v,m,label) in enumerate([(original['views'][0],orig_manifest,'BEFORE Up'),(layout['views'][0],manifest,'PROPOSED Up'),(layout['views'][1],manifest,'Down unchanged')]):
 slices={s['name']:s for s in m['sprites']};ppu=115
 for p in sorted(v['parts'],key=lambda p:p['order']):
  s=slices[p['sprite']];piece=atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y']))
  scale=min(p['width']/s['w'],p['height']/s['h'])*ppu;w,h=round(s['w']*scale),round(s['h']*scale);piece=piece.resize((w,h),Image.Resampling.LANCZOS)
  px=s['pivotX'];py=s['pivotY']
  if p['flipX']:piece=piece.transpose(Image.Transpose.FLIP_LEFT_RIGHT);px=1-px
  radius=math.ceil(math.hypot(w,h));pad=Image.new('RGBA',(radius*2,radius*2));pad.alpha_composite(piece,(round(radius-px*w),round(radius-(1-py)*h)));pad=pad.rotate(p['angle'],resample=Image.Resampling.BICUBIC)
  board.paste(pad,(round(col*500+250+p['x']*ppu-radius),round(540-p['y']*ppu-radius)),pad)
 draw.text((col*500+15,15),'OFFLINE layout only - '+label,fill='white')
board.save(HERE/'layout_proposal.png')
print(json.dumps({'baseline_files':len(files),'preexisting_drift':[s for s,h in old.items() if files[s]!=h],'tail':tail}))
