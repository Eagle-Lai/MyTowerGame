from session_swine import *
from PIL import Image
import numpy as np, shutil
owner(); out=D/'local_raster_revision_03';out.mkdir(exist_ok=False)
for p in ['art_selection.json','processing.json','runtime_summary.json','runtime_visual_strip.png','installed_manifest.json','installed_verify.txt']:
    shutil.copy2(D/p,out/('before_'+p))
shutil.copytree(D/'staged_art',out/'before_staged_art')
im=Image.open(D/'local_raster_revision_02/Up_sheet.png').convert('RGB');a=np.array(im)
for y in range(828,863):
    for x in range(181,202):
        t=(x-175)/32;a[y,x]=np.round(a[y,175]*(1-t)+a[y,207]*t).astype(np.uint8)
Image.fromarray(a).save(out/'Up_sheet.png')
write(out/'processing.json',dict(observed_at=now(),parent='local_raster_revision_02/Up_sheet.png',parent_sha256=sha(D/'local_raster_revision_02/Up_sheet.png'),output='Up_sheet.png',output_sha256=sha(out/'Up_sheet.png'),method='Complete interior row-color interpolation, x181..201 y828..862, removes faint remaining triangle from earlier thresholded rear heel repair. Outer heel contour preserved. No paid generation.',rect=[181,828,202,863]))
write(out/'rejected_previous.json',dict(observed_at=now(),viewed='staged_art/Up_LegFront.png at native resolution',finding='Native-size review found a faint triangular trace at rear heel after thresholded r02 fill; technical 168/0 remains historical. Replace interior with full row interpolation, preserve outline and rerun two rounds on installed final atlas.',old_runtime=['runtime_r01','runtime_updeath_r01'],old_frames=673,old_review_sheets_actually_viewed=10))
sel=read(D/'art_selection.json');sel['Up']=out.name+'/Up_sheet.png';sel['selection_note']+=' Native heel r03 removes residual faint triangle; r01 runtime becomes historical.';write(D/'art_selection.json',sel)
run('pack_character.py',NAME);run('adjust_layout.py',NAME);run('render_staged_rig.py',NAME)
print(json.dumps(dict(stage_revision=out.name,install_not_yet_done=True)))
