# VOL_06 敌人四方向

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：获准名单、Profile/DirectionalVisual 分工、两套架构（AdvancedHen / Monkey）、Monkey v2 控制器细节、构建器与校验坑、测试坑、AI 分件美术要求。

## 敌人四方向（★获准名单 = AdvancedHen + Monkey，其余须用户点名）
- `Profile`(配置) / `DirectionalVisual`(表现) 显式启用，无配置时走原逻辑；`BaseEnemy` 负责首段方向、主轴滞回、镜像、血条补偿、池化 `ResetForSpawn`（★`Animator.Update(0)` 必须在 `SetActive` 之后调）。
- 两套架构（每片段 9 条 DirectionVisual / Motion 曲线）：
  - ①AdvancedHen = `AnimatorOverrideController`（换 clip，不换状态机）；
  - ②Monkey = **真实 AnimatorController**：新增 WalkUp/WalkDown 状态 + int 参数 `Dir`(0 水平 / 1 上 / 2 下)；AnyState → 垂直态条件 `State==2 && !Action && Dir`；原 `→Walk`/`→Run` 加 `Dir==0` 防抢；`Face()` 自动 `SetInteger("Dir")`。
  - 新怪 = 在 `EnemyDirectionSpec` 加条目。
- Monkey v2 细节（真实控制器由 CopyAsset Bunny 后 API 改造，共享资源零改动）：
  - 原 6 个状态换成 `_Directions` motion + 新增 WalkUp/WalkDown（纯 DirectionVisual 曲线 clip）；垂直奔跑留 WalkUp/Down 靠 Speed 提速。
  - `Face()` 与 `BaseEnemy` 用同款 API = AOT 安全；控制器无 `Dir` 参数时静默无效。
- 构建器 `EnemyDirectionPrefabBuilder`；Monkey 布局：头 2.2@1.95 / 躯干 1.5@0.6 / 臂 1.0@±0.80,0.80 / 腿 0.8@±0.36,-0.20（PPU=100），bob 0.04/0.05/0.13。
  - `BuildAndVerify` 幂等 + 写 `Library/FT_<名>DIR_STATUS.txt`（42 项校验）。
  - ★Verify 坑：clips 是 `AnimationClipPair[]`；双腿交替要在同一时刻比左右差；Death 倾斜按片段时长百分比定点采样；`AnimatorCondition` 的属性名是 `mode` 不是 `conditionMode`。
  - 菜单：Tools ▸ 塔防 ▸ 敌人方向示例 ▸ 1/2 接入、3 方向动画预览窗（走真实 `SetAnimState`/`Face` + `Animator.Update`）。
- ★测试坑：直接 `Instantiate` 不走池 `Init` → `_anim` 未缓存 → `SetAnimState` 静默无效；改 `animator.SetInteger("State", N)` 或走 Init。
- ★AI 分件美术：ImageGen + PIL 拼侧视参考图 + 原 atlas 双图输入，模板 `Docs/EnemyDirectionReview/<怪名>/`（含 `generation_*.txt`）。
  - ★生成品红底非纯色（每图不同）→ 必须从角点采样实际背景色再按距离阈值抠；
  - ★躯干格要"无尾完整椭圆 + 轮廓含底边完整可见"（带尾巴会拼装悬空、重心偏）；
  - Wing 槽位语义按怪适配（Monkey = 手臂）。
- ★★编辑器预览（2026-10-19 修复）：Animator/Animation 窗口选 WalkUp/WalkDown 看不到上下动画，根因是垂直分件 SpriteRenderer 默认 enabled=false，而片段只驱动 `DirectionVisual/Motion/*` 的位移旋转 → "动了但看不见"。
  - 做法：两条垂直片段额外烘焙"方向外观曲线"（侧视 7 个 m_Enabled=0；垂直 6 个 m_Enabled=1 + m_Sprite + m_SortingOrder + m_FlipX），值与运行时 `ApplyView()` 完全一致 → 预览真实、运行行为不变；**不动热更运行时码**。
  - ★配套必做：所有状态 `writeDefaultValues=false`（否则 Ready/Idle/Attack 会把渲染开关写回预制体默认=侧视），并用 `NormalizeTransformCurves()` 把全部片段补齐为同一套 Transform 曲线并集（缺失填静止值），否则关 Write Defaults 后会残留上一状态姿势（实测 Attack→Ready 大腿残 13~24°）。
  - ★坑：`AnimationClip.length` 每加一条曲线长一帧（0.5→0.5167）。先记原时长再烘焙；PPtr(`m_Sprite`) 只给一个 t=0 key，补到 stopTime 会让循环变 0.5167s。
  - 菜单 4「重建上下行走片段（不改预制体）」：只重烘两条垂直片段 + 补曲线 + 关 Write Defaults，不换 fileID。
  - 预览窗（菜单 3）实例不走池 `Init` → `SetAnimState` 静默无效，已改为直接写 `State`/`Action` 参数 + `Animator.Update(0)`。
- ★★方向美术图集化（2026-10-19，Monkey 首个）：多张分件 PNG → 一张 `X_Directions.png`（列=部件、行=方向）+ `X_Directions.sprites.json` 清单；构建器 `ImportAtlas()` 读清单写 `TextureImporter.spritesheet` 再按名取切片。
  - 切片必须**按内容紧贴裁**（不要用带透明内边距的格子），否则 `sprite.bounds` 偏大、按框缩放会把角色做小。
  - 源图放 `Docs/EnemyDirectionReview/<怪>/source/`（不进 Assets），避免同一美术两份源、也避免误引用旧 GUID。
- ★★★位置/旋转曲线是 Vector3/Euler **整体烘焙**：只给 `m_LocalPosition.y` 打关键帧 → x/z 被写 0，左右腿和左右臂会塌到中线（表现为"只有一条腿""手臂从身体里钻出来"）。rig 每个节点必须把 x（±布局值）与 z=0 都 key 上；同理 Euler 的 x/y 要显式为 0。
- ★尺寸标定：分件是单件裁切的，长宽比与侧视不同，**按高度缩放会失真**（头会宽到躯干 2 倍）。改用目标框 (宽,高) 取 min 缩放，并以地面 y=0 为锚排布；验收方法是同屏渲染侧/上/下对比：三者高度接近且脚底同一条线。
- ★背面视图头排序不要低于躯干（12<15 会被躯干顶边切成平线），与正面统一用 25；改这里同时要改烘焙曲线的排序值，否则运行时两套值打架。

## 全量续作（2026-10-24 ~ 10-30，108 个角色）
- 除 AdvancedHen / Monkey 外的角色统一走「显式登记 + 脚本生成」两件套：
  - `Assets/Editor/EnemyDirectionRemainingCatalog.cs`：108 条 `EnemyDirectionSpec`（ArtDir / PrefabPath / ControllerSource / OriginalAtlasPath / UseSeparateViewRigs）。★**登记不等于安装**，构建/安装仍要显式点菜单，避免批量误改生产资源。
  - `Assets/Editor/EnemyDirectionRemainingMotion.cs`：按 `layout.anatomy` + `motionKind`（hexapod / scorpion / flying / floating / crawler / chest / giant / hop / bird）生成分方向 Motion 曲线；已批准角色的既有 rig 直接跳过，不重算。
- 状态：内部队列 **108/108 完成**，全部为 `completed_pending_user_art_review`（user_approved=false），首批 10 个（Bat…BoarMounted，见 `Batch01_10/user_approval_20261023.json`）仍是唯一用户已批准的一批。实时事实以 `Docs/EnemyDirectionReview/Remaining_20261024/progress.json` 与 `conversation_chain.json` 为准，README 页首实时块只是快照。
- 每角色产出（结论级）：`installed_manifest.json`（装了哪些文件 + 哈希）、`final_validation_*.json`（两轮真实 Play 各 84 PASS）、`review.json`（实际看过的时序板/采样位）、`anatomy_plan.json` + `layout_adjustments.json`。过程媒体（generation / runtime_* / staged_art / frames / AllGIF）**不入库**，见 `MEMORY.md` 证据入库体量口径。
- 体积事实：单个 `Directions/` 约 7MB（图集 0.9MB + 4 条逐帧 anim 7MB），全量 anim 722MB。这就是 `.anim` 在 git 里最贵的原因，压缩无意义（稠密关键帧是表现精度本身）。

