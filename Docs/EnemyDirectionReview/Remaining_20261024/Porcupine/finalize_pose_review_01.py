"""Archive factual visual review and the exact scope of the Porcupine-only repair."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, hashlib, sys
D=Path(__file__).resolve().parent
HERE=D.parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
OUT=D/'repair_pose_r01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
baseline=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))
delta=[{'path':p,'before':s,'after':sha(ROOT/p) if (ROOT/p).is_file() else None} for p,s in baseline['fingerprints'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=s]
expected={'Assets/_UIAssets/Monsters/Rats/Porcupine/Directions/Animations/'+n+'_Directions.anim' for n in ['Ready','Walk']}
assert {x['path'] for x in delta}==expected,delta
runtime=json.loads((D/'runtime_summary.json').read_text(encoding='utf-8'))
assert runtime['passes']==168 and runtime['failures']==0
assert [x['revision'] for x in runtime['runtime']]==['runtime_r02','runtime_updeath_r02']
for r in runtime['runtime']:
 assert r['pass']==84 and r['fail']==0
 assert sha(D/r['revision']/'actual_frames.jsonl')==r['records_sha256']
client=Client();identity=client.identity()
state=client.tool('execute_code',{'action':'execute','code':'return Newtonsoft.Json.JsonConvert.SerializeObject(new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,scriptCompilationFailed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path});'})
value=state.get('structuredContent') or json.loads(state['content'][0]['text'])
assert value['success'],value
state=json.loads(value['data']['result'])
assert not any(v for k,v in state.items() if k!='scene'),state
console=client.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
value=console.get('structuredContent') or json.loads(console['content'][0]['text'])
assert value['success'] and value['data']==[],value
manifest=json.loads((HERE.parent/'AllGIF/manifest.json').read_text(encoding='utf-8'))
sprite_manifest=json.loads((ROOT/'Assets/_UIAssets/Monsters/Rats/Porcupine/Directions/Porcupine_Directions.sprites.json').read_text(encoding='utf-8'))
images=['final_visual_review_montage.png','runtime_r02/four_directions.png','runtime_visual_strip.png','repair_pose_r01/motion_review_r02.png','repair_pose_r01/lifecycle_review_r02.png','repair_pose_r01/walk_phase_review_r02.png']
note=(OUT/'visual_note_utf8.txt').read_text(encoding='utf-8').strip()
assert '?' not in note and '�' not in note
report={'name':'Porcupine','revision':'repair_pose_r01','at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'identity':identity,'scope_delta':delta,'state':state,'console_errors':value['data'],'runtime':runtime['runtime'],'actual_frames':runtime['actual_frames'],'visual_pass':True,'visual_note':note,'images':images,'viewed_image_count':6,'image_review_limit_note':'Sixth image has an incorrect crop and is not used as visual evidence. Conclusions use the full native four-direction and runtime strips and GIF contact sheets listed first.','sprite_count':len(sprite_manifest['sprites']),'new_gifs':sum(len(list((D/r).glob('*.gif'))) for r in ['runtime_r02','runtime_updeath_r02']),'allgif_count_before_record':manifest['count'],'rebuild_note':'A future full EnemyDirectionalRigBuilder.Build recreates clips from shared source. Reapply repair_pose_r01/patch.cs.txt after such a rebuild; this task does not modify shared builders.','protocol_history':client.history}
(OUT/'final_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'scope_delta.json').write_text(json.dumps(delta,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['actual_frames','sprite_count','new_gifs','allgif_count_before_record','visual_pass','viewed_image_count']},ensure_ascii=False))
