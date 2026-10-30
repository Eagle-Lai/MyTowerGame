from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib, sys
HERE=Path(__file__).resolve().parent
RUN=HERE.parents[1]
q=RUN/'PirateBoar/runtime_shot_r02'
obs=[json.loads(s) for s in (q/'shot_observations.jsonl').read_text().splitlines()]
records=[json.loads(s) for s in (q/'actual_frames.jsonl').read_text().splitlines()]
shots=[]
proof=Image.new('RGB',(1600,1120),(40,48,37));draw=ImageDraw.Draw(proof)
for row,facing in enumerate(['Up','Right','Down','Left']):
    seq=[r for r in obs if r['facing']==facing]
    assert any(r['shot'] for r in seq)
    ys=[r['bodyY'] for r in seq if r['shot']]
    if facing in ['Up','Down']: assert max(ys)-min(ys)>.01
    for i in range(5):
        o=seq[round(i*(len(seq)-1)/4)]
        r=min([r for r in records if r['stage']=='ContinuousTurns'],key=lambda r:abs(r['frame']-o['frame']))
        im=Image.open(q/r['file']).convert('RGB');im.thumbnail((300,260))
        proof.paste(im,(i*320,row*280+20))
        draw.text((i*320+2,row*280+2),facing+' Shot f'+str(r['frame']),fill='white')
        shots.append(r)
proof.save(q/'shot_sequence.png')
images=[Image.open(q/r['file']).convert('RGB').resize((512,512)) for r in shots]
images[0].save(q/'shot_four_directions.gif',save_all=True,append_images=images[1:],duration=120,loop=0)
(q/'shot_media_manifest.json').write_text(json.dumps({'sources':shots,'observation_sha256':hashlib.sha256((q/'shot_observations.jsonl').read_bytes()).hexdigest().upper(),'note':'Real recorded frames nearest Shot probe observations; no synthetic poses'},indent=2)+chr(10),encoding='utf-8')
sys.path.insert(0,str(RUN))
from mcp_call import Client
c=Client();project=c.identity()
r=c.tool('execute_code',{'action':'execute','code':'var names=new[]{"BlackWolf","MimicChest"};var results=new System.Collections.Generic.List<object>();foreach(var name in names){FTProject.EditorTools.EnemyDirectionSpec s;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec(name,out s);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(s,out report);results.Add(new{name=name,pass=pass,report=report});}return results;'})
(HERE/'other_rig_verify.json').write_text(json.dumps({'project':project,'result':r,'history':c.history},ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
v=r.get('structuredContent') or json.loads(r['content'][0]['text'])
print(json.dumps({'regressions':[{'name':x['name'],'pass':x['pass']} for x in v['data']['result']],'shot_frames':len(obs)}))
