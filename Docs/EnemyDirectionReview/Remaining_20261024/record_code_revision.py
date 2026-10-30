from pathlib import Path
import json,hashlib,sys,difflib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
revision,path,reason=sys.argv[1:4]
before=HERE/'staged_code'/Path(path).name
after=ROOT/path
compile_evidence=[]
for stem in ['compile_hop_request_response','compile_hop_check_request_response','compile_hop_snapshot_request_response']:
    candidates=list(HERE.glob(stem+'*.json'))
    if candidates:compile_evidence.append(max(candidates,key=lambda p:p.stat().st_mtime).name)
report={'revision':revision,'path':path,'before_sha256':hashlib.sha256(before.read_bytes()).hexdigest().upper(),'after_sha256':hashlib.sha256(after.read_bytes()).hexdigest().upper(),'reason':reason,'compile_evidence':compile_evidence,'scope':'Editor-only optional layout motion fields. Previously installed layouts have no motion tuning block; their baked assets are not rebuilt.'}
out=HERE/('code_revision_'+revision+'.json')
if out.exists():raise ValueError('Revision record exists')
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/('code_revision_'+revision+'.patch')).write_text(''.join(difflib.unified_diff(before.read_text(encoding='utf-8').splitlines(True),after.read_text(encoding='utf-8').splitlines(True),fromfile=path+' before',tofile=path+' after')),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
