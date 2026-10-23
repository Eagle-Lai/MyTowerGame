# AdvancedHen R3实际验证

环境E:/MyTowerGame、Unity2022.3.62f3c1、unityMCP/8082。现场选定正确实例并核对路径版本；编译/Play域重载后重新选定核对。实际验证日期2026-10-22，交接时间见unity_final_state.txt。

| 实际运行项目 | 结果与证据 |
|---|---|
| 编译 | 强制all刷新并请求编译，compiling/domain_reload/updating全false、ready=true，scriptCompilationFailed=false，控制台error0，未清空日志 |
| 69项检查 | actual_runtime_checks.txt：69 PASS/0 FAIL；重跑R2检查，替换旧阴影alpha断言为复用无Shadow，再增加4向无Shadow |
| 四向 | 实际位移、单一身体、上下清旧镜像、ArtFaceLeft兼容、血条正向、翼腿层级/接地点检查通过 |
| 路径 | path_refresh_checks.txt：纯纵向出生、重复/近零节点、未来横向段不抢出生朝向、刷新后Left且Walk相位保持 |
| 状态事件 | Idle/Ready/Walk/Run/Death、Speed、Attack及既有Action契约，正常/愤怒/死亡头匹配，Attack后返回Walk与正常头 |
| 受击/死亡 | HP与血条更新，真实MPB白闪及致死时到期消退，全身淡出收缩、方向死亡头；动作帧重新采集 |
| 自动回收复用 | action_pool_checks.txt：Up/Down自动回收后取回同一实例、恢复正常头和身体alpha；69项另测复用不恢复Shadow |
| 暂停/倍速 | pause_speed_checks.txt：独立调用跨真实帧观察暂停位置/相位不变，恢复后2x/3x推进；不是性能基准 |
| 飞行与旧敌人 | 飞行Up直线出生/位移；未启用Bat保留旧行为，未改其prefab |
| 无阴影与重应用 | 4向均无Shadow；reapply_check.txt：源prefab临时克隆连续两次Apply，只有1方向组件，Shadow为0；克隆不保存 |
| 美术采集 | 当前真实Play中重采四向、10+10上下循环、180转弯、128动作PNG；检查尾羽连接/遮挡及死亡，不用离线草图充当结果 |
| 依赖 | dependencies.txt和collector_coverage.txt本轮重新运行，当前非C#依赖全部被现有YooAsset收集覆盖；无发布包构建 |
| 范围/语义 | 119个prefab仅AdvancedHen改变；删除Shadow三组件后，36个非DirectionVisual组件语义一致，运行脚本3个逐字节不变 |
| 退出/移交 | Boot dirty=false，playing/compiling/updating/failed/otherVerifier均false；error0、ready=true后正式交还并行任务 |

## R3追加验证与制作

本轮仅修改2个Editor脚本及示例美术/重建资源，BaseEnemy、EnemyDirectionalVisual、EnemyDirectionalProfile均与R2逐字节相同。原图/源prefab/共享Rooster和战斗prefab GUID保持不变；战场机位、碰撞、移动参数、血条与配置表未变。R2记录中的旧阴影透明度检查在本轮被替换，不再需要阴影淡出或恢复。

- 图像生成：读取imagegen技能后，使用用户授权AIHub gpt-image-2编辑一次、n=1、medium，HTTP200。prompt_tail.txt、输入/输出、request/result摘要均在revision_03。请求1024方图，实际返回1254方图，按实际尺寸去底。未存密钥。
- 尾羽：米白分层羽毛、赭色根部、粗黑重叠线，置于后躯中央，下缘仍遮腿根。合入原Up_Body切片，没有新增部件查找/渲染器/动画事件；现有身体动画和死亡透明度直接承接。
- 图集范围：revision_03/atlas_scope.json确认只改变Up_Body，其余11切片像素完全不变；全部12rect/pivot/PPU不变。
- 全方向去阴影：Builder在编辑期删除Shadow节点，当前prefab四向均不存在；四向显示与对象池复用中分别断言通过。源prefab临时克隆连续两次Apply后仍无Shadow、只有1个方向组件；未保存克隆或处理其他敌人。
- 当前四向PNG、10+10行走循环帧、180转弯帧及128动作帧全部重新采集。最终查看背向尾羽、正面脚位、转弯和死亡关键帧，不使用离线草图代替运行结果。
- 后续规则：所有敌人逐个完成方向适配时都移除全部方向地面阴影，本轮尚未修改其他118个；用户仍未批准批量。

历史R2材料与实现备份位于history/revision_02；其中关于R2生图、翼腿修复和旧阴影的描述只用于追溯，当前效果以上述R3及新采集为准。APK/真机/发布包及全关卡边界仍未验证。
