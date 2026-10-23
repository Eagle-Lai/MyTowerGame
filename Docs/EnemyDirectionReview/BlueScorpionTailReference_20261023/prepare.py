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
# Supporting pose reference and construction diagram, not final game assets.
shutil.copy2(Path('C:/Users/ADMINI~1/AppData/Local/Temp/codex-clipboard-231f7312-f79f-4297-9fe8-cbba7bdbc969.png'),gen/'user_rear_reference.png')
guide=Image.new('RGB',(1024,1024),'white');d=ImageDraw.Draw(guide)
points=[(460,920),(318,778),(256,584),(287,379),(430,205),(604,154),(758,236),(789,369),(707,522)]
d.line(points,fill=(30,100,220),width=30,joint='curve')
d.polygon([(707,522),(700,441),(766,474)],fill=(30,100,220))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
d.text((210,945),'ROOT / POSTERIOR ABDOMEN',font=font,fill='black')
d.text((790,490),'STING',font=font,fill='black')
d.text((32,30),'POSE ONLY: HIGH UPRIGHT ARCH, STINGER HANGS DOWN',font=font,fill='black')
guide.save(gen/'rear_arch_guide.png')
print(json.dumps({'baseline_files':len(files),'preexisting_drift':drift,'tail_slice':s}))
