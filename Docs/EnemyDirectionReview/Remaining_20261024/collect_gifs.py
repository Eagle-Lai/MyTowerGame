"""Copy every available review GIF into one flat folder, preserving source and version identity."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,html,json,shutil
from urllib.parse import quote
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
OUT=BASE/'AllGIF'
OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--render-only',action='store_true',help='Reuse the archive manifest; only rebuild the page and movement index')
args=parser.parse_args()
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8')) if args.render_only else None
items=manifest['files'] if manifest else []
progress_path=HERE/'progress.json'
review_items={x['name']:x for x in json.loads(progress_path.read_text(encoding='utf-8'))['items']} if progress_path.exists() else {}
approved={'AdvancedHen','Bat','BattlePanther','Bear','BearMounted','BlackBoar','Boar','BoarMounted'}
for source in ([] if args.render_only else sorted(BASE.rglob('*.gif'))):
    if OUT in source.parents: continue
    relative=source.relative_to(BASE).as_posix()
    digest=hashlib.sha256(source.read_bytes()).hexdigest().upper()
    name='__'.join(source.relative_to(BASE).parts)
    if len(name)>180: name=name[:140]+'__'+digest[:16]+'.gif'
    dest=OUT/name
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest().upper()!=digest:
        name=dest.stem+'__'+digest[:16]+'.gif';dest=OUT/name
    if not dest.exists(): shutil.copy2(source,dest)
    final=False
    parts=source.relative_to(BASE).parts
    if len(parts)>3 and parts[0]=='Batch01_10' and parts[1] in approved:
        final=parts[2]==('runtime_r02' if parts[1]=='Bat' else 'runtime_r01')
    if parts[0]=='AnimationPolish_20261023' and ('BlackBear' in source.name or 'BlackWolf' in source.name): final=True
    if parts[0]=='Batch01_10' and len(parts)>3 and parts[1] in ['BlackBear','BlackWolf'] and parts[2] in ['runtime_polish_r01','runtime_polish_updeath_r02']: final=True
    if parts[0]=='BlueScorpionTailReference_20261023' and source.name in ['up_walk_fixed.gif','up_attack_fixed.gif','up_death_fixed.gif','continuous_turns.gif','tail_before_after.gif']: final=True
    if parts[0]=='Batch01_10' and len(parts)>3 and parts[1]=='BlueScorpion' and parts[2] in ['runtime_tailref_r02','runtime_tailref_updeath_r02']: final=True
    if parts[0]=='Remaining_20261024' and len(parts)>3:
        item=review_items.get(parts[1],{})
        revisions={r['revision'] for r in item.get('runtime',[])}
        final=item.get('status') in ['completed_pending_user_art_review','user_approved'] and parts[2] in revisions
    status='当前审核版本' if final else '历史或准备材料'
    if any('TailOut' in p or p in ['BlueScorpionTail_20261023','BlueScorpionTailUp_20261023'] for p in parts): status='已否决历史方案'
    items.append({'file':name,'source':relative,'sha256':digest,'bytes':source.stat().st_size,'status':status})
if not args.render_only:
    manifest={'updated_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'count':len(items),'files':items,'policy':'复制全部现存GIF；原证据保留，状态仅用于索引，不代表追加审核通过'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Select final deliverables by exact source revision and action. The archive's
# broad status labels include comparison images and are not a final-media list.
archived={i['source']:i['file'] for i in items if (OUT/i['file']).is_file()}
batch={i['name']:i for i in json.loads((BASE/'Batch01_10/progress.json').read_text(encoding='utf-8'))['items']}
revisions={'Bat':'runtime_r02','BlackBear':'runtime_polish_r01','BlackWolf':'runtime_polish_r01','BlueScorpion':'runtime_tailref_r02'}
actions={
    'walk_turn.gif':'四方向移动',
    'UpWalk.gif':'朝上行走',
    'DownWalk.gif':'朝下行走',
    'up_down_walk.gif':'上下行走',
    'attack_death_reuse.gif':'攻击、受击、死亡与复用',
    'pause_speed.gif':'暂停与倍速',
}
movements=[]
final_media=[]
prefabs=sorted((BASE.parents[1]/'Assets/Prefabs/Enemy').glob('Enemy_*.prefab'))

def resolve_media(name,source,action,movement=False):
    if not (BASE/source).is_file() and source not in archived:
        return None
    href=quote(archived[source] if source in archived else '../'+source,safe='/')
    return {'name':name,'prefab':'Enemy_'+name+'.prefab','source':source,'href':href,
        'action':action,'movement':movement,'available':True}

for prefab in prefabs:
    name=prefab.stem[len('Enemy_'):]
    selected=[]
    item=review_items.get(name,{})
    if item.get('status') in ['completed_pending_user_art_review','user_approved']:
        runtime=[r for r in item.get('runtime',[]) if r.get('pass',0)>0 and r.get('fail')==0]
        regular=[r for r in runtime if 'updeath' not in r['revision'].lower()]
        if len(regular)!=1:
            raise ValueError('Expected exactly one final regular runtime revision for '+name)
        directory=f"Remaining_20261024/{name}/{regular[0]['revision']}"
        selected.extend((directory+'/'+file,action,file=='walk_turn.gif') for file,action in actions.items())
        for r in runtime:
            if 'updeath' in r['revision'].lower():
                selected.append((f"Remaining_20261024/{name}/{r['revision']}/attack_death_reuse.gif",'朝上死亡与复用',False))
    elif name in batch:
        revision=revisions.get(name,batch[name].get('runtime_revision','runtime_r01'))
        directory=f'Batch01_10/{name}/{revision}'
        selected.extend((directory+'/'+file,action,file=='walk_turn.gif') for file,action in actions.items())
        if name in ['BlackBear','BlackWolf']:
            for facing,title in [('Up','朝上'),('Down','朝下')]:
                selected.append((f'AnimationPolish_20261023/{name}_{facing}_Attack.gif',title+'攻击',False))
                selected.append((f'AnimationPolish_20261023/{name}_{facing}_DeathAutoRecycle.gif',title+'死亡',False))
    elif name=='AdvancedHen':
        selected.extend(('AdvancedHen/'+file,actions[file],file=='walk_turn.gif')
            for file in ['walk_turn.gif','up_down_walk.gif','attack_death_reuse.gif'])
    if name=='BlueScorpion':
        # Focused final exports of the approved tail-reference revision; never
        # substitute the older AnimationPolish scorpion or before/after GIFs.
        if not any(resolve_media(name,s,a,m) for s,a,m in selected if m):
            selected.append(('BlueScorpionTailReference_20261023/continuous_turns.gif','四方向移动',True))
        selected.extend(('BlueScorpionTailReference_20261023/'+file,action,False) for file,action in [
            ('up_walk_fixed.gif','朝上行走'),('up_attack_fixed.gif','朝上攻击'),('up_death_fixed.gif','朝上死亡')])
    resolved=[media for source,action,movement in selected
        if (media:=resolve_media(name,source,action,movement)) is not None]
    final_media.extend(resolved)
    movements.extend(media for media in resolved if media['movement'])
if not prefabs:
    raise ValueError('No combat prefabs found; cannot build four-direction movement gallery')
available=len(movements)
movement_names={i['name'] for i in movements}
missing=[p.stem[len('Enemy_'):] for p in prefabs if p.stem[len('Enemy_'):] not in movement_names]
(OUT/'four_direction_moves.json').write_text(json.dumps({'total_prefabs':len(prefabs),'available_gifs':available,'missing':missing,'items':movements},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'final_gifs.json').write_text(json.dumps({'count':len(final_media),'policy':'仅最终选定版本；排除过渡、前后对比与重复移动轮次','items':final_media},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def movement_card(item):
    title=html.escape(item['prefab'])
    href=html.escape(item['href'],quote=True)
    media='<a href="'+href+'"><img loading="lazy" src="'+href+'" alt="'+title+' '+html.escape(item['action'],quote=True)+'"></a>'
    detail='<p>'+html.escape(item['action'])+' · 最终成品</p><small>'+html.escape(item['source'])+'</small>'
    initial_visibility='' if item['movement'] else ' hidden'
    return '<article data-movement="'+str(item['movement']).lower()+'"'+initial_visibility+'>'+media+'<b>'+title+'</b>'+detail+'</article>'

cards='\n'.join(movement_card(i) for i in final_media)
page='''<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>敌人方向最终成品 GIF</title>
<style>
body{font:15px system-ui;background:#172019;color:#eee;margin:24px}
header{position:sticky;top:0;background:#172019;padding:12px 0;z-index:1}
input,select{font:inherit;padding:9px;margin:4px;max-width:100%;box-sizing:border-box}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(320px,100%),1fr));gap:20px}
[hidden]{display:none!important}
article{overflow-wrap:anywhere}
img{width:100%;height:280px;object-fit:contain;background:#283025}
b,small{display:block}p{margin:6px 0;color:#eccd80}
#hint{margin:8px 4px 0;font-size:14px}
</style>
<header>
<h1>敌人方向最终成品 GIF</h1>
<p>按预制体名称查看最终四方向移动；点击图片查看原尺寸。</p>
<input id="q" placeholder="输入角色名或动作" aria-label="搜索角色或动作">
<select id="s" aria-label="选择 GIF 浏览范围">
<option value="four-direction-moves" selected>四方向移动（最终成品）</option>
<option value="final-all">全部最终成品 GIF</option>
</select>
<span id="n" aria-live="polite"></span><p id="hint" hidden></p>
</header>
<main id="gallery">'''+cards+'''</main>
<script>
const q=document.querySelector('#q'),s=document.querySelector('#s');
const cards=Array.from(document.querySelector('#gallery').children);
const totalMovements=cards.filter(card=>card.dataset.movement==='true').length;
const hint=document.querySelector('#hint'),counter=document.querySelector('#n');
function filter(){
  const movementMode=s.value==='four-direction-moves';
  const query=q.value.trim().toLowerCase();
  let count=0;
  cards.forEach(card=>{
    const visible=card.textContent.toLowerCase().includes(query)&&
      (!movementMode||card.dataset.movement==='true');
    card.hidden=!visible;
    if(visible)count++;
  });
  counter.textContent=movementMode?count+' 个预制体 · '+count+' 个最终GIF':count+' 个最终GIF';
  hint.hidden=false;
  hint.textContent=count===0?'没有匹配的最终成品 GIF。':
    (movementMode?'共 '+totalMovements+' 个预制体有最终四方向移动 GIF，每个仅展示一份。':'最终版本的行走、攻击、死亡等动作。');
}
if(location.hash==='#final-all')s.value='final-all';
q.addEventListener('input',filter);s.addEventListener('change',filter);filter();
</script>
</html>
'''
(OUT/'index.html').write_text(page,encoding='utf-8')
readme=('# 敌人方向 GIF 集中目录\n\n'
    '打开 `index.html` 默认选择“四方向移动（最终成品）”，按预制体名称排序，每个角色仅展示一份最终四向移动 GIF。也可选择“全部最终成品 GIF”查看最终动作。浏览列表排除过渡版本、前后对比、被否决方案和重复移动轮次。\n\n'
    f'目前 {available} 个预制体的最终四方向移动 GIF 可查看。'
    + ('另有 '+str(len(missing))+' 个预制体缺少最终四向移动媒体：'+'、'.join(missing)+'；不在浏览列表中放置占位卡片。' if missing else '')
    + '来源及缺失列表见 `four_direction_moves.json`，全部最终动作索引见 `final_gifs.json`。\n\n'
    '筛选依据为 `Remaining_20261024/progress.json` 的最终选定运行版本、首批批准的组合版本和 AdvancedHen R3。只收录明确动作文件，不按模糊的“当前审核版本”标签选图。\n\n'
    '生成器为 `../Remaining_20261024/collect_gifs.py`。使用 `--render-only` 仅重建页面、说明和四向索引，复用原归档清单，不重新复制媒体或改写 `manifest.json`。补回有效版本的移动 GIF 后再次运行即可收录。\n')
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'directory':str(OUT),'archive_count':len(items),'final_gifs':len(final_media),'movement_gifs':available,'missing':missing},ensure_ascii=False))
