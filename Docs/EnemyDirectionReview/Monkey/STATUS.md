# Monkey 上下方向接入进度

状态：v2 完成（2026-10-17）。分件美术重生成（无尾躯干）、**真实动画控制器**（含 WalkUp/WalkDown 状态 + Dir 参数）、Play 模式端到端验证通过，控制台 0 错误。等待用户美术审核；真机验证需按热更三件套重打 dll/AB。

## 产物

- 分件美术：`Assets/_UIAssets/Monsters/Apes/Monkey/Directions/{Up,Down}/`（12 张）。v1 的躯干格带尾巴导致拼装悬空/重心偏移，v2 重生成改为**无尾完整椭圆躯干**（垂直视角尾巴本被身体遮挡）。内置 ImageGen 生成（约 5-10 积分/张 × 4，含 v1 两张）。
- **动画控制器（v2 架构）**：`Directions/Animations/Monkey_Directions.controller` = 复制 Bunny/Controller 后扩展的**真实 AnimatorController**（旧 overrideController 已删除）：
  - 原有 6 状态（Idle/Ready/Walk/Run/Attack/Death）motion 全部换为 `_Directions` 变体（水平+垂直曲线并存）；
  - 新增 **WalkUp / WalkDown** 两个垂直状态（clip 仅 DirectionVisual 曲线，编辑器 Animator 窗口可直接预览垂直动画）；
  - 新增 int 参数 **Dir**（0=水平/1=上/2=下）：AnyState→WalkUp/Down 条件 `State==2 && !Action && Dir`；原 `→Walk`、`→Run` 追加 `Dir==0` 防抢状态（垂直奔跑时留在 WalkUp/Down 由 Speed 提速）；
  - 共享 Bunny 控制器未动一字节。
- 预制体：`Enemy_Monkey.prefab` 挂 EnemyDirectionalVisual + DirectionVisual/Motion 层级，控制器已换真实控制器，GUID 未变。
- 布局常量 v2：头 2.20@1.95、躯干 **1.50**@0.60、臂 **1.00**@±0.80,0.80、腿 **0.80**@±0.36,-0.20；bob 0.04/0.05/0.13。
- 运行时：`EnemyDirectionalVisual.Face()` 朝向变化时自动 `SetInteger("Dir", 0/1/2)`（与 BaseEnemy 同款 SetInteger(int,int) 重载 + StringToHash，无新增 AOT 面；控制器无 Dir 参数时静默无效，AdvancedHen 不受影响）。BaseEnemy 零改动。

## 验证（Library/FT_MONKEYDIR_STATUS.txt → verification.txt，42 项 PASS）

- 编辑器采样：Walk/WalkUp/WalkDown 三条行走动画躯干起伏+抬腿交替实测命中；WalkUp clip 纯垂直（9/9）；AnyState 条件齐全；→Walk 有 Dir==0 保护。
- Play 模式端到端（MCP execute_code，隔离场景，直接驱动 State 参数 + 真实 Face()）：Walk→WalkUp→WalkDown→Walk→Death 全链路正确，渲染器开关/头贴图/腿动画全程同步，0 错误。
- ★测试方法论坑：①直接 Instantiate 不走对象池 Init → BaseEnemy._anim 未缓存 → SetAnimState 静默无效（测试须直接 SetInteger 或等 Init）；②execute_code 的 codedom 单引号字符串报错；③Python str.replace 补丁静默失配导致测试脚本带旧变量编译失败——失败输出被过滤器吞掉，过滤展示要留 isError。

## 编辑器查看真实运行效果

- 菜单 `Tools/塔防/敌人方向示例/3. 方向动画预览窗`（EnemyDirectionPreviewWindow）：实例化预制体，按钮走真实代码路径（SetAnimState/Face），播放开关用 Animator.Update 推进。
- 或：选中预制体 → Animator 窗口可直接选 WalkUp/WalkDown 状态预览；或拖入场景按 Play。

## 待办

- 用户审核 proof_up/proof_down；其余 117 只未获准。
- 真机可见需重打 dll+AB（EnemyDirectionalVisual 改了热更码）。
