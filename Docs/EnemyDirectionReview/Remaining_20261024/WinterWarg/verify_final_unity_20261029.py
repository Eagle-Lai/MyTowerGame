from session_winterwarg import *
from mcp_call import URL
owner();out=D/'unity_release_final_20261029.json';assert not out.exists()
c=Client();report={'observed_at':now(),'transport':URL,'project':c.identity()}
report['errors_before']=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'});report['initial_state']=c.resource('mcpforunity://editor/state');idle(probe(c))
code='''var path="Assets/_UIAssets/Monsters/Dogs/WinterWarg/Directions/WinterWarg_Directions.png";
var importer=UnityEditor.AssetImporter.GetAtPath(path) as UnityEditor.TextureImporter;
if(importer==null)throw new System.Exception("WinterWarg atlas importer missing");
var sprites=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.OfType<UnityEngine.Sprite>(UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path)));
var battle=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Prefabs/Enemy/Enemy_WinterWarg.prefab");
return Newtonsoft.Json.JsonConvert.SerializeObject(new {spriteMode=importer.spriteImportMode.ToString(),ppu=importer.spritePixelsPerUnit,alphaIsTransparency=importer.alphaIsTransparency,mipmaps=importer.mipmapEnabled,spriteCount=sprites.Length,
sprites=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.OrderBy(sprites,s=>s.name),s=>new {name=s.name,ppu=s.pixelsPerUnit,x=s.rect.x,y=s.rect.y,w=s.rect.width,h=s.rect.height,pivotX=s.pivot.x,pivotY=s.pivot.y})),
dependencies=UnityEditor.AssetDatabase.GetDependencies(UnityEditor.AssetDatabase.GetAssetPath(battle),true),
clips=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(new [] {"Ready","Walk","Attack","Death"},n=>{var p="Assets/_UIAssets/Monsters/_Common/Animations/Wolf/"+n+".anim";var a=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(p);return new {name=n,path=p,length=a.length,loop=a.isLooping,rate=a.frameRate,floatBindings=UnityEditor.AnimationUtility.GetCurveBindings(a).Length,objectBindings=UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(a).Length,events=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(a),e=>new {time=e.time,functionName=e.functionName,intParameter=e.intParameter,stringParameter=e.stringParameter}))};}))});'''
report['installed_data']=result(c.tool('execute_code',{'action':'execute','code':code}))
cache='var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);if(t!=null){var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);if(m!=null)m.Invoke(null,new object[]{"WinterWarg final factual snapshot"});}return true;'
c.tool('execute_code',{'action':'execute','code':cache});report['state']=c.resource('mcpforunity://editor/state')
for key,args in [('errors',{}),('compile_errors',{'filter_text':'error CS'})]:
    r=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json',**args});report[key]=r.get('structuredContent') or json.loads(r['content'][0]['text'])
report['final_probe']=probe(c);idle(report['final_probe']);v=report['state']['data']
assert v['advice']['ready_for_tools'] and not v['tests']['is_running'] and not v['compilation']['is_compiling'] and not v['compilation']['is_domain_reload_pending'] and not v['assets']['is_updating']
assert report['errors']['data']==[] and report['compile_errors']['data']==[]
report.update(success=True,note='No Unity CSharp changed; actual 8088 import/dependency/native-clip checks, console not cleared.',protocol_history=c.history)
write(out,report,True)
print(json.dumps({k:report[k] for k in ['project','success','final_probe','errors','compile_errors']},ensure_ascii=False))
