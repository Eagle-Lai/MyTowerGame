from pathlib import Path
import hashlib,json,shutil,subprocess,sys
D=Path(__file__).resolve().parent
R=D/'repair_proportions_r02';R.mkdir(exist_ok=False)
shutil.copytree(D/'staged_art',R/'staged_before')
for f in ['runtime_summary.json','runtime_visual_strip.png','offline_rig_proof.png']:
    shutil.copy2(D/f,R/(f.replace('.json','_r01.json').replace('.png','_r01.png')))
path=D/'staged_art/Warg_Directions.layout.json'
layout=json.loads(path.read_text(encoding='utf-8'));bottom=layout['referenceBottom'];factor=1.6
for view in layout['views']:
    for p in view['parts']:
        for f in ['x','width','height']:p[f]*=factor
        p['y']=bottom+(p['y']-bottom)*factor
path.write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
report={'revision':'R02','reason':'R01 real four-direction frame shows axial head much smaller than original horizontal head. Uniform 1.6 scale of both axial rigs preserves anatomy, attached pivots and shape, with ground baseline fixed.','factor':factor,'origin_y':bottom,'unchanged':'Original atlas/prefab, horizontal curves, all raw/cutout pixels, sprite pivots and shared C#','previous_runtime':'R01 passed 168 checks but rejected visually for undersized axial head/body. Four-direction and strip actually viewed; complete R01 media was not reviewed.','layout_sha256':hashlib.sha256(path.read_bytes()).hexdigest().upper(),'user_approved':False}
(R/'staged_revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Character-scoped offline proof with larger canvas and reduced px/unit avoids
# the generic 800px frame's crop after increasing the physical rig size.
source=(D.parent/'render_staged_rig.py').read_text(encoding='utf-8')
source=source.replace('HERE=Path(__file__).resolve().parent','HERE=Path(__file__).resolve().parent.parent')
source=source.replace('resolution=800;ppu=600/height','resolution=800;ppu=330/height')
source=source.replace("'offline_rig_proof.png'","'offline_rig_proof_r02.png'")
(D/'render_proportions_r02.py').write_text(source,encoding='utf-8')
subprocess.run([sys.executable,str(D/'render_proportions_r02.py'),'Warg'],check=True)
print(json.dumps(report,ensure_ascii=False))
