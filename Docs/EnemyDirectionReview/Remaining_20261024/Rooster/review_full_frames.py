"""Create one character's chronological proof sheets from current real-Play summary."""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import json, sys

HERE = Path(__file__).resolve().parent.parent
name = sys.argv[1]
d = HERE / name
summary = json.loads((d / 'runtime_summary.json').read_text(encoding='utf-8'))
out = d / ('visual_review_' + (sys.argv[2] if len(sys.argv) > 2 else 'final_20261026'))
out.mkdir(exist_ok=False)
groups = [['UpWalk', 'DownWalk', 'LeftWalk', 'RightWalk', 'ContinuousTurns'],
          ['Attack', 'Hurt', 'DeathAutoRecycle', 'Reuse'],
          ['Pause', 'Resume1x', 'Speed2x', 'Speed3x']]
sources = []

def add_row(sheet, row, records, rev, label, filename):
    chosen = [records[round((len(records)-1)*i/7)] for i in range(8)]
    images = [Image.open(d/rev/r['file']).convert('RGB') for r in chosen]
    bounds = []
    for im in images:
        a = np.asarray(im).astype(np.int16)
        delta = np.max(np.abs(a-a[0,0]), axis=2)
        mask = delta > 15
        mask[:100] = False
        yy, xx = np.where(mask)
        if len(xx):
            bounds.append((max(0,int(xx.min())-12),max(95,int(yy.min())-12),
                           min(im.width,int(xx.max())+13),min(im.height,int(yy.max())+13)))
    bbox = (min(x[0] for x in bounds),min(x[1] for x in bounds),
            max(x[2] for x in bounds),max(x[3] for x in bounds)) if bounds else (50,270,718,700)
    draw = ImageDraw.Draw(sheet)
    for col, (r, im) in enumerate(zip(chosen,images)):
        im = im.crop(bbox)
        im.thumbnail((235,230),Image.Resampling.LANCZOS)
        sheet.paste(im,(col*240+(240-im.width)//2,row*270+35+(230-im.height)//2))
        draw.text((col*240+3,row*270+3),label+' '+r['facing']+' f'+str(r['frame']),fill='white')
        draw.text((col*240+3,row*270+16),'n='+str(round(r['normalizedTime'],2)),fill='white')
        sources.append({'sheet':filename,'revision':rev,'source':r['file'],'frame':r['frame'],'crop':bbox})

for item in summary['runtime']:
    rev=item['revision']
    records=[json.loads(x) for x in (d/rev/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    for i,stages in enumerate(groups):
        filename=rev+'_sequence_'+str(i)+'.png'
        sheet=Image.new('RGB',(1920,len(stages)*270),(41,48,38))
        for row,stage in enumerate(stages):
            subset=[r for r in records if r['stage']==stage]
            if not subset: raise ValueError('Missing actual stage '+stage)
            add_row(sheet,row,subset,rev,stage,filename)
        sheet.save(out/filename)
    filename=rev+'_walk_cycle.png'
    sheet=Image.new('RGB',(1920,540),(41,48,38))
    for row,stage in enumerate(['UpWalk','DownWalk']):
        subset=[r for r in records if r['stage']==stage]
        start=subset[1]['normalizedTime']
        window=[r for r in subset if start<=r['normalizedTime']<=start+1]
        add_row(sheet,row,window if len(window)>=8 else subset[:16],rev,stage,filename)
    sheet.save(out/filename)
    angry=[r for r in records if r['stage']=='Attack' and r['headAngry'] and r['facing']=='Down']
    if angry:
        filename=rev+'_angry_detail.png'
        sheet=Image.new('RGB',(1920,270),(41,48,38))
        add_row(sheet,0,angry,rev,'AttackAngry',filename)
        sheet.save(out/filename)
(out/'sources.json').write_text(json.dumps({'method':'Chronological real PNG samples and one-cycle samples; no live GIF playback','runtime_summary':summary['runtime'],'sources':sources},indent=2)+chr(10),encoding='utf-8')
print(str(out))
