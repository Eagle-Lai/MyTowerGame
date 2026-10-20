# Monkey 上下方向接入进度

状态：v2 完成（2026-10-17）。分件美术重生成（无尾躯干）、**真实动画控制器**（含 WalkUp/WalkDown 状态 + Dir 参数）、Play 模式端到端验证通过，控制台 0 错误。等待用户美术审核；真机验证需按热更三件套重打 dll/AB。

状态：v2.1（2026-10-19）**修复编辑器无法预览上下动画**——垂直行走片段自带方向外观曲线，Animation / Animator 窗口选中 WalkUp/WalkDown 即可看到真实的背面/正面走路。详见文末「v2.1 预览修复」。

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

## v2.1 预览修复（2026-10-19）

**问题**：在 `Monkey_Directions.controller` 里选 WalkUp/WalkDown，编辑器看不到任何上下动画——预览画面一直是侧视且不动。

**根因**：两个垂直片段只有 `DirectionVisual/Motion/*` 的位移/旋转曲线，而垂直分件 `DirectionVisual/Motion/{Torso,Head,WingL,WingR,LegL,LegR}/Sprite` 的 SpriteRenderer 在预制体里 **enabled=false**，侧视 `Body/*` 是 enabled=true。曲线驱动的全是不可见节点，于是"动了但看不见"。

**做法**（只改资源 + 编辑器构建器，**不动热更运行时代码**）：

1. `WalkUp_Directions` / `WalkDown_Directions` 额外写入"方向外观曲线"，与运行时 `EnemyDirectionalVisual.ApplyView()` 写完全相同的值：
   - 侧视 7 个渲染器 `m_Enabled=0`（Body / Body/Head / Body/LegFrontL/R、LegBackL/R / Body/Tail）；
   - 垂直 6 个 `…/Sprite` 渲染器 `m_Enabled=1` + `m_Sprite`（Up 或 Down 分件）+ `m_SortingOrder`（Head 背面 12 / 正面 25，其余 15/20/5）+ `m_FlipX`（WingR=true）。
2. `writeDefaultValues` 全部关闭。否则其余状态（Ready/Idle/Attack/Death/Walk）会把渲染开关写回预制体默认值，朝上待机时又变回侧视。
3. 关闭 Write Defaults 后"片段曲线集不一致"会残留上一个状态的姿势（实测 Attack→Ready 大腿残留 13~24°、Death→WalkUp 残留 60~70°），因此新增 `NormalizeTransformCurves()`：把所有片段补齐为**同一套 Transform 曲线并集**，缺失项填预制体静止值（与原先 Write Defaults 的复位效果等价）。补齐后 7 状态两两切换实测 0 残留（42/42）。
4. 菜单 `Tools/塔防/敌人方向示例/4. 重建上下行走片段（不改预制体）`：只重建两条垂直片段 + 补齐曲线 + 关 Write Defaults，不碰预制体、不换 fileID，日常改完直接跑它。
5. 顺手修 `EnemyDirectionPreviewWindow`（菜单 3）：预览实例没走对象池 `Init`，`BaseEnemy.SetAnimState` 因 `_anim` 未缓存会静默返回，按钮等于没反应；改为直接写同款参数（`State` int + `Action` false）+ `Animator.Update(0)`。

**坑**：`AnimationClip.length` 每加一条曲线会长一帧（0.5→0.5167→…）。必须**先记下原时长**再烘焙，且 PPtr（`m_Sprite`）关键帧**只能给一个 t=0 的 key**——补到 stopTime 上会让 Unity 多算一帧，循环周期变 0.5167s。

**验证**：`Verify(Monkey)` 42 项全 PASS（新增 "preview shows vertical rig (rig=True side=False)" 断言）；片段时长保持 0.5s；垂直视角在 Ready/Idle/Attack/Death/Walk 之间不再被写回侧视。

## v2.2 图集合并 + 骨架校准（2026-10-19 晚）

用户在编辑器里看到上下行走"效果错误"（腿沉到地面以下、手臂像从脸颊长出来、头和身体比例失衡），并要求把 `Directions/{Up,Down}` 的 12 张分件合并成 `Monkey.png` 那样的图集并应用到动画。

**1. 图集（合并）**

- 产物：`Directions/Monkey_Directions.png`（2368×762，6 列 × 2 行，列=部件、行=Up/Down）+ `Monkey_Directions.sprites.json`（切片清单）。
- 切片：**按内容紧贴裁**（不含透明内边距，避免按 bounds 缩放时基准偏小），PPU 100、FullRect、无压缩、中心轴心；12 个命名切片 `Up_HeadNormal … Down_Leg`。
- 生成脚本：`.workbuddy/tools/build_monkey_direction_atlas.py`（源图已移到 `Docs/EnemyDirectionReview/Monkey/source/{Up,Down}`，不再进 Assets，避免同一美术两份源）。
- 构建器：`ImportAtlas()` 读清单 → 写 `TextureImporter.spritesheet` → 按名取切片；`ImportParts(atlas, dir)` 替换原先逐张 PNG 导入。预制体/Profile/两条垂直片段的 `m_Sprite` 全部指向图集（已核）。
- 旧 `Directions/Up|Down` 目录移出 Assets，全工程无残留 GUID 引用。

**2. 骨架校准（真正的"效果错误"）**

- 现象根因 A：**位置曲线是 Vector3 整体烘焙的**。`AddVerticalCurves` 只给 `m_LocalPosition.y` 打关键帧时，x/z 被写成 0 → 左右腿、左右臂全部塌到中线（看着像一条腿、手臂从身体里钻出来）。修法：rig 的每个节点补齐 `m_LocalPosition.x`（左右取 ±spec 值）与 `z=0`，手臂额外补 `y`。
- 现象根因 B：原先按"高度"缩放，而 Up/Down 美术是单件裁切的，长宽比和侧视差很多 → 头被拉宽到躯干的 2 倍、手臂短小。改为 **按目标框 (宽,高) 取 min 缩放**（`TorsoSize/HeadSize/WingSize/LegSize`，spec 新增字段；AdvancedHen 无尺寸时回退旧的高度规则）。
- 现象根因 C：整体尺寸/落点没对齐侧视。新布局以地面 y=0 为锚：腿 0.46×0.44@±0.24、躯干 1.24×1.25@1.175、头 1.95×1.41@2.225、臂 0.42×0.74@±0.60,1.0，总高 ≈2.95（侧视实测 2.98）。同屏实测：侧/上/下 高度 1.49 / 1.45 / 1.45，三者脚底同在高度的 -0.07 线上。
- 现象根因 D：背面头排序 12（在躯干之后）会让躯干顶边把头切成一条平线；改为 **两个方向都用 25**（`EnemyDirectionalVisual.ApplyView` 与烘焙曲线同步）。★这条改了热更运行时代码，真机需重打 dll。

**3. 验证**

- `Verify(Monkey)` 全 PASS（新增 WalkUp 片段 42 条 motion + 25 条 showcase）；7 状态两两切换姿势残留 0/42；朝上时 Ready/Idle/Attack/Death/Walk 均保持背面 rig（写默认值已关）。
- 离屏渲染（正交相机 → RenderTexture）逐帧确认：正面/背面上下行走四肢分开、脚在地面线、头身比例正常；同屏对比图见 `.workbuddy/tmp_monkey_preview/compare_sizes.png`。
- 旧分件 GUID 全工程零引用。

**4. 仍需**

- 用户美术终审（耳背在 Up 图里偏灰是原图色，不是渲染问题）；真机/热更需重打 dll + AB。
