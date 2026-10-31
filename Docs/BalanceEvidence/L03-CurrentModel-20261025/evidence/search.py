import json, pathlib, sys, hashlib, time
ROOT=pathlib.Path('D:/FreedomTower_1')
OUT=ROOT/'Library/L03StrategySearch-20261025'
sys.path.insert(0,str(ROOT/'Library/CodexLevel3Tuning'))
from unity_rpc import UnityRpc
def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def client(): return UnityRpc()
def execute(code):
    c=client();return c.call('execute_code',{'action':'execute','code':code})
def start(request):
    path=str(pathlib.Path(request).resolve()).replace(chr(92),'/')
    code='var verifier=System.AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetType("FTProject.EditorTools.BalancePlayModeVerifier")).First(x=>x!=null); verifier.GetMethod("StartBatch").Invoke(null,new object[]{"'+path+'"}); return "started";'
    return execute(code)
def request(name,ops_paths,wait=False,step=.02,keep=False):
    p=OUT/(name+'.request.json')
    runs=[{'profileId':'D04','levelId':3,'strategy':'replay','speed':1,'operationsPath':str(op).replace(chr(92),'/'),'waitForFunds':wait,'captureStages':False,'screenshots':False,'wallTimeoutSeconds':300} for op in ops_paths]
    dump(p,{'output':str(OUT/name).replace(chr(92),'/'),'stepSeconds':step,'stepsPerUpdate':100,'batchTimeoutSeconds':max(3600,350*len(runs)),'keepPlaying':keep,'captureOutcomes':True,'runs':runs})
    return p
if __name__=='__main__':
    if sys.argv[1]=='baseline':
        paths=list((ROOT/'Assets/ConfigJson').glob('*.json'))+list((ROOT/'Assets/Scripts').rglob('*.cs'))
        dump(OUT/'input-hashes.json',{str(p.relative_to(ROOT)).replace(chr(92),'/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
        p=request('baseline',[ROOT/'Docs/BalanceEvidence/L02-L30-ManualBalance-100Gold/L03/best-operations.json'],True)
        print(json.dumps(start(p)))
    elif sys.argv[1]=='schema':
        d=json.loads((ROOT/'Library/CodexLevel3Tuning/mcp-session.json').read_text())
        print(json.dumps([t for t in d['tools'] if t['name'] in sys.argv[2:]],ensure_ascii=False))
    elif sys.argv[1]=='start': print(json.dumps(start(sys.argv[2])))
    elif sys.argv[1]=='status':
        for p in OUT.glob('*/status.json'): print(p.parent.name,p.read_text())
