from pathlib import Path
import json, shutil, subprocess, sys
D=Path(__file__).resolve().parent
backup=D/'staged_initial_r01'
assert not backup.exists() and not (D/'installed_manifest.json').exists()
backup.mkdir()
for p in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png','layout_adjustments.json']:
    shutil.copy2(D/p,backup/p)
shutil.copytree(D/'staged_art',backup/'staged_art')
p=D/'layout_adjustments.json'
j=json.loads(p.read_text(encoding='utf-8'))
j['reason']+=' r02 after actual offline inspection: reveal far feet around torso flanks; hide rear tail root beneath rump, preserve four-paw anatomy.'
for side,sign in [('L',-1),('R',1)]:
    j['parts']['Up/Fore'+side].update(x=sign*.10,y=.68,height=.32,angle=sign*48)
    j['parts']['Down/Hind'+side].update(x=sign*.10,y=.92,height=.28,angle=sign*50)
j['parts']['Up/Tail'].update(y=.27,order=18)
p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'adjust_layout.py'),'Watchdog'],check=True)
subprocess.run([sys.executable,str(D.parent/'render_staged_rig.py'),'Watchdog'],check=True)
