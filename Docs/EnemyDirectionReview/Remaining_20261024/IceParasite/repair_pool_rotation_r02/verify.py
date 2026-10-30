import json, sys
from pathlib import Path
REV=Path(__file__).resolve().parent
sys.path.insert(0,str(REV.parent.parent))
from mcp_call import Client
def unwrap(v):
    v=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    if 'result' in v and 'data' not in v:v=v['result']
    assert v.get('success'),v
    return v['data']['result']
c=Client();project=c.identity()
refresh=c.tool('refresh_unity',{'mode':'force','scope':'assets','compile':'none','wait_for_ready':True})
c.identity()
code='''
var lines=new System.Collections.Generic.List<string>();
string root="Assets/_UIAssets/Monsters/Parasites/IceParasite/Directions/Animations/";
foreach(string action in new[]{"Ready","Walk"}) {
 var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(root+action+"_Directions.anim");
 foreach(string axis in new[]{"x","y","z"}) {
  var curve=UnityEditor.AnimationUtility.GetEditorCurve(clip,UnityEditor.EditorCurveBinding.FloatCurve("Body",typeof(UnityEngine.Transform),"localEulerAnglesRaw."+axis));
  if(curve==null || curve.keys.Length!=2 || curve.keys[0].value!=0 || curve.keys[1].value!=0 || curve.keys[1].time!=clip.length) throw new System.InvalidOperationException("Missing reset: "+action+axis);
  lines.Add(action+" Body "+axis+" resets at 0 and "+clip.length);
 }
}
FTProject.EditorTools.EnemyDirectionSpec spec;
FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("IceParasite",out spec);
string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);
System.IO.File.WriteAllText("Docs/EnemyDirectionReview/Remaining_20261024/IceParasite/repair_pool_rotation_r02/verify.txt",report);
return new {pass=pass,report=report,resetChecks=lines,compilationFailed=UnityEditor.EditorUtility.scriptCompilationFailed};
'''
verified=unwrap(c.tool('execute_code',{'action':'execute','code':code}))
assert verified['pass'] and not verified['compilationFailed'],verified
# Refresh the plugin's cached snapshot from live Unity state; idle snapshots otherwise go stale.
cache='''var t=typeof(MCPForUnity.Editor.Tools.RefreshUnity).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"IceParasite_readiness_probe"});return true;'''
cache_result=c.tool('execute_code',{'action':'execute','code':cache})
state=c.resource('mcpforunity://editor/state')
console=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
(REV/'verification.json').write_text(json.dumps({'project':project,'refresh':refresh,'verification':verified,'cache_refresh':cache_result,'state':state,'console':console,'protocol_history':c.history},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'verification':verified,'state':state,'console':console},ensure_ascii=False))
