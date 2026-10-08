using System.Collections.Generic;
using AStar;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 怪物动画状态。
    /// 【实测结论】怪物素材包的 AnimatorController 用 **int 参数 `State`** 驱动
    /// （Transition 条件是 `State != N`），而不是 Play 具名状态：
    ///   State = 0 → Idle，1 → Ready，2 → Walk，3 → Run，9 → Death
    /// 另有 `Speed`(float) 控制播放速度、`Attack`(Trigger) 触发攻击。
    /// 不同家族（Rat/Bat/Bear…）各有独立 Controller，切换类型时必须换 runtimeAnimatorController。
    /// </summary>
    public enum EnemyAnimState
    {
        Idle = 0,
        Ready = 1,
        Walk = 2,
        Run = 3,
        Death = 9,
    }

    /// <summary>
    /// 怪物基类（v2.1 的 2D 版）。
    ///
    /// 相对 v1.0 的关键改动：
    ///   - 去掉 Rigidbody / Vector3.ProjectOnPlane 广告牌 / 世界空间 TextMeshPro 血条
    ///   - 用 Transform（世界空间）+ SpriteRenderer 血条；位置用 transform.position
    ///   - 新增 IsAlive / PathProgress / GridKey（战斗判定与索敌策略的基础）
    ///   - 死亡时**发奖励**（v1.0 遗漏）、到终点时**扣玩家血**（v1.0 直接回收，玩家永不失败）
    ///   - 死亡动画播完再回收（延迟回收期间 IsAlive=false，不计入存活数）
    /// </summary>
    public class BaseEnemy : MonoBehaviour
    {
        // ---- 运行时状态 ----
        public bool IsAlive { get; private set; }
        /// <summary>是否已完成回收（CombatSystem 据此从列表移除）</summary>
        public bool IsFullyRecycled { get; private set; }
        /// <summary>EnemyGrid 中的格子 key（0 表示未入格）</summary>
        public int GridKey { get; set; }

        public Vector2 Position
        {
            get { Vector2 p = transform.position; return p; }
        }

        public float CurrentHp { get; private set; }
        public float TotalHp { get; private set; }

        /// <summary>
        /// 路径进度 0~1（0=刚出生，1=快到终点）。索敌"最危险优先"策略的基础。
        ///
        /// 【为什么飞行单位要单独算】地面怪按"走了几格 / 总格数"衡量；
        /// 飞行怪只有起点和终点两个点，格数比值毫无意义（永远是 0 或 1），
        /// 于是"最危险优先"会对它们完全失效。改用直线上的行驶比例，语义才一致。
        /// </summary>
        public float PathProgress
        {
            get
            {
                if (_flying)
                {
                    return _flyProgress;
                }
                if (_path == null || _path.Count <= 1)
                {
                    return 0f;
                }
                return Mathf.Clamp01((float)_pathIndex / (_path.Count - 1));
            }
        }

        public float BodyRadius { get; private set; }
        public EnemyConfig Config { get; private set; }

        /// <summary>
        /// 下一次允许弹出伤害飘字的时间（Time.unscaledTime）。
        /// 【为什么挂在怪身上】用"怪 → 时间"的字典做节流时，对象池复用会让字典键失效并持续泄漏；
        /// 状态跟着对象走就不会有这个问题。由 FloatingTextManager 维护，别处不要写。
        /// </summary>
        public float NextDamageTextTime { get; set; }

        // ---- 内部 ----
        private List<Point> _path;
        private int _pathIndex;
        private float _speed;

        // ---- 打击感（M2-W5）----
        /// <summary>身体部位的 SpriteRenderer 缓存（不含血条）。闪白 / 死亡淡出都改它。</summary>
        private SpriteRenderer[] _bodyRenderers;
        private float _flashTimer;
        private float _deathFade = 1f;
        /// <summary>出生时的最终缩放（配置缩放已生效）。死亡收缩在它基础上插值。</summary>
        private Vector3 _spawnScale = Vector3.one;

        private const float FlashDurationSec = 0.08f;
        private static readonly Color FlashColor = new Color(1f, 1f, 1f, 1f);

        // ---- 飞行单位（M2-W4）：直线寻路，不入 A* 网格 ----
        /// <summary>本怪是否飞行（由 EnemyConfig.IsFlying 决定，Init 时定型）</summary>
        private bool _flying;
        private Vector2 _flyStart;
        private Vector2 _flyEnd;
        private float _flyTotal = 1f;
        private float _flyProgress;
        private Transform _hpBarFill;
        private Transform _hpBarRoot;
        private Animator _anim;
        private SpriteRenderer _hpFillSr;
        private bool _pendingRecycle;
        private float _recycleTimer;

        // ---- 血条尺寸（首次 Init 时从 prefab 授权值测得，之后按比例改 localScale）----
        /// <summary>血条 Fill 满血时的 localScale.x</summary>
        private float _hpFillBaseScaleX = 1f;
        /// <summary>血条 Fill 满血时的 localPosition.x（与 Bg 左对齐的基准）</summary>
        private float _hpFillBaseX;
        /// <summary>血条总宽（HpBar 本地空间单位）</summary>
        private float _hpBarWidth = 1f;
        /// <summary>血条节点自身的 X 缩放绝对值（翻转补偿用）</summary>
        private float _hpBarBaseScaleX;
        /// <summary>血条是否已就绪</summary>
        private bool _hpBarReady;
        /// <summary>AnimatorController 是否已按配置换过（每个池化实例只需一次）</summary>
        private bool _animCtrlApplied;

        /// <summary>美术默认朝向是否朝左（来自常数表 Global.artFaceLeft）</summary>
        private bool _artFaceLeft = true;

        /// <summary>朝向诊断日志只打一次（避免刷屏）</summary>
        private static bool _facingLogged;

        // ---- prefab 授权缩放 ----
        /// <summary>
        /// prefab 根节点自带的缩放。
        /// 【为什么需要】怪物素材包的根节点 scale 是 0.5（美术按图集尺寸调好的），
        /// 早期实现直接 `transform.localScale = Vector3.one * cfg.Scale`，
        /// 会把美术调好的 0.5 覆盖掉，导致怪物突然变大 2 倍。
        /// 正确做法是**乘**在 prefab 授权值上，这样配置表的 scale=1 表示"保持美术原样"。
        /// </summary>
        private Vector3 _baseScale = Vector3.zero;

        private static readonly int ANIM_STATE = Animator.StringToHash("State");
        private static readonly int ANIM_SPEED = Animator.StringToHash("Speed");
        private static readonly int ANIM_ATTACK = Animator.StringToHash("Attack");

        /// <summary>到达判定阈值（格），太小会导致抖动，太大则拐角被切</summary>
        private const float ArriveThreshold = 0.08f;

        // ------------------------------------------------------------------
        // 生命周期
        // ------------------------------------------------------------------

        /// <summary>
        /// 由 EnemyManager 在生成时调用（不使用 Unity 的 Awake/Start，
        /// 因为对象是池化复用的，Awake 只跑一次）。
        /// </summary>
        public void Init(EnemyConfig cfg, List<Point> path)
        {
            Config = cfg;
            _speed = cfg.Speed;
            TotalHp = cfg.Hp;
            CurrentHp = cfg.Hp;
            BodyRadius = cfg.BodyRadius;

            // 池化复用必须清状态效果，否则新怪会带着上一只的减速 / 持续伤害出场
            _slowRatio = 0f;
            _slowTimer = 0f;
            _dotDps = 0f;
            _dotTimer = 0f;

            // 首次 Init 时记下 prefab 授权缩放，之后只在此基础上乘配置值
            if (_baseScale == Vector3.zero)
            {
                _baseScale = transform.localScale;
            }
            transform.localScale = _baseScale * (cfg.Scale > 0f ? cfg.Scale : 1f);
            _spawnScale = transform.localScale;

            // 表现状态同样要复位：池化复用否则会带着上一只的"半透明尸体"出场
            _flashTimer = 0f;
            _deathFade = 1f;
            NextDamageTextTime = 0f;

            // 美术默认朝向来自常数表（Global.artFaceLeft）
            if (Configs.Global != null)
            {
                _artFaceLeft = Configs.Global.ArtFaceLeft;
            }

            CacheRefs();
            // 飞行标记必须在 SetPath 之前定型：SetPath 会据此决定"逐格走"还是"走直线"
            _flying = cfg.IsFlying;
            SetPath(path);

            IsAlive = true;
            IsFullyRecycled = false;
            _pendingRecycle = false;
            _recycleTimer = 0f;
            GameObjSetActive(true);
            SetAnimState(EnemyAnimState.Walk);
            UpdateHpBar();
        }

        private void CacheRefs()
        {
            // 【注意 includeInactive=true 不能省】对象池归还时会 SetActive(false)，
            // 而 Init 是在"取出后、激活前"调用的 —— 此时整棵子树都是未激活状态。
            // GetComponentInChildren 默认跳过未激活的子物体，动画可能挂在子节点上
            // （怪物素材包的 Animator 在根节点，但换家族时未必），加 true 才稳妥。
            if (_anim == null)
            {
                _anim = GetComponentInChildren<Animator>(true);
            }
            // Controller 只需要换一次（对象池复用同一个实例，家族不会变）
            if (_anim != null && !_animCtrlApplied && Config != null &&
                !string.IsNullOrEmpty(Config.AnimController))
            {
                LoadAnimatorController(Config.AnimController);
            }
            // P2b：动画机速度必须每次"从池里取出"时重设 —— 上一只可能是别的倍速档
            SyncAnimSpeed();
            if (_hpBarRoot == null)
            {
                _hpBarRoot = transform.Find("HpBar");
            }
            if (_hpBarRoot != null && !_hpBarReady)
            {
                _hpBarFill = _hpBarRoot.Find("Fill");
                if (_hpBarFill != null)
                {
                    _hpFillSr = _hpBarFill.GetComponent<SpriteRenderer>();
                    if (_hpFillSr == null)
                    {
                        Debug.LogError("[Enemy] HpBar/Fill 上没有 SpriteRenderer，血条不会显示");
                    }
                    _hpFillBaseScaleX = Mathf.Abs(_hpBarFill.localScale.x);
                    if (_hpFillBaseScaleX < 0.0001f)
                    {
                        _hpFillBaseScaleX = 1f;
                    }
                    _hpFillBaseX = _hpBarFill.localPosition.x;

                    // 血条总宽 = 精灵原生世界宽 × 满血缩放
                    float nativeW = 1f;
                    if (_hpFillSr != null && _hpFillSr.sprite != null)
                    {
                        nativeW = _hpFillSr.sprite.rect.width /
                                  Mathf.Max(0.0001f, _hpFillSr.sprite.pixelsPerUnit);
                    }
                    _hpBarWidth = nativeW * _hpFillBaseScaleX;
                    _hpBarBaseScaleX = Mathf.Abs(_hpBarRoot.localScale.x);
                    _hpBarReady = true;
                }
                else
                {
                    Debug.LogError("[Enemy] HpBar 下缺少子节点「Fill」，血条不会显示");
                }
            }
        }

        /// <summary>
        /// 给 Animator 换 Controller（不同怪物家族各有独立 Controller）。
        /// 编辑器下用 ResLoader 取到的是 RuntimeAnimatorController。
        /// </summary>
        private void LoadAnimatorController(string family)
        {
            if (_anim == null)
            {
                return;
            }
            // 标记为"已处理"：对象池复用同一实例，家族不会变，没必要每次出生都重查表
            _animCtrlApplied = true;

            string key = "AnimController_" + family;
            if (!ResTable.TryGet(key, out _))
            {
                return;   // 未登记则不换，沿用 prefab 上已挂的 Controller
            }
            RuntimeAnimatorController ctrl = ResLoader.Instance.Load<RuntimeAnimatorController>(key);
            if (ctrl != null)
            {
                _anim.runtimeAnimatorController = ctrl;
            }
        }

        /// <summary>回收状态重置（对象池归还时调用，必须清空全部跨帧状态）</summary>
        public void OnRecycle()
        {
            IsAlive = false;
            IsFullyRecycled = true;
            _pendingRecycle = false;
            _recycleTimer = 0f;
            _path = null;
            _pathIndex = 0;
            GridKey = 0;

            // 表现状态必须还原，否则下一次从池里取出来时：
            // 身体是透明的、缩放的、或者还白着 —— 都是"看起来像 bug"的经典池化残留。
            _flashTimer = 0f;
            _deathFade = 1f;
            ApplyBodyAlpha(1f);
            transform.localScale = _spawnScale;
            NextDamageTextTime = 0f;

            // P2b：动画机速度还原 1，防止"×3 时死亡回收、×1 时复用"带着旧档位出场。
            // CacheRefs 在下次取出时还会再设一次，这里是双保险（池化残留一律按"必须清零"处理）。
            if (_anim != null)
            {
                _anim.speed = 1f;
            }

            GameObjSetActive(false);
        }

        private void GameObjSetActive(bool active)
        {
            if (gameObject.activeSelf != active)
            {
                gameObject.SetActive(active);
            }
        }

        // ------------------------------------------------------------------
        // 每帧（由 CombatSystem 集中驱动，不自行订阅 UpdateEvent）
        // ------------------------------------------------------------------

        public void Tick(float dt)
        {
            // P2b：动画机速度跟随倍速。
            // 【为什么放在每帧比对，而不是只订阅 GameSpeedChangedEvent】
            //   敌人是**池化**的：订阅/退订必须严格配对，漏一次就会在回收后仍被事件引用；
            //   而且从池里复用出来的实例，收不到"它出生之前"已经派发过的换档事件。
            //   每帧比对一次（只在不相等时才写）永远正确，代价只是一次浮点比较。
            SyncAnimSpeed();

            // 死亡动画播完 → 真正回收
            if (_pendingRecycle)
            {
                _recycleTimer -= dt;
                TickDeathFade(dt);
                if (_recycleTimer <= 0f)
                {
                    EnemyManager.Instance.RecycleEnemy(this);
                }
                return;
            }

            TickFlash(dt);

            // 状态效果先结算：持续伤害可能就在这一步把怪打死，
            // 打死之后就不能再移动了（否则尸体会顺着路径再滑一格）。
            TickEffects(dt);
            if (!IsAlive || _pendingRecycle)
            {
                return;
            }

            if (_path == null || _path.Count == 0)
            {
                return;
            }

            MoveAlongPath(dt);
            FaceMoveDirection();
        }

        /// <summary>
        /// 飞行单位的路径 = 出生点 → 终点的一条直线。
        ///
        /// 【为什么复用 A* 路径的首尾两点，而不是另开一套生成入口】
        /// EnemyManager / 波次系统只认识"这条 A* 路径"，取首尾即可。
        /// 飞行逻辑因此完全收在 BaseEnemy 内部，上层一行都不用改，
        /// 也不会出现"忘了给飞行单位传路径"的新失败模式。
        ///
        /// 【飞行单位的副作用，都是有意为之】
        ///   · 不参与"禁止完全堵路"的判定（塔墙拦不住它）
        ///   · 不参与路径重算（建塔/拆塔不影响它）
        ///   · 不阻止玩家在它脚下建塔（见 CombatSystem.HasAliveEnemyNear）
        /// </summary>
        private void SetupFlyingPath(List<Point> path)
        {
            if (path == null || path.Count == 0)
            {
                _flying = false;   // 拿不到路径就退回地面逻辑，别把怪卡死
                return;
            }
            _flyStart = Position;
            _flyEnd = path[path.Count - 1].Center;
            _flyTotal = Mathf.Max(0.0001f, Vector2.Distance(_flyStart, _flyEnd));
            _flyProgress = 0f;

            Vector2 d = _flyEnd - _flyStart;
            if (d.sqrMagnitude > 0.000001f)
            {
                _lastDir = d.normalized;
                FaceMoveDirection();
            }
        }

        /// <summary>飞行：直线飞向终点。到达即算漏怪。</summary>
        private void MoveStraight(float dt)
        {
            Vector2 pos = Position;
            Vector2 dir = _flyEnd - pos;
            float dist = dir.magnitude;

            if (dist <= ArriveThreshold)
            {
                _flyProgress = 1f;
                OnReachEnd();
                return;
            }

            Vector2 step = dir / dist * (_speed * dt);
            if (step.magnitude > dist)
            {
                step = dir;
            }
            transform.position = new Vector3(pos.x + step.x, pos.y + step.y, 0f);
            _lastDir = dir;
            _flyProgress = Mathf.Clamp01(1f - (dist - step.magnitude) / _flyTotal);
        }

        private void MoveAlongPath(float dt)
        {
            if (_flying)
            {
                MoveStraight(dt);
                return;
            }

            if (_pathIndex >= _path.Count)
            {
                OnReachEnd();
                return;
            }

            Vector2 target = _path[_pathIndex].Center;
            Vector2 pos = Position;
            Vector2 dir = target - pos;
            float dist = dir.magnitude;

            if (dist <= ArriveThreshold)
            {
                _pathIndex++;
                if (_pathIndex >= _path.Count)
                {
                    OnReachEnd();
                }
                return;
            }

            Vector2 step = dir / dist * (_speed * dt);
            // 防止单帧冲过目标点（低帧率时步长可能大于剩余距离）
            if (step.magnitude > dist)
            {
                step = dir;
            }
            transform.position = new Vector3(pos.x + step.x, pos.y + step.y, 0f);
            _lastDir = dir;
        }

        private Vector2 _lastDir = Vector2.right;

        /// <summary>
        /// 按移动方向做水平翻转。
        ///
        /// 【为什么之前是错的】原实现假设"美术默认朝右"，于是向右移动时不翻转。
        /// 但本美术包的怪物**默认朝左**（以 Rat 为例：Head 在 -X=-1.19，Tail 在 +X=+0.99），
        /// 结果就是"朝向与运动方向相反"。
        ///
        /// 现在把"默认朝向"做成常数（`Global.artFaceLeft`），逻辑变成：
        ///   默认朝左 → 向右移动时翻转；默认朝右 → 向左移动时翻转。
        /// 换美术包时只改配置，不用改代码。
        /// </summary>
        private void FaceMoveDirection()
        {
            float absX = Mathf.Abs(transform.localScale.x);
            if (absX < 0.0001f)
            {
                return;
            }
            // 纯纵向移动时保持当前朝向，避免上下来回抖
            bool movingLeft = _lastDir.x < -0.01f;
            bool movingRight = _lastDir.x > 0.01f;
            if (!movingLeft && !movingRight)
            {
                return;
            }

            bool flip = _artFaceLeft ? movingRight : movingLeft;
            float wantX = flip ? -absX : absX;

            // 【一次性诊断】把"翻转是否发生"打到日志里，和画面对照就能确定结论：
            //   日志说翻转了、画面也头朝右 → 逻辑正确
            //   日志说翻转了、画面仍头朝左 → 说明美术默认朝向其实是"右"，
            //     把 Global.xlsx 的 artFaceLeft 改成 0 并重跑导出即可
            if (!_facingLogged && movingRight)
            {
                _facingLogged = true;
                Debug.Log(string.Format(
                    "[朝向] 首次向右移动：artFaceLeft(默认朝左)={0} → 翻转={1}，scale.x={2:F2}\n" +
                    "  请对照画面：此时怪物头应朝右（终点方向）。\n" +
                    "  · 若正确 → 无需处理\n" +
                    "  · 若仍朝左 → 美术默认朝向其实是右，把 Global.xlsx 的 artFaceLeft 改为 0 再重跑导出",
                    _artFaceLeft, flip, wantX));
            }

            Vector3 s = transform.localScale;
            if (!Mathf.Approximately(s.x, wantX))
            {
                transform.localScale = new Vector3(wantX, s.y, s.z);
                CompensateHpBarFlip(wantX);
            }
        }

        /// <summary>
        /// 血条是根节点的子物体，根节点做水平翻转时血条会被一起镜像 ——
        /// 表现为"血条反向消耗 / 看起来位置不对"，而且只在朝某个方向时出现。
        /// 这里给血条节点一个反向的 X 缩放把它抵消掉。
        /// </summary>
        private void CompensateHpBarFlip(float rootScaleX)
        {
            if (_hpBarRoot == null || _hpBarBaseScaleX <= 0.0001f)
            {
                return;
            }
            Vector3 bs = _hpBarRoot.localScale;
            float want = (rootScaleX < 0f ? -1f : 1f) * _hpBarBaseScaleX;
            if (!Mathf.Approximately(bs.x, want))
            {
                bs.x = want;
                _hpBarRoot.localScale = bs;
            }
        }

        // ------------------------------------------------------------------
        // 路径
        // ------------------------------------------------------------------

    public void SetPath(List<Point> path)
    {
        _path = path;
        _pathIndex = 0;

        // 飞行单位：不逐格走 A*，改为"当前位置 → 终点"的直线。
        // 【为什么入口放在 SetPath 而不是 Init】路径在任何时候都可能被重设，
        // 把飞行分支收在这里，就不会出现"某条重设路径的调用绕过了飞行逻辑"。
        if (_flying)
        {
            SetupFlyingPath(path);
            return;
        }
        // 让第一格从当前位置自然衔接：若已经在第一格附近，直接跳到下一格
        if (_path != null && _path.Count > 1)
        {
            Vector2 pos = Position;
            if (Vector2.Distance(pos, _path[0].Center) < ArriveThreshold * 2f)
            {
                _pathIndex = 1;
            }
        }

        // ------------------------------------------------------------------
        // 初始朝向：沿路径向前找第一段"横向"移动，让怪物出生时就面朝那个方向。
        //
        // 【为什么必须做】路径经常以纯纵向开头（本工程实测：
        //   (0,0)→(1,0)→…→(8,0)→(8,1)→…→(8,15)，即先向下 8 格再向右 15 格）。
        // 而侧视精灵在纯纵向移动时**不能翻转**（翻了会上下颠倒），
        // 于是怪物在纵向段会一直保持美术默认朝向 —— 看起来就是
        // "怪物朝下走却面朝左"，这也是玩家反馈"朝向与运动方向不匹配"的真正原因
        // （跟 artFaceLeft 取 0 还是 1 无关，所以之前两轮改配置都没用）。
        //
        // 让它出生时就面朝"路径接下来要转向的那个方向"，全程观感就一致了。
        // ------------------------------------------------------------------
        if (_path != null && _path.Count > 1)
        {
            for (int i = 1; i < _path.Count; i++)
            {
                float dx = _path[i].Center.x - _path[i - 1].Center.x;
                if (Mathf.Abs(dx) > 0.01f)
                {
                    _lastDir = new Vector2(Mathf.Sign(dx), 0f);
                    FaceMoveDirection();
                    break;
                }
            }
        }
    }

        /// <summary>路径重算（建塔/拆塔后由事件触发）</summary>
        public void RefreshPath()
        {
            if (!IsAlive || AStarManager.Instance == null)
            {
                return;
            }
            // 飞行单位走直线，与 A* 无关：重算路径对它没有任何意义，
            // 强行重算反而会把它从直线拽回地面路线（那是 bug，不是特性）。
            if (_flying)
            {
                return;
            }
            // 找到当前所在格，从那里重新寻路
            int row, col;
            Vector2 pos = Position;
            if (!BoardView.Instance.WorldToCell(pos, out row, out col))
            {
                // 已走出棋盘（可能刚好在终点），忽略
                return;
            }
            Point from = AStarManager.Instance.GetPoint(row, col);
            if (from == null)
            {
                return;
            }
            List<Point> newPath = AStarManager.Instance.UpdatePathByEnemyPoint(from);
            if (newPath != null && newPath.Count > 0)
            {
                SetPath(newPath);
            }
        }

        // ------------------------------------------------------------------
        // 受击 / 死亡 / 漏怪
        // ------------------------------------------------------------------

        /// <summary>受到伤害。伤害已由塔的 power 经子弹传入。</summary>
        public void Hurt(float damage)
        {
            if (!IsAlive)
            {
                return;
            }

            float real = damage * (1f - Config.Armor);
            CurrentHp -= real;
            UpdateHpBar();

            // 持续伤害是"每帧一小口"（dps × dt，通常 0.1 上下），
            // 若也走闪白与飘字，被 DOT 的怪会一直白着、数字也毫无信息量。
            // 用 1 点伤害作为门槛，把 DOT 的碎伤害挡在外面。
            if (real >= 1f)
            {
                FlashOnHit();
            }

            if (CombatSystem.Instance != null)
            {
                CombatSystem.Instance.AddHitCount(1);
            }

            bool killing = CurrentHp <= 0f;
            // 【为什么飘字在这里而不是子弹侧】real 是**扣过护甲**的最终伤害，
            // 只有在这里才知道玩家真正打出了多少。放到子弹侧算会漏掉护甲这一层。
            if (real >= 1f)
            {
                FloatingTextManager.Show(this, transform.position, Mathf.Max(1, Mathf.RoundToInt(real)), killing);
            }

            // 受击音效加一道"显著伤害"门槛：几十发子弹每秒都响的话，
            // 音效就不再是信息而是噪音了（与飘字节流同一个理由，只是判据不同）。
            // 取最大生命的 8% 作为"这一下打得疼"的界线。
            if (!killing && TotalHp > 0f && real >= TotalHp * 0.08f && AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayAt(AudioName.EnemyHit, transform.position);
            }

            if (killing)
            {
                Die();
            }
        }

        private void Die()
        {
            IsAlive = false;

            // ★ 击杀奖励（v1.0 遗漏：原实现死亡时不发奖励）
            int reward = Config.Reward;
            PlayerDataManager.Instance.AddGold(reward);
            // 统计口径：结算界面的「击杀 N」读的就是这个计数器。
            // 【为什么必须在这里调】OnEnemyKilled 存在但**全工程没有任何调用点**，
            // 于是 TotalKilled 恒为 0 —— 结算弹窗永远显示"击杀 0"。
            PlayerDataManager.Instance.OnEnemyKilled();
            EventDispatcher.TriggerEvent<BaseEnemy, int>(EventName.EnemyKilledEvent, this, reward);

            SetAnimState(EnemyAnimState.Death);
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayAt(AudioName.EnemyDeath, transform.position);
            }

            // 从空间哈希移除，不再参与索敌
            if (CombatSystem.Instance != null && CombatSystem.Instance.Grid != null)
            {
                CombatSystem.Instance.Grid.Remove(this);
            }

            // 死亡动画播完再回收
            _pendingRecycle = true;
            _recycleTimer = (Configs.Global != null ? Configs.Global.DeathRecycleDelayMs : 600) / 1000f;
        }

        /// <summary>走到终点：扣玩家生命（v1.0 直接回收，导致玩家永不失败）</summary>
        private void OnReachEnd()
        {
            IsAlive = false;
            int dmg = Config.DamageToPlayer;

            EventDispatcher.TriggerEvent<BaseEnemy, int>(EventName.EnemyReachedEndEvent, this, dmg);
            PlayerDataManager.Instance.LoseHp(dmg);

            // 漏怪是玩家最该立刻感知的负面反馈 → 屏幕震动。
            // 幅度按"漏这一只有多疼"分级：Boss 漏掉（dmg=10）比小怪（dmg=1）震得明显得多。
            if (CameraController.Instance != null && Configs.Global != null)
            {
                float amp = Configs.Global.ShakeAmplitude * (1f + 0.35f * Mathf.Max(0, dmg - 1));
                CameraController.Instance.Shake(amp, Configs.Global.ShakeDurationSec);
            }
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.Play(AudioName.EnemyLeak);
            }

            if (CombatSystem.Instance != null && CombatSystem.Instance.Grid != null)
            {
                CombatSystem.Instance.Grid.Remove(this);
            }

            // 漏怪直接回收，不播死亡动画
            EnemyManager.Instance.RecycleEnemy(this);
        }

        /// <summary>
        /// 刷新血条。
        /// 【实现选择】用 localScale 缩放 Fill，并把它的中心左移让左边缘与背景对齐 ——
        /// 不用 SpriteRenderer.size，因为 size 只在 drawMode 为 Sliced/Tiled 时生效，
        /// 而 Sliced 要求精灵带九宫格边框，对程序生成的纯色条不适用。
        /// SpriteRenderer 改 transform 不触发 Canvas 重建，是低端机上最省的做法。
        /// </summary>
        private void UpdateHpBar()
        {
            if (!_hpBarReady || TotalHp <= 0f || _hpBarFill == null)
            {
                return;
            }
            float ratio = Mathf.Clamp01(CurrentHp / TotalHp);

            Vector3 s = _hpBarFill.localScale;
            s.x = _hpFillBaseScaleX * ratio;
            _hpBarFill.localScale = s;

            // 左边缘对齐：中心需左移 (总宽 - 当前宽) / 2
            Vector3 p = _hpBarFill.localPosition;
            p.x = _hpFillBaseX - _hpBarWidth * (1f - ratio) * 0.5f;
            _hpBarFill.localPosition = p;

            if (_hpBarRoot != null && !_hpBarRoot.gameObject.activeSelf)
            {
                _hpBarRoot.gameObject.SetActive(true);
            }
        }

        // ------------------------------------------------------------------
        // 动画
        // ------------------------------------------------------------------

        public void SetAnimState(EnemyAnimState state)
        {
            if (_anim == null)
            {
                return;
            }
            _anim.SetInteger(ANIM_STATE, (int)state);
        }

        /// <summary>
        /// P2b：让 Animator 的播放速度跟随 <see cref="GameClock.Speed"/>。
        /// 【暂停为什么不在这里处理】暂停靠 `Time.timeScale = 0`，Animator 默认 Normal
        ///   更新模式下会自己冻结，不需要也不能在这里把 speed 设成 0
        ///   （否则恢复时要额外记得改回来，反而多一个状态）。
        /// </summary>
        private void SyncAnimSpeed()
        {
            if (_anim != null && !Mathf.Approximately(_anim.speed, GameClock.Speed))
            {
                _anim.speed = GameClock.Speed;
            }
        }

        public void SetAnimSpeed(float speedScale)
        {
            if (_anim != null)
            {
                _anim.SetFloat(ANIM_SPEED, speedScale);
            }
        }

        public void TriggerAttackAnim()
        {
            if (_anim != null)
            {
                _anim.SetTrigger(ANIM_ATTACK);
            }
        }

        // ------------------------------------------------------------------
        // 打击感：命中闪白 / 死亡消散（M2-W5）
        // ------------------------------------------------------------------

        /// <summary>
        /// 缓存"身体"的 SpriteRenderer（**排除血条**）。
        /// 闪白与死亡淡出都只该作用于身体：把血条也刷白/刷透明，
        /// 玩家就没法判断还剩多少血了 —— 表现不能吃掉信息。
        /// </summary>
        private void CacheBodyRenderers()
        {
            if (_bodyRenderers != null)
            {
                return;
            }
            SpriteRenderer[] all = GetComponentsInChildren<SpriteRenderer>(true);
            List<SpriteRenderer> list = new List<SpriteRenderer>(all.Length);
            for (int i = 0; i < all.Length; i++)
            {
                SpriteRenderer sr = all[i];
                if (sr == null)
                {
                    continue;
                }
                if (_hpBarRoot != null && sr.transform.IsChildOf(_hpBarRoot))
                {
                    continue;
                }
                list.Add(sr);
            }
            _bodyRenderers = list.ToArray();
        }

        /// <summary>受击闪白。由 Hurt 在伤害达到门槛时调用（DOT 的碎伤害不闪）。</summary>
        public void FlashOnHit()
        {
            CacheBodyRenderers();
            if (_bodyRenderers.Length == 0)
            {
                return;
            }
            for (int i = 0; i < _bodyRenderers.Length; i++)
            {
                _bodyRenderers[i].color = FlashColor;
            }
            _flashTimer = FlashDurationSec;
        }

        private void TickFlash(float dt)
        {
            if (_flashTimer <= 0f)
            {
                return;
            }
            _flashTimer -= dt;
            if (_flashTimer > 0f)
            {
                return;
            }
            _flashTimer = 0f;
            // 还原成白色：本工程的怪物美术没有被额外染色，白色即"原样"
            for (int i = 0; i < _bodyRenderers.Length; i++)
            {
                _bodyRenderers[i].color = Color.white;
            }
        }

        /// <summary>
        /// 死亡消散：在"死亡动画播完再回收"的这段时间里做淡出 + 轻微收缩。
        /// 时长直接复用 DeathRecycleDelayMs —— 两处用同一个数，
        /// 就不会出现"已经回收了但还没淡完"或者"淡完了还杵在那"的错位。
        /// </summary>
        private void TickDeathFade(float dt)
        {
            float total = (Configs.Global != null ? Configs.Global.DeathRecycleDelayMs : 600) / 1000f;
            if (total <= 0f)
            {
                return;
            }
            _deathFade = Mathf.Clamp01(_deathFade - dt / total);
            ApplyBodyAlpha(_deathFade);
            transform.localScale = _spawnScale * (0.85f + 0.15f * _deathFade);
        }

        private void ApplyBodyAlpha(float a)
        {
            CacheBodyRenderers();
            for (int i = 0; i < _bodyRenderers.Length; i++)
            {
                Color c = _bodyRenderers[i].color;
                if (Mathf.Approximately(c.a, a))
                {
                    continue;
                }
                c.a = a;
                _bodyRenderers[i].color = c;
            }
        }

        // ------------------------------------------------------------------
        // 状态效果：减速 / 持续伤害（M2-W3）
        // ------------------------------------------------------------------

        /// <summary>当前减速比例（0 = 未减速）</summary>
        private float _slowRatio;
        private float _slowTimer;

        private float _dotDps;
        private float _dotTimer;

        /// <summary>
        /// 施加减速。
        ///
        /// 【为什么不叠加】多个减速塔叠加会让"铺满减速塔"变成唯一解，经济与难度都会失控。
        /// 取最强的一层并刷新时长，是塔防里的通行做法，也更容易向玩家解释。
        /// </summary>
        /// <param name="ratio">减速比例 0~1（0.5 = 速度减半）</param>
        public void ApplySlow(float ratio, float durationSec)
        {
            if (!IsAlive || ratio <= 0f || durationSec <= 0f)
            {
                return;
            }
            // 上限 0.95：留 5% 速度，避免怪被定住后看起来像卡死（也防止除零类隐患）
            ratio = Mathf.Clamp(ratio, 0f, 0.95f);
            if (ratio >= _slowRatio)
            {
                _slowRatio = ratio;
            }
            _slowTimer = Mathf.Max(_slowTimer, durationSec);
            SetSpeedScale(1f - _slowRatio);
        }

        /// <summary>施加持续伤害（每秒 dps 点，持续 durationSec 秒）。重复施加取更强的一层并刷新时长。</summary>
        public void ApplyDot(float dps, float durationSec)
        {
            if (!IsAlive || dps <= 0f || durationSec <= 0f)
            {
                return;
            }
            if (dps >= _dotDps)
            {
                _dotDps = dps;
            }
            _dotTimer = Mathf.Max(_dotTimer, durationSec);
        }

        /// <summary>推进状态效果计时器。由 Tick 在最前面调用。</summary>
        private void TickEffects(float dt)
        {
            if (_slowTimer > 0f)
            {
                _slowTimer -= dt;
                if (_slowTimer <= 0f)
                {
                    _slowTimer = 0f;
                    _slowRatio = 0f;
                    ResetSpeed();
                }
            }

            if (_dotTimer > 0f && IsAlive)
            {
                _dotTimer -= dt;
                // 【为什么走 Hurt 而不是直接扣 CurrentHp】
                // 护甲减伤、血条刷新、击杀奖励、命中统计、伤害飘字全都挂在 Hurt 上，
                // 绕过去等于每一条都要单独再实现一遍，迟早不一致。
                Hurt(_dotDps * dt);
                if (_dotTimer <= 0f)
                {
                    _dotTimer = 0f;
                    _dotDps = 0f;
                }
            }
        }

        // ------------------------------------------------------------------
        // 速度（减速效果用）
        // ------------------------------------------------------------------

        public void SetSpeedScale(float scale)
        {
            _speed = Config.Speed * Mathf.Max(0f, scale);
            SetAnimSpeed(Mathf.Max(0.1f, scale));
        }

        public void ResetSpeed()
        {
            _speed = Config.Speed;
            SetAnimSpeed(1f);
        }
    }
}
