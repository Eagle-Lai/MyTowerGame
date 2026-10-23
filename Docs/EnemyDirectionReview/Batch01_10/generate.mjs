// AIHub is explicitly authorized by AGENTS.md. Key exists in process memory only.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const [name,direction,revision]=process.argv.slice(2);
if(!/^[A-Za-z]+$/.test(name??'')||!['Up','Down'].includes(direction))throw new Error('Use character name and Up/Down');
if(revision&&!/^revision_\d\d$/.test(revision))throw new Error('Invalid revision');
const dir=path.join(root,name,'generation',direction,...(revision?[revision]:[]));
const output=path.join(dir,'raw.png');
if(fs.existsSync(output))throw new Error('Output already exists; a paid request will not be repeated.');
if(fs.existsSync(path.join(dir,'request.json')))throw new Error('Prior request exists. Inspect its result before any retry.');
const target=JSON.parse(fs.readFileSync(path.join(root,'local_baseline.json'),'utf8')).targets.find(t=>t.name===name);
const inputs=[path.join(root,name,'reference',name+'.png'),path.join(root,name,'reference','source_prefab_offline.png')];
if(revision)inputs.push(path.join(root,name,'generation',direction,'raw.png'));
const prompt=fs.readFileSync(path.join(dir,'prompt.txt'),'utf8');
const request={started:new Date().toISOString(),endpoint:'https://aihub.dog/v1/images/edits',model:'gpt-image-2',quality:'medium',n:1,size:'1536x1024',inputs,prompt};
fs.writeFileSync(path.join(dir,'request.json'),JSON.stringify(request,null,2));
const form=new FormData();
for(const [k,v] of Object.entries({model:request.model,quality:request.quality,n:'1',size:request.size,prompt}))form.set(k,v);
for(const input of inputs)form.append('image[]',new Blob([fs.readFileSync(input)],{type:'image/png'}),path.basename(input));
try{
 const response=await fetch(request.endpoint,{method:'POST',redirect:'error',signal:AbortSignal.timeout(600000),headers:{Authorization:`Bearer ${process.env.AIHUB_IMAGE_API_KEY}`},body:form});
 const data=await response.json();
 if(!response.ok){fs.writeFileSync(path.join(dir,'result.json'),JSON.stringify({finished:new Date().toISOString(),status:response.status,error:data.error},null,2));throw new Error('AIHub HTTP '+response.status+' '+(data.error?.code??''));}
 const item=data.data?.[0];
 if(item?.b64_json)fs.writeFileSync(output,Buffer.from(item.b64_json,'base64'));
 else if(item?.url){const result=await fetch(item.url,{redirect:'error'});if(!result.ok)throw new Error('Image download HTTP '+result.status);fs.writeFileSync(output,Buffer.from(await result.arrayBuffer()));}
 else throw new Error('Success response contained no image');
 fs.writeFileSync(path.join(dir,'result.json'),JSON.stringify({finished:new Date().toISOString(),status:response.status,usage:data.usage,bytes:fs.statSync(output).size},null,2));
 console.log(JSON.stringify({name,direction,status:response.status,file:output,bytes:fs.statSync(output).size}));
}catch(error){if(!fs.existsSync(path.join(dir,'result.json')))fs.writeFileSync(path.join(dir,'uncertain_result.json'),JSON.stringify({finished:new Date().toISOString(),error:error.name,message:error.message,note:'No automatic retry. Check for an existing server result before repeating.'},null,2));throw error;}
