from pathlib import Path
from datetime import datetime,timezone,timedelta
import subprocess,json,hashlib,os
HERE=Path(__file__).resolve().parent
c=json.loads((HERE.parent/'conversation_chain.json').read_text(encoding='utf-8'))
assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='WinterWolfTypeA'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
inputs=[HERE/'reference/WinterWolfTypeA.png',HERE/'reference/source_prefab_offline.png']
report={'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'credential_present':False,'new_paid_diagnostic_requests':0,'input_sha256':[sha(p) for p in inputs],'controls':[]}
for label,route in [('direct',['--noproxy','*']),('existing_local_proxy',['--proxy','http://127.0.0.1:7897','--noproxy',''])]:
    args=['curl.exe','-q','--silent','--show-error','--max-time','20','--connect-timeout','8','--proto','=https','--request','POST','--url','https://aihub.dog/v1/images/edits',*route,'--form-string','model=gpt-image-2','--form-string','quality=medium','--form-string','size=1536x1024','--form-string','n=1','--form-string','prompt=Unauthenticated transport control; no paid request.']
    for p in inputs:args+=['--form','image[]=@"'+p.as_posix()+'";type=image/png']
    args+=['--write-out','\nCONTROL_METRICS={"http_status":%{http_code},"uploaded":%{size_upload},"downloaded":%{size_download},"tls_verify":%{ssl_verify_result},"seconds":%{time_total}}\n']
    env=dict(os.environ);env.pop('AIHUB_IMAGE_API_KEY',None)
    result=subprocess.run(args,env=env,capture_output=True,text=True,encoding='utf-8',timeout=25)
    report['controls'].append({'route':label,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
file=HERE/'unauthenticated_transport_control_20261029.json';assert not file.exists();file.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
