from pathlib import Path
import json,sys
from mcp_call import Client
HERE=Path(__file__).resolve().parent
name,revision=sys.argv[1:3];death_up=len(sys.argv)>3 and sys.argv[3]=='up'
client=Client();identity=client.identity()
response=client.tool('execute_code',{'action':'execute','code':'FTProject.EditorTools.EnemyDirectionBatchReview.Start('+json.dumps(name)+','+json.dumps(revision)+','+str(death_up).lower()+');return true;'})
record={'project':identity,'name':name,'revision':revision,'death_up':death_up,'response':response,'protocol_history':client.history}
(HERE/name/(revision+'_start.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ['protocol_history','response']},ensure_ascii=False))
