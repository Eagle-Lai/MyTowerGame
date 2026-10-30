"""Release WildRooster and prepare the one authorized fresh local successor."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import ast, hashlib, json, os, re, sys, uuid

D=Path(__file__).resolve().parent; H=D.parent; ROOT=H.parents[2]
NAME='WildRooster'; NEXT='WinterBear'; N=H/NEXT
OWNER='01a18560-5f4b-7b42-a2cf-f926c68a77ae'
OLD='wildgoat-to-wildrooster-20261029_095556-9aeda72a-08aa-4bfe-aca0-1b03c0381c5e'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now=lambda:datetime.now(timezone(timedelta(hours=8)))
rel=lambda p:p.relative_to(ROOT).as_posix()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
assert os.environ['CODEX_THREAD_ID']==OWNER
chain=read(H/'conversation_chain.json');progress=read(H/'progress.json')
assert chain['state']=='active' and chain['owner_thread_id']==OWNER and chain['dispatch_token']==OLD and chain['current_character']==NAME
done=next(r for r in progress['items'] if r['name']==NAME)
assert progress['completed_count']==97 and done['status']=='completed_pending_user_art_review' and not done['user_approved']
remaining=[r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[r for r in remaining if r['status'] not in ['not_started','blocked']]
selected=min(recoverable or [r for r in remaining if r['status']!='blocked'],key=lambda r:r['index'])
assert selected['name']==NEXT and selected['index']==109 and selected['status']=='not_started'
assert len(remaining)==11 and next(r for r in remaining if r['name']=='PossessedWarg')['status']=='blocked'
existing=sorted(p for p in N.rglob('*') if p.is_file())
assert len(existing)==8 and all(p.is_relative_to(N/'reference') for p in existing)
t=next(r for r in read(H/'local_baseline.json')['targets'] if r['name']==NEXT)
six={p:sha(ROOT/p) for k in ['battle','source','atlas'] for p in [t[k],t[k]+'.meta']}
assert all(six.values()) and all(sha(N/'reference'/Path(p).name)==v for p,v in six.items())
final=read(D/'final_validation_20261029.json');binding=read(D/'version_binding_final_20261029.json');scope=read(D/'scope_incremental_final_20261029.json')
assert (final['passes'],final['failures'],final['actual_png_frames'])==(168,0,600) and final['final_revision']=='art_r03'
assert all(sha(ROOT/p)==v for p,v in binding['installed_files'].items()) and len(binding['installed_files'])==22
assert all(sha(ROOT/p)==v for p,v in binding['production_scope_files'].items())
for file,key in [('version_binding_final_20261029.json','version_binding_sha256'),('scope_incremental_final_20261029.json','incremental_scope_sha256'),('visual_review_art_r03_20261029/review.json','visual_review_sha256'),('gif_archive_verification_20261029.json','gif_archive_sha256')]:
    assert sha(D/file)==final[key]
assert (scope['baseline_files'],scope['current_files'],len(scope['changes']),scope['added_count'],scope['deleted_count'])==(5485,5505,22,20,0)
assert not scope['unexpected_incremental'] and not scope['shared_CSharp_drift'] and scope['prefab_semantics']['pass']
assert final['global_archive_count']==1570
assert not any(r.get('character')==NAME for r in chain.get('completed_handoffs',[]))

sys.path.insert(0,str(H));from mcp_call import Client,URL
c=Client();project=c.identity()
tree=ast.parse((D/'verify_unity_final_r03_20261029.py').read_text(encoding='utf-8'))
probe_code=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='probe' for a in n.targets))
cache_call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='tool' and len(n.args)>1 and isinstance(n.args[1],ast.Dict) and 'ForceUpdate' in ast.unparse(n.args[1]))
c.tool('execute_code',ast.literal_eval(cache_call.args[1]))
state=c.resource('mcpforunity://editor/state')['data']
response=c.tool('execute_code',{'action':'execute','code':probe_code})
live=unwrap(response)['data']['result'];live=json.loads(live) if isinstance(live,str) else live
errors=unwrap(c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'}))
assert URL=='http://127.0.0.1:8088/mcp' and errors['data']==[]
assert state['advice']['ready_for_tools'] and not state['tests']['is_running']
assert not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending']
assert not state['assets']['is_updating'] and not state['assets']['external_changes_dirty']
assert live['scene']=='Assets/Scenes/Boot.unity' and live['sceneCount']==1
assert all(live[k] is False for k in ['playing','compiling','failed','updating','sceneDirty','balance','recording','review','manual'])
stamp=now().strftime('%Y%m%d_%H%M%S');token='wildrooster-to-winterbear-'+stamp+'-'+str(uuid.uuid4())
handoff=H/'conversation_handoffs'/(stamp+'_WildRooster_completed.md')
assessment=N/('successor_assessment_'+stamp+'.json');prompt_path=N/('successor_prompt_'+stamp+'.txt')
release_path=D/'handoff_release_20261029.json';dispatch_path=N/'prepared_dispatch_20261029.json'
assert all(not p.exists() for p in [handoff,assessment,prompt_path,release_path,dispatch_path])
write(release_path,{'observed_at':now().isoformat(),'released_by_thread_id':OWNER,'current_character':NAME,'next_character':NEXT,'next_dispatch_token':token,
                    'transport':URL,'project':project,'editor_state':state,'live_probe':live,'console_errors':[],'safe_to_handoff':True,'protocol_history':c.history})
write(assessment,{'observed_at':now().isoformat(),'completed_count':97,'authorized_count':108,'next_character':NEXT,'next_index':109,
                  'status':'not_started','dispatch_token':token,'target':t,'protected_six':six,'reference_matches_live':True,
                  'existing_files':[p.relative_to(N).as_posix() for p in existing],
                  'source_art_reviewed_by_parent':False,'source_instruction':'Next owner must inspect original atlas, full source prefab, actual limb/tail structure and native Bear animation before designing this character.',
                  'no_generation_staging_install_or_runtime':True,'remaining':[{k:r[k] for k in ['index','name','status']} for r in remaining],
                  'blocked_preserved':[r for r in remaining if r['status']=='blocked']})
summary=f'''# WildRooster108 完成与 WinterBear109 唯一串行交接

时间 {now().isoformat()}。父线程 {OWNER}；旧token {OLD}。WildRooster已record，completed_pending_user_art_review、user_approved=false；进度97/108。

## 最终实现与修整历史

最终art_r03，14个透明切片。保留金赭公鸡、高金冠、奶油长脸/后颈、钩形金喙、双瓣垂肉、白根金羽双翅、双爪与Body一体尾羽。原源prefab无独立Tail renderer；最终每方向双翼双腿、无Tail节点，1x1透明Tail仅切片兼容。离线r01浮翅、重复领口和高位尾簇被否决；r02帽盖接缝/矩形尾根被否决；完整历史保留。r03局部RGBA清理混色，Up三羽尾簇融入下臀，Down尾羽被躯干遮蔽并移除重复领口/突起，翅内收、头身重叠/腿根内收。无侧图冒充正背面。两方向各一次HTTP200，原PNG1536x1024/RGB均实际查看、SHA未改，无重试或追加付费；usage为估算而非实际账单。

最终仅安装一次：WildRooster/installed_manifest.json，SHA {final['manifest_sha256']}，Builder/Verify通过。22条prePlay生产指纹不变。原源图/源prefab与GUID保护，原侧面、72条float绑定与攻击/SetHead事件、时长/loop继承。无共享C#改动，不重跑prepare/stage/install覆盖本次最终资源。

## 运行及实际视觉审阅

runtime_r01：84/0，293真实PNG，records SHA {final['runtime'][0]['records_sha256']}。
runtime_updeath_r01：84/0，307真实PNG，records SHA {final['runtime'][1]['records_sha256']}；第二轮Up死亡。合计168PASS/0FAIL、600真实PNG，两个returned均为clean Boot。

实际审过最终离线rig和Body局部、两轮四向图、runtime strip、10张时序/步态/愤怒板，256采样位/226张不同真实PNG；6张完整768像素原PNG；12GIF每个5编码帧共60帧；另4张未裁切完整编码GIF帧。头颈/肩/腿根相连、Up纯后脑无脸及同图三表情、Down三表情、双腿步态、攻击、受击白闪恢复、Down/Up死亡旋转缩小淡出、自动回收/同实例正常Down复用、暂停/恢复及1x/2x/3x推进均有记录与抽样。通用时序板有冠尖裁切，原PNG和未裁切GIF整帧确认实际完整且与HP有间距。无地面阴影。抽样不等于实时播放或逐帧全审；600原PNG均保留哈希。内部技术视觉通过，不代替用户美术批准。

AllGIF1570，本角色12个全部当前审核版本，源/归档SHA一致；归档前1558。最终证据WildRooster/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r03_20261029/review.json、gif_archive_verification_20261029.json、unity_release_final_r03_20261029.json、runtime_summary.json、record_note_utf8.txt。

## 范围与Unity释放

基于当前磁盘的完整路径并集5485→5505文件、22变化、20新增/0删除、unexpected0。仅本角色battle/Directions，及未改ReporterEditor自动Play时间戳单列。其余5保护、共享C#、其他角色、配置和无声版本无增量漂移；本角色原组件语义PASS。历史全局291unexpected/6其他角色语义失败保留，未全局重审，不称全局PASS。证据脚本曾有一个字符串替换语法错误，修正后audit/seal成功；未写入Assets或影响运行结果。

正确Unity2022.3.62f3c1经8088动态选择实例并核E:/MyTowerGame；最终refresh/compile通过、error0。交接前再次核身份及状态：单一clean Boot、非Play，tests/review/balance/recording/manual/compile/reload/update全部空闲，failed=false、ready=true、external_changes_dirty=false。释放证据{rel(release_path)}。未清日志或操作桌面。

## 下一唯一角色

重读实时items，剩余11项含PossessedWarg旧blocked/结果不明Down请求与10项not_started，无可恢复已开始非blocked项。按index选择WinterBear109。父仅核其8个reference与六保护匹配，未看源图、未做新角色生产/生成/暂存/安装/运行。后继必须独立查看{t['atlas']}、{t['source']}、{t['battle']}及{t['controller']}，按真实解剖制定方向，不能套公鸡参数。

新token {token}；assessment {rel(assessment)}；完整prompt {rel(prompt_path)}。chain先handoff_ready，现场list_projects确认E:/MyTowerGame，再唯一fresh local create_thread，无fork/子代理/计时器/模型覆盖。创建明确成功后登记新active owner为父最后工作区写入；此后父只读。PossessedWarg阻断与不明收费证据原样保留。
'''
handoff.write_text(summary,encoding='utf-8')
prompt=f'''在E:/MyTowerGame继续敌人四方向串行续作，唯一角色WinterBear(index109)。这是用户2026-10-26明确授权的“完成一个角色→总结/更新prompt→唯一全新local后继”循环。

唯一dispatch_token：{token}
父线程：{OWNER}

先完整读取当前磁盘：
1. E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
3. Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
4. 同目录CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json。
5. 同目录standing_network_recovery_authorization_20261028.json、TreasureChest/standing_recovery_application_20261028.json，核对有界恢复授权，保留收费和结果不明证据。
6. E:/MyTowerGame/{rel(handoff)}。
7. E:/MyTowerGame/{rel(assessment)}。
8. WinterBear/reference原图、源结构与prefab；按需读取本角色流水线及共享实现直接调用、依赖、生命周期。

只有chain.state=active、owner_thread_id等于本新聊天、current_character=WinterBear、dispatch_token匹配才能操作生产、Unity和付费请求。父handoff_ready期间只读等登记，不抢锁、不修改链、不创建别的任务。父登记后停止全部工作区写入。先按实时文件恢复已有阶段，禁止盲重跑prepare/生成/安装。一次只做WinterBear，不并发、不子代理、不fork、不计时器、不覆盖模型/推理设置。

实时97/108。WildRooster108已record，art_r03，completed_pending_user_art_review、user_approved=false。剩余11项：PossessedWarg79旧blocked和结果不明Down付费请求保留、10项not_started；无可恢复已开始项，选择最低index非blocked的WinterBear109。不能盲用progress.current。队列108为授权数量，并非最大index（终项Zombie118）。WinterBear仅reference8文件；assessment/prompt/dispatch/creation为调度证据，无生成/暂存/安装/运行。

WinterBear生产路径：
- battle：{t['battle']}
- source：{t['source']}
- atlas：{t['atlas']}
- controller：{t['controller']}
父只核六保护与reference匹配，未审其源图。必须实际查看完整原atlas及源prefab，核层级、renderer/腿尾等真实解剖、原float/PPtr/事件/时长/loop及移动/战斗/回收/同实例复用，独立制定WinterBear正背面，不套公鸡/别的角色参数。开工前用当前磁盘包含既有用户修改建立Assets/Packages/ProjectSettings/Luban完整路径SHA基线及六保护，不用Git HEAD，不重置旧指纹。

逐阶段推进：源图解剖审阅→需要时按方向AIHub生成并实看raw→透明分件/atlas/pivot/PPU/layout/离线rig→保护/Unity空闲复核→仅本角色Builder安装/Verify→两轮真实Unity Play各84项，第二轮Up死亡→分批实际看原PNG/时序板/GIF，诚实记录抽样范围→最终安装/运行哈希绑定→UTF8 note/现有record流程→GIF归档SHA核对→完整路径并集/原组件语义审计。不能用程序PASS替代美术复核。视觉失败保留旧revision/运行历史、修复再测；优先复用成功raw，不删安装清单绕过防重。请求仍运行或结果不明先查进程/文件/响应，禁止盲目重发付费请求。不得无条件连跑各阶段。

需要生成时读取imagegen技能，沿用generate_character.ps1/generate.mjs和用户已授权AIHub https://aihub.dog/v1，gpt-image-2、medium、1536x1024、n=1。密钥仅运行时解密并仅发aihub.dog，不随跨域重定向，结束清理；不输出密钥/base64。按实际格式/尺寸保存；usage估算不是实际账单。遵守有界网络恢复授权及intent/revision保护，PossessedWarg不明请求不重发、不删阻断，不以换角色付费试探。

保护源atlas/源prefab/GUID/root/HP/碰撞/锚点/移动战斗参数和原侧面float/PPtr/事件/时长/loop。Up纯后脑无脸、后足方向正确，颈/肩髋/尾根连接，实际不存在的部件不新增。保留攻击、受击/致死白闪、全身死亡缩小旋转淡出、自动回收、同实例复用、暂停与1x/2x/3x，所有方向/状态无地面阴影。用既有方向系统，不加逐帧材质/层级查找。本角色不改共享C#、其他角色、配置表、Assets/ConfigJson、Assets/Gen或声音；不git pull/reset/clean/commit、不构建/设备部署、不更新长期memory。

用户本轮已确认正确MCP为8088。使用http://127.0.0.1:8088/mcp及Remaining_20261024/mcp_call.py Client.identity，动态读取custom-tools/instances、明确选现场完整MyTowerGame ID，再project/info核E:/MyTowerGame和2022.3.62f3c1（以版本文件为准）。8082是其他工程、8080是CatchFish；根AGENTS的FreedomTower/D盘/8082为历史错配，本任务和用户8088指令覆盖，不改根规则文件。不用路由其他工程的注入unityMCP结果代替；可用既有直接HTTP客户端。域重载/重连后重选并核身份，不硬编码旧ID。离线按规则自主恢复；失败报告环节/具体开启动作，不伪称成功。默认仅Unity MCP，桌面控制须另弹确认，此prompt未授权桌面。

本任务两轮真实Play明确授权，不重复询问。排查先本工程错误日志再状态和复现。只停本任务Play，不强停外来Play。最终单一clean Boot、非Play，tests/review/balance/recording/manual/compile/reload/update全部idle、failed=false/error0/ready=true；不清日志。C#只有另获明确授权才改，改后需正确工程refresh/compile/state/error闭环，编译时不继续改。缓存stale取新事实，不用端口/进程/旧快照代替端到端验证。

前任WildRooster最终证据WildRooster/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r03_20261029/review.json、gif_archive_verification_20261029.json。最终art_r03，installed_manifest.json，22条prePlay路径不变；293+307=600真实PNG，168/0。离线r01浮翅/重复领口和r02接缝已否决保留，r03局部融合臀尾/清理正面和根部连接；成功Up/Down raw未变，2次HTTP200/零重试。实际审10板256采样位/226不同PNG、6原PNG、12GIF各5编码帧及4未裁切整帧，非实时播放/逐帧全审。AllGIF1570，WildRooster12当前审核GIF，源归档SHA匹配。5485→5505文件、并集22变化/20新增、unexpected0；本角色语义PASS、其余5保护/共享C#无漂移，Reporter自动时间戳单列。旧global291unexpected/6其他角色语义失败保留，未重审，不称全局PASS。不要运行前任prepare/stage/install/finalize或覆盖封存证据。

每次实际查看1–2张清晰图，原图/完整帧留盘，不一次嵌全部角色/GIF历史。不能播放就实际看时序编码帧并明确限制，未看不写通过。中文UTF8，最终只能completed_pending_user_art_review、user_approved=false，不代替用户美术批准。

完成WinterBear全流程或准确记录真实阻断并释放Unity后，重读实时items，优先已开始可恢复项，否则最低index非blocked。写完整时间戳交接、更新README/执行prompt实时标记块、NEXT_ENEMY_TASK/progress并保留历史。按CONTINUATION_PROTOCOL主动创建唯一fresh local后继，不逐角色再问：chain先handoff_ready，现场list_projects确认E:/MyTowerGame，create_thread不传model/thinking、不fork，新聊天等active。创建明确成功后保存真实响应并登记新active owner/token为父最后工作区写入，此后父只读；一次有界wait_threads并给created-thread。创建不明先查真实列表，不重复创建；失败保留完整可执行NEXT并如实报告。循环至108项有效完成或只剩真实阻断。
'''
prompt_path.write_text(prompt,encoding='utf-8');(H/'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 WinterBear(index 109)\n\n'+prompt,encoding='utf-8')
live_text=f'''{now().strftime('%Y-%m-%d')} WildRooster108已record，97/108，completed_pending_user_art_review、user_approved=false。最终art_r03/14透明切片，installed_manifest.json；离线r01浮翅/重复领口和r02接缝否决保留，r03局部RGBA融合下臀尾羽、清理Down及连接，成功Up/Down raw未变、2次HTTP200/零重试。两轮293+307=600真实PNG、168PASS/0FAIL；实际审最终离线rig/Body、两轮四向/strip、10板256采样位/226不同PNG、6原PNG、12GIF各5编码帧与4未裁切整帧，非实时播放或逐帧全审。AllGIF1570，本角色12当前审核GIF，源/归档SHA一致。5485→5505文件、路径并集22变化20新增unexpected0，本角色语义PASS、其余5保护/共享C#无漂移，Reporter自动时间戳单列；旧global291unexpected/6其他角色语义失败未重审，不称全局PASS。Unity8088正确身份、最终编译/error0、单一clean Boot/非Play/全空闲/failed=false/ready=true/external_changes_dirty=false。最终WildRooster/final_validation_20261029.json及绑定/范围/视觉/归档。交接{rel(handoff)}。下一唯一WinterBear109 not_started，仅reference8文件；token={token}。剩余11含PossessedWarg旧blocked/uncertain及10项not_started。'''
for path,begin,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    content=path.read_text(encoding='utf-8-sig');pattern=re.escape(begin)+r'.*?'+re.escape(end)
    assert len(re.findall(pattern,content,re.S))==1
    content=re.sub(pattern,lambda _:begin+'\n'+live_text+'\n'+end,content,flags=re.S)
    if path.name=='README.md':
        content,count=re.subn(r'\d{4}-\d{2}-\d{2} 本轮当前清单为 \d+ 个文件',now().strftime('%Y-%m-%d')+' 本轮当前清单为 1570 个文件',content);assert count==1
    path.write_text(content,encoding='utf-8')
done['handoff_file']=handoff.relative_to(H).as_posix();progress.update(current=NEXT,updated_at=now().isoformat());write(H/'progress.json',progress)
dispatch={'prepared_at':now().isoformat(),'created':False,'parent_thread_id':OWNER,'character':NEXT,'character_index':109,'dispatch_token':token,
          'project_root':'E:/MyTowerGame','project_id':None,'project_live_confirmed':False,'project_association_confirmed':False,
          'handoff_file':rel(handoff),'handoff_sha256':sha(handoff),'assessment_file':rel(assessment),'assessment_sha256':sha(assessment),
          'unity_release_file':rel(release_path),'unity_release_sha256':sha(release_path),'prompt_file':rel(prompt_path),'prompt_sha256':sha(prompt_path),
          'next_task_file':rel(H/'NEXT_ENEMY_TASK.md'),'next_task_sha256':sha(H/'NEXT_ENEMY_TASK.md'),'progress_sha256':sha(H/'progress.json'),
          'response_file':rel(N/'successor_creation_response_20261029.json')}
write(dispatch_path,dispatch)
chain.setdefault('completed_handoffs',[]).append({'character':NAME,'status':done['status'],'current_stage':'recorded_pending_user_art_review',
              'closed_at':now().isoformat(),'owner_thread_id':OWNER,'dispatch_token':OLD,'handoff_file':rel(handoff),'final_evidence':rel(D/'final_validation_20261029.json')})
chain.update(state='handoff_ready',parent_thread_id=OWNER,current_character=NEXT,dispatch_token=token,character_status_at_handoff='not_started',
             completed_count_snapshot=97,previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),
             successor_assessment=rel(assessment),progress_sha256_at_handoff=sha(H/'progress.json'),unity_release_file=rel(release_path),
             dispatch_ready_for=NEXT,successor_created=False,current_stage='handoff_ready_pending_single_successor_creation',
             resume_character=NEXT,resume_stage='Verify owner/token; inspect original WinterBear anatomy and native motion; establish baseline',
             handoff_ready_at=now().isoformat(),updated_at=now().isoformat())
write(H/'conversation_chain.json',chain)
print(json.dumps({'state':'handoff_ready','character':NEXT,'dispatch_token':token,'dispatch_file':rel(dispatch_path),'prompt_file':rel(prompt_path),'handoff_file':rel(handoff),'safe_to_handoff':True},ensure_ascii=False))
