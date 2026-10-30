from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,sys
REV=Path(__file__).resolve().parent;CHAR=REV.parent;HERE=CHAR.parent
source=(HERE/'finish_runtime.py').read_text(encoding='utf-8')
source=source.replace("'runtime_r01'","'runtime_r02'").replace("'runtime_updeath_r01'","'runtime_updeath_r02'").replace('runtime_r01/actual_frames.jsonl','runtime_r02/actual_frames.jsonl').replace('runtime_updeath_r01/actual_frames.jsonl','runtime_updeath_r02/actual_frames.jsonl')
sys.argv=['finish_runtime.py','IceParasite']
exec(compile(source,str(HERE/'finish_runtime.py'),'exec'),{'__file__':str(HERE/'finish_runtime.py'),'__name__':'__main__'})
records={rev:[json.loads(x) for x in (CHAR/rev/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if x] for rev in ['runtime_r02','runtime_updeath_r02']}
evidence=[]
def pick(rev,stage,count=6,facing=None):
    rows=[r for r in records[rev] if r['stage']==stage and (not facing or r['facing']==facing)]
    assert rows,(rev,stage,facing)
    return [(rev,rows[round(i*(len(rows)-1)/(count-1))]) for i in range(count)]
def board(filename,rows):
    size=270;gap=30
    out=Image.new('RGB',(1800,len(rows)*310),(40,48,37));draw=ImageDraw.Draw(out)
    for row,(label,cells) in enumerate(rows):
        draw.text((8,row*310+4),label,fill='white')
        for col,(rev,record) in enumerate(cells):
            path=CHAR/rev/record['file']
            im=Image.open(path).convert('RGB').resize((size,size),Image.Resampling.LANCZOS)
            out.paste(im,(col*300+15,row*310+34))
            draw.text((col*300+10,row*310+20),record['facing']+' f'+str(record['frame'])+' nt='+format(record['normalizedTime'],'.2f')+' a='+format(record['alpha'],'.2f'),fill='white')
            evidence.append({'board':filename,'revision':rev,**record,'sha256':hashlib.sha256(path.read_bytes()).hexdigest().upper()})
    out.save(REV/filename)
walkrows=[]
for stage in ['UpWalk','DownWalk']:
    rev='runtime_updeath_r02'
    rows=[r for r in records[rev] if r['stage']==stage and r['state']=='Walk']
    start=next(i for i,r in enumerate(rows) if r['normalizedTime']>=int(rows[0]['normalizedTime'])+1)
    cycle=[r for r in rows[start:] if r['normalizedTime']<int(rows[start]['normalizedTime'])+1]
    assert len(cycle)>=4
    walkrows.append((stage+' - one recorded cycle',[(rev,cycle[round(i*(len(cycle)-1)/5)]) for i in range(6)]))
for stage in ['Pause','Resume1x','Speed2x','Speed3x']:
    walkrows.append((stage,pick('runtime_updeath_r02',stage)))
board('walk_pause_speed_board.png',walkrows)
board('reuse_turn_board.png',[
    ('Reuse after automatic recycle',pick('runtime_updeath_r02','Reuse')),
    ('ContinuousTurns Up after reuse',pick('runtime_updeath_r02','ContinuousTurns',facing='Up')),
    ('ContinuousTurns Right after reuse',pick('runtime_updeath_r02','ContinuousTurns',facing='Right')),
    ('ContinuousTurns Down after reuse',pick('runtime_updeath_r02','ContinuousTurns',facing='Down')),
    ('ContinuousTurns Left after reuse',pick('runtime_updeath_r02','ContinuousTurns',facing='Left'))])
board('attack_death_board.png',[
    ('Up Attack',pick('runtime_updeath_r02','Attack',facing='Up')),
    ('Down Attack',pick('runtime_updeath_r02','Attack',facing='Down')),
    ('Hurt',pick('runtime_updeath_r02','Hurt')),
    ('Down death -> shrink/fade/recycle',pick('runtime_r02','DeathAutoRecycle')),
    ('Up death -> shrink/fade/recycle',pick('runtime_updeath_r02','DeathAutoRecycle'))])
(REV/'visual_sample_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'boards':['walk_pause_speed_board.png','reuse_turn_board.png','attack_death_board.png'],'source_samples':len(evidence)}))
