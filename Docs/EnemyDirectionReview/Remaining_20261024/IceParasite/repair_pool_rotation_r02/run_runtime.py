from pathlib import Path
import subprocess,sys,time,json
REV=Path(__file__).resolve().parent;CHAR=REV.parent;HERE=CHAR.parent
sys.path.insert(0,str(HERE))
from mcp_call import Client
def unwrap(v):
    v=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    if 'result' in v and 'data' not in v:v=v['result']
    assert v.get('success'),v
    return v['data']['result']
probe='''
var type=typeof(FTProject.EditorTools.EnemyDirectionBatchReview);
var obj=type.GetField("_enemy",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).GetValue(null) as UnityEngine.Component;
var body=obj?obj.transform.Find("Body"):null;
var animator=obj?obj.GetComponent<UnityEngine.Animator>():null;
return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,stage=type.GetField("_stage",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).GetValue(null),bodyAngle=body?(float?)UnityEngine.Mathf.DeltaAngle(0,body.localEulerAngles.z):null,bodyScaleY=body?(float?)body.localScale.y:null,frame=UnityEngine.Time.frameCount,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};
'''
for revision,death in [('runtime_r02',False),('runtime_updeath_r02',True)]:
    output=CHAR/revision
    if not output.exists():
        subprocess.run([sys.executable,str(HERE/'start_runtime.py'),'IceParasite',revision]+(['up'] if death else []),check=True)
    else:
        assert (CHAR/(revision+'_start.json')).exists(), 'Only resume the already-started review'
    deadline=time.monotonic()+240
    observation_path=REV/(revision+'_live_observations.json')
    observations=json.loads(observation_path.read_text()) if observation_path.exists() else []
    while True:
        time.sleep(.5)
        try:
            c=Client();c.identity()
            state=unwrap(c.tool('execute_code',{'action':'execute','code':probe}))
        except Exception as error:
            if time.monotonic()>deadline:raise
            print('Waiting for review domain reload/reconnect: '+str(error),flush=True)
            time.sleep(5)
            continue
        observations.append(state)
        (REV/(revision+'_live_observations.json')).write_text(json.dumps(observations,indent=2),encoding='utf-8')
        if (output/'exception.txt').exists():raise RuntimeError((output/'exception.txt').read_text())
        if (output/'actual_runtime_checks.txt').exists() and not state['playing'] and not state['review']:
            checks=(output/'actual_runtime_checks.txt').read_text(encoding='utf-8')
            assert checks.count('PASS ')==84 and checks.count('FAIL ')==0,checks
            (CHAR/(revision+'_returned.json')).write_text(json.dumps({'state':state,'protocol_history':c.history},ensure_ascii=False,indent=2),encoding='utf-8')
            break
        if time.monotonic()>deadline:raise TimeoutError('Runtime unfinished; not forcing Play exit')
    reused=[o for o in observations if o['stage'] in [11,13,14,15,16] and o['bodyAngle'] is not None]
    assert all(abs(o['bodyAngle'])<.1 for o in reused),reused
    print(json.dumps({'revision':revision,'pass':84,'fail':0,'reuse_rotation_observations':len(reused),'max_body_angle':max([abs(o['bodyAngle']) for o in reused],default=None),'state':state}),flush=True)
    subprocess.run([sys.executable,str(HERE/'build_runtime_media.py'),'IceParasite',revision],check=True)
print('Both repaired real-Play revisions completed.',flush=True)
