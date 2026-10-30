from session_current import *
from PIL import Image,ImageDraw,ImageChops
import math,shutil

owner()
out=HERE/'visual_review_final_20261029'
backup=HERE/'media_before_gif_quantization_fix_20261029'
assert not out.exists() and not backup.exists()
out.mkdir();backup.mkdir()
runs=['runtime_r02','runtime_updeath_r02']
seconds=next(c['length'] for c in read(HERE/'source_animation_contract_complete_20261029.json')['contract']['clips'] if c['name']=='Walk')
target_ms=round(seconds*1000)
assert target_ms>0 and target_ms%10==0
positions=[];gif_samples=[];timing=[];changes=[];originals=[]

def encoded(path):
    with Image.open(path) as im:
        d=[]
        for i in range(im.n_frames):
            im.seek(i);d.append(im.info.get('duration',0))
    return d

def source_frame(folder,r,label):
    im=Image.open(folder/r['file']).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
    ImageDraw.Draw(im).text((12,12),label,fill='white')
    return im

def pick(rows,n):
    n=min(n,len(rows))
    return [rows[round((len(rows)-1)*i/max(1,n-1))] for i in range(n)]

def union_crop(images):
    boxes=[]
    for im in images:
        diff=ImageChops.difference(im,Image.new('RGB',im.size,im.getpixel((0,0))))
        mask=diff.convert('L').point(lambda v:255 if v>8 else 0)
        b=mask.getbbox()
        if b:boxes.append(b)
    assert boxes
    w,h=images[0].size
    return [max(0,min(b[0] for b in boxes)-18),max(0,min(b[1] for b in boxes)-18),min(w,max(b[2] for b in boxes)+18),min(h,max(b[3] for b in boxes)+18)]

def board(run,tag,rows):
    images=[Image.open(HERE/run/r['file']).convert('RGB') for r in rows]
    crop=union_crop(images)
    sheet=Image.new('RGB',(1500,270*math.ceil(len(rows)/6)),(40,48,37));draw=ImageDraw.Draw(sheet)
    for i,(r,im) in enumerate(zip(rows,images)):
        im=im.crop(crop);im.thumbnail((242,230),Image.Resampling.LANCZOS)
        x,y=i%6*250,i//6*270;sheet.paste(im,(x+(250-im.width)//2,y+38))
        draw.text((x+3,y+3),f"{r['stage']} {r['facing']} f{r['frame']}\nn{r['normalizedTime']:.3f} a{r['alpha']:.2f}",fill='white')
        p=HERE/run/r['file']
        positions.append({'revision':run,'source':r['file'],'source_sha256':sha(p),'board':tag+'.png','position':i,'crop':crop,'frame':r['frame'],'stage':r['stage']})
    sheet.save(out/(tag+'.png'))

for run in runs:
    folder=HERE/run;hist=backup/run;hist.mkdir()
    rows=[json.loads(l) for l in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l]
    assert 'FAIL ' not in (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8')
    groups={s:[r for r in rows if r['stage']==s] for s in dict.fromkeys(r['stage'] for r in rows)}
    manifest=read(folder/'media_manifest.json');cycles={};manifest_changed=False
    for stage in ['UpWalk','DownWalk']:
        samples=[r for r in groups[stage] if r['state']=='Walk'];start=math.ceil(samples[0]['normalizedTime'])
        selected=[r for r in samples if start<=r['normalizedTime']<start+1];cycles[stage]=selected
        name=stage+'.gif';before=encoded(folder/name)
        if sum(before)!=target_ms:
            if not manifest_changed:shutil.copy2(folder/'media_manifest.json',hist/'media_manifest.json')
            manifest_changed=True;shutil.copy2(folder/name,hist/name)
            times=[round((r['normalizedTime']-selected[0]['normalizedTime'])*target_ms/10)*10 for r in selected]
            durations=[b-a for a,b in zip(times,times[1:]+[target_ms])]
            assert min(durations)>=10 and sum(durations)==target_ms
            images=[source_frame(folder,r,NAME+f' native Walk {seconds}s | '+stage) for r in selected]
            images[0].save(folder/name,save_all=True,append_images=images[1:],duration=durations,loop=0,optimize=False,disposal=2)
            next(m for m in manifest['media'] if m['file']==name).update(durations_ms=durations,native_clip_seconds=seconds,encoded_cycle_ms=target_ms,source_frames=[r['file'] for r in selected],note='Cumulative recorded native phase boundaries quantized to GIF centiseconds; actual PNG unchanged, no synthesized poses.')
            after=encoded(folder/name);assert sum(after)==target_ms
            changes.append({'revision':run,'file':name,'before_encoded_ms':sum(before),'after_encoded_ms':sum(after),'before_sha256':sha(hist/name),'after_sha256':sha(folder/name)})
        timing.append({'revision':run,'file':name,'encoded_ms':sum(encoded(folder/name)),'durations_ms':encoded(folder/name),'native_seconds':seconds,'changed':sum(before)!=target_ms})
    paired=encoded(folder/'up_down_walk.gif');assert sum(paired)==target_ms
    timing.append({'revision':run,'file':'up_down_walk.gif','encoded_ms':sum(paired),'durations_ms':paired,'native_seconds':seconds,'changed':False})
    if manifest_changed:
        manifest['centisecond_fix']={'source_contract_sha256':sha(HERE/'source_animation_contract_complete_20261029.json'),'old_media':hist.relative_to(HERE).as_posix(),'production_modified':False}
        (folder/'media_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    sets=[(['UpWalk','DownWalk','LeftWalk','RightWalk'],6),(['Idle','Ready','Walk','Run'],6),(['Attack','Hurt','DeathAutoRecycle','Reuse'],10),(['Pause','Resume1x','Speed2x','Speed3x'],6),(['ContinuousTurns','Flying'],18)]
    for i,(stages,n) in enumerate(sets):board(run,run+f'_sequence_{i+1:02}',[r for s in stages for r in pick(groups[s],n)])
    board(run,run+'_native_walk_cycles',cycles['UpWalk']+cycles['DownWalk'])
    for stage in ['UpWalk','DownWalk','Attack','DeathAutoRecycle','Reuse','Flying']:
        selected=groups[stage];r=next((r for r in selected if r.get('headAngry') and r['facing']=='Down'),selected[len(selected)//2])
        dest=out/(run+'_'+stage+'_uncropped.png');shutil.copy2(folder/r['file'],dest)
        originals.append({'revision':run,'source':r['file'],'source_sha256':sha(folder/r['file']),'output':dest.name})
    cells=[]
    for g in sorted(folder.glob('*.gif')):
        with Image.open(g) as gif:
            indexes=sorted(set(round((gif.n_frames-1)*i/4) for i in range(5)))
            selected=[]
            for i in indexes:gif.seek(i);selected.append(gif.convert('RGB').copy())
            crop=union_crop(selected)
            for i,im in zip(indexes,selected):
                dest=out/(run+'_'+g.stem+f'_encoded_{i:03}.png');im.save(dest)
                cell=Image.new('RGB',(300,270),(40,48,37));actor=im.crop(crop);actor.thumbnail((292,228),Image.Resampling.LANCZOS)
                cell.paste(actor,((300-actor.width)//2,38));ImageDraw.Draw(cell).text((4,4),g.name+f' encoded frame {i}',fill='white');cells.append(cell)
                gif_samples.append({'revision':run,'gif':g.name,'gif_sha256':sha(g),'encoded_frame':i,'output':dest.name,'output_sha256':sha(dest),'crop':crop})
    sheet=Image.new('RGB',(1500,270*math.ceil(len(cells)/5)),(40,48,37))
    for i,cell in enumerate(cells):sheet.paste(cell,(i%5*300,i//5*270))
    sheet.save(out/(run+'_gif_samples.png'))

save(HERE/'gif_quantization_fix_20261029.json',{'observed_at':now(),'changes':changes,'source_png_modified':False,'production_changed':False,'Unity_rerun_required':False,'method':'Quantize cumulative recorded phase boundaries only where decoded total differs from own native Walk contract. Maximum half-centisecond boundary rounding; preserve original changed GIFs/manifests. No synthesized poses.'})
save(out/'sources.json',{'sources':positions,'method':'Chronological sample of actual Unity PNG; group foreground union crops include full actor and HP; no poses synthesized.'})
save(out/'gif_samples.json',{'samples':gif_samples,'method':'Five decoded frames per final GIF; does not claim real-time playback or all-frame visual inspection.'})
save(out/'uncropped_png_selection.json',originals)
save(out/'native_walk_timing.json',timing)
print(json.dumps({'positions':len(positions),'unique_pngs':len({(r['revision'],r['source']) for r in positions}),'gif_samples':len(gif_samples),'boards':[p.name for p in out.glob('*sequence*.png')]+[p.name for p in out.glob('*cycles.png')]+[p.name for p in out.glob('*gif_samples.png')],'timing_changes':changes},ensure_ascii=False))
