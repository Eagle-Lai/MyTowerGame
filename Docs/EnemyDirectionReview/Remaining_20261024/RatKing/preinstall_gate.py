"""Immutable RatKing installation-time snapshot after actual offline review."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import os,json,hashlib,sys
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2];sys.path.insert(0,str(H))
from mcp_call import Client
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
chain=read(H/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='RatKing' and chain['dispatch_token']=='rat-to-ratking-5222dbfeb5d146d7ad666975e4e8d90e'
assert not (D/'installed_manifest.json').exists()
output=D/'incremental_before_20261026.json';assert not output.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
t=next(t for t in read(H/'local_baseline.json')['targets'] if t['name']=='RatKing');baseline=read(H/'production_fingerprints_before.json')
protected=[t[k]+s for k in ['battle','source','atlas'] for s in ['', '.meta']]
assert all(sha(ROOT/p)==baseline[p] for p in protected)
assert not (ROOT/t['art_dir']).exists()
def unwrap(r):return r.get('structuredContent') or json.loads(r['content'][0]['text'])
c=Client();project=c.identity();errors=c.tool('read_console',dict(action='get',types=['error'],count='50',format='json'));state=c.resource('mcpforunity://editor/state')
probe=unwrap(c.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'}))['data']['result']
assert not any(probe.values()),probe
s=state['data'];assert s['advice']['ready_for_tools'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating']
files={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
write(output,dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),files=files,protected_ratking={p:files[p] for p in protected},chain_owner=chain['owner_thread_id'],dispatch_token=chain['dispatch_token']))
write(D/'preinstall_identity_20261026.json',dict(project=project,state=state,probe=probe,errors=errors,protocol_history=c.history))
write(D/'offline_review_20261026.json',dict(stage='offline_reviewed_pending_Unity',raster_revision='raster_revision_04',raw_sources_unchanged={k:sha(D/'generation'/k/'raw.png') for k in ['Up','Down']},final_staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},observations_zh='已查看原始图集、完整源参考、上下原始生成图、离线整身与实际切片。金冠只在头上，单耳环按前后投影换侧。Up 后脑无眼鼻牙和内耳色块，金冠背面去掉正面黑宝石；背部原画重复腿已剪除，后足是无正面趾沟的连续后跟，四只骨架足仍保留，远前足由背身遮挡。Down 琥珀眼、赭色颊斑、四只短足和尾根相接，身体没有第二个头。尾巴均从后臀伸出。颈部帽由头片遮住，无地面阴影；透明切片保留银环孔、尖牙和深色器官，边缘局部去底色，无明显残留洋红背景。最终待真实运行审阅；未获用户批准。',user_approved=False))
print(json.dumps(dict(snapshot_files=len(files),protected_match=len(protected),project=project,probe=probe),ensure_ascii=False))
