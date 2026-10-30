from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
REV=Path(__file__).resolve().parent;CHAR=REV.parent;HERE=CHAR.parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
before=json.loads((REV/'scope_before.json').read_text())
after={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changes=[{'path':p,'before':before.get(p),'after':after.get(p)} for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
allowed={f'Assets/_UIAssets/Monsters/Parasites/IceParasite/Directions/Animations/{a}_Directions.anim' for a in ['Ready','Walk']}
side_effect='Assets/StreamingAssets/build_info'
unexpected=[x for x in changes if x['path'] not in allowed|{side_effect}]
assert not unexpected,unexpected
if any(x['path']==side_effect for x in changes):
    assert sha(ROOT/'Assets/Reporter/Editor/ReporterEditor.cs')==before['Assets/Reporter/Editor/ReporterEditor.cs']
    assert (ROOT/side_effect).read_text().startswith('Build from ')
c=Client();project=c.identity()
code='''var t=typeof(MCPForUnity.Editor.Tools.RefreshUnity).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"IceParasite_final_probe"});return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compilationFailed=UnityEditor.EditorUtility.scriptCompilationFailed,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'''
live=c.tool('execute_code',{'action':'execute','code':code})
v=live.get('structuredContent') or json.loads(live['content'][0]['text'])
assert v.get('success') and not any(v['data']['result'].values()),v
state=c.resource('mcpforunity://editor/state')
s=state['data'];assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools'],state
console=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
logs=console.get('structuredContent') or json.loads(console['content'][0]['text'])
assert logs.get('success') and not logs.get('data'),logs
summary=json.loads((CHAR/'runtime_summary.json').read_text())
assert summary['passes']==168 and summary['failures']==0
assert [r['revision'] for r in summary['runtime']]==['runtime_r02','runtime_updeath_r02']
for r in summary['runtime']:
    path=CHAR/r['revision'];assert sha(path/'actual_frames.jsonl')==r['records_sha256']
    checks=(path/'actual_runtime_checks.txt').read_text();assert checks.count('PASS ')==84 and 'FAIL ' not in checks
reviewed=['reference/source_prefab_offline.png','runtime_r02/four_directions.png','runtime_visual_strip.png','repair_pool_rotation_r02/reuse_turn_board.png','repair_pool_rotation_r02/walk_pause_speed_board.png','repair_pool_rotation_r02/attack_death_board.png']
review={'name':'IceParasite','revision':'repair_pool_rotation_r02','visual_reviewed':True,'visual_passed':True,'visual_note':(REV/'visual_note_utf8.txt').read_text(encoding='utf-8').strip(),'images_viewed':reviewed,'image_count':6,'review_method':'Actual-frame summary boards with source frame IDs/hashes; no claim of playing GIFs in the viewer. Current turn prioritizes strips within the six-image limit.','runtime':summary,'previous_block':'../blocked_visual_review.json','production_changes':changes,'unexpected':unexpected,'project':project,'state':state,'console':logs,'protocol_history':c.history,'observed_at':datetime.now(timezone.utc).isoformat()}
(REV/'final_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
(REV/'scope_after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
print(json.dumps({'pass':True,'changes':changes,'unexpected':unexpected,'runtime':summary['runtime'],'actual_frames':summary['actual_frames'],'images':6,'editor_ready':True,'errors':0},ensure_ascii=False))
