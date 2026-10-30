"""Run the two required real-Play reviews for ONE installed character, restoring scene each time."""
from pathlib import Path
import subprocess,sys,time,json
from mcp_call import Client
HERE=Path(__file__).resolve().parent;name=sys.argv[1]
for revision,death in [('runtime_r01',False),('runtime_updeath_r01',True)]:
    directory=HERE/name/revision
    if not directory.exists():
        args=[sys.executable,str(HERE/'start_runtime.py'),name,revision]+(['up'] if death else [])
        subprocess.run(args,check=True)
    deadline=time.monotonic()+180
    while not (directory/'actual_runtime_checks.txt').exists():
        if (directory/'exception.txt').exists():raise ValueError('Runtime exception: '+str(directory))
        if time.monotonic()>deadline:raise TimeoutError('Runtime review unfinished; not forcing Play exit: '+revision)
        time.sleep(2)
    if 'FAIL ' in (directory/'actual_runtime_checks.txt').read_text(encoding='utf-8'):raise ValueError('Failed runtime assertions: '+revision)
    deadline=time.monotonic()+30
    while True:
        client=Client();client.identity()
        result=client.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'})
        value=result.get('structuredContent') or json.loads(result['content'][0]['text'])
        state=value['data']['result']
        if not state['playing'] and not state['review']:
            (HERE/name/(revision+'_returned.json')).write_text(json.dumps({'state':state,'protocol_history':client.history},ensure_ascii=False,indent=2),encoding='utf-8');break
        if time.monotonic()>deadline:raise TimeoutError('Waiting for safe scene return; not forcing Play exit')
        time.sleep(2)
    print(name+' '+revision+' complete; Unity returned',flush=True)
subprocess.run([sys.executable,str(HERE/'finish_runtime.py'),name],check=True)
