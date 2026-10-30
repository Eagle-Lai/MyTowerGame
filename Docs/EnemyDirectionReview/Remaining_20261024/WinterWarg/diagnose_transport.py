from session_winterwarg import *
import time

owner()
inputs=[D/'reference/WinterWarg.png',D/'reference/source_prefab_offline.png']
report={'observed_at':now(),'credential_present':False,'new_paid_diagnostic_requests':0,'input_sha256':[sha(p) for p in inputs],'controls':[]}
for label,route in [('direct',['--noproxy','*']),('existing_local_proxy',['--proxy','http://127.0.0.1:7897','--noproxy',''])]:
    args=['curl.exe','-q','--silent','--show-error','--max-time','30','--proto','=https','--request','POST','--url','https://aihub.dog/v1/images/edits',*route,'--form-string','model=gpt-image-2','--form-string','quality=medium','--form-string','size=1536x1024','--form-string','n=1','--form-string','prompt=Unauthenticated transport control; no paid request.']
    for p in inputs: args+=['--form','image[]=@"'+p.as_posix()+'";type=image/png']
    args+=['--write-out','\nCONTROL_METRICS={"http_status":%{http_code},"uploaded":%{size_upload},"downloaded":%{size_download},"tls_verify":%{ssl_verify_result},"seconds":%{time_total}}\n']
    env=dict(os.environ);env.pop('AIHUB_IMAGE_API_KEY',None)
    p=subprocess.run(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',timeout=40)
    report['controls'].append({'route':label,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
write(D/'unauthenticated_transport_control_20261029.json',report,True)
print(json.dumps(report,ensure_ascii=False))
