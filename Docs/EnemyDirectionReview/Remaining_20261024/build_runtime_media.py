"""Assemble evidence ONLY from the generic review's actual Unity Play-frame log."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,sys,math
HERE=Path(__file__).resolve().parent
name,revision=sys.argv[1:3];directory=HERE/name/revision
records=[json.loads(s) for s in (directory/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
if not records or any(b['frame']<=a['frame'] for a,b in zip(records,records[1:])):raise ValueError('Expected strictly increasing actual Unity frames')
if (directory/'exception.txt').exists():raise ValueError('Review has an exception; do not publish media as final evidence')
checks=(directory/'actual_runtime_checks.txt').read_text(encoding='utf-8')
if 'FAIL ' in checks:raise ValueError('Runtime checks failed; preserve the revision and fix before publishing final media')
stages={s:[r for r in records if r['stage']==s] for s in set(r['stage'] for r in records)}
def frame(record,size=512):
    im=Image.open(directory/record['file']).convert('RGB')
    if size!=im.width:im=im.resize((size,size),Image.Resampling.LANCZOS)
    return im
def labeled(record,label,size=512):
    im=frame(record,size);ImageDraw.Draw(im).text((12,12),label,fill='white');return im
def animation(selected,path,label,durations=None):
    if len(selected)<2:raise ValueError('Insufficient real frames for '+path)
    frames=[labeled(r,label+' | '+r['stage']+' | '+r['facing']) for r in selected]
    if durations is None:
        durations=[max(10,min(500,round((b['realtime']-a['realtime'])*1000))) for a,b in zip(selected,selected[1:])]
        durations.append(durations[-1] if durations else 50)
    frames[0].save(directory/path,save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False,disposal=2)
    return {'file':path,'real_frames':len(selected),'first_unity_frame':selected[0]['frame'],'last_unity_frame':selected[-1]['frame'],'durations_ms':durations}
static=[]
for stage in ['LeftWalk','RightWalk','UpWalk','DownWalk']:
    subset=[r for r in stages[stage] if r['state']=='Walk' and r['alpha']>.99]
    static.append(subset[len(subset)//2])
contact=Image.new('RGB',(2048,560),(40,48,37));draw=ImageDraw.Draw(contact)
for i,r in enumerate(static):contact.paste(labeled(r,name+' '+r['facing']), (i*512,40))
draw.text((12,12),'FINAL INSTALLED PREFAB - real Unity Play frames; '+name+' / '+revision,fill='white')
contact.save(directory/'four_directions.png')
media=[];cycles={}
for stage in ['UpWalk','DownWalk']:
    samples=[r for r in stages[stage] if r['state']=='Walk']
    start=math.ceil(samples[0]['normalizedTime']);end=start+1
    cycle=[r for r in samples if start<=r['normalizedTime']<end]
    if len(cycle)<4:raise ValueError('No complete readable actual walk cycle: '+stage)
    phases=[r['normalizedTime'] for r in cycle]
    durations=[max(10,round((b-a)*500)) for a,b in zip(phases,phases[1:])]
    durations.append(max(10,500-sum(durations)))
    item=animation(cycle,stage+'.gif',name+' - actual 0.5s loop',durations)
    # Source Walk clips are 0.5s. Preserve exactly one cycle rather than closing at an
    # arbitrary 1.1-second recording boundary. No image or Animator frames are fabricated.
    item['normalized_time_interval']=[start,end];media.append(item);cycles[stage]=cycle
paired=[];paired_sources=[]
for i in range(10):
    image=Image.new('RGB',(1024,512));sources=[]
    for column,stage in enumerate(['UpWalk','DownWalk']):
        def distance(r):
            phase=r['normalizedTime']%1;delta=abs(phase-i/10);return min(delta,1-delta)
        r=min(cycles[stage],key=distance);image.paste(labeled(r,name+' '+r['facing']), (column*512,0));sources.append(r['file'])
    paired.append(image);paired_sources.append(sources)
paired[0].save(directory/'up_down_walk.gif',save_all=True,append_images=paired[1:],duration=50,loop=0,optimize=False,disposal=2)
media.append({'file':'up_down_walk.gif','actual_frame_pairs':paired_sources,'note':'Nearest recorded native phases, composed side by side; no synthesized poses.'})
media.append(animation(stages['ContinuousTurns'],'walk_turn.gif',name+' - actual BaseEnemy.Tick'))
media.append(animation([r for r in records if r['stage'] in ['Attack','Hurt','DeathAutoRecycle','Reuse']],'attack_death_reuse.gif',name+' - native events/automatic pool'))
media.append(animation([r for r in records if r['stage'] in ['Pause','Resume1x','Speed2x','Speed3x']],'pause_speed.gif',name+' - actual pause and speed tiers'))
(directory/'media_manifest.json').write_text(json.dumps({'source':'actual_frames.jsonl','source_type':'real Unity Play; final installed prefab; no manual Animator.Update capture','static_source_frames':[r['file'] for r in static],'media':media},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'name':name,'revision':revision,'actual_frames':len(records),'media':[m['file'] for m in media]}))
