from session_current import *
import subprocess

owner();assert not (HERE/'staged_art').exists()
save(HERE/'generation_selected_review_20261029.json',{'observed_at':now(),'viewed':['generation/Up/revision_01/raw.png','generation/Down/raw.png'],
 'findings':'Up correction now has true plain occiput and outer ear backs with small crown brain, no face in all three head cells; source-like stitched rear torso, two complete cuffed arms with unique right-hand club and smooth rear heel. Down has own normal/angry/blank-eyed dead faces, front belly sutures/loincloth, correct viewer-left club and bare front toes. No skull necklace or duplicate limb/weapon. Complete raw sheets viewed before extraction.',
 'initial_Up_rejected':'generation/Up/raw.png: frontal heads, retained.','selected_sha256':{v:sha(HERE/p) for v,p in {'Up':'generation/Up/revision_01/raw.png','Down':'generation/Down/raw.png'}.items()},'user_approved':False})
rects={
 'Up':[[25,90,335,430],[410,90,720,430],[790,90,1100,430],[1125,60,1530,495],[15,535,490,955],[520,535,745,955],[810,535,1045,955]],
 'Down':[[25,60,340,405],[410,60,725,405],[790,60,1105,405],[1130,75,1525,490],[0,515,410,930],[500,515,725,930],[820,535,1045,930]]}
parts=read(HERE/'anatomy_plan.json')['parts']
save(HERE/'art_selection.json',{'Up':'generation/Up/revision_01/raw.png','Down':'generation/Down/raw.png','rectangles':{v+'_'+p:r for v,rs in rects.items() for p,r in zip(parts,rs)},
 'note':'Explicit actual component rectangles; weapon-arm exceeds nominal grid. Up expressions reuse its accepted plain rear normal head as recorded pack behavior. Initial front-headed Up is rejected and preserved.'})
subprocess.run([sys.executable,str(RUN/'pack_character.py'),NAME],check=True)
save(HERE/'layout_adjustments.json',{'reason':'Actual shoulder roots are off-center in combined club-arm art. Weapon remains anatomical RIGHT (screen right rear / screen left front). Stocky short legs, arm/hip roots buried under body; two-leg opposite phases.',
 'layout':{'motion':{'legAngle':7,'legLift':0.10,'bodyBob':0.005,'bodyRoll':1.0,'tailSwing':0}},
 'sprites':{'Up_ArmWeapon':{'pivotX':0.245,'pivotY':0.965},'Down_ArmWeapon':{'pivotX':0.83,'pivotY':0.965},'Up_ArmFree':{'pivotX':0.52,'pivotY':0.965},'Down_ArmFree':{'pivotX':0.45,'pivotY':0.965}},
 'parts':{**{v+'/Head':{'y':0.81,'width':0.48,'height':0.40} for v in ['Up','Down']},
          **{v+'/Body':{'y':0.48,'width':0.68,'height':0.58} for v in ['Up','Down']},
          **{v+'/Leg'+s:{'x':(-1 if s=='L' else 1)*0.15,'y':0.23,'width':0.19,'height':0.25,'phase':int(s=='R')} for v in ['Up','Down'] for s in ['L','R']},
          'Up/ArmR':{'x':0.26,'y':0.65,'width':0.58,'height':0.59,'order':24,'phase':1},
          'Up/ArmL':{'x':-0.26,'y':0.65,'width':0.25,'height':0.50,'order':24,'phase':0},
          'Down/ArmR':{'x':-0.26,'y':0.65,'width':0.51,'height':0.58,'order':24,'phase':1},
          'Down/ArmL':{'x':0.26,'y':0.65,'width':0.25,'height':0.50,'order':24,'phase':0}}})
subprocess.run([sys.executable,str(RUN/'adjust_layout.py'),NAME],check=True)
subprocess.run([sys.executable,str(RUN/'render_staged_rig.py'),NAME],check=True)
print(json.dumps({'stage':NAME,'sprites':len(read(HERE/'staged_art/Zombie_Directions.sprites.json')['sprites'])}))
