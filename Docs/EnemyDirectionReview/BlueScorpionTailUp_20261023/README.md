# BlueScorpion 尾弧朝上修正 · 2026-10-23

状态：已安装，等待用户美术审核。上次将尾巴朝下展开的方案错误，本轮恢复从腹部末端向屏幕上方卷起的姿态；不继续后续角色。

## 实际效果

- [修正后的行走近景](up_walk_close.gif) / [近景静态](up_walk_close.png)。
- [左：上轮错误朝下；右：本轮向上卷起](tail_before_after.gif) / [静态对照](tail_before_after.png)。
- [朝上攻击](up_attack_fixed.gif) / [攻击相位](up_attack_fixed_phases.png)。
- [朝上死亡](up_death_fixed.gif) / [死亡相位](up_death_fixed_phases.png)。
- [行走六相位](up_walk_fixed_phases.png)、[四方向完整实际帧](../Batch01_10/BlueScorpion/runtime_tailup_r01/four_directions.png)、[连续转向](../Batch01_10/BlueScorpion/runtime_tailup_r01/walk_turn.gif)、[攻击受击死亡复用](../Batch01_10/BlueScorpion/runtime_tailup_r01/attack_death_reuse.gif)、[暂停倍速](../Batch01_10/BlueScorpion/runtime_tailup_r01/pause_speed.gif)。

所有动作媒体来自最终安装资源的真实 Unity Play 帧。前后对照以未改动的 HP 条宽度统一世界比例并对齐位置，取相近原生行走相位；近景进一步裁切放大，仅进行排版、文字、等比缩放，没有合成姿态。focused_media_manifest.json 与 close_media_manifest.json 记录原始帧和处理方法。layout_proposal.png / layout_refined.png 是离线方案图，不是运行证据。

已查看行走、攻击和死亡关键相位。尾根在腹部后端，尾巴沿右侧向上卷回，腹部遮住连接处；随动作摆动、倾倒、淡出和收缩。最终美术批准由用户决定，程序检查不代替美术审核。

## 本轮变化

仅调整 Up/Tail：x=0.25、y=0.5、width=2.3296、height=3.7856、angle=0、order=15；Up_Tail pivot=(0.4, 0.04)。恢复原分件的上扬方向和尺寸，尾根继续位于腹部后端。Down 和其他部件布局不变，没有旋转整个角色，没有改 PNG。

本任务写入 9 个生产文件，精确相对路径和前后 SHA256 见 implementation_manifest.json：战斗 Enemy_BlueScorpion.prefab、Directions 中的 layout.json / sprites.json / png.meta、四个角色专用 Ready/Walk/Attack/Death .anim，以及角色专用 controller。四个动作逐绑定比较，仅 DirectionVisual/Up/Motion/Tail 的位置和角度曲线变化。GUID、Sprite ID、侧面动作/事件/时长/循环标记保持。原图、源 prefab、共享动作、其他 118 个战斗 prefab、数值和场景未被本任务改动。

修改前建立 11539 文件本地基线，与上次尾巴版本零漂移；before/ 保存方向资源和战斗 prefab，source_snapshot.json 保存全部 C# 原文。prepare.py 建立基线和初案，refine_stage.py 确定最终遮挡布局，staged/ 为实际应用的两份 JSON。不要重复运行 prepare.py 覆盖基线。

审计发现三个不属于本任务写入的并行变化：Assets/Editor/Balance/BalancePlayModeVerifier.cs、BalanceVideoRecorder.cs 和其 .meta。作者未确认；文件时间在本轮运行期间，本任务未覆盖、还原或修复这些文件。concurrent_observed/、concurrent_balance_diff.txt 保存观察副本；scope_audit_unclassified.json 保留首次未分类结果。scope_audit.json 明列全部观察差异、本任务 9 文件与并行变化，workspace_no_external_drift=false；其 pass 仅表示本任务边界、资源与运行证据通过，不代表整个工作区无漂移。

../Batch01_10/scope_tailup_r01.json 对最初十角色原始 prefab 做语义核对，全部通过：根/碰撞/HP/移动战斗参数等无关结构保持。该旧基线下的历史代码漂移与本轮并行工具变化均不能算作本任务写入。

## 实际运行与编辑器状态

Unity 2022.3.62f3c1，E:/MyTowerGame，unityMCP / 8082。资源应用后完成 force/all/request 刷新编译，重载后重新发现实例、明确选择并核对工程。

| 本轮独立 revision | 结果 | 实际帧 | 死亡方向 |
|---|---|---|---|
| runtime_tailup_r01 | 84 PASS / 0 FAIL | 342 | Down |
| runtime_tailup_updeath_r01 | 84 PASS / 0 FAIL | 335 | Up |

共 168 PASS / 0 FAIL、677 个严格递增真实 Unity 帧，无 exception。原始帧、normalizedTime、真实 Unity 帧号和运行断言保存在 ../Batch01_10/BlueScorpion 对应目录，未覆盖任何旧 revision。检查覆盖四向移动与相位、状态、表情事件、白闪、死亡淡出/收缩、自动回收及同实例复用、真实暂停、1/2/3 倍速、连续转向和飞行直线。

installed.txt 记录依赖收集、侧面曲线/事件保留、Missing 引用、两次临时克隆重复接入、单一方向层/无 Shadow、根/HP/事件接收保持。最终 compilationFailed=false，控制台 error=0；保留 3 条原编辑器代码过时 API 警告和 2 条 MCP WebSocket 重连警告，未清空日志。Boot.unity 已恢复且 clean，playing/compiling/updating/balance/review/manual=false，ready_for_tools=true，详见 editor_validation.json。

未执行 APK/真机、发布包构建回读、长期战斗和数值套件回归。依赖收集不代表发布包验证。本轮没有调用 Image API。

可重复单例接入：FTProject.EditorTools.EnemyDirectionalRigBuilder.Build("BlueScorpion")。实际审核：FTProject.EditorTools.EnemyDirectionBatchReview.Start("BlueScorpion", "全新未使用的revision")，第三参数 true 补查朝上死亡。只在工程 idle、场景已保存并取得使用窗口时运行；不执行全量构建。

历史 Batch01_10、AnimationPolish_20261023、BlueScorpionTail_20261023 的身份文件未覆盖。progress.json 保存最终资源与证据指纹。当前仅等待 BlueScorpion 尾巴效果反馈，Unity 已释放。
