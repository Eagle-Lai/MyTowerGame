# 下一唯一角色 WinterWolfTypeA(index113)

在 E:/MyTowerGame 继续敌人四方向续作，只负责 WinterWolfTypeA(index113)。这是用户已授权的逐角色串行循环接棒；完成一个角色后总结、更新完整prompt并主动创建唯一下一全新本地聊天，不逐角色再次请求确认。父线程 01a186cb-e01e-72b2-ad8b-f5a5b86bfd1f。本次dispatch_token：winterwarg-to-winterwolftypea-20261029_173527-8e8dd053-9008-4a8f-b69a-61a589f400a4。

先完整读取以下现场文件，路径以 E:/MyTowerGame 为根：
1. AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
3. Docs/EnemyDirectionReview/Remaining_20261024/CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md。
4. Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md、conversation_chain.json、progress.json。
5. Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
6. Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_173527_WinterWarg_completed.md。
7. Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/successor_assessment_20261029_173527.json、Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/prepared_dispatch_20261029.json。
8. 现有character_step.py、prepare_character.py、generate_character.ps1/generate.mjs、pack_character.py、adjust_layout.py、install_character.py、runtime_runner.py/runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py，local_baseline.json/production_fingerprints_before.json、首批Batch01_10/user_approval_20261023.json与AllGIF/manifest.json，以及当前角色实际文件；只针对当前角色扩展调用/依赖/生命周期检查。

所有权：先核链state=active、owner_thread_id等于新聊天实际CODEX_THREAD_ID、current_character=WinterWolfTypeA、dispatch_token精确匹配后才允许生产修改或Unity操作。新聊天可能在父登记前启动；handoff_ready期间只做独立只读同步，分段等待，不超时抢锁、不改链、不另建后继。父响应落盘或转移失败时报告准确现场。父转移成功后停止所有工作区写入。

实时进度101/108。WinterWarg112最终art_r02已record，completed_pending_user_art_review、user_approved=false；两轮168PASS0FAIL/679真实PNG。余7项：PossessedWarg79旧Down结果不明blocked；WinterWolfTypeA113、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118六项not_started。不要盲用progress.current和旧快照，不把Zombie118误作108项以外。WinterWolfTypeA目前只有reference8文件及调度材料；父仅核六保护，未审源图、未prepare/生成/暂存/安装/运行。

当前角色路径：battle=Assets/Prefabs/Enemy/Enemy_WinterWolfTypeA.prefab；source=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/WinterWolfTypeA.prefab；atlas=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/WinterWolfTypeA.png；controller=Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller；Directions=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/Directions。先实际查看完整原atlas、source prefab和battle层级、Body/Head/四腿/Tail/耳与锚点，检查真实原float/PPtr曲线、头事件/攻击/移动/回收/复用及clip时长/loop。制定自身解剖、正背面和步态，不套WinterWarg图案或布局。读取现有git状态和差异，建立Assets/Packages/ProjectSettings/Luban完整路径SHA增量基线及battle/source/atlas和各meta六保护，新增/删除按路径并集审计；不以Git HEAD重置历史或用户变更。

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

完成WinterWolfTypeA或准确记录真实阻断后，先安全交回Unity，重读实时items优先可恢复已开始项，再选最低index独立未开始项（正常应WinterWolfTypeB114），PossessedWarg无新恢复证据继续保留。新建带时间总结，更新README/live executable prompt、完整NEXT_ENEMY_TASK和progress；chain=handoff_ready并产生唯一新token。现场list_projects确认E:/MyTowerGame，唯一create_thread(target={type:"project",projectId:现场ID,environment:{type:"local"}},prompt:完整新提示)，不fork/不model/thinking覆盖。保存明确成功响应后以父最后工作区写入转移active新owner/token，之后父只读，一次有界wait_threads确认启动，最终给真实::created-thread。创建不明先查返回/实际聊天，不能再盲创建；失败保留完整交接如实报告。循环到108有效完成或只剩真实阻断，不逐角色再等用户确认。
