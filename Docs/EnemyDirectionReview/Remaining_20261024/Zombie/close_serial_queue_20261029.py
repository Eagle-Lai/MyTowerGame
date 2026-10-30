from session_current import *
from mcp_call import URL
import subprocess,shutil,time

chain=owner();progress=read(RUN/'progress.json')
assert progress['completed_count']==107 and progress['authorized_count']==108
item=next(r for r in progress['items'] if r['name']==NAME)
assert item['status']=='completed_pending_user_art_review' and not item['user_approved']
remaining=[r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']]
assert len(remaining)==1 and remaining[0]['name']=='PossessedWarg' and remaining[0]['status']=='blocked'
assessment=read(HERE/'successor_assessment_final_20261029.json')
assert assessment['selected'] is None and assessment['independently_recoverable_count']==0
binding=read(HERE/'final_version_binding_20261029.json');final=read(HERE/'final_validation_20261029.json')
runtime=read(HERE/'runtime_summary.json');review=read(HERE/'visual_review_final_20261029/review.json')
archive=read(HERE/'gif_archive_verification_20261029.json');accounting=read(HERE/'generation_final_accounting_20261029.json')
assert final['record_completed'] and final['original_semantics_pass'] and archive['after']==1744
assert snapshot()==binding['all_production_fingerprints']
oldblock=read(RUN/'PossessedWarg/blocked_20261026_125634_639300.json')
folder=RUN/'PossessedWarg';down=folder/'generation/Down'
material={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
assert material==assessment['remaining'][0]['files']
assert sha(down/'request.json')==oldblock['request_sha256']
assert sorted(p.name for p in down.iterdir())==['prompt.txt','request.json']
for path,v in oldblock['source_fingerprints'].items():assert sha(ROOT/path)==v['sha256']
process_code=r'''$rows=@(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.Name -in @('node.exe','curl.exe','python.exe','powershell.exe','pwsh.exe') -and $_.CommandLine -match 'generate_character\.ps1|generate\.mjs|generate_initial_direct_20261029\.ps1|generate_up_art_repair_r01_20261029\.ps1' } | Select-Object ProcessId,Name,CreationDate); ConvertTo-Json -InputObject $rows -Compress'''
proc=subprocess.run(['powershell.exe','-NoProfile','-Command',process_code],capture_output=True,text=True,check=True)
active=json.loads(proc.stdout.strip() or '[]');assert active==[],active
save(HERE/'image_process_snapshot_final_20261029.json',{'observed_at':now(),'active_image_generation_processes':active,'query':'Local node/curl/python/PowerShell processes invoking existing image-generation entry points; command lines not retained.'})
c=Client();project=c.identity()
def logs(extra=None):
    r=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json',**(extra or {})})
    v=r.get('structuredContent') or json.loads(r['content'][0]['text']);assert v['success'] and v['data']==[],v
    return r
errors=logs();compile_errors=logs({'filter_text':'error CS'})
state=fresh_state(c,'Zombie queue closeout actual state');p=probe(c);idle(p)
refresh=None
if state['data']['assets']['external_changes_dirty']:
    refresh=c.tool('refresh_unity',{'mode':'force','scope':'all','compile':'none','wait_for_ready':True})
    for attempt in range(20):
        c.identity();state=fresh_state(c,'Zombie closeout external changes imported')
        if not state['data']['assets']['external_changes_dirty']:break
        time.sleep(1)
    errors=logs();compile_errors=logs({'filter_text':'error CS'});p=probe(c);idle(p)
assert not state['data']['assets']['external_changes_dirty']
assert snapshot()==binding['all_production_fingerprints']
release=HERE/'handoff_release_final_20261029.json'
save(release,{'observed_at':now(),'project':project,'transport':URL,'success':True,'editor_state':state,'final_probe':p,'errors':errors,'compile_errors':compile_errors,'asset_refresh_to_clear_pending_external_changes':refresh,'all_production_unchanged_since_final_binding':True,'protocol_history':c.history})
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
rel=lambda p:p.relative_to(ROOT).as_posix()
handoff=RUN/'conversation_handoffs'/(stamp+'_Zombie_completed_queue_blocked.md')
stop_record=HERE/('queue_blocked_final_'+stamp+'.json')
backup=HERE/('docs_before_queue_stop_'+stamp);backup.mkdir()
for path in [RUN/'conversation_chain.json',RUN/'progress.json',RUN/'NEXT_ENEMY_TASK.md',RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',RUN.parent/'README.md']:
    shutil.copy2(path,backup/path.name)
reason='Only PossessedWarg79 remains. Original Down paid image-edit request has no raw/result/uncertain result, saved provider response or provider query ID; outcome and possible charge remain unknown. No independently recoverable production phase remains; no reissue, paid probe or successor chat.'
recovery=[
    '恢复原Down请求对应的完整图片/服务响应，并用request.json SHA256、输入/提示词和原时间核对身份；若取得服务端请求/任务ID，先查询原结果，不能把查询当作新生成。',
    '如果无法取回原结果，需要用户针对PossessedWarg Down明确授权一个新的有费用请求，并知悉旧请求结果/费用仍unknown及可能重复计费；一般API授权和其他角色的恢复额度不能替代这一针对性授权。',
    '合法恢复条件满足后先重读progress/chain与磁盘，显式登记唯一active所有权和适用于PossessedWarg的新token，再从已有Up和Down原始请求阶段恢复。不得清除旧unknown、重置计数或把Zombie再次执行。'
]
scope=read(HERE/'scope_incremental_final_20261029.json')
summary=f'''# Zombie118 完成；队列仅余 PossessedWarg79 阻断

封存时间：{now()}。本聊天/最终审计owner：{chain['owner_thread_id']}；本轮dispatch_token：{chain['dispatch_token']}。Zombie已record为completed_pending_user_art_review，user_approved=false；实时107/108。唯一未完成项PossessedWarg79保持blocked。没有后继候选，不创建新聊天、fork、子代理或自动化。

## 最终资源与原生合同

最终版本：{binding['art_revision']}。仅改Assets/Prefabs/Enemy/Enemy_Zombie.prefab及Assets/_UIAssets/Monsters/Giants/Zombie/Directions；battle SHA256为{binding['production_fingerprints']['Assets/Prefabs/Enemy/Enemy_Zombie.prefab']}。22个生产绑定、全部暂存、installed_manifest/Verify与角色专属native_attack_timing01 manifest/Verify均匹配preplay_version_binding_20261029.json，最终绑定见{rel(HERE/'final_version_binding_20261029.json')}。

源为灰褐/橄榄色缝合双足巨人，赭斑、浅米大块高光、刺状缝线与小环、头顶小块浅褐脑瓣、淡黄圆眼小黑瞳、愤怒张嘴/死亡空白眼闭嘴、深色宽护腕、米白破腰裙。解剖右手唯一象牙刺金褐木棒，左手空拳；没有骷髅项链、腰扣、尾巴或靴子。Up初图三个头误为正脸，否决原图完整保留；Up revision_01成功得到无脸后脑/耳背，Down用初图。Up三表情用选定Normal后脑复用，明确记录在art_selection。14透明分件、2048atlas、PPU100，alpha01填354个小孔像素且保原件/区域方法，最终0孔洞/0品红；layout02将肩髋根埋入躯干、双腿错相短步、后臂在body后。没有重新pack覆盖这些修订。

自身Giant Ready0.5s/Walk0.666666687s/Attack1s/Death0.5s，float绑定18/30/27/24、PPtr均0。Attack原事件SetHead0@0、SetHead1@0.25、Attack@0.766666651、SetHead0@0.783333361，Death SetHead2@0；完整曲线key/tangent/weight/wrap、事件、controller参数/过渡及原件字节存档。仅本角色Attack_Directions的92条DirectionVisual曲线，将蓄力结束定为2/3秒、发力峰值对齐原Attack事件，Down双臂相对Up镜像且空臂幅度30%。原左右绑定、事件、时长、loop和原源动画保持；没有修改共享C#。Zombie原battle表情接收器完整，无HeadSprites修复。generic原组件语义直接PASS，无例外门。

## 真实运行与视觉审阅

runtime_r01：84PASS0FAIL，{runtime['runtime'][0]['frames']}张PNG，JSONL SHA256 {runtime['runtime'][0]['records_sha256']}。runtime_updeath_r01：84PASS0FAIL，{runtime['runtime'][1]['frames']}张PNG，JSONL SHA256 {runtime['runtime'][1]['records_sha256']}。总168PASS0FAIL、639张真实Unity Play帧；两轮自动返回clean Boot。保存actual_frames.jsonl、checks、全部PNG的frame/realtime/normalizedTime/SHA及媒体。覆盖四向、斜向滞回/近零、原生状态/表情/攻击事件、连续转向保相位、受击和致死白闪结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复与1x/2x/3x、测试器Flying探针。无Animator.Update或合成姿态冒充实机帧。

实际审完整源/离线四向与两轮four_directions、runtime strip、14张时序/原生循环/GIF解码板，{review['png_sample_positions']}采样位/{review['unique_png_samples']}张不同真实PNG；12个最终GIF各5编码帧，共60。另看未裁Up、Down愤怒攻击、Up死亡、复用、双向GIF整帧，以及两轮Up/Down距0.766666651秒最近的发力峰值原PNG。所审样本肩髋根连接、短步及单手木棒横扫正常，发力时手和棒柄在躯干后自然遮挡；无五官后脑、重复器官、地面影或头手脚武器裁边。白闪结束、死亡和复用复位正常。死亡为分renderer淡出，重叠分件可见。采用逐序抽样，未实时播放GIF、未逐张审完全部639帧；不声称一体alpha。仍须用户美术验收。

Zombie原生Walk约666.6667ms，GIF只能编码10ms单位，6个行走循环分别从430/440/500/450/430/500ms修为最近合法670ms，量化差+3.3333ms。只在Docs按真实normalized phase及原有10组实际PNG配对重编码，无合成姿态，原6份GIF和两manifest保留。AllGIF1726→1744，本角色18来源=12当前审核版本+6历史时长版；本角色全部源/集中副本SHA一致，1726个旧来源及副本逐个SHA校验一致，分类保留。

## 范围与交还Unity

Assets/Packages/ProjectSettings/Luban全路径SHA并集5685→5705，共22变化=20新增Directions文件含根meta+当前battle修改+Reporter build_info自动时间戳，0删除、0unexpected。ReporterEditor代码未改，build_info严格匹配本机名/本地格式及两轮Play时间窗。源prefab/atlas及meta、原动画/controller字节、共享C#、其他角色/配置与首批批准/BlueScorpion历史保护保持。历史global scope不改写PASS。最终现场8088检查14个sprite rect/pivot/PPU100、Multiple/alphaTransparency/mipmap、依赖和live Verify通过；error/errorCS均0、scriptCompilationFailed=false；单一Assets/Scenes/Boot.unity干净，非Play、compile/update/reload/test/balance/recording/review/manual均空闲。无C#修改，不为形式额外编译。最终交还见{rel(release)}，未构建或部署。

## 网络与唯一未完成项

Zombie正式图像请求3次，全HTTP200：Up初图1532858bytes、Up定向美术revision_01为1481775bytes、Down初图1547009bytes，实际均PNG RGBA1536×1024。0unknown、0网络恢复、1次必要付费美术修正；费用未独立核实，响应usage为本地估计。保现有generate入口和Curl固定域名边缘，凭据仅运行时使用，无系统代理/hosts/TLS改动。其他历史unknown/计数完整保留，无借其他角色付费探测。

重新递归核所有未完成材料，仅PossessedWarg79，21个文件；Up已成功、Down只有prompt.txt和request.json，原请求SHA256 {oldblock['request_sha256']}，无raw/result/uncertain result、服务响应或查询ID，无stage/install/runtime；六源指纹仍与原阻断记录一致。本机没有既有入口的在途图像生成进程。原请求结果和可能费用unknown，不能推断未发送/未收费；本轮未重新发送或修改其原材料。队列因此blocked，不是108/108完成，也不因待用户美术审核而阻断。

恢复条件：

1. {recovery[0]}
2. {recovery[1]}
3. {recovery[2]}

真实队列、全部原失败/否决/未知请求及历史已保留；没有Git提交/同步/清理、配置表写入、声音恢复、桌面控制或memory修改。
'''
assert not handoff.exists();handoff.write_text(summary,encoding='utf-8')
next_text=f'''# 串行任务已封存：107/108，仅 PossessedWarg79 阻断

时间：{now()}。工程E:/MyTowerGame，Unity2022.3.62f3c1，unityMCP HTTP http://127.0.0.1:8088/mcp；根AGENTS中的FreedomTower_1/D:/8082是旧说明，不操作其他工程。完整本轮总结：{rel(handoff)}。

Zombie118已经完成制作、单角色安装、两轮真实Play、视觉抽样、record和GIF归档，状态completed_pending_user_art_review、user_approved=false。最终{binding['art_revision']}；runtime_r01/runtime_updeath_r01各84PASS0FAIL，共639PNG；AllGIF1744，本角色12最终+6历史。源与原动画保持、generic语义PASS、全路径增量0unexpected，22生产绑定与prePlay一致。证据：{rel(HERE/'final_validation_20261029.json')}、{rel(HERE/'final_version_binding_20261029.json')}、{rel(HERE/'visual_review_final_20261029/review.json')}、{rel(HERE/'gif_archive_verification_20261029.json')}。不得重复prepare/generate/install Zombie。

重读实时progress.items及递归未完成材料后，唯一未完成是PossessedWarg79 blocked。无其他可独立恢复角色/阶段，不创建后继聊天、子代理、fork、定时器或自动化；本次串行链在blocked停止。107项仅内部完成并待美术验收，不表示108项完成或用户批准。

## 唯一阻断现场

原Down开始于{oldblock['request_started']}，request.json SHA256 {oldblock['request_sha256']}。目录Docs/EnemyDirectionReview/Remaining_20261024/PossessedWarg/generation/Down仅prompt.txt和request.json，无raw.png/result.json/uncertain_result.json、服务响应或provider request/job ID。Up成功图保留，无stage/install/runtime；全部21材料文件及六源指纹保持，无在途生成进程。旧阻断记录{remaining[0]['blocked_record']}；最新递归指纹/评估{rel(HERE/'successor_assessment_final_20261029.json')}。结果及可能费用仍unknown；不能认定未发/失败/未收费，不重发，不借其他角色或非鉴权请求探测，不重置恢复计数。

## 满足恢复条件后再启动

1. {recovery[0]}
2. {recovery[1]}
3. {recovery[2]}

恢复时先读AGENTS.md、ProjectVersion.txt、README、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、progress.json、conversation_chain.json、上述总结及PossessedWarg全部请求/阻断材料，定向读取实现与既有差异。当前chain.state=blocked：保留封存owner {chain['owner_thread_id']}与旧Zombie token {chain['dispatch_token']}仅供审计，旧token不授权PossessedWarg生产操作；无active匹配新角色令牌时不得写生产或操作Unity。时间经过不会获得所有权。

满足针对性恢复条件并登记唯一active owner后，依实际已有阶段恢复，不清旧unknown/installed_manifest。Python固定C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8。图像继续使用现有合法generate_character.ps1/generate.mjs及用户固定域名边缘，密钥运行时DPAPI读取，不落明文；不在未满足条件时发付费诊断。单角色完成后仍须两轮各84检查的真实Play、原生合同/事件、实际PNG/GIF审阅和scope/record/归档，仅标待用户美术验收。

最终Unity已通过8088动态发现实例/选定/路径版本核对并交还单一clean Boot，非Play、所有任务空闲、error/errorCS0、failedfalse。见{rel(release)}。新恢复必须重新读取错误→fresh state→实际probe，不能继承旧空闲结论。不擅控桌面，确需电脑控制先明确确认。不改配置表/导出产物、声音、其他工程，不构建部署、Git提交同步清理或memory写入。
'''
(RUN/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
live=f'''{now()} Zombie118已record，107/108，completed_pending_user_art_review/user_approved=false。最终{binding['art_revision']}；两轮runtime_r01/runtime_updeath_r01共168PASS0FAIL/639PNG，实审14板319采样位/303不同PNG、12GIF各5编码帧，另审两轮发力峰值。自身Walk666.6667ms，6行走GIF仅Docs修为最近合法670ms，量化差+3.3333ms，原6GIF/两manifest保留。AllGIF1744，本角色18=12最终+6历史，全部旧1726来源/副本及新增SHA核对一致。全路径5685→5705，22变化/20新增/0删除/unexpected0，22生产绑定与prePlay一致，generic原组件语义PASS；无HeadSprites修复或C#改动。Unity8088 clean Boot非Play/error0/failedfalse。图像3请求3HTTP200/0unknown/0网络恢复/1付费美术修正，费用未独立核实。唯一未完成PossessedWarg79旧Down结果与费用unknown，无raw/result/查询ID，不重发；无独立恢复项，chain=blocked停止、不创建后继。针对性恢复条件见NEXT_ENEMY_TASK.md和{rel(handoff)}，保全部历史。'''
for path,begin,end in [(RUN.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=path.read_text(encoding='utf-8');assert text.count(begin)==text.count(end)==1
    start=text.index(begin)+len(begin);stop=text.index(end,start)
    text=text[:start]+'\n'+live+'\n'+text[stop:]
    if path.name=='README.md':
        old='2026-10-29 本轮当前清单为 1726 个文件'
        assert text.count(old)==1;text=text.replace(old,'2026-10-29 本轮当前清单为 1744 个文件')
    text+='\n\n2026-10-29 Zombie收口记录：'+live+'\n'
    path.write_text(text,encoding='utf-8')
stopped=now()
progress.update(status='blocked',current='PossessedWarg',updated_at=stopped,stopped_at=stopped,stop_reason=reason,remaining_count=1,last_completed_character=NAME,last_completed_handoff=rel(handoff))
(RUN/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
final.update(queue_state='blocked',queue_completed_count=107,queue_remaining=['PossessedWarg'],stop_reason=reason,handoff=rel(handoff),handoff_release=rel(release),handoff_release_sha256=sha(release),progress_sha256_at_stop=sha(RUN/'progress.json'))
(HERE/'final_validation_20261029.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
chain.setdefault('completed_handoffs',[]).append({'character':NAME,'status':item['status'],'current_stage':'recorded_pending_user_art_review','closed_at':stopped,'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'handoff_file':rel(handoff),'final_evidence':rel(HERE/'final_validation_20261029.json')})
chain.setdefault('blocked_history',[]).append({'character':'PossessedWarg','blocked_at':stopped,'blocked_reason':reason,'handoff_file':rel(handoff),'recovery_file':remaining[0]['blocked_record'],'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'after_completed_character':NAME})
chain.update(state='blocked',current_character='PossessedWarg',blocked_character='PossessedWarg',last_completed_character=NAME,last_owner_character=NAME,character_status_at_handoff='blocked',completed_count_snapshot=107,previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),successor_assessment=rel(HERE/'successor_assessment_final_20261029.json'),progress_sha256_at_stop=sha(RUN/'progress.json'),unity_release_file=rel(release),previous_prepared_dispatch_file=chain.get('prepared_dispatch_file'),prepared_dispatch_file=None,previous_creation_response_file=chain.get('creation_response_file'),creation_response_file=None,previous_successor_created=chain.get('successor_created'),successor_created=False,dispatch_ready_for=None,current_stage='queue_exhausted_only_original_down_unknown',resume_character='PossessedWarg',resume_stage='Reconcile original Down result or obtain targeted new-request authority, then register active exclusive owner with new character token before production.',current_blocked=True,blocked_reason=reason,stop_reason=reason,blocked_owner_retained=True,no_successor_creation_reason='Only the original PossessedWarg Down unknown blocker remains; no independent work.',stopped_at=stopped,updated_at=stopped,last_stage_evidence=rel(HERE/'final_validation_20261029.json'),recovery_file=remaining[0]['blocked_record'],previous_ownership_transfer_note=chain.get('ownership_transfer_note'),ownership_transfer_note='Completed Zombie owner and token retained only for audit. Chain is blocked; old Zombie token does not authorize PossessedWarg production. No successor created.',stop_record=rel(stop_record))
chain_bytes=(json.dumps(chain,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
chain_sha=hashlib.sha256(chain_bytes).hexdigest().upper()
save(stop_record,{'observed_at':stopped,'state':'blocked','completed':107,'authorized':108,'remaining':['PossessedWarg'],'owner_thread_id':chain['owner_thread_id'],'retained_dispatch_token':chain['dispatch_token'],'completed_character':NAME,'current_character':'PossessedWarg','reason':reason,'recovery_conditions':recovery,'old_unknown_request_sha256':oldblock['request_sha256'],'old_material_hashes_unchanged':True,'no_successor_created':True,'no_paid_reissue_or_probe':True,'expected_chain_sha256':chain_sha,'files':{rel(p):sha(p) for p in [handoff,release,RUN/'NEXT_ENEMY_TASK.md',RUN/'progress.json',RUN.parent/'README.md',RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',HERE/'final_validation_20261029.json',HERE/'final_version_binding_20261029.json',HERE/'gif_archive_verification_20261029.json']}})
# Final workspace write: freeze queue ownership and stop. No more mutations after this.
(RUN/'conversation_chain.json').write_bytes(chain_bytes)
assert sha(RUN/'conversation_chain.json')==chain_sha
print(json.dumps({'state':'blocked','completed':107,'authorized':108,'remaining':['PossessedWarg'],'Zombie_passes':168,'Zombie_failures':0,'actual_frames':639,'AllGIF':1744,'clean_Boot':True,'handoff':rel(handoff),'stop_record':rel(stop_record),'chain_sha256':chain_sha,'successor_created':False},ensure_ascii=False))
