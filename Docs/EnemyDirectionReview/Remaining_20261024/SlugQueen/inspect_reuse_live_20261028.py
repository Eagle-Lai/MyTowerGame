from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,os,sys,time,subprocess
D=Path(__file__).resolve().parent;H=D.parent;sys.path.insert(0,str(H))
from mcp_call import Client
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='SlugQueen'
rev=sys.argv[1] if len(sys.argv)>1 else 'runtime_r01';out=D/rev
client=Client();identity=client.identity()
source_code='''var source=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.RuntimeAnimatorController>("Assets/_UIAssets/Monsters/_Common/Animations/Larva/Controller.controller");return string.Join("\\n",System.Linq.Enumerable.Select(System.Linq.Enumerable.Distinct(source.animationClips),clip=>clip.name+"|"+string.Join(";",System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(clip),b=>b.path+"/"+b.propertyName+"="+string.Join(",",System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetEditorCurve(clip,b).keys,k=>k.time+":"+k.value))))+"|events="+string.Join(";",System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(clip),e=>e.time+":"+e.functionName+":"+e.intParameter))));'''
contracts=unwrap(client.tool('execute_code',dict(action='execute',code=source_code)))
detail=D/'source_animation_contracts_detail_20261028.json'
if not detail.exists():detail.write_text(json.dumps(dict(project=identity,source_details=contracts),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if not (D/(rev+'_start.json')).exists():subprocess.run([sys.executable,str(H/'start_runtime.py'),'SlugQueen',rev],check=True)
rows=[];deadline=time.monotonic()+80
code='''var t=typeof(FTProject.EditorTools.EnemyDirectionBatchReview);var flags=System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static;var enemy=t.GetField("_enemy",flags).GetValue(null) as FTProject.BaseEnemy; if(!enemy)return new{present=false};var head=enemy.transform.Find("Body");return new{present=true,stage=(int)t.GetField("_stage",flags).GetValue(null),playing=UnityEditor.EditorApplication.isPlaying,frame=UnityEngine.Time.frameCount,headX=head.localEulerAngles.x,headY=head.localEulerAngles.y,headZ=head.localEulerAngles.z};'''
# Discover the concrete BaseEnemy namespace from existing project sources instead of guessing.
code=code.replace(' as FTProject.BaseEnemy',' as UnityEngine.Component')
while time.monotonic()<deadline:
    result=unwrap(client.tool('execute_code',dict(action='execute',code=code)))
    if not result.get('success'):
        rows.append(dict(transient_tool_result=result));time.sleep(1);client.identity();continue
    r=result['data']['result'];rows.append(r)
    if (out/'actual_runtime_checks.txt').exists():break
    time.sleep(.6)
else:raise TimeoutError('Read-only pose inspection timed out; did not force Play exit')
deadline=time.monotonic()+30
while time.monotonic()<deadline:
    probe=unwrap(client.tool('execute_code',dict(action='execute',code='return new{playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))['data']['result']
    if not probe['playing'] and not probe['review']:break
    time.sleep(1)
else:raise TimeoutError('Waiting for own safe return, not forcing Play exit')
before=[r for r in rows if r.get('present') and r.get('stage') in [2,3]];after=[r for r in rows if r.get('present') and r.get('stage')==16]
report=dict(project=identity,revision=rev,rows=rows,initial_horizontal_body_z=sorted({r['headZ'] for r in before}),after_reuse_horizontal_body_z=sorted({r['headZ'] for r in after}),returned=probe,history=client.history,method='Read actual live transforms during existing real Play tester, no Animator.Update or pose synthesis')
(D/('reuse_live_inspection_'+rev+'_20261028.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['history','rows']},ensure_ascii=False))
