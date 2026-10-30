"""Read the final installed WinterOgre, native clip contract, and 8088 editor state."""
from session_winterogre import *
from mcp_call import URL

owner()
output = D / 'unity_release_final_20261029.json'
assert not output.exists()
c = Client()
report = {'observed_at': now(), 'transport': URL}
try:
    report['project'] = c.identity()
    report['errors_before'] = c.tool('read_console', {'action':'get','types':['error'],'count':'50','format':'json'})
    report['initial_state'] = c.resource('mcpforunity://editor/state')
    report['live_probe'] = probe(c)
    idle(report['live_probe'])
    code = '''var path="Assets/_UIAssets/Monsters/Giants/WinterOgre/Directions/WinterOgre_Directions.png";
var importer=UnityEditor.AssetImporter.GetAtPath(path) as UnityEditor.TextureImporter;
if(importer==null)throw new System.Exception("WinterOgre atlas importer missing");
var sprites=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.OfType<UnityEngine.Sprite>(UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path)));
var battle=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Prefabs/Enemy/Enemy_WinterOgre.prefab");
return Newtonsoft.Json.JsonConvert.SerializeObject(new {spriteMode=importer.spriteImportMode.ToString(),ppu=importer.spritePixelsPerUnit,alphaIsTransparency=importer.alphaIsTransparency,mipmaps=importer.mipmapEnabled,spriteCount=sprites.Length,
sprites=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.OrderBy(sprites,s=>s.name),s=>new {name=s.name,ppu=s.pixelsPerUnit,x=s.rect.x,y=s.rect.y,w=s.rect.width,h=s.rect.height,pivotX=s.pivot.x,pivotY=s.pivot.y})),
dependencies=UnityEditor.AssetDatabase.GetDependencies(UnityEditor.AssetDatabase.GetAssetPath(battle),true),
weaponEnabled=battle.transform.Find("Body/ArmR/FistR/Weapon").GetComponent<UnityEngine.SpriteRenderer>().enabled,
clips=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(new [] {"Ready","Walk","Attack","Death"},n=>{var p="Assets/_UIAssets/Monsters/_Common/Animations/Giant/"+n+".anim";var a=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(p);return new {name=n,path=p,length=a.length,loop=a.isLooping,rate=a.frameRate,floatBindings=UnityEditor.AnimationUtility.GetCurveBindings(a).Length,objectBindings=UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(a).Length,events=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(a),e=>new {time=e.time,functionName=e.functionName,intParameter=e.intParameter,stringParameter=e.stringParameter}))};}))});'''
    report['installed_data_response'] = c.tool('execute_code', {'action':'execute','code':code})
    report['installed_data'] = result(report['installed_data_response'])
    # Update plugin status metadata after the test runner has restored Boot; no asset/code refresh.
    cache = 'var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);if(t!=null){var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);if(m!=null)m.Invoke(null,new object[]{"WinterOgre final factual snapshot"});}return true;'
    report['state_cache_probe'] = c.tool('execute_code', {'action':'execute','code':cache})
    report['state'] = c.resource('mcpforunity://editor/state')
    report['errors_response'] = c.tool('read_console', {'action':'get','types':['error'],'count':'50','format':'json'})
    report['errors'] = report['errors_response'].get('structuredContent') or json.loads(report['errors_response']['content'][0]['text'])
    report['compile_errors_response'] = c.tool('read_console', {'action':'get','types':['error'],'filter_text':'error CS','count':'50','format':'json'})
    report['compile_errors'] = report['compile_errors_response'].get('structuredContent') or json.loads(report['compile_errors_response']['content'][0]['text'])
    report['final_probe'] = probe(c)
    idle(report['final_probe'])
    data = report['installed_data']
    assert data['spriteMode']=='Multiple' and data['ppu']==100 and data['spriteCount']==14
    assert data['alphaIsTransparency'] and not data['mipmaps'] and data['weaponEnabled'] is False
    state = report['state']['data']
    assert state['advice']['ready_for_tools'] and not state['tests']['is_running']
    assert not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending']
    assert not state['assets']['is_updating']
    assert report['compile_errors']['data']==[]
    report['success'] = True
    report['note'] = 'No shared Unity CSharp changed. Read-only contract/import/dependency checks; console retained without clearing.'
except Exception as error:
    report.update(success=False,error=str(error))
finally:
    report['protocol_history'] = c.history
    write(output, report, fresh=True)
print(json.dumps({k:report.get(k) for k in ['success','error','transport','project','final_probe','errors','compile_errors']},ensure_ascii=False))
if not report['success']: raise SystemExit(1)
