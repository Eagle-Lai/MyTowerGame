"""Inspect five encoded frames per WinterBear GIF with a single stable per-GIF crop."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json
import numpy as np
D=Path(__file__).resolve().parent
OUT=D/'gif_samples_art_r05_20261029';OUT.mkdir(exist_ok=False)
evidence=[]
for run in ['runtime_r01','runtime_updeath_r01']:
    cells=[]
    for path in sorted((D/run).glob('*.gif')):
        digest=hashlib.sha256(path.read_bytes()).hexdigest().upper();gif=Image.open(path)
        indices=sorted(set(round((gif.n_frames-1)*n/4) for n in range(5)))
        frames=[];bounds=[]
        for i in indices:
            gif.seek(i);im=gif.convert('RGB');frames.append((i,im.copy(),gif.info.get('duration')))
            a=np.asarray(im).astype(np.int16);mask=np.max(np.abs(a-a[-1,0]),axis=2)>22
            mask[:int(im.height*.30)]=False
            yy,xx=np.where(mask)
            if len(xx):bounds.append((max(0,int(xx.min())-18),max(int(im.height*.30),int(yy.min())-18),min(im.width,int(xx.max())+19),min(im.height,int(yy.max())+19)))
        crop=(min(b[0] for b in bounds),min(b[1] for b in bounds),max(b[2] for b in bounds),max(b[3] for b in bounds)) if bounds else (0,0,gif.width,gif.height)
        for i,im,duration in frames:
            frame=im.crop(crop);frame.thumbnail((300,215),Image.Resampling.LANCZOS)
            cell=Image.new('RGB',(320,250),(40,48,37));cell.paste(frame,((320-frame.width)//2,30+(215-frame.height)//2))
            ImageDraw.Draw(cell).text((6,5),path.name+' f'+str(i),fill='white');cells.append(cell)
            evidence.append({'revision':run,'file':path.name,'gif_sha256':digest,'frame_index_zero_based':i,'frame_count':gif.n_frames,'duration_ms':duration,'stable_crop':crop,'sample_sha256':hashlib.sha256(frame.tobytes()).hexdigest().upper()})
    assert len(cells)==30
    sheet=Image.new('RGB',(1600,1500),(40,48,37))
    for i,cell in enumerate(cells):sheet.paste(cell,((i%5)*320,(i//5)*250))
    sheet.save(OUT/(run+'_samples.png'))
(OUT/'samples.json').write_text(json.dumps({'method':'Five evenly spaced encoded GIF frames per file, stable union crop below header/HP at 30 percent. Not live playback or exhaustive every-frame review.','samples':evidence},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'gifs':12,'samples':len(evidence)}))
