from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from mcp_call import Client
old=json.loads((HERE/'source_animation_contract_20261029.json').read_text(encoding='utf-8'))
code=next(h['params']['arguments']['code'] for h in old['protocol_history'] if h['method']=='tools/call' and h['params']['name']=='execute_code')
code=code.replace('return new {hierarchies=','var report = new {hierarchies=').replace('position=t.localPosition,rotation=t.localEulerAngles,scale=t.localScale','position=new[]{t.localPosition.x,t.localPosition.y,t.localPosition.z},rotation=new[]{t.localEulerAngles.x,t.localEulerAngles.y,t.localEulerAngles.z},scale=new[]{t.localScale.x,t.localScale.y,t.localScale.z}')
code+=' return Newtonsoft.Json.JsonConvert.SerializeObject(report);'
client=Client();project=client.identity()
response=client.tool('execute_code',{'action':'execute','code':code})
data=response.get('structuredContent') or json.loads(response['content'][0]['text'])
assert data['success'],data
result=data['data']['result']
if isinstance(result,str):result=json.loads(result)
(HERE/'source_animation_contract_complete_20261029.json').write_text(json.dumps({'project':project,'contract':result,'protocol_history':client.history},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'hierarchies':result['hierarchies'],'parameters':result['parameters'],'clips':[{k:v for k,v in c.items() if k not in ['floatCurves','pptrCurves']}|{'float_bindings':len(c['floatCurves']),'pptr_bindings':len(c['pptrCurves']),'float_paths':sorted(set(x['path'] for x in c['floatCurves']))} for c in result['clips']]},ensure_ascii=False))
