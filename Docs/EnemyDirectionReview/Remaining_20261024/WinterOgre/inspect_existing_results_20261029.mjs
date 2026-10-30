// Only documented GET endpoints. This file cannot submit an image operation.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const dir=path.dirname(fileURLToPath(import.meta.url)),hub=path.dirname(dir);
const owner='01a18619-6aa0-7a31-ac62-10a82077950b';
const token='winterboar-to-winterogre-20261029_131318-14b528b1-8990-455f-8069-d7ea49019046';
const chain=JSON.parse(fs.readFileSync(path.join(hub,'conversation_chain.json'),'utf8'));
if(chain.state!=='blocked'||chain.owner_thread_id!==owner||chain.dispatch_token!==token||process.env.CODEX_THREAD_ID!==owner)throw new Error('Only the retained blocked owner may inspect');
const key=process.env.AIHUB_IMAGE_API_KEY;
if(!key||/[\r\n"\\]/.test(key))throw new Error('Runtime-only credential required');
const clean=s=>String(s).split(key).join('[REDACTED]').replace(/sk-[A-Za-z0-9_-]{12,}/g,'[REDACTED]');
const report={observed_at:new Date().toISOString(),owner_thread_id:owner,dispatch_token:token,paid_requests:0,
 purpose:'Search existing documented image batch metadata for recoverable results, without creating a batch or changing synchronous edit request outcomes.',
 source:'GET /v1/images/batches?limit is used by the current public AIHub BatchImageGuideView-C20d0zIh.js. GET /v1/usage by KeyUsageView-DpOKodHs.js.',responses:[]};
for(const url of ['https://aihub.dog/v1/images/batches?limit=20','https://aihub.dog/v1/usage?start_date=2026-10-29&end_date=2026-10-29&days=1&timezone=Asia%2FShanghai']){
 const env={...process.env};delete env.AIHUB_IMAGE_API_KEY;
 const r=spawnSync('curl.exe',['-q','--config','-','--silent','--show-error','--max-time','20','--connect-timeout','8','--proto','=https','--request','GET','--url',url,'--write-out','\nINSPECT_HTTP=%{http_code}\n'],
  {input:'header = "Authorization: Bearer '+key+'"\n',encoding:'utf8',maxBuffer:4*1024*1024,timeout:25000,windowsHide:true,env});
 const m=r.stdout?.match(/\nINSPECT_HTTP=(\d{3})\s*$/);
 const entry={url,method:'GET',exit_code:r.status,http_status:m?Number(m[1]):null};
 if(!m||r.status!==0)entry.error=clean(r.stderr||r.error?.message||'Transport failed').slice(0,600);
 else try{
  const v=JSON.parse(r.stdout.slice(0,m.index));
  entry.response_keys=Object.keys(v);
  if(url.includes('/batches?')){
   const items=Array.isArray(v)?v:Array.isArray(v.data)?v.data:v.items||v.batches||v.data?.items||[];
   entry.items_count=Array.isArray(items)?items.length:null;
   entry.metadata=Array.isArray(items)?items.map(i=>Object.fromEntries(['id','object','model','status','created_at','completed_at','task_name','parent_batch_id','counts','request_count','completed_count','failed_count','actual_cost'].filter(k=>k in i).map(k=>[k,typeof i[k]==='string'?clean(i[k]):i[k]]))):[];
   entry.pagination=Object.fromEntries(['has_more','next_cursor','total','limit','cursor'].filter(k=>k in v).map(k=>[k,v[k]]));
   if(v.error||v.message)entry.message=clean(v.error?.message||v.message);
  }else entry.aggregate={balance:v.balance,unit:v.unit,isValid:v.isValid,daily_usage:v.daily_usage};
 }catch{entry.response_preview=clean(r.stdout.slice(0,m.index)).slice(0,500);}
 report.responses.push(entry);
}
report.limitations='These five synchronous edits were not submitted as batches. Empty batch metadata does not prove they failed or were free. A GET aggregate does not assign a charge to an individual missing outcome.';
report.completed_at=new Date().toISOString();
const out=path.join(dir,'existing_result_inspection_'+report.completed_at.replace(/[-:]/g,'').replace(/\..*$/,'Z')+'.json');
const bytes=JSON.stringify(report,null,2)+'\n';
if(bytes.includes(key))throw new Error('Refuse credential in evidence');
fs.writeFileSync(out,bytes,{flag:'wx'});
console.log(JSON.stringify({file:out,sha256:createHash('sha256').update(bytes).digest('hex'),...report}));
