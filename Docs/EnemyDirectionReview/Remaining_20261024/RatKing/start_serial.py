"""RatKing-only serial preflight and reference preparation; no production writes."""
from pathlib import Path
import hashlib, json, os, subprocess, sys
from datetime import datetime, timezone, timedelta
D=Path(__file__).resolve().parent; H=D.parent; ROOT=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def owner():
    c=read(H/'conversation_chain.json')
    assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
    assert c['current_character']=='RatKing' and c['dispatch_token']=='rat-to-ratking-5222dbfeb5d146d7ad666975e4e8d90e'
def unwrap(r): return r.get('structuredContent') or json.loads(r['content'][0]['text'])
owner()
t=next(t for t in read(H/'local_baseline.json')['targets'] if t['name']=='RatKing')
baseline=read(H/'production_fingerprints_before.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
protected={p:sha(ROOT/p) for q in ['battle','source','atlas'] for p in [t[q],t[q]+'.meta']}
assert all(s==baseline[p] for p,s in protected.items())
for q in ['source','atlas','battle']:
    assert sha(D/'reference'/Path(t[q]).name)==protected[t[q]]
    assert sha(D/'reference'/(Path(t[q]).name+'.meta'))==protected[t[q]+'.meta']
assert not (D/'installed_manifest.json').exists()
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
state=c.resource('mcpforunity://editor/state')
probe=unwrap(c.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'}))['data']['result']
assert not any(v for k,v in probe.items() if k!='scene'),probe
assert state['data']['advice']['ready_for_tools']
write(D/'start_preflight_20261026.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),project=project,protected=protected,state=state,errors=errors,probe=probe,protocol_history=c.history,rule_path_discrepancy='AGENTS FreedomTower_1/D: is historical; explicit target E:/MyTowerGame'))
print(json.dumps(dict(project=project,probe=probe,protected_count=len(protected)),ensure_ascii=False))
assert not (D/'anatomy_plan.json').exists()
subprocess.run([sys.executable,str(H/'character_step.py'),'prepare','RatKing'],check=True)
plan=read(D/'anatomy_plan.json')
plan['identity']='Large low olive-brown shaggy rat king, amber eyes, ochre cheek tufts and spots, four short paws, pale gold dark-ringed thin tail; ONE small gold crown with a black diamond-shaped inset and ONE silver hoop earring on the anatomical LEFT ear. Preserve original asymmetry and low rodent silhouette.'
plan['observed_reference_notes_zh']='已实际查看原图集及完整源预制体：金冠与黑色菱形镶饰只在头上，单只银色耳环，橄榄棕色背毛、赭色颊毛与斑点，四只短足和浅金色环纹细尾；无白色鬃毛。Up 为无脸后脑与背部，后足不画正面趾沟，Down 保持琥珀眼、尖牙、单侧耳环与四足。'
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    p=D/'generation'/direction/'prompt.txt'
    source=p.read_text(encoding='utf-8')
    old='Large olive ragged rat with small gold crown, amber eye, pale cheek tufts, four paws and long thin striped tail. Preserve crown.'
    source=source.replace(old,plan['identity'])
    source+='\nREFERENCE-SPECIFIC REQUIREMENTS: Crown belongs only to HEAD slices, never body. ONE silver hoop earring belongs only to the anatomical LEFT ear (screen LEFT in Up/back, screen RIGHT in Down/front); never duplicate the hoop or add a second one. Same crown size/alignment in all head states. Cheek fur is ochre-brown, not white. Spiky olive back fur is part of torso, with ochre flank spots, no cream mane. The rat has a low quadruped posture, four paws, and exactly one pale gold tail with dark bands. '
    if direction=='Up':
        source+='Rear paws show continuous backs/heels, no front toe grooves or forward claws. Heads show back of crown/ears and plain rear fur only, absolutely no eyes, teeth, nose, inner ear pads, or face. Tail root must be filled, not an open tube.'
    else:
        source+='Small front-facing paws have restrained original toe lines. Normal head stern mouth closed with two small fangs, angry head open attack mouth, dead head matching original dazed dead eye and open mouth. Preserve tongue/mouth interiors in warm ochre colors; no magenta inside pieces.'
    p.write_text(source+'\n',encoding='utf-8')
print('RatKing reference plan and two unique unrequested prompts prepared')
