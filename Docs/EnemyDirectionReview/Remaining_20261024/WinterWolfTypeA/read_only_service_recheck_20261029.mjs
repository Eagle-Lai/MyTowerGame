// Read-only, non-billable service inspection. No image POST or paid retry.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';

const dir=path.dirname(fileURLToPath(import.meta.url));
const root=path.dirname(dir);
const owner='01a18704-42a8-7f52-bc92-f8ca404a0b39';
const token='winterwarg-to-winterwolftypea-20261029_173527-8e8dd053-9008-4a8f-b69a-61a589f400a4';
const chain=JSON.parse(fs.readFileSync(path.join(root,'conversation_chain.json'),'utf8'));
if(!['active','blocked'].includes(chain.state)||chain.owner_thread_id!==owner||chain.dispatch_token!==token||process.env.CODEX_THREAD_ID!==owner)throw new Error('Read-only recheck requires the unchanged owner');
const secret=process.env.AIHUB_IMAGE_API_KEY;
if(!secret||/[\r\n"\\]/.test(secret))throw new Error('Missing or invalid runtime-only credential');
const sanitize=value=>{
 if(Array.isArray(value))return value.map(sanitize);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,/^(api_key|key|token|secret|email|username|user_name|user_email)$/i.test(k)?'[REDACTED]':sanitize(v)]));
 if(typeof value==='string')return value.split(secret).join('[REDACTED]').replace(/sk-[A-Za-z0-9_-]{12,}/g,'[REDACTED]');
 return value;
};
const report={observed_at:new Date().toISOString(),character:'WinterWolfTypeA',owner_thread_id:owner,dispatch_token:token,
 chain_state:chain.state,purpose:'Inspect current authentication/models and key usage. No image-generation/edit POST and no retry allowance change.',
 source:{usage_endpoint:'AIHub public KeyUsageView-DpOKodHs.js: fetch /v1/usage with Authorization Bearer and start_date/end_date/days/timezone parameters.',
  source_url:'https://aihub.dog/assets/KeyUsageView-DpOKodHs.js'},
 prior_requests_unchanged:true,unknown_charges_not_reclassified:true,paid_requests:0,responses:[]};
const urls=[
 'https://aihub.dog/v1/models',
 'https://aihub.dog/v1/usage?start_date=2026-10-29&end_date=2026-10-29&days=1&timezone=Asia%2FShanghai'
];
for(const url of urls){
 const childEnv={...process.env};delete childEnv.AIHUB_IMAGE_API_KEY;
 const start=Date.now();
 const r=spawnSync('curl.exe',['-q','--config','-','--silent','--show-error','--max-time','25','--connect-timeout','10','--proto','=https','--request','GET','--url',url,'--write-out','\nREAD_ONLY_HTTP_STATUS=%{http_code}\n'],
  {input:'header = "Authorization: Bearer '+secret+'"\n',env:childEnv,encoding:'utf8',windowsHide:true,maxBuffer:4*1024*1024,timeout:30000});
 const match=r.stdout?.match(/\nREAD_ONLY_HTTP_STATUS=(\d{3})\s*$/);
 const entry={url,method:'GET',duration_ms:Date.now()-start,process_exit:r.status,http_status:match?Number(match[1]):null};
 if(r.status!==0||!match)entry.transport_error=sanitize((r.stderr||r.error?.message||'Unknown transport error').slice(0,800));
 else{
  const body=r.stdout.slice(0,match.index);
  try{
   const parsed=JSON.parse(body);
   if(url.endsWith('/models')){
    entry.body_keys=Object.keys(parsed);
    entry.model_count=Array.isArray(parsed.data)?parsed.data.length:null;
    entry.image_models=Array.isArray(parsed.data)?parsed.data.filter(x=>/image/i.test(x.id||'')).map(x=>x.id):[];
   }else entry.body=sanitize(parsed);
  }catch{entry.body_preview=sanitize(body.slice(0,800));}
 }
 report.responses.push(entry);
}
const output=path.join(dir,'read_only_service_recheck_'+new Date().toISOString().replace(/[-:]/g,'').replace(/\..*$/,'Z')+'.json');
report.completed_at=new Date().toISOString();
report.limitations='GET/models or unauthenticated POST reachability does not prove billable image edits are available. Aggregate usage alone cannot assign a result or charge to an unknown individual request.';
const serialized=JSON.stringify(report,null,2)+'\n';
if(serialized.includes(secret))throw new Error('Refuse credential in evidence');
fs.writeFileSync(output,serialized,{flag:'wx'});
console.log(JSON.stringify({evidence:output,sha256:createHash('sha256').update(serialized).digest('hex'),...report}));
