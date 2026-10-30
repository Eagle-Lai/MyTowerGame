from session_current import *
import subprocess, shutil

owner()
assert not (HERE / 'installed_manifest.json').exists()
revision = 'Up_local02_Down_AI01local02_alpha01_layout03_nativeattack01'
stage = {p.relative_to(HERE/'staged_art').as_posix(): sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
save(HERE / 'staged_visual_review_final_20261030.json', {
    'observed_at': now(), 'art_revision': revision,
    'viewed_full_images': {p: sha(HERE/p) for p in ['offline_four_directions_final_20261030.png', 'parts_clean.png', 'staged_art/PossessedWarg_Directions.png']},
    'findings': 'Own dark olive/brown warg coat, golden crown/back spikes, ochre details, amber eyes, ivory fangs, four legs and long tail retained. Rear head faceless, front ear pads and toe divisions removed, true front expressions retained. Torso duplicate muzzle removed locally; no ground shadow. Final roots overlap body, distant paws are mostly occluded under body in axial perspective, tail stays within image. Full parts/atlas checked; no visible magenta halo, cut outline or interior hole. Eight small mask-hole pixels filled, twelve detached dust pixels removed with preserved parent stage. Local02 and layout03 replace rejected seam/placement versions; raw images unchanged.',
    'stage_files': stage, 'internal_stage_accepted_for_install': True, 'user_approved': False,
    'own_native_contract': 'source_animation_contract_complete_20261030.json',
    'HeadSprites': 'Original actual three expressions plus original HeadRenderer correctly bound. No component or shared CSharp repair.',
})
c = Client(); project = c.identity()
errors = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'})
state = fresh_state(c, 'PossessedWarg install gate'); p = probe(c); idle(p)
files = snapshot()
assert files == read(HERE/'production_paths_before_20261030.json')
assert all(files[k] == v for k, v in read(HERE/'sync_start_20261030.json')['protected_six'].items())
save(HERE/'preinstall_final_20261030.json', {'observed_at': now(), 'project': project, 'probe': p, 'state': state,
    'errors': errors, 'production_fingerprints': files, 'six_protected_match': True, 'protocol_history': c.history})
owner()
subprocess.run([sys.executable, str(RUN/'install_character.py'), NAME], check=True)
owner(); c = Client(); c.identity(); idle(probe(c))
clip = ROOT / target()['art_dir'] / 'Animations/Attack_Directions.anim'
shutil.copy2(clip, HERE/'Attack_Directions_before_nativeattack01.anim')
before = snapshot()
code = '''var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/Dogs/PossessedWarg/Directions/Animations/Attack_Directions.anim");
var original=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Attack.anim");
float duration=original.length;
float wind=UnityEditor.AnimationUtility.GetAnimationEvents(original).First(e=>e.functionName=="SetHead"&&e.intParameter==1).time/duration;
float hit=UnityEditor.AnimationUtility.GetAnimationEvents(original).First(e=>e.functionName=="Event"&&e.stringParameter=="Attack").time/duration;
var bodyBinding=UnityEditor.AnimationUtility.GetCurveBindings(original).First(b=>b.path=="Body"&&b.propertyName=="m_LocalPosition.y");
var nativeBody=UnityEditor.AnimationUtility.GetEditorCurve(original,bodyBinding);
int changed=0;
foreach(var b in UnityEditor.AnimationUtility.GetCurveBindings(clip).Where(b=>b.path.StartsWith("DirectionVisual/"))){
 var curve=UnityEditor.AnimationUtility.GetEditorCurve(clip,b);var keys=new UnityEngine.Keyframe[61];
 bool whole=b.path.EndsWith("/Motion")&&b.propertyName=="m_LocalPosition.y";
 bool up=b.path.Contains("/Up/");float baseline=curve.Evaluate(0f);
 System.Func<float,float> sample=n=>{float u=n<=wind?n*.28f/wind:n<=hit?.28f+(n-wind)*.16f/(hit-wind):.44f+(n-hit)*.56f/(1f-hit);return whole?baseline+(up?1:-1)*(nativeBody.Evaluate(n*duration)-nativeBody.Evaluate(0f))*.65f:curve.Evaluate(u*duration);};
 for(int i=0;i<keys.Length;i++){float n=i/60f,l=Mathf.Max(0,n-.0005f),r=Mathf.Min(1,n+.0005f);float tangent=(sample(r)-sample(l))/((r-l)*duration);keys[i]=new UnityEngine.Keyframe(n*duration,sample(n),tangent,tangent);}
 UnityEditor.AnimationUtility.SetEditorCurve(clip,b,new UnityEngine.AnimationCurve(keys));changed++;
}
UnityEditor.EditorUtility.SetDirty(clip);UnityEditor.AssetDatabase.SaveAssets();
return new {duration=duration,windup_seconds=wind*duration,hit_seconds=hit*duration,changedDirectionalBindings=changed};'''
result = unwrap(c.tool('execute_code', {'action': 'execute', 'code': code}))
after = snapshot()
changes = [{'path': k, 'before': before.get(k), 'after': after.get(k)} for k in sorted(set(before)|set(after)) if before.get(k) != after.get(k)]
assert len(changes) == 1 and changes[0]['path'].endswith('/Attack_Directions.anim'), changes
save(HERE/'native_attack_timing01_manifest_20261030.json', {'observed_at': now(), 'result': result,
    'reason': 'Own Wolf native 0.5s Attack: anger/windup at 1/6s, force at 1/3s. Retime only added vertical curves; vertical body advance follows original Body y curve with view sign, 65 percent amplitude. Original horizontal curves, events, durations and loop retained.',
    'changes': changes, 'protocol_history': c.history})
verify = unwrap(c.tool('execute_code', {'action': 'execute', 'code': 'FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("PossessedWarg",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);return new {pass=pass,report=report};'}))
assert verify['pass'], verify
save(HERE/'installed_verify_nativeattack01_20261030.json', verify)
state = fresh_state(c, 'PossessedWarg prePlay final binding'); p = probe(c); idle(p)
errors = c.tool('read_console', {'action':'get','types':['error'],'count':'50','format':'json'})
files = snapshot(); scope = audit(files)
assert scope['pass'], scope
save(HERE/'scope_incremental_preplay_20261030.json', scope)
assert stage == {p.relative_to(HERE/'staged_art').as_posix(): sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
save(HERE/'preplay_version_binding_20261030.json', {'observed_at': now(), 'owner_thread_id': owner()['owner_thread_id'], 'dispatch_token': owner()['dispatch_token'],
    'art_revision': revision, 'project': project, 'production_fingerprints': bound(files), 'all_production_fingerprints': files,
    'staged_fingerprints': stage, 'manifest_sha256': sha(HERE/'installed_manifest.json'), 'verify_sha256': sha(HERE/'installed_verify.txt'),
    'nativeattack_verify_sha256': sha(HERE/'installed_verify_nativeattack01_20261030.json'),
    'scope': 'scope_incremental_preplay_20261030.json', 'probe': p, 'editor_state': state, 'errors': errors, 'protocol_history': c.history})
print(json.dumps({'installed': True, 'scope_pass': scope['pass'], 'semantic_pass': scope['prefab_semantic']['pass'], 'bound_paths':len(bound(files)), 'native_attack': result}))
