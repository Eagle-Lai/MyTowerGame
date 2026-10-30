from serial_common import *
from PIL import Image,ImageDraw
import numpy as np,shutil
owner();A=D/'staged_art';R=D/'raster_revision_03';R.mkdir()
for p in A.iterdir():
    if p.is_file():shutil.copy2(p,R/p.name)
shutil.copy2(D/'transparency_detail_final.png',R/'transparency_detail_before.png')
# Restore crisp cel regions where the previous local fill blurred source-colored shell patches.
for direction in ['Up','Down']:
    original=Image.open(D/'raster_revision_02'/(direction+'_Body.png')).convert('RGBA')
    w,h=original.size
    box=(137,0,214,94) if direction=='Up' else (103,0,177,87)
    cone=original.crop(box);cw,ch=cone.size;mask=Image.new('L',cone.size);md=ImageDraw.Draw(mask)
    md.polygon([(cw*.5,0),(cw*.76,ch*.13),(cw-1,ch*.83),(cw*.92,ch*.96),(cw*.67,ch-1),(cw*.25,ch-1),(0,ch*.87),(cw*.10,ch*.48),(cw*.31,ch*.10)],fill=255)
    a=np.asarray(cone).copy();a[:,:,3]=np.minimum(a[:,:,3],np.asarray(mask));cone=Image.fromarray(a)
    S=3;im=Image.new('RGBA',(w*S,h*S));dr=ImageDraw.Draw(im)
    xy=lambda pts:[(round(x*w*S),round(y*h*S)) for x,y in pts]
    dark=(54,43,22,255);gold=(214,153,33,255);light=(235,181,65,255);ochre=(151,102,17,255);shade=(183,123,18,255)
    dr.ellipse((.02*w*S,.15*h*S,.98*w*S,.99*h*S),fill=dark)
    for top,bottom in [(.17,.63),(.41,.84),(.67,.98)]:
        dr.ellipse((.04*w*S,top*h*S,.96*w*S,bottom*h*S),fill=gold,outline=dark,width=5*S)
        dr.ellipse((.12*w*S,(top+.025)*h*S,.82*w*S,(top+.13)*h*S),fill=light)
    patches=[[(.13,.32),(.22,.29),(.29,.35),(.25,.42),(.16,.41)],[(.70,.25),(.81,.31),(.88,.43),(.80,.44),(.72,.37)],[(.20,.57),(.31,.51),(.39,.56),(.34,.65),(.24,.66)],[(.70,.56),(.82,.61),(.87,.70),(.78,.74),(.70,.68)],[(.36,.78),(.46,.76),(.55,.86),(.50,.94),(.40,.91)],[(.67,.80),(.79,.78),(.84,.87),(.73,.92)]]
    for pts in patches:dr.polygon(xy(pts),fill=ochre)
    im=im.resize((w,h),Image.Resampling.LANCZOS)
    for cy,ratio in ([(.34,.62),(.60,.82),(.88,1)] if direction=='Up' else [(.31,.70),(.56,.90),(.82,1)]):
        p=cone.resize((round(cw*ratio),round(ch*ratio)),Image.Resampling.LANCZOS)
        im.alpha_composite(p,(round(w*.5-p.width/2),round(h*cy-p.height)))
    im.save(A/(direction+'_Body.png'))
# Use the original rear-head colors with an exact smooth shell silhouette and two existing horns.
src=Image.open(D/'raster_revision_01/Up_HeadNormal.png').convert('RGBA')
w,h=src.size;mask=Image.new('L',src.size);dr=ImageDraw.Draw(mask)
dr.ellipse((42,53,215,221),fill=255)
dr.polygon([(32,76),(31,27),(41,4),(58,1),(83,11),(115,43),(96,69),(74,93)],fill=255)
dr.polygon([(143,43),(174,13),(198,1),(214,6),(224,25),(222,64),(207,91),(178,79)],fill=255)
a=np.asarray(src).copy();a[:,:,3]=np.minimum(a[:,:,3],np.asarray(mask));head=Image.fromarray(a)
ImageDraw.Draw(head).arc((42,53,215,221),0,360,fill=(54,43,22,255),width=5)
for name in ['Up_HeadNormal','Up_HeadAngry','Up_HeadDead']:head.save(A/(name+'.png'))
# Remove disconnected flecks left in the open tail arch and other transparent exterior regions.
for p in A.glob('*.png'):
    if p.name.startswith(NAME+'_'):continue
    a=np.asarray(Image.open(p).convert('RGBA')).copy();on=a[:,:,3]>0;seen=np.zeros(on.shape,bool);comps=[]
    for yy,xx in zip(*np.where(on)):
        if seen[yy,xx]:continue
        todo=[(int(yy),int(xx))];seen[yy,xx]=1;comp=[]
        while todo:
            y,x=todo.pop();comp.append((y,x))
            for dy,dx in [(0,1),(0,-1),(1,0),(-1,0),(-1,-1),(-1,1),(1,-1),(1,1)]:
                ny,nx=y+dy,x+dx
                if 0<=ny<a.shape[0] and 0<=nx<a.shape[1] and on[ny,nx] and not seen[ny,nx]:seen[ny,nx]=1;todo.append((ny,nx))
        comps.append(comp)
    main=max(comps,key=len)
    for comp in comps:
        if comp is not main:
            for y,x in comp:a[y,x]=0
    Image.fromarray(a).save(p)
m=read(A/(NAME+'_Directions.sprites.json'));atlas=Image.new('RGBA',(2048,2048))
for s in m['sprites']:atlas.alpha_composite(Image.open(A/(s['name']+'.png')),(s['x'],2048-s['y']-s['h']))
atlas.save(A/(NAME+'_Directions.png'))
board=Image.new('RGB',(1600,840),(40,48,37));dr=ImageDraw.Draw(board)
keys=['Up_HeadNormal','Up_Body','Up_LegFront','Up_Tail','Down_HeadNormal','Down_Body','Down_Claw','Down_Tail']
for i,key in enumerate(keys):
    im=Image.open(A/(key+'.png'));im.thumbnail((380,380));x=i%4*400+(400-im.width)//2;y=i//4*420+30
    board.paste(im,(x,y),im);dr.text((i%4*400+6,i//4*420+8),key,fill='white')
board.save(D/'parts_final_retouch.png')
write(R/'retouch_record.json',dict(observed_at=now(),parent='raster_revision_02',reason='Checkerboard detail review found blurred local shell fill and small head-edge fragments; revised to crisp source-palette three-plate cel regions, reused three existing spine shapes and removed detached flecks.',method='Local raster repair, not a new AI return',final_staged={p.name:sha(p) for p in A.iterdir() if p.is_file()}))
