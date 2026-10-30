from session_winterwarg import *
from PIL import Image,ImageDraw
import math,shutil
owner();runs=['runtime_art_r02','runtime_art_updeath_r02'];out=D/'visual_review_art_r02_full_actor_20261029';assert not out.exists();out.mkdir()
seconds=next(c['length'] for c in read(D/'source_contract_20261029.json')['contract']['clips'] if c['name']=='Walk');assert seconds==.5
positions=[];gif_samples=[];originals=[];full=[];timing=[]
def pick(rows,n):
    return [rows[round((len(rows)-1)*i/(n-1))] for i in range(n)]
def board(run,tag,rows,axial=False):
    cellw,cellh=220,250;crop=(300,235,535,565) if axial else (80,235,700,650)
    sheet=Image.new('RGB',(cellw*6,cellh*math.ceil(len(rows)/6)),(40,48,37));draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        p=D/run/r['file'];im=Image.open(p).convert('RGB').crop(crop);im.thumbnail((212,215),Image.Resampling.LANCZOS)
        x,y=i%6*cellw,i//6*cellh;sheet.paste(im,(x+(cellw-im.width)//2,y+32))
        draw.text((x+3,y+3),f"{r['stage']} {r['facing']} f{r['frame']}\nn{r['normalizedTime']:.3f} a{r['alpha']:.2f}",fill='white')
        positions.append({'revision':run,'source':r['file'],'source_sha256':sha(p),'board':tag+'.png','position':i,'crop':list(crop),'frame':r['frame'],'stage':r['stage']})
    sheet.save(out/(tag+'.png'))
for run in runs:
    folder=D/run;records=[json.loads(l) for l in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l]
    assert 'FAIL ' not in (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8')
    groups={s:[r for r in records if r['stage']==s] for s in dict.fromkeys(r['stage'] for r in records)}
    cycles={}
    for stage in ['UpWalk','DownWalk']:
        samples=[r for r in groups[stage] if r['state']=='Walk'];start=math.ceil(samples[0]['normalizedTime']);cycles[stage]=[r for r in samples if start<=r['normalizedTime']<start+1]
    for name in ['UpWalk.gif','DownWalk.gif','up_down_walk.gif']:
        with Image.open(folder/name) as gif:
            durations=[]
            for i in range(gif.n_frames):gif.seek(i);durations.append(gif.info['duration'])
        timing.append({'revision':run,'file':name,'native_seconds':seconds,'encoded_ms':sum(durations),'durations_ms':durations})
    assert all(x['encoded_ms']==500 for x in timing if x['revision']==run),'Inspect GIF timing; preserve old media before correcting.'
    sets=[['UpWalk','DownWalk','LeftWalk','RightWalk'],['Idle','Ready','Walk','Run'],['Attack','Hurt','DeathAutoRecycle','Reuse'],['Pause','Resume1x','Speed2x','Speed3x']]
    for i,stages in enumerate(sets):board(run,run+'_sequence_'+str(i),[r for stage in stages for r in pick(groups[stage],6)])
    board(run,run+'_turns_flying',pick(groups['ContinuousTurns'],12)+pick(groups['Flying'],6))
    board(run,run+'_walk_cycle',cycles['UpWalk']+cycles['DownWalk'],True)
    originals.extend(run+'/'+r['file'] for r in [pick(groups['UpWalk'],3)[1],pick(groups['DownWalk'],3)[1],next(r for r in groups['Attack'] if r['facing']=='Down' and r['expression']==1),next(r for r in groups['DeathAutoRecycle'] if .3<r['alpha']<.85)])
    cells=[]
    for path in sorted(folder.glob('*.gif')):
        with Image.open(path) as gif:
            indices=sorted(set(round((gif.n_frames-1)*i/4) for i in range(5)))
            crop=(50,175,gif.width-35,gif.height-12)
            for index in indices:
                gif.seek(index);im=gif.convert('RGB').crop(crop);im.thumbnail((290,210),Image.Resampling.LANCZOS)
                cell=Image.new('RGB',(300,245),(40,48,37));cell.paste(im,((300-im.width)//2,32+(210-im.height)//2));ImageDraw.Draw(cell).text((4,4),f'{path.name} f{index}',fill='white');cells.append(cell)
                gif_samples.append({'revision':run,'file':path.name,'gif_sha256':sha(path),'frame_index_zero_based':index,'frame_count':gif.n_frames,'duration_ms':gif.info.get('duration'),'crop':list(crop),'sample_sha256':hashlib.sha256(im.tobytes()).hexdigest().upper()})
            if path.name in ['UpWalk.gif','attack_death_reuse.gif']:
                index=gif.n_frames//2;gif.seek(index);p=out/(run+'_'+path.stem+'_uncropped.png');gif.convert('RGB').save(p)
                full.append({'source':path.relative_to(D).as_posix(),'source_sha256':sha(path),'frame':index,'output':p.relative_to(D).as_posix(),'output_sha256':sha(p)})
    sheet=Image.new('RGB',(1500,1470),(40,48,37));assert len(cells)==30
    for i,cell in enumerate(cells):sheet.paste(cell,(i%5*300,i//5*245))
    sheet.save(out/(run+'_gif_samples.png'))
write(out/'sources.json',{'sources':positions,'method':'Chronological sample of real Unity PNG; fixed documented crop; no generated pose.'},True)
write(out/'gif_samples.json',{'samples':gif_samples,'method':'Five encoded frames per final GIF; not real-time playback or every-frame review.'},True)
write(out/'uncropped_gif_sources.json',full,True)
write(out/'original_png_selection.json',originals,True)
write(out/'native_walk_timing.json',timing,True)
print(json.dumps({'positions':len(positions),'unique_pngs':len({(r['revision'],r['source']) for r in positions}),'gif_samples':len(gif_samples),'originals':originals,'boards':[p.name for p in out.glob('*.png')],'timing':timing},ensure_ascii=False))
