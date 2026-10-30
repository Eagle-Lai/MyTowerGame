"""Refine only the relocated ochre patch edge; retain paid originals and r01."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import hashlib, json, os, shutil, subprocess, sys
import numpy as np

D = Path(__file__).resolve().parent
H = D.parent
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
c = read(H/'conversation_chain.json')
assert c['state'] == 'active' and c['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert c['current_character'] == 'SlugQueen' and c['dispatch_token'] == 'sheep-to-slugqueen-5dd11f24cb8646d0ac5a622d232ec22d'
out = D/'local_raster_revision_02'
assert not out.exists()
out.mkdir()
for f in ['art_selection.json', 'layout_adjustments.json', 'offline_rig_proof.png', 'offline_Up.png', 'processing.json']:
    shutil.copy2(D/f, out/f)
shutil.copytree(D/'staged_art', out/'staged_art_before')
a = np.asarray(Image.open(D/'generation/Up/raw.png').convert('RGB')).copy()
region = a[200:305,1290:1420].astype(np.int16)
core = (region[:,:,0]-region[:,:,1]>30) & (region[:,:,2]<60) & (region[:,:,1]>65)
# Expanded erase mask removes the old antialias pixels. The paste mask instead
# shrinks into spot pigment before feathering, avoiding the old pale brown rim.
erase = np.asarray(Image.fromarray((core*255).astype('uint8')).filter(ImageFilter.MaxFilter(3))) > 0
edge = Image.fromarray((core*255).astype('uint8')).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.45))
yy, xx = np.where(erase)
for y in np.unique(yy):
    xs = np.where(erase[y])[0]
    lo, hi = int(xs.min())+1290, int(xs.max())+1290
    left, right = a[y+200,lo-2].astype(float), a[y+200,hi+2].astype(float)
    for x in xs+1290:
        a[y+200,x] = np.round(left+(right-left)*((x-(lo-2))/(hi-lo+4))).astype(np.uint8)
patch = Image.fromarray(region.astype('uint8'), 'RGB').convert('RGBA')
patch.putalpha(edge)
derived = Image.fromarray(a,'RGB').convert('RGBA')
derived.alpha_composite(patch, (1290,330))
derived.convert('RGB').save(out/'Up_sheet.png')
preview = Image.new('RGB',(1000,530),(40,48,37))
draw = ImageDraw.Draw(preview)
for i, (p, label) in enumerate([(D/'local_raster_revision_01/Up_sheet.png','R01 pale rim'),(out/'Up_sheet.png','R02 refined same patch')]):
    crop=Image.open(p).crop((1140,110,1520,500));crop.thumbnail((470,470))
    preview.paste(crop,(i*500+(500-crop.width)//2,45));draw.text((i*500+15,15),label,fill='white')
preview.save(out/'repair_preview.png')
write(out/'processing.json', dict(parent='generation/Up/raw.png',parent_sha256=sha(D/'generation/Up/raw.png'),previous='local_raster_revision_01/Up_sheet.png',previous_sha256=sha(D/'local_raster_revision_01/Up_sheet.png'),output='Up_sheet.png',output_sha256=sha(out/'Up_sheet.png'),method='Same original ochre patch moved down 130px. Erase original with same-row brown interpolation; refine paste alpha with one-pixel erosion and 0.45px feather to remove the r01 pale fringe. Original paid sheet and prior local revision retained.',offset=[0,130],paste_core_pixels=int(core.sum()),erase_pixels=int(erase.sum()),paid_request=False))
selection=read(D/'art_selection.json')
selection.update(Up='local_raster_revision_02/Up_sheet.png',selection_note='Up uses same original patch moved below collar with refined antialias edge; Down uses its original HTTP200 raw. No extra generation. Originals and r01 remain.')
write(D/'art_selection.json', selection)
subprocess.run([sys.executable,str(H/'character_step.py'),'stage','SlugQueen'],check=True)
print(json.dumps(dict(output=str(out/'Up_sheet.png'),sha256=sha(out/'Up_sheet.png'))))
