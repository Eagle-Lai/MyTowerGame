// Read-only local Mihomo API diagnostics. No config, selection or listener write.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const dir=path.dirname(fileURLToPath(import.meta.url));
const hub=path.dirname(dir);
const owner='01a18619-6aa0-7a31-ac62-10a82077950b';
const token='winterboar-to-winterogre-20261029_131318-14b528b1-8990-455f-8069-d7ea49019046';
const chain=JSON.parse(fs.readFileSync(path.join(hub,'conversation_chain.json'),'utf8'));
if(chain.state!=='blocked'||chain.owner_thread_id!==owner||chain.dispatch_token!==token||process.env.CODEX_THREAD_ID!==owner)throw new Error('Expected retained blocked owner');
const configFile='C:/Users/Administrator/AppData/Roaming/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml';
const config=fs.readFileSync(configFile,'utf8');
const pipe=config.match(/^external-controller-pipe:\s*(.+)\s*$/m)?.[1].trim();
if(!pipe?.startsWith('\\\\.\\pipe\\verge-mihomo-'))throw new Error('Unexpected local proxy pipe');
async function get(route){
 return await new Promise((resolve,reject)=>{
  const socket=net.connect(pipe);const chunks=[];
  socket.setTimeout(5000,()=>socket.destroy(new Error('Local pipe timeout')));
  socket.on('connect',()=>socket.write('GET '+route+' HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'));
  socket.on('data',x=>chunks.push(x));socket.on('error',reject);
  socket.on('end',()=>{
   const bytes=Buffer.concat(chunks),boundary=bytes.indexOf('\r\n\r\n');
   if(boundary<0)return reject(new Error('Incomplete pipe HTTP response'));
   const headers=bytes.subarray(0,boundary).toString(),status=Number(headers.match(/^HTTP\/\d\.\d (\d+)/)?.[1]);
   let body=bytes.subarray(boundary+4);
   if(/transfer-encoding:\s*chunked/i.test(headers)){
    let offset=0;const parts=[];
    while(offset<body.length){const e=body.indexOf('\r\n',offset);if(e<0)throw new Error('Invalid chunk header');const n=parseInt(body.subarray(offset,e).toString(),16);if(!n)break;parts.push(body.subarray(e+2,e+2+n));offset=e+2+n+2;}body=Buffer.concat(parts);
   }
   try{resolve({status,body:JSON.parse(body.toString())});}catch{resolve({status,response_preview:body.toString().slice(0,100)});}
  });
 });
}
const report={observed_at:new Date().toISOString(),paid_requests:0,local_configuration_changed:false,
 config_file:configFile,config_sha256:createHash('sha256').update(config).digest('hex'),
 aihub_rules:config.split(/\r?\n/).filter(x=>/aihub\.dog/i.test(x)),responses:[]};
for(const route of ['/version','/configs','/proxies','/listeners']){
 try{
  const r=await get(route),entry={route,http_status:r.status};
  if(route==='/version')entry.data=r.body;
  if(route==='/configs')entry.data=Object.fromEntries(['mode','mixed-port','port','socks-port','allow-lan','log-level','listeners'].filter(k=>k in (r.body||{})).map(k=>[k,r.body[k]]));
  if(route==='/proxies')entry.groups=Object.values(r.body?.proxies||{}).filter(x=>Array.isArray(x.all)).map(x=>({name:x.name,type:x.type,now:x.now,members:x.all?.length,selected_type:r.body?.proxies?.[x.now]?.type}));
  if(route==='/listeners')entry.data=r.body||r.response_preview;
  report.responses.push(entry);
 }catch(e){report.responses.push({route,error:e.message});}
}
report.finding='The configured aihub.dog rule says DIRECT. Sending CONNECT through 7897 alone does not prove a different external network route; previous full unauthenticated upload remains only a buffering/connectivity control.';
const out=path.join(dir,'proxy_routing_inspection_'+new Date().toISOString().replace(/[-:]/g,'').replace(/\..*$/,'Z')+'.json');
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({file:out,...report}));
