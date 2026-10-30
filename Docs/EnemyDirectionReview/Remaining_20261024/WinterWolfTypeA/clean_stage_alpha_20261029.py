from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
from collections import deque
from datetime import datetime,timezone,timedelta
import hashlib,json,shutil
import numpy as np
HERE=Path(__file__).resolve().parent
RUN=HERE.parent
art=HERE/'staged_art'
backup=HERE/'staged_art_before_alpha_r01';assert not backup.exists();shutil.copytree(art,backup)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
records=[]
for p in sorted(art.glob('*.png')):
    if p.name.startswith('WinterWolfTypeA_Directions'):continue
    a=np.array(Image.open(p).convert('RGBA'))
    exterior=ImageOps.expand(Image.fromarray(np.where(a[:,:,3]==0,0,255).astype('uint8')),border=1,fill=0)
    ImageDraw.floodfill(exterior,(0,0),128)
    holes=np.asarray(exterior)[1:-1,1:-1]==0
    pending=set(zip(*np.where(holes)))
    hole_sizes=[]
    while pending:
        seed=pending.pop();queue=deque([seed]);component=[seed];boundary=[]
        while queue:
            y,x=queue.popleft()
            for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
                if not(0<=yy<a.shape[0] and 0<=xx<a.shape[1]):continue
                if (yy,xx) in pending:pending.remove((yy,xx));queue.append((yy,xx));component.append((yy,xx))
                elif a[yy,xx,3]:boundary.append(a[yy,xx,:3])
        assert len(component)<=50 and boundary, (p,len(component))
        color=np.median(np.asarray(boundary),axis=0).astype('uint8')
        for y,x in component:a[y,x]=[*color,255]
        hole_sizes.append(len(component))
    # Keep the complete silhouette. Report detached pixels without silently dropping any large organ.
    visited=np.zeros(a.shape[:2],dtype=bool);components=[]
    for y,x in zip(*np.where(a[:,:,3]>0)):
        if visited[y,x]:continue
        component=[];queue=deque([(y,x)]);visited[y,x]=True
        while queue:
            yy,xx=queue.popleft();component.append((yy,xx))
            for y2,x2 in [(yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)]:
                if 0<=y2<a.shape[0] and 0<=x2<a.shape[1] and not visited[y2,x2] and a[y2,x2,3]:visited[y2,x2]=True;queue.append((y2,x2))
        components.append(component)
    removed=0
    for component in components:
        if len(component)<=4:
            for y,x in component:a[y,x]=0
            removed+=len(component)
    Image.fromarray(a,'RGBA').save(p)
    records.append({'part':p.name,'before_sha256':sha(backup/p.name),'after_sha256':sha(p),
                    'hole_pixels_filled':int(holes.sum()),'hole_components':hole_sizes,
                    'dust_pixels_removed':removed,'largest_components':sorted([len(x) for x in components],reverse=True)[:5]})
manifest=json.loads((art/'WinterWolfTypeA_Directions.sprites.json').read_text())
atlas=Image.new('RGBA',(manifest['width'],manifest['height']))
for s in manifest['sprites']:
    im=Image.open(art/(s['name']+'.png')).convert('RGBA');assert im.size==(s['w'],s['h'])
    atlas.alpha_composite(im,(s['x'],manifest['height']-s['y']-s['h']))
atlas.save(art/'WinterWolfTypeA_Directions.png')
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,s in enumerate(manifest['sprites']):
    piece=Image.open(art/(s['name']+'.png')).convert('RGBA');piece.thumbnail((195,300))
    proof.paste(piece,(i%8*200+(200-piece.width)//2,i//8*350+35),piece);draw.text((i%8*200+5,i//8*350+8),s['name'],fill='white')
shutil.copy2(HERE/'parts_clean.png',HERE/'parts_clean_before_alpha_r01.png')
proof.save(HERE/'parts_clean.png')
layout_path=HERE/'layout_adjustments.json';layout=json.loads(layout_path.read_text())
shutil.copy2(layout_path,HERE/'layout_adjustments_before_tail_scale_r01.json')
layout['parts']['Up/Tail']['width']=.30;layout['parts']['Down/Tail']['width']=.30
layout_path.write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
report={'method':'Only fill small enclosed chroma-mask holes from opaque boundary median; remove isolated components<=4pixels, preserve silhouette dimensions and rebuild atlas in existing rects.',
        'parts':records,'filled_pixels':sum(x['hole_pixels_filled'] for x in records),
        'removed_dust_pixels':sum(x['dust_pixels_removed'] for x in records),'source_raws_preserved':True}
(HERE/'staged_alpha_cleanup_r01_20261029.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
now=datetime.now(timezone(timedelta(hours=8))).isoformat()
chain_path=RUN/'conversation_chain.json';chain=json.loads(chain_path.read_text());assert chain['state']=='active' and chain['current_character']=='WinterWolfTypeA'
chain.update(current_stage='staged_art_review_after_Down03_HTTP200',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/staged_alpha_cleanup_r01_20261029.json',updated_at=now)
chain_path.write_text(json.dumps(chain,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
live=f'{now} WinterWolfTypeA113继续中：用户已实施generate.mjs固定aihub.dog→191.101.132.254修复，本次独立有限Down03直连请求HTTP200，未新增付费诊断；旧Down3次结果/费用unknown及standing2/2消耗保留。选Up本地03与Down03实际区域，排除额外后脑，14分件2048atlas/PPU100，正在审透明/连接/布局，未安装/Play/record。101/108、AllGIF1642。chain active保留原owner/token。历史阻塞报告保留，当前以progress、chain、WinterWolfTypeA证据为准。'
for path,begin,end in [(RUN.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=path.read_text();prefix,rest=text.split(begin,1);old,suffix=rest.split(end,1);path.write_text(prefix+begin+'\n'+live+'\n'+end+suffix,encoding='utf-8')
print(json.dumps({'filled_pixels':report['filled_pixels'],'dust_removed':report['removed_dust_pixels']}))
