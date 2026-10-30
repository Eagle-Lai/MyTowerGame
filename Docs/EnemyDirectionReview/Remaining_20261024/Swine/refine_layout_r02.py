from session_swine import *
from PIL import Image, ImageDraw
import numpy as np, shutil
owner(); assert not (D/'installed_manifest.json').exists()
old=D/'offline_layout_revision_01';old.mkdir(exist_ok=False)
for p in ['art_selection.json','layout_adjustments.json','processing.json','parts_clean.png','offline_rig_proof.png','offline_Up.png','offline_Down.png']:
    shutil.copy2(D/p,old/p)
shutil.copytree(D/'staged_art',old/'staged_art')
write(old/'rejected_review.json',dict(observed_at=now(),viewed=['offline_rig_proof.png','parts_clean.png'],finding='Torso fit preserved a narrow pear aspect and left four foot roots detached. Rear head overlaid too much neck and hid torso ears. Reject this layout; no install or Play on it.',not_installed=True))
out=D/'local_raster_revision_02';out.mkdir(exist_ok=False)
for direction in ['Up','Down']:
    parent=D/('local_raster_revision_01/Up_sheet.png' if direction=='Up' else 'generation/Down/raw.png')
    im=Image.open(parent).convert('RGB')
    rect=(1140,65,1525,535) if direction=='Up' else (1145,60,1530,555)
    body=im.crop(rect);a=np.asarray(body);mask=(a[:,:,1]>25)&(a[:,:,0]<250)|(a[:,:,1]>75)
    # Tight crop is derived from the same foreground predicate used by the packer.
    b=a.astype(np.int16);m=(b[:,:,2]<=b[:,:,1]+8)&(b[:,:,2]<=b[:,:,0]+12)&((b[:,:,0]-b[:,:,1])<=(b[:,:,1]-b[:,:,2])+26)
    yy,xx=np.where(m);tight=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));body=body.crop(tight)
    body=body.resize((360,330),Image.Resampling.LANCZOS)
    ImageDraw.Draw(im).rectangle(rect,fill=(255,0,255));im.paste(body,(1165,155))
    if direction=='Up':
        original=Image.open(D/'generation/Up/raw.png').convert('RGB');im.paste(original.crop((110,560,275,900)),(110,560))
        a=np.array(im)
        for y in range(828,857):
            for x in range(181,199):
                if int(a[y,x,0])<180:
                    t=(x-177)/28;a[y,x]=np.round(a[y,177]*(1-t)+a[y,205]*t).astype(np.uint8)
        im=Image.fromarray(a)
    im.save(out/(direction+'_sheet.png'))
    write(out/(direction+'_processing.json'),dict(observed_at=now(),parent=parent.relative_to(D).as_posix(),parent_sha256=sha(parent),output=direction+'_sheet.png',output_sha256=sha(out/(direction+'_sheet.png')),torso_original_crop=rect,torso_tight=tight,torso_resize=[360,330],torso_destination=[1165,155],method='Only generated torso compressed vertically to restore round original boar proportions; no source-side rotation or fake directional view. Up toe seam restored from original then interior dark seam locally interpolated. Prior images preserved.'))
sel=read(D/'art_selection.json')
for direction in ['Up','Down']:
    sel[direction]=out.name+'/'+direction+'_sheet.png';sel['rectangles'][direction+'_Body']=[1155,145,1535,495]
sel['selection_note']='Both original images and initial offline proof viewed. Local r02 rounds generated axial torso without altering original source; duplicate Up head ears removed, rear heel seam closed. Prior narrow disconnected layout retained.'
write(D/'art_selection.json',sel)
adj=read(D/'layout_adjustments.json');adj['parts']['Up/Head'].update(order=12)
for direction in ['Up','Down']:
    up=direction=='Up'
    for side in ['L','R']:
        sign=-1 if side=='L' else 1
        for front in [True,False]:
            near=(not front) if up else front
            adj['parts'][direction+'/'+('Fore' if front else 'Hind')+side].update(x=sign*(.235 if near else .35),y=.29 if near else .50,height=.17 if near else .20,angle=0 if near else sign*8)
    adj['parts'][direction+'/Tail'].update(height=.095,width=.07)
adj['reason']+=' Revision02 widens axial torso by compressing generated body height; embeds all four roots and puts plain rear head behind body and original torso ears.'
write(D/'layout_adjustments.json',adj)
run('character_step.py','stage',NAME)
