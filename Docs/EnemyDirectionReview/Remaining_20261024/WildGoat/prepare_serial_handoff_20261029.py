"""Release WildGoat and prepare its one authorized fresh local successor."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import ast, hashlib, json, os, re, sys, uuid

D=Path(__file__).resolve().parent; H=D.parent; ROOT=H.parents[2]; N=H/'WildRooster'
OWNER='01a1841b-d4fc-7eb2-9ace-b66dc688e0c2'
OLD='whitewolf-to-wildgoat-20261029_040116-747154f6-09f2-4b00-940c-121c7a063e19'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now=lambda:datetime.now(timezone(timedelta(hours=8)))
rel=lambda p:p.relative_to(ROOT).as_posix()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
assert os.environ['CODEX_THREAD_ID']==OWNER
chain=read(H/'conversation_chain.json');progress=read(H/'progress.json')
assert chain['state']=='active' and chain['owner_thread_id']==OWNER and chain['dispatch_token']==OLD and chain['current_character']=='WildGoat'
done=next(r for r in progress['items'] if r['name']=='WildGoat')
assert progress['completed_count']==96 and done['status']=='completed_pending_user_art_review' and not done['user_approved']
remaining=[r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[r for r in remaining if r['status'] not in ['not_started','blocked']]
selected=min(recoverable or [r for r in remaining if r['status']!='blocked'],key=lambda r:r['index'])
assert selected['name']=='WildRooster' and selected['index']==108 and selected['status']=='not_started'
assert len(remaining)==12 and next(r for r in remaining if r['name']=='PossessedWarg')['status']=='blocked'
existing=sorted(p for p in N.rglob('*') if p.is_file())
assert len(existing)==8 and all(p.is_relative_to(N/'reference') for p in existing)
t=next(r for r in read(H/'local_baseline.json')['targets'] if r['name']=='WildRooster')
six={p:sha(ROOT/p) for k in ['battle','source','atlas'] for p in [t[k],t[k]+'.meta']}
assert all(six.values()) and all(sha(N/'reference'/Path(p).name)==v for p,v in six.items())
final=read(D/'final_validation_20261029.json');binding=read(D/'version_binding_final_20261029.json');scope=read(D/'scope_incremental_final_20261029.json')
assert (final['passes'],final['failures'],final['actual_png_frames'])==(168,0,596) and final['final_revision']=='art_r02'
assert all(sha(ROOT/p)==v for p,v in binding['installed_files'].items()) and len(binding['installed_files'])==22
for file,key in [('version_binding_final_20261029.json','version_binding_sha256'),('scope_incremental_final_20261029.json','incremental_scope_sha256'),('visual_review_art_r02_20261029/review.json','visual_review_sha256'),('gif_archive_verification_20261029.json','gif_archive_sha256')]:
    assert sha(D/file)==final[key]
assert (scope['baseline_files'],scope['current_files'],len(scope['changes']),scope['added_count'],scope['deleted_count'])==(5465,5485,22,20,0)
assert not scope['unexpected_incremental'] and not scope['shared_CSharp_drift'] and scope['prefab_semantics']['pass']
assert final['global_archive_count']==1558
assert not any(r.get('character')=='WildGoat' for r in chain.get('completed_handoffs',[]))
sys.path.insert(0,str(H));from mcp_call import Client,URL
c=Client();project=c.identity()
# Reuse the already reviewed, short factual probes, without running the verifier again.
tree=ast.parse((D/'verify_unity_post_r02_20261029.py').read_text(encoding='utf-8'))
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
stamp=now().strftime('%Y%m%d_%H%M%S');token='wildgoat-to-wildrooster-'+stamp+'-'+str(uuid.uuid4())
handoff=H/'conversation_handoffs'/(stamp+'_WildGoat_completed.md')
assessment=N/('successor_assessment_'+stamp+'.json');prompt_path=N/('successor_prompt_'+stamp+'.txt')
release_path=D/'handoff_release_20261029.json';dispatch_path=N/'prepared_dispatch_20261029.json'
assert all(not p.exists() for p in [handoff,assessment,prompt_path,release_path,dispatch_path])
write(release_path,{'observed_at':now().isoformat(),'released_by_thread_id':OWNER,'current_character':'WildGoat','next_character':'WildRooster','next_dispatch_token':token,
                    'transport':URL,'project':project,'editor_state':state,'live_probe':live,'console_errors':[],'safe_to_handoff':True,'protocol_history':c.history})
write(assessment,{'observed_at':now().isoformat(),'completed_count':96,'authorized_count':108,'next_character':'WildRooster','next_index':108,
                  'status':'not_started','dispatch_token':token,'target':t,'protected_six':six,'reference_matches_live':True,
                  'existing_files':[p.relative_to(N).as_posix() for p in existing],
                  'source_art_reviewed_by_parent':False,'source_instruction':'Next owner must inspect original atlas, full source prefab and native Rooster animation before planning bird anatomy.',
                  'no_generation_staging_install_or_runtime':True,'remaining':[{k:r[k] for k in ['index','name','status']} for r in remaining],
                  'blocked_preserved':[r for r in remaining if r['status']=='blocked']})
summary=f'''# WildGoat107 完成与 WildRooster108 唯一串行交接

时间 {now().isoformat()}。父线程 {OWNER}；旧token {OLD}。WildGoat已record为completed_pending_user_art_review，user_approved=false；进度96/108。

## 最终实现与视觉返修

最终art_r02，14透明切片；灰褐赭斑山羊、双弯角、垂耳、奶油鬃毛/胡须、四蹄、短翘尾保留。r01的Down躯干包含重复角与毛肢片，Up蹄为前向趾，被内部视觉否决；旧r01生产备份、运行和媒体保留。r02复用无脸Up轴向躯干纵向翻转作为Down躯干，保留真Down三表情头；Up蹄内局部改绘后跟、腿根内收。成功Up/Down raw未改，无新增收费请求。Up纯后脑无脸，三表情图相同；原左右侧面和镜像、战斗/回收/同实例复用契约保留，无共享C#修改。不要重跑prepare/stage/pack/install覆盖最终资源。

最终安装清单WildGoat/repair_art_r02/manifest.json，SHA {final['manifest_sha256']}；Builder/Verify通过。完整22路径在WildGoat/production_before_play_20261029.json，两轮Play前已安装r02，直到封存均未变。原installed_manifest.json属于r01，不作为最终版本。14片Multiple、PPU100、透明、无mipmap，实际矩形/pivot匹配。

## 真实运行与审阅

runtime_r02：84/0、296帧，records SHA {final['runtime'][0]['records_sha256']}。
runtime_updeath_r02：84/0、300帧，records SHA {final['runtime'][1]['records_sha256']}。第二轮Up死亡。共168 PASS/0 FAIL、596真实PNG；两轮均恢复clean Boot。

实际查看离线rig和透明分件、两轮四向图、strip、10张时序/步态/愤怒板：256采样位、229不同真实PNG；5张完整原PNG，12个最终GIF各5编码帧共60帧及4张未裁切编码整帧。观察步态错相、攻击头切换、白闪恢复、Down/Up死亡缩小旋转淡出、回收与正常Down复用、暂停冻结/恢复及1x/2x/3x推进。头身/腿根/尾根相连、无地面阴影；整帧角尖完整，血条有间距。非实时播放或逐GIF全帧审阅；596原PNG留盘并哈希。用户美术验收仍待进行。

AllGIF1558，WildGoat24项：12个r02当前审核版本、12个r01历史；源/归档SHA一致。现场归档前实际1546（已有12个r01），本次增加12个r02。不能使用旧1534快照计算本次新增。

最终证据：WildGoat/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r02_20261029/review.json、gif_archive_verification_20261029.json、unity_release_post_r02_20261029.json、runtime_summary.json和record_note_utf8.txt。

## 范围与Unity释放

原本角色当前磁盘基线5465→5485文件；Assets/Packages/ProjectSettings/Luban路径并集22变化、20新增、0删除、unexpected0。仅本角色battle/Directions，另未修改Reporter自动Play时间戳单列。源图/源prefab/GUID及其余5保护、共享C#、其他角色、配置/无声版本无漂移。本角色原组件语义PASS。历史全局291unexpected/6其他角色语义失败保留，本轮未全局复审，不称全局PASS。

正确Unity经8088动态custom-tools/instances选定MyTowerGame、project/info核E:/MyTowerGame和2022.3.62f3c1。最终刷新/编译成功、error0；释放时再次动态核身份，单一clean Boot/非Play，全worker/编译/更新/重载空闲，failed=false、ready=true、external_changes_dirty=false。释放证据{rel(release_path)}。不清日志，不使用桌面。

## 下一唯一角色

剩余12项：PossessedWarg旧blocked及不明付费请求保留；11项not_started。无已开始可恢复的非blocked项，按index选择WildRooster108。仅8个reference文件，六保护一致，无anatomy/generation/stage/install/runtime。父未看WildRooster源图，不声称已审鸟类造型；后继自行检查{t['atlas']}、{t['source']}、{t['battle']}和{t['controller']}，为它独立制定正背解剖。

新token {token}。完整prompt {rel(prompt_path)}，assessment {rel(assessment)}。先handoff_ready，再现场list_projects并创建唯一fresh local聊天，不fork/子代理/计时器/模型覆盖；创建明确成功后登记active作为父最后工作区写入。后继仅匹配active owner/token时操作生产/Unity。未将美术待审当批准。
'''
handoff.write_text(summary,encoding='utf-8')
prompt=f'''在E:/MyTowerGame继续敌人四方向串行续作，唯一角色WildRooster(index108)。这是用户2026-10-26明确授权的“完成一个角色→总结/更新prompt→唯一全新local后继”循环。

唯一dispatch_token：{token}
父线程：{OWNER}

先完整读取当前磁盘：
1. E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
3. Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
4. 同目录CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json。
5. 同目录standing_network_recovery_authorization_20261028.json、TreasureChest/standing_recovery_application_20261028.json，核对有界恢复授权，保留结果不明/收费证据。
6. E:/MyTowerGame/{rel(handoff)}。
7. E:/MyTowerGame/{rel(assessment)}。
8. WildRooster/reference全部原图、源结构与prefab；按需读取单角色流水线与共享实现的直接调用/依赖/生命周期。

仅chain.state=active、owner_thread_id等于本新聊天、current_character=WildRooster、dispatch_token与上方一致时，才能操作Unity、生产或付费请求。父handoff_ready期间只读等待登记，不超时抢锁，不修改链，不创建别的任务。父注册成功后停止全部工作区写入。开工检查实时文件，恢复已有阶段，禁止盲重跑prepare、生成或安装。一次仅处理一个角色，不并发、不子代理、不fork、不计时器、不覆盖模型/推理设置。

实时96/108；WildGoat107已record，art_r02、completed_pending_user_art_review、user_approved=false；12项未完成包括PossessedWarg旧blocked与不明Down付费请求、11项not_started。WildRooster108仅reference8文件，无生成/暂存/安装/运行；本目录新增assessment/prompt/dispatch/creation属于调度证据。PossessedWarg不重发、不删阻断、不伪称完成。队列108为授权数量，不是最大index（终项Zombie118）。

WildRooster生产路径：
- battle：{t['battle']}
- source：{t['source']}
- atlas：{t['atlas']}
- controller：{t['controller']}
父仅核六保护与reference匹配，未审该鸟类原图。后继必须实际查看完整原atlas及源prefab、层级绑定、原float/PPtr/事件/时长/loop和移动/战斗/回收/同实例复用，独立设计WildRooster的头、喙、冠/尾羽/翅及双足，以原图实际存在部件为准，不套山羊/四足或其他角色参数。改动前以当前磁盘含既有用户改动建立Assets/Packages/ProjectSettings/Luban全路径SHA增量基线及六保护；不使用Git HEAD、不重置历史指纹。

逐阶段执行原prompt：原图/解剖审阅→按需逐方向AIHub并实看raw→透明分件/atlas/pivot/PPU/layout及离线rig检查→六保护及Unity空闲复核→仅当前角色Builder安装/Verify→两轮真实Unity Play各84项，第二轮Up死亡→分批实际看PNG/时序板/GIF并如实记抽样→最终安装/运行版本哈希绑定→UTF8 note/record→GIF归档SHA核对→完整路径并集及原组件语义审计。程序PASS不能代替美术审阅；视觉失败须保留旧revision、修复并重测。优先复用成功raw；现有请求仍运行/结果不明先查进程、落盘和响应，不重发付费请求，不删安装清单绕过防重。不得一口气无条件连跑各阶段。

需要生成时读取imagegen技能并沿用generate_character.ps1/generate.mjs和用户授权AIHub https://aihub.dog/v1，gpt-image-2、medium、1536x1024、n=1；密钥运行时读取且仅发aihub.dog、不随跨域重定向，结束清理，不输出密钥或base64。按实际返回格式/尺寸保存，usage估算不当实际账单；遵守现有有界网络恢复授权与intent/revision护栏，不把不明请求当未收费或换角色付费试探。

保护原atlas/源prefab/GUID/root/HP/碰撞/锚点/移动战斗参数和原侧面动画float/PPtr/事件/时长/loop；Up纯后脑无脸、后足方向正确，肩髋/颈/尾根和翅连接，无原图没有的部件。保留攻击、受击和致死白闪、全身死亡缩小淡出、自动回收、同实例复用、暂停及1x/2x/3x；四向及各状态无地面阴影。使用既有方向系统，不新增逐帧材质/层级查找；本角色不改其他角色及共享C#，不改配置表、Assets/ConfigJson、Assets/Gen或声音；不Git pull/reset/clean/commit、不构建或设备部署、不更新长期memory。

用户本次再次确认正确MCP端口8088。使用http://127.0.0.1:8088/mcp与Remaining_20261024/mcp_call.py Client.identity，动态读取custom-tools/instances、明确选现场完整MyTowerGame ID、再project/info核E:/MyTowerGame及版本2022.3.62f3c1（仍以版本文件为准）。8082连接其他工程，8080是CatchFish；根AGENTS中FreedomTower/D盘/8082为历史错配，以本任务与用户8088指令覆盖，不改根规则文件。服务注入unityMCP若路由其他工程不可使用其结果替代；可继续既有直接HTTP客户端。重连/域重载后重新核身份，不硬编码旧ID。离线按规则自主恢复，失败报告实际环节和具体开启动作，不假称验证。默认仅Unity MCP，桌面控制须先弹确认，本prompt未授权桌面。

本任务两轮真实Play已授权，无需重复询问。运行时排查先日志、再场景状态；只停本任务Play，不强停外来任务。完成必须回单一clean Boot、非Play，tests/review/balance/recording/manual/compile/reload/update全部idle、failed=false、error0、ready=true；不清日志。C#仅另获明确修改授权时再动，改后必须正确工程refresh/compile/state/error闭环且编译中不改代码。缓存stale取新事实，不用端口监听或旧快照冒充成功。

WildGoat最终证据WildGoat/final_validation_20261029.json及version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r02_20261029/review.json、gif_archive_verification_20261029.json。r01重复角/毛肢与前向Up蹄已否决并保留；最终r02本地复用无脸躯干、真Down头、后跟及腿根，成功raw未改。最终安装是repair_art_r02/manifest.json，原installed_manifest为历史r01。22条prePlay生产路径无漂移；两轮296+300=596PNG、168/0。实际看10板256采样位/229不同PNG、5原PNG、12GIF各5编码帧及4未裁切整帧，非实时播放或逐帧全审。AllGIF1558，WildGoat24（r02当前12+r01历史12），源/归档SHA一致。5465→5485文件，路径并集22变化20新增unexpected0，本角色语义PASS、其余5保护/共享C#无漂移；Reporter自动时间戳单列。旧全局291unexpected/6其他角色语义失败未重审，禁止称全局PASS。不要重跑前任prepare/stage/pack/Build/install/finalize覆盖已封存资源。

图片分次每次1-2张清晰预览及必要原图细节，原件与完整帧留盘，不一次嵌入全部角色/GIF/历史图。不能播放则按时序实际看编码帧并准确声明限制，未看不能写通过。中文文档UTF8；最终只能completed_pending_user_art_review、user_approved=false，不代替用户美术批准。

完成WildRooster原全流程或准确记录真实阻断并释放Unity后，重读实时items，先已开始可恢复项，否则最低index非blocked，不盲用progress.current。写完整交接总结、更新README实时块、原执行prompt实时块、NEXT_ENEMY_TASK/progress，保留历史与阻断。按CONTINUATION_PROTOCOL主动创建唯一fresh local后继，不逐角色再问：chain先handoff_ready，现场list_projects确认E:/MyTowerGame，再create_thread，不传model/thinking、不fork；新聊天等active。创建明确成功后保存真实响应并登记active新owner/token作为父最后一次工作区写入，此后只读，一次有界wait_threads并报告created-thread。创建结果不明先查实际列表，不重复创建；失败保留完整可执行NEXT并报告。循环至108全部有效完成或只余真实阻断。
'''
prompt_path.write_text(prompt,encoding='utf-8');(H/'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 WildRooster(index 108)\n\n'+prompt,encoding='utf-8')
live_text=f'''{now().strftime('%Y-%m-%d')} WildGoat107已record，96/108，completed_pending_user_art_review、user_approved=false。最终art_r02、14透明切片；r01重复角/毛肢和前向Up蹄否决保留，r02复用无脸轴向躯干为Down、保留真头、局部后跟和腿根修复，成功raw未改、无新请求。两轮296+300=596真实PNG、168PASS/0FAIL；实际看离线rig/分件、两轮四向/strip、10板256采样位/229不同PNG、5原PNG、12GIF各5编码帧与4未裁切整帧，角尖完整且HP有间距；非实时播放或逐GIF全帧。AllGIF1558，WildGoat24（r02当前12、r01历史12），源/归档SHA一致。5465→5485路径并集22变化20新增unexpected0，本角色语义PASS、其余5保护/共享C#无漂移，Reporter自动时间戳单列。旧global291unexpected/6其他角色语义失败保留，不称全局PASS。Unity8088正确身份，最终刷新/编译无误、单一clean Boot/非Play/全空闲/failed=false/error0/ready=true/external_changes_dirty=false。最终WildGoat/final_validation_20261029.json及绑定/范围/视觉/归档；repair_art_r02/manifest.json为最终安装，原installed_manifest属于r01。交接{rel(handoff)}。下一唯一WildRooster108 not_started，仅reference8文件，token={token}。剩余12含PossessedWarg旧blocked/uncertain及11项not_started。'''
for path,begin,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    content=path.read_text(encoding='utf-8-sig');pattern=re.escape(begin)+r'.*?'+re.escape(end)
    assert len(re.findall(pattern,content,re.S))==1
    content=re.sub(pattern,lambda _:begin+'\n'+live_text+'\n'+end,content,flags=re.S)
    if path.name=='README.md':
        content,count=re.subn(r'\d{4}-\d{2}-\d{2} 本轮当前清单为 \d+ 个文件',now().strftime('%Y-%m-%d')+' 本轮当前清单为 1558 个文件',content);assert count==1
    path.write_text(content,encoding='utf-8')
done['handoff_file']=handoff.relative_to(H).as_posix();progress.update(current='WildRooster',updated_at=now().isoformat());write(H/'progress.json',progress)
dispatch={'prepared_at':now().isoformat(),'created':False,'parent_thread_id':OWNER,'character':'WildRooster','character_index':108,'dispatch_token':token,
          'project_root':'E:/MyTowerGame','project_id':None,'project_live_confirmed':False,'project_association_confirmed':False,
          'handoff_file':rel(handoff),'handoff_sha256':sha(handoff),'assessment_file':rel(assessment),'assessment_sha256':sha(assessment),
          'unity_release_file':rel(release_path),'unity_release_sha256':sha(release_path),'prompt_file':rel(prompt_path),'prompt_sha256':sha(prompt_path),
          'next_task_file':rel(H/'NEXT_ENEMY_TASK.md'),'next_task_sha256':sha(H/'NEXT_ENEMY_TASK.md'),'progress_sha256':sha(H/'progress.json'),
          'response_file':rel(N/'successor_creation_response_20261029.json')}
write(dispatch_path,dispatch)
chain.setdefault('completed_handoffs',[]).append({'character':'WildGoat','status':done['status'],'current_stage':'recorded_pending_user_art_review',
              'closed_at':now().isoformat(),'owner_thread_id':OWNER,'dispatch_token':OLD,'handoff_file':rel(handoff),'final_evidence':rel(D/'final_validation_20261029.json')})
chain.update(state='handoff_ready',parent_thread_id=OWNER,current_character='WildRooster',dispatch_token=token,character_status_at_handoff='not_started',
             completed_count_snapshot=96,previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),
             successor_assessment=rel(assessment),progress_sha256_at_handoff=sha(H/'progress.json'),unity_release_file=rel(release_path),
             dispatch_ready_for='WildRooster',successor_created=False,current_stage='handoff_ready_pending_single_successor_creation',
             resume_character='WildRooster',resume_stage='Verify owner/token; inspect original bird anatomy and native motion; establish baseline',
             handoff_ready_at=now().isoformat(),updated_at=now().isoformat())
write(H/'conversation_chain.json',chain)
print(json.dumps({'state':'handoff_ready','character':'WildRooster','dispatch_token':token,'dispatch_file':rel(dispatch_path),'prompt_file':rel(prompt_path),'handoff_file':rel(handoff),'safe_to_handoff':True},ensure_ascii=False))
