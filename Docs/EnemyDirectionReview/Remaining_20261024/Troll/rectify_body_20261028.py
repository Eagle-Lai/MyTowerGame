from session_troll import *
import numpy as np
from PIL import Image
owner();out=D/'local_raster_revision_01';assert not out.exists();out.mkdir()
parent=D/'generation/Down/raw.png';image=Image.open(parent).convert('RGB');a=np.array(image)
rect=[1170,80,1515,460];x0,y0,x1,y1=rect;crop=a[y0:y1,x0:x1].copy();rgb=crop.astype(np.int16)
mask=(rgb[:,:,0]<rgb[:,:,2]+24)&(rgb[:,:,2]<=rgb[:,:,1]+8)
# Use the exact same foreground classifier as the existing packer.
mask=(rgb[:,:,2]<=rgb[:,:,1]+8)&(rgb[:,:,2]<=rgb[:,:,0]+12)&((rgb[:,:,0]-rgb[:,:,1])<=(rgb[:,:,1]-rgb[:,:,2])+26)
# Source feature centreline was visually measured in the newly generated FRONT torso.
anchors=[[96,1362],[140,1347],[200,1308],[245,1297],[280,1297],[315,1287],[345,1285],[367,1305],[392,1332],[430,1343]]
target_center=1342-x0;outcrop=np.full_like(crop,[255,0,255]);xx=np.arange(crop.shape[1],dtype=float)
for y in range(crop.shape[0]):
    occupied=np.flatnonzero(mask[y])
    if len(occupied)<2:continue
    left,right=float(occupied[0]),float(occupied[-1]);axis=float(np.interp(y+y0,*np.array(anchors).T))-x0
    axis=np.clip(axis,left+1,right-1);half=(right-left)/2
    band=min(40,half*.40,(axis-left)*.65,(right-axis)*.65)
    dest=[target_center-half,target_center-band,target_center+band,target_center+half]
    src=[left,axis-band,axis+band,right]
    inv=np.interp(xx,dest,src);lo=np.floor(inv).astype(int);hi=np.minimum(lo+1,crop.shape[1]-1);f=inv-lo
    values=np.clip(crop[y,lo]*(1-f[:,None])+crop[y,hi]*f[:,None],0,255).astype(np.uint8)
    valid=(xx>=dest[0])&(xx<=dest[-1]);outcrop[y,valid]=values[valid]
a[y0:y1,x0:x1]=outcrop
Image.fromarray(a).save(out/'Down_sheet.png')
Image.fromarray(outcrop).resize((690,760)).save(out/'body_detail_after.png')
Image.fromarray(crop).resize((690,760)).save(out/'body_detail_before.png')
write(out/'derivation.json',dict(observed_at=now(),parent='generation/Down/raw.png',parent_sha256=sha(parent),output='local_raster_revision_01/Down_sheet.png',output_sha256=sha(out/'Down_sheet.png'),method='Rowwise piecewise horizontal recentering of the newly generated frontal torso; source feature band retained 1:1 and exterior sides remapped to symmetric silhouette. Bilinear original-pixel interpolation only, no color repaint, no source-side sprite used.',rectangle=rect,source_axis_anchors_global=anchors,destination_axis_global=target_center+x0,unchanged='Other six raw parts and all pixels outside body crop',rejected_paid_correction='generation/Down/revision_01/uncertain_result.json',prior_charge='unknown; no retry or reclassification'))
print(json.dumps(dict(output=str(out/'Down_sheet.png'),sha256=sha(out/'Down_sheet.png'))))
