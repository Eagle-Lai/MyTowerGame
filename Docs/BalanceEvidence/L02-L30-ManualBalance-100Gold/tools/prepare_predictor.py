"""Create an isolated read-only prediction model; never change shipped combat."""
from formal_tools import *
source=(ROOT/'.workbuddy/tools/balance_simulator.py').read_text(encoding='utf-8')
source=source.replace("VERSION='spatial-fixed-step-30x25-maze-v6-astar'","VERSION='manual-prediction-air-priority-reverse-towers-r1'")
old="""                if target is None and t['searchTimer']+1e-9>=cfg['searchIntervalMs']/1000:
                    t['searchTimer']=0
                    options=[e for e in alive if e['alive'] and (not e['cfg']['isFlying'] or cfg['canAttackAir']) and d2(t['cell'],position(e))<=radius2]
                    if options:
                        # Normalized path progress; persistent lock until out of range.
                        target=max(options,key=lambda e:(e['segment']+e['segmentProgress'])/max(1,len(e['path'])-1));t['target']=target
"""
new="""                if t['searchTimer']+1e-9>=cfg['searchIntervalMs']/1000:
                    t['searchTimer']=0
                    if target is None or cfg['canAttackAir'] and not target['cfg']['isFlying']:
                        options=[e for e in alive if e['alive'] and (not e['cfg']['isFlying'] or cfg['canAttackAir']) and d2(t['cell'],position(e))<=radius2]
                        air=[e for e in options if e['cfg']['isFlying']]
                        if air:options=air
                        elif target is not None:options=[]
                        if options:
                            mode=cfg.get('targetMode',0)
                            def rank(e):
                                if mode==1:return -d2(t['cell'],position(e))
                                if mode==2:return e['hp']
                                return 0 if e['cfg']['isFlying'] else (e['segment']+1)/max(1,len(e['path'])-1)
                            target=max(options,key=rank);t['target']=target
"""
assert source.count(old)==1;source=source.replace(old,new)
old="            for t in towers:\n                cfg=tower_table[t['id']];radius2=cfg['radius']**2"
assert source.count(old)==1;source=source.replace(old,"            for t in reversed(towers):\n                cfg=tower_table[t['id']];radius2=cfg['radius']**2")
source=source.replace("(new['effectValue']-old['effectValue'])*400*g","(new['effectValue']-old['effectValue'])*POLICY.get('slowUpgradeWeight',160)*g")
old="        if 0<=y<len(cells) and 0<=x<len(cells[0]) and cells[y][x]=='.' and cell not in blocked and path_for(cells,blocked+[cell]):return cell,tid"
assert source.count(old)==1
source=source.replace(old,"        if 0<=y<len(cells) and 0<=x<len(cells[0]) and cells[y][x]=='.' and cell not in blocked and path_for(cells,blocked+[cell]):\n            hinted=next((h['towerId']for h in POLICY.get('towerTypeHints',[])if h['row']==y and h['col']==x),tid)\n            return cell,hinted")
source=source.replace("'Four-direction path search mirrors shipped AStarWrapper insertion ties; battle timing still approximate',","'Air priority, periodic ground-to-air retargeting and reverse tower order follow current code; spatial-grid tie order remains approximate',\n 'Four-direction path search mirrors shipped AStarWrapper insertion ties; battle timing still approximate',")
(REPORT/'tools/predictor.py').write_text(source,encoding='utf-8');print('isolated predictor created')
