# 后续 10 个敌人审核材料

已按文件名顺序接入 Bat 至 BoarMounted，并完成逐个真实 Play 验收与画面检查。AdvancedHen 的共享代码回归也已完成。本批之后是 `Enemy_BugQueen.prefab`，未接入。

已明确交回 Unity 给并行数值任务，此后固定 Assets、Packages、ProjectSettings、Luban。交回记录及清单 SHA256 见 [unity_return.json](unity_return.json)。结束时 Boot 场景干净、非 Play、两个测试器未运行；编译/域重载/导入均结束，ready=true，脚本编译失败=false，控制台错误/警告=0。状态资源最初缓存过期，原响应与短探针均保留；调用插件既有采样方法读取实际状态后得到 is_stale=false、age_ms=90，未修改插件或业务代码，也未额外切换 Play。

每项 84 PASS：四向实际位移、首段/重复节点、滞回、镜像、原生攻击表情事件、Idle/Ready/Walk/Run、受击白闪、致死闪白消退、全身淡出收缩、自动入池并取回同实例、跨帧暂停、1/2/3 倍速、连续转弯和飞行直线。测试使用临时未保存场景及内存配置，媒体来自真实 Unity 帧；无手动 Animator.Update 采样媒体。

|角色|四向|上下行走|转向|攻击/死亡/复用|实测|
|---|---|---|---|---|---|
|Bat|[PNG](Bat/runtime_r02/four_directions.png)|[GIF](Bat/runtime_r02/up_down_walk.gif)|[GIF](Bat/runtime_r02/walk_turn.gif)|[GIF](Bat/runtime_r02/attack_death_reuse.gif)|[84 PASS](Bat/runtime_r02/actual_runtime_checks.txt)|
|BattlePanther|[PNG](BattlePanther/runtime_r01/four_directions.png)|[GIF](BattlePanther/runtime_r01/up_down_walk.gif)|[GIF](BattlePanther/runtime_r01/walk_turn.gif)|[GIF](BattlePanther/runtime_r01/attack_death_reuse.gif)|[84 PASS](BattlePanther/runtime_r01/actual_runtime_checks.txt)|
|Bear|[PNG](Bear/runtime_r01/four_directions.png)|[GIF](Bear/runtime_r01/up_down_walk.gif)|[GIF](Bear/runtime_r01/walk_turn.gif)|[GIF](Bear/runtime_r01/attack_death_reuse.gif)|[84 PASS](Bear/runtime_r01/actual_runtime_checks.txt)|
|BearMounted|[PNG](BearMounted/runtime_r01/four_directions.png)|[GIF](BearMounted/runtime_r01/up_down_walk.gif)|[GIF](BearMounted/runtime_r01/walk_turn.gif)|[GIF](BearMounted/runtime_r01/attack_death_reuse.gif)|[84 PASS](BearMounted/runtime_r01/actual_runtime_checks.txt)|
|BlackBear|[PNG](BlackBear/runtime_r01/four_directions.png)|[GIF](BlackBear/runtime_r01/up_down_walk.gif)|[GIF](BlackBear/runtime_r01/walk_turn.gif)|[GIF](BlackBear/runtime_r01/attack_death_reuse.gif)|[84 PASS](BlackBear/runtime_r01/actual_runtime_checks.txt)|
|BlackBoar|[PNG](BlackBoar/runtime_r01/four_directions.png)|[GIF](BlackBoar/runtime_r01/up_down_walk.gif)|[GIF](BlackBoar/runtime_r01/walk_turn.gif)|[GIF](BlackBoar/runtime_r01/attack_death_reuse.gif)|[84 PASS](BlackBoar/runtime_r01/actual_runtime_checks.txt)|
|BlackWolf|[PNG](BlackWolf/runtime_r01/four_directions.png)|[GIF](BlackWolf/runtime_r01/up_down_walk.gif)|[GIF](BlackWolf/runtime_r01/walk_turn.gif)|[GIF](BlackWolf/runtime_r01/attack_death_reuse.gif)|[84 PASS](BlackWolf/runtime_r01/actual_runtime_checks.txt)|
|BlueScorpion|[PNG](BlueScorpion/runtime_r01/four_directions.png)|[GIF](BlueScorpion/runtime_r01/up_down_walk.gif)|[GIF](BlueScorpion/runtime_r01/walk_turn.gif)|[GIF](BlueScorpion/runtime_r01/attack_death_reuse.gif)|[84 PASS](BlueScorpion/runtime_r01/actual_runtime_checks.txt)|
|Boar|[PNG](Boar/runtime_r01/four_directions.png)|[GIF](Boar/runtime_r01/up_down_walk.gif)|[GIF](Boar/runtime_r01/walk_turn.gif)|[GIF](Boar/runtime_r01/attack_death_reuse.gif)|[84 PASS](Boar/runtime_r01/actual_runtime_checks.txt)|
|BoarMounted|[PNG](BoarMounted/runtime_r01/four_directions.png)|[GIF](BoarMounted/runtime_r01/up_down_walk.gif)|[GIF](BoarMounted/runtime_r01/walk_turn.gif)|[GIF](BoarMounted/runtime_r01/attack_death_reuse.gif)|[84 PASS](BoarMounted/runtime_r01/actual_runtime_checks.txt)|

AdvancedHen 回归：[四向](AdvancedHen/runtime_r01/four_directions.png)、[行走](AdvancedHen/runtime_r01/up_down_walk.gif)、[84 PASS](AdvancedHen/runtime_r01/actual_runtime_checks.txt)。原 R3 证据完整保留。

## 范围与实现

仅改动本批 10 个战斗 prefab，其他 109 个（含 AdvancedHen 和 BugQueen）与修改前本地基线逐字节相同。原图、源 prefab、共享动作与现有 GUID 无漂移；逐组件 YAML 审计确认根变换、原碰撞/战斗组件、血条、锚点及事件接收引用保持。删除仅限当前战斗 prefab 的 Shadow。

公共扩展仅修改 EnemyDirectionalProfile、EnemyDirectionalVisual、EnemyDirectionPrefabBuilder，新增 EnemyDirectionalRigBuilder 与 EnemyDirectionBatchReview。角色使用独立正背分件、专用控制器和动作副本；原侧面曲线/事件/时长保留。复用既有闪白材质，不实例化材质；Bat 用 forceRenderingOff 门控保留原 enabled 翼姿动画。旧 AdvancedHen 分支维持原逻辑。

单例接入入口：选中一个已授权的战斗 prefab，执行 `Tools/塔防/敌人方向批次/接入选中的单个战斗预制体`；或 `EnemyDirectionalRigBuilder.Build("Bat")`（替换成表中单个名称）。缺真实图集/切片/解剖部件即失败，不支持全目录批量重建。各角色 `installed_verify_r01.txt` 记录两次克隆重建钩子、依赖、Missing 脚本、原曲线事件和现 YooAsset 收集覆盖；真实重复导入的 `.meta` 稳定性另有记录。

## 指纹和异常

- [前后 SHA256 与精确实现清单](implementation_manifest.json)
- [最终冻结指纹](final_frozen_fingerprints.json)
- [119 个 prefab 范围及语义审计](scope_final.json)
- [移交时 9304 文件边界审计](handoff_boundary_audit.json)
- [进度与逐角色画面记录](progress.json)

Bat runtime_r01 的旧式重复节点回归断言只 Tick 一次，尚未越过重复点，出现一项 FAIL。审核工具改为四次 Tick，未改 BaseEnemy；runtime_r02 为最终 84 PASS。原失败记录保留。后续使用修正后的工具。

所有角色目录保留 reference、原始生成返回、提示词/请求/结果、去底切片过程及 staged_art。`offline_*`、CPU 拼装图只供草稿检查，不是运行证据。最终运行目录包含原始 768px PNG、严格递增 Unity 帧号日志、状态/相位/时间/血量和全部衍生媒体来源。

BlueScorpion 沿用原图的金黄色身份与透镜眼，六步足/双钳/分节尾；BearMounted、BoarMounted 沿用只有鞍具没有骑手的设计。野猪为短腿圆胖体型。所有最终角色四向、死亡及复用后均无地面阴影。

未执行 APK/真机、发布包构建回读、完整关卡或长期战斗。本批只完成资源依赖/现有收集覆盖，数值任务最终严格复跑由其原任务在交回后执行。Unity 编译与结束状态详见 [editor_validation.json](editor_validation.json)。
