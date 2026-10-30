from pathlib import Path
import json, sys
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parent))
from mcp_call import Client
old=json.loads((D/'preflight_20261028.json').read_text(encoding='utf-8'))
code=next(x['params']['arguments']['code'] for x in reversed(old['protocol_history']) if x['method']=='tools/call' and x['params']['name']=='execute_code')
code=code.replace('return new { battle=', 'return Newtonsoft.Json.JsonConvert.SerializeObject(new { battle=')
for expression in ['p.transform.localPosition','p.transform.localScale','v.transform.localPosition','v.transform.localScale']:
    code=code.replace(expression,expression+'.ToString()')
code=code.rsplit(' };',1)[0]+' });'
c=Client();project=c.identity()
result=c.tool('execute_code',{'action':'execute','code':code})
value=result.get('structuredContent') or json.loads(result['content'][0]['text'])
assert value['success'],value
contract=json.loads(value['data']['result'])
p=D/'source_contract_20261028.json'
assert not p.exists()
p.write_text(json.dumps({'project':project,'contract':contract,'protocol_history':c.history},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'clips':[{k:v[k] for k in ['name','length','loop','events']} for v in contract['clips']],'parameters':contract['parameters']},ensure_ascii=False))
