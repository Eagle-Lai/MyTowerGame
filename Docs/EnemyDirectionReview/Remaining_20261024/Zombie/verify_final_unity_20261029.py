from session_current import *
from mcp_call import URL

owner();out=HERE/'unity_release_final_20261029.json';assert not out.exists()
c=Client();report={'observed_at':now(),'transport':URL,'project':c.identity()}
report['errors_before']=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
report['initial_state']=fresh_state(c,'Zombie final verification entry');idle(probe(c))
code='''var path="Assets/_UIAssets/Monsters/Giants/Zombie/Directions/Zombie_Directions.png";
var importer=UnityEditor.AssetImporter.GetAtPath(path) as UnityEditor.TextureImporter;
if(importer==null)throw new System.Exception("Zombie atlas importer missing");
var sprites=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.OfType<UnityEngine.Sprite>(UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path)));
var battle=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Prefabs/Enemy/Enemy_Zombie.prefab");
return Newtonsoft.Json.JsonConvert.SerializeObject(new {spriteMode=importer.spriteImportMode.ToString(),ppu=importer.spritePixelsPerUnit,alphaIsTransparency=importer.alphaIsTransparency,mipmaps=importer.mipmapEnabled,spriteCount=sprites.Length,
sprites=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.OrderBy(sprites,s=>s.name),s=>new {name=s.name,ppu=s.pixelsPerUnit,x=s.rect.x,y=s.rect.y,w=s.rect.width,h=s.rect.height,pivotX=s.pivot.x,pivotY=s.pivot.y})),
dependencies=UnityEditor.AssetDatabase.GetDependencies(UnityEditor.AssetDatabase.GetAssetPath(battle),true),
clips=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(new [] {"Ready","Walk","Attack","Death"},n=>{var p="Assets/_UIAssets/Monsters/_Common/Animations/Giant/"+n+".anim";var a=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(p);return new {name=n,path=p,length=a.length,loop=a.isLooping,rate=a.frameRate,floatBindings=UnityEditor.AnimationUtility.GetCurveBindings(a).Length,objectBindings=UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(a).Length,events=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(a),e=>new {time=e.time,functionName=e.functionName,intParameter=e.intParameter,stringParameter=e.stringParameter}))};}))});'''
report['installed_data']=unwrap(c.tool('execute_code',{'action':'execute','code':code}))
data=report['installed_data'];expected=read(HERE/'staged_art/Zombie_Directions.sprites.json')
assert data['spriteCount']==len(expected['sprites'])==14 and data['ppu']==100 and data['spriteMode']=='Multiple'
assert data['alphaIsTransparency'] and not data['mipmaps']
checks=[]
for s in expected['sprites']:
    live=next(a for a in data['sprites'] if a['name']==s['name'])
    ok=all(abs(live[k]-s[k])<.001 for k in ['x','y','w','h']) and abs(live['pivotX']-s['pivotX']*s['w'])<.01 and abs(live['pivotY']-s['pivotY']*s['h'])<.01 and live['ppu']==100
    checks.append({'name':s['name'],'pass':ok})
assert all(r['pass'] for r in checks),checks
report['sprite_checks']=checks
assert 'Assets/_UIAssets/Monsters/Giants/Zombie/Directions/Zombie_Directions.png' in data['dependencies']
assert 'Assets/_UIAssets/Monsters/Giants/Zombie/Directions/Animations/Zombie_Directions.controller' in data['dependencies']
contract=read(HERE/'source_animation_contract_complete_20261029.json')['contract']
for clip in data['clips']:
    original=next(v for v in contract['clips'] if v['name']==clip['name'])
    assert abs(original['length']-clip['length'])<.00001 and original['loop']==clip['loop'] and original['frameRate']==clip['rate']
    assert [{k:e[k] for k in ['time','functionName','intParameter','stringParameter']} for e in original['events']]==clip['events']
assert [(v['floatBindings'],v['objectBindings']) for v in data['clips']]==[(18,0),(30,0),(27,0),(24,0)]
report['live_Verify']=unwrap(c.tool('execute_code',{'action':'execute','code':'FTProject.EditorTools.EnemyDirectionSpec spec; if(!FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("Zombie",out spec))throw new System.Exception("Zombie spec missing"); string text; bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out text); return new {pass=pass,report=text};'}))
assert report['live_Verify']['pass'] and 'FAIL ' not in report['live_Verify']['report']
report['state']=fresh_state(c,'Zombie final verified factual snapshot')
for key,args in [('errors',{}),('compile_errors',{'filter_text':'error CS'})]:
    r=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json',**args})
    report[key]=r.get('structuredContent') or json.loads(r['content'][0]['text'])
report['final_probe']=probe(c);idle(report['final_probe']);v=report['state']['data']
assert report['errors']['data']==[] and report['compile_errors']['data']==[]
pre=read(HERE/'preplay_version_binding_20261029.json')
assert bound(snapshot())==pre['production_fingerprints']
report.update(success=True,production_unchanged_since_preplay=True,note='No Unity CSharp changed; actual 8088 import/dependency/native-clip checks and live Verify. Console not cleared.',protocol_history=c.history)
save(out,report)
print(json.dumps({k:report[k] for k in ['project','success','final_probe','errors','compile_errors']},ensure_ascii=False))
