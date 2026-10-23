"""Compose only recorded native Unity poses; no synthetic animation frames."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,sys,math,re
HERE=Path(__file__).resolve().parent;BATCH=HERE.parent/'Batch01_10'
name=sys.argv[1];revision=sys.argv[2] if len(sys.argv)>2 else 'runtime_polish_r01'
def load(rev):
 d=BATCH/name/rev;rs=[json.loads(s) for s in (d/'actual_frames.jsonl').read_text().splitlines()]
 assert all(b['frame']>a['frame'] for a,b in zip(rs,rs[1:]))
 assert 'FAIL ' not in (d/'actual_runtime_checks.txt').read_text() and not (d/'exception.txt').exists()
 return d,rs
before,br=load('runtime_r01');after,ar=load(revision)
walks={}
for version,rs in [('BEFORE',br),('AFTER',ar)]:
 for facing in ['Up','Down']:
  samples=[r for r in rs if r['stage']==facing+'Walk' and r['state']=='Walk'];start=math.ceil(samples[0]['normalizedTime'])
  walks[version,facing]=[r for r in samples if start<=r['normalizedTime']<start+1]
def bounds(d,r):
 a=np.array(Image.open(d/r['file']).convert('RGB'));bg=np.array([40,48,37]);mask=np.abs(a.astype(int)-bg).max(axis=2)>24
 mask &= ~((a[:,:,1]>100)&(a[:,:,0]<100)&(a[:,:,2]<100))
 yy,xx=np.where(mask)
 return [xx.min(),yy.min(),xx.max()+1,yy.max()+1]
boxes=[bounds(before if v=='BEFORE' else after,r) for (v,f),rs in walks.items() for r in rs]
box=tuple(map(int,(max(0,min(b[0] for b in boxes)-24),max(0,min(b[1] for b in boxes)-24),min(768,max(b[2] for b in boxes)+24),min(768,max(b[3] for b in boxes)+24))))
scale=min(340/(box[2]-box[0]),365/(box[3]-box[1]));size=(round((box[2]-box[0])*scale),round((box[3]-box[1])*scale))
sources=[];frames=[]
def panel(d,r,label):
 im=Image.new('RGB',(360,420),(40,48,37));piece=Image.open(d/r['file']).convert('RGB').crop(box).resize(size,Image.Resampling.LANCZOS)
 im.paste(piece,((360-size[0])//2,45+(365-size[1])//2));ImageDraw.Draw(im).text((10,12),label,fill='white');return im
for i in range(12):
 im=Image.new('RGB',(1440,420),(40,48,37));source=[]
 for col,(version,facing) in enumerate([('BEFORE','Up'),('AFTER','Up'),('BEFORE','Down'),('AFTER','Down')]):
  rs=walks[version,facing];phase=i/12
  r=min(rs,key=lambda r:min(abs(r['normalizedTime']%1-phase),1-abs(r['normalizedTime']%1-phase)))
  d=before if version=='BEFORE' else after;im.paste(panel(d,r,name+' '+facing+' '+version),(col*360,0));source.append(str(d/r['file']))
 frames.append(im);sources.append(source)
frames[0].save(HERE/(name+'_walk_before_after.gif'),save_all=True,append_images=frames[1:],duration=[40,40,40,50,40,40,40,50,40,40,40,40],loop=0,disposal=2,optimize=False)
frames[0].save(HERE/(name+'_walk_before_after.png'))
manifest={'source':'Recorded actual Unity Play frames only; nearest native phases at 12 samples, presented as a 0.50s comparison loop. Cropping/zoom is shared by before and after.','crop':box,'walk_sources':sources,'revision':revision}
# Keep action contact sheets as well as sequential native attack/death video frames.
board=Image.new('RGB',(1440,1680),(40,48,37));draw=ImageDraw.Draw(board)
for row,(stage,facing) in enumerate([('Attack','Up'),('Attack','Down'),('DeathAutoRecycle','Down'),('UpWalk','Up')]):
 samples=[r for r in ar if r['stage']==stage and r['facing']==facing and (stage!='Attack' or r['state']=='Attack')]
 if not samples:continue
 for col,p in enumerate([.10,.25,.38,.65]):
  r=min(samples,key=lambda r:abs((r['normalizedTime'] if stage=='DeathAutoRecycle' else r['normalizedTime']%1)-p));board.paste(panel(after,r,stage+' '+facing+' phase '+str(round(r['normalizedTime'],2))),(col*360,row*420))
board.save(HERE/(name+'_actions_after.png'))
for stage,facing in [('Attack','Up'),('Attack','Down'),('DeathAutoRecycle','Down')]:
 rs=[r for r in ar if r['stage']==stage and r['facing']==facing and (stage!='Attack' or r['state']=='Attack')]
 if len(rs)<2:continue
 # A single actual native attack, or the full native death/fade sequence.
 if stage=='Attack':
  first=rs[0]['normalizedTime'];rs=[r for r in rs if r['normalizedTime']<min(1,math.floor(first)+1)]
 out=[panel(after,r,name+' '+facing+' '+stage) for r in rs]
 family='Scorpions' if name=='BlueScorpion' else 'Dogs'
 clip=HERE.parents[2]/f'Assets/_UIAssets/Monsters/{family}/{name}/Directions/Animations/{"Attack" if stage=="Attack" else "Death"}_Directions.anim'
 clip_seconds=float(re.search(r'm_StopTime: ([0-9.]+)',clip.read_text())[1])
 duration=[max(10,min(180,round((b['normalizedTime']-a['normalizedTime'])*1000*clip_seconds))) for a,b in zip(rs,rs[1:])]
 if len(duration)!=len(out)-1 or any(x<0 for x in duration):duration=[50]*(len(out)-1)
 duration.append(500)
 if out:out[0].save(HERE/(name+'_'+facing+'_'+stage+'.gif'),save_all=True,append_images=out[1:],duration=duration,loop=0,disposal=2,optimize=False)
(HERE/(name+'_comparison_sources.json')).write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(name,revision,'actual comparison written')
