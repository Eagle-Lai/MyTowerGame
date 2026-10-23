"""Show observed transaction stages without presenting development evidence as final."""
from formal_tools import *
from evidence_drawing import draw_board
import sys,shutil
source=pathlib.Path(sys.argv[1]);index=int(sys.argv[2]);out=pathlib.Path(sys.argv[3]);r=json.loads(source.read_text(encoding='utf-8'))[index]
assert r['victory']and r['metrics']['leaked']==0
t=tables();tower={x['id']:x for x in t['tbtowerinfo']};scene=next(x for x in t['tbsceneinfo']if x['id']==r['levelId']);mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId']);dest=out/'阶段图';dest.mkdir(parents=True,exist_ok=True)
lines=['# 首次成功的实际换塔阶段（开发证据）','',f"runId：`{r['metrics']['runId']}`。封印：`{r['profile']['runtimeContentHash']}`。最终校准和两次严格复跑尚待完成。",'']
for i,s in enumerate(r.get('operationStages',[])):
    filename=f"stage-{i:02}-W{s['waveOrdinal']}-at{s['timeMs']}-{s['phase']}.png"
    board={(x['row'],x['col']):x['towerId']for x in s['layout']}
    title=f"L{r['levelId']:02} W{s['waveOrdinal']} {s['timeMs']/1000:.2f}秒："+('交易前'if s['phase']=='before'else'交易后')
    subtitle=f"已执行{s['operationCount']}笔操作；余额{s['cash']}；生命{s['hp']}；实际路径{len(s['pathCells'])-1}步。"
    recent=[o for o in r['operations'][:s['operationCount']]if o['waveOrdinal']==s['waveOrdinal']and o['timeMs']==s['timeMs']]
    draw_board(dest/filename,board,s['pathCells'],title,subtitle,{(o['row'],o['col'])for o in recent},t=tower,mp=mp,footer='来自实际交易时点的布局和寻路；开发证据，最终校准与严格复跑待完成。')
    lines += [f'## {title}','',subtitle,'',f'![{title}](阶段图/{filename})','']
    if s.get('screenshot'):
        screenshot=source.parent/pathlib.Path(s['screenshot']).name
        if screenshot.exists():
            shutil.copy2(screenshot,dest/screenshot.name);lines += [f'![实际Unity截图](阶段图/{screenshot.name})','']
(out/'实际换塔阶段.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(len(r.get('operationStages',[])),'observed stages drawn')
