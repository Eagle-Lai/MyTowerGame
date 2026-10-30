from session_tiger import *
import numpy as np
from PIL import Image,ImageDraw

owner();assert inventory()==read(D/'incremental_before_20261028.json')['files']
alpha={}
for p in sorted((D/'staged_art').glob('Up_*.png'))+sorted((D/'staged_art').glob('Down_*.png')):
    im=Image.open(p).convert('RGBA');a=np.array(im)[:,:,3];mask=Image.fromarray(np.where(a==0,255,0).astype('uint8'));pad=Image.new('L',(im.width+2,im.height+2),255);pad.paste(mask,(1,1));ImageDraw.floodfill(pad,(0,0),127);interior=int((np.array(pad)==255).sum());assert interior==0,(p.name,interior)
    alpha[p.name]=dict(size=list(im.size),opaque=int((a==255).sum()),transparent=int((a==0).sum()),internal_transparent_holes=interior,sha256=sha(p))
assert len(alpha)==14
client=Client();project=client.identity();errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));state=client.resource('mcpforunity://editor/state');live=probe(client)
assert errors['data']==[] and not any(v for k,v in live.items() if k!='scene') and live['scene']=='Assets/Scenes/Boot.unity'
write(D/'preinstall_review_20261028.json',dict(observed_at=now(),project=project,errors=errors,state=state,live=live,history=client.history,
    actual_views=['generation/Up/revision_01/raw.png','generation/Down/raw.png','reference/source_prefab_offline.png','Up_heel_detail_before.png','local_raster_revision_01/heel_detail_after.png','parts_clean.png','offline_initial_default/offline_rig_proof.png','offline_layout_revision_01/offline_rig_proof.png','offline_rig_proof.png'],
    observations=['Back heads have no facial features; rear heel side claw removed with the intact half of that heel.','Four limbs with solid connection roots under torso; axial Down head covers neck ruff; no extra head ears.','Oversized tail root pads cropped out, actual stem pivots measured; Up thin tail curves over back from rump, Down rises behind rump without preview clipping.','Gold/ochre stripes and spots, cream muzzle/ruff and paws, rounded ears preserved. Native chroma scan found27 isolated1-4pixel pinholes; documented nearest-neighbor repair filled only these, leaving zero interior transparent holes in all14 native parts.'],
    alpha=alpha,staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},decision='Install staged revision, then mandatory real Play checks and visual review; not user art approval'))
c=owner();c.update(current_stage='staged_reviewed_pending_install',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Tiger/preinstall_review_20261028.json',updated_at=now());write(H/'conversation_chain.json',c)
print(json.dumps(dict(alpha_parts=len(alpha),holes=0,live=live,errors=0)))
