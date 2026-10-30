"""Release WinterBoar and prepare one fresh local WinterOgre successor."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import os
import re
import sys
import uuid

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
sys.path.insert(0, str(D))
from checkpoint_20261029 import owner, read, sha, write, now, NAME, TOKEN, LIVE, idle, result, unwrap

OWNER = os.environ['CODEX_THREAD_ID']
chain = owner()
progress = read(H / 'progress.json')
done = next(i for i in progress['items'] if i['name'] == NAME)
assert progress['completed_count'] == 99 and done['status'] == 'completed_pending_user_art_review' and not done['user_approved']
remaining = [i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review', 'user_approved']]
recoverable = [i for i in remaining if i['status'] not in ['not_started', 'blocked']]
selected = min(recoverable or [i for i in remaining if i['status'] != 'blocked'], key=lambda i: i['index'])
NEXT = selected['name']
N = H / NEXT
assert NEXT == 'WinterOgre' and selected['index'] == 111 and selected['status'] == 'not_started'
assert len(remaining) == 9 and sum(i['status'] == 'not_started' for i in remaining) == 8
assert next(i for i in remaining if i['name'] == 'PossessedWarg')['status'] == 'blocked'
existing = sorted(p for p in N.rglob('*') if p.is_file())
assert len(existing) == 8 and all(p.is_relative_to(N / 'reference') for p in existing)
t = next(t for t in read(H / 'local_baseline.json')['targets'] if t['name'] == NEXT)
six = {p: sha(ROOT / p) for k in ['battle', 'source', 'atlas'] for p in [t[k], t[k] + '.meta']}
assert all(six.values()) and all(sha(N / 'reference' / Path(p).name) == v for p, v in six.items())
final = read(D / 'final_validation_20261029.json')
binding = read(D / 'version_binding_final_20261029.json')
scope = read(D / 'scope_incremental_final_20261029.json')
assert (final['passes'], final['failures'], final['actual_png_frames']) == (168, 0, 589) and final['final_revision'] == 'art_r04'
assert len(binding['installed_files']) == 22 and all(sha(ROOT / p) == v for p, v in binding['installed_files'].items())
assert all(sha(ROOT / p) == v for p, v in binding['production_scope_files'].items())
for file, key in [('version_binding_final_20261029.json', 'version_binding_sha256'),
                  ('scope_incremental_final_20261029.json', 'incremental_scope_sha256'),
                  ('visual_review_art_r04_20261029/review.json', 'visual_review_sha256'),
                  ('gif_archive_verification_20261029.json', 'gif_archive_sha256')]:
    assert sha(D / file) == final[key]
assert (scope['baseline_files'], scope['current_files'], len(scope['changes']), scope['added_count'], scope['deleted_count']) == (5525, 5545, 22, 20, 0)
assert not scope['unexpected_incremental'] and not scope['shared_CSharp_drift'] and scope['prefab_semantics']['pass']
assert final['global_archive_count'] == 1594 and not any(r.get('character') == NAME for r in chain.get('completed_handoffs', []))

sys.path.insert(0, str(H))
from mcp_call import Client, URL
c = Client()
project = c.identity()
errors = unwrap(c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'}))
assert errors['data'] == []
c.tool('execute_code', {'action': 'execute', 'code': 'var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);if(t==null)throw new System.Exception("State cache unavailable");var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);if(m==null)throw new System.Exception("Cache refresh unavailable");m.Invoke(null,new object[]{"WinterBoar final handoff snapshot"});return true;'})
state = c.resource('mcpforunity://editor/state')['data']
live = result(c.tool('execute_code', {'action': 'execute', 'code': LIVE}))
idle(live)
assert state['advice']['ready_for_tools'] and not state['tests']['is_running']
assert not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending']
assert not state['assets']['is_updating'] and not state['assets']['external_changes_dirty']

stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token = 'winterboar-to-winterogre-' + stamp + '-' + str(uuid.uuid4())
rel = lambda p: p.relative_to(ROOT).as_posix()
handoff = H / 'conversation_handoffs' / (stamp + '_WinterBoar_completed.md')
assessment = N / ('successor_assessment_' + stamp + '.json')
prompt_path = N / ('successor_prompt_' + stamp + '.txt')
release_path = D / 'handoff_release_20261029.json'
dispatch_path = N / 'prepared_dispatch_20261029.json'
assert all(not p.exists() for p in [handoff, assessment, prompt_path, release_path, dispatch_path])
write(release_path, {'observed_at': now(), 'released_by_thread_id': OWNER, 'current_character': NAME,
                     'next_character': NEXT, 'next_dispatch_token': token, 'transport': URL, 'project': project,
                     'editor_state': state, 'live_probe': live, 'console_errors': [], 'safe_to_handoff': True,
                     'protocol_history': c.history})
write(assessment, {'observed_at': now(), 'completed_count': 99, 'authorized_count': 108,
                   'next_character': NEXT, 'next_index': 111, 'status': 'not_started', 'dispatch_token': token,
                   'target': t, 'protected_six': six, 'reference_matches_live': True,
                   'existing_files': [p.relative_to(N).as_posix() for p in existing],
                   'source_art_reviewed_by_parent': False,
                   'source_instruction': 'Next owner must inspect the original atlas and full source prefab, limbs, weapon/fist/anchors and Giant native animation. Do not copy WinterBoar quadruped anatomy or layout.',
                   'no_generation_staging_install_or_runtime': True,
                   'remaining': [{k: i[k] for k in ['index', 'name', 'status']} for i in remaining],
                   'blocked_preserved': [i for i in remaining if i['status'] == 'blocked']})

summary = f'''# WinterBoar110 完成与 WinterOgre111 唯一串行交接

时间 {now()}。父线程{OWNER}，旧token {TOKEN}。WinterBoar已record为completed_pending_user_art_review、user_approved=false；进度99/108。

## 最终美术与原生行为

最终art_r04，12个非空透明切片、2048² atlas、PPU100。白灰圆胖长毛、赭色斑点、棕背鬃、宽金鼻和双象牙色獠牙；四足，原始无独立尾，不新增尾。耳属于头、背鬃只在躯干。Up纯后脑无脸、外耳背和光滑后跟；Down三表情鼻口居中，原耳眉与脸保留。轴向正背面比原侧面窄、圆身遮挡多数远侧腿，此限制如实记录，不新增器官。原左右侧面保留、无地面阴影，头身/肩髋腿根连接。

2次付费调用：generation/Up和Down均HTTP200，gpt-image-2/medium/1536×1024/n1，raw为RGB PNG且1536×1024。无重试、无结果不明请求；usage是估算，不是实际账单。两个raw均实看并原样保留。Down raw在头和身体重复背鬃，本地修额顶保留原脸/耳眉，身体保留唯一背鬃。r01角折额顶/裁耳眉、r02白眉缺口/品红边/露远腿根否决保留；r03恢复原眉与内收根部，安装前数检发现28个缩小后品红染边，未安装。r04保持alpha/形状，以最近不污染描边RGB修复所有检测到的997个边缘染色像素（含低alpha）。local_raster_r01..r04各manifest和offline_art_r01..r03保留。不把本地修绘冒充生成原图。

只安装一次，installed_manifest.json SHA {final['manifest_sha256']}。Builder/Verify及资源收集覆盖通过。22条prePlay生产哈希在两轮后保持。源atlas/source prefab/metas/battle meta不改；原Ready/Attack/Death/Walk全部.5s、60FPS，Ready/Walk loop。Attack原SetHead1@0、Event("Attack")@.333333343、SetHead0@.5，Death SetHead2@0保留；原float27/27/32/30、PPtr0，原侧面曲线/事件/时长/loop保留。Battle原组件语义PASS，GUID/root/HP/锚点/碰撞/移动战斗/接收器保护。共享C#、其他角色、配置表、ConfigJson/Gen与无声版本无本轮增量漂移。

## 真实运行、实际审阅与封存

runtime_r01：84PASS/0FAIL、295张真实PNG，records SHA {final['runtime'][0]['records_sha256']}。
runtime_updeath_r01：84PASS/0FAIL、294张真实PNG，records SHA {final['runtime'][1]['records_sha256']}；第二轮指定Up死亡。共168/0、589原PNG，两个returned都是clean Boot。

实际查看最终离线组合及Up Body局部，两轮four_directions和runtime strip、10张时序/步态/愤怒板（256采样位/229不同真实PNG）、8张768完整原PNG、12GIF各5编码帧共60帧、另4张未裁切GIF整帧。覆盖四向/连续转向、Up/Down攻击、受击白闪恢复、Down/Up全身死亡旋转缩小淡出、自动回收/同实例Down正常复用、暂停冻结与恢复、1x/2x/3x推进。淡出时既有逐renderer alpha可见重叠分件透叠。没有实时播放或逐帧全审，589帧全部留盘并哈希。内部技术视觉通过、用户美术待验收。

AllGIF由1582变1594，本角色12条均当前审核版本，源/归档SHA一致。最终证据WinterBoar/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r04_20261029/review.json、gif_archive_verification_20261029.json、unity_release_final_r04_20261029.json、runtime_summary.json、record_note_utf8.txt。finalize脚本已audit和seal成功，不再重跑。

## 增量范围与Unity释放

当前磁盘完整路径并集5525→5545文件、22变化/20新增/0删除、unexpected0。仅WinterBoar battle/Directions及未改ReporterEditor自动Play时间戳单列。其余5保护、共享C#、其他角色和配置无增量漂移，本角色原组件语义PASS。旧全局291unexpected/6其他角色语义失败保留且未重审，不称全局PASS。基线files是dict路径到SHA，不是WinterBear的列表。

Unity2022.3.62f3c1/8088动态选MyTowerGame并核E:/MyTowerGame；最终refresh/compile/error0。交接前再核：单一clean Boot、非Play，tests/review/balance/recording/manual/compile/reload/update全空闲、failed=false、ready=true、external_changes_dirty=false。{rel(release_path)}。不清日志、无桌面控制、无Git改写/构建/部署/子代理/长期memory写入。

## 下一唯一角色

重读实时items，剩余9：PossessedWarg79旧blocked及结果不明Down付费请求保留、8项not_started，无可恢复已开始项。选最低index的WinterOgre111。父只核其reference8文件及六保护匹配，未审源图、未生成/暂存/安装/运行。下一owner独立查看{t['atlas']}、{t['source']}、{t['battle']}和{t['controller']}，核真实肢体与Weapon/Fist/Anchor及原Giant契约，不能沿用野猪四足参数。

新token {token}；assessment {rel(assessment)}；完整prompt {rel(prompt_path)}。链先handoff_ready，现场list_projects，再唯一fresh local create_thread，不fork、不子代理、不计时器、不改模型/推理。成功后登记新active owner为父最后工作区写入，之后父只读。PossessedWarg历史不明请求与阻断保留。
'''
handoff.write_text(summary, encoding='utf-8')

# Preserve the complete operational instructions, replacing only current facts.
prompt = (H / 'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8').split('\n\n', 1)[1]
prompt = prompt.replace('WinterBoar', 'WinterOgre').replace('index110', 'index111').replace('index 110', 'index 111')
prompt = prompt.replace('WinterOgre110', 'WinterOgre111')
prompt = prompt.replace('01a18593-9b41-7262-bc3d-c7df48244120', OWNER).replace(TOKEN, token)
prompt = re.sub(r'6\. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/[^\n]+',
                lambda _: '6. E:/MyTowerGame/' + rel(handoff) + '。', prompt)
prompt = re.sub(r'7\. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/successor_assessment_[^\n]+',
                lambda _: '7. E:/MyTowerGame/' + rel(assessment) + '。', prompt)
start = prompt.index('实时98/108。')
end = prompt.index('\n\n逐阶段推进：', start)
prompt = prompt[:start] + f'''实时99/108。WinterBoar110已record，art_r04，completed_pending_user_art_review、user_approved=false。剩余9项：PossessedWarg79旧blocked和结果不明Down付费请求保留、8项not_started；无可恢复已开始项，选最低index的WinterOgre111。不能盲用progress.current。108是授权数量，终项Zombie118。WinterOgre仅reference8文件；assessment/prompt/dispatch/creation为调度证据，无生成/暂存/安装/运行。

WinterOgre生产路径：
- battle：{t['battle']}
- source：{t['source']}
- atlas：{t['atlas']}
- controller：{t['controller']}
父只核六保护与reference匹配，未审新源图。必须实际查看完整原atlas/源prefab，核层级、renderer、真实肢体、武器/拳头/WeaponAnchor及原float/PPtr/事件/时长/loop与移动/战斗/回收/同实例复用，独立制定WinterOgre正背面，不套野猪四足或其他角色参数。原Giant动画和武器/攻击契约必须先实读，不能猜用Boar。开工前以当前磁盘包含既有用户修改建立Assets/Packages/ProjectSettings/Luban完整SHA基线及六保护，不用Git HEAD。''' + prompt[end:]
start = prompt.index('前任WinterBear最终证据')
end = prompt.index('\n\n每次实际查看', start)
prompt = prompt[:start] + '''前任WinterBoar最终证据WinterBoar/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r04_20261029/review.json、gif_archive_verification_20261029.json。最终art_r04/12非空透明切片/四足无独立尾、22条prePlay路径不变；295+294=589真实PNG、168/0。r01角折额顶/裁耳眉、r02眉缺口/品红边/露远腿根否决保留；r03预检发现28个缩小后染边，未安装；r04保持alpha/形状，用最近不污染描边RGB修复997个边缘染色像素含低alpha。Down本地去重复额鬃、保留原耳眉/脸，原raw不变。2次付费HTTP200，无重试/结果不明，usage估算非账单。实际审10板256采样位/229不同PNG、8原PNG、12GIF各5编码帧及4未裁切整帧；非实时播放/逐帧全审，轴向窄且圆身遮远腿，淡出既有逐renderer透明透叠如实保留。AllGIF1594、本角色12当前审核GIF，源归档SHA匹配。5525→5545文件、路径并集22变化/20新增、unexpected0，本角色语义PASS、其余5保护/共享C#无漂移，Reporter自动时间戳单列；旧global291unexpected/6其他角色语义失败保留未重审，不称全局PASS。基线files为dict路径到SHA，不能套WinterBear列表格式。不运行前任prepare/stage/install/finalize或覆盖封存证据。''' + prompt[end:]
assert TOKEN not in prompt and '实时98/' not in prompt and 'WinterBear109' not in prompt
assert token in prompt and t['atlas'] in prompt and 'index111' in prompt
prompt_path.write_text(prompt, encoding='utf-8')
(H / 'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 WinterOgre(index 111)\n\n' + prompt, encoding='utf-8')

live_text = f'''2026-10-29 WinterBoar110已record，99/108，completed_pending_user_art_review、user_approved=false。最终art_r04/12非空透明切片/四足无独立尾，installed_manifest.json；r01..r03否决保留，r04仅修染边RGB保留alpha/形状，Down重复额鬃本地修整，2次付费HTTP200且无重试/结果不明，raw保留。两轮295+294=589真实PNG、168PASS/0FAIL；实际审最终离线组合/Up Body、两轮四向/strip、10板256采样位/229不同PNG、8原PNG、12GIF各5编码帧与4未裁切整帧，非实时播放/逐帧全审。轴向窄及圆身遮远腿、淡出既有分件透叠如实记录。AllGIF1594、本角色12当前审核GIF、源归档SHA一致。5525→5545文件、路径并集22变化20新增unexpected0、本角色语义PASS，其余5保护/共享C#无漂移，Reporter自动时间戳单列；旧global291unexpected/6其他角色语义失败未重审。Unity8088正确身份、最终编译/error0，单一clean Boot/非Play/全空闲/failed=false/ready=true/external_changes_dirty=false。最终WinterBoar/final_validation_20261029.json及绑定/范围/视觉/归档。交接{rel(handoff)}。下一唯一WinterOgre111 not_started、reference8文件；token={token}。剩余9含PossessedWarg旧blocked/uncertain与8项not_started。'''
for path, begin, end in [(H.parent / 'README.md', '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->'),
                          (H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    content = path.read_text(encoding='utf-8-sig')
    pattern = re.escape(begin) + r'.*?' + re.escape(end)
    assert len(re.findall(pattern, content, re.S)) == 1
    content = re.sub(pattern, lambda _: begin + '\n' + live_text + '\n' + end, content, flags=re.S)
    if path.name == 'README.md':
        content, count = re.subn(r'\d{4}-\d{2}-\d{2} 本轮当前清单为 \d+ 个文件', '2026-10-29 本轮当前清单为 1594 个文件', content)
        assert count == 1
    path.write_text(content, encoding='utf-8')

done['handoff_file'] = handoff.relative_to(H).as_posix()
progress.update(current=NEXT, updated_at=now())
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
dispatch = {'prepared_at': now(), 'created': False, 'parent_thread_id': OWNER, 'character': NEXT,
            'character_index': 111, 'dispatch_token': token, 'project_root': 'E:/MyTowerGame',
            'project_id': None, 'project_live_confirmed': False, 'project_association_confirmed': False,
            'handoff_file': rel(handoff), 'handoff_sha256': sha(handoff), 'assessment_file': rel(assessment),
            'assessment_sha256': sha(assessment), 'unity_release_file': rel(release_path),
            'unity_release_sha256': sha(release_path), 'prompt_file': rel(prompt_path),
            'prompt_sha256': sha(prompt_path), 'next_task_file': rel(H / 'NEXT_ENEMY_TASK.md'),
            'next_task_sha256': sha(H / 'NEXT_ENEMY_TASK.md'), 'progress_sha256': sha(H / 'progress.json'),
            'response_file': rel(N / 'successor_creation_response_20261029.json')}
write(dispatch_path, dispatch)
chain.setdefault('completed_handoffs', []).append({'character': NAME, 'status': done['status'],
    'current_stage': 'recorded_pending_user_art_review', 'closed_at': now(), 'owner_thread_id': OWNER,
    'dispatch_token': TOKEN, 'handoff_file': rel(handoff), 'final_evidence': rel(D / 'final_validation_20261029.json')})
chain.update(state='handoff_ready', parent_thread_id=OWNER, current_character=NEXT, dispatch_token=token,
             character_status_at_handoff='not_started', completed_count_snapshot=99,
             previous_handoff_file=chain.get('last_handoff_file'), last_handoff_file=rel(handoff),
             handoff_sha256=sha(handoff), successor_assessment=rel(assessment),
             progress_sha256_at_handoff=sha(H / 'progress.json'), unity_release_file=rel(release_path),
             dispatch_ready_for=NEXT, successor_created=False, current_stage='handoff_ready_pending_single_successor_creation',
             resume_character=NEXT, resume_stage='Verify owner/token; inspect WinterOgre source and native Giant/weapon motion; establish baseline',
             handoff_ready_at=now(), updated_at=now())
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'state': 'handoff_ready', 'character': NEXT, 'dispatch_token': token,
                  'dispatch_file': rel(dispatch_path), 'prompt_file': rel(prompt_path),
                  'handoff_file': rel(handoff), 'safe_to_handoff': True}, ensure_ascii=False))
