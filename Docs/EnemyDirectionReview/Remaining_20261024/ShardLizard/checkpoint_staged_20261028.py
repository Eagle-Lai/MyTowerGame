"""Record the actually viewed r02 staging gate and current, guarded preinstall state."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys, re
from PIL import Image

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from mcp_call import Client

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None

chain = read(HERE/'conversation_chain.json')
assert chain['state'] == 'active' and chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == 'ShardLizard'
assert chain['dispatch_token'] == 'scarabmounted-to-shardlizard-e066b2f9cbb54a5ca5b215b2e08ea8d2'
assert not (D/'installed_manifest.json').exists()
output = D/'staged_visual_gate_20261028.json'
assert not output.exists(), 'Preserve existing visual gate'
baseline = read(D/'incremental_before_recovery_20261028_085812.json')
baseline['files'] = {p:s.upper() for p,s in baseline['files'].items()}
current = {p.relative_to(ROOT).as_posix(): sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changes = [{'path': p, 'before': baseline['files'].get(p), 'after': current.get(p)} for p in sorted(set(current)|set(baseline['files'])) if current.get(p) != baseline['files'].get(p)]
side_effects = [dict(c, origin='Unmodified ReporterEditor.cs InitializeOnLoad BuildInfo.Update writes timestamp after startup/compilation') for c in changes if c['path']=='Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs']==baseline['files']['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+', (ROOT/c['path']).read_text(encoding='utf-8'))]
unexpected = [c for c in changes if c['path'] not in {s['path'] for s in side_effects}]
assert not unexpected, 'Production drift before installation: '+str(unexpected[:12])
protected = baseline['protected_shardlizard']
assert all(sha(ROOT/p) == s.upper() for p,s in protected.items())
client = Client()
project = client.identity()
errors = client.tool('read_console', {'action':'get','types':['error'],'count':'50','format':'json'})
state = client.resource('mcpforunity://editor/state')
probe = client.tool('execute_code', {'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'})
value = probe.get('structuredContent') or json.loads(probe['content'][0]['text'])
assert value['success'], value
observed = value['data']['result']
assert not any(observed[k] for k in ['playing','compiling','failed','balance','review','manual','dirty']), observed
assert state['data']['advice']['ready_for_tools']
now = datetime.now(timezone(timedelta(hours=8))).isoformat()
paths = ['generation/Up/revision_02/raw.png','generation/Down/raw.png','local_raster_revision_01/Up.png','local_raster_revision_01/Down.png','local_raster_revision_02/Up.png','local_raster_revision_02/Down.png','art_selection.json','layout_adjustments.json','processing.json','parts_clean.png','offline_rig_proof.png']
paths += [p.relative_to(D).as_posix() for p in (D/'staged_art').glob('*') if p.is_file()]
art = Image.open(D/'staged_art/ShardLizard_Directions.png').convert('RGBA')
pixels = list(art.getdata())
alpha = {'size': art.size, 'transparent_pixels': sum(p[3]==0 for p in pixels), 'opaque_pixels': sum(p[3]==255 for p in pixels), 'opaque_magenta_pixels': sum(p[3]>0 and p[0]>200 and p[2]>200 and p[1]<80 for p in pixels)}
assert alpha['transparent_pixels'] > 0 and alpha['opaque_magenta_pixels'] == 0
review = dict(observed_at=now, status='staged_visual_gate_passed_pending_install', revision='local_raster_revision_02', user_approved=False,
    actually_viewed=['offline_rig_proof.png','parts_clean.png'],
    upstream_review='Both paid originals and local r01/r02 were actually viewed earlier in this same continuation; retained records are not user approval.',
    observations=['Down explicit rectangles exclude the tail from HeadDead and retain the whole tail tip. Three facial states remain distinct.',
        'Up head is axial and faceless. Front-facing toe ink is absent; four short broad feet and a single trailing-down segmented tail are visible.',
        'One broad flat-topped golden dorsal shard remains on the torso. Down forehead carries two small chips; r02 forehead is simple with a softened patch boundary.',
        'Neck overlaps, four limb roots and both tail roots meet the torso in the static staged proof. Runtime phase/attack/death checks remain required.',
        'Olive/ochre/cream colors and dark outlines retained. No magenta fringe, ground shadow or invented ears/rider visible in the staged proof.'],
    rejected_intermediate='local_raster_revision_01 retained: residual Up toe lines and hard Down forehead patches. Initial generic staged layout was rejected and restaged with explicit rectangles and dedicated pivots.',
    evidence_sha256={p:sha(D/p) for p in paths}, alpha=alpha, protected_six=protected,
    production_scope={'baseline':'incremental_before_recovery_20261028_085812.json','baseline_files':len(baseline['files']),'changes':changes,'unexpected':unexpected,'automatic_editor_side_effects':side_effects},
    project=project, state=state, errors=errors, probe=probe, protocol_history=client.history)
write(output, review)
progress = read(HERE/'progress.json')
item = next(i for i in progress['items'] if i['name']=='ShardLizard')
item.update(status='staged_pending_visual_check', staged_visual_reviewed=True, staged_visual_gate=output.relative_to(HERE).as_posix(), selected_art_revision='local_raster_revision_02', user_approved=False)
progress.update(current='ShardLizard', updated_at=now)
write(HERE/'progress.json', progress)
live = '2026-10-28 ShardLizard(index94)，79/108，原owner/token不变、chain=active。Up revision_02与Down正式生成均已HTTP200且原图已审；旧503原件保留，不重发。local_raster_revision_01保留为否决中间稿，当前选择local_raster_revision_02：去掉Up正面趾线、Down重复大额晶片；Down显式切片修正死亡头/尾尖串入。已两次stage并实际审阅最新offline_rig_proof与parts_clean，专属尾根pivot和四肢/颈部静态接缝通过，待Unity动态检查。六保护指纹未变；5138文件基线仅ReporterEditor启动/编译自动时间戳变化，无其他增量。8082独立HTTP服务与MyTowerGame桥接已恢复；通过现有mcp_call.py动态核对E:/MyTowerGame/Unity2022.3.62f3c1，Boot、非Play、非dirty、无编译/review/manual占用。即将仅安装ShardLizard、Verify、两轮真实Play各84项；尚未install/Play/record，用户未批准美术。证据ShardLizard/staged_visual_gate_20261028.json。'
prompt = HERE/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
text = prompt.read_text(encoding='utf-8')
start = '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->'
end = '<!-- ENEMY_SERIAL_LIVE_STATE_END -->'
head, tail = text.split(start,1)
_, rest = tail.split(end,1)
prompt.write_text(head+start+'\n'+live+'\n'+end+rest, encoding='utf-8')
(HERE/'NEXT_ENEMY_TASK.md').write_text('# 当前唯一敌人任务：ShardLizard（暂存已审，待安装与真实运行）\n\n'+live+'\n\n继续使用原执行prompt及CONTINUATION_PROTOCOL_20261026.md，owner_thread_id=01a178a8-fc5a-77b0-9881-0a0b40872da8，dispatch_token='+chain['dispatch_token']+'。优先恢复当前阶段，不prepare、不重发图片、不删除既有记录。禁止并发角色/子代理、配置表/ConfigJson/Gen/声音改动。安装前再次核对指纹和Unity占用，character_step.py install-and-review ShardLizard；之后实际媒体审阅，必要返修并使用新运行revision；最终168 PASS/0 FAIL与UTF-8真实观察匹配才record/GIF归档。完成后安全交回Unity、新建时间戳交接，按实时队列及协议只创建一个新本地后继。历史交接不覆盖。\n',encoding='utf-8')
chain.update(character_status_at_handoff='staged_pending_visual_check', resume_stage='reviewed local_raster_revision_02 staged; install/Verify/runtime pending', current_stage='staged_visual_gate_passed_pending_install', last_stage_evidence=output.relative_to(ROOT).as_posix(), updated_at=now)
write(HERE/'conversation_chain.json', chain)
print(json.dumps({'owner':chain['owner_thread_id'],'gate':str(output),'protected':len(protected),'production_changes':len(changes),'alpha':alpha,'editor':observed}, ensure_ascii=False))
