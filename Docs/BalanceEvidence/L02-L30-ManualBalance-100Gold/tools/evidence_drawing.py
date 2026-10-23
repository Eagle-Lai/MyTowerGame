from PIL import Image,ImageDraw,ImageFont
import collections
name={1:'普',2:'爆',3:'缓'};colors={1:'#3d6cac',2:'#b57534',3:'#2b897b'}
def label(tid,t):return name[t[tid]['type']]+str(t[tid]['level'])
fontpath='C:/Windows/Fonts/msyh.ttc'
def font(n):return ImageFont.truetype(fontpath,n)
def draw_board(target,board,path,title,subtitle,highlight=(),*,t,mp,footer="来自同版 Unity 实测；固定步长回放，未验证手动触控。"):
    cells=mp['cells']
    size=86;left=100;top=210;cols=mp['cols'];rows=mp['rows'];width=max(1300,left+cols*size+85);height=top+rows*size+210
    im=Image.new('RGB',(width,height),'#f6f5f0');d=ImageDraw.Draw(im)
    d.text((60,30),title,font=font(34),fill='#25312e');d.text((60,88),subtitle,font=font(20),fill='#25312e')
    d.text((60,126),'坐标：(行,列)，从 0 开始；图上方为第 0 行。路径采用 Unity 实测记录。',font=font(19),fill='#59635b')
    for c in range(cols):d.text((left+c*size+size/2,top-32),str(c),font=font(20),anchor='mm',fill='#5f6f64')
    for r,row in enumerate(cells):
        d.text((left-35,top+r*size+size/2),str(r),font=font(20),anchor='mm',fill='#5f6f64')
        for c,ch in enumerate(row):
            x=left+c*size;y=top+r*size;fill='#ffffff'if ch in '.SE'else'#bec4c0'if ch=='#'else'#e8e2cf'
            d.rectangle((x,y,x+size,y+size),fill=fill,outline='#ced6d0',width=2)
    def center(p):return(left+(p[0]+.5)*size,top+(p[1]+.5)*size)
    points=[center(p)for p in path]
    if len(points)>1:
        d.line(points,fill='#b2c9a4',width=16,joint='curve')
        for a,b in zip(points,points[1:]):
            x=(a[0]+b[0])/2;y=(a[1]+b[1])/2;vx=(b[0]-a[0])/size;vy=(b[1]-a[1])/size
            d.polygon([(x+vx*9,y+vy*9),(x-vx*5-vy*5,y-vy*5+vx*5),(x-vx*5+vy*5,y-vy*5-vx*5)],fill='#638456')
    endpoints={ch:(c,r)for r,row in enumerate(cells)for c,ch in enumerate(row)if ch in 'SE'}
    a=center(endpoints['S']);b=center(endpoints['E'])
    # Dashed air direction is a geometry reference, never a substitute for the ground path.
    for k in range(0,40,2):
        p=(a[0]+(b[0]-a[0])*k/40,a[1]+(b[1]-a[1])*k/40);q=(a[0]+(b[0]-a[0])*(k+1)/40,a[1]+(b[1]-a[1])*(k+1)/40)
        d.line([p,q],fill='#b3a6c3',width=3)
    for (r,c),tid in board.items():
        x=left+c*size+9;y=top+r*size+9;cfg=t[tid]
        d.rounded_rectangle((x,y,x+size-18,y+size-18),radius=10,fill=colors[cfg['type']],outline='#deb04e'if(r,c)in highlight else colors[cfg['type']],width=4)
        d.text((x+(size-18)/2,y+(size-18)/2),label(tid,t),font=font(25),fill='white',anchor='mm')
    for ch,text in [('S','起'),('E','终')]:
        x,y=center(endpoints[ch]);d.ellipse((x-25,y-25,x+25,y+25),fill='#46623e'if ch=='S'else'#8e493f');d.text((x,y),text,font=font(24),anchor='mm',fill='white')
    y=top+rows*size+30;counts=collections.Counter(t[i]['type']for i in board.values())
    d.text((60,y),f'地面路线 {len(path)-1} 步（相邻格移动边数）；{len(board)} 座塔：普 {counts[1]} / 爆 {counts[2]} / 缓 {counts[3]}。',font=font(22),fill='#25312e')
    d.text((60,y+42),'绿色箭头：地面路线；紫色虚线：空中直达方向；金边：本阶段改动格。',font=font(20),fill='#59635b')
    d.text((60,y+80),footer,font=font(19),fill='#59635b')
    im.save(target)
