// Project-owner-authorized AIHub image edit. Key exists only in process memory.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
const gen=path.join(dir,'generation');
const output=path.join(gen,'raw.png');
const requestPath=path.join(gen,'request.json');
if(fs.existsSync(output)||fs.existsSync(requestPath))throw new Error('Existing request/result; inspect before any paid retry.');
const inputs=['tail_style_reference.png','original_style_reference.png','outward_direction_guide.png'].map(p=>path.join(gen,p));
const prompt=fs.readFileSync(path.join(dir,'generation_prompt.txt'),'utf8');
const request={started:new Date().toISOString(),endpoint:'https://aihub.dog/v1/images/edits',model:'gpt-image-2',quality:'medium',n:1,size:'1024x1024',inputs,prompt};
fs.writeFileSync(requestPath,JSON.stringify(request,null,2));
const form=new FormData();
for(const [k,v] of Object.entries({model:request.model,quality:request.quality,n:'1',size:request.size,prompt}))form.set(k,v);
for(const input of inputs)form.append('image[]',new Blob([fs.readFileSync(input)],{type:'image/png'}),path.basename(input));
try{
 const response=await fetch(request.endpoint,{method:'POST',redirect:'error',signal:AbortSignal.timeout(600000),headers:{Authorization:`Bearer ${process.env.AIHUB_IMAGE_API_KEY}`},body:form});
 const data=await response.json();
 if(!response.ok){fs.writeFileSync(path.join(gen,'result.json'),JSON.stringify({finished:new Date().toISOString(),status:response.status,error:data.error},null,2));throw new Error('AIHub HTTP '+response.status+' '+(data.error?.code??''));}
 const item=data.data?.[0];
 if(item?.b64_json)fs.writeFileSync(output,Buffer.from(item.b64_json,'base64'));
 else if(item?.url){const r=await fetch(item.url,{redirect:'error'});if(!r.ok)throw new Error('Result download HTTP '+r.status);fs.writeFileSync(output,Buffer.from(await r.arrayBuffer()));}
 else throw new Error('No image in success response');
 fs.writeFileSync(path.join(gen,'result.json'),JSON.stringify({finished:new Date().toISOString(),status:response.status,usage:data.usage,bytes:fs.statSync(output).size},null,2));
 console.log(JSON.stringify({status:response.status,file:output,bytes:fs.statSync(output).size}));
}catch(error){if(!fs.existsSync(path.join(gen,'result.json')))fs.writeFileSync(path.join(gen,'uncertain_result.json'),JSON.stringify({finished:new Date().toISOString(),error:error.name,message:error.message,note:'No automatic retry; inspect any existing server result.'},null,2));throw error;}
