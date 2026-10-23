from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np,re
HERE=Path(__file__).resolve().parent;BATCH=HERE.parent/'Batch01_10';names=['BlackBear','BlackWolf','BlueScorpion']
for name in names:
 d=BATCH/name/'runtime_polish_updeath_r02';rs=[json.loads(s) for s in (d/'actual_frames.jsonl').read_text().splitlines()]
 assert 'FAIL ' not in (d/'actual_runtime_checks.txt').read_text() and not (d/'exception.txt').exists()
 rs=[r for r in rs if r['stage']=='DeathAutoRecycle'];assert all(r['facing']=='Up' for r in rs)
 # Keep the complete actual frame, so collapse and tail movement cannot be cropped off.
 frames=[];sources=[]
 for r in rs:
  im=Image.open(d/r['file']).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
  ImageDraw.Draw(im).text((12,12),name+' Up death - native Play',fill='white');frames.append(im);sources.append(r['file'])
 family='Scorpions' if name=='BlueScorpion' else 'Dogs'
 clip=HERE.parents[2]/f'Assets/_UIAssets/Monsters/{family}/{name}/Directions/Animations/Death_Directions.anim'
 seconds=float(re.search(r'm_StopTime: ([0-9.]+)',clip.read_text())[1])
 durations=[max(10,min(200,round((b['normalizedTime']-a['normalizedTime'])*1000*seconds))) for a,b in zip(rs,rs[1:])]+[400]
 frames[0].save(HERE/(name+'_Up_DeathAutoRecycle.gif'),save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False,disposal=2)
 board=Image.new('RGB',(1536,512),(40,48,37))
 selected=[]
 for col,phase in enumerate([.1,.35,.65]):
  i=min(range(len(rs)),key=lambda i:abs(rs[i]['normalizedTime']-phase));board.paste(frames[i],(col*512,0));selected.append(rs[i]['file'])
 board.save(HERE/(name+'_Up_death_contact.png'))
 (HERE/(name+'_Up_death_sources.json')).write_text(json.dumps({'directory':str(d),'frames':sources,'contact_frames':selected,'durations_ms':durations,'source':'Actual Unity frames, natural Animator and native death event; no synthesized poses.'},indent=2),encoding='utf-8')
gifs=[Image.open(HERE/(n+'_walk_before_after.gif')) for n in names];overview=[]
for i in range(12):
 board=Image.new('RGB',(1440,1260),(40,48,37))
 for row,gif in enumerate(gifs):gif.seek(i);board.paste(gif.convert('RGB'),(0,row*420))
 overview.append(board)
overview[0].save(HERE/'walk_before_after_all.gif',save_all=True,append_images=overview[1:],duration=[40,40,40,50,40,40,40,50,40,40,40,40],loop=0,optimize=False,disposal=2)
html=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>三个敌人动画返修</title><style>body{margin:0;background:#171e17;color:#eee;font:16px system-ui;line-height:1.6}main{max-width:1440px;margin:auto;padding:30px}h1{font-size:30px}h2{margin-top:48px}img{max-width:100%;height:auto}a{color:#a9dbaf}.actions{display:flex;flex-wrap:wrap;gap:10px}.actions figure{margin:0;flex:1;min-width:260px}.actions img{width:100%}p{color:#c5cec5}figcaption{font-size:14px}</style><main><h1>BlackBear / BlackWolf / BlueScorpion 动画返修</h1><p>来自最终安装资源的真实 Unity Play 帧。行走对照从左到右：旧 Up、新 Up、旧 Down、新 Down；前后使用同一裁切和缩放。攻击与死亡保留实际采样姿态。</p>']
for name in names:
 html.append(f'<section><h2>{name}</h2><img src="{name}_walk_before_after.gif" alt="{name} 上下行走前后对照"><div class="actions">')
 for facing,action,title in [('Up','Attack','朝上攻击'),('Down','Attack','朝下攻击'),('Up','DeathAutoRecycle','朝上死亡'),('Down','DeathAutoRecycle','朝下死亡')]:
  html.append(f'<figure><img src="{name}_{facing}_{action}.gif" alt="{title}"><figcaption>{title}</figcaption></figure>')
 html.append(f'</div><p><a href="../Batch01_10/{name}/runtime_polish_r01/walk_turn.gif">连续转向</a> · <a href="../Batch01_10/{name}/runtime_polish_r01/attack_death_reuse.gif">受击、死亡与同实例复用</a> · <a href="../Batch01_10/{name}/runtime_polish_r01/pause_speed.gif">暂停与倍速</a></p></section>')
html.append('<p>当前状态及精确 SHA256 见 README.md / scope_audit.json / implementation_manifest.json。历史批次的审核身份保留，当前版本等待用户美术审核。</p></main></html>')
(HERE/'preview.html').write_text('\n'.join(html),encoding='utf-8')
print('Built actual Up death media, combined comparison and local review page.')
