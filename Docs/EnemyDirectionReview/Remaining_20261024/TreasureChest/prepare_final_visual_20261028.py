"""Create traceable chronological PNG contact sheets from final real Play rounds."""
from session_treasurechest import *
from PIL import Image, ImageDraw, ImageFont

owner()
out = D/'visual_review_final_20261028'
assert not out.exists(), 'Do not overwrite visual review evidence'
out.mkdir()
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 14)
sources = []
def pick(rows, n):
    assert len(rows) >= n, (len(rows), n)
    return [rows[round(i*(len(rows)-1)/(n-1))] for i in range(n)]
for rev in ['runtime_r02', 'runtime_updeath_r02']:
    rows = [json.loads(x) for x in (D/rev/'actual_frames.jsonl').read_text(encoding='utf-8-sig').splitlines() if x]
    stage = lambda name: [x for x in rows if x['stage'] == name]
    groups = [
        ('01_four_walks', sum([pick(stage(s),6) for s in ['UpWalk','DownWalk','LeftWalk','RightWalk']],[])),
        ('02_states', sum([pick(stage(s),6) for s in ['Idle','Ready','Walk','Run']],[])),
        ('03_attacks', sum([pick([x for x in stage('Attack') if x['facing']==f],12) for f in ['Up','Down']],[])),
        ('04_hurt_death_reuse', stage('Hurt') + stage('DeathAutoRecycle') + pick(stage('Reuse'),8)),
        ('05_pause_speed', sum([pick(stage(s),6) for s in ['Pause','Resume1x','Speed2x','Speed3x']],[])),
        ('06_turns_flying', pick(stage('ContinuousTurns'),16) + pick(stage('Flying'),8)),
    ]
    for name, sample in groups:
        assert len(sample)==24
        filename = rev+'_'+name+'.png'
        board = Image.new('RGB',(1800,1380),'#172019');draw=ImageDraw.Draw(board)
        draw.text((8,5),rev+' / '+name+' / actual PNG chronological samples, full frame scaled only',font=font,fill='white')
        for i,row in enumerate(sample):
            x=(i%6)*300;y=32+(i//6)*337
            img=Image.open(D/rev/row['file']).convert('RGB');assert img.size==(768,768)
            board.paste(img.resize((300,300),Image.Resampling.LANCZOS),(x,y))
            label=f"{row['stage']} {row['facing']} f{row['frame']} {row['state']}\na={row['alpha']:.2f} expr={row['expression']} speed={row['speed']:g} pause={row['paused']}"
            draw.text((x+4,y+301),label,font=font,fill='white')
            sources.append(dict(sheet=filename,slot=i,revision=rev,source=row['file'],source_sha256=sha(D/rev/row['file']),frame=row['frame'],stage=row['stage'],state=row['state'],facing=row['facing'],alpha=row['alpha'],expression=row['expression'],speed=row['speed'],paused=row['paused']))
        board.save(out/filename)
write(out/'sources.json',dict(observed_at=now(),method='Full 768x768 actual runtime PNGs, no crop, scaled to300x300 in chronological per-stage groups; no GIF playback claim',sources=sources,boards={p.name:sha(p) for p in sorted(out.glob('*.png'))}))
print(json.dumps(dict(boards=12,sample_slots=len(sources),unique_frames=len({(x['revision'],x['source']) for x in sources}))))
audit('final')
