from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,re,subprocess,sys
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2];sys.path.insert(0,str(H))
from mcp_call import Client
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):
    assert not p.exists(),str(p)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='Sheep'
manifest=read(D/'installed_manifest.json');assert all(sha(R/x['path'])==x['after'] for x in manifest['changes'])
result=subprocess.run([sys.executable,str(H/'audit_scope.py'),'scope_Sheep_preplay_20261028.json'],capture_output=True,encoding='utf-8',check=True);(D/'preplay_scope_console.txt').write_text(result.stdout,encoding='utf-8')
scope=read(H/'scope_Sheep_preplay_20261028.json');before=read(H/'scope_Sheep_before_20261028.json')
assert scope['semantics']['Sheep']['pass'],scope['semantics']['Sheep']
assert {x['path']:x['after'] for x in scope['unexpected']}=={x['path']:x['after'] for x in before['unexpected']}
source=(D/'reference/Enemy_Sheep.prefab').read_text(encoding='utf-8-sig');installed=(R/'Assets/Prefabs/Enemy/Enemy_Sheep.prefab').read_text(encoding='utf-8-sig')
original_sprite_contract={}
for fid,block in re.findall(r'^--- !u!212 &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',source,re.M|re.S):
    if 'guid: fefe1d76b13a7e14abf83510d6d1eeb6' in block:continue
    old=re.search(r'^  m_Sprite: .+$',block,re.M)[0];current=re.search(r'^--- !u!212 &'+fid+r'\s*\n(.*?)(?=^--- !u!|\Z)',installed,re.M|re.S)
    assert current and re.search(r'^  m_Sprite: .+$',current[1],re.M)[0]==old,(fid,old)
    original_sprite_contract[fid]=old
client=Client();project=client.identity();errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));assert errors['data']==[]
code='''var source=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.RuntimeAnimatorController>("Assets/_UIAssets/Monsters/_Common/Animations/Goat/Controller.controller");return new{dependencies=UnityEditor.AssetDatabase.GetDependencies("Assets/Prefabs/Enemy/Enemy_Sheep.prefab",true),clips=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Distinct(source.animationClips),clip=>new{name=clip.name,length=clip.length,loop=clip.isLooping,bindings=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(clip),b=>new{path=b.path,property=b.propertyName,values=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetEditorCurve(clip,b).keys,k=>new{time=k.time,value=k.value}))})),events=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(clip),e=>new{time=e.time,function=e.functionName,intParameter=e.intParameter}))})),headPosition=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Prefabs/Enemy/Enemy_Sheep.prefab").transform.Find("Body/Head").localPosition};'''
contracts=unwrap(client.tool('execute_code',dict(action='execute',code=code)));assert contracts['success']
write(D/'source_animation_contracts_20261028.json',dict(project=project,result=contracts,original_sprite_contract=original_sprite_contract,verify_report_sha256=sha(D/'installed_verify.txt'),source_body_rotation='Goat Death has no Body rotation; no Scarab-specific additive reset applied. Reuse checked in real Play.',dependency_limit='AssetDatabase dependency and existing YooAsset collector coverage only. No package build or release archive readback.',history=client.history))
write(D/'preplay_version_binding_20261028.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),installed_manifest_sha256=sha(D/'installed_manifest.json'),installed_files={x['path']:sha(R/x['path']) for x in manifest['changes']},staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},original_sprites=original_sprite_contract,source_contract_sha256=sha(D/'source_animation_contracts_20261028.json'),runtime_revisions=['runtime_r01','runtime_updeath_r01']))
print(json.dumps(dict(semantics=True,original_sprites_retained=len(original_sprite_contract),installed_files=len(manifest['changes']),legacy_unexpected=len(scope['unexpected']),source_contracts=True)))
