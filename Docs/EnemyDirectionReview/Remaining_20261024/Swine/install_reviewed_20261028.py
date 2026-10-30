from session_swine import *
from PIL import Image
import numpy as np
owner(); assert not (D/'installed_manifest.json').exists()
assert inventory()==read(D/'incremental_before_20261028.json')['files'],'Production drift before install'
client=Client();project=client.identity()
errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));live=probe(client)
assert errors['data']==[] and not any(v for k,v in live.items() if k!='scene'),live
write(D/'preinstall_unity_20261028.json',dict(observed_at=now(),project=project,errors=errors,live=live,history=client.history))
alpha={}
for p in (D/'staged_art').glob('*.png'):
    a=np.asarray(Image.open(p).convert('RGBA'))
    alpha[p.name]=dict(size=list(a.shape[:2][::-1]),transparent=int((a[:,:,3]==0).sum()),opaque=int((a[:,:,3]==255).sum()),magenta_foreground=int(((a[:,:,0]>200)&(a[:,:,2]>150)&(a[:,:,1]<80)&(a[:,:,3]>128)).sum()))
assert all(v['magenta_foreground']==0 and v['opaque']>0 and v['transparent']>0 for v in alpha.values())
write(D/'offline_review_20261028.json',dict(observed_at=now(),accepted_for_install=True,viewed=['reference/source_prefab_offline.png','reference/Swine.png','generation/Up/raw.png','generation/Down/raw.png','offline_layout_revision_01/offline_rig_proof.png','offline_layout_revision_01/parts_clean.png','offline_layout_revision_02/offline_rig_proof.png','offline_rig_proof.png','offline_Up.png','offline_Down.png'],observation='Original round tan/ochre boar preserved. Up duplicate head ears removed locally; exactly two ears remain on torso, rear head plain without face or tusks. Local r02 makes generated torso rounder; layout03 hides neck cap and embeds four short foot roots. Down three expressions axial, ivory cheek tusks and tiny pointed tail once. Prior two layouts rejected before installation. No visible magenta holes, detached roots or ground shadow in current offline PNGs. Generated smooth shading and higher axial silhouette remain subject to user art review.',alpha=alpha,staging_sha256={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},selection_sha256=sha(D/'art_selection.json'),layout_sha256=sha(D/'layout_adjustments.json')))
battle=R/'Assets/Prefabs/Enemy/Enemy_Swine.prefab'
def sprites(text):
    return {m.group(2):re.search(r'^  m_Sprite: (.+)$',m.group(3),re.M).group(1) for m in re.finditer(r'^--- !u!(212) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',text,re.M|re.S)}
before=sprites(battle.read_text(encoding='utf-8-sig'))
run('install_character.py',NAME)
after=sprites(battle.read_text(encoding='utf-8-sig'))
assert all(after.get(k)==v for k,v in before.items())
write(D/'original_sprite_contracts_20261028.json',dict(before=before,after_existing={k:after[k] for k in before},retained=True,included_hp_sprites=True))
p=read(H/'progress.json');i=next(x for x in p['items'] if x['name']==NAME);i.update(installed_manifest='Swine/installed_manifest.json');write(H/'progress.json',p)
c=owner();c.update(current_stage='installed_pending_own_Walk_reset_and_two_Play_rounds',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Swine/installed_manifest.json',updated_at=now());write(H/'conversation_chain.json',c)
