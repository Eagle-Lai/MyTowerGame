"""Explicit R3 single-example repack. Use a coordinated Assets edit window, then BuildAdvancedHen."""
from pathlib import Path
import runpy,shutil,json
from PIL import Image
HERE=Path(__file__).resolve().parent
if HERE.name=='revision_03':HERE=HERE.parent
ROOT=HERE.parents[2]
R3=HERE/'revision_03'
ART=ROOT/'Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions'
runpy.run_path(str(R3/'pack_art.py'))
assert (R3/'atlas/AdvancedHen_Directions.sprites.json').read_bytes()==(ART/'AdvancedHen_Directions.sprites.json').read_bytes()
shutil.copyfile(R3/'atlas/AdvancedHen_Directions.png',ART/'AdvancedHen_Directions.png')
atlas=Image.open(ART/'AdvancedHen_Directions.png').convert('RGBA')
data=json.loads((ART/'AdvancedHen_Directions.sprites.json').read_text())
proof=Image.new('RGBA',(3072,1024),(40,48,37,255))
for i,s in enumerate(data['sprites']):
    y=atlas.height-s['y']-s['h'];part=atlas.crop((s['x'],y,s['x']+s['w'],y+s['h']))
    proof.alpha_composite(part,((i%6)*512+(512-part.width)//2,(i//6)*512+(512-part.height)//2))
proof.convert('RGB').save(HERE/'parts_comparison.png')
print('R3 PNG installed with the original rects/pivots/PPU. Run single AdvancedHen builder; it removes all Shadow nodes.')
