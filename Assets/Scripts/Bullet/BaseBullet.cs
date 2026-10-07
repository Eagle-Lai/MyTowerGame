using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    public enum BulletState { None = 0, Fire, Idle }

    /// <summary>
    /// 子弹基类（v2.1 的 2D 版，M2 补齐穿透 / 范围 / 减速 / 持续伤害）。
    ///
    /// 相对 v1.0 的关键改动：
    ///   - **移除 OnTriggerEnter 命中判定**，改为每帧「与目标的距离 ≤ hitRadius + 怪物体半径」判定
    ///   - 不再用 transform.Translate(Vector3.forward)，改为 Vector2 方向位移
    ///   - 伤害由发射塔注入（v1.0 硬编码 Hurt(1)）
    ///   - 复用时必须完整重置状态，否则会出现"带着上次目标飞出去"的经典池化 Bug
    ///
    /// 【M2 修复的两个真实缺陷】
    ///   1. 穿透**完全无效**：原实现在 _pierce > 0 时把 _target 置 null 后 return，
    ///      而命中判定要求 _target != null —— 子弹此后再也不会命中任何东西。
    ///      现在改为"用空间哈希找最近的、还没打过的敌人"，穿透才有意义。
    ///   2. AOE 每次命中 new List（每跳一次 GC）：缓冲改为实例字段复用。
    ///
    /// 【命中效果的口径】以**子弹的 effectType** 为准（见 EffectType 枚举注释）；
    ///   强度 effectValue 由塔覆盖（塔里填了正数就用塔的），这样减速塔三级各不相同，
    ///   而 AOE / 穿透塔不必在表里重复填同样的值。
    /// </summary>
    public class BaseBullet : MonoBehaviour
    {
        public BulletState State { get; private set; }

        /// <summary>配置里没填 resName 时的兜底逻辑名（BulletManager 与归还逻辑共用，避免两处写死不一致）</summary>
        public const string FallbackResName = "Bullet_Normal";

        /// <summary>本发子弹所属的对象池 key（= 配置的 resName）。归还时用它找对池子。</summary>
        public string ResName { get; private set; }

        /// <summary>减速持续时长（秒）。做成常数而不是配置列：当前只有一种减速弹，
        /// 加一列只会让表更宽；真要做"不同时长"时再加列即可。</summary>
        private const float SlowDurationSec = 2f;

        /// <summary>持续伤害的持续时间（秒），同上。</summary>
        private const float DotDurationSec = 3f;

        /// <summary>
        /// 空间哈希查询的额外半径余量，用来覆盖"怪物受击半径"。
        /// 取 1.0 世界单位，远大于当前所有怪的 bodyRadius（默认 0.4）；
        /// 多查出来的候选会被随后的精确距离判定过滤掉，只是多几次比较。
        /// </summary>
        private const float QueryPad = 1.0f;

        private BaseEnemy _target;
        private Vector2 _dir = Vector2.right;
        private float _speed;
        private float _hitRadius;
        private float _lifeTime;
        private float _lifeTimer;
        private float _damage;
        private int _pierce;
        private float _aoeRadius;
        private EffectType _effect;
        private float _effectValue;
        private SpriteRenderer _sr;

        // ---- AOE 专用（见 Init 里的说明）----
        /// <summary>是否为 AOE 弹：飞向**发射瞬间锁定的落点**，到达即引爆，不追尾。</summary>
        private bool _isAoe;
        /// <summary>AOE 落点（世界坐标，发射瞬间确定，之后不再改变）</summary>
        private Vector2 _aoeTargetPos;
        /// <summary>引爆判定的到达阈值（世界单位）。取小值：让弹体基本飞到落点才炸。</summary>
        private const float AoeArriveEpsilon = 0.08f;
        /// <summary>命中判定 / AOE 的候选缓冲。实例字段复用 → 命中过程零 GC。</summary>
        private readonly List<BaseEnemy> _queryBuf = new List<BaseEnemy>(32);

        /// <summary>已被**这一发**子弹打过的敌人。穿透时用来避免反复打同一个目标。</summary>
        private readonly HashSet<BaseEnemy> _hitSet = new HashSet<BaseEnemy>();

        /// <summary>
        /// 初始化一发子弹。
        /// </summary>
        /// <param name="towerEffectValue">
        /// 发射塔的 effectValue。&gt; 0 时覆盖子弹自己的值（减速塔三级强度因此不同）。
        /// </param>
        public void Init(BaseEnemy target, float damage, BulletConfig cfg, float towerEffectValue)
        {
            _target = target;
            _damage = damage;
            _speed = cfg.Speed;
            _hitRadius = cfg.HitRadius;
            _lifeTime = cfg.LifeTimeSec;
            _pierce = cfg.Pierce;
            _aoeRadius = cfg.AoeRadius;
            _effect = cfg.Effect;
            _effectValue = towerEffectValue > 0f ? towerEffectValue : cfg.EffectValue;
            ResName = string.IsNullOrEmpty(cfg.ResName) ? FallbackResName : cfg.ResName;
            _lifeTimer = 0f;
            _hitSet.Clear();
            State = BulletState.Fire;

            // includeInactive=true：对象池归还时会 SetActive(false)，
            // 而 Init 发生在"取出后、激活前"，默认参数会漏掉未激活的子物体
            if (_sr == null)
            {
                _sr = GetComponentInChildren<SpriteRenderer>(true);
            }
            if (_sr != null)
            {
                _sr.sortingOrder = BoardSorting.Bullet;
                transform.localScale = Vector3.one * cfg.Scale;
            }

            // AOE 弹：目标不是"要打中的那只怪"，而是"要炸掉的落点"。
            //   落点在发射瞬间就锁定（怪物死了/飞走了都不改），弹体直飞到落点引爆 ——
            //   这才是"范围攻击"；若仍追着怪跑，就退化成了单体攻击（哪怕炸开有溅射）。
            _isAoe = _aoeRadius > 0f;
            if (_isAoe)
            {
                _aoeTargetPos = target != null ? target.Position : (Vector2)transform.position;
            }

            // 初始朝向：AOE 朝落点，普通弹朝目标当前位置
            Vector2 aimAt = _isAoe ? _aoeTargetPos : (target != null ? target.Position : (Vector2)transform.position);
            Vector2 d = aimAt - (Vector2)transform.position;
            if (d.sqrMagnitude > 0.000001f)
            {
                _dir = d.normalized;
            }
            gameObject.SetActive(true);
        }

        /// <summary>由 CombatSystem 每帧调用</summary>
        public void Tick(float dt)
        {
            if (State != BulletState.Fire)
            {
                return;
            }

            // ① 制导：
            //    - AOE 弹**不追踪**，直飞落点（见 Init）；到达即引爆。
            //    - 普通弹只在"还没打中任何敌人"时制导。一旦打中过（穿透弹），
            //      就保持最后方向直线飞行 —— 否则子弹会拐回去追已被打过的那只，穿透变绕圈。
            if (_isAoe)
            {
                Vector2 toPos = _aoeTargetPos - (Vector2)transform.position;
                // 到达（或越过）落点 → 引爆
                if (toPos.sqrMagnitude <= AoeArriveEpsilon * AoeArriveEpsilon)
                {
                    transform.position = new Vector3(_aoeTargetPos.x, _aoeTargetPos.y, 0f);
                    Explode(_aoeTargetPos);
                    return;
                }
            }
            else if (_hitSet.Count == 0 && _target != null && _target.IsAlive)
            {
                Vector2 d = _target.Position - (Vector2)transform.position;
                if (d.sqrMagnitude > 0.000001f)
                {
                    _dir = d.normalized;
                }
            }

            // ② 位移
            Vector2 pos = transform.position;
            pos += _dir * (_speed * dt);
            transform.position = new Vector3(pos.x, pos.y, 0f);

            // ③ AOE 弹位移后可能正好跨过落点：再判一次（高速弹 + 大 dt 时必需），
            //    到达即引爆并回收，不做穿透/命中扫描。
            if (_isAoe)
            {
                Vector2 after = _aoeTargetPos - pos;
                if (after.sqrMagnitude <= AoeArriveEpsilon * AoeArriveEpsilon
                    || Vector2.Dot(_aoeTargetPos - pos, _dir) <= 0f)   // 已越过落点
                {
                    transform.position = new Vector3(_aoeTargetPos.x, _aoeTargetPos.y, 0f);
                    Explode(_aoeTargetPos);
                    return;
                }
                // 飞行中未到达：只走超时回收
                _lifeTimer += dt;
                if (_lifeTimer >= _lifeTime)
                {
                    Explode(Position);   // 超时也别白飞：就地炸掉
                }
                return;
            }

            // ③′ 普通弹命中判定：找最近的、本发子弹还没打过的敌人
            BaseEnemy hit = FindHit(pos);
            if (hit != null)
            {
                OnHit(hit);
                if (State != BulletState.Fire)
                {
                    return;   // 已回收，后面的逻辑不能再碰 transform
                }
            }

            // ④ 超时回收（防止"追不上的子弹"永久存在）
            _lifeTimer += dt;
            if (_lifeTimer >= _lifeTime)
            {
                Recycle();
            }
        }

        /// <summary>
        /// 找当前位置能命中的敌人（最近优先）。
        ///
        /// 【为什么不能只认 _target】穿透弹打中第一个之后 _target 就没有意义了，
        /// 必须能"沿路找下一个"。空间哈希已经把候选压到常数级，这里再精确过滤即可。
        /// </summary>
        private BaseEnemy FindHit(Vector2 pos)
        {
            CombatSystem cs = CombatSystem.Instance;
            if (cs == null || cs.Grid == null)
            {
                return null;
            }

            _queryBuf.Clear();
            cs.Grid.QueryCircle(pos, _hitRadius + QueryPad, _queryBuf);

            BaseEnemy best = null;
            float bestSqr = float.MaxValue;
            for (int i = 0; i < _queryBuf.Count; i++)
            {
                BaseEnemy e = _queryBuf[i];
                if (e == null || !e.IsAlive || _hitSet.Contains(e))
                {
                    continue;
                }
                // 命中面 ≈ 怪物身体轮廓：只用子弹半径的话，怪物越大反而越难打中
                float hitR = _hitRadius + e.BodyRadius;
                float sqr = (e.Position - pos).sqrMagnitude;
                if (sqr > hitR * hitR)
                {
                    continue;   // 网格查询会带出范围外元素，这里精确过滤
                }
                if (sqr < bestSqr)
                {
                    bestSqr = sqr;
                    best = e;
                }
            }
            return best;
        }

        private void OnHit(BaseEnemy e)
        {
            e.Hurt(_damage);
            ApplyEffect(e);
            _hitSet.Add(e);

            // AOE 弹：理论上走不到这里（Tick 里到达落点就直接 Explode 了），
            // 但保留此分支作为兜底 —— 万一飞行途中撞到别的怪，也应当就地炸开。
            if (_aoeRadius > 0f)
            {
                Explode(Position);
                return;
            }

            if (_pierce > 0)
            {
                _pierce--;
                return;   // 不回收：继续沿当前方向飞，找下一个目标
            }
            Recycle();
        }

        /// <summary>
        /// 在 <paramref name="center"/> 处引爆：对半径 _aoeRadius 内的**全部**存活敌人
        /// 造成伤害并施加效果，然后回收自身。
        ///
        /// AOE 的口径是"范围攻击"而非"单体 + 溅射"：伤害范围从落点算，
        /// 与落点上是否站怪无关 —— 怪死了/没打中，只要在范围内一样吃伤害。
        /// </summary>
        private void Explode(Vector2 center)
        {
            CombatSystem cs = CombatSystem.Instance;
            if (cs != null && cs.Grid != null && _aoeRadius > 0f)
            {
                _queryBuf.Clear();
                cs.Grid.QueryCircle(center, _aoeRadius, _queryBuf);
                float r2 = _aoeRadius * _aoeRadius;
                for (int i = 0; i < _queryBuf.Count; i++)
                {
                    BaseEnemy other = _queryBuf[i];
                    if (other == null || !other.IsAlive)
                    {
                        continue;
                    }
                    if ((other.Position - center).sqrMagnitude <= r2)
                    {
                        other.Hurt(_damage);
                        ApplyEffect(other);
                    }
                }
            }
            Recycle();
        }

        /// <summary>
        /// 施加命中效果。effectType 以子弹为准（见 EffectType 注释）。
        /// Aoe / Laser 不在子弹侧额外处理：前者由 aoeRadius 分支完成，后者根本不生成弹体。
        /// </summary>
        private void ApplyEffect(BaseEnemy e)
        {
            switch (_effect)
            {
                case EffectType.Slow:
                    e.ApplySlow(_effectValue, SlowDurationSec);
                    break;
                case EffectType.Dot:
                    e.ApplyDot(_effectValue, DotDurationSec);
                    break;
                default:
                    break;
            }
        }

        public Vector2 Position
        {
            get { Vector2 p = transform.position; return p; }
        }

        public void Recycle()
        {
            BulletManager.Instance.RecycleBullet(this);
        }

        /// <summary>对象池归还时调用，必须清空全部跨帧状态</summary>
        public void OnRecycle()
        {
            State = BulletState.Idle;
            _target = null;
            _dir = Vector2.right;
            _lifeTimer = 0f;
            _pierce = 0;
            _damage = 0f;
            _aoeRadius = 0f;
            _isAoe = false;
            _aoeTargetPos = Vector2.zero;
            _effect = EffectType.None;
            _effectValue = 0f;
            _hitSet.Clear();
            _queryBuf.Clear();
            gameObject.SetActive(false);
        }
    }

    /// <summary>
    /// 子弹管理器（池化）。
    ///
    /// 【为什么按 resName 分池】不同子弹将来会有不同外观（爆炸弹/穿透弹/腐蚀弹…），
    ///   TBBulletData.resName 已经能表达这件事。现在五种子弹都还指向 Bullet_Normal，
    ///   所以实际只有一个池；但接口先按多池设计，将来换美术时不用再改这里。
    /// </summary>
    public class BulletManager : BaseManager<BulletManager>
    {
        public Transform BulletParent { get; private set; }

        /// <summary>兜底资源名：配置里没填 resName 时用它</summary>
        private readonly Dictionary<string, ObjectPool<BaseBullet>> _pools =
            new Dictionary<string, ObjectPool<BaseBullet>>();

        private int _maxPoolSize = 256;
        private bool _inited;
        /// <summary>RecycleAll 的复用缓冲</summary>
        private readonly List<BaseBullet> _clearBuf = new List<BaseBullet>(256);

        public override void OnInit()
        {
            base.OnInit();

            // 幂等保护：重复初始化会新建对象池，之前发出去的池化对象就再也回不来了
            if (_inited)
            {
                Debug.LogWarning("[Bullet] OnInit 被重复调用，已忽略（管理器应只初始化一次）");
                return;
            }
            _inited = true;

            int prewarm = Configs.Global != null ? Configs.Global.BulletPoolSize : 128;
            _maxPoolSize = Mathf.Max(16, prewarm * 2);
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
            foreach (KeyValuePair<string, ObjectPool<BaseBullet>> kv in _pools)
            {
                ObjectPool<BaseBullet> pool = kv.Value;
                if (pool != null)
                {
                    pool.Clear(b =>
                    {
                        if (b != null && b.gameObject != null)
                        {
                            Object.Destroy(b.gameObject);
                        }
                    });
                }
            }
            _pools.Clear();
        }

        public void SetParent(Transform parent)
        {
            BulletParent = parent;
        }

        private ObjectPool<BaseBullet> GetPool(string resName)
        {
            ObjectPool<BaseBullet> pool;
            if (_pools.TryGetValue(resName, out pool))
            {
                return pool;
            }
            if (!_inited)
            {
                Debug.LogError("[Bullet] 管理器尚未初始化，无法创建子弹");
                return null;
            }
            string captured = resName;
            pool = new ObjectPool<BaseBullet>(
                create: () => CreateBullet(captured),
                reset: b => b.OnRecycle(),
                maxSize: _maxPoolSize,
                prewarm: 0);
            _pools[resName] = pool;
            return pool;
        }

        private BaseBullet CreateBullet(string resName)
        {
            if (BulletParent == null)
            {
                GameObject root = GameObject.Find("BulletRoot");
                BulletParent = root != null ? root.transform : null;
            }
            GameObject go = ResLoader.Instance.Instantiate(resName, BulletParent);
            if (go == null)
            {
                return null;
            }
            BaseBullet b = go.GetComponent<BaseBullet>();
            if (b == null)
            {
                b = go.AddComponent<BaseBullet>();
            }
            CombatSystem.Instance.RegisterBullet(b);
            go.SetActive(false);
            return b;
        }

        /// <summary>
        /// 发射一颗子弹。
        /// </summary>
        /// <param name="towerEffectValue">发射塔的 effectValue（&gt;0 时覆盖子弹的，见 BaseBullet.Init）</param>
        public void Fire(BaseEnemy target, float damage, Vector2 fromPos, BulletConfig cfg, float towerEffectValue)
        {
            if (target == null || cfg == null)
            {
                return;
            }
            string resName = string.IsNullOrEmpty(cfg.ResName) ? BaseBullet.FallbackResName : cfg.ResName;
            ObjectPool<BaseBullet> pool = GetPool(resName);
            if (pool == null)
            {
                return;
            }
            BaseBullet b = pool.Get();
            if (b == null)
            {
                Debug.LogError("[Bullet] 子弹创建失败，请检查 ResTable 中的 " + resName + " 是否就绪");
                return;
            }
            b.transform.SetParent(BulletParent, false);
            b.transform.position = new Vector3(fromPos.x, fromPos.y, 0f);
            b.Init(target, damage, cfg, towerEffectValue);

            if (CombatSystem.Instance != null)
            {
                CombatSystem.Instance.AddFireCount(1);
            }
        }

        /// <summary>兼容旧调用点：不带塔效果参数（等价于 effectValue=0，用子弹自己的值）。</summary>
        public void Fire(BaseEnemy target, float damage, Vector2 fromPos, BulletConfig cfg)
        {
            Fire(target, damage, fromPos, cfg, 0f);
        }

        public void RecycleBullet(BaseBullet b)
        {
            if (b == null)
            {
                return;
            }
            string resName = string.IsNullOrEmpty(b.ResName) ? BaseBullet.FallbackResName : b.ResName;
            ObjectPool<BaseBullet> pool;
            if (!_pools.TryGetValue(resName, out pool) || pool == null)
            {
                // 找不到原池（理论上不会）：直接销毁，避免对象泄漏在场景里
                Object.Destroy(b.gameObject);
                return;
            }
            pool.Release(b);
        }

        /// <summary>
        /// 回收全部在场子弹（切关 / 重开用）。
        /// 【为什么必须走 RecycleBullet 而不是直接 OnRecycle】
        /// 只有走对象池的 Release 才会把 reset 回调跑全、并把对象真正放回池子；
        /// 直接调 OnRecycle 会让子弹"看起来回收了、其实既不在场上也不在池里"，下次开火凭空少一发。
        /// </summary>
        public void RecycleAll()
        {
            _clearBuf.Clear();
            if (CombatSystem.Instance != null)
            {
                CombatSystem.Instance.CopyBullets(_clearBuf);
            }
            for (int i = _clearBuf.Count - 1; i >= 0; i--)
            {
                BaseBullet b = _clearBuf[i];
                if (b != null && b.State == BulletState.Fire)
                {
                    RecycleBullet(b);
                }
            }
            _clearBuf.Clear();
        }

        /// <summary>空闲子弹总数（自检/调试用）</summary>
        public int PooledCount
        {
            get
            {
                int n = 0;
                foreach (KeyValuePair<string, ObjectPool<BaseBullet>> kv in _pools)
                {
                    if (kv.Value != null)
                    {
                        n += kv.Value.IdleCount;
                    }
                }
                return n;
            }
        }
    }
}
