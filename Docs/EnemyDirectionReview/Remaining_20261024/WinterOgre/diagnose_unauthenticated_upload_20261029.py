"""Measure upload transport with NO API credential; cannot generate a paid image."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,subprocess,sys

D=Path(__file__).resolve().parent
H=D.parent
OWNER='01a18619-6aa0-7a31-ac62-10a82077950b'
TOKEN='winterboar-to-winterogre-20261029_131318-14b528b1-8990-455f-8069-d7ea49019046'
chain=json.loads((H/'conversation_chain.json').read_text(encoding='utf-8-sig'))
assert chain['owner_thread_id']==OWNER and chain['dispatch_token']==TOKEN and chain['state']=='active'
assert os.environ.get('CODEX_THREAD_ID')==OWNER
request=json.loads((D/'generation/Up/revision_03/request.json').read_text(encoding='utf-8-sig'))
env={k:v for k,v in os.environ.items() if k!='AIHUB_IMAGE_API_KEY'}
assert sys.argv[1:] in [[],['--system-proxy-control']]
proxy_control=sys.argv[1:]==['--system-proxy-control']
args=['curl.exe','-q','--silent','--show-error','--max-time','25','--connect-timeout','10','--proto','=https',
      '--request','POST','--url','https://aihub.dog/v1/images/edits','--write-out',
      '\nUNAUTH_METRICS={"http_status":%{http_code},"uploaded":%{size_upload},"downloaded":%{size_download},"remote_ip":"%{remote_ip}","total_seconds":%{time_total},"tls_verify":%{ssl_verify_result}}\n']
if proxy_control:args+=['--proxy','http://127.0.0.1:7897','--noproxy','']
for k,v in [('model','gpt-image-2'),('quality','medium'),('n','1'),('size','1536x1024')]:
    args+=['--form-string',k+'='+v]
args+=['--form','prompt=<'+str(D/'generation/Up/revision_03/prompt.txt')]
for file in request['inputs']:args+=['--form','image[]=@'+file]
started=datetime.now(timezone.utc).isoformat()
r=subprocess.run(args,capture_output=True,text=True,env=env,timeout=30)
report=dict(observed_at=started,completed_at=datetime.now(timezone.utc).isoformat(),
    purpose='Non-billable multipart upload transport diagnosis using existing references, with NO Authorization/header/cookie/API credential. Same exact HTTPS host, no redirects.',
    paid_requests=0,credential_present=False,method='POST',url='https://aihub.dog/v1/images/edits',
    route='explicit existing local system proxy http://127.0.0.1:7897' if proxy_control else 'existing direct route; NO_PROXY includes aihub.dog',
    inputs=[dict(name=Path(p).name,bytes=Path(p).stat().st_size,sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest()) for p in request['inputs']],
    process_exit=r.returncode,stdout=r.stdout[:3000],stderr=r.stderr[:2000],
    limitation='An unauthorized request cannot validate a successful authorized upstream generation. No previous uncertain request is reclassified.')
p=D/('unauthenticated_upload_diagnosis_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
assert not p.exists()
p.write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(evidence=str(p),**report),ensure_ascii=False))
