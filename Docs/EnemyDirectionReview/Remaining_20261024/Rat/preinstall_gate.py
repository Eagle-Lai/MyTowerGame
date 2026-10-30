"""Capture immutable installation-time evidence before Rat production changes."""
from pathlib import Path
from datetime import datetime
import os,json,hashlib,sys
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;HERE=D.parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
chain=json.loads((HERE/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='Rat' and chain['dispatch_token']=='ram-to-rat-20261026-7f3d9c2a'
assert not (D/'installed_manifest.json').exists()
output=D/'incremental_before_20261026.json';assert not output.exists(),'Do not overwrite preinstallation baseline'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
target=next(t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name']=='Rat')
baseline=json.loads((HERE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
protected=[target[k]+suffix for k in ['battle','source','atlas'] for suffix in ['', '.meta']]
assert all(sha(ROOT/p)==baseline[p] for p in protected),'Protected Rat assets drifted'
assert not (ROOT/target['art_dir']).exists(),'Unexpected Rat Directions before install'
def unwrap(r):
    v=r.get('structuredContent') or json.loads(r['content'][0]['text'])
    if 'result' in v and 'data' not in v:v=v['result']
    assert v.get('success'),v
    return v
c=Client();project=c.identity()
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
state=c.resource('mcpforunity://editor/state')
probe=unwrap(c.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'}))['data']['result']
assert not any(probe.values()),probe
s=state['data'];assert s['advice']['ready_for_tools'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating']
files={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
output.write_text(json.dumps(dict(observed_at=datetime.now().isoformat(),files=files,protected_rat={p:files[p] for p in protected},chain_owner=chain['owner_thread_id'],dispatch_token=chain['dispatch_token']),ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
(D/'preinstall_identity_20261026.json').write_text(json.dumps(dict(project=project,state=state,probe=probe,errors=errors,protocol_history=c.history),ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
# The packer's parts_clean is pre-retouch. Publish a distinctly named actual final slice proof.
sprites=json.loads((D/'staged_art/Rat_Directions.sprites.json').read_text())['sprites']
board=Image.new('RGB',(1400,700),(40,48,37));draw=ImageDraw.Draw(board)
for i,entry in enumerate(sprites):
    key=entry['name'];im=Image.open(D/'staged_art'/(key+'.png')).convert('RGBA');im.thumbnail((185,300))
    x=i%7*200+(200-im.width)//2;y=i//7*350+35;board.paste(im,(x,y),im);draw.text((i%7*200+4,i//7*350+8),key,fill='white')
board.save(D/'parts_final_retouch.png')
review=dict(stage='offline_reviewed_pending_Unity',raw_sources_unchanged={direction:sha(D/'generation'/direction/'raw.png') for direction in ['Up','Down']},observations='Reviewed original references and final offline Up/Down. Back head has no face; neck cap concealed; rear heels have no front toe grooves. Up forelegs remain present and intentionally occluded by broad back; Down has four connected paws with hidden joint caps. Striped tails attach at rear. No cast ground shadow. Runtime review remains required.',final_staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},raster_revision='raster_revision_04',user_approved=False)
(D/'offline_review_20261026.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
print(json.dumps(dict(protected_match=len(protected),snapshot_files=len(files),project=project,probe=probe,console=errors)))
