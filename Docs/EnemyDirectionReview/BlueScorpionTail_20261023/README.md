# BlueScorpion 朝上尾巴位置修正 · 2026-10-23

当前状态：已安装并完成实际运行检查，等待用户美术审核，停在 BlueScorpion。

尾根从靠近头胸的位置移到腹部末端，并由腹部遮住连接处；尾弧向身后展开。只调整 Up/Tail 分件的局部轴点、位置、角度和尺寸，重新生成对应专用动画。原 PNG 不变，也没有旋转整个角色来替代方向设计。

## 查看效果

- [实际行走前后对照 GIF](tail_before_after.gif) / [静态对照](tail_before_after.png)：左侧是本次修改前的 runtime_polish_r01，右侧是修正后的 runtime_tailfix_r01。
- [修正后朝上行走](up_walk_fixed.gif) / [六个相位](up_walk_fixed_phases.png)。
- [朝上攻击](up_attack_fixed.gif) / [攻击相位](up_attack_fixed_phases.png)。
- [朝上死亡](up_death_fixed.gif) / [死亡相位](up_death_fixed_phases.png)。
- [四方向完整实际帧](../Batch01_10/BlueScorpion/runtime_tailfix_r01/four_directions.png)、[连续转向](../Batch01_10/BlueScorpion/runtime_tailfix_r01/walk_turn.gif)、[上下攻击、受击、朝下死亡和回收复用](../Batch01_10/BlueScorpion/runtime_tailfix_r01/attack_death_reuse.gif)、[暂停及倍速](../Batch01_10/BlueScorpion/runtime_tailfix_r01/pause_speed.gif)。

媒体全部来自最终安装资源的真实 Unity Play 帧。前后取相近的原生行走相位，并使用未改动的 HP 条宽度统一世界比例、对齐 HP 中心；只做裁切、等比缩放和文字排版，没有合成姿态。不同版本的原始取景范围略有变化，不直接比较未经比例校正的像素尺寸。focused_media_manifest.json 记录每个输出使用的原始文件、Unity 帧号、动作相位和缩放比例。

已逐相位查看行走、朝上攻击与死亡的真实图像：尾根保持在腹部后端，攻击时跟随身体，死亡时随全身倾倒、收缩和淡出。程序检查不代表用户美术批准。

## 改动与范围

只修改 BlueScorpion 朝上尾巴：布局 x=0、y=0.59736、width=1.86368、height=3.02848、angle=180、order=15；Up_Tail pivot 从 (0.5, 0.05) 改为 (0.4, 0.1)，尺寸为此前的 80%。其他方向和其他分件布局保留。

生产变更共 9 文件，完整路径和前后 SHA256 见 implementation_manifest.json：

1. Assets/Prefabs/Enemy/Enemy_BlueScorpion.prefab
2. Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions/BlueScorpion_Directions.layout.json
3. Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions/BlueScorpion_Directions.sprites.json
4. Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions/BlueScorpion_Directions.png.meta
5. Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions/Animations/Ready_Directions.anim
6. Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions/Animations/Walk_Directions.anim
7. Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions/Animations/Attack_Directions.anim
8. Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions/Animations/Death_Directions.anim
9. Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions/Animations/BlueScorpion_Directions.controller

修改前 11539 文件基线与上一轮最终身份零漂移，并保存完整 C# 原文和角色方向资源备份。此次全部 C#、原始 PNG、源 prefab、其他 118 个战斗 prefab、配置表、导出数据和正式场景均与本次基线逐字节相同。GUID 和 Sprite ID 保留。四个专用动作逐绑定对比，仅 DirectionVisual/Up/Motion/Tail 的位置和角度曲线变化，Down 和其余分件曲线完全保留。scope_audit.json 为本次独立边界审计。

原根节点、碰撞、移动/战斗参数、血条和无关组件通过十角色原始 prefab 语义核对，见 ../Batch01_10/scope_tailfix_r01.json。该文件相对最初接入基线列出的三个代码漂移属于此前接入；本次独立基线无任何 C# 变化，不能将旧漂移算成本次修改。

## 实际检查

Unity 2022.3.62f3c1，E:/MyTowerGame，unityMCP / 8082。资源应用后已完成 force/all/request 刷新与编译，域重载后重新选定现场实例并核对工程。最终 compilationFailed=false，控制台 error/warning=0，compiling/reload/updating=false，ready_for_tools=true。

| 本次 revision | 实际检查 | 原始帧 | 死亡方向 |
|---|---|---|---|
| runtime_tailfix_r01 | 84 PASS / 0 FAIL | 340 | Down |
| runtime_tailfix_updeath_r01 | 84 PASS / 0 FAIL | 341 | Up |

共 168 PASS / 0 FAIL、681 个严格递增真实 Unity 帧；两轮均无 exception。覆盖实际四向位移、朝向/相位、状态与头事件、白闪、全身淡出/收缩、自动回收与同实例复用、暂停、1/2/3 倍速、连续转弯和飞行直线移动。原始帧和 actual_runtime_checks.txt 在上述两个独立 revision 目录中。

installed.txt 记录依赖与 YooAsset 收集、侧面动作/事件/时长保留、Missing 检查、两次临时克隆重复接入、单一方向层、无 Shadow、根/HP/事件接收引用保持。最终已退出自己的 Play，恢复 Boot.unity，场景 clean，balance/review/manual simulation 均为 false；详见 editor_validation.json。Unity 已释放。

未执行 APK/真机、发布包构建/回读、长期战斗或完整数值回归。依赖收集检查不代表发布包验证。本次无需重新生图，没有调用 Image API。

## 备份、复现与下一步

before/ 保留本次修改前方向资源和战斗 prefab；baseline.json、source_snapshot.json 保存本地基线。prepare.py 会拒绝覆盖基线，请勿重复运行。layout_proposal.png 仅为离线布局预演，不作为实际效果证据。

在正确工程 idle、场景已保存且没有其他任务使用 Unity 时，可单独执行 FTProject.EditorTools.EnemyDirectionalRigBuilder.Build("BlueScorpion")。实际审核入口为 FTProject.EditorTools.EnemyDirectionBatchReview.Start("BlueScorpion", "一个未使用过的revision")，第三参数 true 用于朝上死亡；不要重复使用已有 revision，不运行全量构建。

上一批 Batch01_10 的 implementation_manifest.json / final_frozen_fingerprints.json，以及上一轮 AnimationPolish_20261023 的身份文件均保留。progress.json 记录本次最终文件身份、历史身份核对和审核状态。当前等待本角色反馈，未启动后续角色。
