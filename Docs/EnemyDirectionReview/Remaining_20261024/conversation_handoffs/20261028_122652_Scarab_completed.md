# Scarab 完成与 ScarabMounted 唯一串行交接

- 时间：2026-10-28T12:26:53.132076+08:00；实际工程 E:/MyTowerGame，Unity2022.3.62f3c1，unityMCP / HTTP Local8082。根AGENTS中FreedomTower_1/D盘标题为旧文案，不改规则、不转工程。
- Scarab(index92)已安装、Verify、两轮最终真实Play、实际PNG视觉审阅、record和GIF归档；总进度82/108，completed_pending_user_art_review，user_approved=false。
- Up复用revision_01 HTTP200并采用local_raster_revision_01去除错误背面口器；原图保留。Down旧revision_01仍uncertain，未推定未收费、未改分类，原request/console/uncertain哈希已核对。最新用户明确允许同类网络问题静默继续，按standing_network_recovery_authorization_20261028.json在新revision_02只发一次，HTTP200、1446258 bytes。无新付费需求，未查实际账单，不声称具体费用。
- 14分件、放大头部和触角、修正六足根部pivot与三足错相；Up无眼口，Down三表情。后脑下缘补色简洁且有色调过渡，组合大部分被胸甲遮挡；正背更接近轴向俯视，保留给用户美术判断。
- 初轮runtime_r01/runtime_updeath_r01虽168/0、692帧，实际审阅发现死亡后同实例复用的侧身倒置，已内部否决，旧证据不删。源Death把Body z翻到-180而源/copied Walk无Body旋转绑定。side_reuse_repair_r02仅给Scarab自己的Walk副本添加Body x/y/z常量0，不改已有原侧图float/PPtr曲线、事件、时长/loop、共享源动画或C#。Verify再次PASS。全Build会重新生成副本，今后若重建须保留此明确修复；不能用旧安装清单覆盖。
- 最终runtime_r02与runtime_updeath_r02各84 PASS/0 FAIL、346帧，合计168/0、692张真实Unity帧。实际查看最终四方向、strip和10张时序/步态/愤怒板，256采样位、227张不同实际帧。修复后两轮ContinuousTurns左右侧身均直立，头/甲壳/六足连接完整，触角不碰血条；白闪结束、死亡全身倾斜淡出、回收同实例复用恢复、暂停/1x/2x/3x有帧及检查支持；抽样未见地面阴影。未播放GIF全片、未逐张审完692帧。
- 证据：Scarab/installed_manifest.json、side_reuse_repair_r02/repair.json、visual_review_final_r02_20261028/review.json、record_note_utf8.txt、version_binding_final_20261028.json。最终绑定全部实际PNG、records、checks、媒体、所选原图/修补与安装/暂存哈希，漂移0。
- 5178文件前基线并集22项变化、20项新增，生产只当前Scarab战斗prefab和Directions(含目录meta)，Reporter未改代码的Play时间戳单独归因；本角色语义PASS、六保护除授权battle外无drift、unexpected_incremental=[]。全局历史291unexpected及6其他角色语义失败(MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky)仍保留，新增0，不称全局PASS。范围证据Scarab/scope_incremental_final_20261028.json及scope_Scarab_20261028_final.json。
- AllGIF实时1270项，Scarab24项，12个r02为当前审核版本、12个r01为历史；全部来源/归档SHA一致，见Scarab/gif_archive_verification_20261028.json。
- Unity刚经动态实例/路径/版本重核，已回Boot、非Play、全部场景非dirty，编译/更新/录像/审阅/手动模拟无占用、scriptCompilationFailed=false、错误0。释放：Docs/EnemyDirectionReview/Remaining_20261024/Scarab/unity_release_completed_20261028_122652.json。没有桌面控制、共享C#改动、表/ConfigJson/Gen/音频改动、构建部署或Git同步提交。

## 下一唯一角色 ScarabMounted(index93)

dispatch_token：`scarab-to-scarabmounted-dd3da45145854f44998a5b6bdc48d12e`。候选评估：Docs/EnemyDirectionReview/Remaining_20261024/Scarab/successor_recovery_assessment_20261028_122652.json。先等chain.active且owner为新聊天、token/current匹配才能操作生产/Unity。

旧Up明确HTTP402 insufficient_balance，无raw；Down从未请求。anatomy/reference/prompt已备，不重跑prepare、不覆盖旧request/result。六保护指纹现场无drift，无生成/运行/平衡进程占用。Scarab最新Up/Down同服务HTTP200支持一次有界恢复评估，不保证余额或上游持续可用。后继先重看源参考/当前进程及证据，按明确失败恢复路径使用新的revision与intent，先Up单次正式请求，成功并实际审图才继续Down；网络故障按最新standing授权有界恢复，不重复弹确认，鉴权/余额或限额耗尽则真实记录阻断，避免盲目付费探针。

解剖为橄榄赭色甲壳、双触角、橙眼、六足、唯一棕色鞍、无骑手/尾/翅。保持旧battle Head共享Scarab atlas原绑定，不因美术任务修原PPtr。注意同Scarab家族的死亡复用Body倒置；先读本角色源曲线，如需修只给本角色自有Walk缺失旋转增加reset，保留所有已有曲线/事件/时长，再实际运行确认。不得改Scarab或共享动画。

PossessedWarg旧Down仍uncertain，不重发、不改分类；SabretoothTiger旧Down仍uncertain，其一次$0.07专用授权已消耗。没有其他角色生产并行。用户电脑控制限制仍保留：优先目标Unity MCP，如确需桌面控制必须先弹对话确认。

完成或真实阻断后按原prompt及CONTINUATION_PROTOCOL_20261026.md写新完整交接，更新LIVE/NEXT/progress，安全交回Unity，创建唯一全新本地后继。不是fork，不子代理，不改模型，不计时器。创建成功后旧聊天登记新owner/token并立即停止全部工作区/链写入。
