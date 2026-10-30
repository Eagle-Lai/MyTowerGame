"""Restore the original serialized side Head sprite after builder preview initialization."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,re,shutil,sys
D=Path(__file__).resolve().parent;HERE=D.parent;ROOT=HERE.parents[2];sys.path.insert(0,str(HERE))
from mcp_call import Client
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
chain=read(HERE/'conversation_chain.json');assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and chain['current_character']=='ScarabMounted' and chain['dispatch_token']=='scarab-to-scarabmounted-dd3da45145854f44998a5b6bdc48d12e'
out=D/'source_head_repair_r02';assert not out.exists()
manifest=read(D/'installed_manifest.json');assert all(sha(ROOT/x['path'])==x['after'] for x in manifest['changes'])
c=Client();project=c.identity()
probe=unwrap(c.tool('execute_code',dict(action='execute',code='return new{playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success'] and not any(v for k,v in probe['data']['result'].items() if k!='scene') and probe['data']['result']['scene']=='Assets/Scenes/Boot.unity'
battle='Assets/Prefabs/Enemy/Enemy_ScarabMounted.prefab';p=ROOT/battle
original=(D/'reference/Enemy_ScarabMounted.prefab').read_text(encoding='utf-8-sig');current=p.read_text(encoding='utf-8-sig')
pat=r'(^--- !u!212 &2508898428600365937\s*\n)(.*?)(?=^--- !u!|\Z)'
old_block=re.search(pat,original,re.M|re.S);new_block=re.search(pat,current,re.M|re.S)
old_line=re.search(r'^  m_Sprite: .+$',old_block[2],re.M)[0];new_line=re.search(r'^  m_Sprite: .+$',new_block[2],re.M)[0]
assert old_line=='  m_Sprite: {fileID: -1828946549344447192, guid: 306903ba18c180f46ac3783156892cb4, type: 3}'
assert new_line=='  m_Sprite: {fileID: -1828946549344447192, guid: 61c99d3081db09a40a7cb3ef485b597a, type: 3}'
out.mkdir()
for name in ['installed_manifest.json','installed_verify.txt','runtime_summary.json','runtime_visual_strip.png']:shutil.copy2(D/name,out/name)
shutil.copy2(p,out/'Enemy_ScarabMounted_before.prefab')
write(out/'rejection.json',dict(observed_at=now(),reason='Builder preview ResetForSpawn resolved original side Head sprite to receiver HeadSprites[0]. Scope audit rejects changing original serialized Sprite PPtr, despite 168/0 and acceptable runtime visuals.',original_sprite=old_line,installed_sprite=new_line,previous_revisions=['runtime_r01','runtime_updeath_r01'],technical='168/0 and 691 frames retained; final evidence requires r02 after source binding restoration',shared_code_changes=False))
patched=current[:new_block.start(2)]+new_block[2].replace(new_line,old_line,1)+current[new_block.end(2):]
with p.open('w',encoding='utf-8',newline='') as f:f.write(patched)
result=unwrap(c.tool('execute_code',dict(action='execute',code='UnityEditor.AssetDatabase.ImportAsset("'+battle+'",UnityEditor.ImportAssetOptions.ForceUpdate);FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("ScarabMounted",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);return new{pass=pass,report=report};')))
write(out/'repair_mcp.json',dict(observed_at=now(),project=project,probe_before=probe,result=result,protocol_history=c.history));assert result['success'] and result['data']['result']['pass']
assert old_line in re.search(pat,p.read_text(encoding='utf-8'),re.M|re.S)[2]
changes=[x for x in manifest['changes'] if sha(ROOT/x['path'])!=x['after']];assert len(changes)==1 and changes[0]['path']==battle
entry=changes[0];manifest.setdefault('repair_history',[]).append(dict(observed_at=now(),revision=out.name,path=battle,before=entry['after'],after=sha(p),reason='Restore original shared Scarab Head Sprite PPtr only. Original receiver expression array and copied animation tracks/events remain unchanged.',original_manifest=out.name+'/installed_manifest.json'))
entry['after']=sha(p);manifest['verification']=result;write(D/'installed_manifest.json',manifest);(D/'installed_verify.txt').write_text(result['data']['result']['report'],encoding='utf-8')
write(out/'repair.json',dict(observed_at=now(),path=battle,renderer_file_id=2508898428600365937,before_sprite=new_line,after_sprite=old_line,before_sha256=sha(out/'Enemy_ScarabMounted_before.prefab'),after_sha256=sha(p),verify=True,new_runtime_revisions=['runtime_r02','runtime_updeath_r02'],source_and_shared_assets_unchanged=True))
write(D/'preplay_version_binding_r02_20261028.json',dict(observed_at=now(),installed_manifest_sha256=sha(D/'installed_manifest.json'),installed_files={x['path']:sha(ROOT/x['path']) for x in manifest['changes']},repair_sha256=sha(out/'repair.json'),selection=read(D/'art_selection.json')))
chain.update(current_stage='Mounted_original_head_restored_pending_r02_Play',last_stage_evidence=(out/'repair.json').relative_to(ROOT).as_posix(),updated_at=now());write(HERE/'conversation_chain.json',chain)
print(json.dumps(dict(repaired=battle,only_sprite_binding=True,verify=True,next=['runtime_r02','runtime_updeath_r02'])))
