from session_troll import *
from PIL import Image,ImageDraw,ImageFont
owner();out=D/'visual_review_final_20261028';assert not out.exists() or not any(out.iterdir()),'Do not replace existing visual evidence';out.mkdir(exist_ok=True);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);sources=[];candidates=[]
def pick(rows,n):
    assert len(rows)>=n,(len(rows),n)
    return [rows[round(i*(len(rows)-1)/(n-1))] for i in range(n)]
for rev in ['runtime_r01','runtime_updeath_r01']:
    rows=[json.loads(x) for x in (D/rev/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if x];stage=lambda name:[x for x in rows if x['stage']==name]
    hurt=stage('Hurt');death=stage('DeathAutoRecycle');reuse=stage('Reuse');sample_lifecycle=hurt+death+pick(reuse,24-len(hurt)-len(death))
    groups=[('01_four_walks',sum([pick(stage(s),6) for s in ['UpWalk','DownWalk','LeftWalk','RightWalk']],[])),('02_states',sum([pick(stage(s),6) for s in ['Idle','Ready','Walk','Run']],[])),('03_attacks',sum([pick([x for x in stage('Attack') if x['facing']==f],12) for f in ['Up','Down']],[])),('04_hurt_death_reuse',sample_lifecycle),('05_pause_speed',sum([pick(stage(s),6) for s in ['Pause','Resume1x','Speed2x','Speed3x']],[])),('06_turns_flying',pick(stage('ContinuousTurns'),16)+pick(stage('Flying'),8))]
    for name,sample in groups:
        filename=rev+'_'+name+'.png';board=Image.new('RGB',(1800,1380),'#172019');draw=ImageDraw.Draw(board);draw.text((8,5),rev+' / '+name+' / actual full PNG scaled only',font=font,fill='white')
        for i,row in enumerate(sample):
            x=i%6*300;y=32+i//6*337;im=Image.open(D/rev/row['file']).convert('RGB');assert im.size==(768,768);board.paste(im.resize((300,300),Image.Resampling.LANCZOS),(x,y));draw.text((x+4,y+301),f"{row['stage']} {row['facing']} f{row['frame']} {row['state']}\na={row['alpha']:.2f} expr={row['expression']} speed={row['speed']:g} pause={row['paused']}",font=font,fill='white')
            sources.append(dict(sheet=filename,slot=i,revision=rev,source=row['file'],source_sha256=sha(D/rev/row['file']),frame=row['frame'],stage=row['stage'],state=row['state'],facing=row['facing'],alpha=row['alpha'],expression=row['expression'],speed=row['speed'],paused=row['paused']))
        board.save(out/filename)
    for facing in ['Up','Down']:
        attack=[x for x in stage('Attack') if x['facing']==facing and x['expression']==1];r=min(attack,key=lambda x:abs(x['normalizedTime']%1-.42));candidates.append(dict(revision=rev,purpose='full-size '+facing+' attack weapon peak',file=r['file'],frame=r['frame']))
    death=stage('DeathAutoRecycle');r=min(death,key=lambda x:abs(x['alpha']-.6));candidates.append(dict(revision=rev,purpose='full-size death fade',file=r['file'],frame=r['frame']))
write(out/'sources.json',dict(observed_at=now(),method='Full768 actual PNG chronological sampling scaled300; no GIF playback or all-frame review claim',sources=sources,boards={p.name:sha(p) for p in sorted(out.glob('*.png'))}));write(out/'full_size_candidates.json',candidates)
print(json.dumps(dict(boards=12,sample_slots=len(sources),distinct_actual_frames=len({(x['revision'],x['source']) for x in sources}),candidates=candidates)))
audit('final')
