"""Release art_r02 and prepare exactly one local WinterWolfTypeA successor."""
from session_winterwarg import *
from mcp_call import URL
import re, shutil, uuid

chain=owner(); progress=read(H/'progress.json')
done=next(i for i in progress['items'] if i['name']==NAME)
assert progress['completed_count']==101 and done['status']=='completed_pending_user_art_review' and done['user_approved'] is False
remaining=[i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[i for i in remaining if i['status'] not in ['not_started','blocked']]
selected=min(recoverable or [i for i in remaining if i['status']!='blocked'],key=lambda i:i['index'])
NEXT=selected['name'];N=H/NEXT
assert (NEXT,selected['index'],selected['status'])==('WinterWolfTypeA',113,'not_started')
assert len(remaining)==7 and sum(i['status']=='not_started' for i in remaining)==6
blocked=next(i for i in remaining if i['name']=='PossessedWarg');assert blocked['status']=='blocked'
old_block=read(H/'PossessedWarg/blocked_20261026_125634_639300.json')
down=H/'PossessedWarg/generation/Down'
assert sha(down/'request.json')==old_block['request_sha256']
assert not any((down/p).exists() for p in ['raw.png','result.json','uncertain_result.json'])
existing=[p for p in N.rglob('*') if p.is_file()]
assert len(existing)==8 and all(p.is_relative_to(N/'reference') for p in existing)
t=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']==NEXT)
six={p:sha(ROOT/p) for k in ['battle','source','atlas'] for p in [t[k],t[k]+'.meta']}
assert all(sha(N/'reference'/Path(p).name)==s for p,s in six.items())
final=read(D/'final_validation_20261029.json');binding=read(D/'version_binding_final_20261029.json')
assert (final['passes'],final['failures'],final['actual_png_frames'])==(168,0,679)
assert all(sha(ROOT/p)==s for p,s in binding['production_scope_files'].items())
assert all(sha(ROOT/p)==s for p,s in binding['installed_files'].items())
for file,key in [('version_binding_final_20261029.json','version_binding_sha256'),
                 ('scope_incremental_final_20261029.json','incremental_scope_sha256'),
                 ('visual_review_art_r02_full_actor_20261029/review.json','visual_review_sha256'),
                 ('gif_archive_verification_20261029.json','gif_archive_sha256')]:
    assert sha(D/file)==final[key]
assert read(H.parent/'AllGIF/manifest.json')['count']==final['global_archive_count']==1642
c=Client();project=c.identity()
def logs(**extra):
    r=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json',**extra})
    return r.get('structuredContent') or json.loads(r['content'][0]['text'])
errors=logs();error_cs=logs(filter_text='error CS')
state=c.resource('mcpforunity://editor/state')['data'];live=probe(c);idle(live)
assert state['advice']['ready_for_tools'] and not state['tests']['is_running']
assert not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending']
assert not state['assets']['is_updating'] and not state['assets']['external_changes_dirty']
assert errors['data']==error_cs['data']==[]

stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token='winterwarg-to-winterwolftypea-'+stamp+'-'+str(uuid.uuid4())
rel=lambda p:p.relative_to(ROOT).as_posix()
handoff=H/'conversation_handoffs'/(stamp+'_WinterWarg_completed.md')
assessment=N/('successor_assessment_'+stamp+'.json')
prompt_path=N/('successor_prompt_'+stamp+'.txt')
release=D/'handoff_release_final_20261029.json';dispatch_path=N/'prepared_dispatch_20261029.json'
assert all(not p.exists() for p in [handoff,assessment,prompt_path,release,dispatch_path])
backup=D/'docs_before_final_handoff_20261029';assert not backup.exists();backup.mkdir()
for p in [H/'NEXT_ENEMY_TASK.md',H/'conversation_chain.json',H/'progress.json',H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',H.parent/'README.md']:
    shutil.copy2(p,backup/p.name)
write(release,{'observed_at':now(),'released_by_thread_id':OWNER,'current_character':NAME,'next_character':NEXT,
    'next_dispatch_token':token,'transport':URL,'project':project,'editor_state':state,'live_probe':live,
    'current_console_errors':errors,'current_error_CS':error_cs,'earlier_errors_preserved_in_evidence':True,
    'safe_to_handoff':True,'protocol_history':c.history},True)
write(assessment,{'observed_at':now(),'completed_count':101,'authorized_count':108,'next_character':NEXT,'next_index':113,
    'status':'not_started','dispatch_token':token,'target':t,'protected_six':six,'reference_matches_live':True,
    'existing_files':[p.relative_to(N).as_posix() for p in existing],'source_art_reviewed_by_parent':False,
    'source_instruction':'Next owner must independently inspect WinterWolfTypeA original atlas/full prefab, four legs, Tail, anchors and Wolf animation contract; no copying WinterWarg anatomy or layout.',
    'no_generation_staging_install_or_runtime':True,'remaining':[{k:i[k] for k in ['index','name','status']} for i in remaining],
    'blocked_preserved':[blocked],'possessedwarg_readonly_recheck':{'request_unchanged':True,'raw_result_uncertain_file_still_absent':True,
    'old_block_file':'PossessedWarg/blocked_20261026_125634_639300.json','no_new_request':True}},True)

summary=f'''# WinterWarg112 完成与 WinterWolfTypeA113 唯一串行交接

时间 {now()}。父线程 {OWNER}，旧 token {TOKEN}。WinterWarg 已 record 为 completed_pending_user_art_review，user_approved=false；总进度101/108，当前唯一后继WinterWolfTypeA113 not_started。仍余PossessedWarg79 blocked及113–118六项未开始，终项Zombie118；108是授权数，不是末项index。PossessedWarg原Down request SHA仍与旧阻断一致且无raw/result/uncertain/可查询新结果，未重发或删除。

## 生产与美术最终版本

最终art_r02，battle {t['battle'].replace('WinterWolfTypeA','WinterWarg')}；Directions Assets/_UIAssets/Monsters/Dogs/WinterWarg/Directions。初装installed_manifest.json为art_r01，因真实运行观察轴向头偏小而保留并否决。installed_repair_art_r02_20261029.json为最终返修，Up头height0.57/y0.79，Down头height0.64/y0.42；最终22个prePlay生产指纹在两轮后未变，含Directions根meta。原source/atlas及meta、battle.meta、原Wolf动画和共享C#无本轮漂移。

选图Up=generation/Up/local_revision_05/raw.png（父为成功revision_02），Down=首次generation/Down/raw.png。白/象牙蓬毛、金赭斑点、棕背刺、圆耳、剑齿、四犬腿、下垂长尾；Up无脸短后冠毛/光滑后跟，三种后脑状态共用；Down三种头状态正确。局部03/04修补伪影和art_r01运行均保留，不回退或覆盖。14透明分件/2048atlas/PPU100，尾根按各方向实测pivot，短步四足对角相位。清理填793封闭微小透明像素、去4外部尘点，清理前保存；最终alpha无封闭洞/不透明品红。

原Wolf契约Ready/Walk/Attack均0.5秒，Death0.416666657秒；float/PPtr曲线、事件、loop、长度和rate按源合同与当前Unity核对。14实际导入sprite逐rect/pivot/PPU核对，Multiple/alphaTransparency=true/mipmap=false；prefab依赖与现有YooAsset收集器Verify通过，没有发布构建。

## 运行与视觉证据

runtime_art_r02：84PASS/0FAIL，340真实PNG，records SHA {final['runtime'][0]['records_sha256']}。
runtime_art_updeath_r02：84PASS/0FAIL，339真实PNG，records SHA {final['runtime'][1]['records_sha256']}。总168PASS/0FAIL、679真实PNG，均在最终生产版本安装之后实际Play，均安全返回clean Boot；完整PNG指纹在version_binding_final_20261029.json。旧art_r01两轮678PNG/168PASS0FAIL仅为否决历史。

实际审两轮four_directions、最终runtime_visual_strip、12张时序/步态板共268采样位/254不同PNG、8张原始768PNG、12最终GIF各5编码帧共60帧和4张未裁切GIF整帧。覆盖四向步态/原生状态/连续转向/攻击张口/受击和致死白闪恢复/Down及Up整身死亡旋转收缩淡出/自动回收与同实例Down正常复用/暂停恢复与1x2x3x。无地面阴影，尾根和肩髋保持连接。未实时播放GIF、未逐帧全审；死亡既有逐renderer alpha会显出重叠分件。早先visual_review_art_r02_20261029裁掉Up耳，保留为历史，最终使用visual_review_art_r02_full_actor_20261029并另看整帧；attempt01时长断言失败保留。

GIF逐帧毫秒截断使原Up480ms/Down490ms，本角色按累计相位量化修成原Walk500ms，不生成姿态/不改生产。六个修前GIF在media_before_gif_quantization_fix_art_r02保留。AllGIF1612→1642，本角色30来源=12最终+12否决art_r01+6旧时长，全源/副本SHA一致；历史分类不代表批准。

## 请求状态与范围

首次Up和revision01结果/费用仍不明，原请求、uncertain_result及stderr均保留。既有standing_recovery2/2已消耗且未重置；Up revision02及首次Down均HTTP200，成功raw保留。不能以成功新请求推断旧请求未计费。不得再发本角色旧请求或复制角色特定恢复许可。

完整路径并集Assets/Packages/ProjectSettings/Luban：5565→5585，22变化、20新增、0删除、unexpected0；仅WinterWarg battle、Directions含根meta和确证未改ReporterEditor产生的build_info时间戳。本角色原prefab语义PASS、源/meta保护及共享C#无增量漂移；旧全局scope失败未重审，不称全局PASS。没有配置表/声音/构建/部署/Git提交或桌面控制。

最终入口WinterWarg/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r02_full_actor_20261029/review.json、gif_archive_verification_20261029.json、gif_quantization_fix_art_r02_20261029.json、unity_release_final_20261029.json、runtime_summary.json、record_note_utf8.txt。audit和seal已完成，不重跑。接棒前重新动态核对Unity2022.3.62f3c1/E:/MyTowerGame/8088，clean Boot非Play，failed/compile/reload/update/test/review/recording/balance/manual均false、ready=true、external_changes_dirty=false，error/errorCS0，旧错误未清。

下一WinterWolfTypeA仅reference8文件，六保护匹配，父没有审源图或生成/暂存/安装/运行。请独立读Dogs/WinterWolfTypeA完整原atlas/prefab、四腿/Tail/Head/锚点与Wolf动画，不复制WinterWarg布局。用户先前明确要求控制桌面前询问；文件/命令行与Unity MCP仍可用。新token {token}。完整prompt {rel(prompt_path)}；assessment {rel(assessment)}；释放 {rel(release)}。先handoff_ready再现场list_projects，唯一fresh local create_thread，不fork/子代理/并行/定时器/模型覆盖。明确成功响应先落盘，父最后工作区写入active新owner/token，之后父只读。
'''
handoff.write_text(summary,encoding='utf-8')

prompt=f'''在 E:/MyTowerGame 继续敌人四方向续作，只负责 WinterWolfTypeA(index113)。这是用户已授权的逐角色串行循环接棒；完成一个角色后总结、更新完整prompt并主动创建唯一下一全新本地聊天，不逐角色再次请求确认。父线程 {OWNER}。本次dispatch_token：{token}。

先完整读取以下现场文件，路径以 E:/MyTowerGame 为根：
1. AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
3. Docs/EnemyDirectionReview/Remaining_20261024/CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md。
4. Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md、conversation_chain.json、progress.json。
5. Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
6. {rel(handoff)}。
7. {rel(assessment)}、{rel(dispatch_path)}。
8. 现有character_step.py、prepare_character.py、generate_character.ps1/generate.mjs、pack_character.py、adjust_layout.py、install_character.py、runtime_runner.py/runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py，local_baseline.json/production_fingerprints_before.json、首批Batch01_10/user_approval_20261023.json与AllGIF/manifest.json，以及当前角色实际文件；只针对当前角色扩展调用/依赖/生命周期检查。

所有权：先核链state=active、owner_thread_id等于新聊天实际CODEX_THREAD_ID、current_character=WinterWolfTypeA、dispatch_token精确匹配后才允许生产修改或Unity操作。新聊天可能在父登记前启动；handoff_ready期间只做独立只读同步，分段等待，不超时抢锁、不改链、不另建后继。父响应落盘或转移失败时报告准确现场。父转移成功后停止所有工作区写入。

实时进度101/108。WinterWarg112最终art_r02已record，completed_pending_user_art_review、user_approved=false；两轮168PASS0FAIL/679真实PNG。余7项：PossessedWarg79旧Down结果不明blocked；WinterWolfTypeA113、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118六项not_started。不要盲用progress.current和旧快照，不把Zombie118误作108项以外。WinterWolfTypeA目前只有reference8文件及调度材料；父仅核六保护，未审源图、未prepare/生成/暂存/安装/运行。

当前角色路径：battle={t['battle']}；source={t['source']}；atlas={t['atlas']}；controller={t['controller']}；Directions={t['art_dir']}。先实际查看完整原atlas、source prefab和battle层级、Body/Head/四腿/Tail/耳与锚点，检查真实原float/PPtr曲线、头事件/攻击/移动/回收/复用及clip时长/loop。制定自身解剖、正背面和步态，不套WinterWarg图案或布局。读取现有git状态和差异，建立Assets/Packages/ProjectSettings/Luban完整路径SHA增量基线及battle/source/atlas和各meta六保护，新增/删除按路径并集审计；不以Git HEAD重置历史或用户变更。

实际Unity路由为2022.3.62f3c1 / unityMCP / http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082为旧信息，8082现属D:/FishTestGame，不操作其他工程或改写根规则。先读mcpforunity://custom-tools和instances，动态发现完整MyTowerGame ID、set_active_instance，再project/info核E:/MyTowerGame及版本；每次重连/域重载重核。桌面MCP握手问题可审阅复用现有mcp_call.py Client.identity()直接HTTP8088，保持动态核对/loopback禁代理。离线按规则自主恢复已有服务/桥接，不抢占端口/杀进程；需要桌面控制时先问用户，用户明确要求未经询问不控制桌面。本任务自身两轮真实Play已有授权，先读目标错误日志、editor/state与占用，禁止强停他人任务/录像或覆盖脏场景。

逐阶段完成：参考/解剖/prompt实审 → 仅确实缺少且无在途或结果不明请求时首次生成Up并实际看raw → 首次Down并实审 → 透明分件/Atlas/Pivot/PPU/布局/离线组合实审 → 单角色Builder安装/Verify → 最终生产版本两轮真实Play（普通死亡与指定Up死亡，每轮84PASS0FAIL）→ 足够时序PNG/最终GIF编码帧实审 → record → 全部GIF源/集中副本SHA核对 → 总结/完整后继prompt/唯一新聊天。各阶段落盘实际revision、运行计数、指纹和阻断。程序PASS仍有视觉问题必须保留旧版本修复并使用新runtime revision，不能删除installed_manifest绕保护。

所有pipeline Python必须用 C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8，子进程沿用sys.executable；PATH Python3.13 isolated会使install找不到mcp_call，不使用。PowerShell中文长备注写UTF8文件后读取传参，勿把JSON.stringify当shell转义。

仅当前角色尚未prepare时入口character_step.py prepare WinterWolfTypeA，先核不会覆盖现存材料。图像任务先读imagegen SKILL.md，沿用已授权AIHub https://aihub.dog/v1 与既有生成器，默认gpt-image-2/medium/n1/1536x1024，优先现有Curl传输和Preflight。密钥仅运行时从环境或DPAPI clixml读取，只发送aihub.dog，不输出/落盘明文、不跨域携带。保留原request/raw/result/uncertain/错误，先查在途及已有结果，禁止盲重发。失败区分鉴权/余额/上游/网络/结果不明，不能认定未计费；不改系统代理。standing_recovery仅在确实适用时读取原用户证据、核当前角色范围和计数，不把前角色计数清零，不把代理保守max说成用户预算。WinterWarg两旧Up不明和2/2已消耗，两个HTTP200不证明旧请求免费；前任WinterOgre五不明亦保留。

stage入口character_step.py stage WinterWolfTypeA。实际审Up/Down完整raw、14或按实际需要的分件、透明背景/底色污染/描边/孔洞/Atlas切片/PPU/pivot/渲染顺序与离线四向。原颜色/材质/脸/毛/器官/尾根保持，Up纯后脑无脸与正确后跟，Down正确脸/脚趾，肩髋与尾根连接；左右保留原侧图，四向及攻击/受击/死亡/复用均无地面阴影。测量矩形可跨名义行界，不为模板删掉实际器官；局部raster修补记录来源/范围/哈希，保留旧raw。不得对已清理暂存无条件重跑prepare/full stage。

安装前核生产指纹、六保护、Unity身份及空闲；Directions.meta在目录外，prePlay指纹务必单列。有installed_manifest就走真实恢复/返修路径不删清单；保存最终生产全指纹再两轮实际Play。保存actual_frames.jsonl/actual_runtime_checks.txt/全部PNG/真实Unity帧号/normalizedTime/realtime及SHA，运行后安全恢复原场景。覆盖四向步态、纯纵向与斜向滞回、近零保持、连续转向相位、原生状态和头事件、攻击/受击与致死白闪结束、完整死亡旋转收缩淡出、自动回收及同实例复用、暂停恢复及1x2x3x和适用飞行；不以手动Animator.Update或离线合成冒充Play。

先读取当前角色原Walk长度。build_runtime_media.py可能写死0.5s，即使原生正好0.5s，GIF逐帧非10ms时长仍会截短；实际解码累计时长并与原clip/真实相位核对。必要时仅在当前角色Docs保留修前GIF，用累计时间量化到GIF10ms精度，不合成姿态或改共享脚本，准确记录量化差。WinterWarg原Walk0.5s的六GIF从480/490修500ms；不要照抄WinterOgre670ms。

C#如需最小修改先读实现/调用/生命周期，同批全部完成后8088 MCP refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，1–2秒轮询compile/reload/update=false和ready=true，read_console(error/errorCS)及scriptCompilationFailed=false，错误修复重跑；编译中不继续写代码，断线先等约5秒再重连重核，保留历史错误不清控制台。没有UnityC#改动不为收尾额外改脚本或请求编译。

实际查看最终两轮four_directions、runtime strip、足够真实时序原PNG及全部最终GIF编码帧，1–2图片/次、原件留盘；无法实时播放则如实抽样记录范围，不声称播放或全帧通过。完整角色不能被审图crop裁耳/足/尾而不知；必要时另看未裁切native PNG与GIF整帧。runtime_summary必须绑定最终生产版本且168PASS0FAIL才record，actual视觉备注UTF8写record_note_utf8.txt再调用现有record流程。最终只能completed_pending_user_art_review和user_approved=false，用户明确批准才可批准。

record_review.py调用collect_gifs.py归档所有现存GIF，核当前角色全部源和副本SHA，分清当前与历史；不要固定每角色12或固定总数。当前AllGIF1642含WinterWarg30=12最终+12否决art_r01+6旧时长。最终本角色完整路径并集审计只允许当前prefab/Directions含根meta与确证未改ReporterEditor产生的build_info时间戳，核原prefab语义/GUID/root/HP/锚点/移动战斗/原动画合同/导入/依赖/现有收集器；历史全局scope失败保持，不声称全局通过或发布包回读。

WinterWarg最终入口：WinterWarg/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r02_full_actor_20261029/review.json、gif_archive_verification_20261029.json、gif_quantization_fix_art_r02_20261029.json。最终两轮340+339=679真实PNG/168PASS0FAIL；12板268采样位254不同PNG、8完整原PNG、60编码GIF帧和4整帧，非实时/全审。5565→5585文件，22变化20新增0删除unexpected0，含根meta/Reporter时间戳；源/meta/共享C#无漂移、原prefab语义PASS。art_r01两轮678PNG仅历史否决；旧裁耳板和时长失败证据均保留。不要运行前任prepare/stage/install/finalize脚本，不重发或删任何旧请求。

边界：不git pull/reset/clean/checkout覆盖，不commit/push，不构建/部署，不删除资源/场景，不改Luban/Config/Datas/Levels/**、EnemyData.xlsx、__tables__.xlsx，不直接写Assets/ConfigJson或Gen，不恢复声音，不建子代理/fork/并行角色/定时器/自动化，不改长期memory，不覆盖模型或推理设置。后继prompt交付完整UTF8可一次复制文件，不用占位符或省略段落。

完成WinterWolfTypeA或准确记录真实阻断后，先安全交回Unity，重读实时items优先可恢复已开始项，再选最低index独立未开始项（正常应WinterWolfTypeB114），PossessedWarg无新恢复证据继续保留。新建带时间总结，更新README/live executable prompt、完整NEXT_ENEMY_TASK和progress；chain=handoff_ready并产生唯一新token。现场list_projects确认E:/MyTowerGame，唯一create_thread(target={{type:"project",projectId:现场ID,environment:{{type:"local"}}}},prompt:完整新提示)，不fork/不model/thinking覆盖。保存明确成功响应后以父最后工作区写入转移active新owner/token，之后父只读，一次有界wait_threads确认启动，最终给真实::created-thread。创建不明先查返回/实际聊天，不能再盲创建；失败保留完整交接如实报告。循环到108有效完成或只剩真实阻断，不逐角色再等用户确认。
'''
prompt_path.write_text(prompt,encoding='utf-8')
(H/'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 WinterWolfTypeA(index113)\n\n'+prompt,encoding='utf-8')
live_text=f'''2026-10-29 WinterWarg112已record，101/108，art_r02，completed_pending_user_art_review、user_approved=false。最终runtime_art_r02/runtime_art_updeath_r02两轮340+339=679真实PNG、168PASS0FAIL；实审四向/strip、12板268采样位254不同PNG、8原PNG、12GIF的60编码帧与4整帧，非实时播放/逐帧全审。Up后脑短冠毛/光滑后跟、白赭棕刺四足长尾，art_r02放大轴向头，art_r01运行否决保留。14分件/2048atlas/PPU100，alpha补793小洞/去4尘点，无封闭洞/不透明品红。六行走GIF累计量化修500ms，原六保留。AllGIF1642，本角色30=12最终+12旧art_r01+6旧时长，全SHA一致。旧2次Up结果/费用不明、standing恢复2/2已消耗保留；Up02及首次Down HTTP200、实际选本地Up05/Down原件。完整路径并集5565→5585，22变化20新增0删除unexpected0，含Directions根meta和确证Reporter时间戳；本角色语义PASS、源/meta与共享C#无漂移；历史全局失败未重审。Unity2022.3/8088正确身份、clean Boot非Play/全空闲/failed=false/ready=true/error与errorCS0。最终WinterWarg/final_validation_20261029.json；交接{rel(handoff)}。下一唯一WinterWolfTypeA113 not_started/reference8，token={token}；PossessedWarg旧blocked及113–118六项未开始。完整入口NEXT_ENEMY_TASK.md。'''
for path,begin,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),
                       (H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=path.read_text(encoding='utf-8-sig');pattern=re.escape(begin)+r'.*?'+re.escape(end)
    assert len(re.findall(pattern,text,re.S))==1
    text=re.sub(pattern,lambda _:begin+'\n'+live_text+'\n'+end,text,flags=re.S)
    if path.name=='README.md':
        text,count=re.subn(r'\d{4}-\d{2}-\d{2} 本轮当前清单为 \d+ 个文件','2026-10-29 本轮当前清单为 1642 个文件',text);assert count==1
    path.write_text(text,encoding='utf-8')
done['handoff_file']=handoff.relative_to(H).as_posix();progress.update(current=NEXT,updated_at=now());write(H/'progress.json',progress)
dispatch={'prepared_at':now(),'created':False,'parent_thread_id':OWNER,'character':NEXT,'character_index':113,
    'dispatch_token':token,'project_root':'E:/MyTowerGame','project_id':None,'project_live_confirmed':False,'project_association_confirmed':False,
    'handoff_file':rel(handoff),'handoff_sha256':sha(handoff),'assessment_file':rel(assessment),'assessment_sha256':sha(assessment),
    'unity_release_file':rel(release),'unity_release_sha256':sha(release),'prompt_file':rel(prompt_path),'prompt_sha256':sha(prompt_path),
    'next_task_file':rel(H/'NEXT_ENEMY_TASK.md'),'next_task_sha256':sha(H/'NEXT_ENEMY_TASK.md'),'progress_sha256':sha(H/'progress.json'),
    'response_file':rel(N/'successor_creation_response_20261029.json')}
write(dispatch_path,dispatch,True)
assert not any(i['character']==NAME for i in chain.get('completed_handoffs',[]))
chain.setdefault('completed_handoffs',[]).append({'character':NAME,'status':done['status'],'current_stage':'recorded_pending_user_art_review',
    'closed_at':now(),'owner_thread_id':OWNER,'dispatch_token':TOKEN,'handoff_file':rel(handoff),'final_evidence':rel(D/'final_validation_20261029.json')})
for key in ['resume_conditions','current_turn_resume_file','previous_resume_authorization','closeout_receipt_file']:
    chain.pop(key,None)
chain.update(state='handoff_ready',parent_thread_id=OWNER,current_character=NEXT,dispatch_token=token,character_status_at_handoff='not_started',
    completed_count_snapshot=101,previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),
    successor_assessment=rel(assessment),progress_sha256_at_handoff=sha(H/'progress.json'),unity_release_file=rel(release),
    prepared_dispatch_file=rel(dispatch_path),creation_response_file=dispatch['response_file'],dispatch_ready_for=NEXT,successor_created=False,
    current_stage='handoff_ready_pending_single_successor_creation',resume_character=NEXT,
    resume_stage='Verify owner/token; independently inspect WinterWolfTypeA source and Wolf native contract; establish baseline',
    handoff_ready_at=now(),updated_at=now())
write(H/'conversation_chain.json',chain)
print(json.dumps({'state':'handoff_ready','character':NEXT,'dispatch_token':token,'dispatch_file':rel(dispatch_path),
    'prompt_file':rel(prompt_path),'handoff_file':rel(handoff),'safe_to_handoff':True},ensure_ascii=False))
