from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,shutil,datetime,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REL='Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
if (HERE/'baseline.json').exists():raise RuntimeError('Do not replace baseline')
prior=HERE.parent/'BlueScorpionTail_20261023'
old=json.loads((prior/'final_fingerprints.json').read_text())['files']
files={s:sha(ROOT/s) for s in old}
for folder in ['Assets','Packages','ProjectSettings','Luban']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and (folder!='Assets' or p.suffix in ['.cs','.meta','.prefab','.unity','.asset','.json','.anim','.controller','.png','.shader']):files[p.relative_to(ROOT).as_posix()]=sha(p)
drift=[s for s,h in old.items() if files[s]!=h]
if drift:raise RuntimeError('Resolve baseline drift before preparing: '+str(drift))
for p in [p for p in (ROOT/REL).rglob('*') if p.is_file()]+[ROOT/'Assets/Prefabs/Enemy/Enemy_BlueScorpion.prefab']:
 dest=HERE/'before'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
(HERE/'source_snapshot.json').write_text(json.dumps([{'path':s,'sha256':h,'content':(ROOT/s).read_text(encoding='utf-8-sig')} for s,h in files.items() if s.endswith('.cs') and h],ensure_ascii=False,indent=2),encoding='utf-8')
history={f'{d}/{f}':sha(HERE.parent/d/f) for d,fs in {'BlueScorpionTail_20261023':['implementation_manifest.json','final_fingerprints.json','progress.json'],'AnimationPolish_20261023':['implementation_manifest.json','final_fingerprints.json','progress.json'],'Batch01_10':['implementation_manifest.json','final_frozen_fingerprints.json']}.items() for f in fs}
(HERE/'baseline.json').write_text(json.dumps({'observed_at':datetime.datetime.now().astimezone().isoformat(),'files':files,'history_identity':history,'preexisting_drift':drift},indent=2),encoding='utf-8')
original=json.loads((ROOT/REL/'BlueScorpion_Directions.layout.json').read_text());orig_manifest=json.loads((ROOT/REL/'BlueScorpion_Directions.sprites.json').read_text())
layout=json.loads(json.dumps(original));manifest=json.loads(json.dumps(orig_manifest))
tail=next(p for p in layout['views'][0]['parts'] if p['role']=='tail')
tail.update(x=0,y=.50,width=2.3296,height=3.7856,angle=0,order=25)
sprite=next(s for s in manifest['sprites'] if s['name']=='Up_Tail');sprite.update(pivotX=.4,pivotY=.04)
stage=HERE/'staged';stage.mkdir()
for obj,ext in [(layout,'layout'),(manifest,'sprites')]:
 (stage/f'BlueScorpion_Directions.{ext}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
atlas=Image.open(ROOT/REL/'BlueScorpion_Directions.png').convert('RGBA')
behind=json.loads(json.dumps(layout));next(p for p in behind['views'][0]['parts'] if p['role']=='tail')['order']=15
board=Image.new('RGB',(1500,850),(40,48,37));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
for col,(v,m,label) in enumerate([(original['views'][0],orig_manifest,'上轮错误：朝下'),(layout['views'][0],manifest,'方案：腹部末端向上卷曲'),(behind['views'][0],manifest,'遮挡对照：尾巴全在躯干后')]):
 slices={s['name']:s for s in m['sprites']};ppu=110
 for p in sorted(v['parts'],key=lambda p:p['order']):
  s=slices[p['sprite']];piece=atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y']))
  scale=min(p['width']/s['w'],p['height']/s['h'])*ppu;w,h=round(s['w']*scale),round(s['h']*scale);piece=piece.resize((w,h),Image.Resampling.LANCZOS)
  px=s['pivotX'];py=s['pivotY']
  if p['flipX']:piece=piece.transpose(Image.Transpose.FLIP_LEFT_RIGHT);px=1-px
  radius=math.ceil(math.hypot(w,h));pad=Image.new('RGBA',(radius*2,radius*2));pad.alpha_composite(piece,(round(radius-px*w),round(radius-(1-py)*h)));pad=pad.rotate(p['angle'],resample=Image.Resampling.BICUBIC)
  board.paste(pad,(round(col*500+250+p['x']*ppu-radius),round(520-p['y']*ppu-radius)),pad)
 draw.text((col*500+15,15),label,font=font,fill='white')
draw.text((15,810),'离线布局预演，仅供确定尾根、上扬方向和遮挡；非运行证据。',font=font,fill='white')
board.save(HERE/'layout_proposal.png')
print(json.dumps({'files':len(files),'drift':drift,'tail':tail}))
