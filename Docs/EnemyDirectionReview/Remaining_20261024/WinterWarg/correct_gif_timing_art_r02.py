from session_winterwarg import *
from PIL import Image,ImageDraw
import math,shutil
owner();review=D/'visual_review_art_r02_20261029';failed=D/'visual_review_art_r02_attempt01_20261029'
assert review.exists() and not list(review.iterdir()) and not failed.exists();review.rename(failed)
back=D/'media_before_gif_quantization_fix_art_r02';assert not back.exists();back.mkdir()
seconds=next(c['length'] for c in read(D/'source_contract_20261029.json')['contract']['clips'] if c['name']=='Walk');assert seconds==.5
reports=[]
def encoded(path):
    with Image.open(path) as gif:
        durations=[]
        for i in range(gif.n_frames):gif.seek(i);durations.append(gif.info.get('duration',0))
    return durations
def frame(folder,r,label):
    im=Image.open(folder/r['file']).convert('RGB').resize((512,512),Image.Resampling.LANCZOS);ImageDraw.Draw(im).text((12,12),label,fill='white');return im
for run in ['runtime_art_r02','runtime_art_updeath_r02']:
    folder=D/run;hist=back/run;hist.mkdir()
    for n in ['UpWalk.gif','DownWalk.gif','up_down_walk.gif','media_manifest.json']:shutil.copy2(folder/n,hist/n)
    rows=[json.loads(l) for l in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l];manifest=read(folder/'media_manifest.json');cycles={}
    for stage in ['UpWalk','DownWalk']:
        samples=[r for r in rows if r['stage']==stage and r['state']=='Walk'];start=math.ceil(samples[0]['normalizedTime']);selected=[r for r in samples if start<=r['normalizedTime']<start+1];cycles[stage]=selected
        times=[round((r['normalizedTime']-selected[0]['normalizedTime'])*50)*10 for r in selected]
        durations=[b-a for a,b in zip(times,times[1:]+[500])];assert all(t>=10 for t in durations) and sum(durations)==500,durations
        images=[frame(folder,r,NAME+' native Walk 0.5s | '+stage) for r in selected];name=stage+'.gif'
        images[0].save(folder/name,save_all=True,append_images=images[1:],duration=durations,loop=0,optimize=False,disposal=2)
        item=next(m for m in manifest['media'] if m['file']==name);item.update(durations_ms=durations,native_clip_seconds=.5,encoded_cycle_ms=500,source_frames=[r['file'] for r in selected],note='Actual native phases quantized to GIF centiseconds at cumulative boundaries; no synthesized pose.')
    frames=[];pairs=[]
    for i in range(10):
        im=Image.new('RGB',(1024,512));sources=[]
        for j,stage in enumerate(['UpWalk','DownWalk']):
            def distance(r):
                d=abs(r['normalizedTime']%1-i/10);return min(d,1-d)
            r=min(cycles[stage],key=distance);im.paste(frame(folder,r,NAME+' '+r['facing']+' native 0.5s'),(j*512,0));sources.append(r['file'])
        frames.append(im);pairs.append(sources)
    frames[0].save(folder/'up_down_walk.gif',save_all=True,append_images=frames[1:],duration=50,loop=0,optimize=False,disposal=2)
    next(m for m in manifest['media'] if m['file']=='up_down_walk.gif').update(actual_frame_pairs=pairs,durations_ms=[50]*10,native_clip_seconds=.5,encoded_cycle_ms=500)
    manifest['centisecond_fix']={'source_clip_seconds':.5,'source_contract_sha256':sha(D/'source_contract_20261029.json'),'old_media':hist.relative_to(D).as_posix(),'production_modified':False};write(folder/'media_manifest.json',manifest)
    for name in ['UpWalk.gif','DownWalk.gif','up_down_walk.gif']:
        before=encoded(hist/name);after=encoded(folder/name);assert sum(after)==500
        reports.append({'revision':run,'file':name,'before_encoded_ms':sum(before),'after_encoded_ms':sum(after),'before_sha256':sha(hist/name),'after_sha256':sha(folder/name)})
write(failed/'failure.json',{'observed_at':now(),'reason':'Initial review preparation deliberately rejected encoded GIF timing before visual-review boards were generated.','actual_before':[{'revision':r['revision'],'file':r['file'],'encoded_ms':r['before_encoded_ms']} for r in reports]},True)
write(D/'gif_quantization_fix_art_r02_20261029.json',{'observed_at':now(),'reason':'Pillow GIF durations truncate individual non-centisecond values, shortening the encoded native 500ms cycle. Quantize cumulative phase times, preserving original actual PNG and original media.','changes':reports,'production_changed':False,'Unity_rerun_required':False},True)
print(json.dumps(reports,ensure_ascii=False))
