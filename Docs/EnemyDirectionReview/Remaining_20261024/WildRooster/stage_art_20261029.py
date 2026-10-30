"""Stage reviewed initial WildRooster raws; no production writes."""
from PIL import Image
import json, subprocess, sys
from checkpoint_20261029 import D,H,NAME,owner,read,write,sha,now
owner()
assert not (D/'installed_manifest.json').exists()
assert not (D/'staged_art').exists(), 'Preserve prior stage; repair through a fresh revision'
parts=read(D/'anatomy_plan.json')['parts']
rectangles={}
raws={}
for direction in ['Up','Down']:
    p=D/'generation'/direction/'raw.png';r=read(p.parent/'result.json');im=Image.open(p)
    assert r['status']==200 and r['bytes']==p.stat().st_size and im.size==(1536,1024)
    raws[direction]={'file':p.relative_to(D).as_posix(),'sha256':sha(p),'format':im.format,'size':im.size,'mode':im.mode,'status':200,'actual_billing':'not queried; usage marked local_estimate, not an actual bill'}
    for i,part in enumerate(parts):
        x=i%4*384;y=i//4*512
        rectangles[direction+'_'+part]=[x,y,x+384,y+512]
write(D/'generation_visual_review_20261029.json',{'at':now(),'raws':raws,'method':'Actually viewed full Up and Down returned sheets separately at original dimensions.','observations':'Up三头纯奶油后脑无脸，原金冠保留，后足呈单后趾/后跟。Down正面居中金喙、双眼与正常/愤怒/死亡表情，双瓣垂肉。两张Body的三枚金色凸羽按原Body一体尾羽处理，Down上缘另有肩部小突起，须组合审查是否多余。两张Wing白根金羽，单脚方向区分；空白Tail槽为透明兼容。','decision':'Usable inputs for staging; assembled anatomy and connections remain pending actual offline review.','paid_requests':2,'retries':0})
write(D/'art_selection.json',{'Up':'generation/Up/raw.png','Down':'generation/Down/raw.png','rectangles':rectangles,'transparent_parts':['Up_Tail','Down_Tail'],'rationale':'Integral original Body tail, no separate source Tail renderer. Full explicit nominal cells after actual raw review; transparent Tail compatibility slices only.'})
write(D/'layout_adjustments.json',{'remove':['Up/Tail','Down/Tail'],'layout':{'motion':{'legAngle':10.5,'legLift':0.16,'bodyBob':0.006,'bodyRoll':1.1,'tailSwing':0}},'parts':{},'sprites':{},'reason':'WildRooster has 2 clawed legs, 2 cream-root folded wings, and Body-integral tail. Per-character modest two-leg stepping and wing sway; no separate tail joint.'})
for script in ['pack_character.py','adjust_layout.py','render_staged_rig.py']:
    subprocess.run([sys.executable,str(H/script),NAME],check=True)
p=read(H/'progress.json');i=next(i for i in p['items'] if i['name']==NAME);i.update(status='staged_pending_visual_check',stage='initial_offline_rig_pending_review');p.update(current=NAME,updated_at=now());write(H/'progress.json',p)
print('Initial stage ready for actual anatomy and alpha review')
