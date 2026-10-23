from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,shutil,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REL='Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
if (HERE/'baseline.json').exists():raise RuntimeError('Baseline already exists')
prior=HERE.parent/'BlueScorpionTailUp_20261023'
old=json.loads((prior/'final_fingerprints.json').read_text(encoding='utf-8'))['files']
files={s:sha(ROOT/s) for s in old}
for folder in ['Assets','Packages','ProjectSettings','Luban']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and (folder!='Assets' or p.suffix in ['.cs','.meta','.prefab','.unity','.asset','.json','.anim','.controller','.png','.shader']):files[p.relative_to(ROOT).as_posix()]=sha(p)
drift=[{'path':s,'previous':h,'current':files[s]} for s,h in old.items() if files[s]!=h]
for p in [p for p in (ROOT/REL).rglob('*') if p.is_file()]+[ROOT/'Assets/Prefabs/Enemy/Enemy_BlueScorpion.prefab']:
 dest=HERE/'before'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
history={f'{d}/{f}':sha(HERE.parent/d/f) for d,fs in {'BlueScorpionTailUp_20261023':['implementation_manifest.json','final_fingerprints.json','progress.json'],'BlueScorpionTail_20261023':['implementation_manifest.json','final_fingerprints.json','progress.json'],'AnimationPolish_20261023':['implementation_manifest.json','final_fingerprints.json','progress.json'],'Batch01_10':['implementation_manifest.json','final_frozen_fingerprints.json']}.items() for f in fs}
(HERE/'baseline.json').write_text(json.dumps({'observed_at':datetime.datetime.now().astimezone().isoformat(),'files':files,'history_identity':history,'preexisting_drift':drift},indent=2),encoding='utf-8')
(HERE/'source_snapshot.json').write_text(json.dumps([{'path':s,'sha256':h,'content':(ROOT/s).read_text(encoding='utf-8-sig')} for s,h in files.items() if s.endswith('.cs') and h],ensure_ascii=False,indent=2),encoding='utf-8')
gen=HERE/'generation';gen.mkdir()
manifest=json.loads((ROOT/REL/'BlueScorpion_Directions.sprites.json').read_text())
atlas=Image.open(ROOT/REL/'BlueScorpion_Directions.png').convert('RGBA')
s=next(s for s in manifest['sprites'] if s['name']=='Up_Tail')
tail=atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y']))
tail.save(gen/'tail_style_reference.png')
shutil.copy2(ROOT/'Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/BlueScorpion.png',gen/'original_style_reference.png')
# Supporting direction guide only, never a game asset or final evidence.
guide=Image.new('RGB',(1024,1024),'white');d=ImageDraw.Draw(guide)
path=[(280,900),(315,780),(365,635),(440,475),(545,330),(680,250),(825,205)]
d.line(path,fill=(30,100,220),width=45,joint='curve')
d.polygon([(825,205),(750,200),(792,270)],fill=(30,100,220))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',27)
d.text((120,930),'ROOT: bottom; attaches to posterior abdomen',font=font,fill='black')
d.text((600,120),'TIP: up + OUTWARD RIGHT',font=font,fill='black')
d.text((30,30),'Direction guide only. No U-loop back toward body.',font=font,fill='black')
guide.save(gen/'outward_direction_guide.png')
print(json.dumps({'baseline_files':len(files),'preexisting_drift':drift,'tail_slice':s}))
