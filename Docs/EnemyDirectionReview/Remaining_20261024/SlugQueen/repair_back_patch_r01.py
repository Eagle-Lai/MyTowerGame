from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import hashlib,json,os,shutil,subprocess,sys
import numpy as np
D=Path(__file__).resolve().parent;H=D.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='SlugQueen'
out=D/'local_raster_revision_01';assert not out.exists();out.mkdir()
for f in ['art_selection.json','layout_adjustments.json','offline_rig_proof.png','offline_Up.png','runtime_visual_strip.png','runtime_summary.json']:
    shutil.copy2(D/f,out/f)
shutil.copytree(D/'staged_art',out/'staged_art_before')
im=Image.open(D/'generation/Up/raw.png').convert('RGB');a=np.asarray(im).copy();before=a.copy()
region=a[200:305,1290:1420].astype(np.int16)
mask=(region[:,:,0]-region[:,:,1]>30)&(region[:,:,2]<60)&(region[:,:,1]>65)
m=Image.fromarray((mask*255).astype('uint8')).filter(ImageFilter.MaxFilter(3));mask=np.asarray(m)>0
assert mask.sum()>2000
yy,xx=np.where(mask);bounds=[int(xx.min()+1290),int(yy.min()+200),int(xx.max()+1291),int(yy.max()+201)]
# Preserve the original patch's raster and antialiased outline, then fill its old
# location by interpolating the immediate same-row brown body colors.
patch=np.zeros((105,130,4),dtype=np.uint8);patch[:,:,:3]=region.astype(np.uint8);patch[:,:,3]=mask*255
for y in np.unique(yy):
    xs=np.where(mask[y])[0];lo=int(xs.min())+1290;hi=int(xs.max())+1290
    left=a[y+200,lo-2].astype(float);right=a[y+200,hi+2].astype(float)
    for x in xs+1290:a[y+200,x]=np.round(left+(right-left)*((x-(lo-2))/(hi-lo+4))).astype(np.uint8)
derived=Image.fromarray(a,'RGB').convert('RGBA');patch_im=Image.fromarray(patch,'RGBA')
derived.alpha_composite(patch_im,(1290,330))
derived.convert('RGB').save(out/'Up_sheet.png')
preview=Image.new('RGB',(1000,600),(40,48,37));draw=ImageDraw.Draw(preview)
for i,img in enumerate([Image.fromarray(before,'RGB'),derived.convert('RGB')]):
    crop=img.crop((1140,110,1520,500));crop.thumbnail((470,540));preview.paste(crop,(i*500+(500-crop.width)//2,45));draw.text((i*500+15,15),'ORIGINAL hidden patch' if i==0 else 'LOCAL relocated same patch',fill='white')
preview.save(out/'repair_preview.png')
write(out/'processing.json',dict(parent='generation/Up/raw.png',parent_sha256=sha(D/'generation/Up/raw.png'),output='Up_sheet.png',output_sha256=sha(out/'Up_sheet.png'),method='Move same-sheet ochre Body patch down 130px; fill old patch by interpolation of immediate brown row boundary colors. No other source pixels, silhouette, head, crown or lobes changed. Local deterministic edit, not another AI result.',patch_bounds=bounds,offset=[0,130],pixels=int(mask.sum())))
selection=read(D/'art_selection.json');selection['Up']='local_raster_revision_01/Up_sheet.png';selection['selection_note']='Up original with same ochre Body patch relocated below collar occlusion; local deterministic derivation. Down original HTTP200. Original source and raw results preserved.';write(D/'art_selection.json',selection)
subprocess.run([sys.executable,str(H/'character_step.py'),'stage','SlugQueen'],check=True)
write(out/'rejected_previous.json',dict(reason='Up torso ochre patch fully occluded by collar. Technical 168/0 is retained but not final visual completion.',old_runtime=['runtime_r01','runtime_updeath_r01'],old_frames=670,actually_viewed_old=['runtime_r01/four_directions.png','runtime_visual_strip.png','visual_review_final_20261028/runtime_r01_sequence_0.png','visual_review_final_20261028/runtime_r01_sequence_1.png'],next_runtime=['runtime_r02','runtime_updeath_r02']))
print(json.dumps(dict(derived='local_raster_revision_01/Up_sheet.png',patch_bounds=bounds,pixels=int(mask.sum()))))
