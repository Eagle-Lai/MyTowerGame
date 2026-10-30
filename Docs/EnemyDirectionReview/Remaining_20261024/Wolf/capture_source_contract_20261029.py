from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent
RUN=HERE.parent
sys.path.insert(0,str(HERE))
from session_current import owner,save,sha,Client,probe,idle
owner();c=Client();project=c.identity();idle(probe(c))
for n in ['source_animation_contract_complete_20261029.json','source_controller_and_renderers_20261029.json']:
    prior=json.loads((RUN/'WinterWolfTypeB'/n).read_text(encoding='utf-8'))
    code=[x['params']['arguments']['code'] for x in prior['protocol_history'] if x.get('params',{}).get('name')=='execute_code'][-1].replace('WinterWolfTypeB','Wolf')
    from session_current import unwrap
    value=unwrap(c.tool('execute_code',{'action':'execute','code':code}))
    save(HERE/n,{'project':project,'contract':value,'protocol_history':c.history})
    print(n, 'saved', len(json.dumps(value)))
