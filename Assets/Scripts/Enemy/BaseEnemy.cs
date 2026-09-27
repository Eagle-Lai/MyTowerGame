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

        /// <summary>路径进度 0~1（0=刚出生，1=快到终点）。索敌"最危险优先"策略的基础。</summary>
        public float PathProgress
        {
            get
            {
                if (_path == null || _path.Count <= 1)
                {
                    return 0f;
                }
                return Mathf.Clamp01((float)_pathIndex / (_path.Count - 1));
            }
        }

        public float BodyRadius { get; private set; }
        public EnemyConfig Config { get; private set; }

        // ---- 内部 ----
        private List<Point> _path;
        private int _pathIndex;
        private float _speed;
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

            // 首次 Init 时记下 prefab 授权缩放，之后只在此基础上乘配置值
            if (_baseScale == Vector3.zero)
            {
                _baseScale = transform.localScale;
            }
            transform.localScale = _baseScale * (cfg.Scale > 0f ? cfg.Scale : 1f);

            // 美术默认朝向来自常数表（Global.artFaceLeft）
            if (Configs.Global != null)
            {
                _artFaceLeft = Configs.Global.ArtFaceLeft;
            }

            CacheRefs();
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
            // 死亡动画播完 → 真正回收
            if (_pendingRecycle)
            {
                _recycleTimer -= dt;
                if (_recycleTimer <= 0f)
                {
                    EnemyManager.Instance.RecycleEnemy(this);
                }
                return;
            }

            if (!IsAlive || _path == null || _path.Count == 0)
            {
                return;
            }

            MoveAlongPath(dt);
            FaceMoveDirection();
        }

        private void MoveAlongPath(float dt)
        {
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

            if (CombatSystem.Instance != null)
            {
                CombatSystem.Instance.AddHitCount(1);
            }

            if (CurrentHp <= 0f)
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
            EventDispatcher.TriggerEvent<BaseEnemy, int>(EventName.EnemyKilledEvent, this, reward);

            SetAnimState(EnemyAnimState.Death);

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
