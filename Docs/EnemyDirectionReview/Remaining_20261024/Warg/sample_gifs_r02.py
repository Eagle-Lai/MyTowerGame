from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json
D=Path(__file__).resolve().parent
OUT=D/'gif_samples_r02_20261028';OUT.mkdir(exist_ok=False)
evidence=[]
for run in ['runtime_r02','runtime_updeath_r02']:
    cells=[]
    for path in sorted((D/run).glob('*.gif')):
        digest=hashlib.sha256(path.read_bytes()).hexdigest().upper();gif=Image.open(path)
        for i in sorted(set(round((gif.n_frames-1)*n/4) for n in range(5))):
            gif.seek(i);frame=gif.convert('RGB');frame.thumbnail((300,220),Image.Resampling.LANCZOS)
            cell=Image.new('RGB',(320,250),(40,48,37));cell.paste(frame,((320-frame.width)//2,22+(220-frame.height)//2))
            ImageDraw.Draw(cell).text((6,5),path.name+' f'+str(i),fill='white');cells.append(cell)
            evidence.append({'revision':run,'file':path.name,'gif_sha256':digest,'frame_index_zero_based':i,'frame_count':gif.n_frames,'duration_ms':gif.info.get('duration'),'sample_sha256':hashlib.sha256(frame.tobytes()).hexdigest().upper()})
    assert len(cells)==30
    sheet=Image.new('RGB',(1600,1500),(40,48,37))
    for i,cell in enumerate(cells):sheet.paste(cell,((i%5)*320,(i//5)*250))
    sheet.save(OUT/(run+'_samples.png'))
(OUT/'samples.json').write_text(json.dumps({'method':'Five evenly spaced encoded GIF frames per file, not live playback or exhaustive every-frame review.','samples':evidence},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'gifs':12,'samples':len(evidence)}))
