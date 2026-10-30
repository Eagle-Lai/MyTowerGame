"""Repair this character's copied Walk clip; preserve sources and prior evidence."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, shutil, sys

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from mcp_call import Client

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, data): p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v): return v.get('structuredContent') or json.loads(v['content'][0]['text'])

chain = read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='Scarab'
assert chain['dispatch_token']=='sabretoothtiger-to-scarab-a14cefa3c87b4f9187c899d88ead8c0c'
out = D/'side_reuse_repair_r02'
assert not out.exists(), 'Inspect existing repair evidence before retrying'
manifest = read(D/'installed_manifest.json')
assert all(sha(ROOT/x['path'])==x['after'].upper() for x in manifest['changes'])
summary = read(D/'runtime_summary.json')
assert [x['revision'] for x in summary['runtime']]==['runtime_r01','runtime_updeath_r01']
protected = read(D/'incremental_before_recovery_20261028.json')['protected_scarab']
assert all(sha(ROOT/p)==s.upper() for p,s in protected.items() if p!='Assets/Prefabs/Enemy/Enemy_Scarab.prefab')

c = Client()
project = c.identity()
refresh = c.tool('refresh_unity', dict(mode='force',scope='assets',compile='none',wait_for_ready=True))
project = c.identity()
state = c.resource('mcpforunity://editor/state')
probe = unwrap(c.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success'] and not any(v for k,v in probe['data']['result'].items() if k!='scene')
assert probe['data']['result']['scene']=='Assets/Scenes/Boot.unity'
out.mkdir()
clip_path = 'Assets/_UIAssets/Monsters/Insects/Scarab/Directions/Animations/Walk_Directions.anim'
for p in ['installed_manifest.json','installed_verify.txt','runtime_summary.json','runtime_visual_strip.png']:
    shutil.copy2(D/p,out/p)
shutil.copy2(ROOT/clip_path,out/'Walk_Directions_before.anim')
write(out/'visual_rejection.json',dict(observed_at=now(),status='rejected_by_internal_visual_review',user_approved=False,
    revisions=['runtime_r01','runtime_updeath_r01'],technical_checks='168 PASS / 0 FAIL; insufficient for visual approval',
    inspected=['runtime_r01/four_directions.png','runtime_visual_strip.png','visual_review_final_20261028/runtime_r01_sequence_0.png','visual_review_final_20261028/runtime_r01_walk_cycle.png','visual_review_final_20261028/runtime_r01_sequence_1.png','visual_review_final_20261028/runtime_r01_sequence_2.png','visual_review_final_20261028/runtime_updeath_r01_sequence_0.png','visual_review_final_20261028/runtime_updeath_r01_walk_cycle.png'],
    finding='Both ContinuousTurns sequences show the original side body upside down after real death/pool reuse. Vertical rigs recover. The source Death anim rotates Body z to -180 while the source/copied Walk has no Body rotation binding.',
    remedy='Add only missing constant zero Body Euler rotation tracks to Scarab copied Walk. Preserve all existing source curves/events/timing, source/shared clips and C#; new r02 Play evidence required.'))
code='var path="'+clip_path+'";var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(path);if(!clip)throw new System.Exception("Missing copied Walk");foreach(var b in UnityEditor.AnimationUtility.GetCurveBindings(clip))if(b.path=="Body"&&(b.propertyName.Contains("Euler")||b.propertyName.Contains("Rotation")))throw new System.Exception("Body rotation already exists; inspect before changing");float length=clip.length;foreach(string axis in new[]{"x","y","z"}){var binding=UnityEditor.EditorCurveBinding.FloatCurve("Body",typeof(UnityEngine.Transform),"localEulerAnglesRaw."+axis);UnityEditor.AnimationUtility.SetEditorCurve(clip,binding,UnityEngine.AnimationCurve.Constant(0f,length,0f));}UnityEditor.EditorUtility.SetDirty(clip);UnityEditor.AssetDatabase.SaveAssets();FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("Scarab",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);System.IO.File.WriteAllText("'+(out/'installed_verify_after.txt').relative_to(ROOT).as_posix()+'",report);return new {pass=pass,report=report,length=clip.length};'
result = unwrap(c.tool('execute_code',dict(action='execute',code=code)))
write(out/'repair_mcp.json',dict(observed_at=now(),project=project,refresh=refresh,state_before=state,probe_before=probe,result=result,protocol_history=c.history))
assert result['success'] and result['data']['result']['pass'], result
after = sha(ROOT/clip_path)
assert after!=sha(out/'Walk_Directions_before.anim')
changed = [x for x in manifest['changes'] if sha(ROOT/x['path'])!=x['after'].upper()]
assert len(changed)==1 and changed[0]['path']==clip_path, changed
manifest.setdefault('repair_history',[]).append(dict(observed_at=now(),revision='side_reuse_repair_r02',path=clip_path,before=changed[0]['after'],after=after,
    reason='Reset otherwise unbound Body rotation during Walk/Run after death pool reuse',source_curves_events_timing_retained=True,
    original_manifest='side_reuse_repair_r02/installed_manifest.json',reapply_if_full_rig_build='Run this documented additive reset on a new repair revision; full Build regenerates copied clips'))
changed[0]['after']=after
manifest['verification']=result
write(D/'installed_manifest.json',manifest)
(D/'installed_verify.txt').write_text(result['data']['result']['report'],encoding='utf-8')
write(out/'repair.json',dict(observed_at=now(),path=clip_path,before=sha(out/'Walk_Directions_before.anim'),after=after,
    added_bindings=['Body/localEulerAnglesRaw.x','Body/localEulerAnglesRaw.y','Body/localEulerAnglesRaw.z'],constant_value=0,
    new_runtime_revisions=['runtime_r02','runtime_updeath_r02'],no_shared_code_or_source_changes=True,verify=True))
chain.update(current_stage='Scarab_side_reuse_r02_repaired_pending_two_Play_rounds',last_stage_evidence=(out/'repair.json').relative_to(ROOT).as_posix(),updated_at=now())
write(HERE/'conversation_chain.json',chain)
print(json.dumps(dict(repaired=clip_path,verify=True,source_curves_preserved=True,next=['runtime_r02','runtime_updeath_r02']),ensure_ascii=False))
