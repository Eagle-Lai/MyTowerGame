using UnityEngine;

namespace FTProject
{
    public enum BulletState { None = 0, Fire, Idle }

    /// <summary>
    /// 子弹基类（v2.1 的 2D 版）。
    ///
    /// 相对 v1.0 的关键改动：
    ///   - **移除 OnTriggerEnter 命中判定**，改为每帧「与目标的距离 ≤ hitRadius」判定（需求 8）
    ///   - 不再用 transform.Translate(Vector3.forward)，改为 Vector2 方向位移
    ///   - 伤害由发射塔注入（v1.0 硬编码 Hurt(1)）
    ///   - 复用时必须完整重置状态，否则会出现"带着上次目标飞出去"的经典池化 Bug
    /// </summary>
    public class BaseBullet : MonoBehaviour
    {
        public BulletState State { get; private set; }

        private BaseEnemy _target;
        private Vector2 _dir = Vector2.right;
        private float _speed;
        private float _hitRadius;
        private float _lifeTime;
        private float _lifeTimer;
        private float _damage;
        private int _pierce;
        private float _aoeRadius;
        private SpriteRenderer _sr;

        public void Init(BaseEnemy target, float damage, BulletConfig cfg)
        {
            _target = target;
            _damage = damage;
            _speed = cfg.Speed;
            _hitRadius = cfg.HitRadius;
            _lifeTime = cfg.LifeTimeSec;
            _pierce = cfg.Pierce;
            _aoeRadius = cfg.AoeRadius;
            _lifeTimer = 0f;
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

            if (target != null && target.IsAlive)
            {
                Vector2 d = target.Position - (Vector2)transform.position;
                if (d.sqrMagnitude > 0.000001f)
                {
                    _dir = d.normalized;
                }
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

            // ① 追踪目标（目标死亡则保持最后方向飞完剩余寿命）
            if (_target != null && _target.IsAlive)
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

            // ③ 命中判定：与目标的距离 ≤ (子弹命中半径 + 怪物受击半径)
            // 【为什么要加怪物半径】只用子弹自己的 hitRadius 时，判定面是"目标中心的一个小圆"，
            // 怪物越大反而越难打中（视觉上明显穿过身体却不算命中）。
            // 加上 BodyRadius 后，判定面 ≈ 怪物身体轮廓，符合直觉，且两个半径都可配。
            if (_target != null && _target.IsAlive)
            {
                float hitR = _hitRadius + _target.BodyRadius;
                float sqr = ((Vector2)_target.Position - pos).sqrMagnitude;
                if (sqr <= hitR * hitR)
                {
                    OnHit(_target);
                    return;
                }
            }

            // ④ 超时回收（防止"追不上的子弹"永久存在）
            _lifeTimer += dt;
            if (_lifeTimer >= _lifeTime)
            {
                Recycle();
            }
        }

        private void OnHit(BaseEnemy e)
        {
            e.Hurt(_damage);

            // AOE：对半径内其他敌人也造成伤害（M2 启用，M0 的配置 aoeRadius=0）
            if (_aoeRadius > 0f && CombatSystem.Instance != null && CombatSystem.Instance.Grid != null)
            {
                // 简化实现：用空间哈希取候选后精确过滤，避免全表遍历
                System.Collections.Generic.List<BaseEnemy> buf =
                    new System.Collections.Generic.List<BaseEnemy>(16);
                CombatSystem.Instance.Grid.QueryCircle(Position, _aoeRadius, buf);
                float r2 = _aoeRadius * _aoeRadius;
                for (int i = 0; i < buf.Count; i++)
                {
                    BaseEnemy other = buf[i];
                    if (other == null || !other.IsAlive || other == e)
                    {
                        continue;
                    }
                    if ((other.Position - Position).sqrMagnitude <= r2)
                    {
                        other.Hurt(_damage);
                    }
                }
            }

            if (_pierce > 0)
            {
                _pierce--;
                _target = null;   // 继续飞行，寻找下一个目标（M2 完善）
                return;
            }
            Recycle();
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
            gameObject.SetActive(false);
        }
    }

    /// <summary>
    /// 子弹管理器（池化）。
    /// 与 v1.0 的差异：统一使用通用 ObjectPool，并在取出/归还时完整重置状态。
    /// </summary>
    public class BulletManager : BaseManager<BulletManager>
    {
        public Transform BulletParent { get; private set; }

        private ObjectPool<BaseBullet> _pool;
        private string _resName = "Bullet_Normal";
        private bool _inited;

        public override void OnInit()
        {
            base.OnInit();

            // 幂等保护：重复初始化会新建一个对象池，之前发出去的池化对象就再也回不来了
            if (_inited)
            {
                Debug.LogWarning("[Bullet] OnInit 被重复调用，已忽略（管理器应只初始化一次）");
                return;
            }
            _inited = true;

            int prewarm = Configs.Global != null ? Configs.Global.BulletPoolSize : 128;
            _pool = new ObjectPool<BaseBullet>(
                create: CreateBullet,
                reset: b => b.OnRecycle(),
                maxSize: prewarm * 2,
                prewarm: 0);
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
            if (_pool != null)
            {
                _pool.Clear(b =>
                {
                    if (b != null && b.gameObject != null)
                    {
                        Object.Destroy(b.gameObject);
                    }
                });
            }
        }

        public void SetParent(Transform parent)
        {
            BulletParent = parent;
        }

        private BaseBullet CreateBullet()
        {
            if (BulletParent == null)
            {
                GameObject root = GameObject.Find("BulletRoot");
                BulletParent = root != null ? root.transform : null;
            }
            GameObject go = ResLoader.Instance.Instantiate(_resName, BulletParent);
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

        /// <summary>发射一颗子弹</summary>
        public void Fire(BaseEnemy target, float damage, Vector2 fromPos, BulletConfig cfg)
        {
            if (target == null || cfg == null)
            {
                return;
            }
            BaseBullet b = _pool.Get();
            if (b == null)
            {
                Debug.LogError("[Bullet] 子弹创建失败，请检查 ResTable 中的 Bullet_Normal 是否就绪");
                return;
            }
            b.transform.SetParent(BulletParent, false);
            b.transform.position = new Vector3(fromPos.x, fromPos.y, 0f);
            b.Init(target, damage, cfg);

            if (CombatSystem.Instance != null)
            {
                CombatSystem.Instance.AddFireCount(1);
            }
        }

        public void RecycleBullet(BaseBullet b)
        {
            if (b == null)
            {
                return;
            }
            _pool.Release(b);
        }

        public int PooledCount { get { return _pool != null ? _pool.IdleCount : 0; } }
    }
}
