"""Render only observed real results. Drafts remain explicitly uncalibrated."""
from formal_tools import *
from PIL import Image,ImageDraw,ImageFont
import collections,sys,csv
resultfile=pathlib.Path(sys.argv[1]);index=int(sys.argv[2]);out=pathlib.Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
result=json.loads(resultfile.read_text(encoding='utf-8'))
if isinstance(result,list):result=result[index]
m=result['metrics'];level=result['levelId'];ops=result['operations'];t={r['id']:r for r in tables()['tbtowerinfo']}
scene=next(r for r in tables()['tbsceneinfo']if r['id']==level);mp=next(r for r in tables()['tblevelmap']if r['id']==scene['mapId']);cells=mp['cells']
assert result['victory'] and m['completedWaveCount']==25 and result['initialGold']==100 and not m['debugOverride']
layout={}
for o in ops:
    key=(o['row'],o['col'])
    if o['action']=='sell':assert layout.pop(key)==o['towerId']
    elif o['action']=='build':assert key not in layout;layout[key]=o['towerId']
    else:assert t[layout[key]]['upgradeTo']==o['towerId'];layout[key]=o['towerId']
assert layout=={(x['row'],x['col']):x['towerId']for x in result['towerContributions']}
name={1:'普',2:'爆',3:'缓'};colors={1:'#3d6cac',2:'#b57534',3:'#2b897b'}
def label(tid):return name[t[tid]['type']]+str(t[tid]['level'])
fontpath='C:/Windows/Fonts/msyh.ttc'
def font(n):return ImageFont.truetype(fontpath,n)
def draw_board(target,board,path,title,subtitle,highlight=()):
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
        d.text((x+(size-18)/2,y+(size-18)/2),label(tid),font=font(25),fill='white',anchor='mm')
    for ch,text in [('S','起'),('E','终')]:
        x,y=center(endpoints[ch]);d.ellipse((x-25,y-25,x+25,y+25),fill='#46623e'if ch=='S'else'#8e493f');d.text((x,y),text,font=font(24),anchor='mm',fill='white')
    y=top+rows*size+30;counts=collections.Counter(t[i]['type']for i in board.values())
    d.text((60,y),f'地面路线 {len(path)-1} 步（相邻格移动边数）；{len(board)} 座塔：普 {counts[1]} / 爆 {counts[2]} / 缓 {counts[3]}。',font=font(22),fill='#25312e')
    d.text((60,y+42),'绿色箭头：地面路线；紫色虚线：空中直达方向；金边：本阶段改动格。',font=font(20),fill='#59635b')
    d.text((60,y+80),'本图由实际操作、最终塔清单及寻路记录绘制；首次成功，最终校准与严格复跑仍待完成。',font=font(19),fill='#59635b')
    im.save(target)
subtitle=f"25/25 波 · {m['killed']}/{m['expectedEnemyCount']} 击杀 · {m['leaked']} 漏怪 · 生命 {m['hp']}/{m['maxHp']} · 实际 {result['stars']} 星"
draw_board(out/'首次成功布阵图.png',layout,result['finalPathCells'],f'第 {level} 关：首次成功布局（最终操作后，待最终认证）',subtitle,{(o['row'],o['col'])for o in ops if o['waveOrdinal']==25 and o['timeMs']>0})
cash=[];previous=100
for w in m['waves']:
    wo=[o for o in ops if o['waveOrdinal']==w['ordinal']];spend=sum(max(0,o['cost'])for o in wo);refund=-sum(min(0,o['cost'])for o in wo)
    expected=previous+w['killGold']+w['clearGold']+refund-spend;assert expected==w['gold'],(w['ordinal'],expected,w['gold'])
    cash.append(dict(wave=w['ordinal'],before=previous,kill=w['killGold'],clear=w['clearGold'],spend=spend,refund=refund,after=w['gold'],hp=w['hp'],spawned=w['successfulSpawned'],killed=w['killed'],leaked=w['leaked'],combatSeconds=w['combatEndSeconds']-w['combatStartSeconds']))
    previous=w['gold']
assert previous==result['finalGold'];assert all(o['balanceAfter']>=0 for o in ops)
(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');(out/'operations.json').write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8');(out/'cashflow.json').write_text(json.dumps(cash,ensure_ascii=False,indent=2),encoding='utf-8')
lines=[f'# 第 {level} 关首次成功逐波记录（开发证据，未最终认证）','',f"真实 runId：`{m['runId']}`。版本：`{result['versionKey']}`。",'',f"{subtitle}。战斗 {m['combatElapsedSeconds']:.2f} 秒，终局金币 {result['finalGold']}。",'',f"配置封印：`{result['profile']['runtimeContentHash']}`。固定步长 {result['stepSeconds']} 秒、1 倍速，资金策略 {result['fundingPolicy']}。存档由既有隔离回放入口保护，无 debugOverride。",'','本记录保留首次结果；最终数据版本、时间校准和两次严格复跑尚未完成。固定步长回放未验证手动触控执行难度。','', '![最终操作后的布局](首次成功布阵图.png)','', '## 完整 W1—W25 操作','', '|波|实际时机|操作顺序、费用及余额|','|---:|---|---|']
for wave in range(1,26):
    wo=[(i+1,o)for i,o in enumerate(ops)if o['waveOrdinal']==wave]
    if not wo:lines.append(f'|{wave}|—|无|')
    for seq,o in wo:
        action={'build':'建造','upgrade':'升级','sell':'出售'}[o['action']];when='波前'if o['timeMs']==0 else f"本波 {o['timeMs']/1000:.2f} 秒"
        money=f"退款 {-o['cost']}"if o['cost']<0 else f"支出 {o['cost']}"
        lines.append(f"|{wave}|{when}|#{seq} {action} ({o['row']},{o['col']}) {label(o['towerId'])}；{money}；余额 {o['balanceAfter']}|")
lines+=['','## 逐波现金流与结果','','|波|波前金|击杀金|清波金|建造升级|退款|结余|出生/击杀/漏|生命|战斗秒|','|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|']
for w in cash:lines.append(f"|{w['wave']}|{w['before']}|{w['kill']}|{w['clear']}|{w['spend']}|{w['refund']}|{w['after']}|{w['spawned']}/{w['killed']}/{w['leaked']}|{w['hp']}|{w['combatSeconds']:.2f}|")
lines+=['','## 最终逐塔清单','','|坐标|塔型等级|全局伤害|空中命中|减速次数|复入射程后生效次数|','|---|---|---:|---:|---:|---:|']
for row in sorted(result['towerContributions'],key=lambda x:(x['row'],x['col'])):lines.append(f"|({row['row']},{row['col']})|{label(row['towerId'])}|{row['damage']:.2f}|{row['airHits']}|{row['slowApplications']}|{row['repeatEffectEnemies']}|")
lines+=['','## 总账与来源','',f"`100 + 击杀 {sum(w['kill']for w in cash)} + 清波 {sum(w['clear']for w in cash)} + 退款 {sum(w['refund']for w in cash)} − 支出 {sum(w['spend']for w in cash)} = {previous}`。每波现金守恒，最小操作后余额 {min(o['balanceAfter']for o in ops)}。",'', '[完整原始结果](result.json) · [实际操作](operations.json) · [逐波资金账](cashflow.json)','',f'原始批次：`{resultfile.as_posix()}`，索引 {index}。完整候选比较见本关 trial-index.json；本稿尚未提供最终最佳方案结论。']
(out/'首次成功逐波记录.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(out,len(ops),'operations; cash reconciled')
