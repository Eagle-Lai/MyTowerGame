from pathlib import Path
import json,shutil,subprocess,sys
D=Path(__file__).resolve().parent;H=D.parent;old=D/'offline_layout_revision_01';assert not old.exists()
old.mkdir()
for f in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','layout_adjustments.json']:shutil.copy2(D/f,old/f)
shutil.copy2(D/'staged_art/Sheep_Directions.layout.json',old/'Sheep_Directions.layout.json')
(old/'rejected.json').write_text(json.dumps(dict(reason='Default quadruped layout exposed large round leg roots and made Sheep legs too long relative to source. No production install or runtime yet.',next='offline_layout_revision_02'),indent=2)+'\n',encoding='utf-8')
p=D/'layout_adjustments.json';adj=json.loads(p.read_text(encoding='utf-8'));parts={}
parts['Up/Body']=dict(y=.52,width=.81,height=.71)
parts['Up/Head']=dict(y=.82,width=.75,height=.43,order=25)
parts['Down/Body']=dict(y=.60,width=.82,height=.72)
parts['Down/Head']=dict(y=.46,width=.78,height=.60)
for direction in ['Up','Down']:
    for side in ['L','R']:
        sign=-1 if side=='L' else 1
        for front in [True,False]:
            near=(not front) if direction=='Up' else front
            parts[direction+'/'+('Fore' if front else 'Hind')+side]=dict(x=sign*(.22 if near else .27),y=.29 if near else .49,width=.165 if near else .15,height=.20 if near else .18)
adj['parts']=parts;adj['reason']='Sheep-specific short hooves; roots buried under wool, broad fleece body and larger face. Up nape overlays closed wool neck while body keeps leg roots hidden. Four actual limb nodes; no tail.'
p.write_text(json.dumps(adj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(H/'adjust_layout.py'),'Sheep'],check=True)
subprocess.run([sys.executable,str(H/'render_staged_rig.py'),'Sheep'],check=True)
