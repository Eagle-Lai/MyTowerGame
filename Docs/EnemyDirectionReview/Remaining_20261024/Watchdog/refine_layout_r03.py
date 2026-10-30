from pathlib import Path
import json, shutil, subprocess, sys
D=Path(__file__).resolve().parent
backup=D/'staged_layout_r02'
assert not backup.exists() and not (D/'installed_manifest.json').exists()
backup.mkdir()
for f in ['layout_adjustments.json','offline_rig_proof.png','offline_Down.png']:
    shutil.copy2(D/f,backup/f)
shutil.copytree(D/'staged_art',backup/'staged_art')
p=D/'layout_adjustments.json';j=json.loads(p.read_text(encoding='utf-8'))
j['reason']+=' r03 rejects visible round hip caps above rump; moves hip roots inward and under torso, offsets front head toward near chest.'
for side,sign in [('L',-1),('R',1)]:
    j['parts']['Down/Hind'+side].update(x=sign*.035,y=.83,height=.31,angle=sign*60)
    j['parts']['Down/Fore'+side]['y']=.30
j['parts']['Down/Head']['y']=.36
p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'adjust_layout.py'),'Watchdog'],check=True)
subprocess.run([sys.executable,str(D.parent/'render_staged_rig.py'),'Watchdog'],check=True)
