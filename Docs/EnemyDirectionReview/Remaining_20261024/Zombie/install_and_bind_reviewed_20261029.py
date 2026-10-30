from session_current import *
import subprocess,shutil

owner();assert not (HERE/'installed_manifest.json').exists()
art_revision='Up_AIrevision01_Down_AIinitial_alpha01_layout02_nativeattack01'
stage={p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
save(HERE/'staged_visual_review_final_20261029.json',{'observed_at':now(),'art_revision':art_revision,
 'viewed_full_images':{p:sha(HERE/p) for p in ['offline_four_directions_final_20261029.png','offline_Up.png','offline_Down.png','parts_clean.png']},
 'findings':'Actually viewed full source atlas/source/battle, accepted Up AI correction and Down original sheets, all fourteen transparent parts, four-direction equal-height offline comparison and uncropped rear/front. Plain rear skull/outer ear backs with original small brain; matching frontal normal/angry/dead expressions, skin seams and ochre patches, two cuffs, short pale torn loincloth, single wooden spiked club on anatomical RIGHT. Rear smooth heels, front toes; no skull jewelry or new equipment. Layout02 buries hip and arm roots and hides rear shoulder junctions. Widened Docs preview only to retain entire club. Alpha01 fills recorded small extraction holes; final 0 holes/0 magenta. Two legs/two arms, no floating or duplicate organs, no ground shadow. Actual Play required for animation.',
 'stage_files':stage,'user_approved':False})
c=Client();project=c.identity();errors={}
for key,args in [('errors',{}),('errorCS',{'filter_text':'error CS'})]:
 v=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json',**args});errors[key]=v.get('structuredContent') or json.loads(v['content'][0]['text']);assert errors[key]['data']==[]
state=fresh_state(c,'Zombie preinstall actual snapshot');p=probe(c);idle(p)
files=snapshot();assert files==read(HERE/'production_paths_before_20261029.json')
scope=audit(files);assert all(x['matches'] for x in scope['protected_six'].values())
save(HERE/'preinstall_final_20261029.json',{'observed_at':now(),'project':project,'errors':errors,'state':state,'probe':p,'scope_diagnostic':scope,'all_path_sha256_match':True,'diagnostic_note':'Preinstall semantic missing Directions is diagnostic only; exact full path/SHA and six protections are the gate.','protocol_history':c.history})
owner();subprocess.run([sys.executable,str(RUN/'install_character.py'),NAME],check=True)
# This character-only asset edit aligns vertical windup/strike/recovery with its
# own 1s Giant contract. It never touches original or horizontal bindings/events.
owner();c=Client();project=c.identity();idle(probe(c));before=bound(snapshot())
clip=ROOT/'Assets/_UIAssets/Monsters/Giants/Zombie/Directions/Animations/Attack_Directions.anim'
backup=HERE/'before_native_attack_timing01';backup.mkdir();shutil.copy2(clip,backup/clip.name)
code=r'''
var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/Giants/Zombie/Directions/Animations/Attack_Directions.anim");
var original=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/_Common/Animations/Giant/Attack.anim");
float hit=UnityEditor.AnimationUtility.GetAnimationEvents(original).First(e=>e.functionName=="Event"&&e.stringParameter=="Attack").time;
float wind=2f/3f;int changed=0;
foreach(var b in UnityEditor.AnimationUtility.GetCurveBindings(clip)){
 if(!b.path.StartsWith("DirectionVisual/",System.StringComparison.Ordinal))continue;
 var curve=UnityEditor.AnimationUtility.GetEditorCurve(clip,b);var keys=new UnityEngine.Keyframe[61];
 bool armed=b.path.EndsWith("/ArmR",System.StringComparison.Ordinal),free=b.path.EndsWith("/ArmL",System.StringComparison.Ordinal),angle=b.propertyName=="localEulerAnglesRaw.z",down=b.path.StartsWith("DirectionVisual/Down/",System.StringComparison.Ordinal);
 float baseline=curve.Evaluate(0f);
 System.Func<float,float> sample=t=>{float u=t<=wind?t*.28f/wind:t<=hit?.28f+(t-wind)*.16f/(hit-wind):.44f+(t-hit)*.56f/(1f-hit);float v=curve.Evaluate(u);if(angle&&(armed||free)){float delta=v-baseline;if(down)delta=-delta;if(free)delta*=.30f;v=baseline+delta;}return v;};
 for(int i=0;i<=60;i++){float t=i/60f,left=UnityEngine.Mathf.Max(0,t-.0005f),right=UnityEngine.Mathf.Min(1,t+.0005f);float tangent=(sample(right)-sample(left))/(right-left);keys[i]=new UnityEngine.Keyframe(t,sample(t),tangent,tangent);}
 UnityEditor.AnimationUtility.SetEditorCurve(clip,b,new UnityEngine.AnimationCurve(keys));changed++;
}
UnityEditor.EditorUtility.SetDirty(clip);UnityEditor.AssetDatabase.SaveAssets();
FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("Zombie",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);
System.IO.File.WriteAllText("Docs/EnemyDirectionReview/Remaining_20261024/Zombie/native_attack_timing01_verify.txt",report);
return new {pass=pass,report=report,changedDirectionalBindings=changed,windupEnd=wind,attackEventTime=hit,length=clip.length};
'''
result=unwrap(c.tool('execute_code',{'action':'execute','code':code}));assert result['pass'] and result['length']==1.0
after=bound(snapshot());changes=[{'path':p,'before':before.get(p),'after':after.get(p)} for p in set(before)|set(after) if before.get(p)!=after.get(p)]
assert len(changes)==1 and changes[0]['path'].endswith('/Attack_Directions.anim'),changes
save(HERE/'native_attack_timing01_manifest_20261029.json',{'observed_at':now(),'reason':'Giant 1s Attack has native damage event at 0.766666651s and long windup through 2/3s. Retime only existing vertical curves; mirror right-arm swing front/rear and reduce free-arm countergesture. Preserve every original horizontal float/PPtr curve, original events/length/loop and source files.','changes':changes,'result':result,'protocol_history':c.history})
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'});assert (errors.get('structuredContent') or json.loads(errors['content'][0]['text']))['data']==[]
state=fresh_state(c,'Zombie installed native timing actual snapshot');p=probe(c);idle(p);files=snapshot();scope=audit(files);assert scope['pass'],scope
save(HERE/'scope_incremental_preplay_20261029.json',scope)
assert stage=={p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
save(HERE/'preplay_version_binding_20261029.json',{'observed_at':now(),'owner_thread_id':owner()['owner_thread_id'],'dispatch_token':owner()['dispatch_token'],'art_revision':art_revision,'project':project,
 'production_fingerprints':bound(files),'all_production_fingerprints':files,'staged_fingerprints':stage,'manifest_sha256':sha(HERE/'installed_manifest.json'),'verify_sha256':sha(HERE/'installed_verify.txt'),
 'native_attack_manifest_sha256':sha(HERE/'native_attack_timing01_manifest_20261029.json'),'native_attack_verify_sha256':sha(HERE/'native_attack_timing01_verify.txt'),'probe':p,'editor_state':state,'errors':errors})
print(json.dumps({'installed':True,'semantic_pass':scope['prefab_semantic']['pass'],'scope_pass':scope['pass'],'bound_files':len(bound(files)),'paths':len(files),'directional_attack_bindings_retimed':result['changedDirectionalBindings']}))
