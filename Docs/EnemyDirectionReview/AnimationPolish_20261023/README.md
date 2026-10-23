# 三个敌人动画返修 · 2026-10-23

当前版本：独立返修，等待用户美术审核。仅 BlackBear、BlackWolf、BlueScorpion；不继续其他角色。

## 查看效果

- [本地动画审核页](preview.html)：上下行走前后对照、上下攻击、上下死亡，以及连续转向、受击、回收复用、暂停与倍速。
- [三个角色行走前后总览](walk_before_after_all.gif)：每行依次为旧 Up、新 Up、旧 Down、新 Down。
- [BlackBear](BlackBear_walk_before_after.gif) / [BlackWolf](BlackWolf_walk_before_after.gif) / [BlueScorpion](BlueScorpion_walk_before_after.gif)。

所有动作媒体均来自安装后真实 Unity Play 帧；原始 PNG、严格递增的 Unity frame、normalizedTime 和运行检查保存在 Batch01_10 对应角色的新 revision 目录。对照仅使用相近原生相位进行裁切、缩放、排版，无合成姿态或手动 Animator.Update 录帧。GIF 末尾可有便于观察的停留。前后行走使用同一裁切和缩放，完整四方向原帧见 runtime_polish_r01/four_directions.png。

## 具体变化

- BlackBear：腿根收进躯干，身体遮住肩胯连接；四拍重步、落足与轻微重心摆动；攻击加入蓄力、前压及左右前肢的时差；死亡侧倒时收拢四肢。
- BlackWolf：交替的对角步态，抬腿绕固定关节收腿，头与身体错相；尾轴改到真实尾根并延迟跟随；攻击加入短促蓄力和扑咬，死亡附肢随身体收拢。
- BlueScorpion：前中后足按自身结构分开朝向和遮挡，交替三足组略有时差；双钳与尾巴独立跟随；攻击先张钳蓄力再合击，死亡收腿收钳并垂尾。

只新增上下方向的角色专用曲线。原侧面 float/PPtr 曲线、事件、时长、循环标记逐项保留；原始图集、源 prefab 和共享动作未改。新增逻辑只在 Editor 生成曲线，不新增运行组件或 Update；沿用已有 Animator、移动和生命周期。运行时、数值、表、碰撞、HP 和正式场景相机均保持原有逻辑。

## 实际验证

Unity 2022.3.62f3c1，正确实例 MyTowerGame / unityMCP / 8082；代码完成后执行 force/all/request 刷新与编译，重连后重新选实例核对工程，最终 compilationFailed=false、控制台 error/warning=0、ready_for_tools=true。最终已退出自己的 Play，恢复 Boot.unity，场景 clean，balance/review/manual simulation 均未运行。

| 角色 | 原生运行与朝下死亡 | 朝上死亡补测 | 最终结果 |
|---|---|---|---|
| BlackBear | runtime_polish_r01 | runtime_polish_updeath_r02 | 168 PASS / 0 FAIL |
| BlackWolf | runtime_polish_r01 | runtime_polish_updeath_r02 | 168 PASS / 0 FAIL |
| BlueScorpion | runtime_polish_r01 | runtime_polish_updeath_r02 | 168 PASS / 0 FAIL |

Bear 作为未修改、同一构建工具覆盖的角色做真实 Play 回归：runtime_polish_regression_r01，84 PASS / 0 FAIL。最终上述 7 次审核合计 588 PASS / 0 FAIL。每次覆盖四方向实际位移与相位、Idle/Ready/Walk/Run/Attack/Death、动画头事件、白闪、死亡淡出收缩、自动入池与同一实例取出、跨帧暂停及 1/2/3 倍速、连续转向、飞行直线和未配置角色抽查。程序检查与逐帧美术审阅分别进行，最终美术批准由用户决定。

每个目标另完成 Verify：实际引用与 YooAsset 收集、原横向动作/事件、缺失脚本、两次临时克隆重复接入、单一 DirectionVisual、无 Shadow、根/HP/事件接收引用保持。见各角色 *_installed.txt。循环首尾位置/角度最大偏差 0.000016，切线最大偏差 0.025，见 loop_seams.txt。

朝上补测的 BlackBear/BlackWolf runtime_polish_updeath_r01 各保留 83 PASS / 1 FAIL：审核工具错误地将预期死亡头固定为 Down；真实帧已有 Up、expression=2。只修正审核预期并以 r02 重跑，三者最终均 84 PASS。旧失败记录未删除，诊断见 updeath_r01_diagnostic.json。没有用失败版本媒体作为最终证据。

## 范围、备份和版本身份

修改前读取本地最新文件，11537 个文件建立独立基线，并保存 265 份 C# 内容快照。与上一批 9611 文件冻结基线现场比较：修改前零漂移；不执行 pull/reset/clean。

本轮生产变化 30 个文件，精确路径、前后 SHA256、字节数见 implementation_manifest.json。战斗 prefab 只有这 3 个变化，其余 116 个逐字节相同；目标原图/源 prefab/共享动作与原 GUID、Sprite ID 保留。原根节点、碰撞、HP、移动/战斗参数及其他无关组件通过原始 prefab 组件语义审核；完整 10 角色审核见 ../Batch01_10/scope_polish_r01.json。

- baseline.json：本次修改前指纹、前一批批准身份及零漂移结果。
- before/：三个角色原方向资源、战斗 prefab 和旧 RigBuilder 的完整副本；source_snapshot.json 保存其余代码原文。
- staged/、stage_layout.py：本次布局与切片轴点方案，离线 layout_proposal 图仅用于预演。
- implementation_manifest.json / scope_audit.json / final_fingerprints.json：本次精确变更、范围审核和当前版本身份。
- progress.json：可恢复状态与最终指纹；旧 Batch01_10 implementation_manifest.json / final_frozen_fingerprints.json 完全保留，不将旧数值实测的冻结身份冒称本次版本。

## 单例复现

在 idle、已交接的正确工程中，用 EnemyDirectionalRigBuilder.Build("BlackBear")、Build("BlackWolf") 或 Build("BlueScorpion") 单独接入；也可选中对应战斗 prefab 使用既有 Tools/塔防/敌人方向批次/接入选中的单个战斗预制体。不运行全目录构建。新增 Editor 曲线逻辑按这三个名字门控，其他角色仍走原曲线生成分支。

真实审核入口 EnemyDirectionBatchReview.Start("BlackBear", "全新且未使用过的revision")；朝上死亡用第三参数 true。替换角色名即可，输出目录拒绝覆盖历史。会建立未保存的隔离 Play 场景，完成后恢复原场景；要求场景已保存、无并行实测或编译。

未执行：APK/真机、发布包构建与回读、完整长期战斗、新版数值套件重跑。YooAsset 收集与依赖检查不代表发布包回读。当前停在这三个角色，等待用户审核。
