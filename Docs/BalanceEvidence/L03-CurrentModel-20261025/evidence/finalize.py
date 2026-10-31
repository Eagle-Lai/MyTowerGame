from candidates import *
import shutil,csv
from PIL import Image,ImageDraw,ImageFont
DOC=ROOT/'Docs/BalanceEvidence/L03-CurrentModel-20261025'
def font(n):return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
def draw_board(r,path):
    towers=r['towerContributions'];m=r['metrics'];route=r['finalPathCells'];s=68;x0=75;y0=170
    im=Image.new('RGB',(1306,950),'#f7f8f5');d=ImageDraw.Draw(im)
    d.text((35,25),'第3关 · S型阵地与最终操作结果',font=font(29),fill='#243535')
    d.text((35,76),f"25波 · 击杀 {m['killed']}/5082 · 漏怪 {m['leaked']} · 生命 {m['hp']}/12 · 实际 {r['stars']}星",font=font(23),fill='#243535')
    d.text((35,115),'坐标从0开始：上方第0行、左侧第0列；绿色实线=地面，紫色虚线=飞行。',font=font(18),fill='#546564')
    for y in range(9):
        d.text((37,y0+y*s+22),str(y),font=font(19),fill='#536565')
        for x in range(17):d.rectangle((x0+x*s,y0+y*s,x0+(x+1)*s,y0+(y+1)*s),fill='white',outline='#cad5d3',width=2)
    for x in range(17):d.text((x0+x*s+25,y0-31),str(x),font=font(18),fill='#536565')
    centers=[(x0+p[0]*s+s//2,y0+p[1]*s+s//2) for p in route]
    if len(centers)>1:d.line(centers,fill='#a9c69b',width=11)
    for a,b in zip(centers,centers[1:]):
        cx=(a[0]+b[0])/2;cy=(a[1]+b[1])/2;dx=(b[0]-a[0])/s;dy=(b[1]-a[1])/s
        d.polygon([(cx+dx*6,cy+dy*6),(cx-dx*4-dy*4,cy-dy*4+dx*4),(cx-dx*4+dy*4,cy-dy*4-dx*4)],fill='#719464')
    for y in range(y0+s//2,y0+8*s+s//2,19):d.line((x0+8*s+s//2,y,x0+8*s+s//2,y+9),fill='#b49fcd',width=2)
    names={1:'普',2:'爆',3:'缓'};colors={1:'#3e6fb5',2:'#b87830',3:'#278c80'}
    for t in towers:
        c=table[t['towerId']];x=x0+t['col']*s+6;y=y0+t['row']*s+6
        d.rounded_rectangle((x,y,x+s-12,y+s-12),radius=8,fill=colors[c['type']])
        label=names[c['type']]+str(c['level']);d.text((x+9,y+14),label,font=font(23),fill='white')
    for y,tx,col in [(0,'起','#405e3e'),(8,'终','#a44840')]:
        x=x0+8*s+s//2;yy=y0+y*s+s//2;d.ellipse((x-23,yy-23,x+23,yy+23),fill=col);d.text((x-13,yy-17),tx,font=font(26),fill='white')
    counts=collections.Counter(table[t['towerId']]['type'] for t in towers)
    d.text((35,805),f"合法地面路线 {len(route)-1} 步 · {len(towers)} 座塔（普{counts[1]} / 爆{counts[2]} / 缓{counts[3]}）",font=font(22),fill='#243535')
    d.text((35,846),f"战斗 {m['combatElapsedSeconds']:.2f}秒；当前五星限时870秒，出怪理论下界1345.28秒。",font=font(20),fill='#8b4b3e')
    d.text((35,884),'来自当前正式配置的Unity真实回放；未改数值、未注资、未跳波。',font=font(19),fill='#546564')
    im.save(path)
def all_rows():
    rows=[]
    for p in OUT.glob('*/unity-results.json'):
        req=OUT/(p.parent.name+'.request.json');inputs=json.loads(req.read_text()) if req.exists() else {}
        for i,r in enumerate(json.loads(p.read_text())):
            m=r['metrics'];rows.append({'batch':p.parent.name,'index':i,'runId':m['runId'],'state':r['state'],'valid':r['valid'],'stars':r['stars'],'victory':m['victory'],'waves':m['completedWaveCount'],'killed':m['killed'],'leaked':m['leaked'],'hp':m['hp'],'combatSeconds':m['combatElapsedSeconds'],'operations':len(r['operations']),'stepSeconds':r['stepSeconds'],'operationError':r.get('operationError'),'input':inputs.get('runs',[{}]*(i+1))[i].get('operationsPath')})
    return rows
if __name__=='__main__':
    rows=all_rows();dump(DOC/'trial-index.json',rows)
    if len(sys.argv)>2:
        source=pathlib.Path(sys.argv[1]);idx=int(sys.argv[2]);r=json.loads(source.read_text())[idx]
        dump(DOC/'selected-result.json',r);dump(DOC/'best-operations.json',[{k:o[k] for k in ['waveOrdinal','timeMs','action','row','col','towerId']} for o in r['operations']])
        dump(DOC/'operations-with-cash.json',r['operations']);dump(DOC/'final-layout.json',{'towers':r['towerContributions'],'groundPath':r['finalPathCells']})
        draw_board(r,DOC/'最终布阵图.png')
        with (DOC/'完整操作流水.csv').open('w',encoding='utf-8-sig',newline='') as f:
            fields=['序号','波次','波内毫秒','动作','行','列','塔ID','花费','余额'];w=csv.writer(f);w.writerow(fields)
            for n,o in enumerate(r['operations'],1):w.writerow([n,o['waveOrdinal'],o['timeMs'],o['action'],o['row'],o['col'],o['towerId'],o['cost'],o['balanceAfter']])
        print('Selected',source,idx,r['stars'],r['metrics']['leaked'])
    print('Trials',len(rows))
